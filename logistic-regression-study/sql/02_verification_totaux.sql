-- ============================================================================
-- Vérification après construction de avis_deleted_panel (01_build_avis_deleted_panel.sql).
--
-- Sur les fichiers locaux, la construction équivalente donnait :
--   - avis dans le panel : ~4 875 000 (le total d'avis moins ceux nés à la
--     toute dernière vague, qui n'ont pas de vague suivante pour observer
--     s'ils survivent — c'est normal, pas un bug) ;
--   - avis distincts marqués supprimés après correction : ~4 740.
--
-- Si ces deux nombres s'éloignent beaucoup de ceux obtenus ici, vérifier
-- d'abord que `reviews.parquet` et `waves.parquet` chargés dans BigQuery
-- correspondent bien à l'export utilisé pour ces tests.
-- ============================================================================

SELECT
  COUNT(DISTINCT review_id) AS avis_dans_le_panel,
  COUNTIF(deleted)          AS lignes_marquees_supprimees,
  (SELECT COUNT(DISTINCT review_id)
   FROM `client-divers.reviewflowz.avis_deleted_panel`
   WHERE deleted)           AS avis_distincts_supprimes
FROM `client-divers.reviewflowz.avis_deleted_panel`;
