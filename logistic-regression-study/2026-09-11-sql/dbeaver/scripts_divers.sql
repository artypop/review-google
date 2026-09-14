WITH review_deleted AS (
  SELECT COUNT(*
  FROM `client-divers.reviewflowz.reviews`
  WHERE NOT is_update
    AND deleted_detected_at IS NOT NULL
)



SELECT
  *,
  CONCAT("https://www.google.com/maps?cid=", CAST(r.cid AS STRING)) AS web_cid
FROM review_deleted r
LEFT JOIN `client-divers.reviewflowz.businesses` b
  USING (place_id);

/* Suppression dans les 30 derniers jours */
SELECT COUNT(*)
FROM `client-divers`.reviewflowz.reviews
WHERE NOT is_update
  AND deleted_detected_at IS NOT NULL
  AND DATE_DIFF('day', created_at, deleted_detected_at) <= 30
  
/* Review supprimés qui sont toujours supprimés au bout des 14 vagues */
  
WITH supprimes AS (
  SELECT review_id, deleted_detected_at
  FROM `client-divers`.reviewflowz.reviews
  WHERE NOT is_update AND deleted_detected_at IS NOT NULL
)
SELECT COUNT(*)
FROM supprimes s
WHERE NOT EXISTS (
  SELECT 1 FROM `client-divers`.reviewflowz.reviews r
  WHERE r.review_id = s.review_id AND NOT r.is_update AND r.deleted_detected_at IS NULL
)


SELECT * FROM `client-divers.reviewflowz.reviews` WHERE review_id = "ChZDSUhNMG9nS0VJQ0FnSUM2b0oyeVZBEAE";

CREATE OR REPLACE VIEW `client-divers.reviewflowz.ressuscites` AS
WITH flags AS (
  SELECT
    review_id,
    LOGICAL_OR(deleted_detected_at IS NOT NULL) AS a_disparu,
    LOGICAL_OR(deleted_detected_at IS NULL)     AS a_un_retour
  FROM `client-divers.reviewflowz.reviews`
  WHERE NOT is_update
  GROUP BY review_id
  HAVING a_disparu AND a_un_retour
)
SELECT
  r.*,
  CASE WHEN r.deleted_detected_at IS NOT NULL THEN 'disparition' ELSE 'retour' END AS etat
FROM `client-divers.reviewflowz.reviews` r
JOIN flags USING (review_id)
WHERE NOT r.is_update
ORDER BY r.review_id, r.created_at;
