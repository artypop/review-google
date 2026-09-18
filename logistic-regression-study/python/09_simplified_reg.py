#!/usr/bin/env python3
"""
==============================================================================
Script : 09_simplified_reg.py
Table source : client-divers.reviewflowz.reviews_panel_features

Régression logistique réduite à cinq caractéristiques, demandée par Romain le
2026-09-17 :

  1. la note, de 1 à 5 étoiles ;
  2. la présence d'une photo ;
  3. la longueur du texte ;
  4. la réponse du propriétaire ;
  5. le nombre d'avis que la fiche reçoit habituellement par jour.

Rien d'autre n'entre dans le modèle. Le 07 garde le modèle complet.

------------------------------------------------------------------------------
LES QUATRE PASSAGES
------------------------------------------------------------------------------
La régression tourne quatre fois, sur quatre populations d'avis :

  US_avec_enseignes       tous les avis des fiches américaines
  US_sans_enseignes       les mêmes, moins les fiches de biz_surveillance
  Europe_avec_enseignes   tous les avis des fiches européennes
  Europe_sans_enseignes   les mêmes, moins les fiches de biz_surveillance

`biz_surveillance` liste 95 fiches : 93 succursales américaines des quatre
chaînes antiparasitaires et les 2 salles de sport espagnoles attaquées. Le
passage « sans » retire donc 93 fiches côté US et 2 côté Europe. Un avis est
rattaché à une enseigne surveillée quand son `cid` figure dans la table ; la
jointure se fait dans BigQuery (voir `lire`).

La région vient de la colonne `region` de la table : « US » si le pays de la
fiche est les États-Unis, « Europe » pour tous les autres.

------------------------------------------------------------------------------
CE QUE LE SCRIPT FAIT, DANS L'ORDRE
------------------------------------------------------------------------------
  1. Il lit les 225 757 avis du panel dans BigQuery, une ligne par avis, une
     seule fois pour les quatre passages.
  2. Il fabrique les cinq colonnes d'entrée (voir `preparer`).
  Puis, pour chacun des quatre passages :
  3. Il écrit un tableau croisé : pour chaque valeur de chaque caractéristique,
     combien d'avis, combien de suppressions, combien de suppressions pour
     10 000 avis. Aucun modèle à ce stade : ce sont les chiffres bruts.
  4. Il ajuste le modèle sur tous les avis du passage et écrit le tableau des
     effets.
  5. Il met de côté un quart des AVIS, tirés au hasard, réajuste le modèle sur
     les trois quarts restants, puis regarde sur ce quart :
       - s'il classe bien les avis (un avis supprimé reçoit-il un score plus
         haut qu'un avis resté en ligne ?) : graphique `09_ciblage_*.png` ;
       - si les risques qu'il annonce correspondent à ce qui s'est passé :
         tableau `09_justesse_*.csv`.
  Enfin :
  6. Il rassemble les effets des quatre passages dans un seul fichier,
     `09_effets_4_passages.csv`, une ligne par caractéristique et par passage.

Le calcul prend quelques minutes. La lecture BigQuery est la partie la plus
longue.

------------------------------------------------------------------------------
LE QUART MIS DE CÔTÉ EST TIRÉ AVIS PAR AVIS
------------------------------------------------------------------------------
Décision de Romain du 2026-09-17. CLAUDE.md (§ 4 point 3) prévoit un tirage
par établissement et par auteur ; ce script s'en écarte.

Conséquence : deux avis d'une même fiche peuvent tomber l'un dans les trois
quarts d'ajustement, l'autre dans le quart de contrôle. Le contrôle mesure
donc la qualité du modèle sur des avis nouveaux de fiches déjà vues.

Le modèle ne contient ni l'identifiant de la fiche ni celui de l'auteur : il ne
peut pas apprendre par cœur qu'une fiche précise perd ses avis. Le seul lien
entre les deux côtés passe par les cinq caractéristiques elles-mêmes. Exemple :
les 192 suppressions de la salle de sport 3163466139043001754 se répartissent
entre les deux côtés, et elles pèsent sur l'effet de 1 étoile des deux côtés à
la fois.

La graine GRAINE fixe le tirage : relancer le script redonne le même partage.

------------------------------------------------------------------------------
COMMENT LIRE UNE LIGNE DU TABLEAU DES EFFETS
------------------------------------------------------------------------------
La colonne à lire est `risque_relatif`. Elle compare deux avis identiques en
tout point sur les quatre autres caractéristiques, et qui ne diffèrent que par
celle de la ligne.

Exemple de lecture, avec une valeur inventée : si la ligne `has_photo` vaut
0,50, un avis avec photo disparaît deux fois moins souvent qu'un avis de même
note, même longueur de texte, même situation de réponse, sur une fiche au même
rythme, mais sans photo. Si elle vaut 2,0, il disparaît deux fois plus souvent.

`borne_basse` et `borne_haute` encadrent la valeur. Quand la fourchette contient
1, les données ne permettent pas de dire dans quel sens joue la caractéristique.

Les caractéristiques à plusieurs valeurs (note, longueur de texte) se lisent
par rapport à une valeur de référence, qui n'a pas de ligne estimée :
  - la note se compare à l'avis 5 étoiles ;
  - la longueur se compare à l'avis sans texte.
La ligne `etoiles_1` à 4,0 voudrait dire : un avis 1 étoile disparaît 4 fois
plus qu'un avis 5 étoiles qui lui ressemble sur le reste.

Le terme `risque_relatif` est un raccourci. Le modèle compare des cotes (le
rapport « supprimé / resté en ligne »). Tant que les suppressions restent
rares, autour de 1 % des avis sur ce panel, les deux se confondent.

------------------------------------------------------------------------------
TROIS CHOIX DE CONSTRUCTION À CONNAÎTRE
------------------------------------------------------------------------------
A. La réponse du propriétaire est `a_une_reponse`.

   Décision de Romain du 2026-09-17. La colonne vaut 1 si l'avis portait une
   réponse du propriétaire au dernier passage du robot où on l'a vu, 0 sinon.
   Pour un avis supprimé, c'est l'état la veille de sa disparition ; pour un
   avis resté en ligne, l'état au 24 août.

   Le 07 utilise `reponse_avant_surveillance`, qui ne compte que les réponses
   déposées avant le 11 août. Les effets de la réponse dans le 07 et dans le
   09 ne se comparent donc pas directement.

B. Le nombre d'avis par jour de la fiche est `rythme_fiche_avant_vague1`.

   Confirmé par Romain le 2026-09-17. C'est le nombre d'avis reçus par la fiche
   sur les 365 jours avant le 11 août, divisé par 365. Il vaut la même chose
   pour tous les avis d'une fiche. Il mesure une fiche très active (un
   restaurant qui reçoit 5 avis par jour) ou très calme (un plombier qui en
   reçoit un par mois).

   Le rythme entre dans le modèle en logarithme de base 2. Conséquence pour la
   lecture : le `risque_relatif` de cette ligne dit ce qui se passe quand le
   rythme de la fiche DOUBLE. À 0,80, un avis sur une fiche qui reçoit 4 avis
   par jour disparaît 20 % moins qu'un avis sur une fiche qui en reçoit 2, et
   20 % moins encore sur une fiche à 8. Sans logarithme, le modèle donnerait
   le même effet au passage de 0 à 1 avis par jour qu'au passage de 30 à 31.

C. La longueur du texte est découpée en quatre tranches :
   sans texte, 1 à 50 caractères, 51 à 200, plus de 200.
   Ce sont les tranches du 07, gardées pour que les deux modèles se comparent.

L'âge de l'avis n'est pas dans le modèle, à la demande de Romain.

------------------------------------------------------------------------------
COMMANDE
------------------------------------------------------------------------------
  nice -n 19 .venv/bin/python logistic-regression-study/python/09_simplified_reg.py
==============================================================================
"""

