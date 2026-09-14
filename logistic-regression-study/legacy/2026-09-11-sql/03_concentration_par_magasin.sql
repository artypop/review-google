-- ============================================================================
-- Repérer les magasins (cid) qui concentrent le plus de suppressions
-- corrigées, pour vérifier qu'on n'a pas quelques fiches qui écrasent tout
-- dans la future régression logistique.
-- ============================================================================

-- Classement brut : les cid les plus touchés en nombre de suppressions.
SELECT
  cid,
  COUNT(*)                                    AS avis_total,
  COUNTIF(deleted)                            AS avis_supprimes,
  ROUND(100 * COUNTIF(deleted) / COUNT(*), 1) AS pct_supprimes
FROM `client-divers`.reviewflowz.avis_deleted_panel
GROUP BY cid
HAVING COUNTIF(deleted) > 0
ORDER BY avis_supprimes DESC
LIMIT 50;

-- Variante resserrée sur les cas vraiment concentrés : au moins 10 avis
-- supprimés, OU plus de 5 % des avis de la fiche supprimés. Un magasin peut
-- être un cas à part pour l'une ou l'autre de ces deux raisons.
SELECT
  cid,
  COUNT(*)                                    AS avis_total,
  COUNTIF(deleted)                            AS avis_supprimes,
  ROUND(100 * COUNTIF(deleted) / COUNT(*), 1) AS pct_supprimes
FROM `client-divers`.reviewflowz.avis_deleted_panel
GROUP BY cid
HAVING COUNTIF(deleted) >= 10
    OR (COUNT(*) > 0 AND COUNTIF(deleted) / COUNT(*) > 0.05)
ORDER BY avis_supprimes DESC;
