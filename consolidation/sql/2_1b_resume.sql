-- ============================================================================
-- 2.1b. Résumé : les 8 premiers jours de l'avis, et la suite
--
-- Mêmes avis et même calcul que `2_1b_par_age.sql` (publiés du 12 juillet au
-- 24 août 2026). Deux tranches d'âge :
--   « 1 à 8 jours »    l'avis a entre 1 et 8 jours le jour où il disparaît
--   « 9 jours et plus »
--
-- `jours_d_observation` : chaque avis compte une fois par jour où le robot
-- pouvait le voir disparaître. `pour_10000_par_jour` = suppressions pour
-- 10 000 avis en ligne, en moyenne par jour de la tranche.
-- La ligne « total » donne les avis de la fenêtre et ceux qui ont disparu.
-- ============================================================================

WITH premiere_vue AS (
  SELECT review_id, DATE(MIN(first_seen_at)) AS premier_jour_vu
  FROM `client-divers.reviewflowz.reviews`
  GROUP BY review_id
),

avis AS (
  SELECT
    IF(b.country = "US", "US", "Europe") AS region,
    s.cid IS NOT NULL AS enseigne_signalee,
    r.deleted_detected_at IS NOT NULL AS supprime,
    GREATEST(DATE_DIFF(pv.premier_jour_vu, DATE(r.created_at), DAY), 0) AS age_entree,
    DATE_DIFF(COALESCE(DATE(r.deleted_detected_at), DATE "2026-08-24"),
              DATE(r.created_at), DAY) AS age_sortie
  FROM `client-divers.reviewflowz.reviews_doublons_cleaned` r
  JOIN premiere_vue pv USING (review_id)
  LEFT JOIN `client-divers.reviewflowz.businesses` b USING (cid)
  LEFT JOIN `client-divers.reviewflowz.biz_surveillance` s USING (cid)
  WHERE DATE(r.created_at) BETWEEN DATE "2026-07-12" AND DATE "2026-08-24"
),

jours AS (
  SELECT
    a.region,
    a.enseigne_signalee,
    IF(age <= 8, "1 à 8 jours", "9 jours et plus") AS tranche,
    a.supprime AND age = a.age_sortie AS disparu_ce_jour
  FROM avis a, UNNEST(GENERATE_ARRAY(a.age_entree + 1, a.age_sortie)) AS age
)

SELECT
  perimetre,
  region_vue                                         AS region,
  tranche,
  NULL                                               AS avis_publies,
  COUNTIF(disparu_ce_jour)                           AS suppressions,
  COUNT(*)                                           AS jours_d_observation,
  ROUND(10000 * COUNTIF(disparu_ce_jour) / COUNT(*), 1) AS pour_10000_par_jour
FROM jours,
     UNNEST(["tous", "sans_enseignes"]) AS perimetre,
     UNNEST([region, "ensemble"])       AS region_vue
WHERE perimetre = "tous" OR NOT enseigne_signalee
GROUP BY perimetre, region, tranche

UNION ALL

SELECT
  perimetre,
  region_vue,
  "total",
  COUNT(*),
  COUNTIF(supprime),
  NULL,
  NULL
FROM avis,
     UNNEST(["tous", "sans_enseignes"]) AS perimetre,
     UNNEST([region, "ensemble"])       AS region_vue
WHERE perimetre = "tous" OR NOT enseigne_signalee
GROUP BY perimetre, region_vue

ORDER BY perimetre DESC, region, tranche