from __future__ import annotations

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


# ---------------------------------------------------------------------------
# Réglages
# ---------------------------------------------------------------------------

PROJET = "client-divers"
DATASET = "reviewflowz"
TABLE = "reviews_panel_features"
# Les 95 fiches des enseignes signalées. Voir « LES QUATRE PASSAGES ».
TABLE_ENSEIGNES = "biz_surveillance"

# Dossier des clés de service. Le nom du fichier change à chaque rotation de
# clé : on prend le seul `.json` du dossier (même mécanique que le 07).
DOSSIER_CLES = Path("/home/romain/.gcp")

SORTIES = (Path(__file__).resolve().parent.parent / "output-study"
           / f"{date.today():%Y-%m-%d}-sorties-09")

# Nombre d'avis par jour de la fiche. Voir le choix B de l'en-tête.
COLONNE_RYTHME = "rythme_fiche_avant_vague1"

# Longueur du texte, en caractères. Les bornes se lisent ainsi :
# (-1, 0] = 0 caractère, (0, 50] = 1 à 50, (50, 200] = 51 à 200, au-delà = 201+.
TRANCHES_TEXTE = [-1, 0, 50, 200, 10**6]
NOMS_TRANCHES_TEXTE = ["sans_texte", "texte_1_50", "texte_51_200", "texte_201p"]

