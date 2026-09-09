#!/usr/bin/env python3
"""
==============================================================================
Script : 06_statsmodels_analysis_review_claude.py
Objet  : Regression logistique sur les avis recents.

Perimetre : les avis qui ont moins de 3 mois lors de leur premiere vague de
suivi. Ils sont ensuite suivis sur toutes leurs vagues, y compris quand ils
depassent 3 mois d'age.

Unite comptee : une ligne = un avis a une vague ou il etait encore en ligne.
Tous les taux sont rapportes a ce nombre de lignes, jamais au nombre d'avis.

Ce que le script ne fait pas : inventer des donnees. Si BigQuery ne repond
pas, il s'arrete.
==============================================================================
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ----------------------------------------------------------------------------
# Reglages
# ----------------------------------------------------------------------------

PROJET = "client-divers"
DATASET = "reviewflowz"
CLE_JSON = "/home/romain/.gcp/client-divers-8b012e5b7c73.json"

SORTIES = Path(__file__).resolve().parent / "sorties"

# Age maximal, en jours, a la premiere vague du panel.
AGE_MAX_PREMIERE_VAGUE = 90

# Definition d'une fiche attaquee, pour le test de robustesse.
#
# L'ancien critere etait "plus de 5 % des avis perdus". Il melangeait trois
# situations sans rapport, verifiees fiche par fiche sur les 24 qu'il retenait :
#   - 2 fiches reellement attaquees (les salles de sport espagnoles) ;
#   - 1 fiche allemande qui perd un stock de vieux avis negatifs, ecrits sur
#     8 ans, mediane 3 ans, aucun de moins de 30 jours : un retrait demande,
#     pas une attaque ;
#   - 15 fiches qui perdent uniquement leurs avis 4 et 5 etoiles, surtout des
#     artisans americains, c'est-a-dire le phenomene meme que l'etude cherche
#     a documenter ;
#   - 6 fiches de moins de 25 avis, dont une a 2 avis qui atteignait le seuil
#     avec une seule suppression.
#
# Le critere retenu decrit la signature d'une attaque : beaucoup de
# suppressions, presque toutes sur des avis 1 etoile, et presque toutes sur des
# avis ecrits dans le mois. Il retient 4 fiches : les 2 salles de sport
# espagnoles (229 et 135 suppressions), plus Fox Rent A Car Denver et MedVet
# Cleveland (10 et 11 suppressions, 100 % a 1 etoile). Ces deux dernieres ont
# trop d'avis pour que l'ancien seuil en pourcentage les voie : 0,10 % et
# 0,74 % de leur stock. Il ecarte en revanche Bischoff Touristik, qui perd
# 48 avis negatifs ecrits sur 8 ans, mediane 3 ans, aucun de moins de 30
# jours : un retrait obtenu sur demande, pas une attaque.
MIN_SUPPRESSIONS_ATTAQUE = 10
PART_MIN_1_ETOILE = 0.8
PART_MIN_AVIS_RECENTS = 0.8

# Part des lignes non supprimees conservees pour l'ajustement du modele.
# La constante est corrigee ensuite, les autres coefficients ne bougent pas.
TAUX_ECHANTILLON_NEGATIFS = 0.05

# Part des etablissements mis de cote pour le test.
PART_TEST = 0.25

GRAINE = 20260909

# Secteurs representant moins de cette part des lignes : regroupes en "autres".
SEUIL_SECTEUR_RARE = 0.01

# Longueur du texte, en caracteres. Deciles observes sur les avis avec texte :
# 1, 24, 42, 61, 84, 113, 150, 205, 288, 466. Les seuils ci-dessous coupent
# a peu pres en trois tiers de la population qui ecrit quelque chose.
TRANCHES_TEXTE = [-1, 0, 50, 200, 10**6]
NOMS_TRANCHES_TEXTE = ["sans_texte", "texte_1_50", "texte_51_200", "texte_201p"]

TRANCHES_AGE = [-1, 3, 7, 14, 30, 60, 90, 10**6]
NOMS_TRANCHES_AGE = ["0-3j", "4-7j", "8-14j", "15-30j", "31-60j", "61-90j", "90j+"]

COLONNES_CATEGORIELLES = ["cid", "industry", "country", "bucket", "author_key"]

# ----------------------------------------------------------------------------
# Requetes
# ----------------------------------------------------------------------------

SQL_CONTROLE_DOUBLONS = f"""
SELECT
  COUNT(*)                                             AS lignes,
  COUNT(DISTINCT CONCAT(review_id, '|', CAST(wave AS STRING))) AS couples_avis_vague,
  COUNT(DISTINCT review_id)                            AS avis,
  COUNTIF(deleted = 1)                                 AS lignes_supprimees
