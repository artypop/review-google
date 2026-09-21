#!/usr/bin/env python3
"""Les avis disparus puis réapparus : qui, où, combien de temps.

    python etudes-ponctuelles/2026-09-18-reapparitions/reapparitions.py

Produit les CSV de `sorties/`. Le document Word et les figures sont assemblés
ensuite par `note.py`, qui ne calcule rien.

------------------------------------------------------------------------------
CE QU'ON APPELLE UNE RÉAPPARITION
------------------------------------------------------------------------------
Le robot crée une ligne par période de présence continue d'un avis. Un avis vu
sans interruption a donc une seule ligne. Un avis que le robot ne retrouve plus,
puis qu'il revoit, a deux lignes : la première porte une date de disparition,
la seconde une nouvelle date de première observation.

Les lignes d'historique (`is_update = TRUE`) sont des versions successives du
même avis après modification par son auteur. Elles ne signalent aucune absence
et sont écartées ici. C'est aussi le périmètre sur lequel `docs/02-donnees.md`
§ 1 compte 617 lignes en trop et 602 avis.

Un épisode = un couple (ligne qui disparaît, ligne suivante qui revient). Un
avis peut en porter plusieurs. Les deux comptes sont donnés séparément.

------------------------------------------------------------------------------
LA DISTINCTION QUI GOUVERNE LA LECTURE
------------------------------------------------------------------------------
`docs/02-donnees.md` § 3 pose la règle du projet : une absence d'un seul jour
est un raté de collecte, une absence de deux jours ou plus est une vraie
suppression suivie d'un rétablissement. Les deux populations sont comptées à
part partout dans ce script.

Le texte identique de part et d'autre de l'absence sépare en plus le retour du
même avis du bug d'enregistrement décrit au même endroit — même auteur, même
note, même date de publication, texte entièrement différent.
"""
from __future__ import annotations

import sys
from pathlib import Path

DOSSIER = Path(__file__).resolve().parent
RACINE = DOSSIER.parent.parent
SORTIES = DOSSIER / "sorties"
sys.path.insert(0, str(RACINE / "outils"))

from local import connexion  # noqa: E402

EPISODES = """
CREATE TEMP TABLE episodes AS
WITH multi AS (
  SELECT review_id
  FROM reviews
  WHERE NOT is_update
  GROUP BY review_id
  HAVING COUNT(*) > 1
),
lignes AS (
  SELECT r.review_id,
         r.cid,
         r.star,
         r.text,
         CAST(r.first_seen_at AS DATE)        AS vu_le,
         CAST(r.last_seen_at AS DATE)         AS vu_jusquau,
         CAST(r.deleted_detected_at AS DATE)  AS absent_le,
         CAST(r.created_at AS DATE)           AS publie_le,
         ROW_NUMBER() OVER (PARTITION BY r.review_id ORDER BY r.first_seen_at) AS rang
  FROM reviews r
  JOIN multi USING (review_id)
  WHERE NOT r.is_update
)
SELECT a.review_id,
       a.cid,
       a.star,
       a.publie_le,
       a.vu_jusquau,
       COALESCE(a.absent_le, a.vu_jusquau + INTERVAL 1 DAY) AS absent_le,
       b.vu_le                                    AS revu_le,
       -- L'absence se mesure depuis le dernier jour où le robot a vu l'avis.
       -- Deux lignes sur 617 n'ont pas de date de disparition alors qu'un
       -- retour suit ; `last_seen_at` est renseigné partout et donne la même
       -- durée que `deleted_detected_at` sur les 615 autres.
       DATE_DIFF('day', a.vu_jusquau, b.vu_le) - 1 AS jours_absent,
       (a.text IS NOT DISTINCT FROM b.text)       AS meme_texte,
       (a.text IS NULL OR LENGTH(TRIM(a.text)) = 0) AS sans_texte
FROM lignes a
JOIN lignes b ON a.review_id = b.review_id AND b.rang = a.rang + 1
"""


def ecrire(df, nom):
    SORTIES.mkdir(parents=True, exist_ok=True)
    df.to_csv(SORTIES / nom, index=False)
    print(f"  {nom:44s} {len(df):>5} lignes")
    return df