# Valeurs de référence : chaque effet de la famille se lit par rapport à elles.
# 5 étoiles est la note qui porte le plus de suppressions du panel (1 850,
# contre 26 pour 3 étoiles, mesuré le 2026-09-14). Une référence avec peu de
# suppressions élargirait les fourchettes de toutes les autres notes.
REFERENCE_ETOILES = "etoiles_5"
REFERENCE_TEXTE = "texte_sans_texte"

# Un quart des avis mis de côté pour le contrôle de qualité, tiré avis par
# avis. Voir « LE QUART MIS DE CÔTÉ EST TIRÉ AVIS PAR AVIS ».
PART_TEST = 0.25
GRAINE = 20260917

REGIONS = ["US", "Europe"]

COLONNES_LUES = [
    # identifiants, jamais dans le modèle : l'avis sert à ordonner le tirage du
    # contrôle, la fiche aux marges d'incertitude
    "p.review_id", "p.cid",
    # sert à découper US / Europe
    "p.region",
    # la cible : 1 si l'avis a disparu pendant le suivi, 0 sinon
    "p.supprime",
    # les cinq caractéristiques
    "p.star", "p.has_photo", "p.text_chars", "p.a_une_reponse",
    f"p.{COLONNE_RYTHME}",
]


# ---------------------------------------------------------------------------
# 1. Lecture
# ---------------------------------------------------------------------------

