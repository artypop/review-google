-- ============================================================================
-- 5. Une ligne par avis et par jour, pour mesurer l'effet de la réponse
--
-- Table : `reviews_panel_features_03B` (avis publiés du 4 au 17 août 2026),
-- fiches dont l'habitude de réponse est connue (au moins 10 avis l'année
-- précédente).
--
-- Une ligne = un avis, un jour où il pouvait être vu disparaître : du
-- lendemain de sa première observation jusqu'à sa disparition ou au 24 août.
-- Un avis publié le 4 août, vu pour la première fois le 11, n'entre qu'à son
-- 8e jour. Aucun jalon : un avis supprimé au 3e jour est dans le calcul.
--
--   y                   1 si l'avis disparaît ce jour-là
--   age                 âge de l'avis ce jour-là, en jours
--   delai_reponse_j     jours civils entre la publication et la réponse
--   reponse_la_veille   le propriétaire avait déjà répondu la veille
-- ============================================================================

WITH premiere_vue AS (
  SELECT review_id, DATE(MIN(first_seen_at)) AS premier_jour_vu
  FROM `client-divers.reviewflowz.reviews`
  GROUP BY review_id
),

avis AS (
  SELECT
    f.*,
    b.name AS enseigne,
    s.cid IS NOT NULL AS enseigne_signalee,
    GREATEST(DATE_DIFF(pv.premier_jour_vu, f.created_at_day, DAY), 0) AS age_entree,
    IF(f.supprime, f.age_a_la_suppression_j,
       DATE_DIFF(DATE "2026-08-24", f.created_at_day, DAY)) AS age_sortie
  FROM `client-divers.reviewflowz.reviews_panel_features_03B` f
  JOIN premiere_vue pv USING (review_id)
  LEFT JOIN `client-divers.reviewflowz.businesses` b USING (cid)
  LEFT JOIN `client-divers.reviewflowz.biz_surveillance` s USING (cid)
  WHERE f.taux_reponse_fiche_avant_vague1 IS NOT NULL
)

SELECT
  a.review_id,
  a.cid,
  a.enseigne,
  a.bucket                                              AS taille_detail,
  a.region,
  a.enseigne_signalee,
  a.star,
  a.taux_reponse_fiche_avant_vague1                     AS taux_reponse,
  a.delai_reponse_j,
  age,
  DATE_ADD(a.created_at_day, INTERVAL age DAY)          AS jour,
  IF(a.supprime AND age = a.age_sortie, 1, 0)           AS y,
  a.delai_reponse_j IS NOT NULL AND a.delai_reponse_j <= age - 1 AS reponse_la_veille
FROM avis a, UNNEST(GENERATE_ARRAY(a.age_entree + 1, a.age_sortie)) AS age
