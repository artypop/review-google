-- ============================================================================
-- 11, étape C. Dans les fiches touchées en masse (plus de 10 suppressions en
-- 14 jours), avis 4 et 5 étoiles avec texte regroupés par fiche, tranche d'âge
-- et présence d'un nom : avis et suppressions.
--
-- Base : `reviews_doublons_cleaned_all`. Marquage du nom : `reviews_name_enriched`
-- (Axel). Âge au 11 août 2026, mêmes tranches que `11_fiches.sql`.
-- ============================================================================

WITH noms AS (
  SELECT review_id, LOGICAL_OR(has_name) AS a_un_nom
  FROM `client-divers.reviewflowz.reviews_name_enriched`
  GROUP BY review_id
),

masse AS (
  SELECT cid
  FROM `client-divers.reviewflowz.reviews_doublons_cleaned_all`
  GROUP BY cid
  HAVING COUNTIF(deleted_detected_at IS NOT NULL) > 10
)

SELECT
  r.cid,
  CASE WHEN r.cid IN ("3163466139043001754", "10346942689164695031") THEN "salles_espagnoles"
       WHEN s.cid IS NOT NULL THEN "chaines_antiparasitaires"
       ELSE "autres" END                                           AS groupe,
  CASE
    WHEN DATE(r.created_at) >= DATE "2026-08-11"                         THEN "pendant"
    WHEN DATE_DIFF(DATE "2026-08-11", DATE(r.created_at), DAY) <= 30   THEN "m30j"
    WHEN DATE_DIFF(DATE "2026-08-11", DATE(r.created_at), DAY) <= 90   THEN "30_90j"
    WHEN DATE_DIFF(DATE "2026-08-11", DATE(r.created_at), DAY) <= 365  THEN "90_365j"
    WHEN DATE_DIFF(DATE "2026-08-11", DATE(r.created_at), DAY) <= 1095 THEN "1_3ans"
    ELSE "p3ans"
  END                                                              AS age,
  n.a_un_nom,
  COUNT(*)                                                         AS avis,
  COUNTIF(r.deleted_detected_at IS NOT NULL)                       AS suppressions
FROM `client-divers.reviewflowz.reviews_doublons_cleaned_all` r
JOIN masse USING (cid)
JOIN noms n USING (review_id)
LEFT JOIN `client-divers.reviewflowz.biz_surveillance` s USING (cid)
GROUP BY r.cid, groupe, age, n.a_un_nom