def trouver_cle() -> str | None:
    """La clé de service, quel que soit son nom de fichier.

    Si GOOGLE_APPLICATION_CREDENTIALS est déjà posé, on n'y touche pas.
    Plusieurs `.json` dans le dossier veut dire qu'une rotation est en cours :
    le script s'arrête pour ne pas prendre la mauvaise.
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


def lire() -> pd.DataFrame:
    """Charge le panel entier depuis BigQuery, une ligne par avis.

    La colonne `enseigne_surveillee` vaut 1 quand la fiche de l'avis figure
    dans `biz_surveillance`. Le LEFT JOIN garde tous les avis du panel : un avis
    dont la fiche est absente de la table reçoit 0. `biz_surveillance` a un
    `cid` par ligne (95 lignes, 95 `cid` distincts, vérifié le 2026-09-17), la
    jointure ne duplique donc aucun avis.
    """
    cle = trouver_cle()
    if cle:
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = cle
        print(f"[auth] clé : {Path(cle).name}")
    from google.cloud import bigquery

    client = bigquery.Client(project=PROJET)
    sql = f"""
        SELECT {', '.join(COLONNES_LUES)},
               s.cid IS NOT NULL AS enseigne_surveillee
        FROM `{PROJET}.{DATASET}.{TABLE}` p
        LEFT JOIN `{PROJET}.{DATASET}.{TABLE_ENSEIGNES}` s ON s.cid = p.cid
    """

    # Estimation du volume lu, avant de lancer la vraie requête.
    estime = client.query(
        sql, job_config=bigquery.QueryJobConfig(dry_run=True)
    ).total_bytes_processed / 1024**2
    print(f"[lecture] {estime:.0f} Mo à lire")

    df = client.query(sql).to_dataframe()
    print(f"[lecture] {len(df):,} avis".replace(",", " "))
    return df


# ---------------------------------------------------------------------------
# 2. Préparation des cinq caractéristiques
# ---------------------------------------------------------------------------

def preparer(df: pd.DataFrame) -> pd.DataFrame:
    """Met chaque caractéristique sous la forme que le modèle attend."""
    df = df.copy()

    # La cible, en 0 / 1.
    df["supprime"] = df["supprime"].astype(int)
    df["enseigne_surveillee"] = df["enseigne_surveillee"].astype(bool)

    # 1. La note. Gardée en catégorie : le modèle estime un effet par note, sans
    #    supposer que passer de 1 à 2 étoiles joue autant que passer de 4 à 5.
    df["etoiles"] = "etoiles_" + df["star"].astype(int).astype(str)

    # 2. La photo, en 0 / 1.
    df["has_photo"] = df["has_photo"].astype(int)

    # 3. La longueur du texte, en quatre tranches. Un avis sans texte a
    #    `text_chars` à 0 dans la table.
    df["taille_texte"] = pd.cut(
        df["text_chars"].fillna(0).clip(lower=0),
        bins=TRANCHES_TEXTE, labels=NOMS_TRANCHES_TEXTE)
    df["taille_texte"] = "texte_" + df["taille_texte"].astype(str)

    # 4. La réponse du propriétaire, au dernier passage du robot.
    #    Voir le choix A de l'en-tête.
    df["a_une_reponse"] = df["a_une_reponse"].astype(int)

    # 5. Le nombre d'avis par jour de la fiche.
    #    Une valeur vide veut dire que la fiche n'a reçu aucun avis dans les
    #    365 jours avant le 11 août : la requête de `sql/02` ne lui crée alors
    #    pas de ligne. Elle vaut donc 0 avis par jour. 12 avis du panel sont
    #    dans ce cas.
    rythme = df[COLONNE_RYTHME].fillna(0).clip(lower=0)
    df["rythme_brut"] = rythme
    # log2(1 + rythme) : +1 sur cette échelle = le rythme double, à peu près.
    # Le « 1 + » évite le logarithme de zéro.
    df["log2_rythme_fiche"] = np.log2(1 + rythme)

    return df


def matrice(df: pd.DataFrame) -> pd.DataFrame:
    """Transforme les caractéristiques en colonnes de nombres.

    Une caractéristique à plusieurs valeurs devient une colonne 0 / 1 par
    valeur. La valeur de référence n'a pas de colonne : c'est le point de
    comparaison des autres.

    La colonne `const` représente l'avis de référence : 5 étoiles, sans photo,
    sans texte, sans réponse, sur une fiche à 0 avis par jour.
    """
    etoiles = pd.get_dummies(df["etoiles"], dtype=float).drop(columns=[REFERENCE_ETOILES])
    texte = pd.get_dummies(df["taille_texte"], dtype=float).drop(columns=[REFERENCE_TEXTE])
    X = pd.concat([
        etoiles,
        df[["has_photo"]].astype(float),
        texte,
        df[["a_une_reponse"]].astype(float),
        df[["log2_rythme_fiche"]].astype(float),
    ], axis=1)
    return sm.add_constant(X, has_constant="add")


# ---------------------------------------------------------------------------
# 3. Tableau croisé, sans modèle
# ---------------------------------------------------------------------------

def tableau_croise(df: pd.DataFrame) -> pd.DataFrame:
    """Taux de suppression brut pour chaque valeur de chaque caractéristique.

    Dénominateur : le nombre d'avis qui ont cette valeur.
    Le rythme de fiche est découpé en tranches pour pouvoir être lu ici ; le
    modèle, lui, l'utilise en continu.
    """
    df = df.copy()
    df["tranche_rythme_fiche"] = pd.cut(
        df["rythme_brut"],
        bins=[-0.001, 0.1, 0.5, 1, 3, 10, np.inf],
        labels=["moins_de_0.1_par_jour", "0.1_a_0.5", "0.5_a_1",
                "1_a_3", "3_a_10", "plus_de_10"])

    lignes = []
    for var in ["etoiles", "has_photo", "taille_texte",
                "a_une_reponse", "tranche_rythme_fiche"]:
        g = df.groupby(var, observed=True)["supprime"].agg(["sum", "size"])
        for valeur, row in g.iterrows():
            lignes.append({
                "caracteristique": var,
                "valeur": valeur,
                "avis": int(row["size"]),
                "suppressions": int(row["sum"]),
                "suppressions_pour_10000_avis": round(row["sum"] / row["size"] * 10000, 1),
            })
    return pd.DataFrame(lignes)


# ---------------------------------------------------------------------------
# 4. Ajustement du modèle
# ---------------------------------------------------------------------------

def ajuster(df: pd.DataFrame):
    """Ajuste la régression logistique et renvoie le tableau des effets.

    Marges d'incertitude groupées par établissement (`cov_type="cluster"`).
    Les avis d'une même fiche se ressemblent : 192 suppressions sur une seule
    salle de sport ne sont pas 192 observations indépendantes. Sans ce
    regroupement, les fourchettes seraient trop étroites.
    """
    y = df["supprime"].astype(float)
    X = matrice(df)
    res = sm.GLM(y, X, family=sm.families.Binomial()).fit(
        cov_type="cluster", cov_kwds={"groups": df["cid"].astype(str).factorize()[0]})

    ic = res.conf_int()
    tableau = pd.DataFrame({
        "coefficient": res.params,
        "risque_relatif": np.exp(res.params),
        "borne_basse": np.exp(ic[0]),
        "borne_haute": np.exp(ic[1]),
        "p_value": res.pvalues,
    })

    # Lignes des références, pour qu'elles apparaissent dans le fichier.
    # Elles valent 1 par construction : ce sont les points de comparaison.
    references = pd.DataFrame(
        {"coefficient": 0.0, "risque_relatif": 1.0, "borne_basse": 1.0,
         "borne_haute": 1.0, "p_value": np.nan},
        index=[REFERENCE_ETOILES, REFERENCE_TEXTE])
    tableau = pd.concat([tableau, references])
    tableau.index.name = "variable"

    # La constante n'est pas un effet : c'est le niveau de l'avis de référence,
    # exprimé en cote. On la garde dans le fichier mais on ne la lit pas comme
    # un risque relatif.
    return res, tableau


def ordonner(tableau: pd.DataFrame) -> pd.DataFrame:
    """Range les lignes dans l'ordre de lecture : note, photo, texte, réponse, rythme."""
    ordre = (["const"]
             + [f"etoiles_{i}" for i in range(1, 6)]
             + ["has_photo"]
             + [f"texte_{n}" for n in NOMS_TRANCHES_TEXTE]
             + ["a_une_reponse", "log2_rythme_fiche"])
    return tableau.reindex([v for v in ordre if v in tableau.index])


