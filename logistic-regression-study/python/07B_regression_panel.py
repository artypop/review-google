#!/usr/bin/env python3
"""
==============================================================================
Script : 07B_regression_panel.py
Table source : client-divers.reviewflowz.reviews_panel_features_03B

Adaptation de `07_regression_panel.py` à la nouvelle chaîne de tables, écrite
le 2026-09-21. Le `07` n'est pas modifié : il continue de lire
`reviews_panel_features_03` et ses sorties du 17 septembre restent rejouables.

Régression logistique sur le panel construit par `sql/03B_adding_features.bqsql`.

------------------------------------------------------------------------------
CE QUI CHANGE PAR RAPPORT AU 07, ET POURQUOI
------------------------------------------------------------------------------

1. LE PANEL

   35 751 avis publiés du 4 au 17 août 2026, sur 5 566 fiches, 1 355
   suppressions, soit 3,79 % des avis. L'ancien panel en comptait 225 757 sur
   trois mois de publication.

   Une ligne par avis, comme avant. La différence tient à la fenêtre de
   publication : quatorze jours au lieu de quatre-vingt-dix.

2. LE CONTRÔLE D'ÂGE EST REFAIT DE FOND EN COMBLE

   `age_a_la_vague1_j` n'existe plus, et `j8_pendant_suivi`, qui en dérivait,
   disparaît avec lui. Sur un panel dont tous les avis sont publiés du 4 au
   17 août, l'âge au 11 août vaut de +7 à −6 jours : négatif pour la moitié du
   corpus, il ne peut plus servir de contrôle.

   DEUX COLONNES LE REMPLACENT, et elles ne disent pas la même chose.

   `age_a_la_premiere_observation_j` — âge de l'avis le jour où le robot l'a vu
   pour la première fois. C'est le contrôle d'âge de ce panel. Mesuré le
   2026-09-21 sur la table 03B :

     0 j    2 013 avis   4,72 % supprimés
     1 j   17 861 avis   4,02 %
     2 j    2 263 avis   3,00 %
     3 j    2 453 avis   3,18 %
     4 j    2 877 avis   4,03 %
     5 j    2 781 avis   3,88 %
     6 j    2 575 avis   2,72 %
     7 j    2 516 avis   2,78 %
     8 j+     412 avis   7,04 %

   `fenetre_observation_j` — nombre de jours pendant lesquels l'avis pouvait
   être vu disparaître, entre sa première observation et le 24 août.

     CETTE COLONNE N'EXISTAIT DANS AUCUNE VERSION PRÉCÉDENTE, ET ELLE EST
     INDISPENSABLE. Un avis vu pour la première fois le 17 août est regardé
     7 jours, un avis vu le 11 août l'est 13 jours, et les deux comptent
     « non supprimé » s'ils survivent. Sans elle, le modèle mélange le risque
     par jour et le nombre de jours regardés. Elle est fixée avant que le sort
     de l'avis soit connu, donc elle est utilisable en entrée.

     0 à 5 j     266 avis   0,75 % supprimés
     6 à 9 j   9 718 avis   3,51 %
     10 à 12 j 7 938 avis   4,75 %
     13 j     17 829 avis   3,56 %

   Les deux entrent en jours, sans logarithme. Le 07 passait l'âge en
   logarithme parce que le risque y était divisé par 21 entre 0 et 90 jours ;
   ici l'étendue utile est de 0 à 7 jours et la courbe est plate.

   ATTENTION À LA DÉPENDANCE ARITHMÉTIQUE. Les trois quantités sont liées :
   date de publication = 24 août − fenêtre − âge à la première observation. Les
   deux colonnes ensemble contiennent donc la date de publication. C'est
   voulu — elle sert de contrôle de tendance — mais cela interdit d'ajouter
   `ne_pendant_la_surveillance` au modèle. Elle est lue pour le tableau croisé
   et rien de plus.

3. `vu_tardivement` — UNE QUEUE QU'IL FAUT ISOLER

   412 avis ont été vus au 8e jour ou plus tard. Leur taux de suppression,
   7,04 %, vient en presque totalité d'une seule fiche attaquée. Cette colonne
   oui/non les sépare du reste plutôt que de laisser le terme linéaire d'âge
   extrapoler sur dix-huit jours à partir de sept.

   Ce que ces avis ont de particulier est documenté dans
   `etudes-ponctuelles/2026-09-21-avis-vus-tardivement/sorties/2026-09-21-analyse-complementaire.docx` : aucun ne porte 4 étoiles,
   66 % dépassent 200 caractères contre 26 % ailleurs. `--sans-vus-tardivement`
   permet de relancer sans eux.

4. TROIS COLONNES NOUVELLES, LUES MAIS PAS ENTRÉES DANS LE MODÈLE

   `avis_modifie`, `note_modifiee`, `texte_modifiee` sont mesurables pour la
   première fois sur cette chaîne de tables : l'ancienne excluait du corpus
   tout avis à plusieurs enregistrements. 280 avis du panel sont concernés.

   Elles sont observées au dernier passage du robot, donc la modification a pu
   survenir après le début de la période de risque. Même traitement que
   `reponse_pendant_surveillance` : dans le tableau croisé, jamais en entrée.
   `--sans-avis-modifies` permet de relancer sans eux.

5. LES DEUX COURBES DE CIBLAGE PAR SOUS-POPULATION

   Le 07 les traçait de part et d'autre de `j8_pendant_suivi`. Ici le partage
   se fait sur la fenêtre d'observation, à 10 jours : dans chaque courbe, tous
   les avis ont été regardés à peu près aussi longtemps, donc ce que le modèle
   y repère ne vient pas de la durée de suivi.

6. CE QUI NE CHANGE PAS

   Les références, les garde-fous, les cinq tours par établissement, la
   correction de sous-échantillonnage, le tableau croisé et la courbe de
   ciblage sont repris du 07 sans retouche.

------------------------------------------------------------------------------
COLONNES INTERDITES EN ENTRÉE
------------------------------------------------------------------------------
  supprime                       c'est la cible
  age_a_la_suppression_j         connue seulement pour un avis déjà supprimé
  jours_avant_disparition_j      idem
  delai_reponse_j                idem pour les avis supprimés avant la réponse
  a_une_reponse                  état au dernier passage du robot : un survivant
                                 a eu plus de temps pour recevoir une réponse
  reponse_pendant_surveillance   arrive pendant la période de risque
  avis_modifie, note_modifiee,
  texte_modifiee                 observées au dernier passage, voir le § 4

`age_a_la_premiere_observation_j` et `fenetre_observation_j` sont au contraire
des entrées légitimes : elles sont fixées avant que le sort de l'avis soit
connu.

------------------------------------------------------------------------------
DEUX VARIABLES ÉCARTÉES DU MODÈLE, ET POURQUOI
------------------------------------------------------------------------------
`langue_etrangere_au_pays` — retirée le 2026-09-14. La jointure sur
`concordance_pays_langue` est correcte, les codes correspondent : `hr` pour HR,
`el` pour GR, `no` pour NO. Mais en Europe la variable mesure le tourisme.
92,8 % des avis croates sont en langue étrangère, dont 44,7 % en allemand
contre 7,2 % en croate ; 67,0 % en Norvège, 70,4 % au Portugal, 61,8 % en
Grèce. Aux États-Unis, 2,1 %. Son coefficient s'inversait entre les deux
régions : ×2,69 en Europe, ×0,90 aux États-Unis.
`langue_minoritaire_sur_la_fiche` la remplace et ne souffre pas de ce défaut :
un hôtel croate dont la clientèle est allemande a l'allemand pour langue
habituelle, donc un avis en allemand n'y est pas signalé comme inhabituel.

`langue_inconnue` et `rythme_fiche_inconnu` — retirées le 2026-09-14 après un
passage où elles sortaient à 10^8 et 10^10 sur le sous-corpus américain. Voir
le commentaire de VARIABLES_BINAIRES.

Les trois colonnes restent lues depuis BigQuery, pour le tableau croisé.
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
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

# La console Windows écrit en cp1252 et s'arrête sur la flèche « → » des
# repères de la courbe de ciblage, après que le modèle a tourné : le passage
# meurt au moment d'imprimer ses résultats. Sur Linux, où tourne le 07, ces
# deux lignes ne changent rien.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

PROJET = "client-divers"
DATASET = "reviewflowz"
TABLE = "reviews_panel_features_03B"
# Dossier des clés de service, pas un fichier précis.
#
# Le nom du fichier change à chaque rotation de clé — il valait
# `client-divers-8b012e5b7c73.json` jusqu'au 2026-09-14, puis
# `client-divers-df744e79fa71.json`. Coder le nom en dur fait échouer le script
# sur une DefaultCredentialsError qui ne dit pas qu'il s'agit d'une rotation.
# On prend donc le seul `.json` du dossier.
DOSSIER_CLES = Path("/home/romain/.gcp")

# Les sorties vont dans `output-study/`, à côté des notes qui les commentent, et
# non dans `python/` où vivent les scripts. Le `.parent.parent` remonte de
# `python/` à la racine du dossier d'étude : sans lui, le rangement du
# 2026-09-14 ferait écrire les résultats au milieu du code.
SORTIES = (Path(__file__).resolve().parent.parent / "output-study"
           / f"{date.today():%Y-%m-%d}-sorties-07B")

# Part des avis NON supprimés gardée pour l'ajustement.
#
# Mise à 1.0 le 2026-09-14 : le modèle tourne sur tous les avis, aucun n'est
# écarté. Les fichiers `07B_summary_*.txt` et `07B_coefficients_*.csv` donnent
# alors exactement les mêmes valeurs, constante comprise.
#
# `CLAUDE.md` autorise le sous-échantillonnage des avis non supprimés, à
# condition de corriger la constante. Il sert quand les événements rares se
# noient dans des millions de lignes. Ici le panel tient en 35 751 lignes, le
# gain de temps ne valait pas un second jeu de chiffres à réconcilier.
#
# Si la valeur repasse sous 1.0, la mécanique de correction reste en place :
# `echantillonner` tire l'échantillon, `ajuster` corrige la constante et ses
# bornes en leur ajoutant le logarithme du taux, `corriger_probabilites` fait
# de même sur chaque probabilité prédite. Les autres coefficients ne bougent
# pas : retirer des avis au hasard parmi les survivants change le niveau de
# base, pas les écarts entre groupes.
TAUX_ECHANTILLON_NEGATIFS = 1.0

# Mesure de qualité : les établissements sont répartis en N_TOURS groupes, et
# chaque groupe sert de test une fois. Voir `cinq_tours`.
N_TOURS = 5
GRAINE = 20260914

# Longueur du texte, en caractères. Tranches reprises du script 06.
TRANCHES_TEXTE = [-1, 0, 50, 200, 10**6]
NOMS_TRANCHES_TEXTE = ["sans_texte", "texte_1_50", "texte_51_200", "texte_201p"]

# Secteurs sous ce seuil : regroupés, pour ne pas créer une colonne par cas isolé.
SEUIL_SECTEUR_RARE = 0.01

# Âge, en jours, à partir duquel un avis est dit « vu tardivement ». Au-delà de
# 7 jours la fenêtre de publication du panel ne l'explique plus. Voir § 3 de
# l'en-tête.
SEUIL_VU_TARDIVEMENT = 8

# Partage des deux courbes de ciblage par sous-population, en jours de fenêtre
# d'observation. Voir § 5 de l'en-tête.
SEUIL_FENETRE_LONGUE = 10

COLONNES = [
    # identifiants et cible
    "review_id", "cid", "author_key", "supprime",
    # exposition : les deux entrées légitimes qui remplacent age_a_la_vague1_j
    "age_a_la_premiere_observation_j", "fenetre_observation_j",
    "ne_pendant_la_surveillance",
    # A. l'avis
    "star", "has_text", "text_chars", "has_photo",
    "reponse_avant_surveillance", "reponse_dans_les_2_jours",
    # A bis. l'avis a été réécrit par son auteur. Lues pour le tableau croisé
    # et pour les filtres, jamais en entrée du modèle : voir § 4 de l'en-tête.
    "avis_modifie", "note_modifiee", "texte_modifiee",
    # B. l'auteur
    "reviewer_review_count", "log_rc", "palier_local_guide", "reviewer_photo_count",
    "n_avis_meme_jour_auteur", "avis_auteur_90j_avant",
    # C. la langue
    "langue_inconnue", "langue_etrangere_au_pays", "langue_minoritaire_sur_la_fiche",
    # D. l'établissement
    "industry", "bucket", "region",
    "chaine_antiparasitaire_us", "salle_de_sport_attaquee",
    # E. l'afflux
    "log_ratio_pic_journalier_fiche", "rythme_fiche_inconnu",
]

# Deux colonnes ont été retirées des entrées le 2026-09-14, après un premier
# passage où elles sortaient à 10^8 et 10^10 sur le sous-corpus américain :
#   `langue_inconnue`      double `texte_sans_texte`. Sur les 8 925 avis sans
#                          texte de la population fraîche, 8 717 n'ont pas de
#                          langue détectée : 97,7 % de recouvrement. Le modèle
#                          ne peut pas départager deux colonnes identiques.
#   `rythme_fiche_inconnu` ne concerne que 12 avis, dont 5 américains. Sur un
#                          sous-corpus il n'y a plus rien à estimer.
# Les deux restent lues depuis BigQuery, pour le tableau croisé.
VARIABLES_BINAIRES = [
    "has_photo",
    # `reponse_avant_surveillance` retirée du modèle le 2026-09-17 (décision de
    # Romain) : la réponse du propriétaire est étudiée par le 08. Elle reste
    # lue pour le tableau croisé.
    "langue_minoritaire_sur_la_fiche",
    # Variable de contrôle, pas un résultat. Isole les 412 avis vus au 8e jour
    # ou plus tard, sur lesquels le terme linéaire d'âge extrapolerait. Voir
    # § 3 de l'en-tête.
    "vu_tardivement",
]

# Garde-fou : une colonne oui/non trop rare, ou dont toutes les lignes ont le
# même sort, fait diverger l'ajustement. Ces deux seuils l'écartent avant.
MIN_CAS_PAR_COLONNE = 30
MIN_SUPPRESSIONS_PAR_COLONNE = 5

VARIABLES_CONTINUES = [
    "log_rc",
    "log_photos_auteur",
    "log_burst",
    "log_ratio_pic_journalier_fiche",
    # Les deux contrôles d'exposition, en jours. Leurs coefficients ne sont pas
    # des résultats à citer : ils sont là pour que les autres se lisent à âge
    # et à durée de suivi comparables. Voir § 2 de l'en-tête.
    "age_a_la_premiere_observation_j",
    "fenetre_observation_j",
]

# Note servant de référence dans la lecture demandée par Romain le 2026-09-14.
# Le modèle s'ajuste sur `REFERENCES["etoiles"]`, cellule la plus fournie ;
# la colonne `risque_relatif_vs_3_etoiles` du CSV rejoue la comparaison depuis
# l'avis neutre, sans faire reposer l'estimation sur ses 26 suppressions.
NOTE_DE_LECTURE = "etoiles_3"

REFERENCES = {
    "etoiles": "etoiles_5",
    # Palier 1 à 3 : le plus fourni, 20 912 avis et 889 suppressions.
    "profil": "guide_1_3",
    "texte": "texte_sans_texte",
    "taille": "taille_mono",
}


# ---------------------------------------------------------------------------
# Lecture
# ---------------------------------------------------------------------------

def trouver_cle() -> str | None:
    """La clé de service, quel que soit son nom de fichier.

    `GOOGLE_APPLICATION_CREDENTIALS` l'emporte s'il est posé. Sinon on prend le
    seul `.json` de DOSSIER_CLES. S'il y en a plusieurs, on s'arrête plutôt que
    d'en choisir un au hasard : deux clés dans le dossier veut dire qu'une
    rotation est en cours, et prendre la mauvaise donne une erreur de droits
    incompréhensible.

    Les fichiers `:Zone.Identifier` que WSL dépose à côté des téléchargements ne
    finissent pas par `.json` et ne sont donc jamais ramassés.
    """
    if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        return None                       # déjà posé, on n'y touche pas
    if not DOSSIER_CLES.is_dir():
        return None                       # laisse google-auth chercher ailleurs
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
    """Charge le panel entier, 35 751 avis.

    Aucun filtre. Le découpage selon l'âge est délibérément impossible : l'âge
    est une variable de contrôle du modèle, pas un critère de sélection. Voir
    l'en-tête.
    """
    from google.cloud import bigquery

    sql = f"SELECT {', '.join(COLONNES)} FROM `{PROJET}.{DATASET}.{TABLE}`"

    estime = client.query(
        sql, job_config=bigquery.QueryJobConfig(dry_run=True)
    ).total_bytes_processed / 1024**3
    print(f"[lecture] panel entier, {estime:.2f} Go")

    df = client.query(sql).to_arrow(create_bqstorage_client=True).to_pandas(
        split_blocks=True, self_destruct=True)
    print(f"[lecture] {len(df):,} avis".replace(",", " "))
    return df


def compacter(df: pd.DataFrame) -> pd.DataFrame:
    for col in ["cid", "author_key", "industry", "bucket", "region",
                "palier_local_guide"]:
        if col in df.columns:
            df[col] = df[col].astype("category")
    for col in df.select_dtypes(include=["bool"]).columns:
        df[col] = df[col].astype("int8")
    print(f"[mémoire] {df.memory_usage(deep=True).sum() / 1024**2:,.0f} Mo"
          .replace(",", " "))
    return df


# ---------------------------------------------------------------------------
# Préparation
# ---------------------------------------------------------------------------

def ajouter_variables(df: pd.DataFrame) -> pd.DataFrame:
    """Fabrique les colonnes dérivées du modèle.

    CES COLONNES POURRAIENT ÊTRE CALCULÉES DANS sql/03B_adding_features.bqsql.
    Décision de Romain le 2026-09-14 : elles restent ici pour l'instant.

      taille_texte     `text_chars` découpé en 4 tranches (TRANCHES_TEXTE)
      log_burst        logarithme de `n_avis_meme_jour_auteur`
      secteur          `industry`, secteurs sous 1 % regroupés en « autres »
      vu_tardivement   `age_a_la_premiere_observation_j` au-delà de 7 jours

    Ce qu'on y gagne : les seuils se changent en éditant ce fichier, sans
    reconstruire une table BigQuery. Utile tant qu'on tâtonne.

    Ce qu'on y perd : la définition d'une caractéristique est écrite à deux
    endroits. Quelqu'un qui lit `02` ne saura pas que les secteurs rares sont
    regroupés ni où sont coupées les tranches de texte. C'est le défaut qui a
    été corrigé ailleurs dans le projet pour la règle de suppression et pour la
    règle de fiche attaquée. À remonter dans `02` quand les seuils seront figés.
    """
    df = df.copy()

    df["taille_texte"] = pd.cut(
        df["text_chars"].fillna(0).clip(lower=0),
        bins=TRANCHES_TEXTE, labels=NOMS_TRANCHES_TEXTE)

    # Les deux contrôles d'exposition, en jours, tels quels. Aucun logarithme :
    # l'étendue utile est de 0 à 7 jours pour l'âge et de 0 à 13 pour la
    # fenêtre, et la courbe de risque y est plate. Voir § 2 de l'en-tête.
    for colonne in ["age_a_la_premiere_observation_j", "fenetre_observation_j"]:
        df[colonne] = df[colonne].fillna(0).clip(lower=0).astype("float32")

    # L'avis a été vu pour la première fois au 8e jour ou plus tard. 412 avis,
    # dont une bonne part appartient à la fiche espagnole attaquée. Sans cette
    # colonne, le terme linéaire d'âge extrapolerait jusqu'à 18 jours à partir
    # d'une courbe mesurée sur 7. Voir § 3 de l'en-tête.
    df["vu_tardivement"] = (
        df["age_a_la_premiere_observation_j"] >= SEUIL_VU_TARDIVEMENT).astype("int8")

    # Fenêtre d'observation en tranches, pour le tableau croisé seulement. Le
    # modèle prend la colonne en jours.
    df["tranche_fenetre"] = pd.cut(
        df["fenetre_observation_j"], [-1, 5, 9, 12, np.inf],
        labels=["0_5_j", "6_9_j", "10_12_j", "13_j"])

    # Rafale d'auteur en logarithme : l'écart entre 1 et 2 avis le même jour
    # compte plus que celui entre 11 et 12.
    df["log_burst"] = np.log1p(df["n_avis_meme_jour_auteur"].fillna(1).clip(lower=0))

    # Photos publiées par l'auteur, en logarithme : passer de 0 à 10 photos
    # compte plus que passer de 1 000 à 1 010. Vide mis à 0 dans sql/03.
    df["log_photos_auteur"] = np.log1p(df["reviewer_photo_count"].fillna(0).clip(lower=0))
    df["tranche_photos_auteur"] = pd.cut(
        df["reviewer_photo_count"].fillna(0), [-1, 0, 10, 100, np.inf],
        labels=["0", "1_10", "11_100", "plus_de_100"])

    df["log_ratio_pic_journalier_fiche"] = (
        df["log_ratio_pic_journalier_fiche"].fillna(0).astype("float32"))
    df["star"] = df["star"].fillna(0).astype("int8")

    parts = df["industry"].value_counts(normalize=True, dropna=False)
    rares = parts[parts < SEUIL_SECTEUR_RARE].index
    secteur = df["industry"].astype("object").where(~df["industry"].isin(rares), "autres")
    df["secteur"] = secteur.fillna("inconnu").astype("category")
    return df


def matrice_modele(df: pd.DataFrame, avec_region: bool) -> pd.DataFrame:
    """Colonnes d'entrée du modèle.

    Les variables à catégories deviennent des colonnes oui/non. Une catégorie
    sert de référence et n'a pas de colonne : c'est le point de comparaison.
    """
    morceaux = [df[VARIABLES_BINAIRES].astype("float32"),
                df[VARIABLES_CONTINUES].astype("float32")]

    def dummies(serie, prefixe, reference=None):
        d = pd.get_dummies(serie, prefix=prefixe, dtype="float32")
        if reference:
            d = d.drop(columns=[reference], errors="ignore")
        return d

    morceaux.append(dummies(df["star"], "etoiles", REFERENCES["etoiles"]))
    morceaux.append(dummies(df["palier_local_guide"], "guide", REFERENCES["profil"]))
    morceaux.append(dummies(df["taille_texte"], "texte", REFERENCES["texte"]))
    morceaux.append(dummies(df["secteur"], "secteur").iloc[:, 1:])
    morceaux.append(dummies(df["bucket"], "taille", REFERENCES["taille"]))
    if avec_region:
        morceaux.append(dummies(df["region"], "region").iloc[:, 1:])

    X = pd.concat(morceaux, axis=1)
    X = X.loc[:, X.sum(axis=0) >= MIN_CAS_PAR_COLONNE]
    return sm.add_constant(X, has_constant="add")


def ecarter_colonnes_degenerees(X: pd.DataFrame, y: pd.Series) -> pd.DataFrame:
    """Retire les colonnes oui/non dont toutes les lignes à 1 ont le même sort.

    Sans ce contrôle, le modèle pousse leur coefficient vers l'infini et sort
    un risque relatif de plusieurs millions, qui n'a aucun sens.
    """
    a_jeter = []
    for col in X.columns:
        if col == "const":
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


def controler_references(df: pd.DataFrame, y: pd.Series) -> None:
    """Avertit si une catégorie de référence est trop fine.

    `ecarter_colonnes_degenerees` ne peut pas la voir : la référence n'a pas de
    colonne dans la matrice, c'est justement ce qui la définit. Or tous les
    coefficients de sa famille sont mesurés contre elle. Si elle ne porte qu'une
    poignée de suppressions, les fourchettes de toute la famille s'élargissent
    sans que rien ne le signale.
    """
    familles = {
        "etoiles": ("star", lambda v: f"etoiles_{v}"),
        "profil": ("palier_local_guide", lambda v: f"guide_{v}"),
        "texte": ("taille_texte", lambda v: f"texte_{v}"),
        "taille": ("bucket", lambda v: f"taille_{v}"),
    }
    for cle, (colonne, nommer) in familles.items():
        reference = REFERENCES[cle]
        masque = df[colonne].map(nommer) == reference
        n_suppr = int(y[masque].sum())
        if n_suppr < MIN_SUPPRESSIONS_PAR_COLONNE:
            print(f"  ATTENTION : la référence « {reference} » ne porte que "
                  f"{n_suppr} suppression(s). Les coefficients de cette famille "
                  f"sont à lire avec des fourchettes très larges.")


# ---------------------------------------------------------------------------
# Ajustement
# ---------------------------------------------------------------------------

def echantillonner(df: pd.DataFrame, taux: float, graine: int):
    """Garde toutes les suppressions et une part des avis restés en ligne."""
    if taux >= 1.0:
        return df, 1.0
    positifs = df[df["supprime"] == 1]
    negatifs = df[df["supprime"] == 0].sample(frac=taux, random_state=graine)
    return pd.concat([positifs, negatifs]).sort_index(), taux


def corriger_probabilites(p, taux: float):
    """Remet les probabilités à l'échelle réelle après sous-échantillonnage."""
    if taux >= 1.0:
        return np.asarray(p, dtype="float64")
    p = np.clip(np.asarray(p, dtype="float64"), 1e-12, 1 - 1e-12)
    cote = np.log(p / (1 - p)) + np.log(taux)
    return 1 / (1 + np.exp(-cote))


