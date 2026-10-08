-- Tableau 4 d'Axel : comment les suppressions d'une fiche se répartissent sur
-- les 13 jours où une disparition peut être constatée (12 au 24 août).
-- Fiches à 11 suppressions et plus, face aux fiches à 3 à 10.
, par_jour AS (
  SELECT base, cid, suppressions_fiche, suppression, COUNT(*) AS n
  FROM avis_cat
  WHERE suppression IS NOT NULL AND suppressions_fiche >= 3
  GROUP BY base, cid, suppressions_fiche, suppression
),
par_fiche AS (
  SELECT base, cid,
         IF(suppressions_fiche > 10, "11 et plus", "3 à 10") AS groupe,
         COUNT(*)                         AS jours_avec_suppression,
         MAX(n) / SUM(n)                  AS part_jour_le_plus_charge
  FROM par_jour GROUP BY base, cid, groupe
)
SELECT
  base, groupe,
  COUNT(*)                                                       AS fiches,
  ROUND(AVG(jours_avec_suppression), 1)                          AS jours_moyens_avec_suppression,
  ROUND(100 * APPROX_QUANTILES(part_jour_le_plus_charge, 2)[OFFSET(1)], 0)
                                                                 AS part_mediane_jour_le_plus_charge,
  COUNTIF(part_jour_le_plus_charge >= 0.8)                       AS fiches_80pct_en_un_jour
FROM par_fiche
GROUP BY base, groupe
ORDER BY base, groupe
