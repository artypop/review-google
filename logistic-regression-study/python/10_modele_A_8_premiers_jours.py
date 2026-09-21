#!/usr/bin/env python3
"""
==============================================================================
Script : 10_modele_A_8_premiers_jours.py
Table source : client-divers.reviewflowz.reviews_panel_features_03
Plan approuvé par Romain le 2026-09-17. Période réduite au 10-16 août le même jour :
sur les avis du 7 août, 105 des 116 suppressions tombaient à 9 jours ou plus et
étaient retirées, ce qui faisait paraître ces jours presque sans suppression.

QUESTION
  Parmi les avis publiés du 10 au 16 août 2026, qu'est-ce qui fait qu'un avis
  est supprimé au plus tard lors de son 8e jour, comparé à un avis jamais
  supprimé jusqu'au 24 août ?

------------------------------------------------------------------------------
POURQUOI CE MODÈLE
------------------------------------------------------------------------------
Les suppressions se concentrent sur les premiers jours de l'avis : 7 sur 10
tombent au 6e ou au 7e jour (docs/03-resultats.md § 4). Le 07 mesure l'âge par
rapport au 11 août et mélange ces suppressions précoces avec les tardives. Ce
modèle ne regarde que les 8 premiers jours.

------------------------------------------------------------------------------
LA POPULATION ET CE QU'ON PRÉDIT
------------------------------------------------------------------------------
  Avis gardés    publiés du 10 au 16 août inclus.
                 Le dernier, publié le 16, atteint son 8e jour le 24 août, jour
                 du dernier passage du robot : tous sont vus jusqu'à leur 8e
                 jour.
  Supprimé (1)   disparu au plus tard 8 jours après sa publication.
  En ligne (0)   jamais supprimé jusqu'au 24 août.
  Retiré         supprimé 9 jours ou plus après sa publication. Ces avis ne
                 sont ni du côté « supprimé » ni du côté « en ligne ».

La date de publication se lit dans `age_a_la_vague1_j`, l'écart en jours entre
la publication et le 11 août : 1 pour le 10 août, -5 pour le 16 août.

------------------------------------------------------------------------------
LES HUIT CARACTÉRISTIQUES
------------------------------------------------------------------------------
  note                 1 à 5 étoiles, comparées à 5 étoiles
  photo                au moins une photo, oui ou non
  longueur du texte    sans texte (référence), 1-50, 51-200, plus de 200 car.
  avis de l'auteur     nombre d'avis sur son profil, en logarithme
  palier Local Guide   niveaux 1 à 3 (référence), sans niveau, 4 et plus
  photos de l'auteur   nombre de photos publiées sur son profil, en logarithme
                       (ajoutées le 2026-09-17 avec la table 03)
  rafale               avis publiés par le même auteur le même jour, en
                       logarithme
  pic sur la fiche     avis reçus par la fiche ce jour-là, rapportés à son
                       rythme habituel des 365 jours avant le 11 août, en
                       logarithme

La réponse du propriétaire n'y est pas. Un avis supprimé le lendemain n'a pas eu
le temps d'en recevoir une ; sans jalon, elle mesure la survie. Le 08 répond à la
question de la réponse (décision de Romain du 2026-09-17).

------------------------------------------------------------------------------
COMMENT LIRE LE TABLEAU DES EFFETS
------------------------------------------------------------------------------
`risque_relatif` compare deux avis identiques sur les sept autres
caractéristiques. À 2,0, l'avis disparaît deux fois plus souvent ; à 0,5, deux
fois moins. Quand la fourchette `borne_basse` – `borne_haute` contient 1, les
données ne disent pas dans quel sens joue la caractéristique.

Pour les quatre caractéristiques en logarithme, la valeur dit ce qui se passe
quand (1 + la quantité) est multiplié par 2,7.
Exemple : `log_burst` à 3,0. Un auteur qui publie 1 avis dans la journée vaut
1 + 1 = 2 ; un auteur qui en publie 4 vaut 1 + 4 = 5, soit 2,5 fois plus. Le
risque de chacun de ses avis est alors multiplié par 3 puissance log(2,5), soit
environ 2,7.

------------------------------------------------------------------------------
LES PASSAGES
------------------------------------------------------------------------------
  US_avec_enseignes    tous les avis américains
  US_sans_enseignes    sans les fiches de `biz_surveillance`
  Europe               tous les avis européens ; si des avis des deux salles
                       espagnoles sont dans la population, un passage
                       Europe_sans_enseignes est ajouté

------------------------------------------------------------------------------
MESURE DE QUALITÉ : CINQ TOURS PAR ÉTABLISSEMENT
------------------------------------------------------------------------------
Les fiches sont réparties en cinq groupes. À chaque tour, le modèle s'ajuste
sur quatre groupes et note les avis du cinquième. Chaque fiche est notée une
fois, par un modèle qui ne l'a jamais vue. Un avis dont l'auteur a aussi écrit
sur une fiche d'ajustement est écarté du tour. Même mécanique que le 07.

------------------------------------------------------------------------------
BIAIS CONNUS
------------------------------------------------------------------------------
- Un avis publié le 10 août et supprimé avant le 11 août n'est dans aucune
  table : le robot est arrivé le 11. Le tableau par jour de publication
  (`10_par_jour_*.csv`) montre si ces jours ont un taux plus bas.
- Les avis restés en ligne sont suivis 14 jours s'ils sont publiés le 10 août,
  8 jours s'ils le sont le 16.
- Le délai est compté au passage quotidien du robot.
- Le nombre d'avis, les photos et le niveau de l'auteur sont relevés au dernier
  passage.
- La rafale est sous-estimée : les avis à plusieurs enregistrements, dont la
  moitié sont publiés en rafale, sont exclus du panel.

------------------------------------------------------------------------------
COMMANDE
------------------------------------------------------------------------------
  nice -n 19 .venv/bin/python logistic-regression-study/python/10_modele_A_8_premiers_jours.py
==============================================================================
"""