def ajuster(df: pd.DataFrame, libelle: str, avec_region: bool):
    ech, taux = echantillonner(df, TAUX_ECHANTILLON_NEGATIFS, GRAINE)
    y = ech["supprime"].astype("float64")
    controler_references(ech, y)
    X = ecarter_colonnes_degenerees(matrice_modele(ech, avec_region), y)

    res = sm.GLM(y, X, family=sm.families.Binomial()).fit(
        cov_type="cluster", cov_kwds={"groups": ech["cid"].to_numpy()})

    params = res.params.copy()
    ic = res.conf_int()
    basse, haute = ic[0].copy(), ic[1].copy()
    if taux < 1.0 and "const" in params.index:
        params["const"] += np.log(taux)
        basse["const"] += np.log(taux)
        haute["const"] += np.log(taux)

    tableau = pd.DataFrame({
        "modele": libelle,
        "coefficient": params,
        # Erreur-type du coefficient, groupée par établissement. Plus elle est
        # grande, moins le coefficient est précis.
        "std_err": res.bse,
        # Coefficient divisé par son erreur-type. Au-delà de 2 en valeur
        # absolue, l'écart à zéro est net. C'est ce que résume la p_value.
        "z": res.tvalues,
        "risque_relatif": np.exp(params),
        "borne_basse": np.exp(basse),
        "borne_haute": np.exp(haute),
        "p_value": res.pvalues,
    })
    tableau["risque_relatif_vs_3_etoiles"] = rapporter_a_trois_etoiles(tableau)
    tableau = ajouter_ligne_note_de_reference(tableau, libelle)
    print(f"\n[{libelle}] {len(ech):,} avis ajustés, "
          f"{int(ech['supprime'].sum()):,} suppressions".replace(",", " "))
    return res, tableau, X.columns, taux


