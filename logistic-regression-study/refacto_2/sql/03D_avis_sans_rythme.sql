-- Les avis du panel 03D dont la fiche n'a reçu aucun avis du 2025-08-06 au
-- 2026-08-05. Leur rythme habituel, qui vaudrait 0, est mis à 0,1 avis par
-- jour dans la table.
SELECT
  f.cid,
  f.created_at,
  f.supprime,
  f.n_avis_meme_jour_fiche,
  f.n_avis_fiche,
  f.region,
  f.secteur,
  (SELECT MAX(CAST(r.created_at AS DATE))
   FROM `client-divers.reviewflowz.reviews_doublons_cleaned_all` r
   WHERE r.cid = f.cid AND CAST(r.created_at AS DATE) < DATE "2026-08-06") AS avis_precedent_le
FROM `client-divers.reviewflowz.reviews_panel_features_03D` f
WHERE f.rythme_fiche_mis_a_0_1
ORDER BY f.cid, f.created_at
