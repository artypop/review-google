-- ============================================================================
-- 0. Ce que contient `corpus_axel`, comparé à 03B
--
-- Le corpus voulu : les avis de 03B (publiés du 4 au 17 août 2026), plus tous
-- les avis supprimés pendant le suivi, quelle que soit leur date de
-- publication. Les avis supprimés viennent de `reviews_doublons_cleaned`.
--
-- Une ligne par contrôle. Attendu si la table est bien « 03B + suppressions » :
--   avis                                     38 431
--   dont supprimés                            4 035
--   publiés du 4 au 17 août                  35 751
--   publiés à d'autres dates                  2 680, tous supprimés
--   avis de 03B absents de corpus_axel            0
--   avis supprimés de la base absents             0
-- ============================================================================

WITH axel AS (
  SELECT
    review_id,
    DATE(created_at) BETWEEN DATE "2026-08-04" AND DATE "2026-08-17" AS dans_la_periode,
    deleted_detected_at IS NOT NULL AS supprime
  FROM `client-divers.reviewflowz.corpus_axel`
),

panel_03b AS (
  SELECT review_id
  FROM `client-divers.reviewflowz.03B_reviews_panel_filtered_08_04_to_08_26`
),

supprimes_base AS (
  SELECT review_id
  FROM `client-divers.reviewflowz.reviews_doublons_cleaned`
  WHERE deleted_detected_at IS NOT NULL
)

SELECT 1 AS ordre, "lignes de corpus_axel" AS controle, COUNT(*) AS valeur FROM axel
UNION ALL
SELECT 2, "avis distincts", COUNT(DISTINCT review_id) FROM axel
UNION ALL
SELECT 3, "dont supprimés", COUNTIF(supprime) FROM axel
UNION ALL
SELECT 4, "publiés du 4 au 17 août", COUNTIF(dans_la_periode) FROM axel
UNION ALL
SELECT 5, "publiés du 4 au 17 août, supprimés", COUNTIF(dans_la_periode AND supprime) FROM axel
UNION ALL
SELECT 6, "publiés à d'autres dates", COUNTIF(NOT dans_la_periode) FROM axel
UNION ALL
SELECT 7, "publiés à d'autres dates, supprimés", COUNTIF(NOT dans_la_periode AND supprime) FROM axel
UNION ALL
SELECT 8, "avis de corpus_axel absents de 03B", COUNT(*) FROM axel
       WHERE review_id NOT IN (SELECT review_id FROM panel_03b)
UNION ALL
SELECT 9, "avis de 03B absents de corpus_axel", COUNT(*) FROM panel_03b
       WHERE review_id NOT IN (SELECT review_id FROM axel)
UNION ALL
SELECT 10, "avis supprimés de reviews_doublons_cleaned absents de corpus_axel", COUNT(*)
       FROM supprimes_base
       WHERE review_id NOT IN (SELECT review_id FROM axel)
ORDER BY ordre
