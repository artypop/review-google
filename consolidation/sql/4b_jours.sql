-- ============================================================================
-- 4b. Les avis d'une fiche, le jour où elle en perd au moins un
--
-- Table : `reviews_panel_features_03B` (avis publiés du 4 au 17 août 2026).
--
-- Une ligne = un avis, un jour donné, où il pouvait être vu disparaître : du
-- lendemain de sa première observation jusqu'à sa disparition ou au 24 août.
-- On ne garde que les journées où la fiche a perdu au moins un avis ET en a
-- gardé au moins un : ce sont les seules où l'on peut comparer, dans la même
-- fiche, le même jour, les avis qui tombent et ceux qui restent.
--
-- `strate` = fiche + jour. `y` = 1 si l'avis disparaît ce jour-là.
-- `reponse_la_veille` : le propriétaire avait déjà répondu la veille.
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
),

jours AS (
  SELECT
    a.*,
    age,
    DATE_ADD(a.created_at_day, INTERVAL age DAY) AS jour,
    IF(a.supprime AND age = a.age_sortie, 1, 0) AS y
  FROM avis a, UNNEST(GENERATE_ARRAY(a.age_entree + 1, a.age_sortie)) AS age
),

strates AS (
  SELECT cid, jour
  FROM jours
  GROUP BY cid, jour
  HAVING SUM(y) >= 1 AND SUM(y) < COUNT(*)
)

SELECT
  CONCAT(j.cid, "_", CAST(j.jour AS STRING))        AS strate,
  j.review_id,
  j.cid,
  j.enseigne,
  j.region,
  j.enseigne_signalee,
  j.jour,
  j.y,
  j.star,
  j.age,
  j.local_guide_level,
  j.has_photo,
  j.has_text,
  j.text_chars,
  j.reviewer_photo_count,
  j.reviewer_review_count,
  j.delai_reponse_j IS NOT NULL AND j.delai_reponse_j <= j.age - 1 AS reponse_la_veille,
  j.taux_reponse_fiche_avant_vague1                   AS taux_reponse
FROM jours j
JOIN strates USING (cid, jour)
