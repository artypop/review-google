SELECT
  COUNT(DISTINCT review_id) AS avis_dans_le_panel,
  COUNTIF(deleted) AS lignes_marquees_supprimees,
  (SELECT COUNT(DISTINCT review_id) FROM `client-divers.reviewflowz.avis_deleted_panel` WHERE deleted) AS avis_distincts_supprimes
FROM `client-divers.reviewflowz.avis_deleted_panel`;²


SELECT
  cid,
  COUNT(*)                    AS avis_total,
  COUNTIF(deleted)             AS avis_supprimes,
  ROUND(100 * COUNTIF(deleted) / COUNT(*), 1) AS pct_supprimes
FROM `client-divers.reviewflowz.avis_deleted_panel`
GROUP BY cid
HAVING COUNTIF(deleted) >= 10 OR (COUNT(*) > 0 AND COUNTIF(deleted) / COUNT(*) > 0.05)
ORDER BY avis_supprimes DESC;

SELECT * FROM client-divers.reviewflowz.reviews WHERE NOT is_update AND  deleted_detected_at IS NOT NULL AND cid="3163466139043001754"

SELECT * FROM client-divers.reviewflowz.reviews WHERE review_id = "ChdDSUhNMG9nS0VJQ0FnSURtNXJmdzdBRRAB"

SELECT *
FROM `client-divers`.reviewflowz.avis_deleted_panel where jours_en_ligne_avant_suppression > 0