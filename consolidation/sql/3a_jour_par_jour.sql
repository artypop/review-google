-- ============================================================================
-- 3a. Suppressions jour par jour après la publication, selon la réponse
--
-- Population : les avis de `3b_population.sql` (vus naître, suivis 8 jours,
-- encore en ligne au 2e jour, habitude de la fiche connue).
-- Groupes : habitude de la fiche × réponse au 2e jour (oui = réponse le jour
-- même, à 1 ou à 2 jours) × taille × périmètre.
--
-- Pour chaque jour du 3e au 8e : les avis du groupe encore en ligne la
-- veille, ceux qui disparaissent ce jour-là, et la part encore en ligne sur
-- 10 000 avis en ligne au 2e jour. Même calcul que `1d_survie.sql`.
-- ============================================================================

WITH avis AS (
  SELECT
    f.cid,
    s.cid IS NOT NULL                                  AS enseigne_signalee,
    IF(f.bucket = "large", "large", "mono + small")    AS taille,
    IF(f.taux_reponse_fiche_avant_vague1 > 0.75,
       "plus de 75 %", "75 % ou moins")                AS habitude,
    IF(f.delai_reponse_j <= 2, "oui", "non")           AS reponse_au_2e_jour,
    IF(f.supprime AND f.age_a_la_suppression_j <= 8,
       f.age_a_la_suppression_j, 8)                    AS age_sortie,
    f.supprime AND f.age_a_la_suppression_j <= 8       AS supprime_avant_9e_jour
  FROM `client-divers.reviewflowz.reviews_panel_features_03B` f
  LEFT JOIN `client-divers.reviewflowz.biz_surveillance` s USING (cid)
  WHERE f.age_a_la_premiere_observation_j <= 1
    AND DATE_DIFF(DATE "2026-08-24", f.created_at_day, DAY) >= 8
    AND NOT (f.supprime AND f.age_a_la_suppression_j <= 2)
    AND f.taux_reponse_fiche_avant_vague1 IS NOT NULL
),

jours AS (
  SELECT a.*, age, a.supprime_avant_9e_jour AND age = a.age_sortie AS disparu_ce_jour
  FROM avis a, UNNEST(GENERATE_ARRAY(3, a.age_sortie)) AS age
),

comptes AS (
  SELECT
    perimetre, taille, habitude, reponse_au_2e_jour, age AS jour_apres_publication,
    COUNT(*)                  AS en_ligne_la_veille,
    COUNTIF(disparu_ce_jour)  AS suppressions
  FROM jours, UNNEST(["tous", "sans_enseignes"]) AS perimetre
  WHERE perimetre = "tous" OR NOT enseigne_signalee
  GROUP BY perimetre, taille, habitude, reponse_au_2e_jour, jour_apres_publication
)

SELECT
  *,
  ROUND(10000 * suppressions / en_ligne_la_veille, 1) AS pour_10000,
  ROUND(10000 * EXP(SUM(LN(1 - suppressions / en_ligne_la_veille)) OVER (
          PARTITION BY perimetre, taille, habitude, reponse_au_2e_jour
          ORDER BY jour_apres_publication)), 0)        AS encore_en_ligne_sur_10000
FROM comptes
ORDER BY perimetre DESC, taille DESC, habitude, reponse_au_2e_jour DESC, jour_apres_publication
