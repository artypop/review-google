-- ==============================================================================
-- File: sql/04_avis_features.sql
-- Table: client-divers.reviewflowz.avis_features
-- Description: Table de caractérisation individuelle des avis Google et des 
--              contextes d'arrivée (langues, profils auteurs, pics d'avis/raids).
-- ==============================================================================

CREATE OR REPLACE TABLE `client-divers.reviewflowz.avis_features` AS

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
  FROM `client-divers`.reviewflowz.reviews
  WHERE NOT is_update -- Sécurité : exclusion des 2 012 lignes d'historique de modification
),

-- 1. Langue modale (la plus fréquente) par fiche d'établissement (cid)
modal_language_per_cid AS (
  SELECT cid, language AS modal_language
  FROM (
    SELECT 
      cid, 
      language, 
      COUNT(*) AS n,
      ROW_NUMBER() OVER (PARTITION BY cid ORDER BY COUNT(*) DESC, language) AS rn
    FROM base_reviews
    WHERE language IS NOT NULL
    GROUP BY cid, language
  )
  WHERE rn = 1
),

-- 2a. Statistiques globales par fiche d'établissement (sur toute la période)
cid_overall_stats AS (
  SELECT
    cid,
    COUNT(*) AS total_reviews_cid,
    -- Durée totale d'activité de la fiche en jours (au moins 1)
    GREATEST(DATE_DIFF(MAX(CAST(created_at AS DATE)), MIN(CAST(created_at AS DATE)), DAY) + 1, 1) AS total_days_cid
  FROM base_reviews
  GROUP BY cid
),

-- 2b. Volume quotidien et moyenne d'avis journalière globale de la fiche
cid_daily_stats AS (
  SELECT
    r.cid,
    CAST(r.created_at AS DATE) AS created_date,
    COUNT(*) AS n_reviews_same_day,
    -- Moyenne journalière globale de la fiche = total avis / total jours de vie
    s.total_reviews_cid / s.total_days_cid AS avg_daily_reviews
  FROM base_reviews r
  JOIN cid_overall_stats s ON r.cid = s.cid
  GROUP BY r.cid, CAST(r.created_at AS DATE), s.total_reviews_cid, s.total_days_cid
),

-- 3. Détection des rafales d'un même auteur le même jour (author_same_day_burst)
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
  
  -- A. Caractéristiques intrinsèques de l'avis
  r.star,
  (r.text IS NOT NULL AND LENGTH(TRIM(r.text)) > 0) AS has_text,
  COALESCE(LENGTH(r.text), 0) AS text_chars,
  COALESCE(r.n_photos, 0) AS n_photos,
  (COALESCE(r.n_photos, 0) > 0) AS has_photo,
  (r.reply_text IS NOT NULL) AS has_reply,
  
  -- B. Profil et activité de l'auteur
  COALESCE(r.reviewer_review_count, 0) AS reviewer_review_count,
  LN(COALESCE(r.reviewer_review_count, 0) + 1) AS log_rc,
  (COALESCE(r.reviewer_review_count, 0) = 0) AS rc_zero,
  r.local_guide_level,
  (r.local_guide_level IS NULL) AS lg_level_missing,
  r.local_guide_level IS NULL AND reviewer_review_count = 0 AS new_account,
  COALESCE(adb.author_same_day_burst, 1) AS author_same_day_burst,
  
  -- C. Analyse linguistique (Double axe)
  r.language,
  -- L'avis est-il écrit dans une langue qui n'est pas la langue principale du pays ?
  (r.language IS NOT NULL AND b.country IS NOT NULL AND r.language != LOWER(b.country)) AS langue_etrangere_au_pays,
  -- L'avis est-il écrit dans une langue inhabituelle pour cette fiche spécifique ?
  (r.language IS NOT NULL AND ml.modal_language IS NOT NULL AND r.language != ml.modal_language) AS langue_minoritaire_sur_la_fiche,

  -- D. Caractéristiques de l'établissement (Businesses)
  b.industry,
  b.country,
  b.bucket,

  -- E. Métriques de sur-afflux / Raid (Ratio du jour vs moyenne historique de la fiche)
  cds.n_reviews_same_day AS n_avis_meme_jour_fiche,
  ROUND(SAFE_DIVIDE(cds.n_reviews_same_day, NULLIF(cds.avg_daily_reviews, 0)), 2) AS ratio_pic_journalier_fiche,
  ROUND(LN(SAFE_DIVIDE(cds.n_reviews_same_day, NULLIF(cds.avg_daily_reviews, 0)) + 1), 4) AS log_ratio_pic_journalier_fiche

FROM base_reviews r
LEFT JOIN `client-divers`.reviewflowz.businesses b ON r.cid = b.cid
LEFT JOIN modal_language_per_cid ml ON r.cid = ml.cid
LEFT JOIN cid_daily_stats cds ON r.cid = cds.cid AND CAST(r.created_at AS DATE) = cds.created_date
LEFT JOIN author_daily_burst adb ON r.review_link = adb.review_link AND CAST(r.created_at AS DATE) = adb.created_date;
