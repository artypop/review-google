-- ============================================================================
-- 2.3. Taux de suppression par caractéristique — panel 03B
--
-- Table : `reviews_panel_features_03B`, les 35 751 avis publiés du 4 au
-- 17 août 2026 (J-7 à J+6), dont 1 355 supprimés, constatés du 12 au 24 août.
-- Un calcul direct : pour chaque modalité, combien d'avis, combien supprimés.
-- Lecture d'une ligne : « aux États-Unis, sur 10 000 avis 1 étoile du panel,
-- N ont disparu ».
--
-- `fiches_touchees` : nombre de fiches différentes qui portent les avis
-- supprimés de la ligne. 30 suppressions sur 3 fiches ne se lisent pas comme
-- 30 suppressions sur 30 fiches.
--
-- Le script Python fait un CSV par caractéristique, régions en colonnes.
-- ============================================================================

WITH avis AS (
  SELECT
    f.*,
    s.cid IS NOT NULL AS enseigne_signalee
  FROM `client-divers.reviewflowz.reviews_panel_features_03B` f
  LEFT JOIN `client-divers.reviewflowz.biz_surveillance` s USING (cid)
),

-- Chaque avis reçoit sa modalité pour chacune des 11 caractéristiques.
-- `ordre` sert seulement à trier les lignes du CSV.
modalites AS (
  SELECT a.cid, a.supprime, a.region, a.enseigne_signalee, m.*
  FROM avis a, UNNEST([
    STRUCT("note" AS caracteristique, 6 - a.star AS ordre,
           CONCAT(CAST(a.star AS STRING), " étoile(s)") AS modalite),

    -- Paliers décidés le 2026-09-29 : sans niveau / 1 à 4 / 5 et plus, calculés
    -- sur le niveau brut. La colonne `palier_local_guide` de la table garde
    -- l'ancien découpage 1 à 3 / 4 et plus.
    STRUCT("local_guide",
           CASE WHEN a.local_guide_level IS NULL THEN 1 WHEN a.local_guide_level <= 4 THEN 2 ELSE 3 END,
           CASE WHEN a.local_guide_level IS NULL THEN "sans niveau"
                WHEN a.local_guide_level <= 4 THEN "niveau 1 à 4" ELSE "niveau 5 et plus" END),

    STRUCT("photo_jointe",
           IF(a.has_photo, 1, 2),
           IF(a.has_photo, "avec photo", "sans photo")),

    STRUCT("texte",
           IF(a.has_text, 1, 2),
           IF(a.has_text, "avec texte", "sans texte")),

    STRUCT("longueur_texte",
           CASE WHEN NOT a.has_text THEN 1 WHEN a.text_chars <= 50 THEN 2
                WHEN a.text_chars <= 200 THEN 3 ELSE 4 END,
           CASE WHEN NOT a.has_text THEN "sans texte" WHEN a.text_chars <= 50 THEN "1 à 50 caractères"
                WHEN a.text_chars <= 200 THEN "51 à 200 caractères" ELSE "plus de 200 caractères" END),

    STRUCT("photos_auteur",
           CASE WHEN a.reviewer_photo_count = 0 THEN 1 WHEN a.reviewer_photo_count <= 5 THEN 2
                WHEN a.reviewer_photo_count <= 20 THEN 3 WHEN a.reviewer_photo_count <= 100 THEN 4 ELSE 5 END,
           CASE WHEN a.reviewer_photo_count = 0 THEN "0 photo" WHEN a.reviewer_photo_count <= 5 THEN "1 à 5"
                WHEN a.reviewer_photo_count <= 20 THEN "6 à 20" WHEN a.reviewer_photo_count <= 100 THEN "21 à 100"
                ELSE "plus de 100" END),

    STRUCT("avis_auteur",
           CASE WHEN a.reviewer_review_count IS NULL THEN 6 WHEN a.reviewer_review_count <= 1 THEN 1
                WHEN a.reviewer_review_count <= 5 THEN 2 WHEN a.reviewer_review_count <= 20 THEN 3
                WHEN a.reviewer_review_count <= 100 THEN 4 ELSE 5 END,
           CASE WHEN a.reviewer_review_count IS NULL THEN "inconnu" WHEN a.reviewer_review_count <= 1 THEN "1 avis"
                WHEN a.reviewer_review_count <= 5 THEN "2 à 5" WHEN a.reviewer_review_count <= 20 THEN "6 à 20"
                WHEN a.reviewer_review_count <= 100 THEN "21 à 100" ELSE "plus de 100" END),

    STRUCT("secteur",
           0,
           CASE a.industry
             WHEN "automotive"       THEN "Automobile"
             WHEN "home_services"    THEN "Services à domicile"
             WHEN "healthcare"       THEN "Santé"
             WHEN "wellness_fitness" THEN "Sport et bien-être"
             WHEN "food_beverage"    THEN "Restauration"
             WHEN "travel"           THEN "Voyage"
             WHEN "hospitality"      THEN "Hôtellerie"
             ELSE a.industry END),

    STRUCT("taille",
           CASE a.bucket WHEN "mono" THEN 1 WHEN "small" THEN 2 ELSE 3 END,
           CASE a.bucket WHEN "mono" THEN "mono (1 établissement)"
                WHEN "small" THEN "small (4 à 10)" ELSE "large (20 à 50)" END),

    -- Part des avis de la fiche (publiés du 11/08/2025 au 03/08/2026) qui
    -- avaient une réponse avant le 11 août. Vide sous 10 avis d'historique.
    STRUCT("habitude_reponse_fiche",
           CASE WHEN a.taux_reponse_fiche_avant_vague1 IS NULL THEN 4
                WHEN a.taux_reponse_fiche_avant_vague1 <= 0.25 THEN 1
                WHEN a.taux_reponse_fiche_avant_vague1 <= 0.75 THEN 2 ELSE 3 END,
           CASE WHEN a.taux_reponse_fiche_avant_vague1 IS NULL THEN "moins de 10 avis d'historique"
                WHEN a.taux_reponse_fiche_avant_vague1 <= 0.25 THEN "répond à 25 % ou moins"
                WHEN a.taux_reponse_fiche_avant_vague1 <= 0.75 THEN "répond à 25-75 %"
                ELSE "répond à plus de 75 %" END),

    -- Avis publiés sur la même fiche le jour de cet avis, lui compris, sur
    -- toute la base. Seuils de Claude, 2026-09-29. Une grosse fiche reçoit
    -- naturellement plus d'avis par jour : cette colonne suit aussi la taille.
    STRUCT("avis_sur_la_fiche_le_meme_jour",
           CASE WHEN a.n_avis_meme_jour_fiche <= 1 THEN 1 WHEN a.n_avis_meme_jour_fiche <= 4 THEN 2
                WHEN a.n_avis_meme_jour_fiche <= 9 THEN 3 ELSE 4 END,
           CASE WHEN a.n_avis_meme_jour_fiche <= 1 THEN "seul avis du jour"
                WHEN a.n_avis_meme_jour_fiche <= 4 THEN "2 à 4 avis ce jour-là"
                WHEN a.n_avis_meme_jour_fiche <= 9 THEN "5 à 9"
                ELSE "10 et plus" END)
  ]) AS m
)

SELECT
  caracteristique,
  ordre,
  modalite,
  perimetre,
  region_vue                                        AS region,
  COUNT(*)                                          AS avis,
  COUNTIF(supprime)                                 AS suppressions,
  COUNT(DISTINCT IF(supprime, cid, NULL))           AS fiches_touchees,
  ROUND(10000 * COUNTIF(supprime) / COUNT(*), 0)    AS pour_10000
FROM modalites,
     UNNEST(["tous", "sans_enseignes"]) AS perimetre,
     UNNEST([region, "ensemble"])       AS region_vue
WHERE perimetre = "tous" OR NOT enseigne_signalee
GROUP BY caracteristique, ordre, modalite, perimetre, region