def ajouter_ligne_note_de_reference(tableau: pd.DataFrame, libelle: str) -> pd.DataFrame:
    """Ajoute la note de référence au tableau, pour qu'elle soit lisible.

    Elle n'a pas de coefficient : son risque relatif vaut 1 par construction.
    Sans cette ligne, le CSV laisserait croire que la note de référence est
    absente du modèle.
    """
    reference = REFERENCES["etoiles"]
    if reference in tableau.index:
        return tableau
    base = tableau.loc[NOTE_DE_LECTURE, "risque_relatif"] \
        if NOTE_DE_LECTURE in tableau.index else np.nan
    ligne = pd.DataFrame(
        {"modele": libelle, "coefficient": 0.0,
         # La référence n'est pas estimée : elle n'a ni erreur-type ni z.
         "std_err": np.nan, "z": np.nan,
         "risque_relatif": 1.0, "borne_basse": 1.0, "borne_haute": 1.0,
         "p_value": np.nan,
         "risque_relatif_vs_3_etoiles": 1.0 / base if base == base and base > 0 else np.nan},
        index=[reference])
    return pd.concat([tableau, ligne])


def ecrire_summary(res, suffixe: str, n_avis: int, n_suppr: int, taux: float,
                   auc: float | None = None) -> None:
    """Enregistre le tableau de régression tel que statsmodels l'imprime.

    Le CSV de coefficients porte l'essentiel, mais pas l'en-tête de diagnostic :
    nombre d'observations, degrés de liberté, déviance, pseudo R², type de
    covariance. Ce fichier le conserve tel quel.

    Attention en le lisant : la constante et l'intervalle de la constante y sont
    ceux de l'échantillon SOUS-ÉCHANTILLONNÉ, donc trop élevés. Les valeurs
    corrigées sont dans le CSV. Les autres coefficients sont identiques dans les
    deux fichiers.

    `auc` est écrite ici parce qu'elle ne figurait nulle part ailleurs que dans
    le titre du graphique de calibration, donc illisible sans ouvrir une image.
    main() appelle cette fonction deux fois : une première sans l'AUC, qui n'est
    pas encore calculée, et une seconde avec. Le fichier est reconstruit
    entièrement à chaque appel, il n'y a donc rien à défaire entre les deux.
    """
    lignes = [
        "=" * 78,
        f"Passage : {suffixe}",
        # Chaque nombre est mis en forme à part. Un `.replace(",", " ")` sur la
        # phrase entière mangeait aussi la virgule qui sépare les deux membres,
        # et le fichier annonçait « 35 751 avis  1 355 suppressions ».
        "Panel : {} avis, {} suppressions".format(
            f"{n_avis:,}".replace(",", " "), f"{n_suppr:,}".replace(",", " ")),
    ]
    if auc is None:
        lignes.append("AUC : non calculée (test trop petit, ou passage interrompu).")
    else:
        lignes += [
            f"AUC sur des établissements jamais vus : {auc:.3f}",
            "  0,5 = tirage au hasard, 1,0 = classement parfait.",
            "  Sur ce panel elle ne doit presque rien à l'âge : tous les avis",
            "  sont publiés sur quatorze jours. Elle ne se compare donc pas à",
            "  celle du 07, portée par trois mois d'écart d'âge.",
        ]
    if taux >= 1.0:
        lignes += [
            "Aucun sous-échantillonnage : le modèle tourne sur tous les avis.",
            "Ce fichier et 07B_coefficients_*.csv donnent les mêmes valeurs.",
        ]
    else:
        lignes += [
            f"Part des avis non supprimés gardée pour l'ajustement : {taux:.0%}",
            "",
            "La constante ci-dessous n'est PAS corrigée du sous-échantillonnage.",
            "Utiliser celle du CSV de coefficients. Les autres lignes sont bonnes.",
        ]
    lignes += [
        "",
        "age_a_la_premiere_observation_j, fenetre_observation_j et vu_tardivement",
        "sont des variables de contrôle, pas des résultats à citer.",
        "=" * 78,
        "",
        str(res.summary()),
    ]
    (SORTIES / f"07B_summary_{suffixe}.txt").write_text(
        "\n".join(lignes), encoding="utf-8")


