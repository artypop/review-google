-- Suppressions par secteur et par réponse du propriétaire, panel 03D : avis
-- publiés du 6 au 17 août 2026, suivis jusqu'au 24 août.
-- Réponse comme dans `03D_grille_reponse_note.sql` : répondu ou non, quel
-- que soit le délai.
-- Une ligne par périmètre, secteur et réponse, avec les totaux (« total »).
-- `fiches_touchees` : fiches différentes qui portent les avis supprimés.
WITH avis AS (
  SELECT
    cid,
    secteur,
    IF(a_repondu, "a répondu", "n'a pas répondu") AS reponse,
    supprime,
    enseigne_signalee
  FROM `client-divers.reviewflowz.reviews_panel_features_03D`
)
SELECT
  perimetre,
  secteur_vue                             AS secteur,
  reponse_vue                             AS reponse,
  COUNT(*)                                AS avis,
  COUNTIF(supprime)                       AS suppressions,
  COUNT(DISTINCT IF(supprime, cid, NULL)) AS fiches_touchees
FROM avis,
     UNNEST(["tous", "sans_enseignes"]) AS perimetre,
     UNNEST([secteur, "total"])         AS secteur_vue,
     UNNEST([reponse, "total"])         AS reponse_vue
WHERE perimetre = "tous" OR NOT enseigne_signalee
GROUP BY perimetre, secteur, reponse
ORDER BY perimetre, secteur, reponse