def main() -> int:
    con = connexion("4GB")
    con.execute(EPISODES)

    print("\nA. Le périmètre")
    ecrire(con.execute("""
        SELECT 'lignes de la table reviews'            AS mesure,
               (SELECT COUNT(*) FROM reviews)          AS valeur
        UNION ALL SELECT 'dont lignes d''historique (is_update)',
               (SELECT COUNT(*) FROM reviews WHERE is_update)
        UNION ALL SELECT 'lignes de présence (is_update faux)',
               (SELECT COUNT(*) FROM reviews WHERE NOT is_update)
        UNION ALL SELECT 'avis distincts',
               (SELECT COUNT(DISTINCT review_id) FROM reviews)
        UNION ALL SELECT 'avis à plusieurs lignes de présence',
               (SELECT COUNT(DISTINCT review_id) FROM episodes)
        UNION ALL SELECT 'épisodes de réapparition',
               (SELECT COUNT(*) FROM episodes)
    """).df(), "A1-perimetre.csv")

    print("\nB. La durée d'absence")
    ecrire(con.execute("""
        SELECT CASE WHEN jours_absent = 1 THEN 'a. 1 jour — raté de collecte'
                    WHEN jours_absent BETWEEN 2 AND 3 THEN 'b. 2 à 3 jours'
                    WHEN jours_absent BETWEEN 4 AND 7 THEN 'c. 4 à 7 jours'
                    ELSE 'd. 8 jours et plus' END      AS duree_absence,
               COUNT(*)                                AS episodes,
               COUNT(DISTINCT review_id)               AS avis,
               COUNT(DISTINCT cid)                     AS fiches,
               ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS part_pct
        FROM episodes GROUP BY 1 ORDER BY 1
    """).df(), "B1-duree-absence.csv")

    ecrire(con.execute("""
        SELECT jours_absent, COUNT(*) AS episodes, COUNT(DISTINCT review_id) AS avis
        FROM episodes GROUP BY 1 ORDER BY 1
    """).df(), "B2-duree-absence-detail.csv")

    print("\nC. Le texte de part et d'autre de l'absence")
    ecrire(con.execute("""
        SELECT CASE WHEN meme_texte THEN 'le même avis revient'
                    ELSE 'texte différent — bug d''enregistrement' END AS nature,
               CASE WHEN jours_absent = 1 THEN '1 jour' ELSE '2 jours et plus' END AS duree,
               COUNT(*) AS episodes, COUNT(DISTINCT review_id) AS avis
        FROM episodes GROUP BY 1, 2 ORDER BY 1, 2
    """).df(), "C1-texte.csv")

    print("\nD. Les secteurs")
    ecrire(con.execute("""
        WITH parc AS (
          SELECT b.industry, COUNT(*) AS avis_du_secteur, COUNT(DISTINCT r.cid) AS fiches_du_secteur
          FROM reviews r JOIN businesses b USING (cid)
          WHERE NOT r.is_update
          GROUP BY 1
        ),
        touches AS (
          SELECT b.industry,
                 COUNT(*) AS episodes,
                 COUNT(DISTINCT e.review_id) AS avis_revenus,
                 COUNT(DISTINCT e.cid) AS fiches_touchees,
                 SUM(CASE WHEN e.jours_absent = 1 THEN 1 ELSE 0 END) AS ep_1_jour,
                 SUM(CASE WHEN e.jours_absent >= 2 THEN 1 ELSE 0 END) AS ep_2_jours_et_plus
          FROM episodes e JOIN businesses b USING (cid)
          GROUP BY 1
        )
        SELECT p.industry AS secteur, p.avis_du_secteur, p.fiches_du_secteur,
               COALESCE(t.avis_revenus, 0)        AS avis_revenus,
               COALESCE(t.episodes, 0)            AS episodes,
               COALESCE(t.ep_1_jour, 0)           AS ep_1_jour,
               COALESCE(t.ep_2_jours_et_plus, 0)  AS ep_2_jours_et_plus,
               COALESCE(t.fiches_touchees, 0)     AS fiches_touchees,
               ROUND(1000000.0 * COALESCE(t.avis_revenus, 0) / p.avis_du_secteur, 1)
                   AS avis_revenus_par_million
        FROM parc p LEFT JOIN touches t USING (industry)
        ORDER BY avis_revenus_par_million DESC
    """).df(), "D1-secteurs.csv")

    print("\nE. Les pays et la région")
    ecrire(con.execute("""
        WITH parc AS (
          SELECT IF(b.country = 'US', 'États-Unis', 'Europe') AS region,
                 COUNT(*) AS avis_du_parc
          FROM reviews r JOIN businesses b USING (cid) WHERE NOT r.is_update GROUP BY 1
        ),
        touches AS (
          SELECT IF(b.country = 'US', 'États-Unis', 'Europe') AS region,
                 COUNT(*) AS episodes, COUNT(DISTINCT e.review_id) AS avis_revenus,
                 SUM(CASE WHEN e.jours_absent >= 2 THEN 1 ELSE 0 END) AS ep_2_jours_et_plus
          FROM episodes e JOIN businesses b USING (cid) GROUP BY 1
        )
        SELECT p.region, p.avis_du_parc, t.avis_revenus, t.episodes, t.ep_2_jours_et_plus,
               ROUND(1000000.0 * t.avis_revenus / p.avis_du_parc, 1) AS avis_revenus_par_million
        FROM parc p JOIN touches t USING (region) ORDER BY avis_revenus_par_million DESC
    """).df(), "E1-regions.csv")

    print("\nF. La concentration par fiche")
    ecrire(con.execute("""
        SELECT CASE WHEN n = 1 THEN 'a. 1 avis revenu'
                    WHEN n BETWEEN 2 AND 3 THEN 'b. 2 à 3'
                    WHEN n BETWEEN 4 AND 9 THEN 'c. 4 à 9'
                    ELSE 'd. 10 et plus' END AS paquet_par_fiche,
               COUNT(*) AS fiches, SUM(n) AS avis_revenus,
               ROUND(100.0 * SUM(n) / SUM(SUM(n)) OVER (), 1) AS part_des_avis_pct
        FROM (SELECT cid, COUNT(DISTINCT review_id) AS n FROM episodes GROUP BY cid)
        GROUP BY 1 ORDER BY 1
    """).df(), "F1-concentration.csv")

    ecrire(con.execute("""
        SELECT b.name AS enseigne, b.industry AS secteur, b.country AS pays,
               COUNT(DISTINCT e.review_id) AS avis_revenus,
               COUNT(*) AS episodes,
               SUM(CASE WHEN e.jours_absent >= 2 THEN 1 ELSE 0 END) AS ep_2_jours_et_plus,
               MAX(e.jours_absent) AS absence_max_j,
               (SELECT COUNT(*) FROM reviews r
                WHERE r.cid = e.cid AND NOT r.is_update) AS avis_de_la_fiche
        FROM episodes e JOIN businesses b USING (cid)
        GROUP BY b.name, b.industry, b.country, e.cid
        ORDER BY avis_revenus DESC, episodes DESC, enseigne LIMIT 15
    """).df(), "F2-fiches-les-plus-touchees.csv")

    print("\nG. La note et l'âge")
    ecrire(con.execute("""
        WITH parc AS (
          SELECT star, COUNT(*) AS avis_du_parc FROM reviews WHERE NOT is_update GROUP BY 1
        ),
        touches AS (
          SELECT star, COUNT(DISTINCT review_id) AS avis_revenus,
                 SUM(CASE WHEN jours_absent >= 2 THEN 1 ELSE 0 END) AS ep_2_jours_et_plus
          FROM episodes GROUP BY 1
        )
        SELECT p.star AS note, p.avis_du_parc, COALESCE(t.avis_revenus, 0) AS avis_revenus,
               COALESCE(t.ep_2_jours_et_plus, 0) AS ep_2_jours_et_plus,
               ROUND(1000000.0 * COALESCE(t.avis_revenus, 0) / p.avis_du_parc, 1)
                   AS avis_revenus_par_million
        FROM parc p LEFT JOIN touches t USING (star) ORDER BY p.star
    """).df(), "G1-note.csv")

    print("\nH. Le calendrier des disparitions qui ont été suivies d'un retour")
    ecrire(con.execute("""
        SELECT absent_le AS disparu_le, COUNT(*) AS episodes,
               COUNT(DISTINCT cid) AS fiches,
               SUM(CASE WHEN jours_absent >= 2 THEN 1 ELSE 0 END) AS ep_2_jours_et_plus
        FROM episodes GROUP BY 1 ORDER BY 1
    """).df(), "H1-calendrier.csv")

    print("\nI. Contrôle : les deux façons de mesurer l'absence concordent")
    ecrire(con.execute("""
        SELECT CASE WHEN jours_absent
                         = DATE_DIFF('day', absent_le, revu_le) THEN 'concordent'
                    ELSE 'divergent' END AS verdict,
               COUNT(*) AS episodes
        FROM episodes GROUP BY 1 ORDER BY 1
    """).df(), "I1-controle-duree.csv")

    print("\nJ. La population qui compte : le même avis, revenu après 2 jours ou plus")
    ecrire(con.execute("""
        SELECT 'épisodes' AS mesure, COUNT(*) AS valeur FROM episodes
            WHERE meme_texte AND jours_absent >= 2
        UNION ALL SELECT 'avis', COUNT(DISTINCT review_id) FROM episodes
            WHERE meme_texte AND jours_absent >= 2
        UNION ALL SELECT 'fiches', COUNT(DISTINCT cid) FROM episodes
            WHERE meme_texte AND jours_absent >= 2
        UNION ALL SELECT 'disparitions constatées sur toute la table',
            (SELECT COUNT(*) FROM reviews WHERE NOT is_update AND deleted_detected_at IS NOT NULL)
        UNION ALL SELECT 'avis ayant disparu au moins une fois',
            (SELECT COUNT(DISTINCT review_id) FROM reviews
             WHERE NOT is_update AND deleted_detected_at IS NOT NULL)
    """).df(), "J1-population-retenue.csv")

    ecrire(con.execute("""
        WITH parc AS (
          SELECT b.industry, COUNT(*) AS avis_du_secteur
          FROM reviews r JOIN businesses b USING (cid) WHERE NOT r.is_update GROUP BY 1
        ),
        vrais AS (
          SELECT b.industry, COUNT(DISTINCT e.review_id) AS avis_revenus,
                 COUNT(DISTINCT e.cid) AS fiches_touchees,
                 ROUND(AVG(e.jours_absent), 1) AS absence_moyenne_j,
                 MAX(e.jours_absent) AS absence_max_j
          FROM episodes e JOIN businesses b USING (cid)
          WHERE e.meme_texte AND e.jours_absent >= 2
          GROUP BY 1
        )
        SELECT p.industry AS secteur, p.avis_du_secteur,
               COALESCE(v.avis_revenus, 0) AS avis_revenus,
               COALESCE(v.fiches_touchees, 0) AS fiches_touchees,
               v.absence_moyenne_j, v.absence_max_j,
               ROUND(1000000.0 * COALESCE(v.avis_revenus, 0) / p.avis_du_secteur, 1)
                   AS avis_revenus_par_million
        FROM parc p LEFT JOIN vrais v USING (industry)
        ORDER BY avis_revenus_par_million DESC
    """).df(), "J2-secteurs-vrais-retours.csv")

    ecrire(con.execute("""
        WITH parc AS (
          SELECT IF(b.country = 'US', 'États-Unis', 'Europe') AS region,
                 COUNT(*) AS avis_du_parc
          FROM reviews r JOIN businesses b USING (cid) WHERE NOT r.is_update GROUP BY 1
        ),
        vrais AS (
          SELECT IF(b.country = 'US', 'États-Unis', 'Europe') AS region,
                 COUNT(DISTINCT e.review_id) AS avis_revenus,
                 COUNT(DISTINCT e.cid) AS fiches_touchees
          FROM episodes e JOIN businesses b USING (cid)
          WHERE e.meme_texte AND e.jours_absent >= 2 GROUP BY 1
        )
        SELECT p.region, p.avis_du_parc, v.avis_revenus, v.fiches_touchees,
               ROUND(1000000.0 * v.avis_revenus / p.avis_du_parc, 1) AS avis_revenus_par_million
        FROM parc p JOIN vrais v USING (region) ORDER BY avis_revenus_par_million DESC
    """).df(), "J3-regions-vrais-retours.csv")

    ecrire(con.execute("""
        WITH parc AS (
          SELECT star, COUNT(*) AS avis_du_parc FROM reviews WHERE NOT is_update GROUP BY 1
        ),
        vrais AS (
          SELECT star, COUNT(DISTINCT review_id) AS avis_revenus FROM episodes
          WHERE meme_texte AND jours_absent >= 2 GROUP BY 1
        )
        SELECT p.star AS note, p.avis_du_parc, COALESCE(v.avis_revenus, 0) AS avis_revenus,
               ROUND(1000000.0 * COALESCE(v.avis_revenus, 0) / p.avis_du_parc, 1)
                   AS avis_revenus_par_million
        FROM parc p LEFT JOIN vrais v USING (star) ORDER BY p.star
    """).df(), "J4-note-vrais-retours.csv")

    ecrire(con.execute("""
        SELECT b.name AS enseigne, b.industry AS secteur, b.country AS pays,
               COUNT(DISTINCT e.review_id) AS avis_revenus,
               MAX(e.jours_absent) AS absence_max_j,
               (SELECT COUNT(*) FROM reviews r WHERE r.cid = e.cid AND NOT r.is_update)
                   AS avis_de_la_fiche
        FROM episodes e JOIN businesses b USING (cid)
        WHERE e.meme_texte AND e.jours_absent >= 2
        GROUP BY b.name, b.industry, b.country, e.cid
        ORDER BY avis_revenus DESC, absence_max_j DESC, enseigne LIMIT 10
    """).df(), "J5-fiches-vrais-retours.csv")

    ecrire(con.execute("""
        SELECT jours_absent, COUNT(*) AS episodes
        FROM episodes WHERE meme_texte AND jours_absent >= 2
        GROUP BY 1 ORDER BY 1
    """).df(), "J6-duree-vrais-retours.csv")

    print("\nK. Les secteurs, tous retours confondus quelle que soit la durée d'absence")
    ecrire(con.execute("""
        WITH parc AS (
          SELECT b.industry, COUNT(*) AS avis_du_secteur
          FROM reviews r JOIN businesses b USING (cid) WHERE NOT r.is_update GROUP BY 1
        ),
        retours AS (
          SELECT b.industry,
                 COUNT(DISTINCT e.review_id) AS avis_revenus,
                 COUNT(DISTINCT e.cid)       AS fiches_touchees,
                 COUNT(DISTINCT CASE WHEN e.jours_absent = 1 THEN e.review_id END)
                     AS avis_revenus_des_le_lendemain,
                 COUNT(DISTINCT CASE WHEN e.jours_absent >= 2 THEN e.review_id END)
                     AS avis_revenus_apres_2j
          FROM episodes e JOIN businesses b USING (cid)
          WHERE e.meme_texte
          GROUP BY 1
        )
        SELECT p.industry AS secteur, p.avis_du_secteur,
               COALESCE(r.avis_revenus, 0)                  AS avis_revenus,
               COALESCE(r.avis_revenus_des_le_lendemain, 0) AS avis_revenus_des_le_lendemain,
               COALESCE(r.avis_revenus_apres_2j, 0)         AS avis_revenus_apres_2j,
               COALESCE(r.fiches_touchees, 0)               AS fiches_touchees,
               ROUND(1000000.0 * COALESCE(r.avis_revenus, 0) / p.avis_du_secteur, 1)
                   AS avis_revenus_par_million
        FROM parc p LEFT JOIN retours r USING (industry)
        ORDER BY avis_revenus_par_million DESC
    """).df(), "K1-secteurs-tous-retours.csv")

    con.close()
    print(f"\nCSV dans {SORTIES}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
