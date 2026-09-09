"""
Définition corrigée d'une suppression, en DuckDB — module partagé.

Pourquoi ce module existe : `deleted_detected_at` dans l'export brut veut seulement dire « le
robot ne retrouve plus l'avis à ce passage ». Ce n'est pas Google qui annonce une suppression,
c'est nous qui la déduisons. Deux situations rendent la déduction fausse, et il faut les
retirer avant de compter quoi que ce soit :

  1. Bug d'édition (24 avis) : même auteur, même note, même date de dépôt, texte totalement
     réécrit d'une ligne à l'autre. C'est une modification mal enregistrée par le robot.
  2. Raté de collecte : l'avis est absent un seul jour puis revient à l'identique. Un vrai
     retrait revu par Google prend plusieurs jours, pas vingt-quatre heures.

Les avis absents 2 jours ou plus avant de revenir restent comptés comme supprimés, à la date de
leur première disparition.

Résultat, sur l'export BigQuery du 2026-09-09 : 5 230 lignes de disparition, portées par
5 109 avis distincts, -> 4 737 suppressions retenues. Le 5 230 compte des événements, le
4 737 compte des avis : deux unités différentes, à ne jamais mettre de part et d'autre
d'une flèche sans le dire. Le chiffre de 4 747 cité jusqu'au 2026-09-09 n'a pas été
retrouvé ; écart de 10 non élucidé.

La référence de cette logique est `logistic-regression-study/sql/01_build_avis_deleted_panel.sql`,
en BigQuery. Ce module la réimplémente pour les scripts qui tournent en local sur les parquet.
C'est la seule copie hors BigQuery : si la définition change là-bas, ce fichier est à reprendre,
et lui seul — c'est tout l'intérêt de l'avoir sorti ici plutôt que recopié dans chaque script.
"""

import pathlib
import re

import duckdb

RAW = pathlib.Path("data/exports/exports")

# --------------------------------------------------------------------------------------
# Définition d'une fiche attaquée. Seul endroit où ces seuils sont écrits.
#
# Remplace le critère « plus de 5 % des avis perdus », abandonné le 2026-09-09 après
# vérification fiche par fiche des 24 qu'il retenait : 2 attaquées, 1 autocariste allemand
# qui perd un stock de vieux avis négatifs sur 8 ans (retrait obtenu sur demande, pas une
# attaque), 15 qui ne perdent que leurs avis 4 et 5 étoiles — le phénomène même que
# l'étude documente — et 6 fiches de moins de 25 avis, dont une à 2 avis qui atteignait le
# seuil avec une seule suppression.
#
# Le critère ci-dessous décrit la signature d'une attaque : beaucoup de suppressions,
# presque toutes à 1 étoile, presque toutes sur des avis écrits dans le mois. Il attrape
# aussi les petites attaques sur de grosses fiches, invisibles à un seuil en pourcentage
# (10 suppressions sur 9 545 avis font 0,10 % du stock).
MIN_SUPPRESSIONS_ATTAQUE = 10
PART_MIN_1_ETOILE = 0.8
PART_MIN_AVIS_RECENTS = 0.8
JOURS_AVIS_RECENT = 30


def connect(memoire: str = "6GB") -> duckdb.DuckDBPyConnection:
    """Ouvre DuckDB sur les parquet et crée les vues `avis`, `waves`, `base`.

    `avis` : une ligne par avis, avec `death_at` = date de suppression corrigée (NULL si
    jamais supprimé). C'est la vue sur laquelle tout le reste se construit.
    """
    c = duckdb.connect(config={"memory_limit": memoire})
    c.sql("SET enable_progress_bar=false")  # la barre de progression pollue les sorties
    c.sql(f"CREATE VIEW reviews_brut AS SELECT * FROM '{(RAW / 'reviews.parquet').as_posix()}'")
    c.sql(f"CREATE VIEW waves      AS SELECT * FROM '{(RAW / 'waves.parquet').as_posix()}'")
    creer_vue_avis(c)
    return c