FROM `{PROJET}.{DATASET}.avis_panel_final`
"""

SQL_FICHES_ATTAQUEES = f"""
SELECT
  cid,
  COUNT(DISTINCT review_id)                        AS n_avis,
  COUNTIF(deleted = 1)                             AS n_supprimes,
  SAFE_DIVIDE(COUNTIF(deleted = 1),
              COUNT(DISTINCT review_id))           AS part_perdue,
  SAFE_DIVIDE(COUNTIF(deleted = 1 AND star = 1),
              COUNTIF(deleted = 1))                AS part_1_etoile,
  SAFE_DIVIDE(COUNTIF(deleted = 1 AND age_days <= 30),
              COUNTIF(deleted = 1))                AS part_avis_recents
FROM `{PROJET}.{DATASET}.avis_panel_final`
GROUP BY cid
HAVING n_supprimes >= {MIN_SUPPRESSIONS_ATTAQUE}
   AND part_1_etoile >= {PART_MIN_1_ETOILE}
   AND part_avis_recents >= {PART_MIN_AVIS_RECENTS}
ORDER BY n_supprimes DESC
"""

# Ancien critere, calcule seulement pour garder la trace de l'ecart.
SQL_ANCIEN_CRITERE = f"""
SELECT
  COUNT(*) AS n_fiches,
  SUM(n_supprimes) AS n_supprimes
FROM (
  SELECT cid, COUNTIF(deleted = 1) AS n_supprimes
  FROM `{PROJET}.{DATASET}.avis_panel_final`
  GROUP BY cid
  HAVING SAFE_DIVIDE(COUNTIF(deleted = 1), COUNT(DISTINCT review_id)) > 0.05
)
"""

# Extraction du perimetre.
#   - premiere_vague : la premiere vague ou chaque avis apparait dans le panel.
#   - recents        : les avis dont l'age a cette premiere vague est < 3 mois.
#   - auteurs        : une seule ligne par avis, pour ne pas dupliquer le panel
#                      (les avis ressuscites ont plusieurs lignes dans reviews).
#   - QUALIFY        : ecarte les doublons (review_id, wave) issus de la
#                      jointure de 05_panel_final-v2.sql.
SQL_EXTRACTION = f"""
WITH premiere_vague AS (
  SELECT review_id, MIN(wave) AS wave_min
  FROM `{PROJET}.{DATASET}.avis_panel_final`
  GROUP BY review_id
),
recents AS (
  SELECT DISTINCT p.review_id
  FROM `{PROJET}.{DATASET}.avis_panel_final` p
  JOIN premiere_vague f
    ON p.review_id = f.review_id AND p.wave = f.wave_min
  WHERE p.age_days IS NOT NULL
    AND p.age_days < {AGE_MAX_PREMIERE_VAGUE}
),
auteurs AS (
  SELECT review_id, ANY_VALUE(review_link) AS review_link
  FROM `{PROJET}.{DATASET}.reviews`
  WHERE NOT is_update
  GROUP BY review_id
)
SELECT
  p.review_id,
  p.cid,
  p.wave,
  p.deleted,
  p.age_days,

  p.star,
  p.text_chars,
  p.has_photo,
  p.has_reply,

  p.log_rc,
  p.rc_zero,
  p.lg_level_missing,
  p.new_account,
  p.author_same_day_burst,

  p.langue_etrangere_au_pays,
  p.langue_minoritaire_sur_la_fiche,

  p.industry,
  p.country,
  p.bucket,

  p.log_ratio_pic_journalier_fiche,

  {{AUTHOR_KEY}}

