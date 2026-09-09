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

Résultat : 5 230 disparitions brutes -> 4 747 suppressions retenues.

La référence de cette logique est `logistic-regression-study/sql/01_build_avis_deleted_panel.sql`,
en BigQuery. Ce module la réimplémente pour les scripts qui tournent en local sur les parquet.
C'est la seule copie hors BigQuery : si la définition change là-bas, ce fichier est à reprendre,
et lui seul — c'est tout l'intérêt de l'avoir sorti ici plutôt que recopié dans chaque script.
"""

import pathlib
import re

import duckdb

RAW = pathlib.Path("data/exports/exports")


def connect(memoire: str = "6GB") -> duckdb.DuckDBPyConnection:
    """Ouvre DuckDB sur les parquet et crée les vues `avis`, `waves`, `base`.

    `avis` : une ligne par avis, avec `death_at` = date de suppression corrigée (NULL si
    jamais supprimé). C'est la vue sur laquelle tout le reste se construit.
    """
    c = duckdb.connect(config={"memory_limit": memoire})
    c.sql("SET enable_progress_bar=false")  # la barre de progression pollue les sorties
    c.sql(f"CREATE VIEW reviews_brut AS SELECT * FROM '{(RAW / 'reviews.parquet').as_posix()}'")
    c.sql(f"CREATE VIEW waves      AS SELECT * FROM '{(RAW / 'waves.parquet').as_posix()}'")

    # Lignes de base seules : les lignes de version d'édition dupliqueraient le compte.
    c.sql("""
        CREATE VIEW base AS
        SELECT review_id, cid, text, created_at, first_seen_at, deleted_detected_at
        FROM reviews_brut WHERE NOT is_update
    """)
    c.sql("""
        CREATE VIEW flags AS
        SELECT review_id,
               bool_or(deleted_detected_at IS NOT NULL) AS a_disparu,
               bool_or(deleted_detected_at IS NULL)     AS a_un_retour,
               count(DISTINCT text)                     AS n_textes
        FROM base GROUP BY review_id
    """)
    c.sql("""
        CREATE VIEW avis AS
        WITH resurrected AS (   -- disparu puis revenu, texte inchangé
            SELECT review_id FROM flags WHERE a_disparu AND a_un_retour AND n_textes <= 1),
        edit_bugs AS (          -- texte réécrit : bug de collecte, pas une suppression
            SELECT review_id FROM flags WHERE a_disparu AND a_un_retour AND n_textes = 2),
        retours AS (
            SELECT review_id, min(first_seen_at) AS reapparu_le
            FROM base WHERE deleted_detected_at IS NULL GROUP BY review_id),
        instances AS (
            SELECT b.review_id, b.deleted_detected_at, ret.reapparu_le
            FROM base b JOIN resurrected USING (review_id) JOIN retours ret USING (review_id)
            WHERE b.deleted_detected_at IS NOT NULL),
        mort_reelle AS (        -- absence de 2 jours ou plus = vraie suppression
            SELECT review_id, min(deleted_detected_at) AS death_at
            FROM instances
            WHERE date_diff('day', deleted_detected_at, reapparu_le) >= 2
            GROUP BY review_id),
        canon AS (
            SELECT review_id, any_value(cid) AS cid,
                   min(first_seen_at) AS first_seen_at, min(created_at) AS created_at,
                   max(deleted_detected_at) AS raw_deleted_at
            FROM base GROUP BY review_id)
        SELECT c.review_id, c.cid, c.first_seen_at, c.created_at,
               CASE WHEN eb.review_id IS NOT NULL THEN NULL
                    WHEN res.review_id IS NOT NULL THEN mr.death_at
                    ELSE c.raw_deleted_at END AS death_at
        FROM canon c
        LEFT JOIN edit_bugs   eb  USING (review_id)
        LEFT JOIN resurrected res USING (review_id)
        LEFT JOIN mort_reelle mr  USING (review_id)
    """)
    return c


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
