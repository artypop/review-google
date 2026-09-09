-- ==============================================================================
-- File: sql/05_panel_final.sql
-- Table: client-divers.reviewflowz.avis_panel_final
-- Description: Assemblage final du panel d'observation (vagues/surveillance) 
--              et des caractéristiques individuelles et contextuelles (features)
--              prêts pour la régression logistique sous statsmodels.
-- ==============================================================================

CREATE OR REPLACE TABLE `client-divers.reviewflowz.avis_panel_final` AS

SELECT
  p.review_id,
  p.cid,
  p.wave,
  -- Target binaire (0 = vivant lors de la vague w, 1 = supprimé lors de la vague w)
  CAST(p.deleted AS INT64) AS deleted,

  -- Facteurs de temps dynamiques (calculés au début de la vague w)
  TIMESTAMP_DIFF(w.started_at, r.created_at, DAY) AS age_days,
  TIMESTAMP_DIFF(w.started_at, r.first_seen_at, DAY) AS jours_sous_surveillance,

  -- Caractéristiques de l'avis, de l'auteur et du contexte
  f.* EXCEPT(review_id, cid)

FROM `client-divers.reviewflowz.avis_deleted_panel` p
JOIN `client-divers`.reviewflowz.waves w 
  ON p.wave = w.wave
JOIN `client-divers`.reviewflowz.reviews r 
  ON p.review_id = r.review_id AND NOT r.is_update
JOIN `client-divers`.reviewflowz.avis_features f 
  ON p.review_id = f.review_id;
