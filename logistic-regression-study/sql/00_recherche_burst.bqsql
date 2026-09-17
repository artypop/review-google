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
),
-- Restriction aux avis unique (pas d'updates)

review_panel AS (
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
	CAST(created_at AS DATE) AS created_at,
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
	CAST(first_seen_at AS DATE) AS first_seen_at,
	CAST(last_seen_at AS DATE) AS last_seen_at,
	CAST(deleted_detected_at AS DATE) AS deleted_detected_at
FROM
	`client-divers`.reviewflowz.reviews AS reviews
JOIN comptage
    ON
	reviews.review_id = comptage.review_id),
	
-- nb d'avis par jour

 avis_par_jour AS (
    SELECT
        cid,
        created_at,
        COUNT(*) AS nb_avis_ce_jour
    FROM
        review_panel
    GROUP BY
        cid, created_at
),

-- Moyenne et Max du nb_avis_ce_jour

stats_par_fiche AS (
    SELECT
        cid,
        AVG(nb_avis_ce_jour) AS moyenne_avis_jour,
        MAX(nb_avis_ce_jour) AS pic_max_jour
    FROM
        avis_par_jour
    GROUP BY
        cid
),

-- Construction de la table

pic_avec_date AS (
    SELECT
        avis_par_jour.cid,
        avis_par_jour.created_at AS date_du_pic,
        avis_par_jour.nb_avis_ce_jour
    FROM
        avis_par_jour
    JOIN stats_par_fiche
        ON avis_par_jour.cid = stats_par_fiche.cid
        AND avis_par_jour.nb_avis_ce_jour = stats_par_fiche.pic_max_jour
),

-- Nb de suppression des avis publiés le jour du burst

suppressions_du_burst AS (
    SELECT
        pic_avec_date.cid,
        pic_avec_date.date_du_pic,
        COUNTIF(review_panel.deleted_detected_at IS NOT NULL) AS nb_supprimes
    FROM
        pic_avec_date
    JOIN review_panel
        ON pic_avec_date.cid = review_panel.cid
        AND pic_avec_date.date_du_pic = review_panel.created_at
    GROUP BY
        pic_avec_date.cid, pic_avec_date.date_du_pic
)

SELECT
    stats_par_fiche.cid,
    biz.review_count_at_build,
    stats_par_fiche.moyenne_avis_jour,
    stats_par_fiche.pic_max_jour,
    pic_avec_date.date_du_pic,
    stats_par_fiche.pic_max_jour / stats_par_fiche.moyenne_avis_jour AS ratio_pic_sur_moyenne,
    suppressions_du_burst.nb_supprimes
FROM
    stats_par_fiche
JOIN pic_avec_date
    ON stats_par_fiche.cid = pic_avec_date.cid
JOIN suppressions_du_burst
    ON pic_avec_date.cid = suppressions_du_burst.cid
    AND pic_avec_date.date_du_pic = suppressions_du_burst.date_du_pic
JOIN `client-divers`.reviewflowz.businesses AS biz
    ON stats_par_fiche.cid = biz.cid
WHERE
    pic_avec_date.date_du_pic BETWEEN "2026-05-13" AND "2026-08-16"
ORDER BY
     nb_supprimes DESC