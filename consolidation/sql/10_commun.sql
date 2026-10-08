-- Bloc commun aux requêtes 10_*.sql, inséré en tête par 10_fiches_attaquees.py.
-- Les requêtes qui ajoutent leurs propres étapes les ouvrent par une virgule.
--
-- Deux bases :
--   axel      la table brute `reviews`, sans les avis modifiés (lignes
--             `is_update`), comme Axel : toute disparition compte, ratés d'un
--             jour et bugs d'enregistrement compris (5 230 disparitions)
--   nettoyee  `reviews_doublons_cleaned_all`, la base complète de la
--             consolidation, avis modifiés compris (4 590 suppressions).
--             Décision de Romain du 2026-10-08 : on garde notre nettoyage, même
--             si des fiches divergent de celles d'Axel.
-- Catégorie de fiche, calculée dans chaque base : nombre de suppressions en
-- 14 jours, 0 / 1 à 10 / 11 et plus (seuil d'Axel).
WITH avis AS (
  SELECT "axel" AS base, cid, star, DATE(created_at) AS publication,
         DATE(deleted_detected_at) AS suppression
  FROM `client-divers.reviewflowz.reviews`
  WHERE NOT IFNULL(is_update, FALSE)
  UNION ALL
  SELECT "nettoyee", cid, star, DATE(created_at), DATE(deleted_detected_at)
  FROM `client-divers.reviewflowz.reviews_doublons_cleaned_all`
),
fiche AS (
  SELECT base, cid, COUNTIF(suppression IS NOT NULL) AS suppressions_fiche
  FROM avis GROUP BY base, cid
),
avis_cat AS (
  SELECT a.*, f.suppressions_fiche,
         CASE WHEN f.suppressions_fiche > 10 THEN "11 et plus"
              WHEN f.suppressions_fiche >= 1 THEN "1 à 10"
              ELSE "aucune" END AS categorie
  FROM avis a JOIN fiche f USING (base, cid)
)
