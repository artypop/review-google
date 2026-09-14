WITH base_reviews AS (
  SELECT
    review_id,
    cid,
    star,
    text,
    created_at,
    language,
    reviewer_review_count,
    local_guide_level,
    n_photos,
    reply_text,
    review_link
  FROM `client-divers`.reviewflowz.reviews_panel_selection 
  QUALIFY ROW_NUMBER() OVER (
    PARTITION BY review_id
    ORDER BY first_seen_at_day, (deleted_detected_at_day IS NOT NULL)
  ) = 1
),

-- 1. Langue la plus frequente sur la fiche
modal_language_per_cid AS (
  SELECT cid, modal_language
  FROM (
    SELECT
      cid,
      language AS modal_language,
      ROW_NUMBER() OVER (PARTITION BY cid ORDER BY COUNT(*) DESC, language) AS rn
    FROM base_reviews
    WHERE language IS NOT NULL
    GROUP BY cid, language
  )
  WHERE rn = 1
),

-- 2a. Volume et duree de vie de chaque fiche
cid_overall_stats AS (
  SELECT
    cid,
    COUNT(*) AS total_reviews_cid,
    GREATEST(
      DATE_DIFF(MAX(CAST(created_at AS DATE)), MIN(CAST(created_at AS DATE)), DAY) + 1,
      1
    ) AS total_days_cid
  FROM base_reviews
  GROUP BY cid
),

-- 2b. Avis deposes le meme jour sur la fiche, compare a son rythme habituel
cid_daily_stats AS (
  SELECT
    r.cid,
    CAST(r.created_at AS DATE) AS created_date,
    COUNT(*) AS n_reviews_same_day,
    s.total_reviews_cid / s.total_days_cid AS avg_daily_reviews
  FROM base_reviews r
  JOIN cid_overall_stats s ON r.cid = s.cid
  GROUP BY r.cid, CAST(r.created_at AS DATE), s.total_reviews_cid, s.total_days_cid
),

-- 3. Rafales : plusieurs avis du meme auteur le meme jour
author_daily_burst AS (
  SELECT
    review_link,
    CAST(created_at AS DATE) AS created_date,
    COUNT(*) AS author_same_day_burst
  FROM base_reviews
  WHERE review_link IS NOT NULL
  GROUP BY review_link, CAST(created_at AS DATE)
)

SELECT
  r.review_id,
  r.cid,

  -- Identifiant d'auteur, pour le decoupage entrainement / test.
  CAST(FARM_FINGERPRINT(COALESCE(r.review_link, r.review_id)) AS STRING) AS author_key,

  -- A. Caracteristiques de l'avis
  r.star,
  (r.text IS NOT NULL AND LENGTH(TRIM(r.text)) > 0) AS has_text,
  COALESCE(LENGTH(r.text), 0) AS text_chars,
  COALESCE(r.n_photos, 0) AS n_photos,
  (COALESCE(r.n_photos, 0) > 0) AS has_photo,
  (r.reply_text IS NOT NULL) AS has_reply,

  -- B. Profil de l'auteur
  --    rc_zero, lg_level_missing et new_account se recouvrent : new_account
  --    vaut 1 exactement quand les deux autres valent 1. Mises ensemble dans
  --    une regression, ces trois colonnes se partagent un seul effet et
  --    deviennent illisibles. Elles sont conservees ici pour la description ;
  --    c'est le script Python qui les recombine en une seule variable a quatre
  --    situations exclusives.
  COALESCE(r.reviewer_review_count, 0) AS reviewer_review_count,
  LN(COALESCE(r.reviewer_review_count, 0) + 1) AS log_rc,
  (COALESCE(r.reviewer_review_count, 0) = 0) AS rc_zero,
  r.local_guide_level,
  (r.local_guide_level IS NULL) AS lg_level_missing,
  (r.local_guide_level IS NULL AND COALESCE(r.reviewer_review_count, 0) = 0) AS new_account,
  COALESCE(adb.author_same_day_burst, 1) AS author_same_day_burst,

  -- C. Langue
  r.language,
  (r.language IS NOT NULL AND b.country IS NOT NULL
   AND r.language != LOWER(b.country)) AS langue_etrangere_au_pays,
  (r.language IS NOT NULL AND ml.modal_language IS NOT NULL
   AND r.language != ml.modal_language) AS langue_minoritaire_sur_la_fiche,

  -- D. Etablissement
  b.industry,
  b.country,
  b.bucket,

  -- E. Sur-afflux d'avis sur la fiche le jour du depot
  cds.n_reviews_same_day AS n_avis_meme_jour_fiche,
  ROUND(SAFE_DIVIDE(cds.n_reviews_same_day, NULLIF(cds.avg_daily_reviews, 0)), 2)
    AS ratio_pic_journalier_fiche,
  LN(ROUND(SAFE_DIVIDE(cds.n_reviews_same_day, NULLIF(cds.avg_daily_reviews, 0)), 2) + 1)
    AS log_ratio_pic_journalier_fiche

FROM base_reviews r
LEFT JOIN `client-divers`.reviewflowz.businesses b ON r.cid = b.cid
LEFT JOIN modal_language_per_cid ml ON r.cid = ml.cid
LEFT JOIN cid_daily_stats cds
  ON r.cid = cds.cid AND CAST(r.created_at AS DATE) = cds.created_date
LEFT JOIN author_daily_burst adb
  ON r.review_link = adb.review_link AND CAST(r.created_at AS DATE) = adb.created_date;