from __future__ import annotations

import os
import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


# ---------------------------------------------------------------------------
# Réglages
# ---------------------------------------------------------------------------

PROJET = "client-divers"
DATASET = "reviewflowz"
TABLE = "reviews_panel_features_03"
TABLE_ENSEIGNES = "biz_surveillance"
DOSSIER_CLES = Path("/home/romain/.gcp")

SORTIES = (Path(__file__).resolve().parent.parent / "output-study"
           / f"{date.today():%Y-%m-%d}-sorties-10")

PREMIER_PASSAGE = date(2026, 8, 11)
# Publiés du 10 au 16 août : écart au 11 août entre 1 et -5 jours.
AGE_VAGUE1_MAX = 1
AGE_VAGUE1_MIN = -5
# Supprimé au plus tard lors du 8e jour.
DELAI_MAX = 8

TRANCHES_TEXTE = [-1, 0, 50, 200, 10**6]
NOMS_TRANCHES_TEXTE = ["sans_texte", "1_50", "51_200", "201p"]

REFERENCES = {
    "etoiles": "etoiles_5",
    "texte": "texte_sans_texte",
    "profil": "guide_1_3",
}

# Une colonne oui/non portée par moins de 30 avis, ou dont les avis ont moins
# de 5 suppressions, donne un effet sans valeur : elle est retirée du modèle.
MIN_AVIS_PAR_COLONNE = 30
MIN_SUPPRESSIONS_PAR_COLONNE = 5

N_TOURS = 5
GRAINE = 20260917


# ---------------------------------------------------------------------------
# 1. Lecture
# ---------------------------------------------------------------------------

def trouver_cle() -> str | None:
    """La clé de service, quel que soit son nom de fichier (même mécanique que le 07)."""
    if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") or not DOSSIER_CLES.is_dir():
        return None
    cles = sorted(DOSSIER_CLES.glob("*.json"))
    if len(cles) > 1:
        raise SystemExit(f"{len(cles)} clés dans {DOSSIER_CLES} : garder celle qui est "
                         f"active, ou poser GOOGLE_APPLICATION_CREDENTIALS.")
    return str(cles[0]) if cles else None


