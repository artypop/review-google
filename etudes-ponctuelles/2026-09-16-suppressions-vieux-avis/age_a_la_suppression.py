#!/usr/bin/env python3
"""Les avis récents sont-ils supprimés en premier ?

    python etudes-ponctuelles/2026-09-16-suppressions-vieux-avis/age_a_la_suppression.py

La question porte sur l'âge de l'avis au moment où il disparaît, sans tenir
compte de la date du premier passage du robot. Un avis publié le 10 août et
supprimé le 13 a trois jours : il est récent.

Compter les suppressions par âge ne suffit pas. Un avis de 3 jours et un avis
de 3 ans ne sont pas présents en même nombre dans le parc, et un avis n'est
exposé au risque que les jours où il est en ligne. Le taux se calcule donc sur
l'exposition : pour chaque jour du suivi, les avis en ligne ce jour-là, classés
par leur âge à cette date.

    part d'un âge  = suppressions à cet âge / avis ayant eu cet âge pendant le suivi
    taux journalier = suppressions à cet âge / jours-avis passés à cet âge

La part se lit directement et sert au document. Le taux journalier corrige un
défaut de la part : les tranches ne sont pas observées aussi longtemps. Un avis
de plus de trois ans reste dans sa tranche les 12,9 jours du suivi, un avis de
4 à 7 jours n'y reste que 3,2 jours. À risque égal, la tranche large ramasse
donc plus de suppressions. Les deux colonnes figurent dans la sortie.

La table d'exposition fait 63 millions de lignes. Elle est agrégée en SQL sans
jamais être matérialisée.
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

# Les 13 jours pendant lesquels une disparition peut être constatée : du
# deuxième passage au dernier. Le 11 août est le recensement initial.
JOURS = "SELECT UNNEST(generate_series(DATE '2026-08-12', DATE '2026-08-24', INTERVAL 1 DAY))::DATE AS jour"

TRANCHES = """
CASE WHEN age <= 3    THEN 'a. 0 à 3 jours'
     WHEN age <= 7    THEN 'b. 4 à 7 jours'
     WHEN age <= 14   THEN 'c. 8 à 14 jours'
     WHEN age <= 30   THEN 'd. 15 à 30 jours'
     WHEN age <= 90   THEN 'e. 1 à 3 mois'
     WHEN age <= 365  THEN 'f. 3 mois à 1 an'
     WHEN age <= 1095 THEN 'g. 1 à 3 ans'
     ELSE                  'h. plus de 3 ans' END
"""


def montre(con, titre, sql, fichier=None):
    df = con.execute(sql).df()
    print(f"\n=== {titre} ===\n")
    print(df.to_string(index=False))
    if fichier:
        df.to_csv(SORTIES / fichier, index=False)
    return df


def main() -> None:
    SORTIES.mkdir(parents=True, exist_ok=True)
    con = connexion(memoire="8GB")
    creer_vue_avis(con, source="reviews")

    con.execute(f"""
    CREATE OR REPLACE VIEW expo AS
    SELECT {TRANCHES} AS tranche, COUNT(DISTINCT review_id) AS avis_concernes,
           COUNT(*) AS jours_avis
    FROM (
      SELECT a.review_id, date_diff('day', CAST(a.created_at AS DATE), j.jour) AS age
      FROM avis a CROSS JOIN ({JOURS}) j
      WHERE CAST(a.first_seen_at AS DATE) <= j.jour
        AND (a.death_at IS NULL OR CAST(a.death_at AS DATE) >= j.jour)
        AND date_diff('day', CAST(a.created_at AS DATE), j.jour) >= 0
    ) GROUP BY 1
    """)

    con.execute(f"""
    CREATE OR REPLACE VIEW supp AS
    SELECT {TRANCHES} AS tranche, COUNT(*) AS suppressions
    FROM (
      SELECT date_diff('day', CAST(created_at AS DATE), CAST(death_at AS DATE)) AS age
      FROM avis WHERE death_at IS NOT NULL
    ) GROUP BY 1
    """)

    montre(con, "L'âge de l'avis au moment de sa suppression", """
    SELECT s.tranche AS age_a_la_suppression,
           s.suppressions,
           ROUND(100.0 * s.suppressions / SUM(s.suppressions) OVER (), 1) AS part_des_suppressions_pct,
           e.avis_concernes,
           ROUND(10000.0 * s.suppressions / e.avis_concernes, 1) AS supprimes_pour_10000_avis,
           ROUND(1.0 * e.jours_avis / e.avis_concernes, 1) AS jours_observes_par_avis,
           ROUND(1000000.0 * s.suppressions / e.jours_avis, 1) AS supprimes_par_million_de_jours
    FROM supp s JOIN expo e USING (tranche) ORDER BY 1
    """, "E1-age-a-la-suppression.csv")

    montre(con, "Les quinze premiers jours de vie, jour par jour", """
    WITH e AS (
      SELECT age, COUNT(*) AS jours_avis FROM (
        SELECT date_diff('day', CAST(a.created_at AS DATE), j.jour) AS age
        FROM avis a CROSS JOIN (%s) j
        WHERE CAST(a.first_seen_at AS DATE) <= j.jour
          AND (a.death_at IS NULL OR CAST(a.death_at AS DATE) >= j.jour)
          AND date_diff('day', CAST(a.created_at AS DATE), j.jour) BETWEEN 0 AND 15
      ) GROUP BY 1
    ), s AS (
      SELECT date_diff('day', CAST(created_at AS DATE), CAST(death_at AS DATE)) AS age,
             COUNT(*) AS suppressions
      FROM avis WHERE death_at IS NOT NULL
        AND date_diff('day', CAST(created_at AS DATE), CAST(death_at AS DATE)) BETWEEN 0 AND 15
      GROUP BY 1
    )
    SELECT e.age AS age_en_jours, COALESCE(s.suppressions, 0) AS suppressions,
           e.jours_avis AS avis_exposes,
           ROUND(10000.0 * COALESCE(s.suppressions, 0) / e.jours_avis, 1) AS pour_10000_exposes
    FROM e LEFT JOIN s USING (age) ORDER BY 1
    """ % JOURS, "E2-quinze-premiers-jours.csv")

    montre(con, "Un avis récent, c'est quelle part des suppressions", """
    SELECT CASE WHEN age <= 30 THEN 'récent : 30 jours ou moins'
                ELSE 'ancien : plus de 30 jours' END AS categorie,
           COUNT(*) AS suppressions,
           ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS part_pct
    FROM (SELECT date_diff('day', CAST(created_at AS DATE), CAST(death_at AS DATE)) AS age
          FROM avis WHERE death_at IS NOT NULL)
    GROUP BY 1 ORDER BY 2 DESC
    """, "E3-recents-contre-anciens.csv")

    print(f"\nSorties écrites dans {SORTIES}")


if __name__ == "__main__":
    main()
