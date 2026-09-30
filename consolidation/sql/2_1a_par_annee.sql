-- ============================================================================
-- 2.1a. Suppressions par année de publication — base complète
--
-- Base : `reviews_doublons_cleaned_all`. Les suppressions ont toutes été
-- constatées pendant le suivi, du 12 au 24 août 2026. Une ligne dit : « parmi
-- les avis publiés en 2019 et encore en ligne le 11 août, N ont disparu pendant
-- ces 14 jours ».
-- ============================================================================

WITH avis AS (
  SELECT
    EXTRACT(YEAR FROM r.created_at) AS annee,
    r.deleted_detected_at IS NOT NULL AS supprime,
    s.cid IS NOT NULL AS enseigne_signalee
  FROM `client-divers.reviewflowz.reviews_doublons_cleaned_all` r
  LEFT JOIN `client-divers.reviewflowz.biz_surveillance` s USING (cid)
)

SELECT
  perimetre,
  CAST(annee AS STRING)                              AS annee_publication,
  COUNT(*)                                           AS avis,
  COUNTIF(supprime)                                  AS suppressions,
  ROUND(10000 * COUNTIF(supprime) / COUNT(*), 1)     AS pour_10000
FROM avis, UNNEST(["tous", "sans_enseignes"]) AS perimetre
WHERE perimetre = "tous" OR NOT enseigne_signalee
GROUP BY perimetre, annee
ORDER BY perimetre DESC, annee
