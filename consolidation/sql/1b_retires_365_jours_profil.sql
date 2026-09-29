-- ============================================================================
-- 1b. Les 555 suppressions retirées par la règle des 365 jours : leur profil
--
-- Mêmes avis que `verif_avis_modifies_plus_d_un_an.sql`, sans texte ni auteur :
-- seulement des comptes, par dimension.
--   dimension    ce qu'on compte (mois de modification, jour de disparition…)
--   valeur       la modalité
--   avis         avis supprimés dans cette modalité
-- ============================================================================

WITH classement AS (
  SELECT
    r.*,
    COUNT(*) OVER (PARTITION BY r.review_id) AS nb_lignes,
    ROW_NUMBER() OVER (
      PARTITION BY r.review_id
      ORDER BY r.updated_at DESC, r.last_seen_at DESC, r.id DESC
    ) AS rang
  FROM `client-divers.reviewflowz.reviews` r
),

retires AS (
  SELECT c.*, b.country, b.industry, s.cid IS NOT NULL AS enseigne_signalee
  FROM classement c
  LEFT JOIN `client-divers.reviewflowz.businesses` b USING (cid)
  LEFT JOIN `client-divers.reviewflowz.biz_surveillance` s USING (cid)
  WHERE c.rang = 1
    AND (c.nb_lignes = 1 OR c.is_update = TRUE)
    AND TIMESTAMP_DIFF(c.updated_at, c.created_at, DAY) > 365
    AND c.deleted_detected_at IS NOT NULL
)

SELECT "1. chaîne signalée (biz_surveillance)" AS dimension, CAST(enseigne_signalee AS STRING) AS valeur, COUNT(*) AS avis FROM retires GROUP BY 2
UNION ALL SELECT "2. pays", country, COUNT(*) FROM retires GROUP BY 2
UNION ALL SELECT "3. secteur", industry, COUNT(*) FROM retires GROUP BY 2
UNION ALL SELECT "4. note", CAST(star AS STRING), COUNT(*) FROM retires GROUP BY 2
UNION ALL SELECT "5. année de publication", CAST(EXTRACT(YEAR FROM created_at) AS STRING), COUNT(*) FROM retires GROUP BY 2
UNION ALL SELECT "6. mois de la dernière modification", FORMAT_DATE("%Y-%m", DATE(updated_at)), COUNT(*) FROM retires GROUP BY 2
UNION ALL SELECT "7. modifié pendant le suivi", CAST(is_update AS STRING), COUNT(*) FROM retires GROUP BY 2
UNION ALL SELECT "8. jour de disparition", CAST(DATE(deleted_detected_at) AS STRING), COUNT(*) FROM retires GROUP BY 2
UNION ALL SELECT "9. jours entre modification et disparition",
  CASE WHEN DATE_DIFF(DATE(deleted_detected_at), DATE(updated_at), DAY) <= 7 THEN "a. 7 jours ou moins"
       WHEN DATE_DIFF(DATE(deleted_detected_at), DATE(updated_at), DAY) <= 30 THEN "b. 8 à 30 jours"
       WHEN DATE_DIFF(DATE(deleted_detected_at), DATE(updated_at), DAY) <= 90 THEN "c. 31 à 90 jours"
       ELSE "d. plus de 90 jours" END, COUNT(*) FROM retires GROUP BY 2
UNION ALL SELECT "10. réponse du propriétaire", CAST(reply_date IS NOT NULL AS STRING), COUNT(*) FROM retires GROUP BY 2
ORDER BY dimension, valeur
