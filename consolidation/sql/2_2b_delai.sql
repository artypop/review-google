-- ============================================================================
-- 2.2b. Jours entre publication et suppression, par note
--
-- Mêmes groupes et même base que `2_2_resume.sql`. Seuls les avis supprimés.
-- `delai_j` : jours entre la publication et la constatation de la
-- disparition, de 1 à 30. Au-delà, la ligne est regroupée dans `tranche`.
-- ============================================================================

WITH supprimes AS (
  SELECT
    IF(r.cid IN ("3163466139043001754", "10346942689164695031"),
       "salles_espagnoles", "chaines_antiparasitaires") AS groupe,
    r.star AS note,
    DATE_DIFF(DATE(r.deleted_detected_at), DATE(r.created_at), DAY) AS delai
  FROM `client-divers.reviewflowz.reviews_doublons_cleaned` r
  JOIN `client-divers.reviewflowz.biz_surveillance` s USING (cid)
  WHERE r.deleted_detected_at IS NOT NULL
)

SELECT
  groupe,
  CASE WHEN delai <= 30  THEN "30 jours ou moins"
       WHEN delai <= 365 THEN "31 à 365 jours"
       ELSE "plus d'un an" END                  AS tranche,
  IF(delai <= 30, delai, NULL)                  AS delai_j,
  COUNTIF(note = 5)                             AS supprimes_5_etoiles,
  COUNTIF(note = 4)                             AS supprimes_4_etoiles,
  COUNTIF(note IN (2, 3))                       AS supprimes_2_3_etoiles,
  COUNTIF(note = 1)                             AS supprimes_1_etoile,
  COUNT(*)                                      AS supprimes
FROM supprimes
GROUP BY groupe, tranche, delai_j
ORDER BY groupe, tranche, delai_j
