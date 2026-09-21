#!/usr/bin/env python3
"""Le pic du 17 août est-il une action de Google ou un raté du robot ?

    python etudes-ponctuelles/2026-09-16-suppressions-vieux-avis/controle_collecte.py

Trois contrôles, dans l'ordre où ils permettent d'écarter l'explication par la
collecte. La règle du projet : privilégier le défaut de collecte tant qu'il
n'est pas écarté, et le démontrer.

  D1. Les suppressions de chaque jour sont-elles définitives ? Un avis revenu,
      même après deux jours, laisse planer le doute. Une journée dont les
      suppressions reviennent en masse est une journée suspecte.
  D2. Le robot voit-il autant d'avis ce jour-là que les autres ? Une journée où
      la couverture s'effondre produit de fausses disparitions.
  D3. Sur les fiches touchées le 17 août, la perte est-elle groupée ou dispersée ?
      Une purge frappe plusieurs avis d'une même fiche. Un raté de pagination
      frappe des avis isolés un peu partout.
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


def montre(con, titre, sql, fichier=None):
    df = con.execute(sql).df()
    print(f"\n=== {titre} ===\n")
    print(df.to_string(index=False))
    if fichier:
        df.to_csv(SORTIES / fichier, index=False)
    return df


def main() -> None:
    SORTIES.mkdir(parents=True, exist_ok=True)
    con = connexion(memoire="6GB")
    creer_vue_avis(con, source="reviews")

    # Un avis est revenu s'il a une ligne sans date de disparition dont la
    # première observation est postérieure à la disparition retenue.
    con.execute("""
    CREATE OR REPLACE VIEW retours AS
    SELECT review_id, MIN(first_seen_at) AS revu_le
    FROM reviews WHERE NOT is_update AND deleted_detected_at IS NULL
    GROUP BY review_id
    """)

    montre(con, "D1. Les suppressions sont-elles définitives ?", """
    SELECT CAST(a.death_at AS DATE) AS supprime_le,
           COUNT(*) AS suppressions,
           SUM((r.revu_le IS NOT NULL AND r.revu_le > a.death_at)::INT) AS revenues_ensuite,
           ROUND(100.0 * SUM((r.revu_le IS NOT NULL AND r.revu_le > a.death_at)::INT)
                 / COUNT(*), 1) AS part_revenues_pct
    FROM avis a LEFT JOIN retours r USING (review_id)
    WHERE a.death_at IS NOT NULL
    GROUP BY 1 ORDER BY 1
    """, "D1-suppressions-definitives.csv")

    montre(con, "D2. La couverture du robot, jour par jour", """
    SELECT CAST(first_seen_at AS DATE) AS jour,
           COUNT(*) AS avis_vus_pour_la_premiere_fois
    FROM reviews WHERE NOT is_update
    GROUP BY 1 ORDER BY 1
    """, "D2-couverture.csv")

    montre(con, "D3. Le 17 août : groupé sur des fiches, ou dispersé ?", """
    WITH le_jour AS (
      SELECT cid, COUNT(*) AS n
      FROM avis WHERE CAST(death_at AS DATE) = DATE '2026-08-17'
      GROUP BY cid
    )
    SELECT CASE WHEN n = 1 THEN 'a. 1 avis perdu' WHEN n <= 3 THEN 'b. 2 à 3'
                WHEN n <= 10 THEN 'c. 4 à 10' ELSE 'd. plus de 10' END AS perte_par_fiche,
           COUNT(*) AS fiches, SUM(n) AS suppressions,
           ROUND(100.0 * SUM(n) / SUM(SUM(n)) OVER (), 1) AS part_pct
    FROM le_jour GROUP BY 1 ORDER BY 1
    """, "D3-groupement-17-aout.csv")

    montre(con, "D3 bis. Le même découpage sur un jour ordinaire, le 20 août", """
    WITH le_jour AS (
      SELECT cid, COUNT(*) AS n
      FROM avis WHERE CAST(death_at AS DATE) = DATE '2026-08-20'
      GROUP BY cid
    )
    SELECT CASE WHEN n = 1 THEN 'a. 1 avis perdu' WHEN n <= 3 THEN 'b. 2 à 3'
                WHEN n <= 10 THEN 'c. 4 à 10' ELSE 'd. plus de 10' END AS perte_par_fiche,
           COUNT(*) AS fiches, SUM(n) AS suppressions,
           ROUND(100.0 * SUM(n) / SUM(SUM(n)) OVER (), 1) AS part_pct
    FROM le_jour GROUP BY 1 ORDER BY 1
    """, "D3bis-groupement-20-aout.csv")

    print(f"\nSorties écrites dans {SORTIES}")


if __name__ == "__main__":
    main()
