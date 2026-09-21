#!/usr/bin/env python3
"""Le motif des suppressions de vieux avis.

    python etudes-ponctuelles/2026-09-16-suppressions-vieux-avis/vieux_avis.py

`lancer.py` répond aux deux questions de volume. Celui-ci cherche s'il y a un
motif dans les suppressions des avis anciens, que les tableaux d'ensemble ne
montrent pas : ils sont écrasés par les avis récents, qui portent la moitié des
suppressions.

Un vieil avis est ici un avis supprimé à plus d'un an d'âge. Le seuil est
arbitraire et se change en tête de fichier.

Définition d'une suppression : `suppressions_corrigees.py`, importée telle
quelle.
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
AGE_VIEUX_J = 365
PREMIERE_VAGUE = "2026-08-11"


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

    con.execute(f"""
    CREATE OR REPLACE VIEW vieux AS
    SELECT review_id, cid, star,
           CAST(created_at AS DATE) AS publie_le,
           CAST(death_at   AS DATE) AS supprime_le,
           date_diff('day', CAST(created_at AS DATE), CAST(death_at AS DATE)) AS age_j
    FROM avis
    WHERE death_at IS NOT NULL
      AND date_diff('day', CAST(created_at AS DATE), CAST(death_at AS DATE)) > {AGE_VIEUX_J}
    """)

    n, = con.execute("SELECT COUNT(*) FROM vieux").fetchone()
    print(f"Avis supprimés à plus d'un an d'âge : {n:,}")

    montre(con, "C1. Ces suppressions, jour par jour", """
    SELECT supprime_le, COUNT(*) AS suppressions, COUNT(DISTINCT cid) AS fiches,
           ROUND(1.0 * COUNT(*) / COUNT(DISTINCT cid), 1) AS par_fiche,
           ROUND(AVG(star), 2) AS note_moyenne,
           ROUND(MEDIAN(age_j) / 365.0, 1) AS age_median_annees
    FROM vieux GROUP BY 1 ORDER BY 1
    """, "C1-vieux-par-jour.csv")

    montre(con, "C2. Groupées sur une fiche, ou dispersées ?", """
    WITH paquets AS (
      SELECT cid, supprime_le, COUNT(*) AS n FROM vieux GROUP BY 1, 2
    )
    SELECT CASE WHEN n = 1 THEN 'a. 1 seul vieil avis ce jour-là'
                WHEN n <= 3 THEN 'b. 2 à 3'
                WHEN n <= 10 THEN 'c. 4 à 10'
                ELSE 'd. plus de 10' END AS taille_du_paquet,
           COUNT(*) AS paquets, SUM(n) AS suppressions,
           ROUND(100.0 * SUM(n) / SUM(SUM(n)) OVER (), 1) AS part_pct
    FROM paquets GROUP BY 1 ORDER BY 1
    """, "C2-taille-des-paquets.csv")

    montre(con, "C3. Les fiches qui en perdent le plus", """
    SELECT cid, COUNT(*) AS vieux_supprimes, COUNT(DISTINCT supprime_le) AS jours,
           COUNT(DISTINCT publie_le) AS dates_de_publication,
           ROUND(AVG(star), 2) AS note_moyenne,
           MIN(publie_le) AS plus_ancien, MAX(publie_le) AS plus_recent
    FROM vieux GROUP BY 1 ORDER BY 2 DESC LIMIT 15
    """, "C3-fiches-les-plus-touchees.csv")

    montre(con, "C4. La concentration : combien de fiches portent la moitié de ces suppressions", """
    WITH par_fiche AS (
      SELECT cid, COUNT(*) AS n FROM vieux GROUP BY 1
    ), classe AS (
      SELECT *, SUM(n) OVER (ORDER BY n DESC, cid) AS cumul,
                SUM(n) OVER () AS total,
                ROW_NUMBER() OVER (ORDER BY n DESC, cid) AS rang
      FROM par_fiche
    )
    SELECT MIN(rang) FILTER (cumul >= 0.25 * total) AS fiches_pour_un_quart,
           MIN(rang) FILTER (cumul >= 0.50 * total) AS fiches_pour_la_moitie,
           MIN(rang) FILTER (cumul >= 0.90 * total) AS fiches_pour_neuf_dixiemes,
           COUNT(*) AS fiches_touchees
    FROM classe
    """, "C4-concentration.csv")

    montre(con, "C5. La note des vieux avis supprimés, comparée au stock en ligne", f"""
    WITH stock AS (
      SELECT star, COUNT(*) AS en_ligne FROM avis
      WHERE death_at IS NULL
        AND date_diff('day', CAST(created_at AS DATE), DATE '{PREMIERE_VAGUE}') > {AGE_VIEUX_J}
      GROUP BY 1
    ), supp AS (
      SELECT star, COUNT(*) AS supprimes FROM vieux GROUP BY 1
    )
    SELECT s.star AS note, k.en_ligne, s.supprimes,
           ROUND(10000.0 * s.supprimes / k.en_ligne, 1) AS supprimes_pour_10000_en_ligne
    FROM supp s JOIN stock k USING (star) ORDER BY 1
    """, "C5-note-des-vieux.csv")

    montre(con, "C6. Les dates de publication qui perdent le plus de vieux avis", """
    SELECT publie_le, COUNT(*) AS suppressions, COUNT(DISTINCT cid) AS fiches,
           COUNT(DISTINCT supprime_le) AS jours_de_suppression,
           ROUND(AVG(star), 2) AS note_moyenne
    FROM vieux GROUP BY 1 ORDER BY 2 DESC LIMIT 15
    """, "C6-dates-de-publication.csv")

    print(f"\nSorties écrites dans {SORTIES}")


if __name__ == "__main__":
    main()
