#!/usr/bin/env python3
"""
==============================================================================
Script : 07C_regression_reduite.py
Table source : client-divers.reviewflowz.reviews_panel_features_03B

Régression logistique réduite, demandée par Matthieu le 2026-09-28, sur le
panel 03B : 35 751 avis publiés du 4 au 17 août 2026, 1 355 suppressions.

Le 07B garde le modèle complet. Le 07C n'en garde que sept caractéristiques :

  1. la note, de 1 à 5 étoiles                        etoiles_1 … etoiles_4
  2. le pic d'avis sur la fiche le jour du dépôt      log_ratio_pic_journalier_fiche
  3. une photo jointe à l'avis                         has_photo
  4. le nombre de photos publiées par l'auteur         log_photos_auteur
  5. un auteur Local Guide de niveau 4 ou plus         guide_4_et_plus
  6. une réponse du propriétaire                       a_une_reponse
  7. le secteur                                        secteur_*

Le secteur suit la règle du 07B : les secteurs sous 1 % des avis du passage
sont regroupés en « autres ». Référence : automobile.

S'y ajoutent les contrôles d'exposition du 07B, obligatoires sur ce panel
(voir § 2 et § 3 de l'en-tête du 07B) : `age_a_la_premiere_observation_j`,
`fenetre_observation_j`, `vu_tardivement`. Et `region_US` dans les passages
qui mêlent les deux régions. Leurs coefficients ne se citent pas.

------------------------------------------------------------------------------
LES SIX PASSAGES
------------------------------------------------------------------------------
Trois périmètres, US, Europe, tous, chacun sur deux jeux de fiches :

  complet            tous les avis du périmètre
  sans_retraits      sans les 2 salles de sport espagnoles, repérées sur leur
                     `cid`, et sans TOUTES les fiches américaines de traitement
                     antiparasitaire

« Toutes les fiches antiparasitaires » est le repérage de la section 3 du
rapport (`etudes-ponctuelles/2026-09-18-antiparasitaire-home-services/
antiparasitaire.py`) : fiche américaine du secteur `home_services` dont le nom
porte le motif d'activité, ou l'enseigne ABC Home ajoutée à la main. C'est
plus large que le drapeau `chaine_antiparasitaire_us`, qui ne marque que les
quatre chaînes sur une égalité exacte de nom. Le repérage se fait dans
BigQuery ; le nom de la fiche n'est jamais rapatrié.

En Europe, `sans_retraits` ne retire que les deux salles.

------------------------------------------------------------------------------
LA RÉPONSE DU PROPRIÉTAIRE : À LIRE COMME UNE ASSOCIATION
------------------------------------------------------------------------------
`a_une_reponse` est l'état au dernier passage du robot : la veille de sa
disparition pour un avis supprimé, le 24 août pour un avis resté en ligne.
Choix de Matthieu du 2026-09-28, le même que celui de Romain pour le 09 le
2026-09-17.

Le 07B l'interdit en entrée, pour une raison qui vaut toujours : un avis qui
survit a plus de jours pour recevoir une réponse. Son risque relatif mêle donc
l'effet éventuel de la réponse et ce biais de survie, qui pousse vers une
protection apparente. Il ne mesure pas ce que la réponse protège. La mesure
à jalon fixe du 08B (section 6 du rapport) reste la référence sur ce point.

------------------------------------------------------------------------------
LECTURE DES RISQUES RELATIFS
------------------------------------------------------------------------------
  etoiles_*                  par rapport à 5 étoiles
  secteur_*                  par rapport à l'automobile
  guide_4_et_plus            par rapport à tous les autres auteurs, y compris
                             ceux sans niveau Local Guide
  has_photo, a_une_reponse   oui contre non
  log_photos_auteur          par cran de log(1 + photos), comme le 07B
  log_ratio_pic_...          par cran de log(1 + ratio), comme le 07B

Marges d'incertitude groupées par fiche, comme le 07B.

------------------------------------------------------------------------------
COMMANDE
------------------------------------------------------------------------------
  Sur la machine qui a BigQuery :
    nice -n 19 .venv/bin/python logistic-regression-study/python/07C_regression_reduite.py

  Sur un poste sans BigQuery, depuis la transposition locale du 03B :
    .venv/Scripts/python.exe logistic-regression-study/python/03B_features_local.py
    .venv/Scripts/python.exe logistic-regression-study/python/07C_regression_reduite.py --local

  Quand statsmodels ne se charge pas (scipy bloqué par la politique de
  sécurité de Windows), le script passe sur `glm_numpy.py`, qui fait le même
  calcul. Les deux substitutions ont été contrôlées le 2026-09-28 en rejouant
  le modèle complet du 07B (`03B_features_local_controle.py`) : coefficients
  retrouvés à 0,01 près au plus, sur `log_burst`, dont le socle local diffère
  de 1 560 avis.

Une seule lecture pour les six passages. Sorties dans
`output-study/<date>-sorties-07C/`, dont `07C_effets_6_passages.csv` qui
rassemble tout. Le fichier `07C_source.txt` dit d'où viennent les données et
quel moteur a ajusté les modèles.
==============================================================================
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

try:
    import statsmodels.api as sm
    MOTEUR = "statsmodels"
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import glm_numpy
    glm_numpy.installer()
    import statsmodels.api as sm
    MOTEUR = "glm_numpy (statsmodels indisponible sur ce poste)"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

PROJET = "client-divers"
DATASET = "reviewflowz"
TABLE = "reviews_panel_features_03B"
DOSSIER_CLES = Path("/home/romain/.gcp")

SORTIES = (Path(__file__).resolve().parent.parent / "output-study"
           / f"{date.today():%Y-%m-%d}-sorties-07C")

# Les deux salles de sport espagnoles attaquées, sur leur `cid` (décision du
# 2026-09-14). Le drapeau `salle_de_sport_attaquee` marque sur le nom.
CID_SALLES_ATTAQUEES = ("3163466139043001754", "10346942689164695031")

# Repérage de la section 3 du rapport, repris de `antiparasitaire.py`.
MOTIF_ACTIVITE = r"(?i)(pest|exterminat|termite|spidexx|mosquito|rodent|wildlife)"
MOTIF_INCLUSION_MANUELLE = r"(?i)abc home ?(&|and) ?commercial"

TABLE_LOCALE = (Path(__file__).resolve().parents[2] / "data" / "local"
                / "reviews_panel_features_03B.parquet")

SEUIL_VU_TARDIVEMENT = 8          # comme le 07B, § 3 de son en-tête
SEUIL_SECTEUR_RARE = 0.01         # idem
MIN_CAS_PAR_COLONNE = 30          # garde-fous du 07B
MIN_SUPPRESSIONS_PAR_COLONNE = 5
REFERENCE_ETOILES = "etoiles_5"
REFERENCE_SECTEUR = "secteur_automotive"

CARACTERISTIQUES = ["etoiles_1", "etoiles_2", "etoiles_3", "etoiles_4",
                    "log_ratio_pic_journalier_fiche", "has_photo",
                    "log_photos_auteur", "guide_4_et_plus", "a_une_reponse"]
CONTROLES = ["age_a_la_premiere_observation_j", "fenetre_observation_j",
             "vu_tardivement", "region_US"]

COLONNES_LUES = [
    "review_id", "cid", "region", "industry", "supprime",
    "star", "has_photo", "reviewer_photo_count", "palier_local_guide",
    "a_une_reponse", "log_ratio_pic_journalier_fiche",
    "age_a_la_premiere_observation_j", "fenetre_observation_j",
]


# ---------------------------------------------------------------------------
# Lecture
# ---------------------------------------------------------------------------

def trouver_cle() -> str | None:
    """La clé de service, quel que soit son nom de fichier (même mécanique que
    le 07B)."""
    if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        return None
    if not DOSSIER_CLES.is_dir():
        return None
    cles = sorted(DOSSIER_CLES.glob("*.json"))
    if len(cles) > 1:
        raise SystemExit(
            f"{len(cles)} clés dans {DOSSIER_CLES} : "
            f"{', '.join(c.name for c in cles)}.\n"
            f"Garder celle qui est active, ou poser "
            f"GOOGLE_APPLICATION_CREDENTIALS sur le bon fichier.")
    return str(cles[0]) if cles else None


def lire() -> pd.DataFrame:
    """Le panel entier, avec deux drapeaux calculés dans BigQuery."""
    cle = trouver_cle()
    if cle:
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = cle
        print(f"[auth] clé : {Path(cle).name}")
    from google.cloud import bigquery

    client = bigquery.Client(project=PROJET)
    salles = ", ".join(f"'{c}'" for c in CID_SALLES_ATTAQUEES)
    sql = f"""
        SELECT {', '.join('p.' + c for c in COLONNES_LUES)},
               CAST(p.cid AS STRING) IN ({salles}) AS salle_espagnole,
               COALESCE(b.country = 'US' AND b.industry = 'home_services'
                        AND (REGEXP_CONTAINS(b.name, r'{MOTIF_ACTIVITE}')
                             OR REGEXP_CONTAINS(b.name, r'{MOTIF_INCLUSION_MANUELLE}')),
                        FALSE) AS antiparasitaire_us
        FROM `{PROJET}.{DATASET}.{TABLE}` p
        LEFT JOIN `{PROJET}.{DATASET}.businesses` b ON b.cid = p.cid
    """
    estime = client.query(
        sql, job_config=bigquery.QueryJobConfig(dry_run=True)
    ).total_bytes_processed / 1024**2
    print(f"[lecture] {estime:.0f} Mo à lire")
    df = client.query(sql).to_dataframe()
    print(f"[lecture] {len(df):,} avis".replace(",", " "))
    if df["review_id"].duplicated().any():
        raise SystemExit("La jointure sur `businesses` a dupliqué des avis.")
    return df


def lire_local() -> pd.DataFrame:
    """La transposition locale du 03B, écrite par `03B_features_local.py`, qui
    porte déjà `antiparasitaire_us` avec le même repérage."""
    if not TABLE_LOCALE.exists():
        raise SystemExit(f"{TABLE_LOCALE} absent : lancer d'abord 03B_features_local.py")
    df = pd.read_parquet(TABLE_LOCALE, columns=COLONNES_LUES + ["antiparasitaire_us"])
    df["salle_espagnole"] = df["cid"].astype(str).isin(CID_SALLES_ATTAQUEES)
    print(f"[lecture] {TABLE_LOCALE.name} : {len(df):,} avis".replace(",", " "))
    return df


# ---------------------------------------------------------------------------
# Préparation
# ---------------------------------------------------------------------------

def preparer(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["supprime"] = df["supprime"].astype(int)
    df["cid"] = df["cid"].astype(str)
    for col in ["salle_espagnole", "antiparasitaire_us"]:
        df[col] = df[col].astype(bool)

    df["etoiles"] = "etoiles_" + df["star"].fillna(0).astype(int).astype(str)
    df["has_photo"] = df["has_photo"].fillna(False).astype(int)
    df["a_une_reponse"] = df["a_une_reponse"].fillna(False).astype(int)
    df["guide_4_et_plus"] = (df["palier_local_guide"] == "4_et_plus").astype(int)
    # Mêmes transformations que le 07B, pour que les deux modèles se comparent.
    df["log_photos_auteur"] = np.log1p(df["reviewer_photo_count"].fillna(0).clip(lower=0))
    df["log_ratio_pic_journalier_fiche"] = df["log_ratio_pic_journalier_fiche"].fillna(0)
    for col in ["age_a_la_premiere_observation_j", "fenetre_observation_j"]:
        df[col] = df[col].fillna(0).clip(lower=0).astype(float)
    df["vu_tardivement"] = (
        df["age_a_la_premiere_observation_j"] >= SEUIL_VU_TARDIVEMENT).astype(int)
    df["region_US"] = (df["region"] == "US").astype(int)
    df["industry"] = df["industry"].fillna("inconnu").astype(str)
    return df


def secteurs(df: pd.DataFrame) -> pd.Series:
    """Règle du 07B, appliquée à chaque passage : secteurs sous 1 % des avis du
    passage regroupés en « autres »."""
    parts = df["industry"].value_counts(normalize=True)
    rares = parts[parts < SEUIL_SECTEUR_RARE].index
    return "secteur_" + df["industry"].where(~df["industry"].isin(rares), "autres")


def matrice(df: pd.DataFrame, avec_region: bool) -> pd.DataFrame:
    etoiles = (pd.get_dummies(df["etoiles"], dtype=float)
               .drop(columns=[REFERENCE_ETOILES], errors="ignore"))
    etoiles = etoiles[[c for c in CARACTERISTIQUES if c in etoiles.columns]]
    secteur = (pd.get_dummies(df["secteur"], dtype=float)
               .drop(columns=[REFERENCE_SECTEUR], errors="ignore"))
    autres = [c for c in CARACTERISTIQUES if not c.startswith("etoiles_")]
    controles = [c for c in CONTROLES if avec_region or c != "region_US"]
    X = pd.concat([etoiles, df[autres].astype(float), secteur.sort_index(axis=1),
                   df[controles].astype(float)], axis=1)
    return sm.add_constant(X, has_constant="add")


def ecarter_colonnes_degenerees(X: pd.DataFrame, y: pd.Series) -> pd.DataFrame:
    """Garde-fou du 07B : une colonne oui/non trop rare, ou dont toutes les
    lignes à 1 ont le même sort, fait diverger l'ajustement."""
    a_jeter = []
    for col in X.columns:
        if col == "const" or X[col].nunique() > 2:
            continue
        masque = X[col] > 0
        n_suppr = int(y[masque].sum())
        if (masque.sum() < MIN_CAS_PAR_COLONNE or n_suppr < MIN_SUPPRESSIONS_PAR_COLONNE
                or n_suppr == int(masque.sum())):
            a_jeter.append(col)
    if a_jeter:
        print(f"  colonnes écartées, trop rares ou sans variation : {', '.join(a_jeter)}")
    return X.drop(columns=a_jeter)


