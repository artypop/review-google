-- ============================================================================
-- 1b. Les suppressions que la règle des 365 jours retire, fiche par fiche
--
-- Étape 4 de `1b_entonnoir.sql` : sortent les avis dont la dernière
-- modification tombe plus de 365 jours après la publication. Une ligne par
-- fiche qui perd au moins un avis supprimé à cette étape. Sans texte ni
-- auteur : pour lire les avis eux-mêmes, `verif_avis_modifies_plus_d_un_an.sql`
-- dans la console BigQuery.
-- ============================================================================

WITH classement AS (
  SELECT
    cid, star, created_at, updated_at, deleted_detected_at, is_update,
    COUNT(*) OVER (PARTITION BY review_id) AS nb_lignes,
    ROW_NUMBER() OVER (
      PARTITION BY review_id
      ORDER BY updated_at DESC, last_seen_at DESC, id DESC
    ) AS rang
  FROM `client-divers.reviewflowz.reviews`
),

retires AS (
  SELECT * FROM classement
  WHERE rang = 1
    AND (nb_lignes = 1 OR is_update = TRUE)
    AND TIMESTAMP_DIFF(updated_at, created_at, DAY) > 365
)

SELECT
  r.cid,
  b.name                                                   AS enseigne,
  b.country                                                AS pays,
  b.industry                                               AS secteur,
  b.bucket                                                 AS taille,
  s.cid IS NOT NULL                                        AS enseigne_signalee,
  COUNT(*)                                                 AS avis_retires,
  COUNTIF(r.deleted_detected_at IS NOT NULL)               AS suppressions_retirees,
  COUNTIF(r.deleted_detected_at IS NOT NULL AND r.star = 5) AS dont_5_etoiles,
  COUNTIF(r.deleted_detected_at IS NOT NULL AND r.star = 1) AS dont_1_etoile,
  MIN(IF(r.deleted_detected_at IS NOT NULL, DATE(r.created_at), NULL)) AS supprimes_publies_du,
  MAX(IF(r.deleted_detected_at IS NOT NULL, DATE(r.created_at), NULL)) AS supprimes_publies_au,
  MIN(DATE(r.deleted_detected_at))                         AS disparus_du,
  MAX(DATE(r.deleted_detected_at))                         AS disparus_au
FROM retires r
LEFT JOIN `client-divers.reviewflowz.businesses` b USING (cid)
LEFT JOIN `client-divers.reviewflowz.biz_surveillance` s USING (cid)
GROUP BY r.cid, enseigne, pays, secteur, taille, enseigne_signalee
HAVING suppressions_retirees > 0
ORDER BY suppressions_retirees DESC, r.cid
