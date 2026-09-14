CREATE OR REPLACE TABLE `client-divers`.reviewflowz.total_review_per_reviewer_on_unique_review AS (
SELECT
	review_link,
	COUNT(*) AS total_review_per_reviewer
FROM
	`client-divers`.reviewflowz.reviews_panel_selection
GROUP BY
	review_link
ORDER BY
	total_review_per_reviewer DESC
	)