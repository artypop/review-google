-- ============================================================================
-- 4a. Une ligne par fiche du panel 03B
--
-- Table : `reviews_panel_features_03B` (avis publiés du 4 au 17 août 2026).
-- Seules les fiches qui ont au moins 5 avis dans le panel : en dessous,
-- « touchée ou non » tient du hasard (seuil de Claude, 2026-09-29).
--
--   avis           avis de la fiche publiés du 4 au 17 août
--   suppressions   parmi eux, ceux qui ont disparu (12 au 24 août)
--   taux_reponse   part de ses avis de l'année précédente qui avaient une
--                  réponse avant le 11 août (vide sous 10 avis d'historique)
--   rythme         avis par jour, en moyenne, sur les 365 jours avant le 11 août
--   premiere_suppression, derniere_suppression : dates, pour retrouver la fiche
-- ============================================================================

SELECT
  f.cid,
  ANY_VALUE(b.name)                              AS enseigne,
  ANY_VALUE(b.country)                           AS pays,
  ANY_VALUE(f.industry)                          AS secteur,
  ANY_VALUE(f.bucket)                            AS taille,
  ANY_VALUE(f.region)                            AS region,
  LOGICAL_OR(s.cid IS NOT NULL)                  AS enseigne_signalee,
  COUNT(*)                                       AS avis,
  COUNTIF(f.supprime)                            AS suppressions,
  ANY_VALUE(f.taux_reponse_fiche_avant_vague1)   AS taux_reponse,
  ANY_VALUE(f.rythme_fiche_avant_vague1)         AS rythme,
  MIN(IF(f.supprime, DATE_ADD(f.created_at_day, INTERVAL f.age_a_la_suppression_j DAY), NULL))
                                                 AS premiere_suppression,
  MAX(IF(f.supprime, DATE_ADD(f.created_at_day, INTERVAL f.age_a_la_suppression_j DAY), NULL))
                                                 AS derniere_suppression
FROM `client-divers.reviewflowz.reviews_panel_features_03B` f
LEFT JOIN `client-divers.reviewflowz.businesses` b USING (cid)
LEFT JOIN `client-divers.reviewflowz.biz_surveillance` s USING (cid)
GROUP BY f.cid
HAVING COUNT(*) >= 5
