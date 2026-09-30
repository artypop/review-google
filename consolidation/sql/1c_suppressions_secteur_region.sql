-- ============================================================================
-- 1c. Suppressions pour 10 000 avis, par secteur, Europe et US — base complète
--
-- Base : `reviews_doublons_cleaned_all`, toutes dates de publication.
-- Une suppression : la ligne gardée de l'avis est marquée disparue
-- (`deleted_detected_at` rempli). Elles ont toutes été constatées du 12 au
-- 24 août 2026.
-- Lecture d'une case : « en Europe, sur 10 000 avis de restaurant présents
-- dans la base, N ont disparu pendant les 14 jours de suivi ».
-- La ligne « Tous secteurs » donne le total du périmètre.
-- ============================================================================

WITH avis AS (
  SELECT
    IF(b.country = "US", "US", "Europe") AS region,
    CASE b.industry
      WHEN "automotive"       THEN "Automobile"
      WHEN "home_services"    THEN "Services à domicile"
      WHEN "healthcare"       THEN "Santé"
      WHEN "wellness_fitness" THEN "Sport et bien-être"
      WHEN "food_beverage"    THEN "Restauration"
      WHEN "travel"           THEN "Voyage"
      WHEN "hospitality"      THEN "Hôtellerie"
      ELSE b.industry
    END AS secteur,
    r.deleted_detected_at IS NOT NULL AS supprime,
    s.cid IS NOT NULL AS enseigne_signalee
  FROM `client-divers.reviewflowz.reviews_doublons_cleaned_all` r
  LEFT JOIN `client-divers.reviewflowz.businesses` b USING (cid)
  LEFT JOIN `client-divers.reviewflowz.biz_surveillance` s USING (cid)
),

avis_par_perimetre AS (
  SELECT a.region, a.supprime, perimetre, secteur_vu
  FROM avis a,
       UNNEST(["tous", "sans_enseignes"]) AS perimetre,
       UNNEST([a.secteur, "Tous secteurs"]) AS secteur_vu
  WHERE perimetre = "tous" OR NOT a.enseigne_signalee
)

SELECT
  perimetre,
  secteur_vu                                                AS secteur,
  COUNTIF(region = "Europe")                                AS europe_avis,
  COUNTIF(region = "Europe" AND supprime)                   AS europe_suppressions,
  ROUND(10000 * COUNTIF(region = "Europe" AND supprime)
        / NULLIF(COUNTIF(region = "Europe"), 0), 1)         AS europe_pour_10000,
  COUNTIF(region = "US")                                    AS us_avis,
  COUNTIF(region = "US" AND supprime)                       AS us_suppressions,
  ROUND(10000 * COUNTIF(region = "US" AND supprime)
        / NULLIF(COUNTIF(region = "US"), 0), 1)             AS us_pour_10000,
  COUNT(*)                                                  AS ensemble_avis,
  COUNTIF(supprime)                                         AS ensemble_suppressions,
  ROUND(10000 * COUNTIF(supprime) / COUNT(*), 1)            AS ensemble_pour_10000
FROM avis_par_perimetre
GROUP BY perimetre, secteur
ORDER BY perimetre DESC, secteur = "Tous secteurs", ensemble_pour_10000 DESC