def rapporter_a_trois_etoiles(tableau: pd.DataFrame) -> pd.Series:
    """Rejoue les effets de note depuis l'avis 3 étoiles.

    Le modèle s'ajuste avec 5 étoiles en référence, la cellule la plus fournie :
    1 081 suppressions contre 12 pour 3 étoiles. Cette colonne redonne la
    lecture centrée sur l'avis neutre, en divisant chaque effet de note par
    celui de 3 étoiles. La note de référence de l'ajustement vaut alors 1 /
    effet de 3 étoiles, et 3 étoiles vaut 1.

    Les autres variables restent vides : elles ne font pas partie de la famille.
    """
    valeurs = pd.Series(np.nan, index=tableau.index, dtype="float64")
    notes = [i for i in tableau.index if i.startswith("etoiles_")]
    if not notes:
        return valeurs

    # Effet de 3 étoiles. S'il n'a pas de ligne, c'est qu'il sert de référence
    # à l'ajustement et vaut donc 1.
    if NOTE_DE_LECTURE in tableau.index:
        base = float(tableau.loc[NOTE_DE_LECTURE, "risque_relatif"])
    elif REFERENCES["etoiles"] == NOTE_DE_LECTURE:
        base = 1.0
    else:
        return valeurs   # 3 étoiles écartée par un garde-fou : rien à calculer
    if not np.isfinite(base) or base <= 0:
        return valeurs

    for i in notes:
        valeurs[i] = float(tableau.loc[i, "risque_relatif"]) / base
    # La note qui sert de référence à l'ajustement n'a pas de ligne ; sa valeur
    # rapportée à 3 étoiles est ajoutée par main() dans le CSV.
    return valeurs


