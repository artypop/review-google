-- ============================================================================
-- 3. La population du point 3, étape par étape
--
-- Table : `reviews_panel_features_03B`. Même population que le 08B
-- (`logistic-regression-study/python/08B_effet_reponse_commercant.py`).
--
--   1. panel 03B entier
--   2. avis vus par le robot le jour de leur publication ou le lendemain :
--      on connaît leur état dès leurs premiers jours
--   3. publiés au plus tard le 16 août : ils sont suivis jusqu'à leur 8e jour
--      (dernier passage le 24 août)
--   4. encore en ligne au passage du 2e jour : c'est le jalon
--   5. fiche avec au moins 10 avis d'historique : son habitude de réponse est
--      connue
--
-- `suppressions_3_8` : avis disparus du 3e au 8e jour après publication.
-- ============================================================================

WITH p AS (
  SELECT
    *,
    age_a_la_premiere_observation_j <= 1                          AS vu_naitre,
    DATE_DIFF(DATE "2026-08-24", created_at_day, DAY) >= 8         AS suivi_8_jours,
    NOT (supprime AND age_a_la_suppression_j <= 2)                 AS en_ligne_au_2e_jour,
    supprime AND age_a_la_suppression_j BETWEEN 3 AND 8            AS supprime_3_8
  FROM `client-divers.reviewflowz.reviews_panel_features_03B`
)

SELECT 1 AS ordre, "1. panel 03B" AS etape, COUNT(*) AS avis,
       MIN(created_at_day) AS publie_du, MAX(created_at_day) AS publie_au,
       COUNTIF(supprime_3_8) AS suppressions_3_8
FROM p
UNION ALL
SELECT 2, "2. vus le jour de leur publication ou le lendemain", COUNT(*),
       MIN(created_at_day), MAX(created_at_day), COUNTIF(supprime_3_8)
FROM p WHERE vu_naitre
UNION ALL
SELECT 3, "3. suivis jusqu'à leur 8e jour", COUNT(*),
       MIN(created_at_day), MAX(created_at_day), COUNTIF(supprime_3_8)
FROM p WHERE vu_naitre AND suivi_8_jours
UNION ALL
SELECT 4, "4. encore en ligne au 2e jour", COUNT(*),
       MIN(created_at_day), MAX(created_at_day), COUNTIF(supprime_3_8)
FROM p WHERE vu_naitre AND suivi_8_jours AND en_ligne_au_2e_jour
UNION ALL
SELECT 5, "5. fiche avec au moins 10 avis d'historique", COUNT(*),
       MIN(created_at_day), MAX(created_at_day), COUNTIF(supprime_3_8)
FROM p WHERE vu_naitre AND suivi_8_jours AND en_ligne_au_2e_jour
         AND taux_reponse_fiche_avant_vague1 IS NOT NULL
ORDER BY ordre
