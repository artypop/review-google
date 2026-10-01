-- ============================================================================
-- Google supprime peu une fois l'avis publié : les avis publiés pendant le suivi
--
-- Base : `reviews_doublons_cleaned_all`, avis publiés (created_at) du 11 au
-- 23 août 2026. Ceux du 24 août, jour du dernier passage, ne sont suivis
-- aucun jour.
--
-- LE CALCUL, JOUR D'ÂGE PAR JOUR D'ÂGE
--   Pour chaque âge, on prend les avis que le robot voyait en ligne la veille,
--   et on compte ceux qui ont disparu ce jour-là, pour 10 000. Les 1er et 2e
--   jours sont regroupés en « 48 h » : le robot passe une fois par jour et voit
--   la plupart des avis pour la première fois à 1 jour d'âge.
--
--   Un avis du 11 août est suivi jusqu'à 13 jours, un avis du 20 août jusqu'à
--   4 : les derniers âges reposent sur moins d'avis.
--
-- Âge d'entrée : premier jour vu dans `reviews`, comme sql/03D_courbe_de_vie.sql.
-- La ligne `jour` = 0 donne le total : avis publiés, avis supprimés.
-- ============================================================================

WITH premiere_vue AS (
  SELECT review_id, DATE(MIN(first_seen_at)) AS premier_jour_vu
  FROM `client-divers.reviewflowz.reviews`
  GROUP BY review_id
),

avis AS (
  SELECT
    r.review_id,
    r.cid,
    s.cid IS NOT NULL AS enseigne_signalee,
    r.deleted_detected_at IS NOT NULL AS supprime,
    GREATEST(DATE_DIFF(pv.premier_jour_vu, DATE(r.created_at), DAY), 0) AS age_entree,
    DATE_DIFF(COALESCE(DATE(r.deleted_detected_at), DATE "2026-08-24"),
              DATE(r.created_at), DAY) AS age_sortie
  FROM `client-divers.reviewflowz.reviews_doublons_cleaned_all` r
  JOIN premiere_vue pv USING (review_id)
  LEFT JOIN `client-divers.reviewflowz.biz_surveillance` s USING (cid)
  WHERE DATE(r.created_at) BETWEEN DATE "2026-08-11" AND DATE "2026-08-23"
),

-- Une ligne par avis et par âge où il pouvait être vu disparaître ; les âges
-- 1 et 2 sont rangés ensemble sous 2.
jours AS (
  SELECT
    a.review_id,
    a.cid,
    a.enseigne_signalee,
    GREATEST(age, 2) AS jour,
    a.supprime AND age = a.age_sortie AS disparu_ce_jour
  FROM avis a, UNNEST(GENERATE_ARRAY(a.age_entree + 1, a.age_sortie)) AS age
),

par_jour AS (
  SELECT
    perimetre,
    jour,
    COUNT(DISTINCT review_id)                       AS en_ligne_la_veille,
    COUNTIF(disparu_ce_jour)                        AS suppressions,
    COUNT(DISTINCT IF(disparu_ce_jour, cid, NULL))  AS fiches_touchees
  FROM jours, UNNEST(["tous", "sans_enseignes"]) AS perimetre
  WHERE perimetre = "tous" OR NOT enseigne_signalee
  GROUP BY perimetre, jour
),

total AS (
  SELECT
    perimetre,
    0                                               AS jour,
    COUNT(*)                                        AS en_ligne_la_veille,
    COUNTIF(supprime)                               AS suppressions,
    COUNT(DISTINCT IF(supprime, cid, NULL))         AS fiches_touchees
  FROM avis, UNNEST(["tous", "sans_enseignes"]) AS perimetre
  WHERE perimetre = "tous" OR NOT enseigne_signalee
  GROUP BY perimetre
)

SELECT *, ROUND(10000 * suppressions / en_ligne_la_veille, 1) AS pour_10000
FROM (SELECT * FROM par_jour UNION ALL SELECT * FROM total)
ORDER BY perimetre, jour
