CREATE OR REPLACE TABLE `client-divers.reviewflowz.avis_deleted_panel` AS

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

resurrected AS (
  SELECT review_id FROM flags WHERE a_disparu AND a_un_retour AND n_textes <= 1
),

edit_bugs AS (
  SELECT review_id FROM flags WHERE a_disparu AND a_un_retour AND n_textes = 2
),

retours AS (
  SELECT review_id, MIN(first_seen_at) AS reapparu_le
  FROM base
  WHERE deleted_detected_at IS NULL
  GROUP BY review_id
),

instances AS (
  SELECT b.review_id, b.deleted_detected_at, ret.reapparu_le
  FROM base b
  JOIN resurrected res USING (review_id)
  JOIN retours ret USING (review_id)
  WHERE b.deleted_detected_at IS NOT NULL
),

mort_reelle AS (
  SELECT review_id, MIN(deleted_detected_at) AS death_at
  FROM instances
  WHERE TIMESTAMP_DIFF(reapparu_le, deleted_detected_at, DAY) >= 2
  GROUP BY review_id
),

-- ajout : created_at, la date de dépôt de l'avis
canon AS (
  SELECT
    review_id,
    ANY_VALUE(cid) AS cid,
    MIN(first_seen_at) AS first_seen_at,
    MIN(created_at) AS created_at,
    MAX(CASE WHEN deleted_detected_at IS NOT NULL THEN deleted_detected_at END) AS raw_deleted_at
  FROM base
  GROUP BY review_id
),

-- ajout : created_at transporté
reviews_corriges AS (
  SELECT
    c.review_id, c.cid, c.first_seen_at, c.created_at,
    CASE
      WHEN eb.review_id IS NOT NULL THEN NULL
      WHEN res.review_id IS NOT NULL THEN mr.death_at
      ELSE c.raw_deleted_at
    END AS death_at
  FROM canon c
  LEFT JOIN edit_bugs eb USING (review_id)
  LEFT JOIN resurrected res USING (review_id)
  LEFT JOIN mort_reelle mr USING (review_id)
),

-- ajout : created_at transporté
avec_vague_de_mort AS (
  SELECT r.review_id, r.cid, r.first_seen_at, r.created_at, r.death_at,
    (SELECT MAX(w2.wave) FROM `client-divers.reviewflowz.waves` w2
     WHERE w2.started_at <= r.death_at) AS death_wave
  FROM reviews_corriges r
)

SELECT
  r.review_id,
  r.cid,
  w.wave,
  COALESCE(r.death_wave = w.wave, FALSE) AS deleted,
  CASE WHEN r.death_at IS NOT NULL
       THEN TIMESTAMP_DIFF(r.death_at, r.created_at, DAY)
  END AS jours_en_ligne_avant_suppression,
  -- ajout : jours depuis le début de la surveillance, pas depuis la vraie date de dépôt
  CASE WHEN r.death_at IS NOT NULL
       THEN TIMESTAMP_DIFF(r.death_at, r.first_seen_at, DAY)
  END AS jours_sous_surveillance_avant_suppression
FROM avec_vague_de_mort r
JOIN `client-divers`.reviewflowz.waves w
  ON w.wave >= 2
  AND r.first_seen_at < w.started_at
  AND (r.death_wave IS NULL OR w.wave <= r.death_wave)
ORDER BY r.review_id, w.wave;

