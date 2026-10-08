-- ============================================================================
-- Avis du jour face à la moyenne des 7 jours précédents, panel 03D
--
-- Demande d'Axel (2026-10-08) : un avis publié un jour où la fiche reçoit plus
-- d'avis que sa moyenne des 7 jours précédents disparaît-il plus souvent ?
--
-- Panel : `reviews_panel_features_03D`, avis publiés du 6 au 17 août 2026.
-- Historique : `reviews_doublons_cleaned_all`, suppressions comprises.
--
--   n_avis_ce_jour     avis de la fiche le jour de publication, l'avis compris
--   n_avis_7j_avant    avis de la fiche du jour J-7 au jour J-1
--   moyenne_7j         n_avis_7j_avant / 7
--   tranche_7j         n_avis_ce_jour rapporté à moyenne_7j
--
-- Un avis supprimé avant le 11 août n'est dans aucune table : les 7 jours
-- précédents d'un avis publié avant le 18 août sont un peu sous-comptés.
-- Une ligne par avis, avec les colonnes du modèle 03D.
-- ============================================================================

WITH fiche_jour AS (
  SELECT cid, CAST(created_at AS DATE) AS jour, COUNT(*) AS n_avis
  FROM `client-divers.reviewflowz.reviews_doublons_cleaned_all`
  GROUP BY cid, jour
),

avis AS (
  SELECT
    f.*,
    CAST(f.created_at AS DATE) AS jour_publication
  FROM `client-divers.reviewflowz.reviews_panel_features_03D` f
),

fenetre AS (
  SELECT
    a.review_id,
    COALESCE(SUM(fj.n_avis), 0) AS n_avis_7j_avant
  FROM avis a
  LEFT JOIN fiche_jour fj
    ON fj.cid = a.cid
   AND fj.jour BETWEEN DATE_SUB(a.jour_publication, INTERVAL 7 DAY)
                   AND DATE_SUB(a.jour_publication, INTERVAL 1 DAY)
  GROUP BY a.review_id
)

SELECT
  a.review_id, a.cid, a.supprime, a.star, a.has_photo, a.text_chars, a.palier_local_guide,
  a.reviewer_photo_count, a.reviewer_review_count, a.a_repondu, a.taux_reponse_fiche,
  a.secteur, a.bucket, a.region, a.enseigne_signalee,
  a.n_avis_meme_jour_fiche                     AS n_avis_ce_jour,
  w.n_avis_7j_avant,
  ROUND(w.n_avis_7j_avant / 7, 3)              AS moyenne_7j,
  CASE
    WHEN w.n_avis_7j_avant = 0                                       THEN "aucun avis les 7 jours avant"
    WHEN a.n_avis_meme_jour_fiche <= w.n_avis_7j_avant / 7           THEN "au plus la moyenne"
    WHEN a.n_avis_meme_jour_fiche <= 2 * w.n_avis_7j_avant / 7       THEN "1 à 2 fois la moyenne"
    WHEN a.n_avis_meme_jour_fiche <= 3 * w.n_avis_7j_avant / 7       THEN "2 à 3 fois la moyenne"
    ELSE                                                                  "plus de 3 fois la moyenne"
  END                                          AS tranche_7j
FROM avis a
JOIN fenetre w USING (review_id)
