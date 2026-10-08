-- Tableau 5 d'Axel : âge de l'avis au moment de sa suppression (jours entre
-- publication et suppression constatée), fiches à 11 et plus face aux 1 à 10.
-- Stock : âge de tous les avis de ces fiches au 11 août 2026 (0 pour les avis
-- publiés pendant le suivi).
, t AS (
  SELECT base, categorie, suppression IS NOT NULL AS supprime,
         IF(suppression IS NOT NULL, DATE_DIFF(suppression, publication, DAY),
            GREATEST(DATE_DIFF(DATE "2026-08-11", publication, DAY), 0)) AS age
  FROM avis_cat
  WHERE categorie != "aucune"
),
tranches AS (
  SELECT *, CASE
      WHEN age <= 1 THEN "a. 0 à 1 jour"     WHEN age <= 3 THEN "b. 2 à 3 jours"
      WHEN age <= 7 THEN "c. 4 à 7 jours"    WHEN age <= 14 THEN "d. 8 à 14 jours"
      WHEN age <= 30 THEN "e. 15 à 30 jours" WHEN age <= 90 THEN "f. 31 à 90 jours"
      WHEN age <= 365 THEN "g. 91 à 365 jours" WHEN age <= 1095 THEN "h. 1 à 3 ans"
      ELSE "i. plus de 3 ans" END AS tranche
  FROM t
)
SELECT base, categorie, tranche,
       COUNTIF(supprime)                                                         AS suppressions,
       ROUND(100 * COUNTIF(supprime) / SUM(COUNTIF(supprime)) OVER (PARTITION BY base, categorie), 1)
                                                                                 AS pct_des_suppressions,
       ROUND(100 * COUNTIF(NOT supprime) / SUM(COUNTIF(NOT supprime)) OVER (PARTITION BY base, categorie), 2)
                                                                                 AS pct_du_stock
FROM tranches
GROUP BY base, categorie, tranche
ORDER BY base, categorie, tranche