def creer_vue_avis(c: duckdb.DuckDBPyConnection, source: str = "reviews_brut",
                   prefixe: str = "") -> None:
    """Crée les vues `base`, `flags` et `avis` sur une connexion déjà ouverte.

    Sortie utile : la vue `{prefixe}avis`, une ligne par avis, avec `death_at` = date de
    suppression corrigée (NULL si l'avis n'a jamais été supprimé).

    `prefixe` sert aux scripts qui ont déjà des vues portant ces noms : `build_tables.py`
    appelle avec `prefixe="sc_"` pour ne pas écraser sa propre vue `base`.

    Cette fonction est le seul endroit hors BigQuery où la définition d'une suppression
    est écrite. Tout script qui a besoin de savoir si un avis a été supprimé passe par
    elle, jamais par `deleted_detected_at IS NOT NULL`, qui compte aussi les ratés de
    collecte et les bugs d'édition.
    """
    b, f, a = f"{prefixe}base", f"{prefixe}flags", f"{prefixe}avis"

    # Lignes de base seules : les lignes de version d'édition dupliqueraient le compte.
    c.sql(f"""
        CREATE VIEW {b} AS
        SELECT review_id, cid, star, text, created_at, first_seen_at, deleted_detected_at
        FROM {source} WHERE NOT is_update
    """)
    c.sql(f"""
        CREATE VIEW {f} AS
        SELECT review_id,
               bool_or(deleted_detected_at IS NOT NULL) AS a_disparu,
               bool_or(deleted_detected_at IS NULL)     AS a_un_retour,
               count(DISTINCT text)                     AS n_textes
        FROM {b} GROUP BY review_id
    """)
    c.sql(f"""
        CREATE VIEW {a} AS
        WITH resurrected AS (   -- disparu puis revenu, texte inchangé
            SELECT review_id FROM {f} WHERE a_disparu AND a_un_retour AND n_textes <= 1),
        edit_bugs AS (          -- texte réécrit : bug de collecte, pas une suppression
            SELECT review_id FROM {f} WHERE a_disparu AND a_un_retour AND n_textes = 2),
        retours AS (
            SELECT review_id, min(first_seen_at) AS reapparu_le
            FROM {b} WHERE deleted_detected_at IS NULL GROUP BY review_id),
        instances AS (
            SELECT x.review_id, x.deleted_detected_at, ret.reapparu_le
            FROM {b} x JOIN resurrected USING (review_id) JOIN retours ret USING (review_id)
            WHERE x.deleted_detected_at IS NOT NULL),
        mort_reelle AS (        -- absence de 2 jours ou plus = vraie suppression
            SELECT review_id, min(deleted_detected_at) AS death_at
            FROM instances
            WHERE date_diff('day', deleted_detected_at, reapparu_le) >= 2
            GROUP BY review_id),
        canon AS (
            SELECT review_id, any_value(cid) AS cid, any_value(star) AS star,
                   min(first_seen_at) AS first_seen_at, min(created_at) AS created_at,
                   max(deleted_detected_at) AS raw_deleted_at
            FROM {b} GROUP BY review_id)
        SELECT c.review_id, c.cid, c.star, c.first_seen_at, c.created_at,
               CASE WHEN eb.review_id IS NOT NULL THEN NULL
                    WHEN res.review_id IS NOT NULL THEN mr.death_at
                    ELSE c.raw_deleted_at END AS death_at
        FROM canon c
        LEFT JOIN edit_bugs   eb  USING (review_id)
        LEFT JOIN resurrected res USING (review_id)
        LEFT JOIN mort_reelle mr  USING (review_id)
    """)


