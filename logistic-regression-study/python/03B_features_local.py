#!/usr/bin/env python3
"""
==============================================================================
Script : 03B_features_local.py
Sortie : data/local/reviews_panel_features_03B.parquet (non versionné)

Transposition en DuckDB de `sql/03B_adding_features.bqsql`, écrite le
2026-09-28 à la demande de Matthieu, pour faire tourner le 07C sur un poste
sans accès BigQuery. Le fichier SQL n'est pas modifié ; ce script en reprend
les blocs utiles au 07B et au 07C, avec les mêmes bornes et les mêmes règles.

    .venv/Scripts/python.exe logistic-regression-study/python/03B_features_local.py

------------------------------------------------------------------------------
LES SOURCES
------------------------------------------------------------------------------
  panel   data/bigquery/03B_reviews_panel_filtered_08_04_to_08_26.parquet
          35 751 avis, 5 566 fiches, 1 355 disparitions : identique à la table
          BigQuery, vérifié le 2026-09-28.
  socle   data/bigquery/reviews.parquet, dédoublonné sur `review_id` en gardant
          la dernière ligne. C'est la règle de `01_reviews_avis_update_et_unique`,
          dont le SQL n'est pas dans le dépôt.

ÉCART CONNU SUR LE SOCLE. BigQuery annonce 4 875 974 avis dans
`01_reviews_avis_update_et_unique` ; la copie locale en compte 4 877 534
distincts, soit 1 560 de plus (0,03 %). Aucune clé de dédoublonnage testée ne
retombe sur le chiffre BigQuery. Le socle ne sert qu'aux comptes par fiche et
par jour (pic d'avis, rythme de la fiche) et par auteur et par jour. L'effet
est mesuré par `07C_regression_reduite.py --valider-07B`, qui rejoue le modèle
complet du 07B sur cette table et le compare aux sorties du 2026-09-21.

------------------------------------------------------------------------------
CE QUI N'EST PAS REPRIS
------------------------------------------------------------------------------
`profil_auteur`, `record_auteur` et `habitude_reponse_fiche` : aucune de leurs
colonnes n'entre dans le 07B ni dans le 07C. `author_key` est un hachage
DuckDB du lien d'auteur, pas le FARM_FINGERPRINT de BigQuery : il sert à
grouper, jamais à rapprocher des deux tables.

La table produite ne contient ni texte, ni nom, ni lien d'avis.
==============================================================================
"""
from __future__ import annotations

import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "outils"))
from local import connexion  # noqa: E402

SORTIE = RACINE / "data" / "local" / "reviews_panel_features_03B.parquet"

ATTENDU = {"avis": 35_751, "fiches": 5_566, "suppressions": 1_355}

