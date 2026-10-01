-- ============================================================================
-- Courbe de vie d'un groupe d'avis fixe, États-Unis et Europe
--
-- Base : `reviews_doublons_cleaned_all`, avis publiés du 10 au 17 août 2026
-- (J-1 à J+6, J = 11 août, premier passage du robot). Le robot les voit dès
-- leur 1er ou 2e jour et les suit tous au moins jusqu'à 7 jours d'âge.
--
-- LE CALCUL, COMPTÉ DIRECTEMENT
--   Pour chaque jour J, sur les avis du groupe, combien ont disparu au plus
--   tard au jour J. Ce sont les mêmes avis à chaque jour : rien n'est enchaîné.
--   Un jour J n'est compté que pour les dates de publication suivies jusque-là
--   (publication + J au plus tard le 24 août, dernier passage).
--
--   Le jour 2 regroupe les 48 premières heures : le robot passe une fois par
--   jour et voit la plupart des avis pour la première fois à 1 jour d'âge.
--
-- Deux découpages par date de publication :
--   « 10 au 17 août » : le groupe entier, jours 2 à 7 ;
--   chaque date du 10 au 17 août : jours 2 à 14 selon la date.
--
-- `vus_apres_2_jours` : avis que le robot a vus pour la première fois après
-- 2 jours d'âge. Une disparition avant ce premier passage échappe au robot.
-- ============================================================================

WITH premiere_vue AS (
  SELECT review_id, DATE(MIN(first_seen_at)) AS premier_jour_vu
  FROM `client-divers.reviewflowz.reviews`
  GROUP BY review_id
),

avis AS (
  SELECT
    r.cid,
    IF(b.country = "US", "US", "Europe") AS region,
    s.cid IS NOT NULL AS enseigne_signalee,
    DATE(r.created_at) AS date_publication,
    r.deleted_detected_at IS NOT NULL AS supprime,
    DATE_DIFF(pv.premier_jour_vu, DATE(r.created_at), DAY) AS age_entree,
    DATE_DIFF(DATE(r.deleted_detected_at), DATE(r.created_at), DAY) AS age_suppression
  FROM `client-divers.reviewflowz.reviews_doublons_cleaned_all` r
  JOIN premiere_vue pv USING (review_id)
  LEFT JOIN `client-divers.reviewflowz.businesses` b USING (cid)
  LEFT JOIN `client-divers.reviewflowz.biz_surveillance` s USING (cid)
  WHERE DATE(r.created_at) BETWEEN DATE "2026-08-10" AND DATE "2026-08-17"
)

SELECT
  perimetre,
  region,
  publication,
  jour,
  COUNT(*)                                                        AS avis,
  COUNTIF(supprime AND age_suppression <= jour)                   AS disparus,
  COUNT(DISTINCT IF(supprime AND age_suppression <= jour, cid, NULL)) AS fiches_touchees,
  COUNTIF(age_entree > 2)                                         AS vus_apres_2_jours,
  ROUND(100 * COUNTIF(supprime AND age_suppression <= jour) / COUNT(*), 3) AS disparus_pct,
  ROUND(100 - 100 * COUNTIF(supprime AND age_suppression <= jour) / COUNT(*), 3)
                                                                  AS encore_en_ligne_pct
FROM avis,
     UNNEST(["tous", "sans_enseignes"])                          AS perimetre,
     UNNEST(["10 au 17 août", FORMAT_DATE("%Y-%m-%d", date_publication)]) AS publication,
     UNNEST(GENERATE_ARRAY(2, 14))                               AS jour
WHERE (perimetre = "tous" OR NOT enseigne_signalee)
  AND DATE_ADD(date_publication, INTERVAL jour DAY) <= DATE "2026-08-24"
  AND (publication != "10 au 17 août" OR jour <= 7)
GROUP BY perimetre, region, publication, jour
ORDER BY perimetre, region, publication, jour