FROM `{PROJET}.{DATASET}.avis_panel_final` p
JOIN recents USING (review_id)
{{JOINTURE_AUTEURS}}
QUALIFY ROW_NUMBER() OVER (PARTITION BY p.review_id, p.wave ORDER BY p.age_days) = 1
"""

# Depuis 04_avis_features-v3.sql, author_key est une colonne du panel. Avant
# cette version, il faut aller le chercher dans reviews, en ramenant d'abord
# la table a une ligne par avis (sinon la jointure duplique le panel).
AUTHOR_KEY_V3 = "p.author_key"
AUTHOR_KEY_V2 = ("CAST(FARM_FINGERPRINT(COALESCE(a.review_link, p.review_id)) "
                 "AS STRING) AS author_key")
JOINTURE_AUTEURS_V2 = "LEFT JOIN auteurs a USING (review_id)"

# ----------------------------------------------------------------------------
# Acces aux donnees
# ----------------------------------------------------------------------------


def client_bigquery():
    if CLE_JSON and os.path.exists(CLE_JSON):
        os.environ.setdefault("GOOGLE_APPLICATION_CREDENTIALS", CLE_JSON)
    from google.cloud import bigquery

    return bigquery.Client(project=PROJET)


def colonne_existe(client, table: str, colonne: str) -> bool:
    schema = client.get_table(f"{PROJET}.{DATASET}.{table}").schema
    return any(champ.name == colonne for champ in schema)


def cout_estime(client, sql: str) -> float:
    """Octets que la requete va lire, sans l'executer. Renvoie des Go."""
    from google.cloud import bigquery

    job = client.query(sql, job_config=bigquery.QueryJobConfig(dry_run=True))
    return job.total_bytes_processed / 1024**3


def lire(client, sql: str, libelle: str) -> pd.DataFrame:
    print(f"[{libelle}] lecture estimee : {cout_estime(client, sql):.2f} Go")
    table = client.query(sql).to_arrow(create_bqstorage_client=True)
    df = table.to_pandas(split_blocks=True, self_destruct=True)
    del table
    print(f"[{libelle}] {len(df):,} lignes recuperees".replace(",", " "))
    return df


def compacter(df: pd.DataFrame) -> pd.DataFrame:
    """Reduit la place prise en memoire sans changer les valeurs."""
    for col in COLONNES_CATEGORIELLES:
        if col in df.columns:
            df[col] = df[col].astype("category")
    for col in df.select_dtypes(include=["bool"]).columns:
        df[col] = df[col].astype("int8")
    for col in df.select_dtypes(include=["int64", "Int64"]).columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").astype("int32")
    for col in df.select_dtypes(include=["float64", "Float64"]).columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").astype("float32")
    place = df.memory_usage(deep=True).sum() / 1024**2
    print(f"[memoire] {place:,.0f} Mo".replace(",", " "))
    return df


# ----------------------------------------------------------------------------
# Preparation
# ----------------------------------------------------------------------------


def ajouter_variables(df: pd.DataFrame) -> pd.DataFrame:
    df["tranche_age"] = pd.cut(
        df["age_days"], bins=TRANCHES_AGE, labels=NOMS_TRANCHES_AGE
    )
    df["log_burst"] = np.log1p(df["author_same_day_burst"].fillna(1).clip(lower=0))

    # Profil de l'auteur en quatre situations qui ne se chevauchent pas.
    # rc_zero, lg_level_missing et new_account disaient la meme chose trois
    # fois : new_account vaut 1 exactement quand les deux autres valent 1. Mis
    # ensemble dans une regression, ils se partagent un seul effet et chaque
    # chiffre devient impossible a lire. Ici chaque avis tombe dans une case
    # et une seule, comparee aux comptes etablis.
    sans_avis = df["rc_zero"].astype(bool)
    sans_guide = df["lg_level_missing"].astype(bool)
    df["profil_auteur"] = np.select(
        [sans_avis & sans_guide, ~sans_avis & sans_guide, sans_avis & ~sans_guide],
        ["compte_vierge", "sans_statut_guide", "guide_sans_avis_declare"],
        default="guide_etabli",
    )
    df["profil_auteur"] = pd.Categorical(df["profil_auteur"])

    # Longueur du texte en tranches. has_text et log_text_chars disaient aussi
    # la meme chose : log_text_chars vaut 0 exactement quand has_text vaut 0.
    df["taille_texte"] = pd.cut(
        df["text_chars"].fillna(0).clip(lower=0),
        bins=TRANCHES_TEXTE, labels=NOMS_TRANCHES_TEXTE,
    )
    df["log_ratio_pic_journalier_fiche"] = (
        df["log_ratio_pic_journalier_fiche"].fillna(0).astype("float32")
    )
    df["star"] = df["star"].fillna(0).astype("int8")

    # Secteurs rares regroupes, sinon une poignee de lignes cree sa propre colonne.
    parts = df["industry"].value_counts(normalize=True, dropna=False)
    rares = parts[parts < SEUIL_SECTEUR_RARE].index
    df["secteur"] = (
        df["industry"].astype("object").where(~df["industry"].isin(rares), "autres")
    )
    df["secteur"] = df["secteur"].fillna("inconnu").astype("category")
    return df


