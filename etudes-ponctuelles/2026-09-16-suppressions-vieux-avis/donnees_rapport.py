#!/usr/bin/env python3
"""Les chiffres du rapport, en un seul passage. Écrit des CSV dans sorties/.

Séparé de `rapport.py`, qui met en forme, pour qu'aucun chiffre du document ne
soit calculé au moment de la mise en page.
"""
from __future__ import annotations

import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "outils"))
sys.path.insert(0, str(RACINE / "etude-exploratoire" / "scripts"))

from local import connexion  # noqa: E402
from suppressions_corrigees import creer_vue_avis  # noqa: E402

SORTIES = Path(__file__).resolve().parent / "sorties"
JOURS = ("SELECT UNNEST(generate_series(DATE '2026-08-12', DATE '2026-08-24',"
         " INTERVAL 1 DAY))::DATE AS jour")


def main() -> None:
    SORTIES.mkdir(parents=True, exist_ok=True)
    con = connexion(memoire="8GB")
    creer_vue_avis(con, source="reviews")

    # G4 — la note, chez les avis récents et chez les vieux.
    con.execute(f"""
    CREATE OR REPLACE VIEW expo_note AS
    SELECT star, CASE WHEN age <= 30 THEN 'recents' ELSE 'vieux' END AS groupe,
           COUNT(DISTINCT review_id) AS avis_concernes, COUNT(*) AS jours_avis
    FROM (
      SELECT a.review_id, a.star, date_diff('day', CAST(a.created_at AS DATE), j.jour) AS age
      FROM avis a CROSS JOIN ({JOURS}) j
      WHERE CAST(a.first_seen_at AS DATE) <= j.jour
        AND (a.death_at IS NULL OR CAST(a.death_at AS DATE) >= j.jour)
        AND date_diff('day', CAST(a.created_at AS DATE), j.jour) >= 0
    ) GROUP BY 1, 2
    """)
    con.execute("""
    CREATE OR REPLACE VIEW supp_note AS
    SELECT star, CASE WHEN age <= 30 THEN 'recents' ELSE 'vieux' END AS groupe,
           COUNT(*) AS suppressions
    FROM (
      SELECT star, date_diff('day', CAST(created_at AS DATE), CAST(death_at AS DATE)) AS age
      FROM avis WHERE death_at IS NOT NULL
    ) GROUP BY 1, 2
    """)
    con.execute("""
    COPY (
      SELECT e.star AS note, e.groupe, s.suppressions, e.avis_concernes, e.jours_avis,
             ROUND(10000.0 * s.suppressions / e.avis_concernes, 1) AS pour_10000_avis,
             ROUND(1000000.0 * s.suppressions / e.jours_avis, 1) AS par_million
      FROM expo_note e JOIN supp_note s USING (star, groupe) ORDER BY 2, 1
    ) TO '%s' (HEADER, DELIMITER ',')
    """ % (SORTIES / "G4-note.csv").as_posix())

    # Exemples de fiches qui perdent de vieux avis.
    con.execute("""
    COPY (
      WITH vieux AS (
        SELECT review_id, cid, star,
               CAST(created_at AS DATE) AS publie_le,
               CAST(death_at AS DATE) AS supprime_le
        FROM avis WHERE death_at IS NOT NULL
          AND date_diff('day', CAST(created_at AS DATE), CAST(death_at AS DATE)) > 365
      )
      SELECT v.cid, b.country, b.industry, b.bucket, b.review_count_at_build AS avis_a_la_construction,
             COUNT(*) AS vieux_supprimes,
             COUNT(DISTINCT v.publie_le) AS dates_de_publication,
             COUNT(DISTINCT v.supprime_le) AS jours_de_suppression,
             ROUND(AVG(v.star), 2) AS note_moyenne,
             MIN(v.publie_le) AS plus_ancien, MAX(v.publie_le) AS plus_recent
      FROM vieux v LEFT JOIN businesses b USING (cid)
      GROUP BY 1,2,3,4,5 ORDER BY 6 DESC LIMIT 10
    ) TO '%s' (HEADER, DELIMITER ',')
    """ % (SORTIES / "G5-exemples-fiches.csv").as_posix())

    # Un exemple d'avis récent supprimé, sans rien d'identifiant.
    con.execute("""
    COPY (
      SELECT CAST(created_at AS DATE) AS publie_le, CAST(death_at AS DATE) AS supprime_le,
             date_diff('day', CAST(created_at AS DATE), CAST(death_at AS DATE)) AS age_j,
             star AS note, COUNT(*) AS combien_d_avis_dans_ce_cas
      FROM avis WHERE death_at IS NOT NULL
        AND CAST(created_at AS DATE) = DATE '2026-08-10'
      GROUP BY 1,2,3,4 ORDER BY 5 DESC LIMIT 8
    ) TO '%s' (HEADER, DELIMITER ',')
    """ % (SORTIES / "G6-exemple-10-aout.csv").as_posix())

    for f in ["G4-note.csv", "G5-exemples-fiches.csv", "G6-exemple-10-aout.csv"]:
        print(f"écrit : {f}")


if __name__ == "__main__":
    main()
