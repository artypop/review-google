-- Contrôle préalable : quelles fiches porte le flag `salle_de_sport_attaquee`.
--
-- Lecture seule. Ne crée aucune table.
--
-- Le flag de `sql/02_adding_features.sql` marque sur le nom de l'enseigne. Il
-- retient 13 fiches alors que 2 sont attaquées ; les 11 autres portent le même
-- nom, totalisent 90 avis et aucune suppression (`docs/02-donnees.md` § 4).
--
-- Cette requête sort les `cid` avec leurs compteurs, pour que la liste des
-- fiches réellement attaquées soit validée une fois et écrite en dur ensuite.
-- Le nom de l'établissement n'est pas sélectionné : le `cid` suffit à
-- identifier la fiche et rien d'autre n'a besoin d'apparaître ici.
--
-- Périmètre : le panel entier, 225 757 avis. Volontairement large — restreindre
-- aux six journées de suivi cacherait les suppressions qui ont fondé le
-- repérage.

SELECT
  cid,
  COUNT(*)                                      AS avis_du_panel,
  COUNTIF(supprime)                             AS suppressions,
  COUNTIF(supprime AND star = 1)                AS suppressions_1_etoile,
  ROUND(SAFE_DIVIDE(COUNTIF(supprime AND star = 1),
                    NULLIF(COUNTIF(supprime), 0)) * 100, 1)
                                                AS part_1_etoile_pct,
  MIN(age_a_la_suppression_j)                   AS delai_min_suppression_j,
  MAX(age_a_la_suppression_j)                   AS delai_max_suppression_j
FROM `client-divers.reviewflowz.reviews_panel_features`
WHERE salle_de_sport_attaquee
GROUP BY cid
ORDER BY suppressions DESC, avis_du_panel DESC;
