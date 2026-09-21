#!/usr/bin/env python3
"""Les suppressions des vieux avis : y a-t-il un motif ?

    python etudes-ponctuelles/2026-09-16-suppressions-vieux-avis/lancer.py

Deux questions posées par Matthieu le 2026-09-16.

  A. Pour chaque date de publication, les suppressions se concentrent-elles sur
     un jour du suivi, ou se répartissent-elles ?
  B. Parmi les avis supprimés, quelle part a été écrite pendant les 14 jours de
     suivi, et quelle part existait avant ?

Périmètre : les 4,88 millions d'avis, sans la borne des 90 jours du panel de
régression. C'est le seul moyen de voir les vieux avis.

La définition d'une suppression vient de
`etude-exploratoire/scripts/suppressions_corrigees.py`, importée telle quelle :
absence de deux jours ou plus, bugs d'édition retirés, datée du jour de la
première disparition. Ce module est la seule copie de la règle hors BigQuery.
Le dossier qui l'héberge est gelé ; on le lit sans rien y écrire ni y relancer.

Contrôle d'entrée : la vue doit redonner 4 737 suppressions, le chiffre que ce
module produit d'après son propre en-tête.
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
PREMIERE_VAGUE = "2026-08-11"
DERNIERE_VAGUE = "2026-08-24"


def montre(con, titre: str, sql: str, fichier: str | None = None):
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

    # -- Contrôle d'entrée ---------------------------------------------------
    n, = con.execute("SELECT COUNT(*) FROM avis WHERE death_at IS NOT NULL").fetchone()
    print(f"Suppressions retenues par la définition corrigée : {n:,}")
    print(f"Attendu d'après suppressions_corrigees.py : 4 737 — "
          f"{'conforme' if n == 4737 else 'ÉCART À EXPLIQUER'}")

    con.execute(f"""
    CREATE OR REPLACE VIEW supprimes AS
    SELECT review_id, cid, star,
           CAST(created_at AS DATE) AS publie_le,
           CAST(death_at   AS DATE) AS supprime_le,
           date_diff('day', CAST(created_at AS DATE), CAST(death_at AS DATE)) AS age_j,
           CAST(created_at AS DATE) >= DATE '{PREMIERE_VAGUE}' AS ecrit_pendant_le_suivi
    FROM avis WHERE death_at IS NOT NULL
    """)

    # -- B. nouveaux contre anciens ------------------------------------------
    montre(con, "B. Part des suppressions selon que l'avis est né pendant le suivi", f"""
    WITH stock AS (
      SELECT CAST(created_at AS DATE) >= DATE '{PREMIERE_VAGUE}' AS ecrit_pendant_le_suivi,
             COUNT(*) AS avis_en_ligne
      FROM avis GROUP BY 1
    )
    SELECT CASE WHEN s.ecrit_pendant_le_suivi THEN 'écrit pendant les 14 jours'
                ELSE 'déjà en ligne avant le 11 août' END AS population,
           k.avis_en_ligne,
           COUNT(*) AS suppressions,
           ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS part_des_suppressions_pct,
           ROUND(100.0 * COUNT(*) / k.avis_en_ligne, 3) AS taux_de_suppression_pct
    FROM supprimes s JOIN stock k USING (ecrit_pendant_le_suivi)
    GROUP BY 1, 2 ORDER BY 3 DESC
    """, "B-nouveaux-contre-anciens.csv")

    montre(con, "B bis. Les mêmes suppressions par tranche d'âge de l'avis", """
    SELECT CASE WHEN age_j <= 14 THEN 'a. 0 à 14 jours'
                WHEN age_j <= 30 THEN 'b. 15 à 30 jours'
                WHEN age_j <= 90 THEN 'c. 1 à 3 mois'
                WHEN age_j <= 365 THEN 'd. 3 mois à 1 an'
                WHEN age_j <= 1095 THEN 'e. 1 à 3 ans'
                ELSE 'f. plus de 3 ans' END AS age_a_la_suppression,
           COUNT(*) AS suppressions,
           ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS part_pct,
           COUNT(DISTINCT cid) AS fiches
    FROM supprimes GROUP BY 1 ORDER BY 1
    """, "B-age-a-la-suppression.csv")

    montre(con, "B ter. Les suppressions définitives, par tranche d'âge", f"""
    WITH definitives AS (
      SELECT review_id,
             MIN(CAST(deleted_detected_at AS DATE)) AS disparu_le,
             BOOL_OR(deleted_detected_at IS NULL) AS a_ete_revu
      FROM base
      GROUP BY 1
    ), strictes AS (
      SELECT a.created_at, a.cid, d.disparu_le
      FROM definitives d
      JOIN avis a USING (review_id)
      WHERE d.disparu_le IS NOT NULL
        AND NOT d.a_ete_revu
        AND date_diff('day', d.disparu_le, DATE '{DERNIERE_VAGUE}') >= 2
    )
    SELECT CASE WHEN date_diff('day', CAST(created_at AS DATE), disparu_le) <= 14
                    THEN 'a. 0 à 14 jours'
                WHEN date_diff('day', CAST(created_at AS DATE), disparu_le) <= 30
                    THEN 'b. 15 à 30 jours'
                WHEN date_diff('day', CAST(created_at AS DATE), disparu_le) <= 90
                    THEN 'c. 1 à 3 mois'
                WHEN date_diff('day', CAST(created_at AS DATE), disparu_le) <= 365
                    THEN 'd. 3 mois à 1 an'
                WHEN date_diff('day', CAST(created_at AS DATE), disparu_le) <= 1095
                    THEN 'e. 1 à 3 ans'
                ELSE 'f. plus de 3 ans' END AS age_a_la_suppression,
           COUNT(*) AS suppressions,
           ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS part_pct,
           COUNT(DISTINCT cid) AS fiches
    FROM strictes
    GROUP BY 1 ORDER BY 1
    """, "B-age-a-la-suppression-strictes.csv")

    # -- A. les jours de suppression -----------------------------------------
    montre(con, "A1. Les suppressions jour par jour du suivi", """
    SELECT supprime_le,
           COUNT(*) AS suppressions,
           COUNT(DISTINCT cid) AS fiches,
           SUM((age_j > 365)::INT) AS dont_avis_de_plus_d_un_an,
           ROUND(MEDIAN(age_j), 0) AS age_median_j
    FROM supprimes GROUP BY 1 ORDER BY 1
    """, "A1-suppressions-par-jour.csv")

    montre(con, "A2. Les vieux avis supprimés, par année de publication", """
    SELECT YEAR(publie_le) AS annee_de_publication,
           COUNT(*) AS suppressions,
           COUNT(DISTINCT cid) AS fiches,
           COUNT(DISTINCT supprime_le) AS jours_de_suppression_distincts,
           ROUND(100.0 * MAX(n) / COUNT(*), 1) AS part_du_jour_le_plus_charge_pct
    FROM (SELECT *, COUNT(*) OVER (PARTITION BY YEAR(publie_le), supprime_le) AS n
          FROM supprimes)
    GROUP BY 1 ORDER BY 1
    """, "A2-par-annee-de-publication.csv")

    montre(con, "A3. Les couples (date de publication, date de suppression) les plus chargés", """
    SELECT publie_le, supprime_le, COUNT(*) AS suppressions,
           COUNT(DISTINCT cid) AS fiches,
           ROUND(100.0 * MAX(cnt_fiche) / COUNT(*), 0) AS part_de_la_fiche_dominante_pct,
           ANY_VALUE(star) AS une_note, ROUND(AVG(star), 1) AS note_moyenne
    FROM (SELECT *, COUNT(*) OVER (PARTITION BY publie_le, supprime_le, cid) AS cnt_fiche
          FROM supprimes)
    GROUP BY 1, 2 ORDER BY 3 DESC LIMIT 25
    """, "A3-couples-les-plus-charges.csv")

    print(f"\nSorties écrites dans {SORTIES}")


if __name__ == "__main__":
    main()