VARIABLES_BINAIRES = [
    "has_photo",
    "has_reply",
    # Defectueuse : construite dans 04 par `language != LOWER(country)`, elle
    # compare un code de langue a un code de pays. Ca ne tombe juste que quand
    # les deux codes coincident (fr/FR, es/ES) et jamais ailleurs : 71 % des
    # avis americains sont comptes "etrangers" parce que 'en' n'est pas 'us',
    # 60 % des autrichiens parce que 'de' n'est pas 'at'. Comme aucune variable
    # de pays n'entre par ailleurs dans le modele, son coefficient absorbe un
    # effet pays. Gardee pour l'instant, a refaire avec une table pays -> langues
    # officielles avant toute citation.
    "langue_etrangere_au_pays",
    "langue_minoritaire_sur_la_fiche",
]

# log_rc reste dans le modele malgre profil_auteur : la variable a categories
# porte le saut entre "aucun avis declare" et "au moins un", log_rc porte la
# pente au-dela. Les deux ne mesurent pas la meme chose.
VARIABLES_CONTINUES = [
    "log_rc",
    "log_burst",
    "log_ratio_pic_journalier_fiche",
]

# Categorie servant de point de comparaison, sans colonne dans le modele.
REFERENCES = {
    "etoiles": "etoiles_5",
    "age": "age_0-3j",
    "profil": "profil_guide_etabli",
    "texte": "texte_sans_texte",
}


def matrice_modele(df: pd.DataFrame) -> pd.DataFrame:
    """Construit les colonnes d'entree du modele.

    Les variables a categories (etoiles, tranche d'age, secteur, taille) sont
    transformees en colonnes oui/non. Une categorie sert de reference et n'a
    pas de colonne : c'est le point de comparaison des autres.
    """
    morceaux = [df[VARIABLES_BINAIRES].astype("float32")]
    morceaux.append(df[VARIABLES_CONTINUES].astype("float32"))

    etoiles = pd.get_dummies(df["star"], prefix="etoiles", dtype="float32")
    etoiles = etoiles.drop(columns=[REFERENCES["etoiles"]], errors="ignore")
    morceaux.append(etoiles)

    age = pd.get_dummies(df["tranche_age"], prefix="age", dtype="float32")
    age = age.drop(columns=[REFERENCES["age"]], errors="ignore")
    morceaux.append(age)

    profil = pd.get_dummies(df["profil_auteur"], prefix="profil", dtype="float32")
    profil = profil.drop(columns=[REFERENCES["profil"]], errors="ignore")
    morceaux.append(profil)

    texte = pd.get_dummies(df["taille_texte"], prefix="texte", dtype="float32")
    texte = texte.drop(columns=[REFERENCES["texte"]], errors="ignore")
    morceaux.append(texte)

    secteur = pd.get_dummies(df["secteur"], prefix="secteur", drop_first=True,
                             dtype="float32")
    morceaux.append(secteur)

    taille = pd.get_dummies(df["bucket"], prefix="taille", drop_first=True,
                            dtype="float32")
    morceaux.append(taille)

    X = pd.concat(morceaux, axis=1)
    X = X.loc[:, X.sum(axis=0) > 0]  # colonnes toujours a zero : inutiles
    return sm.add_constant(X, has_constant="add")


# ----------------------------------------------------------------------------
# Tableau croise
# ----------------------------------------------------------------------------


