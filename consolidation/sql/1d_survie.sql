-- ============================================================================
-- 1d. Survie des avis publiés de J-7 à J+7 (du 4 au 18 août 2026)
--
-- Base : `reviews_doublons_cleaned_all`, avis publiés du 4 au 18 août.
--
-- LE CALCUL, JOUR PAR JOUR
--   Pour chaque âge (1 jour, 2 jours…), on prend les avis que le robot voyait
--   en ligne la veille de cet âge, et on compte ceux qui ont disparu ce jour-là.
--   Exemple : « au 7e jour, 20 000 avis étaient en ligne la veille, 60 ont
--   disparu : 30 pour 10 000 ».
--
--   Puis on enchaîne les jours : sur 10 000 avis publiés, 9 990 passent le
--   1er jour, puis 9 990 × (1 − taux du 2e jour) passent le 2e, etc. C'est la
--   colonne `encore_en_ligne_sur_10000`.
--
--   Un avis publié le 4 août n'est vu par le robot qu'à partir du 11, à 7 jours.
--   Il ne compte qu'à partir de son 8e jour : ce qui lui est arrivé avant, on ne
--   l'a pas vu.
--
-- Âge d'entrée : jour de la première observation de l'avis, pris sur sa
-- première ligne dans `reviews`. La ligne gardée d'un avis modifié porte la
-- date de la modification, d'où ce détour.
-- Âge de sortie : jour où le robot constate la disparition, ou le 24 août,
-- dernier passage, si l'avis est toujours en ligne.
-- ============================================================================

WITH premiere_vue AS (
  SELECT review_id, DATE(MIN(first_seen_at)) AS premier_jour_vu
  FROM `client-divers.reviewflowz.reviews`
  GROUP BY review_id
),

avis AS (
  SELECT
    IF(b.country = "US", "US", "Europe") AS region,
    s.cid IS NOT NULL AS enseigne_signalee,
    r.deleted_detected_at IS NOT NULL AS supprime,
    GREATEST(DATE_DIFF(pv.premier_jour_vu, DATE(r.created_at), DAY), 0) AS age_entree,
    DATE_DIFF(COALESCE(DATE(r.deleted_detected_at), DATE "2026-08-24"),
              DATE(r.created_at), DAY) AS age_sortie
  FROM `client-divers.reviewflowz.reviews_doublons_cleaned_all` r
  JOIN premiere_vue pv USING (review_id)
  LEFT JOIN `client-divers.reviewflowz.businesses` b USING (cid)
  LEFT JOIN `client-divers.reviewflowz.biz_surveillance` s USING (cid)
  WHERE DATE(r.created_at) BETWEEN DATE "2026-08-04" AND DATE "2026-08-18"
),

-- Une ligne par avis et par âge où il pouvait être vu disparaître.
jours AS (
  SELECT
    a.region,
    a.enseigne_signalee,
    age,
    a.supprime AND age = a.age_sortie AS disparu_ce_jour
  FROM avis a, UNNEST(GENERATE_ARRAY(a.age_entree + 1, a.age_sortie)) AS age
),

comptes AS (
  SELECT
    perimetre,
    region_vue                  AS region,
    age                         AS age_j,
    COUNT(*)                    AS en_ligne_la_veille,
    COUNTIF(disparu_ce_jour)    AS suppressions
  FROM jours,
       UNNEST(["tous", "sans_enseignes"]) AS perimetre,
       UNNEST([region, "ensemble"])       AS region_vue
  WHERE perimetre = "tous" OR NOT enseigne_signalee
  GROUP BY perimetre, region, age_j
)

SELECT
  perimetre,
  region,
  age_j,
  en_ligne_la_veille,
  suppressions,
  ROUND(10000 * suppressions / en_ligne_la_veille, 1) AS pour_10000,
  ROUND(10000 * EXP(SUM(LN(1 - suppressions / en_ligne_la_veille))
                    OVER (PARTITION BY perimetre, region ORDER BY age_j)), 0)
                                                       AS encore_en_ligne_sur_10000
FROM comptes
ORDER BY perimetre DESC, region, age_j
