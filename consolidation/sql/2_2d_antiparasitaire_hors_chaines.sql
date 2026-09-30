-- ============================================================================
-- 2.2d. Les fiches antiparasitaires américaines hors des 4 chaînes
--
-- La version « sans enseignes » de la consolidation retire les 95 fiches de
-- `biz_surveillance` : les 4 chaînes au nom exact et les 2 salles. Le 07C
-- retirait plus large : toute fiche américaine du secteur `home_services` dont
-- le nom porte un mot de l'activité (pest, exterminat, termite, spidexx,
-- mosquito, rodent, wildlife), plus l'enseigne ABC Home ajoutée à la main.
-- Ce repérage est repris tel quel de
-- `logistic-regression-study/python/07C_regression_reduite.py`.
--
-- Cette requête liste les fiches du repérage large qui ne sont PAS dans
-- `biz_surveillance`, une ligne par fiche, pour voir si elles montrent le même
-- phénomène que les 4 chaînes : beaucoup de suppressions, presque toutes à
-- 5 étoiles, souvent 6 ou 7 jours après la publication, et par blocs.
--
-- Base : `reviews_doublons_cleaned_all`, toutes dates de publication. Les colonnes
-- `panel_` comptent les seuls avis de 03B (publiés du 4 au 17 août 2026).
--
--   succursale_de        le nom commence par celui d'une des 4 chaînes : une
--                        succursale que l'égalité exacte de nom a laissée dehors
--   suppressions_le_jour_le_plus_charge
--                        le plus grand nombre de suppressions constatées le même
--                        jour sur la fiche : repère les retraits en bloc
-- ============================================================================

WITH fiches AS (
  SELECT
    b.cid,
    b.name AS enseigne,
    b.bucket AS taille,
    CASE
      WHEN STARTS_WITH(b.name, "EcoShield Pest Solutions") THEN "EcoShield Pest Solutions"
      WHEN STARTS_WITH(b.name, "Insight Pest Solutions")   THEN "Insight Pest Solutions"
      WHEN STARTS_WITH(b.name, "Pointe Pest Control")      THEN "Pointe Pest Control"
      WHEN STARTS_WITH(b.name, "Bulwark Exterminating")    THEN "Bulwark Exterminating"
    END AS succursale_de
  FROM `client-divers.reviewflowz.businesses` b
  LEFT JOIN `client-divers.reviewflowz.biz_surveillance` s USING (cid)
  WHERE s.cid IS NULL
    AND b.country = "US"
    AND b.industry = "home_services"
    AND (REGEXP_CONTAINS(b.name, r"(?i)(pest|exterminat|termite|spidexx|mosquito|rodent|wildlife)")
         OR REGEXP_CONTAINS(b.name, r"(?i)abc home ?(&|and) ?commercial"))
),

avis AS (
  SELECT
    f.cid,
    r.star,
    r.deleted_detected_at IS NOT NULL AS supprime,
    DATE(r.deleted_detected_at) AS jour_suppression,
    DATE_DIFF(DATE(r.deleted_detected_at), DATE(r.created_at), DAY) AS delai,
    p.review_id IS NOT NULL AS dans_le_panel
  FROM fiches f
  JOIN `client-divers.reviewflowz.reviews_doublons_cleaned_all` r USING (cid)
  LEFT JOIN `client-divers.reviewflowz.reviews_panel_features_03B` p USING (review_id)
),

par_jour AS (
  SELECT cid, jour_suppression, COUNT(*) AS n
  FROM avis
  WHERE supprime
  GROUP BY cid, jour_suppression
),

jours AS (
  SELECT cid, COUNT(*) AS jours_avec_suppression, MAX(n) AS suppressions_le_jour_le_plus_charge
  FROM par_jour
  GROUP BY cid
)

SELECT
  f.cid,
  f.enseigne,
  f.succursale_de,
  f.taille,
  COUNT(a.cid)                                          AS avis,
  COUNTIF(a.supprime)                                   AS suppressions,
  COUNTIF(a.supprime AND a.star = 5)                    AS suppressions_5_etoiles,
  COUNTIF(a.supprime AND a.star = 1)                    AS suppressions_1_etoile,
  COUNTIF(a.supprime AND a.delai IN (6, 7))             AS suppressions_a_6_ou_7_jours,
  COUNTIF(a.supprime AND a.delai > 30)                  AS suppressions_a_plus_de_30_jours,
  MIN(a.jour_suppression)                               AS premiere_suppression,
  MAX(a.jour_suppression)                               AS derniere_suppression,
  COALESCE(ANY_VALUE(j.jours_avec_suppression), 0)      AS jours_avec_suppression,
  COALESCE(ANY_VALUE(j.suppressions_le_jour_le_plus_charge), 0)
                                                        AS suppressions_le_jour_le_plus_charge,
  COUNTIF(a.dans_le_panel)                              AS panel_avis,
  COUNTIF(a.dans_le_panel AND a.supprime)               AS panel_suppressions
FROM fiches f
LEFT JOIN avis a USING (cid)
LEFT JOIN jours j USING (cid)
GROUP BY f.cid, f.enseigne, f.succursale_de, f.taille
ORDER BY suppressions DESC, avis DESC
