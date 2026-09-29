-- ============================================================================
-- 1c. Nombre d'avis par secteur et par taille d'entreprise — base complète
--
-- Base : `reviews_doublons_cleaned`, une ligne par avis, toutes dates de
-- publication.
-- Périmètre : `tous`, puis `sans_enseignes` qui retire les 95 fiches de
-- `biz_surveillance` (4 chaînes antiparasitaires US, 2 salles espagnoles).
-- `fiches_*` compte les fiches qui ont au moins un avis dans la base.
-- `part_du_corpus_pct` : part des avis du périmètre portée par le secteur.
-- ============================================================================

WITH avis AS (
  SELECT
    r.cid,
    b.bucket,
    CASE b.industry
      WHEN "automotive"       THEN "Automobile"
      WHEN "home_services"    THEN "Services à domicile"
      WHEN "healthcare"       THEN "Santé"
      WHEN "wellness_fitness" THEN "Sport et bien-être"
      WHEN "food_beverage"    THEN "Restauration"
      WHEN "travel"           THEN "Voyage"
      WHEN "hospitality"      THEN "Hôtellerie"
      ELSE b.industry
    END AS secteur,
    s.cid IS NOT NULL AS enseigne_signalee
  FROM `client-divers.reviewflowz.reviews_doublons_cleaned` r
  LEFT JOIN `client-divers.reviewflowz.businesses` b USING (cid)
  LEFT JOIN `client-divers.reviewflowz.biz_surveillance` s USING (cid)
),

-- Chaque avis est compté une fois dans `tous`, et une seconde fois dans
-- `sans_enseignes` s'il n'est pas sur une fiche signalée.
avis_par_perimetre AS (
  SELECT a.*, perimetre
  FROM avis a, UNNEST(["tous", "sans_enseignes"]) AS perimetre
  WHERE perimetre = "tous" OR NOT a.enseigne_signalee
)

SELECT
  perimetre,
  secteur,
  COUNT(DISTINCT IF(bucket = "mono",  cid, NULL)) AS fiches_mono,
  COUNT(DISTINCT IF(bucket = "small", cid, NULL)) AS fiches_small,
  COUNT(DISTINCT IF(bucket = "large", cid, NULL)) AS fiches_large,
  COUNTIF(bucket = "mono")                        AS avis_mono,
  COUNTIF(bucket = "small")                       AS avis_small,
  COUNTIF(bucket = "large")                       AS avis_large,
  COUNT(*)                                        AS avis,
  ROUND(100 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY perimetre), 1)
                                                  AS part_du_corpus_pct
FROM avis_par_perimetre
GROUP BY perimetre, secteur
ORDER BY perimetre DESC, avis DESC
