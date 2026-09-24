#!/usr/bin/env python3
"""
==============================================================================
Script : 08B_effet_reponse_commercant.py
Table source : client-divers.reviewflowz.reviews_panel_features_03B

Adaptation de `08_effet_reponse_commercant.py` à la nouvelle chaîne de tables,
écrite le 2026-09-21. Le `08` n'est pas modifié : il continue de lire
`reviews_panel_features_03` et ses sorties du 17 septembre restent rejouables.

Répondre vite à un avis le protège-t-il ?

Ce script ne remplace pas `07B_regression_panel.py`, il répond à une autre
question. `07B` mesure l'effet d'une réponse arrivée avant la première
observation, sur tout le panel. Ici on mesure l'effet de répondre dans les deux
jours qui suivent la publication, sur les seuls avis dont on a vu la naissance.

------------------------------------------------------------------------------
CE QUI CHANGE PAR RAPPORT AU 08
------------------------------------------------------------------------------

1. LA POPULATION SE SÉLECTIONNE AUTREMENT, ET TOMBE AU MÊME ENDROIT

   `age_a_la_vague1_j <= 1` n'existe plus. Le critère devient
   `age_a_la_premiere_observation_j <= 1` : le robot a vu l'avis le jour de sa
   publication ou le lendemain, donc son état au jalon du 2e jour est connu.

   Mesuré le 2026-09-21, ce critère retient exactement les avis publiés du
   10 au 17 août, 19 874 en tout. Les avis publiés du 4 au 9 août ont tous été
   vus pour la première fois le 11, jour de l'arrivée du robot, donc un âge à
   la première observation de 2 à 7 jours : ils sortent d'eux-mêmes.

2. LES AVIS DU 17 AOÛT SONT ÉCARTÉS, FAUTE DE HUIT JOURS D'OBSERVATION

   L'ancien panel s'arrêtait au 16 août et tous ses avis atteignaient leur
   8e jour avant le dernier passage du robot. Le panel 03B va jusqu'au 17, et
   un avis du 17 n'est suivi que sept jours.

   Le script mesure donc, pour chaque avis, le nombre de jours écoulés entre sa
   publication et le dernier passage, et écarte ceux qui n'atteignent pas
   `jalon + fenetre` jours. Avec les réglages par défaut, cela retire les
   2 401 avis du 17 août et en laisse 17 473.

     publié le 10   2 436 avis   14 jours observables
     publié le 11   2 539 avis   13 jours
     publié le 12   2 427 avis   12 jours
     publié le 13   2 679 avis   11 jours
     publié le 14   2 777 avis   10 jours
     publié le 15   2 418 avis    9 jours
     publié le 16   2 197 avis    8 jours
     publié le 17   2 401 avis    7 jours   -> écartés

   L'ancien passage travaillait sur 17 735 avis. L'écart avec les 17 473 d'ici
   tient à la sélection, et c'est une correction.

   `age_a_la_vague1_j` mesurait l'âge de l'avis au 11 août, date d'arrivée du
   robot. `age_a_la_premiere_observation_j` mesure son âge le jour où le robot
   l'a VRAIMENT VU. Un avis publié le 10 août mais découvert le 18 vaut 1 pour
   la première et 8 pour la seconde.

   Les 268 avis que le `08` gardait et que celui-ci écarte sont tous dans la
   table `03B` : ils sortent parce que le robot ne les avait pas encore vus au
   moment où l'ancien critère les déclarait observables.

     vus au 8e jour ou après   176 avis   âge de 8 à 13 jours
     vus du 2e au 7e jour       92 avis   âge de 2 à 7 jours

   Le `08` leur attribuait donc une survie entre le 3e et le 8e jour que
   personne n'avait observée. Ces 268 avis ne portent que 3 suppressions, donc
   la correction ne déplace pas le résultat — mais elle est réelle.

3. CE QUI NE CHANGE PAS

   Le montage à jalon fixe, les références, les tranches d'habitude de réponse,
   les garde-fous, le calcul de l'effet minimal détectable et les trois
   variantes en ligne de commande sont repris du `08` sans retouche.

------------------------------------------------------------------------------
LE MONTAGE, ET LE PROBLÈME QU'IL RÈGLE
------------------------------------------------------------------------------
Le problème. « Cet avis a une réponse » se lit facilement comme « le commerçant
l'a protégé ». Mais un avis qui a survécu trois semaines a eu trois semaines
pour recevoir une réponse, et un avis supprimé au troisième jour n'en a eu que
trois. Compter les réponses à la fin de l'histoire revient donc en partie à
compter qui a survécu. C'est ce défaut qui donnait « répondre protège 3,7 fois »
dans l'analyse B.

La solution, en une image. Au lieu de demander à la fin de la course qui portait
un casque, on photographie tous les coureurs au deuxième kilomètre, on note qui
porte un casque à cet instant précis, puis on regarde qui tombe ensuite. Personne
ne peut plus enfiler un casque après sa chute.

Traduit en données :

    jour 0        jour 2                      jour 8
    |-------------|---------------------------|
    publication   JALON                       fin de la fenêtre
                  - tout le monde est encore   on compte qui a
                    en ligne                   disparu entre le
                  - on note qui a déjà une     3e et le 8e jour
                    réponse

Trois conséquences, toutes voulues :

  1. Un avis supprimé avant le jalon sort de l'étude. Il n'apprend rien sur ce
     qui se passe après le jalon.
  2. La réponse est connue AVANT la période de risque. Elle ne peut pas être une
     conséquence de la survie pendant cette période.
  3. L'âge n'a pas à entrer dans le modèle. Tous les avis sont au même âge au
     jalon, et la fenêtre de risque a la même durée pour tous. C'est ce qui
     distingue ce script de `07B`, où deux contrôles d'exposition sont
     indispensables.

     C'est aussi pourquoi `fenetre_observation_j`, la colonne ajoutée au `07B`,
     n'a rien à faire ici : le montage égalise l'exposition au lieu de la
     corriger.

------------------------------------------------------------------------------
HABITUDE DE RÉPONSE DE LA FICHE
------------------------------------------------------------------------------
`taux_reponse_fiche_avant_vague1`, part des avis de la fiche publiés du
2025-08-11 au 2026-08-03 qui portaient une réponse avant le 11 août, en quatre
tranches : moins de 25 % (référence), 25 à 75 %, plus de 75 %, historique
insuffisant (moins de 10 avis).

Pourquoi : un propriétaire qui lit ses avis chaque jour répond vite ET signale
les avis qu'il juge faux. Sans cette variable, « avoir une réponse » peut
mesurer « être sur une fiche surveillée ». Avec elle, on compare un avis répondu
et un avis non répondu sur des fiches qui ont la même habitude.

`--reponse-par-habitude` mesure l'effet de la réponse séparément dans chaque
tranche d'habitude : la variable `reponse_au_jalon` y est remplacée par une
colonne par tranche. `--sans-habitude` refait le passage sans elle, pour voir de
combien l'effet de la réponse bouge.

------------------------------------------------------------------------------
POURQUOI `delai_reponse_j` EST UTILISÉE ICI ALORS QUE `07B` L'INTERDIT
------------------------------------------------------------------------------
`07B` l'interdit parce qu'elle n'est connue que pour un avis ayant vécu assez
longtemps pour recevoir sa réponse : s'en servir sur tout le panel ferait entrer
l'issue dans les entrées.

Ici elle ne sert qu'à répondre à une question posée sur des avis TOUS VIVANTS au
jalon : « la réponse était-elle là au jour 2 ? ». Pour ces avis, `delai <= 2`
signifie qu'elle y était, et `delai > 2` ou vide qu'elle n'y était pas. Une
réponse qui serait arrivée après une suppression n'est jamais observée, mais elle
tombe du bon côté de toute façon : elle n'était pas là au jalon.

------------------------------------------------------------------------------
CE QUE CE SCRIPT NE PEUT PAS DIRE
------------------------------------------------------------------------------
  - Une réponse RETIRÉE est invisible. `changed_fields` ne contient que `star` et
    `text`, jamais `reply`. Un avis dont la réponse a été effacée avant le dernier
    passage est compté « sans réponse ».
  - Le sens de la causalité. Le commerçant qui répond est souvent celui qui
    signale. Une réponse peut marquer une contestation en cours plutôt qu'une
    protection. Aucun modèle ne tranche cela avec ces données.
  - Un résultat non significatif ne dit pas « répondre ne sert à rien ». Le
    script imprime pour cela l'effet minimal qu'il était capable de détecter.
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
import statsmodels.api as sm

# La console Windows écrit en cp1252 et s'arrête sur les caractères que ce
# script imprime. Sur Linux, où tourne le 08, ces deux lignes ne changent rien.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

PROJET = "client-divers"
DATASET = "reviewflowz"
TABLE = "reviews_panel_features_03B"
TABLE_ENSEIGNES = "biz_surveillance"
# Dossier des clés de service, pas un fichier précis : le nom change à chaque
# rotation. Même résolution que dans `07_regression_panel.py`, voir `trouver_cle`.
DOSSIER_CLES = Path("/home/romain/.gcp")

# Les sorties vont dans `output-study/`, pas dans `python/`. Voir le commentaire
# équivalent dans `07_regression_panel.py`.
SORTIES = (Path(__file__).resolve().parent.parent / "output-study"
           / f"{date.today():%Y-%m-%d}-sorties-08B")

# Reprises de 07, pour que les deux scripts découpent pareil.
TRANCHES_TEXTE = [-1, 0, 50, 200, 10**6]
NOMS_TRANCHES_TEXTE = ["sans_texte", "texte_1_50", "texte_51_200", "texte_201p"]
SEUIL_SECTEUR_RARE = 0.01
MIN_CAS_PAR_COLONNE = 30
MIN_SUPPRESSIONS_PAR_COLONNE = 5

# Âge, en jours, au-delà duquel on considère que la naissance de l'avis n'a pas
# été observée. À 1, le robot l'a vu le jour même ou le lendemain, et son état
# au jalon du 2e jour est connu. Voir le § 1 de l'en-tête.
SEUIL_PREMIERE_OBSERVATION = 1

REFERENCES = {
    "etoiles": "etoiles_5",
    "profil": "guide_1_3",
    "habitude": "habitude_moins_de_25",
    "texte": "texte_sans_texte",
    "taille": "taille_mono",
}

# Somme des quantiles normaux pour un test bilatéral à 5 % et une puissance de
# 80 %. Sert au calcul de l'effet minimal détectable.
Z_TEST_PLUS_Z_PUISSANCE = 1.959964 + 0.841621

COLONNES = [
    "review_id", "cid", "author_key",
    "supprime", "age_a_la_suppression_j",
    # Remplacent `age_a_la_vague1_j`. La première sélectionne la population,
    # la seconde sert à calculer combien de jours l'avis a pu être observé
    # depuis sa publication. Voir les § 1 et 2 de l'en-tête.
    "age_a_la_premiere_observation_j", "fenetre_observation_j",
    "created_at_day",
    "delai_reponse_j",
    "star", "has_text", "text_chars", "has_photo",
    "reviewer_review_count", "log_rc", "palier_local_guide", "reviewer_photo_count",
    "n_avis_meme_jour_auteur",
    "langue_minoritaire_sur_la_fiche",
    "industry", "bucket", "region",
    "log_ratio_pic_journalier_fiche",
    "taux_reponse_fiche_avant_vague1",
]

VARIABLES_BINAIRES = [
    # La variable de l'étude. Elle est en tête pour être lue en premier dans
    # toutes les sorties.
    "reponse_au_jalon",
    "has_photo",
    "langue_minoritaire_sur_la_fiche",
]

VARIABLES_CONTINUES = [
    "log_rc",
    "log_photos_auteur",
    "log_burst",
    "log_ratio_pic_journalier_fiche",
]

# Habitude de réponse de la fiche, en tranches. Seuils fixés le 2026-09-17 sur
# l'ancien panel : 8 853 avis sur des fiches à plus de 75 %, 5 418 à moins de
# 25 %, 3 170 entre les deux, 294 sans historique. Repris tels quels ici ; la
# répartition obtenue sur 03B est imprimée par le tableau croisé.
TRANCHES_HABITUDE = [-0.001, 0.25, 0.75, 1.0]
NOMS_TRANCHES_HABITUDE = ["habitude_moins_de_25", "habitude_25_75", "habitude_plus_de_75"]


# ---------------------------------------------------------------------------
# Lecture
# ---------------------------------------------------------------------------

def trouver_cle() -> str | None:
    """La clé de service, quel que soit son nom de fichier.

    `GOOGLE_APPLICATION_CREDENTIALS` l'emporte s'il est posé. Sinon on prend le
    seul `.json` de DOSSIER_CLES, et on s'arrête s'il y en a plusieurs : une
    rotation en cours ferait choisir la mauvaise, avec une erreur de droits
    illisible à l'arrivée.
    """
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


def client_bigquery():
    cle = trouver_cle()
    if cle:
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = cle
        print(f"[auth] clé : {Path(cle).name}")
    from google.cloud import bigquery

    return bigquery.Client(project=PROJET)


def lire(client) -> pd.DataFrame:
    """Charge les avis vus dès leur publication, avec le repère des enseignes.

    Le critère est `age_a_la_premiere_observation_j <= 1` : le robot a vu l'avis
    le jour de sa publication ou le lendemain, donc son état au jalon du 2e jour
    est connu. Voir le § 1 de l'en-tête.

    `jours_observables` est ajoutée ici plutôt qu'en SQL, pour que la formule
    soit lisible à côté du filtre qui s'en sert :

        fenetre_observation_j          = dernier passage − première observation
        age_a_la_premiere_observation_j = première observation − publication

    Leur somme est donc le nombre de jours entre la publication et le dernier
    passage du robot, c'est-à-dire la durée pendant laquelle cet avis pouvait
    être vu disparaître depuis sa naissance.
    """
    sql = (f"SELECT {', '.join('p.' + c for c in COLONNES)}, "
           f"s.cid IS NOT NULL AS enseigne_surveillee "
           f"FROM `{PROJET}.{DATASET}.{TABLE}` p "
           f"LEFT JOIN `{PROJET}.{DATASET}.{TABLE_ENSEIGNES}` s ON s.cid = p.cid "
           f"WHERE p.age_a_la_premiere_observation_j <= "
           f"{SEUIL_PREMIERE_OBSERVATION}")
    df = client.query(sql).to_arrow(create_bqstorage_client=True).to_pandas()
    df["jours_observables"] = (df["fenetre_observation_j"]
                               + df["age_a_la_premiere_observation_j"])
    print(f"[lecture] {len(df):,} avis vus dans les "
          f"{SEUIL_PREMIERE_OBSERVATION} jour(s) suivant leur publication, "
          f"publiés du {df['created_at_day'].min():%d/%m} au "
          f"{df['created_at_day'].max():%d/%m}".replace(",", " "))
    return df


def ecarter_trop_recents(df: pd.DataFrame, jalon: int, fenetre: int) -> pd.DataFrame:
    """Retire les avis publiés trop tard pour être suivis jusqu'au bout.

    Le panel 03B va jusqu'au 17 août, et un avis du 17 n'est suivi que sept
    jours. Le garder reviendrait à compter « non supprimé » un avis dont on n'a
    pas vu la fin de la fenêtre de risque. L'ancien panel s'arrêtant au 16, le
    `08` n'avait pas ce cas à traiter. Voir le § 2 de l'en-tête.
    """
    garde = df["jours_observables"] >= jalon + fenetre
    ecartes = df[~garde]
    if len(ecartes):
        par_jour = (ecartes.groupby("created_at_day").size()
                    .sort_index().items())
        print(f"[fenêtre] {len(ecartes):,} avis publiés trop tard pour être "
              f"suivis {jalon + fenetre} jours, écartés :".replace(",", " ")
              + " " + ", ".join(f"{n:,} le {d:%d/%m}".replace(",", " ")
                                for d, n in par_jour))
    print(f"[fenêtre] {int(garde.sum()):,} avis retenus, publiés du "
          f"{df.loc[garde, 'created_at_day'].min():%d/%m} au "
          f"{df.loc[garde, 'created_at_day'].max():%d/%m}".replace(",", " "))
    return df[garde].copy()


# ---------------------------------------------------------------------------
# Le jalon
# ---------------------------------------------------------------------------

def appliquer_jalon(df: pd.DataFrame, jalon: int, fenetre: int) -> pd.DataFrame:
    """Garde les avis encore en ligne au jalon, et pose la cible.

    `jalon`   : âge en jours à partir duquel on observe. Défaut 2.
    `fenetre` : durée d'observation après le jalon, en jours. Défaut 6, ce qui
                mène au 8e jour de vie.

    Trois colonnes en sortent :
      reponse_au_jalon  la réponse était là au jalon
      supprime_fenetre  la cible : disparu entre jalon+1 et jalon+fenetre
      vivant_au_jalon   sert au filtrage, retiré ensuite
    """
    df = df.copy()
    age_mort = df["age_a_la_suppression_j"]

    # Encore en ligne au jalon : jamais supprimé, ou supprimé plus tard.
    vivant = (~df["supprime"].astype(bool)) | (age_mort > jalon)
    perdus = int((~vivant).sum())

    df = df[vivant].copy()

    # Supprimés après la fenêtre : retirés du corpus (décision du 2026-09-17).
    tardif = df["supprime"].astype(bool) & (df["age_a_la_suppression_j"] > jalon + fenetre)
    df = df[~tardif].copy()

    # La réponse était-elle publiée au jalon ? `delai_reponse_j` vide = pas de
    # réponse connue, donc pas de réponse au jalon.
    df["reponse_au_jalon"] = (
        df["delai_reponse_j"].notna() & (df["delai_reponse_j"] <= jalon)
    ).astype("int8")

    # La cible. Un avis supprimé APRÈS la fenêtre compte comme resté en ligne :
    # la question porte sur ces jours-là, pas sur la suite.
    df["supprime_fenetre"] = (
        df["supprime"].astype(bool)
        & df["age_a_la_suppression_j"].between(jalon + 1, jalon + fenetre)
    ).astype("int8")

    print(f"[jalon] jour {jalon}, fenêtre de {fenetre} jours "
          f"(soit jusqu'au {jalon + fenetre}e jour de vie)")
    print(f"  {perdus:,} avis perdus avant le jalon, écartés".replace(",", " "))
    print(f"  {int(tardif.sum()):,} avis supprimés après le {jalon + fenetre}e jour, "
          f"retirés".replace(",", " "))
    print(f"  {len(df):,} avis au jalon — c'est le dénominateur".replace(",", " "))
    print(f"  {int(df['reponse_au_jalon'].sum()):,} avec une réponse "
          f"({df['reponse_au_jalon'].mean():.1%})".replace(",", " "))
    print(f"  {int(df['supprime_fenetre'].sum()):,} supprimés dans la fenêtre"
          .replace(",", " "))
    return df


def ajouter_variables(df: pd.DataFrame) -> pd.DataFrame:
    """Mêmes découpages que 07, pour que les deux scripts se comparent."""
    df = df.copy()
    df["taille_texte"] = pd.cut(
        df["text_chars"].fillna(0).clip(lower=0),
        bins=TRANCHES_TEXTE, labels=NOMS_TRANCHES_TEXTE)
    df["log_burst"] = np.log1p(df["n_avis_meme_jour_auteur"].fillna(1).clip(lower=0))
    df["log_photos_auteur"] = np.log1p(df["reviewer_photo_count"].fillna(0).clip(lower=0))
    df["log_ratio_pic_journalier_fiche"] = (
        df["log_ratio_pic_journalier_fiche"].fillna(0).astype("float32"))
    habitude = pd.cut(df["taux_reponse_fiche_avant_vague1"],
                      bins=TRANCHES_HABITUDE, labels=NOMS_TRANCHES_HABITUDE)
    df["habitude_reponse_fiche"] = (habitude.astype("object")
                                    .fillna("habitude_historique_insuffisant"))
    df["star"] = df["star"].fillna(0).astype("int8")
    for col in ["has_photo", "langue_minoritaire_sur_la_fiche"]:
        df[col] = df[col].fillna(0).astype("int8")

    parts = df["industry"].value_counts(normalize=True, dropna=False)
    rares = parts[parts < SEUIL_SECTEUR_RARE].index
    secteur = df["industry"].astype("object").where(~df["industry"].isin(rares), "autres")
    df["secteur"] = secteur.fillna("inconnu").astype("category")
    return df


# ---------------------------------------------------------------------------
# Ajustement
# ---------------------------------------------------------------------------

def matrice_modele(df: pd.DataFrame, avec_region: bool, avec_habitude: bool = True,
                   reponse_par_habitude: bool = False) -> pd.DataFrame:
    morceaux = [df[VARIABLES_BINAIRES].astype("float32"),
                df[VARIABLES_CONTINUES].astype("float32")]

    def dummies(serie, prefixe, reference=None):
        d = pd.get_dummies(serie, prefix=prefixe, dtype="float32")
        if reference:
            d = d.drop(columns=[reference], errors="ignore")
        return d

    morceaux.append(dummies(df["star"], "etoiles", REFERENCES["etoiles"]))
    morceaux.append(dummies(df["palier_local_guide"], "guide", REFERENCES["profil"]))
    if avec_habitude:
        d = pd.get_dummies(df["habitude_reponse_fiche"], dtype="float32")
        morceaux.append(d.drop(columns=[REFERENCES["habitude"]], errors="ignore"))
    morceaux.append(dummies(df["taille_texte"], "texte", REFERENCES["texte"]))
    morceaux.append(dummies(df["secteur"], "secteur").iloc[:, 1:])
    morceaux.append(dummies(df["bucket"], "taille", REFERENCES["taille"]))
    if avec_region:
        morceaux.append(dummies(df["region"], "region").iloc[:, 1:])

    X = pd.concat(morceaux, axis=1)

    # Réponse découpée par habitude de la fiche. Les fiches sans historique sont
    # rangées avec celles qui répondent à moins de 25 % : leur tranche ne porte
    # que 2 suppressions et le garde-fou la fond déjà dans la référence.
    if reponse_par_habitude:
        repondu = df["reponse_au_jalon"] == 1
        habitude = df["habitude_reponse_fiche"].astype(str)
        X = X.drop(columns=["reponse_au_jalon"])
        X["reponse_si_habitude_plus_de_75"] = (
            repondu & (habitude == "habitude_plus_de_75")).astype("float32")
        X["reponse_si_habitude_25_75"] = (
            repondu & (habitude == "habitude_25_75")).astype("float32")
        X["reponse_si_habitude_moins_de_25"] = (
            repondu & habitude.isin(["habitude_moins_de_25",
                                     "habitude_historique_insuffisant"])).astype("float32")

    X = X.loc[:, X.sum(axis=0) >= MIN_CAS_PAR_COLONNE]
    return sm.add_constant(X, has_constant="add")


def ecarter_colonnes_degenerees(X: pd.DataFrame, y: pd.Series) -> pd.DataFrame:
    """Même garde-fou que 07 : une colonne trop rare fait diverger l'ajustement.

    `reponse_au_jalon` n'est jamais écartée : si elle tombait sous le seuil, le
    script n'aurait plus de sujet, et le contrôle de main() l'a déjà arrêté.
    """
    a_jeter = []
    for col in X.columns:
        if col in ("const", "reponse_au_jalon"):
            continue
        masque = X[col] > 0
        if not masque.any():
            a_jeter.append(col)
            continue
        n_suppr = int(y[masque].sum())
        if n_suppr < MIN_SUPPRESSIONS_PAR_COLONNE or n_suppr == int(masque.sum()):
            a_jeter.append(col)
    if a_jeter:
        print(f"  colonnes écartées, trop rares ou sans variation : "
              f"{', '.join(a_jeter)}")
    return X.drop(columns=a_jeter)


def ajuster(df: pd.DataFrame, libelle: str, avec_region: bool, avec_habitude: bool = True,
            reponse_par_habitude: bool = False):
    y = df["supprime_fenetre"].astype("float64")
    X = ecarter_colonnes_degenerees(
        matrice_modele(df, avec_region, avec_habitude, reponse_par_habitude), y)

    res = sm.GLM(y, X, family=sm.families.Binomial()).fit(
        cov_type="cluster", cov_kwds={"groups": df["cid"].to_numpy()})

    ic = res.conf_int()
    tableau = pd.DataFrame({
        "modele": libelle,
        "coefficient": res.params,
        "std_err": res.bse,
        "z": res.tvalues,
        "risque_relatif": np.exp(res.params),
        "borne_basse": np.exp(ic[0]),
        "borne_haute": np.exp(ic[1]),
        "p_value": res.pvalues,
    })
    return res, tableau


def effet_minimal_detectable(res) -> tuple[float, float]:
    """L'effet le plus petit que ce montage pouvait repérer.

    Sans ce chiffre, un résultat non significatif se lit à tort comme « répondre
    ne change rien ». Il dit en réalité : « s'il y avait un effet, il était plus
    petit que celui-ci ».

    Calculé depuis l'erreur-type réellement obtenue, groupée par établissement.
    C'est donc la précision du modèle tel qu'il a tourné, sans hypothèse ajoutée.
    Renvoie les deux bornes : protection et aggravation.
    """
    if "reponse_au_jalon" not in res.bse.index:
        return float("nan"), float("nan")
    se = float(res.bse["reponse_au_jalon"])
    ecart = Z_TEST_PLUS_Z_PUISSANCE * se
    return float(np.exp(-ecart)), float(np.exp(ecart))


def tableau_croise(df: pd.DataFrame) -> pd.DataFrame:
    """Taux de suppression par caractéristique, avant tout modèle.
    Dénominateur : le nombre d'avis du groupe, au jalon."""
    lignes = []
    for var in ["reponse_au_jalon", "has_photo", "langue_minoritaire_sur_la_fiche",
                "star", "bucket", "secteur", "palier_local_guide", "taille_texte",
                "habitude_reponse_fiche",
                "region", "n_avis_meme_jour_auteur"]:
        g = df.groupby(var, observed=True)["supprime_fenetre"].agg(["sum", "size"])
        for valeur, row in g.iterrows():
            lignes.append({
                "caracteristique": var, "valeur": valeur,
                "avis_au_jalon": int(row["size"]),
                "supprimes_dans_la_fenetre": int(row["sum"]),
                "taux_pour_10000_avis": round(row["sum"] / row["size"] * 10000, 1),
            })
    return pd.DataFrame(lignes)


