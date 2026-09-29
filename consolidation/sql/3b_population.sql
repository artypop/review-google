-- ============================================================================
-- 3b. Les avis de la régression, un par ligne
--
-- Population : étape 5 de `3_population.sql`. Environ 17 000 lignes, sans
-- texte ni auteur.
--
--   delai        jours civils entre la publication et la réponse du
--                propriétaire, lus au jalon du 2e jour :
--                « jour même », « 1 jour », « 2 jours », ou « pas de réponse
--                au 2e jour » (réponse plus tardive, ou jamais)
--   habitude     part des avis de la fiche, publiés du 11/08/2025 au
--                03/08/2026, qui avaient une réponse avant le 11 août :
--                « plus de 75 % » ou « 75 % ou moins »
--   taille       « mono + small » ou « large »
--   taille_detail « mono », « small » ou « large », pour les passages de contrôle
--   supprime_3_8 l'avis disparaît du 3e au 8e jour
-- ============================================================================

SELECT
  f.cid,
  s.cid IS NOT NULL                                    AS enseigne_signalee,
  IF(f.bucket = "large", "large", "mono + small")      AS taille,
  f.bucket                                             AS taille_detail,
  IF(f.taux_reponse_fiche_avant_vague1 > 0.75,
     "plus de 75 %", "75 % ou moins")                  AS habitude,
  CASE WHEN f.delai_reponse_j <= 0 THEN "jour même"
       WHEN f.delai_reponse_j = 1  THEN "1 jour"
       WHEN f.delai_reponse_j = 2  THEN "2 jours"
       ELSE "pas de réponse au 2e jour" END            AS delai,
  f.star,
  f.region,
  f.supprime AND f.age_a_la_suppression_j BETWEEN 3 AND 8 AS supprime_3_8
FROM `client-divers.reviewflowz.reviews_panel_features_03B` f
LEFT JOIN `client-divers.reviewflowz.biz_surveillance` s USING (cid)
WHERE f.age_a_la_premiere_observation_j <= 1
  AND DATE_DIFF(DATE "2026-08-24", f.created_at_day, DAY) >= 8
  AND NOT (f.supprime AND f.age_a_la_suppression_j <= 2)
  AND f.taux_reponse_fiche_avant_vague1 IS NOT NULL
