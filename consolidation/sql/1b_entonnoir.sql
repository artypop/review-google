-- ============================================================================
-- 1b. De l'export brut au panel 03B, étape par étape
--
-- Les étapes 2 à 4 rejouent la construction de `reviews_doublons_cleaned`
-- (requête de Matthieu du 2026-09-17, retrouvée dans l'historique BigQuery) :
--
--   1. `reviews` tel quel.
--   2. Une ligne par avis : on garde la dernière version, la plus récemment
--      modifiée, puis la plus récemment vue.
--   3. Sans les avis qui ont clignoté : un avis à plusieurs lignes est gardé
--      seulement si sa dernière ligne est une modification de l'auteur. Les
--      autres ont disparu puis sont revenus : ils sortent.
--   4. Sans les avis modifiés plus de 365 jours après leur publication.
--   5. Seulement les avis publiés du 4 au 17 août 2026 (J-7 à J+6) : c'est 03B.
--
-- Les lignes de contrôle comparent l'étape 4 à la table
-- `reviews_doublons_cleaned`, et l'étape 5 à la table 03B. Attendu : 0 écart.
--
-- `avis_supprimes` : avis dont la ligne gardée est marquée disparue. À
-- l'étape 1, avis ayant au moins une ligne marquée disparue.
-- ============================================================================

WITH classement AS (
  SELECT
    review_id,
    is_update,
    created_at,
    updated_at,
    deleted_detected_at,
    COUNT(*) OVER (PARTITION BY review_id) AS nb_lignes,
    ROW_NUMBER() OVER (
      PARTITION BY review_id
      ORDER BY updated_at DESC, last_seen_at DESC, id DESC
    ) AS rang
  FROM `client-divers.reviewflowz.reviews`
),

etape2 AS (SELECT * FROM classement WHERE rang = 1),
etape3 AS (SELECT * FROM etape2 WHERE nb_lignes = 1 OR is_update = TRUE),
etape4 AS (SELECT * FROM etape3 WHERE TIMESTAMP_DIFF(updated_at, created_at, DAY) <= 365),
etape5 AS (SELECT * FROM etape4
           WHERE DATE(created_at) BETWEEN DATE "2026-08-04" AND DATE "2026-08-17"),

table_cleaned AS (SELECT review_id FROM `client-divers.reviewflowz.reviews_doublons_cleaned`),
table_03b     AS (SELECT review_id FROM `client-divers.reviewflowz.03B_reviews_panel_filtered_08_04_to_08_26`)

SELECT 1 AS ordre, "1. export brut (reviews)" AS etape,
       COUNT(*) AS lignes, COUNT(DISTINCT review_id) AS avis,
       COUNT(DISTINCT IF(deleted_detected_at IS NOT NULL, review_id, NULL)) AS avis_supprimes
FROM classement
UNION ALL
SELECT 2, "2. une ligne par avis, la dernière version",
       COUNT(*), COUNT(*), COUNTIF(deleted_detected_at IS NOT NULL) FROM etape2
UNION ALL
SELECT 3, "3. sans les avis qui ont clignoté",
       COUNT(*), COUNT(*), COUNTIF(deleted_detected_at IS NOT NULL) FROM etape3
UNION ALL
SELECT 4, "4. sans les avis modifiés plus d'un an après publication (= reviews_doublons_cleaned)",
       COUNT(*), COUNT(*), COUNTIF(deleted_detected_at IS NOT NULL) FROM etape4
UNION ALL
SELECT 5, "5. publiés du 4 au 17 août, J-7 à J+6 (= 03B)",
       COUNT(*), COUNT(*), COUNTIF(deleted_detected_at IS NOT NULL) FROM etape5
UNION ALL
SELECT 6, "contrôle : avis de l'étape 4 absents de la table reviews_doublons_cleaned",
       COUNT(*), COUNT(*), NULL FROM etape4
       WHERE review_id NOT IN (SELECT review_id FROM table_cleaned)
UNION ALL
SELECT 7, "contrôle : avis de la table reviews_doublons_cleaned absents de l'étape 4",
       COUNT(*), COUNT(*), NULL FROM table_cleaned
       WHERE review_id NOT IN (SELECT review_id FROM etape4)
UNION ALL
SELECT 8, "contrôle : avis de l'étape 5 absents de la table 03B",
       COUNT(*), COUNT(*), NULL FROM etape5
       WHERE review_id NOT IN (SELECT review_id FROM table_03b)
UNION ALL
SELECT 9, "contrôle : avis de la table 03B absents de l'étape 5",
       COUNT(*), COUNT(*), NULL FROM table_03b
       WHERE review_id NOT IN (SELECT review_id FROM etape5)
ORDER BY ordre