def lire() -> pd.DataFrame:
    """Charge les avis publiés du 10 au 16 août, y compris ceux à retirer.

    Les avis supprimés à 9 jours ou plus sont lus pour être comptés, puis retirés
    dans `preparer`. Le filtre de dates est fait dans BigQuery.
    """
    cle = trouver_cle()
    if cle:
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = cle
    from google.cloud import bigquery

    sql = f"""
        SELECT
          p.review_id, p.cid, p.author_key, p.region,
          p.age_a_la_vague1_j, p.supprime, p.age_a_la_suppression_j,
          p.star, p.has_photo, p.text_chars,
          p.log_rc, p.palier_local_guide, p.reviewer_photo_count, p.n_avis_meme_jour_auteur,
          p.log_ratio_pic_journalier_fiche,
          s.cid IS NOT NULL AS enseigne_surveillee
        FROM `{PROJET}.{DATASET}.{TABLE}` p
        LEFT JOIN `{PROJET}.{DATASET}.{TABLE_ENSEIGNES}` s ON s.cid = p.cid
        WHERE p.age_a_la_vague1_j BETWEEN {AGE_VAGUE1_MIN} AND {AGE_VAGUE1_MAX}
    """
    df = bigquery.Client(project=PROJET).query(sql).to_dataframe()
    print(f"[lecture] {len(df):,} avis publiés du 10 au 16 août".replace(",", " "))
    return df


# ---------------------------------------------------------------------------
# 2. Préparation
# ---------------------------------------------------------------------------