def tableau_croise(df: pd.DataFrame) -> pd.DataFrame:
    """Taux de suppression par caracteristique, separe par tranche d'age.

    Denominateur de chaque taux : le nombre de lignes avis-vague du groupe.
    """
    lignes = []
    a_croiser = VARIABLES_BINAIRES + [
        "star", "bucket", "secteur", "profil_auteur", "taille_texte",
    ]
    for var in a_croiser:
        groupe = df.groupby(["tranche_age", var], observed=True)["deleted"].agg(
            ["sum", "size"]
        )
        for (tranche, valeur), row in groupe.iterrows():
            lignes.append(
                {
                    "caracteristique": var,
                    "valeur": valeur,
                    "tranche_age": tranche,
                    "lignes_avis_vague": int(row["size"]),
                    "suppressions": int(row["sum"]),
                    "taux_pour_10000_lignes": round(
                        row["sum"] / row["size"] * 10000, 2
                    ),
                }
            )
    return pd.DataFrame(lignes)


# ----------------------------------------------------------------------------
# Ajustement
# ----------------------------------------------------------------------------


def echantillonner(df: pd.DataFrame, taux: float, graine: int):
    """Garde toutes les suppressions et une part des lignes non supprimees."""
    if taux >= 1.0:
        return df, 1.0
    positifs = df[df["deleted"] == 1]
    negatifs = df[df["deleted"] == 0].sample(frac=taux, random_state=graine)
    echantillon = pd.concat([positifs, negatifs]).sort_index()
    return echantillon, taux


def ajuster(df: pd.DataFrame, libelle: str, taux_negatifs: float):
    ech, taux = echantillonner(df, taux_negatifs, GRAINE)
    y = ech["deleted"].astype("float64")
    X = matrice_modele(ech)

    modele = sm.GLM(y, X, family=sm.families.Binomial())
    res = modele.fit(cov_type="cluster", cov_kwds={"groups": ech["cid"].to_numpy()})

    params = res.params.copy()
    # Correction de la constante : on a garde toutes les suppressions mais
    # seulement une part des autres lignes, la frequence de base est faussee.
    if taux < 1.0:
        params["const"] = params["const"] + np.log(taux)

    ic = res.conf_int()
    basse, haute = ic[0].copy(), ic[1].copy()
    if taux < 1.0 and "const" in basse.index:
        basse["const"] += np.log(taux)
        haute["const"] += np.log(taux)

    tableau = pd.DataFrame(
        {
            "coefficient": params,
            "risque_relatif": np.exp(params),
            "borne_basse": np.exp(basse),
            "borne_haute": np.exp(haute),
            "p_value": res.pvalues,
        }
    )
    tableau.insert(0, "modele", libelle)
    print(f"\n[{libelle}] {len(ech):,} lignes ajustees, ".replace(",", " ")
          + f"{int(ech['deleted'].sum()):,} suppressions".replace(",", " "))
    return res, tableau, X.columns


# ----------------------------------------------------------------------------
# Controles de qualite
# ----------------------------------------------------------------------------


def corriger_probabilites(p, taux: float):
    """Remet les probabilites a l'echelle reelle.

    Le modele est ajuste sur toutes les suppressions mais seulement une part
    des autres lignes : il croit donc les suppressions bien plus frequentes
    qu'elles ne le sont. Meme correction que sur la constante, appliquee ici
    a chaque prevision."""
    if taux >= 1.0:
        return np.asarray(p, dtype="float64")
    p = np.clip(np.asarray(p, dtype="float64"), 1e-12, 1 - 1e-12)
    cote = np.log(p / (1 - p)) + np.log(taux)
    return 1 / (1 + np.exp(-cote))


def aire_sous_courbe(y, p) -> float:
    """AUC par la formule des rangs : probabilite qu'un avis supprime recoive
    un score plus eleve qu'un avis non supprime pris au hasard."""
    y = np.asarray(y)
    p = np.asarray(p, dtype="float64")
    n_pos, n_neg = int(y.sum()), int((1 - y).sum())
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    rangs = pd.Series(p).rank(method="average").to_numpy()
    return (rangs[y == 1].sum() - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg)


def decoupage(df: pd.DataFrame, graine: int):
    """Met de cote une part des etablissements. Les auteurs presents des deux
    cotes sont retires du test : sinon le modele reconnaitrait un auteur deja
    vu et le score serait flatte."""
    tirage = np.random.default_rng(graine)
    fiches = df["cid"].cat.remove_unused_categories().cat.categories.to_numpy()
    test_fiches = set(tirage.choice(fiches, size=int(len(fiches) * PART_TEST),
                                    replace=False))
    est_test = df["cid"].isin(test_fiches)

    auteurs_train = set(
        df.loc[~est_test, "author_key"].cat.remove_unused_categories()
        .cat.categories.to_numpy()
    )
    avant_filtre_auteur = int(est_test.sum())
    est_test = est_test & ~df["author_key"].isin(auteurs_train)
    retirees = avant_filtre_auteur - int(est_test.sum())
    print(f"  {len(test_fiches)} etablissements mis de cote ; {retirees:,} lignes"
          .replace(",", " ") + " retirees du test car leur auteur ecrit aussi"
          " sur un etablissement d'entrainement")
    return df[~est_test].copy(), df[est_test].copy()


