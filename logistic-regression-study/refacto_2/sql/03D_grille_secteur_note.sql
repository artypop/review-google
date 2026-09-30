-- Suppressions par secteur et par note, panel 03D : avis publiés du 6 au
-- 17 août 2026, suivis jusqu'au 24 août.
-- Une ligne par périmètre, secteur et note, avec les totaux (« total »).
-- `fiches_touchees` : fiches différentes qui portent les avis supprimés.
WITH avis AS (
  SELECT cid, secteur, CAST(star AS STRING) AS note, supprime, enseigne_signalee
  FROM `client-divers.reviewflowz.reviews_panel_features_03D`
)
SELECT
  perimetre,
  secteur_vue                             AS secteur,
  note_vue                                AS note,
  COUNT(*)                                AS avis,
  COUNTIF(supprime)                       AS suppressions,
  COUNT(DISTINCT IF(supprime, cid, NULL)) AS fiches_touchees
FROM avis,
     UNNEST(["tous", "sans_enseignes"]) AS perimetre,
     UNNEST([secteur, "total"])         AS secteur_vue,
     UNNEST([note, "total"])            AS note_vue
WHERE perimetre = "tous" OR NOT enseigne_signalee
GROUP BY perimetre, secteur, note
ORDER BY perimetre, secteur, note