def preparer(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Ce qu'on prédit, et le retrait des suppressions tardives.
    supprime = df["supprime"].astype(bool)
    tardif = supprime & (df["age_a_la_suppression_j"] > DELAI_MAX)
    print(f"[corpus] {int(tardif.sum()):,} avis supprimés à 9 jours ou plus, retirés"
          .replace(",", " "))
    df = df[~tardif].copy()
    df["supprime"] = df["supprime"].astype(int)
    assert (df.loc[df["supprime"] == 1, "age_a_la_suppression_j"] <= DELAI_MAX).all()

    df["enseigne_surveillee"] = df["enseigne_surveillee"].astype(bool)
    df["date_publication"] = [
        (PREMIER_PASSAGE - timedelta(days=int(a))).isoformat()
        for a in df["age_a_la_vague1_j"]]

    df["etoiles"] = "etoiles_" + df["star"].astype(int).astype(str)
    df["has_photo"] = df["has_photo"].astype(int)
    df["texte"] = "texte_" + pd.cut(df["text_chars"].fillna(0).clip(lower=0),
                                    bins=TRANCHES_TEXTE,
                                    labels=NOMS_TRANCHES_TEXTE).astype(str)
    df["profil"] = "guide_" + df["palier_local_guide"].astype(str)
    df["log_photos_auteur"] = np.log1p(df["reviewer_photo_count"].fillna(0).clip(lower=0))
    df["log_rc"] = df["log_rc"].astype(float)
    # Rafale : 1 avis seul vaut log(2). `n_avis_meme_jour_auteur` n'est jamais
    # vide dans la table (COALESCE à 1 dans sql/02).
    df["log_burst"] = np.log1p(df["n_avis_meme_jour_auteur"].fillna(1).clip(lower=0))
    # Pic vide = fiche sans aucun avis dans les 365 jours avant le 11 août.
    df["log_ratio_pic_journalier_fiche"] = (
        df["log_ratio_pic_journalier_fiche"].fillna(0).astype(float))
    return df.reset_index(drop=True)


def matrice(df: pd.DataFrame) -> pd.DataFrame:
    """Colonnes de nombres. Chaque référence n'a pas de colonne."""
    morceaux = [df[["has_photo", "log_rc", "log_photos_auteur", "log_burst",
                    "log_ratio_pic_journalier_fiche"]].astype(float)]
    for famille in ["etoiles", "texte", "profil"]:
        d = pd.get_dummies(df[famille], dtype=float)
        morceaux.append(d.drop(columns=[REFERENCES[famille]], errors="ignore"))
    return sm.add_constant(pd.concat(morceaux, axis=1), has_constant="add")


def retirer_colonnes_trop_rares(X: pd.DataFrame, y: pd.Series) -> pd.DataFrame:
    """Retire les colonnes oui/non trop rares ou avec trop peu de suppressions."""
    a_retirer = []
    for col in X.columns:
        if col == "const" or not set(np.unique(X[col])) <= {0.0, 1.0}:
            continue
        a_un = X[col] == 1
        if a_un.sum() < MIN_AVIS_PAR_COLONNE or y[a_un].sum() < MIN_SUPPRESSIONS_PAR_COLONNE:
            a_retirer.append(col)
    if a_retirer:
        print(f"  colonnes retirées, trop rares : {', '.join(a_retirer)}")
    return X.drop(columns=a_retirer)


# ---------------------------------------------------------------------------
# 3. Tableaux bruts, sans modèle
# ---------------------------------------------------------------------------

def taux(g) -> pd.DataFrame:
    t = g["supprime"].agg(avis="size", suppressions="sum").reset_index()
    t["suppressions_pour_10000_avis"] = (t["suppressions"] / t["avis"] * 10000).round(1)
    return t


def tableau_croise(df: pd.DataFrame) -> pd.DataFrame:
    """Taux de suppression par valeur. Dénominateur : les avis qui ont cette valeur.
    Les trois caractéristiques en nombre sont découpées en tranches pour la lecture."""
    df = df.copy()
    df["avis_auteur"] = pd.cut(np.expm1(df["log_rc"]), [-1, 0, 5, 20, 100, np.inf],
                               labels=["0", "1_5", "6_20", "21_100", "plus_de_100"])
    df["rafale"] = pd.cut(df["n_avis_meme_jour_auteur"], [0, 1, 2, 3, np.inf],
                          labels=["1", "2", "3", "4_et_plus"])
    df["photos_auteur"] = pd.cut(df["reviewer_photo_count"].fillna(0), [-1, 0, 10, 100, np.inf],
                                 labels=["0", "1_10", "11_100", "plus_de_100"])
    df["pic_fiche"] = pd.cut(np.expm1(df["log_ratio_pic_journalier_fiche"]),
                             [-np.inf, 1, 3, 10, np.inf],
                             labels=["jusqu_a_1x", "1x_3x", "3x_10x", "plus_de_10x"])
    morceaux = []
    for var in ["etoiles", "has_photo", "texte", "avis_auteur", "photos_auteur", "profil",
                "rafale", "pic_fiche"]:
        t = taux(df.groupby(var, observed=True)).rename(columns={var: "valeur"})
        t.insert(0, "caracteristique", var)
        morceaux.append(t)
    return pd.concat(morceaux, ignore_index=True)


# ---------------------------------------------------------------------------
# 4. Ajustement
# ---------------------------------------------------------------------------

def ajuster(df: pd.DataFrame):
    """Régression logistique, marges groupées par établissement."""
    y = df["supprime"].astype(float)
    X = retirer_colonnes_trop_rares(matrice(df), y)
    res = sm.GLM(y, X, family=sm.families.Binomial()).fit(
        cov_type="cluster", cov_kwds={"groups": df["cid"].astype(str).factorize()[0]})
    ic = res.conf_int()
    tableau = pd.DataFrame({
        "risque_relatif": np.exp(res.params),
        "borne_basse": np.exp(ic[0]),
        "borne_haute": np.exp(ic[1]),
        "coefficient": res.params,
        "p_value": res.pvalues,
    })
    references = pd.DataFrame({"risque_relatif": 1.0, "borne_basse": 1.0,
                               "borne_haute": 1.0, "coefficient": 0.0, "p_value": np.nan},
                              index=list(REFERENCES.values()))
    tableau = pd.concat([tableau, references])
    tableau.index.name = "variable"
    return res, tableau


def ordonner(tableau: pd.DataFrame) -> pd.DataFrame:
    ordre = (["const"] + [f"etoiles_{i}" for i in range(1, 6)] + ["has_photo"]
             + [f"texte_{n}" for n in NOMS_TRANCHES_TEXTE]
             + ["log_rc", "log_photos_auteur", "guide_1_3", "guide_sans_niveau",
                "guide_4_et_plus", "log_burst",
                "log_ratio_pic_journalier_fiche"])
    return tableau.reindex([v for v in ordre if v in tableau.index])


# ---------------------------------------------------------------------------
# 5. Qualité : cinq tours par établissement
# ---------------------------------------------------------------------------

def cinq_tours(df: pd.DataFrame, nom: str):
    """Voir l'en-tête. Renvoie la cible et le score des avis notés."""
    tirage = np.random.default_rng(GRAINE)
    fiches = np.sort(df["cid"].astype(str).unique())
    tirage.shuffle(fiches)
    groupe = df["cid"].astype(str).map(
        pd.Series(np.arange(len(fiches)) % N_TOURS, index=fiches)).to_numpy()

    ys, scores = [], []
    for tour in range(N_TOURS):
        teste = groupe == tour
        ajustement = df[~teste]
        auteur_vu = df["author_key"].astype(str).isin(
            set(ajustement["author_key"].astype(str))).to_numpy()
        test = df[teste & ~auteur_vu]
        res, _ = ajuster(ajustement)
        X_test = matrice(test).reindex(columns=res.params.index, fill_value=0.0)
        scores.append(np.asarray(res.predict(X_test)))
        ys.append(test["supprime"].to_numpy())
        print(f"  tour {tour + 1} : {len(test):,} avis, {int(test['supprime'].sum()):,} "
              f"suppressions ; {int((teste & auteur_vu).sum()):,} avis écartés, "
              f"auteur déjà vu".replace(",", " "))
    return np.concatenate(ys), np.concatenate(scores)


def aire_sous_courbe(y, score) -> float:
    """Part des paires (avis supprimé, avis en ligne) où le supprimé a le score
    le plus haut. 0,5 = hasard, 1,0 = classement parfait."""
    y = np.asarray(y)
    n_pos, n_neg = int(y.sum()), int((1 - y).sum())
    rangs = pd.Series(np.asarray(score)).rank(method="average").to_numpy()
    return (rangs[y == 1].sum() - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg)


def justesse(y, score, n_groupes: int = 10) -> pd.DataFrame:
    """Avis rangés par score, 10 groupes de même taille : suppressions annoncées
    par le modèle et suppressions constatées."""
    t = pd.DataFrame({"score": np.asarray(score), "y": np.asarray(y)})
    t["groupe"] = pd.qcut(t["score"].rank(method="first"), n_groupes, labels=False) + 1
    r = t.groupby("groupe").agg(avis=("y", "size"), annoncees=("score", "sum"),
                                constatees=("y", "sum")).reset_index()
    r["annoncees"] = r["annoncees"].round(1)
    return r


def dessiner_ciblage(y, score, nom: str, auc: float) -> dict:
    """Courbe de ciblage : part des avis examinés, des plus risqués aux moins
    risqués, contre part des suppressions trouvées."""
    y_range = np.asarray(y)[np.argsort(-np.asarray(score), kind="stable")]
    part_avis = np.arange(1, len(y_range) + 1) / len(y_range)
    part_suppr = np.cumsum(y_range) / y_range.sum()
    reperes = {p: float(part_suppr[int(len(y_range) * p) - 1]) for p in (0.10, 0.20, 0.50)}

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.plot([0, 1], [0, 1], "--", color="grey", lw=1, label="tirage au hasard")
    ax.plot(part_avis, part_suppr, lw=2, label="modèle")
    for p, t in reperes.items():
        ax.plot(p, t, "o", color="black")
        ax.annotate(f"{p:.0%} des avis → {t:.0%} des suppressions", (p, t),
                    xytext=(8, -12), textcoords="offset points", fontsize=8)
    ax.set_xlabel("part des avis examinés, des plus risqués aux moins risqués")
    ax.set_ylabel("part des suppressions trouvées")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.02)
    effectifs = f"{len(y_range):,} avis / {int(y_range.sum()):,} suppressions".replace(",", " ")
    ax.set_title(f"10 {nom} — AUC {auc:.3f}\n{effectifs}")
    ax.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(SORTIES / f"10_ciblage_{nom}.png", dpi=150)
    plt.close(fig)
    return reperes


