-- ==============================================================================
-- File: sql/05_panel_final-v3.sql
-- Table: client-divers.reviewflowz.avis_panel_final
-- Description: Assemblage du panel d'observation et des caracteristiques,
--              pret pour la regression logistique.
--
-- A executer APRES 04_avis_features-v3.sql.
--
-- Ce qui change par rapport a la v2
-- --------------------------------
-- La jointure `JOIN reviews r ON p.review_id = r.review_id AND NOT r.is_update`
-- supposait qu'un avis n'a qu'une ligne non-update. C'est faux pour 617 avis :
-- ceux qui ont disparu puis sont revenus ont un enregistrement de disparition
-- et un enregistrement de retour.
--
-- Comme avis_features avait le meme defaut en v2, chaque avis concerne sortait
-- multiplie par 4 a chaque vague. Mesure sur la table produite par la v2 :
--   63 166 588 lignes pour 63 148 730 couples (avis, vague) distincts,
--   soit 17 858 lignes en trop ;
--   5 503 lignes a deleted = 1 pour seulement 4 737 avis reellement supprimes,
--   soit 766 suppressions comptees deux fois, toutes sur les avis ressuscites.
--
-- Correction ici : la table reviews est ramenee a une ligne par avis avant la
-- jointure, avec les memes agregats que le bloc `canon` de
-- 01_build_avis_deleted_panel.sql (MIN sur created_at et first_seen_at), pour
-- que les deux etapes datent les avis de la meme facon.
--
-- Controle a passer apres execution : les deux comptes doivent etre egaux.
--   SELECT COUNT(*), COUNT(DISTINCT CONCAT(review_id,'|',CAST(wave AS STRING)))
--   FROM `client-divers.reviewflowz.avis_panel_final`;
-- Et le nombre de lignes supprimees doit tomber sur 4 737 :
--   SELECT COUNT(*) FROM `client-divers.reviewflowz.avis_panel_final`
--   WHERE deleted = 1;
-- ==============================================================================

CREATE OR REPLACE TABLE `client-divers.reviewflowz.avis_panel_final` AS

-- Une ligne par avis, datee comme dans 01.
WITH reviews_canon AS (
  SELECT
    review_id,
    MIN(created_at)    AS created_at,
    MIN(first_seen_at) AS first_seen_at
  FROM `client-divers`.reviewflowz.reviews
  WHERE NOT is_update
  GROUP BY review_id
)

SELECT
  p.review_id,
  p.cid,
  p.wave,
  -- 0 = encore en ligne a la vague w, 1 = disparu pour de bon a la vague w
  CAST(p.deleted AS INT64) AS deleted,

  -- Facteurs de temps, connus au debut de la vague w donc utilisables en entree
  TIMESTAMP_DIFF(w.started_at, r.created_at, DAY)    AS age_days,
  TIMESTAMP_DIFF(w.started_at, r.first_seen_at, DAY) AS jours_sous_surveillance,

  -- Caracteristiques de l'avis, de l'auteur et du contexte
  f.* EXCEPT(review_id, cid)

FROM `client-divers.reviewflowz.avis_deleted_panel` p
JOIN `client-divers`.reviewflowz.waves w
  ON p.wave = w.wave
JOIN reviews_canon r
  ON p.review_id = r.review_id
JOIN `client-divers`.reviewflowz.avis_features f
  ON p.review_id = f.review_id;
