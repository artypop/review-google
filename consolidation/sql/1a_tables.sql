-- ============================================================================
-- 1a. Ce que contiennent les tables de départ
--
-- Une ligne par table. Pour `reviews`, un avis peut avoir plusieurs lignes :
-- `lignes` et `avis` diffèrent. Dans `reviews_doublons_cleaned_all`, une
-- ligne par avis.
--
-- `suppressions` :
--   reviews                        lignes marquées disparues (`deleted_detected_at`
--                                  rempli). Un avis revenu garde sa ligne marquée.
--   reviews_doublons_cleaned_all   avis dont la ligne gardée est marquée disparue.
--                                  C'est la définition d'une suppression dans
--                                  tout le dossier.
-- ============================================================================

SELECT
  "reviews"                                   AS table_bigquery,
  COUNT(*)                                    AS lignes,
  COUNT(DISTINCT r.review_id)                 AS avis,
  COUNT(DISTINCT r.cid)                       AS fiches,
  COUNT(DISTINCT b.country)                   AS pays,
  MIN(DATE(r.created_at))                     AS premiere_publication,
  MAX(DATE(r.created_at))                     AS derniere_publication,
  COUNTIF(r.deleted_detected_at IS NOT NULL)  AS suppressions
FROM `client-divers.reviewflowz.reviews` r
LEFT JOIN `client-divers.reviewflowz.businesses` b USING (cid)

UNION ALL

SELECT
  "reviews_doublons_cleaned_all",
  COUNT(*),
  COUNT(DISTINCT r.review_id),
  COUNT(DISTINCT r.cid),
  COUNT(DISTINCT b.country),
  MIN(DATE(r.created_at)),
  MAX(DATE(r.created_at)),
  COUNTIF(r.deleted_detected_at IS NOT NULL)
FROM `client-divers.reviewflowz.reviews_doublons_cleaned_all` r
LEFT JOIN `client-divers.reviewflowz.businesses` b USING (cid)

UNION ALL

SELECT
  "businesses",
  COUNT(*),
  NULL,
  COUNT(DISTINCT cid),
  COUNT(DISTINCT country),
  NULL,
  NULL,
  NULL
FROM `client-divers.reviewflowz.businesses`
