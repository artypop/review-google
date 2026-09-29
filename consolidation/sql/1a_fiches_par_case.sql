-- ============================================================================
-- 1a. Comment le panel de fiches a été tiré
--
-- Nombre de fiches par région, secteur et taille d'entreprise. Le panel a été
-- construit pour que chaque case soit représentée.
--   mono   entreprise d'un seul établissement
--   small  groupe de 4 à 10 établissements
--   large  groupe de 20 à 50 établissements
-- ============================================================================

SELECT
  IF(country = "US", "US", "Europe")                 AS region,
  industry                                           AS secteur,
  COUNTIF(bucket = "mono")                           AS fiches_mono,
  COUNTIF(bucket = "small")                          AS fiches_small,
  COUNTIF(bucket = "large")                          AS fiches_large,
  COUNT(*)                                           AS fiches
FROM `client-divers.reviewflowz.businesses`
GROUP BY region, secteur
ORDER BY region DESC, secteur
