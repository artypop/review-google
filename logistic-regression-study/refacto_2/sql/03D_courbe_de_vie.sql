-- ============================================================================
-- Courbe de vie d'un avis sur ses 21 premiers jours, États-Unis et Europe
--
-- Base : `reviews_doublons_cleaned_all`, avis publiés de J-7 à J+14, J étant
-- le premier passage du robot, le 11 août 2026 : du 4 au 25 août. Le suivi
-- s'arrête le 24 août : un avis du 4 août est vu jusqu'à 20 jours d'âge, le
-- 21e jour reste vide.
--
-- LE CALCUL, JOUR PAR JOUR (même méthode que consolidation/sql/1d_survie.sql)
--   Pour chaque âge J, on prend les avis que le robot voyait en ligne à J-1,
--   et on compte ceux qui ont disparu au jour J. Puis on enchaîne les jours :
--   sur 100 avis publiés, la part encore en ligne au jour J est le produit des
--   parts qui ont passé chaque jour de 1 à J.
--
--   Un avis publié le 4 août n'est vu qu'à partir du 11 août, à 7 jours.
--   Il ne compte qu'à partir de son 8e jour.
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
    r.cid,
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
  WHERE DATE(r.created_at) BETWEEN DATE "2026-08-04" AND DATE "2026-08-25"
),

-- Une ligne par avis et par âge, de 1 à 21 jours, où il pouvait être vu
-- disparaître.
jours AS (
  SELECT
    a.cid,
    a.region,
    a.enseigne_signalee,
    age,
    a.supprime AND age = a.age_sortie AS disparu_ce_jour
  FROM avis a, UNNEST(GENERATE_ARRAY(a.age_entree + 1, LEAST(a.age_sortie, 21))) AS age
),

comptes AS (
  SELECT
    perimetre,
    region,
    age                                        AS jour,
    COUNT(*)                                   AS en_ligne_la_veille,
    COUNTIF(disparu_ce_jour)                   AS suppressions,
    COUNT(DISTINCT IF(disparu_ce_jour, cid, NULL)) AS fiches_touchees
  FROM jours,
       UNNEST(["tous", "sans_enseignes"]) AS perimetre
  WHERE perimetre = "tous" OR NOT enseigne_signalee
  GROUP BY perimetre, region, jour
)

SELECT
  perimetre,
  region,
  jour,
  en_ligne_la_veille,
  suppressions,
  fiches_touchees,
  ROUND(100 * EXP(SUM(LN(1 - suppressions / en_ligne_la_veille))
                  OVER (PARTITION BY perimetre, region ORDER BY jour)), 3)
                                               AS encore_en_ligne_pct
FROM comptes
ORDER BY perimetre, region, jour
