-- ============================================================================
-- 8. La réponse du propriétaire sur toute la base : les avis, regroupés
--
-- Base : `reviews_doublons_cleaned_all`, avis publiés avant le 4 août 2026, sur les
-- fiches dont l'habitude de réponse est connue. Ce sont les avis que le panel
-- 03B (4 au 17 août) laisse de côté : le point 5 et celui-ci ne se recouvrent pas.
-- Suppressions : du 12 au 24 août.
--
-- Une ligne = une fiche et une combinaison de caractéristiques.
--   n   avis de cette fiche qui ont cette combinaison
--   k   parmi eux, ceux qui disparaissent
-- 300 avis 5 étoiles, sans photo, de plus d'un an, répondus, d'une même fiche
-- font une ligne avec n = 300 : le modèle donne le même résultat qu'avec
-- 300 lignes, et Python reçoit moins de lignes.
--
--   repondu    le propriétaire avait répondu AVANT le 11 août.
--   age        âge de l'avis le 11 août. Publié avant le 4 août : 8 jours ou plus.
--   taux_reponse
--              l'habitude de la fiche : part de ses avis, publiés du 2025-08-11
--              au 2026-08-03, qui avaient une réponse avant le 11 août. Inconnue
--              sous 10 avis : la fiche sort. Bloc repris tel quel de
--              `logistic-regression-study/sql/03B_adding_features.bqsql`. Le
--              script la range en tranches (`commun.py`).
--   note, local_guide, photo_jointe, texte, photos_auteur, avis_auteur
--              mêmes paliers qu'au 4b (`4b_quel_avis.py`), lus au dernier
--              passage où l'avis est vu.
--   enseigne, jours_de_suppression
--              remplis sur les seules lignes qui perdent un avis, pour
--              `8_fiches_par_case.csv`.
-- ============================================================================

WITH habitude_reponse_fiche AS (
  SELECT
    cid,
    COUNT(*) AS n_avis,
    COUNTIF(reply_date IS NOT NULL
            AND CAST(reply_date AS DATE) < DATE "2026-08-11") / COUNT(*) AS taux
  FROM `client-divers.reviewflowz.01_reviews_avis_update_et_unique`
  WHERE CAST(created_at AS DATE) BETWEEN DATE "2025-08-11" AND DATE "2026-08-03"
  GROUP BY cid
),

avis AS (
  SELECT
    r.cid,
    b.name AS enseigne,
    IF(b.country = "US", "US", "Europe") AS region,
    b.bucket AS taille,
    CASE b.industry
      WHEN "automotive"       THEN "Automobile"
      WHEN "home_services"    THEN "Services à domicile"
      WHEN "healthcare"       THEN "Santé"
      WHEN "wellness_fitness" THEN "Sport et bien-être"
      WHEN "food_beverage"    THEN "Restauration"
      WHEN "travel"           THEN "Voyage"
      WHEN "hospitality"      THEN "Hôtellerie"
      ELSE b.industry
    END AS secteur,
    s.cid IS NOT NULL AS enseigne_signalee,
    h.taux AS taux_reponse,
    CASE WHEN DATE_DIFF(DATE "2026-08-11", CAST(r.created_at AS DATE), DAY) <= 30 THEN "8 à 30 jours"
         WHEN DATE_DIFF(DATE "2026-08-11", CAST(r.created_at AS DATE), DAY) <= 90 THEN "31 à 90 jours"
         WHEN DATE_DIFF(DATE "2026-08-11", CAST(r.created_at AS DATE), DAY) <= 365 THEN "91 à 365 jours"
         ELSE "plus d'un an" END AS age,
    r.reply_date IS NOT NULL AND CAST(r.reply_date AS DATE) < DATE "2026-08-11" AS repondu,
    CONCAT(CAST(r.star AS STRING), " étoile(s)") AS note,
    CASE WHEN r.local_guide_level IS NULL THEN "sans niveau"
         WHEN r.local_guide_level <= 4 THEN "niveau 1 à 4" ELSE "niveau 5 et plus" END AS local_guide,
    IF(COALESCE(r.n_photos, 0) > 0, "avec photo", "sans photo") AS photo_jointe,
    CASE WHEN r.text IS NULL OR LENGTH(TRIM(r.text)) = 0 THEN "sans texte"
         WHEN LENGTH(r.text) <= 50 THEN "1 à 50 caractères"
         WHEN LENGTH(r.text) <= 200 THEN "51 à 200 caractères"
         ELSE "plus de 200 caractères" END AS texte,
    CASE WHEN COALESCE(r.reviewer_photo_count, 0) = 0 THEN "0 photo"
         WHEN r.reviewer_photo_count <= 20 THEN "1 à 20 photos"
         ELSE "plus de 20 photos" END AS photos_auteur,
    CASE WHEN COALESCE(r.reviewer_review_count, 0) <= 1 THEN "1 avis ou moins"
         WHEN r.reviewer_review_count <= 20 THEN "2 à 20 avis"
         ELSE "plus de 20 avis" END AS avis_auteur,
    DATE(r.deleted_detected_at) AS jour_de_suppression
  FROM `client-divers.reviewflowz.reviews_doublons_cleaned_all` r
  JOIN habitude_reponse_fiche h USING (cid)
  LEFT JOIN `client-divers.reviewflowz.businesses` b USING (cid)
  LEFT JOIN `client-divers.reviewflowz.biz_surveillance` s USING (cid)
  WHERE CAST(r.created_at AS DATE) < DATE "2026-08-04"
    AND h.n_avis >= 10
)

SELECT
  cid, region, taille, secteur, enseigne_signalee, taux_reponse, age, repondu,
  note, local_guide, photo_jointe, texte, photos_auteur, avis_auteur,
  COUNT(*)                                                     AS n,
  COUNT(jour_de_suppression)                                   AS k,
  IF(COUNT(jour_de_suppression) > 0, ANY_VALUE(enseigne), NULL) AS enseigne,
  STRING_AGG(DISTINCT CAST(jour_de_suppression AS STRING), ", "
             ORDER BY CAST(jour_de_suppression AS STRING))     AS jours_de_suppression
FROM avis
GROUP BY cid, region, taille, secteur, enseigne_signalee, taux_reponse, age, repondu,
         note, local_guide, photo_jointe, texte, photos_auteur, avis_auteur
