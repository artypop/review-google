-- ============================================================================
-- 2.2. Les avis supprimés des deux groupes, jour par jour
--
-- Mêmes groupes et même base que `2_2_resume.sql`. Seuls les avis supprimés.
-- Une ligne par groupe et par jour :
--   supprimes_publies_ce_jour   avis supprimés qui avaient été publiés ce jour-là
--   supprimes_ce_jour           avis dont la disparition est constatée ce jour-là
--   dont_publies_avant_le_4_aout  parmi ces derniers, ceux publiés avant J-7
-- Donne directement les comptes cités dans `2_2_deux_phenomenes.md`.
-- ============================================================================

WITH supprimes AS (
  SELECT
    IF(r.cid IN ("3163466139043001754", "10346942689164695031"),
       "salles_espagnoles", "chaines_antiparasitaires") AS groupe,
    DATE(r.created_at)          AS jour_publication,
    DATE(r.deleted_detected_at) AS jour_suppression
  FROM `client-divers.reviewflowz.reviews_doublons_cleaned_all` r
  JOIN `client-divers.reviewflowz.biz_surveillance` s USING (cid)
  WHERE r.deleted_detected_at IS NOT NULL
),

par_publication AS (
  SELECT groupe, jour_publication AS jour, COUNT(*) AS n
  FROM supprimes GROUP BY groupe, jour
),

par_suppression AS (
  SELECT groupe, jour_suppression AS jour, COUNT(*) AS n,
         COUNTIF(jour_publication < DATE "2026-08-04") AS n_anciens
  FROM supprimes GROUP BY groupe, jour
)

SELECT
  groupe,
  jour,
  COALESCE(p.n, 0)          AS supprimes_publies_ce_jour,
  COALESCE(s.n, 0)          AS supprimes_ce_jour,
  COALESCE(s.n_anciens, 0)  AS dont_publies_avant_le_4_aout
FROM par_publication p
FULL JOIN par_suppression s USING (groupe, jour)
ORDER BY groupe, jour