# ---------------------------------------------------------------------------
# 5. Contrôle de qualité sur le quart d'avis mis de côté
# ---------------------------------------------------------------------------

def tirer_le_controle(df: pd.DataFrame) -> pd.Series:
    """Désigne, une fois pour tout le panel, le quart des avis mis de côté.

    Chaque avis reçoit un nombre au hasard entre 0 et 1. S'il est sous 0,25,
    l'avis va au contrôle. Voir « LE QUART MIS DE CÔTÉ EST TIRÉ AVIS PAR AVIS »
    dans l'en-tête.

    Le tirage se fait sur le panel entier, avant de découper les passages. Un
    avis américain hors enseigne tombe ainsi du même côté dans
    « US_avec_enseignes » et dans « US_sans_enseignes » : les deux passages se
    comparent sur le même partage.

    Les avis sont triés par `review_id` avant le tirage. BigQuery ne garantit
    pas l'ordre des lignes d'une lecture à l'autre ; sans ce tri, la même
    graine donnerait un partage différent à chaque lancement.
    """
    ordre = df["review_id"].sort_values().index
    tirage = np.random.default_rng(GRAINE).random(len(df))
    au_hasard = pd.Series(tirage, index=ordre)
    return (au_hasard < PART_TEST).reindex(df.index)


def aire_sous_courbe(y, score) -> float:
    """Capacité à classer.

    On tire au hasard un avis supprimé et un avis resté en ligne. La valeur
    renvoyée est la part des tirages où l'avis supprimé a le score le plus
    haut. 0,5 : le modèle ne fait pas mieux qu'une pièce. 1,0 : il classe
    parfaitement.
    """
    y = np.asarray(y)
    n_pos, n_neg = int(y.sum()), int((1 - y).sum())
    rangs = pd.Series(np.asarray(score)).rank(method="average").to_numpy()
    return (rangs[y == 1].sum() - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg)


