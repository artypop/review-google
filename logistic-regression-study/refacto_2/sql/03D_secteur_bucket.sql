-- ============================================================================
-- Distribution secteur × bucket du panel 03D (`dataset_reg`)
--
-- Table `reviews_panel_features_03D` : avis publiés du 6 au 17 août 2026,
-- suivis jusqu'au 24 août. Une ligne par périmètre, secteur et bucket, avec
-- fiches, avis et suppressions. Les lignes « total » donnent les marges.
-- ============================================================================

SELECT
  perimetre,
  secteur_vu                                 AS secteur,
  bucket_vu                                  AS bucket,
  COUNT(DISTINCT cid)                        AS fiches,
  COUNT(*)                                   AS avis,
  COUNTIF(supprime)                          AS suppressions
FROM `client-divers.reviewflowz.reviews_panel_features_03D`,
     UNNEST(["tous", "sans_enseignes"]) AS perimetre,
     UNNEST([secteur, "total"])         AS secteur_vu,
     UNNEST([bucket, "total"])          AS bucket_vu
WHERE perimetre = "tous" OR NOT enseigne_signalee
GROUP BY perimetre, secteur, bucket
ORDER BY perimetre DESC, secteur, bucket