# ---------------------------------------------------------------------------
# Programme
# ---------------------------------------------------------------------------

def un_passage(df: pd.DataFrame, nom: str) -> pd.DataFrame:
    print("\n" + "=" * 78 + f"\n  PASSAGE {nom}\n" + "=" * 78)
    n_suppr = int(df["supprime"].sum())
    print(f"  {len(df):,} avis, {n_suppr:,} supprimés au plus tard au 8e jour, "
          f"{df['cid'].nunique():,} fiches".replace(",", " "))

    par_jour = taux(df.groupby("date_publication"))
    par_jour.to_csv(SORTIES / f"10_par_jour_{nom}.csv", index=False)
    print(f"\n--- par jour de publication ---\n{par_jour.to_string(index=False)}")

    croise = tableau_croise(df)
    croise.to_csv(SORTIES / f"10_croisements_{nom}.csv", index=False)
    print(f"\n--- chiffres bruts, sans modèle ---\n{croise.to_string(index=False)}")

    res, tableau = ajuster(df)
    tableau = ordonner(tableau)
    tableau.to_csv(SORTIES / f"10_effets_{nom}.csv")
    (SORTIES / f"10_summary_{nom}.txt").write_text(str(res.summary()), encoding="utf-8")
    print("\n--- effets, à autres caractéristiques égales ---")
    print(tableau[["risque_relatif", "borne_basse", "borne_haute"]]
          .drop(index="const").round(2).to_string())

    print("\n--- qualité, cinq tours par établissement ---")
    y, score = cinq_tours(df, nom)
    auc = aire_sous_courbe(y, score)
    just = justesse(y, score)
    just.to_csv(SORTIES / f"10_justesse_{nom}.csv", index=False)
    reperes = dessiner_ciblage(y, score, nom, auc)
    print(f"  AUC : {auc:.3f}")
    print("  ciblage : " + " ; ".join(f"{p:.0%} des avis → {t:.0%} des suppressions"
                                     for p, t in reperes.items()))
    print(f"  suppressions annoncées {just['annoncees'].sum():.0f}, "
          f"constatées {int(just['constatees'].sum())}")
    print(just.to_string(index=False))

    tableau.insert(0, "passage", nom)
    tableau["avis"] = len(df)
    tableau["suppressions"] = n_suppr
    tableau["auc"] = auc
    for p, t in reperes.items():
        tableau[f"suppressions_trouvees_dans_{int(p * 100)}pct_des_avis"] = t
    return tableau


