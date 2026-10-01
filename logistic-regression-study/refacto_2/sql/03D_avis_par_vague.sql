-- ============================================================================
-- Nombre d'avis de la base à chaque vague de passage du robot
--
-- Base : `reviews_doublons_cleaned_all`. Vague 1 = 11 août 2026, vague 14 =
-- 24 août, un passage par jour.
--
--   avis_connus      avis déjà vus au moins une fois à cette vague, supprimés
--                    ensuite ou non (cumul)
--   avis_en_ligne    avis vus et pas encore constatés supprimés à cette vague
--   nouveaux         avis vus pour la première fois à cette vague
--   supprimes        avis constatés supprimés à cette vague
--
-- Premier jour vu pris sur la première ligne de l'avis dans `reviews` : la
-- ligne gardée d'un avis modifié porte la date de la modification.
-- ============================================================================

WITH premiere_vue AS (
  SELECT review_id, DATE(MIN(first_seen_at)) AS premier_jour_vu
  FROM `client-divers.reviewflowz.reviews`
  GROUP BY review_id
),

avis AS (
  SELECT pv.premier_jour_vu, DATE(r.deleted_detected_at) AS jour_suppression
  FROM `client-divers.reviewflowz.reviews_doublons_cleaned_all` r
  JOIN premiere_vue pv USING (review_id)
)

SELECT
  DATE_DIFF(jour, DATE "2026-08-11", DAY) + 1                         AS vague,
  jour,
  COUNTIF(premier_jour_vu <= jour)                                    AS avis_connus,
  COUNTIF(premier_jour_vu <= jour
          AND (jour_suppression IS NULL OR jour_suppression > jour))  AS avis_en_ligne,
  COUNTIF(premier_jour_vu = jour)                                     AS nouveaux,
  COUNTIF(jour_suppression = jour)                                    AS supprimes
FROM avis, UNNEST(GENERATE_DATE_ARRAY(DATE "2026-08-11", DATE "2026-08-24")) AS jour
GROUP BY jour
ORDER BY jour
