-- ==============================================================================
-- File: sql/04_avis_features-v3.sql
-- Table: client-divers.reviewflowz.avis_features
-- Description: Caracteristiques individuelles des avis Google et de leur
--              contexte d'arrivee (langues, profil auteur, pics d'avis).
--
-- Ce qui change par rapport a la v2
-- --------------------------------
-- 1. base_reviews ne rendait pas une ligne par avis.
--    `WHERE NOT is_update` laisse passer 4 878 151 lignes pour seulement
--    4 877 534 avis distincts : 617 avis en double. Ce sont les avis disparus
--    puis revenus, qui ont un enregistrement au moment de la disparition et un
--    autre au retour. C'est exactement la population sur laquelle repose la
--    correction de comptage de 01_build_avis_deleted_panel.sql.
--
--    Consequences de ce doublon en v2 :
--      - avis_features sortait 617 lignes en trop ;
--      - jointe dans 05 a une autre table elle aussi non dedoublonnee, chaque
--        avis concerne apparaissait 4 fois par vague dans avis_panel_final,
--        soit 17 858 lignes en trop et 766 suppressions comptees deux fois
--        (5 503 lignes a deleted = 1 pour 4 737 avis reellement supprimes) ;
--      - n_reviews_same_day et author_same_day_burst comptaient ces doublons.
--        Ce dernier point n'est pas anodin : la ligne en double vient de la
--        disparition de l'avis, et elle etait ajoutee au compte d'avis du meme
--        auteur le meme jour. La caracteristique lisait donc en partie la
--        reponse qu'on lui demande de predire. Sur les 602 avis concernes,
--        229 sont comptes supprimes, soit 38 %, contre 0,1 % dans le corpus.
--        Mesure de l'effet apres correction : pour un auteur qui poste 3 avis
--        le meme jour au lieu d'un seul, le risque relatif passe de 7,2 a 3,9.
--
--    Correction : on garde la premiere observation de chaque avis (celle du
--    premier passage du robot). C'est la seule qui soit certainement anterieure
--    a la suppression, donc la seule qui ne fasse pas entrer dans les
--    caracteristiques une information posterieure a ce qu'on cherche a predire.
--
-- 2. Ajout de author_key : identifiant d'auteur derive de review_link. Sert a
--    decouper entrainement et test sans qu'un meme auteur soit des deux cotes.
--    review_link lui-meme n'est pas exporte, l'empreinte suffit.
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
  WHERE NOT is_update -- exclusion des lignes d'historique de modification
  -- Une seule ligne par avis : la premiere fois que le robot l'a vu.
  QUALIFY ROW_NUMBER() OVER (
    PARTITION BY review_id
    ORDER BY first_seen_at, (deleted_detected_at IS NOT NULL)
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
