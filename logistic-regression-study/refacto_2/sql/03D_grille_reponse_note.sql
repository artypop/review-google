-- Suppressions par réponse du propriétaire et par note, panel 03D : avis
-- publiés du 6 au 17 août 2026, suivis jusqu'au 24 août.
-- Réponse lue au dernier passage du robot, comme dans la régression : le
-- propriétaire a-t-il répondu, quel que soit le délai ?
-- Une ligne par périmètre, réponse et note, avec les totaux (« total »).
-- `fiches_touchees` : fiches différentes qui portent les avis supprimés.
WITH avis AS (
  SELECT
    cid,
    IF(a_repondu, "a répondu", "n'a pas répondu") AS reponse,
    CAST(star AS STRING)       AS note,
    supprime,
    enseigne_signalee
  FROM `client-divers.reviewflowz.reviews_panel_features_03D`
)
SELECT
  perimetre,
  reponse_vue                             AS reponse,
  note_vue                                AS note,
  COUNT(*)                                AS avis,
  COUNTIF(supprime)                       AS suppressions,
  COUNT(DISTINCT IF(supprime, cid, NULL)) AS fiches_touchees
FROM avis,
     UNNEST(["tous", "sans_enseignes"]) AS perimetre,
     UNNEST([reponse, "total"])         AS reponse_vue,
     UNNEST([note, "total"])            AS note_vue
WHERE perimetre = "tous" OR NOT enseigne_signalee
GROUP BY perimetre, reponse, note
ORDER BY perimetre, reponse, note
