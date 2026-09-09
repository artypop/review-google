-- Isole les avis classés edit_bugs (disparition + retour + 2 textes distincts)
-- pour inspection manuelle : voir les deux versions du texte côte à côte.

WITH base AS (
  SELECT review_id, cid, star, text, created_at, first_seen_at, last_seen_at, deleted_detected_at
  FROM `client-divers`.reviewflowz.reviews
  WHERE NOT is_update
),

flags AS (
  SELECT
    review_id,
    LOGICAL_OR(deleted_detected_at IS NOT NULL) AS a_disparu,
    LOGICAL_OR(deleted_detected_at IS NULL)     AS a_un_retour,
    COUNT(DISTINCT text)                        AS n_textes
  FROM base
  GROUP BY review_id
),

edit_bugs AS (
  SELECT review_id FROM flags WHERE a_disparu AND a_un_retour AND n_textes = 2
)

SELECT
  b.review_id,
  b.cid,
  b.star,
  b.text,
  b.created_at,
  b.first_seen_at,
  b.last_seen_at,
  b.deleted_detected_at
FROM base b
JOIN edit_bugs eb USING (review_id)
ORDER BY b.review_id, b.first_seen_at;