# ---------------------------------------------------------------------------
# Contrôles de qualité
# ---------------------------------------------------------------------------

def aire_sous_courbe(y, p) -> float:
    """Probabilité qu'un avis supprimé reçoive un score plus élevé qu'un avis
    resté en ligne, tiré au hasard."""
    y = np.asarray(y)
    p = np.asarray(p, dtype="float64")
    n_pos, n_neg = int(y.sum()), int((1 - y).sum())
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    rangs = pd.Series(p).rank(method="average").to_numpy()
    return (rangs[y == 1].sum() - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg)


def cinq_tours(df: pd.DataFrame, avec_region: bool, suffixe: str):
    """Mesure de qualité en cinq tours par établissement.

    Remplace le 2026-09-17 le tirage unique d'un quart des établissements
    (décision de Romain). Ce tirage unique était tombé, en Europe, sur des
    fiches 2,3 fois moins touchées que le corpus : les deux salles de sport
    espagnoles portent 327 des 744 suppressions européennes, et elles étaient
    restées côté ajustement. Voir output-study/2026-09-14-interpretation-panel.md § 5.

    Le principe :
      1. Les établissements sont mélangés avec GRAINE, puis répartis en cinq
         groupes de même nombre de fiches.
      2. Tour 1 : le modèle s'ajuste sur les groupes 2 à 5 et donne un score
         aux avis du groupe 1. Tour 2 : il s'ajuste sur 1, 3, 4, 5 et note le
         groupe 2. Et ainsi de suite.
      3. Chaque fiche passe une fois et une seule en test, toujours notée par
         un modèle qui ne l'a jamais vue. Les scores des cinq tours sont
         rassemblés : l'AUC, la calibration et la courbe de ciblage se lisent
         sur tous les avis du passage. Le niveau de base du test est celui du
         corpus, puisque le test EST le corpus.

    Les auteurs. À chaque tour, un avis du groupe testé dont l'auteur a aussi
    écrit sur une fiche d'ajustement est écarté du test de ce tour, sinon le
    modèle jugerait un auteur déjà vu. Cet avis ne reçoit alors aucun score ;
    leur nombre est affiché. Il reste bien dans l'ajustement des quatre autres
    tours, puisque sa fiche y figure.

    Le taux de suppression de chaque groupe testé est affiché à côté de celui du
    corpus, pour voir d'un coup d'œil si un groupe concentre les suppressions.

    Renvoie la cible et le score des avis notés, dans le même ordre.
    """
    tirage = np.random.default_rng(GRAINE)
    # Tri avant mélange : BigQuery ne garantit pas l'ordre des lignes, et sans
    # tri la même graine répartirait les fiches autrement à chaque lecture.
    fiches = np.sort(df["cid"].astype(str).unique())
    tirage.shuffle(fiches)
    groupe_de_fiche = pd.Series(np.arange(len(fiches)) % N_TOURS, index=fiches)
    groupe = df["cid"].astype(str).map(groupe_de_fiche).to_numpy()

    taux_corpus = df["supprime"].mean() * 10000
    ys, scores, fenetres_longues = [], [], []
    for tour in range(N_TOURS):
        est_teste = groupe == tour
        ajustement = df[~est_teste]
        auteurs_vus = set(ajustement["author_key"].astype(str))
        auteur_deja_vu = df["author_key"].astype(str).isin(auteurs_vus).to_numpy()
        test = df[est_teste & ~auteur_deja_vu]
        ecartes = int((est_teste & auteur_deja_vu).sum())

        res_t, _, colonnes_t, taux_t = ajuster(ajustement, f"{suffixe} tour {tour + 1}",
                                               avec_region)
        X_t = matrice_modele(test, avec_region).reindex(columns=colonnes_t, fill_value=0.0)
        scores.append(corriger_probabilites(res_t.predict(X_t), taux_t))
        ys.append(test["supprime"].to_numpy())
        fenetres_longues.append(
            (test["fenetre_observation_j"] >= SEUIL_FENETRE_LONGUE).to_numpy())

        print(f"  tour {tour + 1} : {test['cid'].nunique():,} fiches testées, "
              f"{len(test):,} avis, {int(test['supprime'].sum()):,} suppressions, "
              f"{test['supprime'].mean() * 10000:.0f} pour 10 000 avis "
              f"(corpus : {taux_corpus:.0f}) ; {ecartes:,} avis écartés, auteur déjà vu"
              .replace(",", " "))

    return (np.concatenate(ys), np.concatenate(scores),
            np.concatenate(fenetres_longues))


