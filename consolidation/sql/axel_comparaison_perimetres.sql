-- ============================================================================
-- Pour Axel : le même taux de suppression, calculé sur deux tables
--
--   « notre panel »      les avis publiés du 4 au 17 août 2026 (J-7 à J+6), qu'ils
--                        aient été supprimés ou non : c'est 03B
--   « table d'Axel »     les avis publiés du 4 au 18 août (J-7 à J+7), plus TOUS
--                        les avis supprimés pendant le suivi, quelle que soit
--                        leur date de publication
--
-- Base : `reviews_doublons_cleaned_all`. Une suppression : `deleted_detected_at`
-- rempli. Pour chaque table, par note, par photos publiées par l'auteur et par
-- niveau Local Guide : avis, suppressions, suppressions pour 10 000 avis.
-- ============================================================================

WITH base AS (
  SELECT
    review_id,
    DATE(created_at) AS jour_publication,
    deleted_detected_at IS NOT NULL AS supprime,
    star,
    COALESCE(reviewer_photo_count, 0) AS photos_auteur,
    local_guide_level
  FROM `client-divers.reviewflowz.reviews_doublons_cleaned_all`
),

tables AS (
  SELECT "1. notre panel (03B)" AS table_, b.*
  FROM base b
  WHERE jour_publication BETWEEN DATE "2026-08-04" AND DATE "2026-08-17"
  UNION ALL
  SELECT "2. table d'Axel", b.*
  FROM base b
  WHERE jour_publication BETWEEN DATE "2026-08-04" AND DATE "2026-08-18"
     OR supprime
),

modalites AS (
  SELECT table_, supprime, m.*
  FROM tables, UNNEST([
    STRUCT("0. ensemble" AS caracteristique, 0 AS ordre, "tous les avis" AS modalite),
    STRUCT("1. note", 6 - star, CONCAT(CAST(star AS STRING), " étoile(s)")),
    STRUCT("2. photos publiées par l'auteur",
           CASE WHEN photos_auteur = 0 THEN 1 WHEN photos_auteur <= 20 THEN 2 ELSE 3 END,
           CASE WHEN photos_auteur = 0 THEN "0 photo" WHEN photos_auteur <= 20 THEN "1 à 20 photos"
                ELSE "plus de 20 photos" END),
    STRUCT("4. date de publication",
           CASE WHEN jour_publication < DATE "2026-08-04" THEN 1
                WHEN jour_publication <= DATE "2026-08-18" THEN 2 ELSE 3 END,
           CASE WHEN jour_publication < DATE "2026-08-04" THEN "avant le 4 août"
                WHEN jour_publication <= DATE "2026-08-18" THEN "du 4 au 18 août"
                ELSE "après le 18 août" END),
    STRUCT("3. niveau Local Guide",
           CASE WHEN local_guide_level IS NULL THEN 1 WHEN local_guide_level <= 4 THEN 2 ELSE 3 END,
           CASE WHEN local_guide_level IS NULL THEN "sans niveau"
                WHEN local_guide_level <= 4 THEN "niveau 1 à 4" ELSE "niveau 5 et plus" END)
  ]) AS m
)

SELECT
  caracteristique,
  ordre,
  modalite,
  table_ AS table_utilisee,
  COUNT(*)                                                   AS avis,
  COUNTIF(supprime)                                          AS suppressions,
  CAST(ROUND(10000 * COUNTIF(supprime) / COUNT(*)) AS INT64) AS pour_10000
FROM modalites
GROUP BY caracteristique, ordre, modalite, table_utilisee
ORDER BY caracteristique, ordre, table_utilisee