SQL = """
WITH
bornes AS (SELECT DATE '2026-08-11' AS vague1, DATE '2026-08-24' AS derniere_vague),

panel AS (
  SELECT review_id, cid, review_link, star, text, "language", n_photos,
         reviewer_review_count, reviewer_photo_count, local_guide_level,
         reply_date, is_update, changed_fields,
         CAST(created_at AS DATE)          AS created_at_day,
         CAST(first_seen_at AS DATE)       AS first_seen_at_day,
         CAST(deleted_detected_at AS DATE) AS deleted_detected_at_day
  FROM "03B_reviews_panel_filtered_08_04_to_08_26"
),

auteur_jour AS (
  SELECT review_link, jour, COUNT(*) AS n_avis_ce_jour
  FROM corpus_unique WHERE review_link IS NOT NULL
  GROUP BY review_link, jour
),

fiche_jour AS (
  SELECT cid, jour, COUNT(*) AS n_avis_ce_jour FROM corpus_unique GROUP BY cid, jour
),

rythme_fiche AS (
  SELECT cid, COUNT(*) / 365.0 AS avis_par_jour_avant_vague1
  FROM corpus_unique, bornes
  WHERE jour BETWEEN bornes.vague1 - INTERVAL 365 DAY AND bornes.vague1 - INTERVAL 1 DAY
  GROUP BY cid
),

langue_modale_fiche AS (
  SELECT cid, "language" AS langue_modale
  FROM (
    SELECT cid, "language",
           ROW_NUMBER() OVER (PARTITION BY cid ORDER BY COUNT(*) DESC, "language") AS rn
    FROM corpus_unique
    WHERE "language" IS NOT NULL AND jour < DATE '2026-08-11'
    GROUP BY cid, "language"
  ) WHERE rn = 1
)

SELECT
  p.review_id,
  p.cid,
  CAST(hash(p.review_link) AS VARCHAR)                        AS author_key,

  p.deleted_detected_at_day IS NOT NULL                       AS supprime,
  date_diff('day', p.created_at_day, p.first_seen_at_day)     AS age_a_la_premiere_observation_j,
  date_diff('day', p.first_seen_at_day, bornes.derniere_vague) AS fenetre_observation_j,
  (p.created_at_day >= bornes.vague1)                         AS ne_pendant_la_surveillance,

  p.star,
  (p.text IS NOT NULL AND length(trim(p.text)) > 0)           AS has_text,
  COALESCE(length(p.text), 0)                                 AS text_chars,
  p.n_photos,
  (p.n_photos > 0)                                            AS has_photo,

  COALESCE(p.is_update, FALSE)                                AS avis_modifie,
  COALESCE(p.changed_fields LIKE '%star%', FALSE)             AS note_modifiee,
  COALESCE(p.changed_fields LIKE '%text%', FALSE)             AS texte_modifiee,

  (p.reply_date IS NOT NULL)                                  AS a_une_reponse,
  (p.reply_date IS NOT NULL
   AND CAST(p.reply_date AS DATE) <  p.first_seen_at_day)     AS reponse_avant_surveillance,
  (p.reply_date IS NOT NULL
   AND date_diff('day', p.created_at_day, CAST(p.reply_date AS DATE)) <= 2)
                                                              AS reponse_dans_les_2_jours,

  p.reviewer_review_count,
  ln(p.reviewer_review_count + 1)                             AS log_rc,
  CASE WHEN p.local_guide_level IS NULL THEN 'sans_niveau'
       WHEN p.local_guide_level <= 3    THEN '1_3'
       ELSE '4_et_plus' END                                   AS palier_local_guide,
  COALESCE(p.reviewer_photo_count, 0)                         AS reviewer_photo_count,
  COALESCE(aja.n_avis_ce_jour, 1)                             AS n_avis_meme_jour_auteur,

  (p."language" IS NULL)                                      AS langue_inconnue,
  (p."language" IS NOT NULL AND NOT EXISTS (
     SELECT 1 FROM concordance_pays_langue k
     WHERE k.code_pays = b.country AND k.code_langue = p."language"))
                                                              AS langue_etrangere_au_pays,
  (p."language" IS NOT NULL AND lm.langue_modale IS NOT NULL
   AND p."language" != lm.langue_modale)                      AS langue_minoritaire_sur_la_fiche,

  b.industry,
  b.country,
  b.bucket,
  IF(b.country = 'US', 'US', 'Europe')                        AS region,
  (b.name IN ('EcoShield Pest Solutions', 'Insight Pest Solutions',
              'Pointe Pest Control', 'Bulwark Exterminating')) AS chaine_antiparasitaire_us,
  (b.name IN ('Boutique The Boxer Club Dr Castelo', 'The Boxer Club'))
                                                              AS salle_de_sport_attaquee,
  -- Repérage de la section 3 du rapport (antiparasitaire.py) : toutes les
  -- fiches américaines de traitement antiparasitaire. Absente de 03B.
  COALESCE(b.country = 'US' AND b.industry = 'home_services'
           AND (regexp_matches(b.name, '{motif}')
                OR regexp_matches(b.name, '{inclusion}')), FALSE)
                                                              AS antiparasitaire_us,

  fj.n_avis_ce_jour                                           AS n_avis_meme_jour_fiche,
  (rf.avis_par_jour_avant_vague1 IS NULL)                     AS rythme_fiche_inconnu,
  ln(fj.n_avis_ce_jour / rf.avis_par_jour_avant_vague1 + 1)   AS log_ratio_pic_journalier_fiche

FROM panel p
CROSS JOIN bornes
LEFT JOIN businesses          b  ON p.cid = b.cid
LEFT JOIN langue_modale_fiche lm ON p.cid = lm.cid
LEFT JOIN rythme_fiche        rf ON p.cid = rf.cid
LEFT JOIN fiche_jour          fj ON p.cid = fj.cid AND p.created_at_day = fj.jour
LEFT JOIN auteur_jour         aja ON p.review_link = aja.review_link
                                 AND p.created_at_day = aja.jour
"""

# Le socle, dernière ligne de chaque avis comme `01_reviews_avis_update_et_unique`.
# Restreint aux avis des fiches du panel et des auteurs du panel : ce sont les
# seuls que les comptes par fiche, par auteur et la langue modale lisent. Le
# résultat est le même qu'avec le socle entier, et tient dans la mémoire d'un
# poste à 1,5 Go libre.
SQL_SOCLE = """
CREATE TEMP TABLE corpus_unique AS
SELECT review_id,
       arg_max(cid, id)                      AS cid,
       arg_max(review_link, id)              AS review_link,
       arg_max("language", id)               AS "language",
       CAST(arg_max(created_at, id) AS DATE) AS jour
FROM reviews
WHERE cid IN (SELECT cid FROM "03B_reviews_panel_filtered_08_04_to_08_26")
   OR review_link IN (SELECT review_link FROM "03B_reviews_panel_filtered_08_04_to_08_26")
GROUP BY review_id
"""

MOTIF_ACTIVITE = r"(?i)(pest|exterminat|termite|spidexx|mosquito|rodent|wildlife)"
MOTIF_INCLUSION_MANUELLE = r"(?i)abc home ?(&|and) ?commercial"


def main() -> int:
    con = connexion("1500MB")
    con.execute("SET threads=2")
    con.execute("SET preserve_insertion_order=false")
    con.execute("SET enable_progress_bar=false")
    SORTIE.parent.mkdir(parents=True, exist_ok=True)
    con.execute(f"SET temp_directory='{(SORTIE.parent / 'tmp_duckdb').as_posix()}'")
    con.execute(SQL_SOCLE)
    print(f"socle : {con.execute('SELECT COUNT(*) FROM corpus_unique').fetchone()[0]:,} avis"
          .replace(",", " "))
    sql = SQL.format(motif=MOTIF_ACTIVITE, inclusion=MOTIF_INCLUSION_MANUELLE)
    con.execute(f"COPY ({sql}) TO '{SORTIE.as_posix()}' (FORMAT parquet)")

    avis, fiches, suppressions, doublons = con.execute(f"""
        SELECT COUNT(*), COUNT(DISTINCT cid), COUNT(*) FILTER (supprime),
               COUNT(*) - COUNT(DISTINCT review_id)
        FROM '{SORTIE.as_posix()}'
    """).fetchone()
    obtenu = {"avis": avis, "fiches": fiches, "suppressions": suppressions}
    print(f"écrit : {SORTIE}\n  {obtenu}, doublons {doublons}")
    if obtenu != ATTENDU or doublons:
        print(f"ARRÊT : attendu {ATTENDU}, sans doublon.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