def creer_vue_fiches_attaquees(c: duckdb.DuckDBPyConnection, prefixe: str = "") -> None:
    """Crée la vue `{prefixe}fiches_attaquees` : un cid par ligne, plus ses compteurs.

    À appeler après `creer_vue_avis`. Sert au contrôle de robustesse : on rejoue les
    modèles sans ces fiches pour vérifier que les conclusions ne reposent pas sur elles.

    Ne pas confondre avec « fiche qui perd beaucoup d'avis ». Une fiche qui perd 40 avis
    tous à 5 étoiles n'est pas attaquée : elle subit exactement ce que l'étude cherche à
    mesurer, et l'écarter reviendrait à retirer le sujet du corpus.
    """
    a, f = f"{prefixe}avis", f"{prefixe}fiches_attaquees"
    c.sql(f"""
        CREATE OR REPLACE VIEW {f} AS
        SELECT cid,
               count(*)                                   AS n_avis,
               count(death_at)                            AS n_supprimes,
               count(*) FILTER (death_at IS NOT NULL AND star = 1)      AS n_supp_1etoile,
               count(*) FILTER (death_at IS NOT NULL
                    AND date_diff('day', created_at, death_at) <= {JOURS_AVIS_RECENT})
                                                          AS n_supp_recents
        FROM {a} GROUP BY cid
        HAVING count(death_at) >= {MIN_SUPPRESSIONS_ATTAQUE}
           AND count(*) FILTER (death_at IS NOT NULL AND star = 1)::DOUBLE
               / count(death_at) >= {PART_MIN_1_ETOILE}
           AND count(*) FILTER (death_at IS NOT NULL
                 AND date_diff('day', created_at, death_at) <= {JOURS_AVIS_RECENT})::DOUBLE
               / count(death_at) >= {PART_MIN_AVIS_RECENTS}
    """)


def vue_panel(c: duckdb.DuckDBPyConnection, source: str = "avis", nom: str = "panel") -> None:
    """Crée la vue d'exposition : un avis × un passage du robot où il est encore en ligne.

    On part de la vague 2 : la vague 1 est le recensement initial, il n'y a rien à comparer
    avant elle. Un avis n'entre qu'à partir du passage suivant celui qui l'a découvert
    (`first_seen_at < w.started_at`), sinon sa découverte compterait comme une exposition.
    """
    c.sql(f"""
        CREATE OR REPLACE VIEW {nom} AS
        WITH a AS (
            SELECT *,
                   (SELECT max(w2.wave) FROM waves w2 WHERE w2.started_at <= s.death_at) AS death_wave
            FROM {source} s)
        SELECT a.review_id, a.cid, w.wave,
               date_diff('day', a.created_at, w.started_at) AS age_days,
               date_trunc('day', a.created_at)              AS jour_publication,
               coalesce(a.death_wave = w.wave, FALSE)       AS deleted
        FROM a
        JOIN waves w
          ON w.wave >= 2
         AND a.first_seen_at < w.started_at
         AND (a.death_wave IS NULL OR w.wave <= a.death_wave)
    """)


def fr(x: float, dec: int = 0) -> str:
    """Nombre au format français : espace pour les milliers, virgule pour les décimales."""
    return f"{x:,.{dec}f}".replace(",", " ").replace(".", ",")


def bloc_ascii(df, label: str, valeur: str, largeur: int = 44, dec: int = 3,
               suffixe: str = " %", largeur_label: int = 20) -> str:
    """Histogramme en barres de texte, lisible tel quel dans un mail.

    Les libellés de tranche portent un préfixe de tri (« a. », « b. »…) qui sert au GROUP BY
    mais n'a rien à faire dans le graphique : on le retire à l'affichage.
    """
    vmax = df[valeur].max()
    lignes = []
    # iterrows() convertit la ligne en Series : un libellé entier y ressort en flottant
    # ("1.0"). On le remet en entier avant de l'écrire.
    for _, r in df.iterrows():
        brut = r[label]
        lib = str(int(brut)) if isinstance(brut, float) and brut.is_integer() else str(brut)
        lib = re.sub(r"^[a-z]\. ", "", lib)
        n = int(round(largeur * r[valeur] / vmax)) if vmax else 0
        lignes.append(f"  {lib:<{largeur_label}} {'#' * n:<{largeur}} {fr(r[valeur], dec)}{suffixe}")
    return "\n".join(lignes)
