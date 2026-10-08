-- Contrôle demandé par Romain : notre base ne doit contenir aucune fiche plus
-- touchée que chez Axel. Catégorie Axel × catégorie nettoyée, et fiches où
-- nous comptons plus de suppressions que lui.
SELECT a.categorie AS categorie_axel, n.categorie AS categorie_nettoyee,
       COUNT(*) AS fiches,
       SUM(a.suppressions_fiche) AS suppressions_axel,
       SUM(n.suppressions_fiche) AS suppressions_nettoyee,
       COUNTIF(n.suppressions_fiche > a.suppressions_fiche) AS fiches_plus_touchees_chez_nous
FROM (SELECT DISTINCT base, cid, categorie, suppressions_fiche FROM avis_cat WHERE base = "axel") a
JOIN (SELECT DISTINCT base, cid, categorie, suppressions_fiche FROM avis_cat WHERE base = "nettoyee") n USING (cid)
GROUP BY 1, 2 ORDER BY 1, 2