# ---------------------------------------------------------------------------
# Un passage
# ---------------------------------------------------------------------------

def effectifs(df: pd.DataFrame) -> pd.DataFrame:
    """Avis et suppressions pour chaque caractéristique oui/non et chaque note,
    sans modèle. Sert à lire les effectifs derrière chaque risque relatif."""
    lignes = []
    for var in ["etoiles", "has_photo", "guide_4_et_plus", "a_une_reponse",
                "secteur", "vu_tardivement", "region"]:
        g = df.groupby(var, observed=True)["supprime"].agg(["sum", "size"])
        for valeur, row in g.iterrows():
            lignes.append({"caracteristique": var, "valeur": valeur,
                           "avis": int(row["size"]), "suppressions": int(row["sum"]),
                           "taux_pour_10000_avis": round(row["sum"] / row["size"] * 1e4, 1)})
    return pd.DataFrame(lignes)


def un_passage(df: pd.DataFrame, nom: str) -> pd.DataFrame:
    df = df.assign(secteur=secteurs(df))
    y = df["supprime"].astype(float)
    avec_region = df["region"].nunique() > 1
    X = ecarter_colonnes_degenerees(matrice(df, avec_region), y)
    res = sm.GLM(y, X, family=sm.families.Binomial()).fit(
        cov_type="cluster", cov_kwds={"groups": df["cid"].factorize()[0]})

    ic = res.conf_int()
    tableau = pd.DataFrame({
        "coefficient": res.params, "std_err": res.bse,
        "risque_relatif": np.exp(res.params),
        "borne_basse": np.exp(ic[0]), "borne_haute": np.exp(ic[1]),
        "p_value": res.pvalues,
    })
    for reference in [REFERENCE_ETOILES, REFERENCE_SECTEUR]:
        tableau.loc[reference] = [0.0, np.nan, 1.0, 1.0, 1.0, np.nan]
    tableau["role"] = ["controle" if v in CONTROLES or v == "const" else "resultat"
                       for v in tableau.index]
    tableau.index.name = "variable"
    colonnes_secteur = sorted(v for v in tableau.index
                              if v.startswith("secteur_") and v != REFERENCE_SECTEUR)
    ordre = (["const", REFERENCE_ETOILES] + CARACTERISTIQUES
             + [REFERENCE_SECTEUR] + colonnes_secteur + CONTROLES)
    tableau = tableau.reindex([v for v in ordre if v in tableau.index])

    tableau.to_csv(SORTIES / f"07C_coefficients_{nom}.csv")
    effectifs(df).to_csv(SORTIES / f"07C_effectifs_{nom}.csv", index=False)
    (SORTIES / f"07C_summary_{nom}.txt").write_text(
        f"Passage : {nom}\n"
        f"{len(df)} avis, {int(y.sum())} suppressions, {df['cid'].nunique()} fiches\n"
        "a_une_reponse : état au dernier passage du robot, à lire comme une\n"
        "association (biais de survie), voir l'en-tête du script.\n"
        "age_a_la_premiere_observation_j, fenetre_observation_j, vu_tardivement\n"
        "et region_US sont des contrôles, pas des résultats.\n\n"
        + str(res.summary()), encoding="utf-8")

    print(f"\n[{nom}] {len(df):,} avis, {int(y.sum()):,} suppressions, "
          f"{df['cid'].nunique():,} fiches".replace(",", " "))
    print(tableau.loc[tableau["role"] == "resultat",
                      ["risque_relatif", "borne_basse", "borne_haute", "p_value"]]
          .round(3).to_string())

    tableau = tableau.reset_index()
    tableau.insert(0, "passage", nom)
    tableau.insert(1, "avis", len(df))
    tableau.insert(2, "suppressions", int(y.sum()))
    tableau.insert(3, "fiches", df["cid"].nunique())
    return tableau


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Régression réduite sur le panel 03B, six passages.")
    ap.add_argument("--local", action="store_true",
                    help="lit data/local/reviews_panel_features_03B.parquet au lieu de BigQuery")
    args = ap.parse_args()

    SORTIES.mkdir(parents=True, exist_ok=True)
    source = (f"transposition locale {TABLE_LOCALE.name} (03B_features_local.py)"
              if args.local else f"BigQuery {PROJET}.{DATASET}.{TABLE}")
    (SORTIES / "07C_source.txt").write_text(
        f"Données : {source}\nMoteur : {MOTEUR}\n", encoding="utf-8")
    print(f"[source] {source}\n[moteur] {MOTEUR}")
    df = preparer(lire_local() if args.local else lire())

    retire = df["salle_espagnole"] | df["antiparasitaire_us"]
    bilan, tableaux = [], []
    for region in ["US", "Europe", "tous"]:
        base = df if region == "tous" else df[df["region"] == region]
        for jeu, garde in [("complet", pd.Series(True, index=base.index)),
                           ("sans_retraits", ~retire.loc[base.index])]:
            sous = base[garde]
            bilan.append({
                "passage": f"{region}_{jeu}",
                "avis": len(sous), "suppressions": int(sous["supprime"].sum()),
                "fiches": sous["cid"].nunique(),
                "avis_retires": int((~garde).sum()),
                "suppressions_retirees": int(base.loc[~garde, "supprime"].sum()),
                "fiches_salles_retirees": base.loc[~garde & base["salle_espagnole"], "cid"].nunique(),
                "fiches_antiparasitaires_retirees":
                    base.loc[~garde & base["antiparasitaire_us"], "cid"].nunique(),
            })
            tableaux.append(un_passage(sous, f"{region}_{jeu}"))

    effets = pd.concat(tableaux, ignore_index=True)
    effets.to_csv(SORTIES / "07C_effets_6_passages.csv", index=False)
    pd.DataFrame(bilan).to_csv(SORTIES / "07C_passages.csv", index=False)
    print(f"\nécrit : 07C_effets_6_passages.csv, 07C_passages.csv dans {SORTIES}")
    print(pd.DataFrame(bilan).to_string(index=False))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as erreur:
        print(f"\nARRÊT : {erreur}", file=sys.stderr)
        sys.exit(1)
