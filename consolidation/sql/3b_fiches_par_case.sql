-- ============================================================================
-- 3b. Quelles fiches portent les suppressions de chaque case délai × habitude ?
--
-- Même population que `3b_population.sql`. Une ligne par fiche et par case
-- (taille, habitude, délai), seulement pour les fiches qui perdent au moins un
-- avis du 3e au 8e jour dans cette case.
--
-- Sert à retrouver une fiche citée dans `3_reponse_proprietaire.md` : chercher
-- son `cid` dans la console BigQuery, table `reviews_doublons_cleaned`, avis
-- publiés entre `publie_du` et `publie_au`.
-- ============================================================================

WITH avis AS (
  SELECT
    f.cid,
    s.cid IS NOT NULL                                  AS enseigne_signalee,
    IF(f.bucket = "large", "large", "mono + small")    AS taille,
    f.bucket                                           AS taille_detail,
    IF(f.taux_reponse_fiche_avant_vague1 > 0.75,
       "plus de 75 %", "75 % ou moins")                AS habitude,
    CASE WHEN f.delai_reponse_j <= 0 THEN "jour même"
         WHEN f.delai_reponse_j = 1  THEN "1 jour"
         WHEN f.delai_reponse_j = 2  THEN "2 jours"
         ELSE "pas de réponse au 2e jour" END          AS delai,
    f.created_at_day,
    f.supprime AND f.age_a_la_suppression_j BETWEEN 3 AND 8 AS supprime_3_8,
    DATE_ADD(f.created_at_day, INTERVAL f.age_a_la_suppression_j DAY) AS jour_suppression
  FROM `client-divers.reviewflowz.reviews_panel_features_03B` f
  LEFT JOIN `client-divers.reviewflowz.biz_surveillance` s USING (cid)
  WHERE f.age_a_la_premiere_observation_j <= 1
    AND DATE_DIFF(DATE "2026-08-24", f.created_at_day, DAY) >= 8
    AND NOT (f.supprime AND f.age_a_la_suppression_j <= 2)
    AND f.taux_reponse_fiche_avant_vague1 IS NOT NULL
)

SELECT
  a.taille,
  a.taille_detail,
  a.habitude,
  a.delai,
  a.cid,
  b.name                                             AS enseigne,
  b.country                                          AS pays,
  b.industry                                         AS secteur,
  a.enseigne_signalee,
  COUNT(*)                                           AS avis_de_la_case,
  COUNTIF(a.supprime_3_8)                            AS suppressions_3_8,
  MIN(a.created_at_day)                              AS publie_du,
  MAX(a.created_at_day)                              AS publie_au,
  STRING_AGG(DISTINCT IF(a.supprime_3_8, CAST(a.jour_suppression AS STRING), NULL), ", "
             ORDER BY IF(a.supprime_3_8, CAST(a.jour_suppression AS STRING), NULL))
                                                     AS jours_de_suppression
FROM avis a
LEFT JOIN `client-divers.reviewflowz.businesses` b USING (cid)
GROUP BY a.taille, a.taille_detail, a.habitude, a.delai, a.cid, enseigne, pays, secteur,
         a.enseigne_signalee
HAVING suppressions_3_8 > 0
ORDER BY a.taille DESC, a.taille_detail, a.habitude, a.delai, suppressions_3_8 DESC, a.cid
