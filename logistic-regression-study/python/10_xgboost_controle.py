#!/usr/bin/env python3
"""
==============================================================================
Script : 10_xgboost_controle.py
Table source : client-divers.reviewflowz.reviews_panel_features
               (ou data/bigquery/reviews_panel_features.parquet)
Texte source : client-divers.reviewflowz.reviews
               (ou data/bigquery/reviews.parquet)

Contrôle par apprentissage automatique (point L15 du backlog).
Évalue un modèle d'arbres de décision (XGBoost) sur le panel de 225 757 avis,
en intégrant des caractéristiques textuelles interprétables (forme, discordance,
mots dominants) et en mesurant les contributions via SHAP.

RÈGLES DE RESTITUTION ET DE MÉTHODE :
  - Découpage par établissement (cid) et retrait des auteurs partagés pour le test.
  - Évaluation sur l'aire sous la courbe (AUC) et la calibration des probabilités.
  - Production systématique avec et sans les six enseignes signalées.
  - L'âge de l'avis est une variable de contrôle.
==============================================================================
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

import xgboost as xgb
import shap
from sklearn.feature_extraction.text import TfidfVectorizer

# ---------------------------------------------------------------------------
# Constantes et chemins
# ---------------------------------------------------------------------------

PROJET = "client-divers"
DATASET = "reviewflowz"
TABLE_PANEL = "reviews_panel_features"
TABLE_REVIEWS = "reviews"

DOSSIER_CLES = Path("/home/romain/.gcp")
RACINE_DEPOT = Path(__file__).resolve().parent.parent.parent
DOSSIER_DATA_LOCAL = RACINE_DEPOT / "data" / "bigquery"

SORTIES = (Path(__file__).resolve().parent.parent / "output-study"
           / f"{date.today():%Y-%m-%d}-sorties-10")

PART_TEST = 0.25
GRAINE = 20260914
SEUIL_SECTEUR_RARE = 0.01
TAILLE_ECHANTILLON_SHAP = 5000

MOTS_NEGATIFS = {
    "bad", "worst", "horrible", "terrible", "awful", "scam", "fraud", "avoid",
    "mauvais", "pire", "catastrophe", "arnaque", "fuyez", "nul", "honte",
    "pesimo", "peor", "engano", "estafa", "mala", "evitar", "schlecht", "falsch"
}
MOTS_POSITIFS = {
    "great", "best", "excellent", "amazing", "wonderful", "perfect", "good", "love",
    "super", "parfait", "meilleur", "top", "merci", "bravo", "adore",
    "excelente", "mejor", "perfecto", "buen", "maravilla", "gracias", "toll", "gut"
}

COLONNES_SOCLE = [
    "review_id", "cid", "author_key", "supprime",
    "age_a_la_vague1_j", "star", "has_photo",
    "reponse_avant_surveillance", "reviewer_review_count",
    "situation_auteur", "n_avis_meme_jour_auteur",
    "langue_minoritaire_sur_la_fiche",
    "industry", "bucket", "region",
    "chaine_antiparasitaire_us", "salle_de_sport_attaquee",
    "log_ratio_pic_journalier_fiche",
]


# ---------------------------------------------------------------------------
# Authentification et chargement des données
# ---------------------------------------------------------------------------

def trouver_cle() -> str | None:
    if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        return None
    if not DOSSIER_CLES.is_dir():
        return None
    cles = sorted(DOSSIER_CLES.glob("*.json"))
    if len(cles) > 1:
        raise SystemExit(
            f"{len(cles)} clés dans {DOSSIER_CLES}. "
            f"Poser GOOGLE_APPLICATION_CREDENTIALS sur la clé active.")
    return str(cles[0]) if cles else None


def charger_donnees(utiliser_bigquery: bool) -> tuple[pd.DataFrame, pd.Series | None]:
    """Charge le panel et le texte associé."""
    chemin_panel_parquet = DOSSIER_DATA_LOCAL / "reviews_panel_features.parquet"
    chemin_reviews_parquet = DOSSIER_DATA_LOCAL / "reviews.parquet"

    if not utiliser_bigquery and chemin_panel_parquet.exists():
        print(f"[donnees] lecture locale : {chemin_panel_parquet.name}")
        df = pd.read_parquet(chemin_panel_parquet, columns=COLONNES_SOCLE).reset_index(drop=True)
        serie_text = None
        if chemin_reviews_parquet.exists():
            print(f"[donnees] lecture du texte local via DuckDB : {chemin_reviews_parquet.name}")
            import duckdb
            con = duckdb.connect()
            con.execute("SET memory_limit = '3GB'")
            sql = f"""
            SELECT r.review_id, r.text
            FROM '{chemin_reviews_parquet.as_posix()}' r
            SEMI JOIN '{chemin_panel_parquet.as_posix()}' p ON r.review_id = p.review_id
            """
            df_text = con.execute(sql).df().drop_duplicates(subset=["review_id"]).set_index("review_id")
            serie_text = df["review_id"].map(df_text["text"]).reset_index(drop=True)
        return df, serie_text

    print("[donnees] interrogation de BigQuery")
    cle = trouver_cle()
    if cle:
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = cle
    from google.cloud import bigquery
    client = bigquery.Client(project=PROJET)

    sql_panel = f"SELECT {', '.join(COLONNES_SOCLE)} FROM `{PROJET}.{DATASET}.{TABLE_PANEL}`"
    df = client.query(sql_panel).to_arrow(create_bqstorage_client=True).to_pandas(
        split_blocks=True, self_destruct=True)

    sql_text = f"""
    SELECT p.review_id, r.text
    FROM `{PROJET}.{DATASET}.{TABLE_PANEL}` p
    LEFT JOIN `{PROJET}.{DATASET}.{TABLE_REVIEWS}` r USING (review_id)
    """
    df_text = client.query(sql_text).to_arrow(create_bqstorage_client=True).to_pandas(
        split_blocks=True, self_destruct=True)
    serie_text = df.merge(df_text, on="review_id", how="left")["text"]
    return df, serie_text


# ---------------------------------------------------------------------------
# Extraction des caractéristiques textuelles
# ---------------------------------------------------------------------------

def extraire_caracteristiques_texte(serie_texte: pd.Series,
                                    star: pd.Series,
                                    masque_train: np.ndarray) -> pd.DataFrame:
    """Calcule les caractéristiques de forme, de discordance et les 50 termes discriminants."""
    print("[texte] extraction des caractéristiques de forme...")
    texte_propre = serie_texte.fillna("").astype(str)

    # 1. Signaux de forme
    chars = texte_propre.str.len().astype("float32")
    words = texte_propre.str.split().str.len().astype("float32")
    avg_word = np.where(words > 0, chars / words, 0.0).astype("float32")

    def ratio_maj(t: str) -> float:
        if not t:
            return 0.0
        n_alpha = sum(1 for c in t if c.isalpha())
        return sum(1 for c in t if c.isupper()) / n_alpha if n_alpha > 0 else 0.0

    part_maj = pd.Series([ratio_maj(t) for t in texte_propre], dtype="float32")
    pts_excl = texte_propre.str.count(r"!").astype("float32")
    pts_interr = texte_propre.str.count(r"\?").astype("float32")
    
    def a_emoji(t: str) -> float:
        return 1.0 if any(ord(c) > 0x1F000 for c in t) else 0.0

    has_emoji = pd.Series([a_emoji(t) for t in texte_propre], dtype="float32")
    is_short = ((words >= 1) & (words <= 3)).astype("float32")

    # 2. Discordance note / ton
    print("[texte] détection de discordance note et lexique...")
    mots_minuscules = texte_propre.str.lower().str.split()

    def verifier_discordance(mots: list[str], note: int) -> float:
        s = set(mots)
        if note <= 2 and (s & MOTS_POSITIFS):
            return 1.0
        if note >= 4 and (s & MOTS_NEGATIFS):
            return 1.0
        return 0.0

    discordance = pd.Series(
        [verifier_discordance(m, n) for m, n in zip(mots_minuscules, star)],
        dtype="float32")

    df_base_texte = pd.DataFrame({
        "texte_chars": chars,
        "texte_mots": words,
        "texte_longueur_moy_mot": avg_word,
        "texte_part_majuscules": part_maj,
        "texte_pts_exclamation": pts_excl,
        "texte_pts_interrogation": pts_interr,
        "texte_presence_emoji": has_emoji,
        "texte_court_generique": is_short,
        "texte_discordance_ton_note": discordance,
    })

    # 3. 50 termes discriminants (TF-IDF ajusté sur le train uniquement)
    print("[texte] ajustement TF-IDF sur le jeu d'entraînement (50 termes)...")
    docs_train = texte_propre[masque_train & (texte_propre.str.strip().str.len() > 0)]
    if len(docs_train) >= 10:
        min_doc_freq = max(2, min(30, int(0.001 * len(docs_train))))
        tfidf = TfidfVectorizer(max_features=50, stop_words="english", min_df=min_doc_freq, binary=True)
        try:
            tfidf.fit(docs_train)
            vocab = [f"mot_{re.sub(r'[^a-zA-Z0-9_]', '', m)}" for m in tfidf.get_feature_names_out()]
            mat_tfidf = tfidf.transform(texte_propre).toarray().astype("float32")
            df_tfidf = pd.DataFrame(mat_tfidf, columns=vocab)
        except ValueError:
            df_tfidf = pd.DataFrame(index=df_base_texte.index)
    else:
        df_tfidf = pd.DataFrame(index=df_base_texte.index)

    return pd.concat([df_base_texte, df_tfidf], axis=1)


# ---------------------------------------------------------------------------
# Préparation de la matrice d'apprentissage
# ---------------------------------------------------------------------------

def preparer_matrice(df: pd.DataFrame, avec_region: bool) -> pd.DataFrame:
    """Construit les variables du socle (catégories en colonnes binaires)."""
    morceaux = []

    # Variables continues et de comptage (inutile de doubler avec le log dans un arbre)
    df_num = pd.DataFrame({
        "age_a_la_vague1_j": df["age_a_la_vague1_j"].fillna(0).clip(lower=0).astype("float32"),
        "reviewer_review_count": df["reviewer_review_count"].fillna(0).astype("float32"),
        "n_avis_meme_jour_auteur": df["n_avis_meme_jour_auteur"].fillna(1).astype("float32"),
        "log_ratio_pic_journalier_fiche": df["log_ratio_pic_journalier_fiche"].fillna(0).astype("float32"),
        "star": df["star"].fillna(0).astype("float32"),
        "has_photo": df["has_photo"].astype("float32"),
        "reponse_avant_surveillance": df["reponse_avant_surveillance"].astype("float32"),
        "langue_minoritaire_sur_la_fiche": df["langue_minoritaire_sur_la_fiche"].astype("float32"),
    })
    morceaux.append(df_num)

    # Variables catégorielles encodées
    def encoder_dummies(serie, prefixe):
        return pd.get_dummies(serie, prefix=prefixe, dtype="float32", drop_first=True)

    morceaux.append(encoder_dummies(df["star"].astype(str), "etoiles"))
    morceaux.append(encoder_dummies(df["situation_auteur"], "profil"))
    morceaux.append(encoder_dummies(df["bucket"], "taille"))

    # Secteurs rares regroupés
    parts = df["industry"].value_counts(normalize=True, dropna=False)
    rares = parts[parts < SEUIL_SECTEUR_RARE].index
    secteur = df["industry"].astype("object").where(~df["industry"].isin(rares), "autres")
    morceaux.append(encoder_dummies(secteur.fillna("inconnu"), "secteur"))

    if avec_region:
        morceaux.append(encoder_dummies(df["region"], "region"))

    return pd.concat(morceaux, axis=1)


# ---------------------------------------------------------------------------
# Protocole d'évaluation et de découpage
# ---------------------------------------------------------------------------

def decoupage_fiches(df: pd.DataFrame, graine: int) -> tuple[np.ndarray, np.ndarray]:
    """Sépare les établissements pour isoler 25 % d'avis de test.
    Retire du test les auteurs présents dans les deux groupes."""
    tirage = np.random.default_rng(graine)
    cids = df["cid"].astype("category").cat.categories.to_numpy()
    cids_test = set(tirage.choice(cids, size=int(len(cids) * PART_TEST), replace=False))

    masque_test = df["cid"].isin(cids_test)
    auteurs_train = set(df.loc[~masque_test, "author_key"].dropna().unique())
    masque_test = masque_test & ~df["author_key"].isin(auteurs_train)
    masque_train = ~masque_test

    print(f"  {len(cids_test)} établissements mis de côté ; "
          f"entraînement : {masque_train.sum():,} avis, "
          f"test : {masque_test.sum():,} avis".replace(",", " "))
    return masque_train.to_numpy(), masque_test.to_numpy()


def aire_sous_courbe(y_true: np.ndarray, y_score: np.ndarray) -> float:
    n_pos = int(y_true.sum())
    n_neg = len(y_true) - n_pos
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    rangs = pd.Series(y_score).rank(method="average").to_numpy()
    return float((rangs[y_true == 1].sum() - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg))


def tableau_calibration(y_true: np.ndarray, y_prob: np.ndarray, n_tranches: int = 10) -> pd.DataFrame:
    tab = pd.DataFrame({"p": y_prob, "y": y_true})
    tab["tranche"] = pd.qcut(tab["p"], n_tranches, duplicates="drop")
    return tab.groupby("tranche", observed=True).agg(
        risque_prevu=("p", "mean"),
        risque_observe=("y", "mean"),
        avis=("y", "size")
    ).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Entraînement et explicabilité
# ---------------------------------------------------------------------------

def entrainer_et_evaluer(X_train: pd.DataFrame, y_train: np.ndarray,
                         X_test: pd.DataFrame, y_test: np.ndarray,
                         suffixe: str) -> dict:
    """Entraîne XGBoost, évalue le classement et génère les diagnostics SHAP."""
    ratio_desequilibre = float((len(y_train) - y_train.sum()) / y_train.sum())
    print(f"[{suffixe}] ratio de pondération des classes : {ratio_desequilibre:.1f}")

    modele = xgb.XGBClassifier(
        n_estimators=300,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=1.0,
        eval_metric="auc",
        random_state=GRAINE,
        n_jobs=4,
    )

    # Entraînement
    modele.fit(
        X_train, y_train,
        eval_set=[(X_train, y_train), (X_test, y_test)],
        verbose=False
    )

    # Prédictions
    prob_test = modele.predict_proba(X_test)[:, 1]
    auc_test = aire_sous_courbe(y_test, prob_test)
    print(f"  AUC XGBoost sur test : {auc_test:.3f}")

    # Importance par gain
    gain_dict = modele.get_booster().get_score(importance_type="gain")
    total_gain = sum(gain_dict.values()) if gain_dict else 1.0
    tab_gain = pd.DataFrame([
        {"variable": k, "gain_brut": v, "part_gain_pct": round(v / total_gain * 100, 2)}
        for k, v in gain_dict.items()
    ]).sort_values(by="gain_brut", ascending=False).reset_index(drop=True)
    tab_gain.to_csv(SORTIES / f"10_importance_gain_{suffixe}.csv", index=False)

    # Calibration
    calib = tableau_calibration(y_test, prob_test)
    calib.to_csv(SORTIES / f"10_calibration_{suffixe}.csv", index=False)

    fig, ax = plt.subplots(figsize=(6, 6))
    hi = float(calib["risque_prevu"].max())
    ax.plot([0, hi], [0, hi], "--", color="grey", lw=1, label="prévision juste")
    ax.plot(calib["risque_prevu"], calib["risque_observe"], "o-",
            color="#2ca02c", label="XGBoost")
    ax.set_xlabel("risque annoncé par le modèle")
    ax.set_ylabel("part réellement supprimée")
    ax.set_title(f"XGBoost {suffixe} — AUC {auc_test:.3f}")
    ax.legend()
    fig.tight_layout()
    fig.savefig(SORTIES / f"10_calibration_{suffixe}.png", dpi=150)
    plt.close(fig)

    # Analyse SHAP sur échantillon
    n_ech = min(TAILLE_ECHANTILLON_SHAP, len(X_test))
    print(f"[{suffixe}] calcul SHAP sur {n_ech:,} avis du test...".replace(",", " "))
    idx_ech = np.random.default_rng(GRAINE).choice(len(X_test), size=n_ech, replace=False)
    X_shap = X_test.iloc[idx_ech].copy()

    explainer = shap.TreeExplainer(modele)
    raw_shap = explainer.shap_values(X_shap)
    if isinstance(raw_shap, list):
        shap_values = raw_shap[1]
    elif len(getattr(raw_shap, "shape", [])) == 3:
        shap_values = raw_shap[:, :, 1]
    else:
        shap_values = raw_shap

    # Beeswarm summary plot
    fig = plt.figure(figsize=(10, 8))
    shap.summary_plot(shap_values, X_shap, show=False, max_display=20)
    plt.title(f"Impact SHAP des 20 variables principales — {suffixe}", fontsize=12)
    plt.tight_layout()
    plt.savefig(SORTIES / f"10_shap_summary_{suffixe}.png", dpi=150)
    plt.close(fig)

    # Courbes de dépendance sur l'âge et la longueur de texte
    variables_dependance = [v for v in ["age_a_la_vague1_j", "texte_chars", "reviewer_review_count"]
                            if v in X_shap.columns]
    if variables_dependance:
        n_plots = len(variables_dependance)
        fig, axes = plt.subplots(1, n_plots, figsize=(6 * n_plots, 5))
        if n_plots == 1:
            axes = [axes]
        for ax, var in zip(axes, variables_dependance):
            idx_var = list(X_shap.columns).index(var)
            ax.scatter(X_shap[var], shap_values[:, idx_var], alpha=0.3, s=12, color="#1f77b4")
            ax.axhline(0, color="grey", linestyle="--", lw=1)
            ax.set_xlabel(var)
            ax.set_ylabel("Valeur SHAP (impact sur log-cote)")
            ax.set_title(f"Dépendance : {var}")
        fig.tight_layout()
        fig.savefig(SORTIES / f"10_dependance_{suffixe}.png", dpi=150)
        plt.close(fig)

    # Extraction des interactions arborescentes
    df_trees = modele.get_booster().trees_to_dataframe()
    branches = df_trees[df_trees["Feature"] != "Leaf"]
    yes_m = branches.merge(branches[["ID", "Feature", "Gain"]], left_on="Yes", right_on="ID", suffixes=("", "_enfant"))
    no_m = branches.merge(branches[["ID", "Feature", "Gain"]], left_on="No", right_on="ID", suffixes=("", "_enfant"))
    paires = pd.concat([yes_m, no_m])
    paires = paires[paires["Feature"] != paires["Feature_enfant"]]
    if not paires.empty:
        paires["var1"] = np.minimum(paires["Feature"], paires["Feature_enfant"])
        paires["var2"] = np.maximum(paires["Feature"], paires["Feature_enfant"])
        tab_inter = paires.groupby(["var1", "var2"])["Gain_enfant"].sum().reset_index()
        tab_inter = tab_inter.sort_values(by="Gain_enfant", ascending=False).reset_index(drop=True)
        tab_inter.rename(columns={"Gain_enfant": "gain_interaction"}, inplace=True)
        tab_inter.to_csv(SORTIES / f"10_interactions_{suffixe}.csv", index=False)
    else:
        tab_inter = pd.DataFrame(columns=["var1", "var2", "gain_interaction"])

    # Synthèse texte
    lignes_summary = [
        "=" * 78,
        f"Modèle XGBoost : {suffixe}",
        f"Avis entraînement : {len(X_train):,}, Avis test : {len(X_test):,}".replace(",", " "),
        f"Suppressions test : {int(y_test.sum()):,}",
        f"AUC XGBoost : {auc_test:.3f}",
        "Comparaison repère : Régression logistique AUC = 0.86",
        "=" * 78,
        "",
        "Dix variables avec le plus fort gain :",
    ]
    for _, row in tab_gain.head(10).iterrows():
        lignes_summary.append(f"  - {row['variable']:<30} : {row['part_gain_pct']:>5.2f} % du gain")

    if not tab_inter.empty:
        lignes_summary += [
            "",
            "Cinq interactions les plus fortes entre variables :",
        ]
        for _, row in tab_inter.head(5).iterrows():
            lignes_summary.append(f"  - {row['var1']} x {row['var2']} (gain cumulé : {row['gain_interaction']:.1f})")

    (SORTIES / f"10_summary_{suffixe}.txt").write_text("\n".join(lignes_summary), encoding="utf-8")

    return {
        "passage": suffixe,
        "auc_xgboost": auc_test,
        "avis_train": len(X_train),
        "avis_test": len(X_test),
        "suppressions_test": int(y_test.sum()),
    }


# ---------------------------------------------------------------------------
# Programme principal
# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description="XGBoost et analyse SHAP sur le panel d'avis.")
    ap.add_argument("--region", default="tous", choices=["US", "Europe", "tous"])
    ap.add_argument("--sans-enseignes-signalees", action="store_true",
                    help="retire les 4 chaînes antiparasitaires et les 2 salles de sport")
    ap.add_argument("--sans-texte", action="store_true",
                    help="tourne sans les caractéristiques textuelles (socle seul)")
    ap.add_argument("--test-rapide", action="store_true",
                    help="limite à 3 000 avis pour tester le pipeline de bout en bout")
    ap.add_argument("--bigquery", action="store_true",
                    help="force la lecture depuis BigQuery au lieu des fichiers locaux")
    args = ap.parse_args()

    SORTIES.mkdir(parents=True, exist_ok=True)

    df_brut, serie_texte = charger_donnees(args.bigquery)

    if args.test_rapide:
        print("[test-rapide] échantillon de 3 000 avis pour validation...")
        pos_idx = df_brut[df_brut["supprime"] == 1].sample(n=150, random_state=GRAINE).index
        neg_idx = df_brut[df_brut["supprime"] == 0].sample(n=2850, random_state=GRAINE).index
        melange_idx = pd.Index(np.random.default_rng(GRAINE).permutation(pos_idx.append(neg_idx)))
        df_brut = df_brut.loc[melange_idx].reset_index(drop=True)
        if serie_texte is not None:
            serie_texte = serie_texte.loc[melange_idx].reset_index(drop=True)

    if args.region != "tous":
        masque_reg = df_brut["region"] == args.region
        df_brut = df_brut[masque_reg].reset_index(drop=True)
        if serie_texte is not None:
            serie_texte = serie_texte[masque_reg].reset_index(drop=True)
        print(f"[filtre] région {args.region} : {len(df_brut):,} avis".replace(",", " "))

    if args.sans_enseignes_signalees:
        garde = (df_brut["chaine_antiparasitaire_us"] == 0) & (df_brut["salle_de_sport_attaquee"] == 0)
        df_brut = df_brut[garde].reset_index(drop=True)
        if serie_texte is not None:
            serie_texte = serie_texte[garde].reset_index(drop=True)
        print(f"[filtre] enseignes signalées retirées : {len(df_brut):,} avis restants".replace(",", " "))

    suffixe = args.region + ("_sans_enseignes" if args.sans_enseignes_signalees else "")
    if args.sans_texte:
        suffixe += "_sans_texte"

    # Découpage par établissement
    masque_train, masque_test = decoupage_fiches(df_brut, GRAINE)

    # Matrice socle
    avec_region = args.region == "tous" and df_brut["region"].nunique() > 1
    X_socle = preparer_matrice(df_brut, avec_region)

    if not args.sans_texte and serie_texte is not None:
        X_texte = extraire_caracteristiques_texte(serie_texte, df_brut["star"], masque_train)
        X = pd.concat([X_socle, X_texte], axis=1)
    else:
        X = X_socle

    y = df_brut["supprime"].astype("int8").to_numpy()

    X_train = X[masque_train].reset_index(drop=True)
    y_train = y[masque_train]
    X_test = X[masque_test].reset_index(drop=True)
    y_test = y[masque_test]

    resultats = entrainer_et_evaluer(X_train, y_train, X_test, y_test, suffixe)

    df_res = pd.DataFrame([resultats])
    df_res.to_csv(SORTIES / f"10_metriques_{suffixe}.csv", index=False)
    print(f"\n[succès] résultats enregistrés dans {SORTIES}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as erreur:
        print(f"\nARRÊT : {erreur}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