def ecrire_summary(res, suffixe: str, df: pd.DataFrame, jalon: int,
                   fenetre: int, mde: tuple[float, float]) -> None:
    lignes = [
        "=" * 78,
        f"Passage : {suffixe}",
        f"Jalon : fin du jour {jalon}. Fenêtre de risque : "
        f"jours {jalon + 1} à {jalon + fenetre}.",
        f"Dénominateur : {len(df):,} avis encore en ligne au jalon"
        .replace(",", " "),
        f"Cible : {int(df['supprime_fenetre'].sum()):,} suppressions dans la fenêtre"
        .replace(",", " "),
        f"Traités : {int(df['reponse_au_jalon'].sum()):,} avis avec une réponse "
        f"au jalon ({df['reponse_au_jalon'].mean():.1%})".replace(",", " "),
        "",
        "L'ÂGE N'EST PAS DANS CE MODÈLE, ET C'EST VOULU. Tous les avis ont le",
        "même âge au jalon et la même durée d'exposition ensuite. Contrairement",
        "à 07_regression_panel.py, il n'y a pas d'âge à contrôler.",
        "",
        f"Effet minimal détectable par ce montage : ×{mde[0]:.2f} en protection,",
        f"×{mde[1]:.2f} en aggravation (test bilatéral 5 %, puissance 80 %).",
        "Un résultat non significatif signifie « l'effet, s'il existe, est plus",
        "faible que cela », pas « il n'y a pas d'effet ».",
        "=" * 78,
        "",
        str(res.summary()),
    ]
    (SORTIES / f"08B_summary_{suffixe}.txt").write_text(
        "\n".join(lignes), encoding="utf-8")