def justesse_des_prevision(y, score, n_groupes: int = 10) -> pd.DataFrame:
    """Justesse des risques annoncés.

    Les avis sont rangés du score le plus bas au plus haut, puis coupés en
    10 groupes de même taille. Pour chaque groupe : le risque moyen annoncé par
    le modèle, et la part des avis réellement supprimés. Si le modèle est
    juste, les deux colonnes sont proches.
    """
    tab = pd.DataFrame({"score": np.asarray(score), "y": np.asarray(y)})
    tab["groupe"] = pd.qcut(tab["score"].rank(method="first"), n_groupes, labels=False) + 1
    return tab.groupby("groupe").agg(
        avis=("y", "size"),
        risque_annonce=("score", "mean"),
        part_reellement_supprimee=("y", "mean"),
    ).reset_index()


def dessiner_ciblage(y, score, nom: str, auc: float) -> None:
    """Courbe de ciblage.

    Les avis du contrôle sont rangés du plus risqué au moins risqué selon le
    modèle. On les parcourt dans cet ordre et, à chaque pas, on note :
      - en abscisse, la part des avis déjà examinés ;
      - en ordonnée, la part des suppressions déjà trouvées.

    Lecture : le point (10 %, 49 %) voudrait dire qu'en examinant les 10 % d'avis
    que le modèle juge les plus risqués, on trouve 49 % des suppressions.
    La diagonale grise est un tirage au hasard : 10 % des avis, 10 % des
    suppressions. Plus la courbe monte vite au-dessus, mieux le modèle classe.

    Avec 1 % d'avis supprimés, cette courbe et la courbe ROC se superposent
    presque ; l'aire sous la courbe ROC est la « capacité à classer » du titre.
    """
    ordre = np.argsort(-np.asarray(score), kind="stable")
    y_range = np.asarray(y)[ordre]
    part_avis = np.arange(1, len(y_range) + 1) / len(y_range)
    part_suppressions = np.cumsum(y_range) / y_range.sum()

    # Valeurs à 10 %, 20 % et 50 % des avis, écrites sur le graphique.
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
    ax.set_title(f"09 {nom} — capacité à classer {auc:.3f}\n{effectifs}")
    ax.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(SORTIES / f"09_ciblage_{nom}.png", dpi=150)
    plt.close(fig)

    print("  ciblage : " + " ; ".join(
        f"{p:.0%} des avis → {t:.0%} des suppressions" for p, t in reperes.items()))


# ---------------------------------------------------------------------------
# Programme
# ---------------------------------------------------------------------------