def calibration(y, p, n_tranches: int = 10) -> pd.DataFrame:
    tab = pd.DataFrame({"p": p, "y": np.asarray(y)})
    tab["tranche"] = pd.qcut(tab["p"], n_tranches, duplicates="drop")
    return tab.groupby("tranche", observed=True).agg(
        risque_prevu=("p", "mean"), risque_observe=("y", "mean"),
        avis=("y", "size")).reset_index(drop=True)


def dessiner_ciblage(y, scores, suffixe: str, auc: float) -> None:
    """Courbe de ciblage, même dessin que le 09.

    Les avis du test sont rangés du plus risqué au moins risqué selon le
    modèle. En abscisse, la part des avis déjà examinés ; en ordonnée, la part
    des suppressions déjà trouvées. La diagonale grise est un tirage au hasard.
    Lecture d'un repère : « 10 % des avis → 49 % des suppressions » veut dire
    qu'en examinant les 10 % d'avis jugés les plus risqués, on trouve 49 % des
    suppressions du test.
    """
    ordre = np.argsort(-np.asarray(scores), kind="stable")
    y_range = np.asarray(y)[ordre]
    part_avis = np.arange(1, len(y_range) + 1) / len(y_range)
    part_suppressions = np.cumsum(y_range) / y_range.sum()
    reperes = {p: float(part_suppressions[int(len(y_range) * p) - 1])
               for p in (0.10, 0.20, 0.50)}

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.plot([0, 1], [0, 1], "--", color="grey", lw=1, label="tirage au hasard")
    ax.plot(part_avis, part_suppressions, lw=2, label="modèle")
    for p, trouve in reperes.items():
        ax.plot(p, trouve, "o", color="black")
        ax.annotate(f"{p:.0%} des avis → {trouve:.0%} des suppressions",
                    (p, trouve), xytext=(8, -12), textcoords="offset points", fontsize=8)
    ax.set_xlabel("part des avis examinés, des plus risqués aux moins risqués")
    ax.set_ylabel("part des suppressions trouvées")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.02)
    effectifs = (f"{len(y_range):,} avis / {int(y_range.sum()):,} suppressions"
                 .replace(",", " "))
    ax.set_title(f"07B {suffixe} — AUC {auc:.3f}\n{effectifs}")
    ax.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(SORTIES / f"07B_ciblage_{suffixe}.png", dpi=150)
    plt.close(fig)

    # La courbe en 200 points, pour qu'une note puisse la redessiner sans
    # relancer les cinq tours. Aucun identifiant d'avis n'y figure : ce sont
    # deux parts cumulées, rien d'autre.
    #
    # Les repères sont écrits à part, avec leur valeur exacte. Les relire sur
    # la courbe échantillonnée donnait 31 % là où le passage annonce 32 % : un
    # point sur 176 est gardé, et la courbe est raide au début.
    pas = max(1, len(y_range) // 200)
    pd.DataFrame({
        "part_avis": part_avis[::pas],
        "part_suppressions": part_suppressions[::pas],
    }).to_csv(SORTIES / f"07B_courbe_ciblage_{suffixe}.csv", index=False)
    pd.DataFrame({"part_avis": list(reperes),
                  "part_suppressions": list(reperes.values())}).to_csv(
        SORTIES / f"07B_reperes_ciblage_{suffixe}.csv", index=False)

    print("  ciblage : " + " ; ".join(
        f"{p:.0%} des avis → {t:.0%} des suppressions" for p, t in reperes.items()))


def concentration(df: pd.DataFrame) -> pd.DataFrame:
    """Combien de fiches portent les suppressions, et à quel point.

    Quatre nombres, écrits dans un CSV pour qu'une note n'ait pas à les
    recopier à la main. Le `03` ne les produisait pas : ils étaient mesurés à
    part, puis recopiés dans le texte du script, où ils ont vieilli.
    """
    par_fiche = (df.groupby("cid", observed=True)["supprime"].sum()
                 .sort_values(ascending=False))
    touchees = par_fiche[par_fiche > 0]
    total = int(par_fiche.sum())
    return pd.DataFrame([{
        "fiches": int(df["cid"].nunique()),
        "fiches_touchees": int(len(touchees)),
        "suppressions": total,
        "part_50_plus_touchees_pct":
            round(touchees.head(50).sum() / total * 100, 1) if total else float("nan"),
        "part_100_plus_touchees_pct":
            round(touchees.head(100).sum() / total * 100, 1) if total else float("nan"),
    }])


def tableau_croise(df: pd.DataFrame) -> pd.DataFrame:
    """Taux de suppression par caractéristique, sans ajustement.
    Dénominateur : le nombre d'avis du groupe.

    Les trois variables écartées du modèle figurent quand même ici : elles
    restent descriptives, c'est leur usage comme régresseur qui pose problème.
    """
    lignes = []
    for var in VARIABLES_BINAIRES + ["langue_etrangere_au_pays", "langue_inconnue",
                                     "rythme_fiche_inconnu",
                                     "star", "bucket", "secteur",
                                     "palier_local_guide", "tranche_photos_auteur", "taille_texte",
                                     "n_avis_meme_jour_auteur",
                                     # Propres au panel 03B : l'exposition et
                                     # les trois colonnes de modification, qui
                                     # ne sont lisibles qu'ici.
                                     "age_a_la_premiere_observation_j",
                                     "tranche_fenetre", "ne_pendant_la_surveillance",
                                     "avis_modifie", "note_modifiee", "texte_modifiee",
                                     "reponse_avant_surveillance",
                                     "reponse_dans_les_2_jours"]:
        g = df.groupby(var, observed=True)["supprime"].agg(["sum", "size"])
        for valeur, row in g.iterrows():
            lignes.append({
                "caracteristique": var, "valeur": valeur,
                "avis": int(row["size"]), "suppressions": int(row["sum"]),
                "taux_pour_10000_avis": round(row["sum"] / row["size"] * 10000, 1),
            })
    return pd.DataFrame(lignes)


# ---------------------------------------------------------------------------
# Programme
# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(
        description="Régression logistique sur le panel entier. "
                    "Aucun découpage selon l'âge : il est variable de contrôle.")
    ap.add_argument("--region", default="tous", choices=["US", "Europe", "tous"])
    ap.add_argument("--sans-enseignes-signalees", action="store_true",
                    help="retire les 4 chaînes antiparasitaires et les 2 salles espagnoles")
    ap.add_argument("--sans-avis-modifies", action="store_true",
                    help="retire les 280 avis réécrits par leur auteur, dont la "
                         "première observation est la date de détection de la "
                         "modification et non celle de la publication")
    ap.add_argument("--sans-vus-tardivement", action="store_true",
                    help=f"retire les avis vus pour la première fois au "
                         f"{SEUIL_VU_TARDIVEMENT}e jour ou plus tard")
    args = ap.parse_args()

    SORTIES.mkdir(exist_ok=True)
    client = client_bigquery()

    df = compacter(lire(client))

    if args.region != "tous":
        df = df[df["region"] == args.region]
        print(f"[filtre] région {args.region} : {len(df):,} avis".replace(",", " "))
    if args.sans_enseignes_signalees:
        garde = (df["chaine_antiparasitaire_us"] == 0) & (df["salle_de_sport_attaquee"] == 0)
        print(f"[filtre] enseignes signalées retirées : "
              f"{int((~garde).sum()):,} avis".replace(",", " "))
        df = df[garde]
    if args.sans_avis_modifies:
        garde = df["avis_modifie"] == 0
        print(f"[filtre] avis réécrits retirés : "
              f"{int((~garde).sum()):,} avis".replace(",", " "))
        df = df[garde]
    if args.sans_vus_tardivement:
        garde = df["age_a_la_premiere_observation_j"] < SEUIL_VU_TARDIVEMENT
        print(f"[filtre] avis vus au {SEUIL_VU_TARDIVEMENT}e jour ou plus tard "
              f"retirés : {int((~garde).sum()):,} avis".replace(",", " "))
        df = df[garde]

    df = ajouter_variables(df)

    suffixe = (args.region
               + ("_sans_enseignes" if args.sans_enseignes_signalees else "")
               + ("_sans_modifies" if args.sans_avis_modifies else "")
               + ("_sans_tardifs" if args.sans_vus_tardivement else ""))

    n_suppr = int(df["supprime"].sum())
    print(f"\n  avis            {len(df):,}".replace(",", " "))
    print(f"  suppressions    {n_suppr:,}".replace(",", " "))
    print(f"  taux            {n_suppr / len(df) * 100:.2f} % des avis")
    print(f"  établissements  {df['cid'].nunique():,}".replace(",", " "))
    if n_suppr < 100:
        print("\n  Moins de 100 suppressions : le modèle n'est pas ajusté.")
        return 0

    conc = concentration(df)
    conc.to_csv(SORTIES / f"07B_concentration_{suffixe}.csv", index=False)
    print(f"  écrit : 07B_concentration_{suffixe}.csv")

    print("\n--- tableau croisé, avant tout modèle ---")
    croise = tableau_croise(df)
    croise.to_csv(SORTIES / f"07B_croisements_{suffixe}.csv", index=False)
    print(f"  écrit : 07B_croisements_{suffixe}.csv")

    avec_region = args.region == "tous" and df["region"].nunique() > 1
    res, tableau, colonnes, taux = ajuster(df, suffixe, avec_region)
    print(res.summary())
    tableau.index.name = "variable"
    tableau.to_csv(SORTIES / f"07B_coefficients_{suffixe}.csv")
    print(f"\n  écrit : 07B_coefficients_{suffixe}.csv")

    ecrire_summary(res, suffixe, len(df), int(df["supprime"].sum()), taux)
    print(f"  écrit : 07B_summary_{suffixe}.txt")

    print("\n--- le modèle sait-il classer, ses risques sont-ils justes ---")
    y_test, scores, fenetre_longue = cinq_tours(df, avec_region, suffixe)
    if len(y_test) < 500 or y_test.sum() < 20:
        print("  test trop petit : AUC et calibration non calculés.")
        return 0

    auc = aire_sous_courbe(y_test, scores)
    print(f"  AUC sur les cinq tours réunis : {auc:.3f}  "
          "(0,5 = tirage au hasard, 1,0 = classement parfait)")

    # Réécriture du summary, maintenant que l'AUC est connue. Voir ecrire_summary.
    ecrire_summary(res, suffixe, len(df), int(df["supprime"].sum()), taux, auc)

    calib = calibration(y_test, scores)
    calib.to_csv(SORTIES / f"07B_calibration_{suffixe}.csv", index=False)

    # Le graphique de calibration a été remplacé le 2026-09-17 par la courbe de
    # ciblage : 8 de ses 10 points s'entassaient sous 1,5 % et le dernier seul
    # tirait la ligne. La calibration reste lisible dans le CSV ci-dessus.
    dessiner_ciblage(y_test, scores, suffixe, auc)

    # Même courbe à l'intérieur de chaque durée de suivi. Dans chaque courbe,
    # les avis ont été regardés à peu près aussi longtemps : ce que le modèle y
    # repère vient de la note, de l'auteur et des autres caractéristiques,
    # jamais du nombre de jours d'observation. Voir § 5 de l'en-tête.
    for valeur, nom in [(True, f"fenetre_{SEUIL_FENETRE_LONGUE}j_et_plus"),
                        (False, f"fenetre_moins_de_{SEUIL_FENETRE_LONGUE}j")]:
        garde = fenetre_longue == valeur
        y_g, s_g = y_test[garde], scores[garde]
        if y_g.sum() < 20:
            print(f"  {nom} : moins de 20 suppressions, courbe non tracée")
            continue
        auc_g = aire_sous_courbe(y_g, s_g)
        print(f"  {nom} : {len(y_g):,} avis, {int(y_g.sum()):,} suppressions, "
              f"AUC {auc_g:.3f}".replace(",", " "))
        dessiner_ciblage(y_g, s_g, f"{suffixe}_{nom}", auc_g)

    print("\n" + "=" * 78)
    print("  À SAVOIR EN LISANT CES CHIFFRES")
    print("=" * 78)
    print("  - Dénominateur : le nombre d'avis, une ligne par avis.")
    print("  - age_a_la_premiere_observation_j, fenetre_observation_j et")
    print("    vu_tardivement sont des variables de contrôle, PAS des résultats.")
    print("    Elles sont là pour que les autres coefficients se lisent à âge et")
    print("    à durée de suivi comparables. Leurs coefficients ne se citent pas.")
    print("  - fenetre_observation_j n'existait dans aucune version précédente.")
    print("    Sans elle, le modèle mélangerait le risque par jour et le nombre")
    print("    de jours pendant lesquels l'avis a été regardé.")
    print("  - Les effets de note se lisent par rapport à 5 étoiles. La colonne")
    print("    risque_relatif_vs_3_etoiles du CSV rejoue la comparaison depuis")
    print("    l'avis neutre, qui ne porte que 12 suppressions sur tout le panel.")
    print("  - langue_etrangere_au_pays n'est pas dans le modèle : en Europe elle")
    print("    mesure le tourisme. Remplacée par langue_minoritaire_sur_la_fiche.")
    print("  - Les avis encore en ligne au dernier passage n'ont pas fini leur")
    print("    histoire : leur sort est inconnu.")
    c = conc.iloc[0]
    print(f"  - Les suppressions sont concentrées : {int(c['fiches_touchees'])} "
          f"fiches sur {int(c['fiches']):,} en portent".replace(",", " "))
    print(f"    au moins une, les 50 plus touchées en portent "
          f"{c['part_50_plus_touchees_pct']:.0f} %, les 100 plus touchées "
          f"{c['part_100_plus_touchees_pct']:.0f} %.")
    print("    Comparer avec et sans les enseignes signalées.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as erreur:
        print(f"\nARRÊT : {erreur}", file=sys.stderr)
        sys.exit(1)