def main() -> int:
    SORTIES.mkdir(parents=True, exist_ok=True)
    df = preparer(lire())

    passages = {}
    for region in ["US", "Europe"]:
        de_la_region = df["region"] == region
        if (de_la_region & df["enseigne_surveillee"]).any():
            passages[f"{region}_avec_enseignes"] = de_la_region
            passages[f"{region}_sans_enseignes"] = de_la_region & ~df["enseigne_surveillee"]
        else:
            print(f"[passages] {region} : aucun avis d'enseigne surveillée, un seul passage")
            passages[region] = de_la_region

    tableaux = [un_passage(df[garde].reset_index(drop=True), nom)
                for nom, garde in passages.items()]

    ensemble = pd.concat(tableaux)
    ensemble.to_csv(SORTIES / f"10_effets_{len(tableaux)}_passages.csv")
    cote_a_cote = (ensemble.drop(index="const").reset_index()
                   .pivot(index="variable", columns="passage", values="risque_relatif"))
    print("\n" + "=" * 78 + "\n  RISQUE RELATIF, PASSAGES CÔTE À CÔTE\n" + "=" * 78)
    print(ordonner(cote_a_cote).round(2).to_string())
    print(f"\n  fichiers écrits dans {SORTIES}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as erreur:
        print(f"\nARRÊT : {erreur}", file=sys.stderr)
        sys.exit(1)
