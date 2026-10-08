-- Tableaux 1 et 3 d'Axel : fiches, suppressions, et part des avis supprimés
-- par catégorie. « Récents » : publiés depuis le 12 juillet 2026 (30 jours avant
-- le premier passage du robot, avis publiés pendant le suivi compris).
-- « Pendant le suivi » : publiés à partir du 11 août.
SELECT
  base,
  groupe,
  COUNT(DISTINCT cid)                                                  AS fiches,
  COUNT(*)                                                             AS avis,
  COUNTIF(suppression IS NOT NULL)                                     AS suppressions,
  ROUND(100 * COUNTIF(suppression IS NOT NULL) / COUNT(*), 3)          AS pct_tous,
  ROUND(100 * COUNTIF(suppression IS NOT NULL AND publication >= "2026-07-12")
        / NULLIF(COUNTIF(publication >= "2026-07-12"), 0), 2)          AS pct_recents,
  ROUND(100 * COUNTIF(suppression IS NOT NULL AND publication >= "2026-08-11")
        / NULLIF(COUNTIF(publication >= "2026-08-11"), 0), 2)          AS pct_pendant_suivi
FROM avis_cat,
     UNNEST([categorie, IF(categorie = "11 et plus", NULL, "toutes sauf 11 et plus"), "toutes"]) AS groupe
WHERE groupe IS NOT NULL
GROUP BY base, groupe
ORDER BY base, groupe