# ---------------------------------------------------------------------------
# Programme
# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(
        description="Répondre vite à un avis le protège-t-il ? "
                    "Cohorte à jalon fixe sur les avis nés pendant la surveillance.")
    ap.add_argument("--jalon-jours", type=int, default=2,
                    help="âge, en jours, auquel on photographie la situation (défaut 2)")
    ap.add_argument("--fenetre-jours", type=int, default=6,
                    help="durée d'observation après le jalon, en jours (défaut 6)")
    ap.add_argument("--sans-enseignes-signalees", action="store_true",
                    help="retire les fiches de biz_surveillance")
    ap.add_argument("--sans-habitude", action="store_true",
                    help="retire l'habitude de réponse de la fiche du modèle")
    ap.add_argument("--reponse-par-habitude", action="store_true",
                    help="mesure l'effet de la réponse dans chaque tranche d'habitude")
    args = ap.parse_args()

    if args.jalon_jours < 0 or args.fenetre_jours < 1:
        print("ARRÊT : jalon négatif ou fenêtre vide.", file=sys.stderr)
        return 1
    # Le `08` s'arrêtait au-delà du 8e jour, borne de l'ancien panel. Ici la
    # borne n'est plus fixe : `ecarter_trop_recents` retire les avis publiés
    # trop tard pour la fenêtre demandée, quelle qu'elle soit. Un jalon et une
    # fenêtre qui mènent au 14e jour ne gardent donc que les avis du 10 août.
    # Le garde-fou porte sur ce qui reste, et il est posé après la sélection.

    SORTIES.mkdir(exist_ok=True)
    df = lire(client_bigquery())
    df = ecarter_trop_recents(df, args.jalon_jours, args.fenetre_jours)
    if len(df) < MIN_CAS_PAR_COLONNE:
        print(f"ARRÊT : {len(df)} avis seulement sont suivis "
              f"{args.jalon_jours + args.fenetre_jours} jours. Réduire le jalon "
              f"ou la fenêtre.", file=sys.stderr)
        return 1

    if args.sans_enseignes_signalees:
        garde = ~df["enseigne_surveillee"].astype(bool)
        print(f"[filtre] enseignes signalées retirées : "
              f"{int((~garde).sum()):,} avis".replace(",", " "))
        df = df[garde]

    df = appliquer_jalon(df, args.jalon_jours, args.fenetre_jours)
    df = ajouter_variables(df)

    suffixe = (f"jalon{args.jalon_jours}_fenetre{args.fenetre_jours}"
               + ("_sans_enseignes" if args.sans_enseignes_signalees else "")
               + ("_sans_habitude" if args.sans_habitude else "")
               + ("_reponse_par_habitude" if args.reponse_par_habitude else ""))

    # Le croisement qui décide si le modèle a de quoi tourner.
    croise_reponse = pd.crosstab(df["reponse_au_jalon"], df["supprime_fenetre"])
    print("\n--- le croisement qui décide ---")
    print(croise_reponse.to_string())
    if croise_reponse.shape != (2, 2) or croise_reponse.to_numpy().min() < MIN_CAS_PAR_COLONNE:
        print(f"\nARRÊT : une des cases est sous {MIN_CAS_PAR_COLONNE} avis. "
              f"Il n'y a rien à estimer ; ne pas forcer le modèle.",
              file=sys.stderr)
        return 1

    print("\n--- tableau croisé, avant tout modèle ---")
    croise = tableau_croise(df)
    croise.to_csv(SORTIES / f"08B_croisements_{suffixe}.csv", index=False)
    print(f"  écrit : 08B_croisements_{suffixe}.csv")

    avec_region = df["region"].nunique() > 1
    if args.reponse_par_habitude and args.sans_habitude:
        print("ARRÊT : --reponse-par-habitude demande l'habitude dans le modèle.",
              file=sys.stderr)
        return 1
    res, tableau = ajuster(df, suffixe, avec_region, not args.sans_habitude,
                           args.reponse_par_habitude)

    # Réponse × habitude, avant tout modèle : taux pour 10 000 avis au jalon.
    g = df.groupby(["habitude_reponse_fiche", "reponse_au_jalon"])["supprime_fenetre"]
    croise_habitude = g.agg(avis_au_jalon="size", supprimes_dans_la_fenetre="sum").reset_index()
    croise_habitude["taux_pour_10000_avis"] = (
        croise_habitude["supprimes_dans_la_fenetre"] / croise_habitude["avis_au_jalon"] * 10000).round(1)
    croise_habitude.to_csv(SORTIES / f"08B_reponse_x_habitude_{suffixe}.csv", index=False)
    print("\n--- réponse au jalon × habitude de réponse de la fiche ---")
    print(croise_habitude.to_string(index=False))
    print(res.summary())

    tableau.index.name = "variable"
    tableau.to_csv(SORTIES / f"08B_coefficients_{suffixe}.csv")
    print(f"\n  écrit : 08B_coefficients_{suffixe}.csv")

    mde = effet_minimal_detectable(res)
    ecrire_summary(res, suffixe, df, args.jalon_jours, args.fenetre_jours, mde)
    print(f"  écrit : 08B_summary_{suffixe}.txt")

    if args.reponse_par_habitude:
        print("\n" + "=" * 78)
        print("  EFFET DE LA RÉPONSE, SÉPARÉMENT PAR HABITUDE DE LA FICHE")
        print("=" * 78)
        for var in ["reponse_si_habitude_plus_de_75", "reponse_si_habitude_25_75",
                    "reponse_si_habitude_moins_de_25"]:
            if var not in tableau.index:
                print(f"  {var:34s} colonne écartée, trop peu de suppressions")
                continue
            l = tableau.loc[var]
            print(f"  {var:34s} ×{l['risque_relatif']:.2f} "
                  f"[{l['borne_basse']:.2f} – {l['borne_haute']:.2f}]")
        return 0

    ligne = tableau.loc["reponse_au_jalon"]
    print("\n" + "=" * 78)
    print("  RÉPONDRE DANS LES DEUX JOURS : CE QUE DIT LE MODÈLE")
    print("=" * 78)
    print(f"  Risque relatif      ×{ligne['risque_relatif']:.2f} "
          f"[{ligne['borne_basse']:.2f} – {ligne['borne_haute']:.2f}], "
          f"p = {ligne['p_value']:.3f}")
    print(f"  Dénominateur        {len(df):,} avis au jalon".replace(",", " "))
    print(f"  Effet détectable    ×{mde[0]:.2f} en protection, "
          f"×{mde[1]:.2f} en aggravation")
    if ligne["borne_basse"] <= 1 <= ligne["borne_haute"]:
        print("  Lecture             la fourchette contient 1 : aucune protection")
        print("                      mesurable. Cela ne prouve pas qu'il n'y en a")
        print("                      pas, seulement qu'elle serait plus faible que")
        print(f"                      ×{mde[0]:.2f}.")
    else:
        print("  Lecture             la fourchette exclut 1 : l'écart est net.")
    print()
    print("  À savoir en citant ce chiffre :")
    print(f"  - Il porte sur les {len(df):,} avis vus dès leur publication et "
          f"suivis".replace(",", " "))
    print(f"    {args.jalon_jours + args.fenetre_jours} jours, pas sur tout le "
          f"panel de 35 751 avis.")
    print("  - Une réponse retirée est invisible dans l'export.")
    print("  - Le commerçant qui répond est souvent celui qui signale : le sens")
    print("    de la causalité n'est pas établi par ce modèle.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as erreur:
        print(f"\nARRÊT : {erreur}", file=sys.stderr)
        sys.exit(1)