def calibration(y, p, n_tranches: int = 10) -> pd.DataFrame:
    tranches = pd.qcut(pd.Series(p), n_tranches, duplicates="drop")
    tab = pd.DataFrame({"p": p, "y": np.asarray(y), "tranche": tranches})
    return tab.groupby("tranche", observed=True).agg(
        risque_prevu=("p", "mean"),
        risque_observe=("y", "mean"),
        lignes=("y", "size"),
    ).reset_index(drop=True)


# ----------------------------------------------------------------------------
# Programme
# ----------------------------------------------------------------------------


def main() -> int:
    SORTIES.mkdir(exist_ok=True)
    client = client_bigquery()

    print("=" * 78)
    print("  CONTROLE DU PANEL")
    print("=" * 78)
    ctrl = lire(client, SQL_CONTROLE_DOUBLONS, "controle").iloc[0]
    doublons = int(ctrl["lignes"]) - int(ctrl["couples_avis_vague"])
    for cle, val in ctrl.items():
        print(f"  {cle:<22} {int(val):,}".replace(",", " "))
    print(f"  {'doublons avis-vague':<22} {doublons:,}".replace(",", " "))
    if doublons:
        print("  -> ecartes a l'extraction ; defaut de jointure dans 05_panel_final-v2.sql")

    print("\n" + "=" * 78)
    print("  FICHES ATTAQUEES (>= 10 suppressions, >= 80 % a 1 etoile,")
    print("                    >= 80 % sur des avis ecrits dans le mois)")
    print("=" * 78)
    fiches = lire(client, SQL_FICHES_ATTAQUEES, "fiches attaquees")
    print(f"  {len(fiches)} fiches, {int(fiches['n_supprimes'].sum()):,} suppressions"
          .replace(",", " "))
    for _, f in fiches.iterrows():
        print(f"    {f['cid']}  {int(f['n_supprimes']):>4} suppressions, "
              f"{f['part_1_etoile']:.0%} a 1 etoile, "
              f"{f['part_avis_recents']:.0%} d'avis de moins de 30 jours")
    ancien = lire(client, SQL_ANCIEN_CRITERE, "ancien critere").iloc[0]
    print(f"  Pour memoire, l'ancien critere des 5 % retenait "
          f"{int(ancien['n_fiches'])} fiches et "
          f"{int(ancien['n_supprimes']):,} suppressions.".replace(",", " "))
    fiches.to_csv(SORTIES / "06_fiches_attaquees.csv", index=False)
    cids_attaques = set(fiches["cid"].astype(str))

    print("\n" + "=" * 78)
    print(f"  EXTRACTION : AVIS DE MOINS DE {AGE_MAX_PREMIERE_VAGUE} JOURS "
          "A LEUR PREMIERE VAGUE")
    print("=" * 78)
    if colonne_existe(client, "avis_panel_final", "author_key"):
        print("  author_key lu directement dans le panel (tables en v3)")
        sql = SQL_EXTRACTION.format(AUTHOR_KEY=AUTHOR_KEY_V3, JOINTURE_AUTEURS="")
    else:
        print("  author_key reconstruit depuis reviews (tables encore en v2)")
        sql = SQL_EXTRACTION.format(AUTHOR_KEY=AUTHOR_KEY_V2,
                                    JOINTURE_AUTEURS=JOINTURE_AUTEURS_V2)
    df = compacter(lire(client, sql, "panel recent"))
    df = ajouter_variables(df)

    n_avis = df["review_id"].nunique()
    n_suppr = int(df["deleted"].sum())
    print(f"  avis distincts        {n_avis:,}".replace(",", " "))
    print(f"  lignes avis-vague     {len(df):,}".replace(",", " "))
    print(f"  suppressions          {n_suppr:,}".replace(",", " "))
    print(f"  taux                  {n_suppr / len(df) * 10000:.2f} "
          "suppressions pour 10 000 lignes avis-vague")

    print("\n--- tableau croise par caracteristique et tranche d'age ---")
    croise = tableau_croise(df)
    croise.to_csv(SORTIES / "06_croisements_par_age.csv", index=False)
    print(f"  ecrit : {SORTIES / '06_croisements_par_age.csv'}")

    print("\n" + "=" * 78)
    print("  MODELES")
    print("=" * 78)
    res_complet, tab_complet, _ = ajuster(df, "complet", TAUX_ECHANTILLON_NEGATIFS)
    print(res_complet.summary())

    df_robuste = df[~df["cid"].isin(cids_attaques)]
    res_robuste, tab_robuste, _ = ajuster(df_robuste, "hors fiches attaquees",
                                          TAUX_ECHANTILLON_NEGATIFS)

    coefficients = pd.concat([tab_complet, tab_robuste])
    coefficients.index.name = "variable"
    coefficients.to_csv(SORTIES / "06_coefficients.csv")
    print(f"\n  ecrit : {SORTIES / '06_coefficients.csv'}")

    print("\n" + "=" * 78)
    print("  CONTROLE : LE MODELE SAIT-IL CLASSER, SES RISQUES SONT-ILS JUSTES")
    print("=" * 78)
    train, test = decoupage(df, GRAINE)
    print(f"  entrainement {len(train):,} lignes / test {len(test):,} lignes"
          .replace(",", " "))
    if len(test) < 1000 or test["deleted"].sum() < 20:
        print("  test trop petit ou sans suppression : AUC et calibration non")
        print("  calcules. Les coefficients ci-dessus restent valables.")
        return 0
    res_train, _, colonnes = ajuster(train, "entrainement", TAUX_ECHANTILLON_NEGATIFS)

    X_test = matrice_modele(test).reindex(columns=colonnes, fill_value=0.0)
    scores = corriger_probabilites(res_train.predict(X_test),
                                   TAUX_ECHANTILLON_NEGATIFS)
    auc = aire_sous_courbe(test["deleted"].to_numpy(), scores)
    print(f"  AUC sur le test : {auc:.3f}  "
          "(0,5 = tirage au hasard, 1,0 = classement parfait)")

    calib = calibration(test["deleted"].to_numpy(), scores)
    calib.to_csv(SORTIES / "06_calibration.csv", index=False)

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.plot([0, calib["risque_prevu"].max()], [0, calib["risque_prevu"].max()],
            "--", color="grey", linewidth=1, label="prevision juste")
    ax.plot(calib["risque_prevu"], calib["risque_observe"], "o-", color="#1f77b4",
            label="modele")
    ax.set_xlabel("risque annonce par le modele")
    ax.set_ylabel("part reellement supprimee")
    ax.set_title(f"Calibration sur les etablissements mis de cote (AUC {auc:.3f})")
    ax.legend()
    fig.tight_layout()
    fig.savefig(SORTIES / "06_calibration.png", dpi=150)
    plt.close(fig)
    print(f"  ecrit : {SORTIES / '06_calibration.png'}")

    print("\n" + "=" * 78)
    print("  A SAVOIR EN LISANT CES CHIFFRES")
    print("=" * 78)
    print("  - Denominateur : lignes avis-vague, pas nombre d'avis.")
    print("  - Les avis encore en ligne au dernier passage n'ont pas fini leur")
    print("    histoire : leur sort est inconnu, pas negatif.")
    print(f"  - Le modele robuste ecarte {len(fiches)} fiches attaquees, "
          f"{int(fiches['n_supprimes'].sum())} suppressions.")
    print("  - NE PAS LIRE langue_etrangere_au_pays comme un effet de langue.")
    print("    Elle compare un code de langue a un code de pays, ce qui ne")
    print("    coincide que par hasard : 71 % des avis americains y sont")
    print("    comptes etrangers parce que 'en' n'est pas 'us'. Elle mesure")
    print("    surtout 'etablissement americain'. A refaire avant citation.")
    print("  - first_seen_at n'est pas la date de publication pour les avis")
    print("    deja en ligne avant le 11 aout.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as erreur:
        print(f"\nARRET : {erreur}", file=sys.stderr)
        print("Aucun chiffre n'est produit sans acces reel a BigQuery.",
              file=sys.stderr)
        sys.exit(1)
