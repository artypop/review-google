CREATE OR REPLACE TABLE `client-divers`.reviewflowz.reviews_panel_selection AS

  -- Reviews uniques dans le corpus
WITH comptage AS (
    SELECT
        review_id,
        COUNT(*) AS nb_total
    FROM
        `client-divers`.reviewflowz.reviews
    GROUP BY
        review_id
    HAVING
        COUNT(*) = 1
)

-- Restriction aux avis qui sont crées à 90 jours de la première vague et au plus tard 6 jours après la première vague pour voir 8 jours de déletion

SELECT
	id,
	place_id,
	cid,
	reviews.review_id,
	is_update,
	changed_fields,
	star,
	text,
	`language`,
	created_at,
	updated_at,
	review_link,
	reviewer_name,
	reviewer_avatar,
	reviewer_review_count,
	reviewer_photo_count,
	local_guide,
	local_guide_level,
	n_photos,
	photo_urls,
	reply_text,
	reply_date,
	CAST(created_at AS DATE) AS created_at_day,
	CAST(first_seen_at AS DATE) AS first_seen_at_day,
	CAST(last_seen_at AS DATE) AS last_seen_at_day,
	CAST(deleted_detected_at AS DATE) AS deleted_detected_at_day
FROM
	`client-divers`.reviewflowz.reviews AS reviews
JOIN comptage
    ON reviews.review_id = comptage.review_id
WHERE CAST(reviews.created_at AS DATE) >= "2026-05-13" AND CAST(reviews.created_at AS DATE) <= "2026-08-16"