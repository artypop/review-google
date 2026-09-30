-- ============================================================================
-- 0b. Les avis que le corpus d'Axel ajoute à 03B : leur profil
--
-- Ce sont les avis de `corpus_axel` absents de 03B : supprimés pendant le
-- suivi (12 au 24 août 2026) et publiés avant le 4 août ou après le 17 août.
-- Seulement des comptes, par dimension.
--   dimension    ce qu'on compte
--   valeur       la modalité
--   avis         avis ajoutés dans cette modalité, tous supprimés
--
-- La « fenêtre de l'habitude de réponse » : les avis publiés du 2025-08-11 au
-- 2026-08-03 servent à calculer la part des avis auxquels une fiche répond
-- (`1_features_axel.bqsql`, bloc `habitude_reponse_fiche`).
-- ============================================================================

WITH ajoutes AS (
  SELECT
    a.star,
    DATE(a.created_at)                        AS publie_le,
    DATE(a.deleted_detected_at)               AS disparu_le,
    IF(b.country = "US", "US", "Europe")      AS region,
    b.industry,
    s.cid IS NOT NULL                         AS enseigne_signalee
  FROM `client-divers.reviewflowz.corpus_axel` a
  LEFT JOIN `client-divers.reviewflowz.businesses` b USING (cid)
  LEFT JOIN `client-divers.reviewflowz.biz_surveillance` s USING (cid)
  WHERE a.review_id NOT IN (
    SELECT review_id FROM `client-divers.reviewflowz.03B_reviews_panel_filtered_08_04_to_08_26`)
)

SELECT "0. total" AS dimension, "avis ajoutés" AS valeur, COUNT(*) AS avis FROM ajoutes
UNION ALL
SELECT "1. période de publication",
  CASE WHEN publie_le < DATE "2025-08-11" THEN "a. avant le 11 août 2025"
       WHEN publie_le <= DATE "2026-08-03" THEN "b. du 11 août 2025 au 3 août 2026 (fenêtre de l'habitude de réponse)"
       ELSE "c. du 18 au 24 août 2026" END, COUNT(*) FROM ajoutes GROUP BY 2
UNION ALL
SELECT "2. âge de l'avis à sa disparition",
  CASE WHEN DATE_DIFF(disparu_le, publie_le, DAY) <= 13 THEN "a. 13 jours ou moins"
       WHEN DATE_DIFF(disparu_le, publie_le, DAY) <= 90 THEN "b. 14 à 90 jours"
       WHEN DATE_DIFF(disparu_le, publie_le, DAY) <= 365 THEN "c. 91 à 365 jours"
       ELSE "d. plus d'un an" END, COUNT(*) FROM ajoutes GROUP BY 2
UNION ALL
SELECT "3. année de publication", CAST(EXTRACT(YEAR FROM publie_le) AS STRING), COUNT(*) FROM ajoutes GROUP BY 2
UNION ALL
SELECT "4. note", CAST(star AS STRING), COUNT(*) FROM ajoutes GROUP BY 2
UNION ALL
SELECT "5. région", region, COUNT(*) FROM ajoutes GROUP BY 2
UNION ALL
SELECT "6. enseigne signalée (biz_surveillance)", CAST(enseigne_signalee AS STRING), COUNT(*) FROM ajoutes GROUP BY 2
UNION ALL
SELECT "7. secteur", industry, COUNT(*) FROM ajoutes GROUP BY 2
UNION ALL
SELECT "8. jour de disparition", CAST(disparu_le AS STRING), COUNT(*) FROM ajoutes GROUP BY 2
ORDER BY dimension, valeur
