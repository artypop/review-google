-- ============================================================================
-- 4.0. Suppressions par niveau Local Guide, avant de fixer les paliers
--
-- Table : `reviews_panel_features_03B` (avis publiés du 4 au 17 août 2026).
-- Une ligne par niveau (« sans niveau », puis 1 à 10) et par périmètre.
-- Sert à décider où couper : l'étude exploratoire voyait un risque plat de 1
-- à 3, qui baisse de 4 à 6, puis plat. Palier proposé : 1 à 4, 5 et plus.
-- ============================================================================

WITH avis AS (
  SELECT f.*, s.cid IS NOT NULL AS enseigne_signalee
  FROM `client-divers.reviewflowz.reviews_panel_features_03B` f
  LEFT JOIN `client-divers.reviewflowz.biz_surveillance` s USING (cid)
)

SELECT
  perimetre,
  IFNULL(CAST(local_guide_level AS STRING), "sans niveau")      AS niveau,
  IFNULL(local_guide_level, 0)                                   AS ordre,
  COUNTIF(region = "US")                                         AS us_avis,
  COUNTIF(region = "US" AND supprime)                            AS us_suppressions,
  CAST(ROUND(10000 * COUNTIF(region = "US" AND supprime)
        / NULLIF(COUNTIF(region = "US"), 0), 0) AS INT64)       AS us_pour_10000,
  COUNTIF(region = "Europe")                                     AS europe_avis,
  COUNTIF(region = "Europe" AND supprime)                        AS europe_suppressions,
  CAST(ROUND(10000 * COUNTIF(region = "Europe" AND supprime)
        / NULLIF(COUNTIF(region = "Europe"), 0), 0) AS INT64)   AS europe_pour_10000,
  COUNT(*)                                                       AS ensemble_avis,
  COUNTIF(supprime)                                              AS ensemble_suppressions,
  CAST(ROUND(10000 * COUNTIF(supprime) / COUNT(*), 0) AS INT64) AS ensemble_pour_10000,
  COUNT(DISTINCT IF(supprime, cid, NULL))                        AS fiches_touchees
FROM avis, UNNEST(["tous", "sans_enseignes"]) AS perimetre
WHERE perimetre = "tous" OR NOT enseigne_signalee
GROUP BY perimetre, niveau, ordre
ORDER BY perimetre DESC, ordre