def un_passage(df: pd.DataFrame, nom: str, au_controle: pd.Series) -> pd.DataFrame:
    """Étapes 3 à 5 de l'en-tête, sur les avis d'un passage.

    `df` ne contient que les avis du passage. `au_controle` dit, pour chaque
    avis du panel, s'il fait partie du quart mis de côté.
    Renvoie le tableau des effets, avec le nom du passage en colonne.
    """
    print("\n" + "=" * 78)
    print(f"  PASSAGE {nom}")
    print("=" * 78)

    n_suppr = int(df["supprime"].sum())
    print(f"  avis            {len(df):,}".replace(",", " "))
    print(f"  suppressions    {n_suppr:,}".replace(",", " "))
    print(f"  soit            {n_suppr / len(df) * 10000:.0f} suppressions pour 10 000 avis")
    print(f"  établissements  {df['cid'].nunique():,}".replace(",", " "))

    # --- 3. tableau croisé --------------------------------------------------
    croise = tableau_croise(df)
    croise.to_csv(SORTIES / f"09_croisements_{nom}.csv", index=False)
    print(f"\n--- chiffres bruts, sans modèle ---\n{croise.to_string(index=False)}")

    # Avertissement : une note ou une tranche de texte avec moins de 5
    # suppressions donne un effet très imprécis, voire absurde. Le passage
    # Europe_sans_enseignes est le plus exposé.
    rares = croise[croise["suppressions"] < 5]
    if not rares.empty:
        print("\n  ATTENTION, valeurs avec moins de 5 suppressions, effet à ne pas citer :")
        print(rares[["caracteristique", "valeur", "avis", "suppressions"]]
              .to_string(index=False))

    # --- 4. modèle sur tous les avis du passage -----------------------------
    res, tableau = ajuster(df)
    tableau = ordonner(tableau)
    tableau.to_csv(SORTIES / f"09_effets_{nom}.csv")
    (SORTIES / f"09_summary_{nom}.txt").write_text(str(res.summary()), encoding="utf-8")

    print("\n--- effets, chaque ligne à autres caractéristiques égales ---")
    print(tableau[["risque_relatif", "borne_basse", "borne_haute"]]
          .drop(index="const").round(2).to_string())

    # --- 5. contrôle de qualité ---------------------------------------------
    print("\n--- le modèle sait-il classer, ses risques sont-ils justes ---")
    est_controle = au_controle.loc[df.index]
    ajustement, controle = df[~est_controle], df[est_controle]
    print(f"  ajustement {len(ajustement):,} avis / contrôle {len(controle):,} avis, "
          f"dont {int(controle['supprime'].sum()):,} suppressions".replace(",", " "))

    res_ajust, _ = ajuster(ajustement)
    # `reindex` : si une valeur (une note, une tranche) manque côté contrôle,
    # sa colonne est recréée à zéro pour que les colonnes correspondent.
    X_controle = matrice(controle).reindex(columns=res_ajust.params.index, fill_value=0.0)
    score = res_ajust.predict(X_controle)

    auc = aire_sous_courbe(controle["supprime"], score)
    print(f"  capacité à classer : {auc:.3f}  (0,5 = hasard, 1,0 = parfait)")

    justesse = justesse_des_prevision(controle["supprime"], score)
    justesse.to_csv(SORTIES / f"09_justesse_{nom}.csv", index=False)
    print(justesse.to_string(index=False))

    dessiner_ciblage(controle["supprime"], score, nom, auc)

    tableau.insert(0, "passage", nom)
    tableau["avis"] = len(df)
    tableau["suppressions"] = n_suppr
    tableau["capacite_a_classer"] = auc
    return tableau


def main() -> int:
    SORTIES.mkdir(parents=True, exist_ok=True)

    # --- 1. lecture, une seule fois -----------------------------------------
    df = lire()

    # --- 2. préparation -----------------------------------------------------
    df = preparer(df).reset_index(drop=True)
    au_controle = tirer_le_controle(df)

    # --- 3 à 5, quatre fois --------------------------------------------------
    tableaux = []
    for region in REGIONS:
        de_la_region = df["region"] == region
        passages = {
            f"{region}_avec_enseignes": de_la_region,
            f"{region}_sans_enseignes": de_la_region & ~df["enseigne_surveillee"],
        }
        for nom, garde in passages.items():
            tableaux.append(un_passage(df[garde], nom, au_controle))

    # --- 6. les quatre passages dans un seul fichier ------------------------
    ensemble = pd.concat(tableaux)
    ensemble.to_csv(SORTIES / "09_effets_4_passages.csv")

    print("\n" + "=" * 78)
    print("  RISQUE RELATIF, LES QUATRE PASSAGES CÔTE À CÔTE")
    print("=" * 78)
    cote_a_cote = (ensemble.drop(index="const")
                   .reset_index()
                   .pivot(index="variable", columns="passage", values="risque_relatif"))
    print(ordonner(cote_a_cote).round(2).to_string())

    print(f"\n  fichiers écrits dans {SORTIES}")
    print("\n  À SAVOIR EN LISANT CES CHIFFRES")
    print("  - Dénominateur : le nombre d'avis du panel, une ligne par avis.")
    print("  - La réponse du propriétaire est a_une_reponse : l'état au dernier")
    print("    passage du robot. Le 07 utilisait reponse_avant_surveillance.")
    print("  - Les notes se lisent par rapport à 5 étoiles, la longueur par rapport")
    print("    à un avis sans texte.")
    print("  - Le rythme de fiche se lit pour un doublement du nombre d'avis par jour.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as erreur:
        print(f"\nARRÊT : {erreur}", file=sys.stderr)
        sys.exit(1)
