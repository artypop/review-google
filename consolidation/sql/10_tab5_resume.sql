-- Tableau 5 d'Axel, bas : âge médian à la suppression et parts à 7 jours ou moins,
-- 30 jours ou moins, au-delà d'un an (bornes d'Axel : ses tranches « 4 à 7 » et
-- « 15 à 30 jours » comprennent le 7e et le 30e jour).
, t AS (
  SELECT base, categorie, DATE_DIFF(suppression, publication, DAY) AS age
  FROM avis_cat
  WHERE suppression IS NOT NULL
)
SELECT base, categorie, COUNT(*) AS suppressions,
       APPROX_QUANTILES(age, 100)[OFFSET(50)]        AS age_median_jours,
       ROUND(100 * COUNTIF(age <= 7) / COUNT(*), 0)  AS pct_7_jours_ou_moins,
       ROUND(100 * COUNTIF(age <= 30) / COUNT(*), 0) AS pct_30_jours_ou_moins,
       ROUND(100 * COUNTIF(age > 365) / COUNT(*), 0) AS pct_plus_1_an
FROM t GROUP BY base, categorie ORDER BY base, categorie
