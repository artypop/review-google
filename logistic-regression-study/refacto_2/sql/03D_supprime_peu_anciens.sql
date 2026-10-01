-- ============================================================================
-- Google supprime peu une fois l'avis publié : les avis publiés avant le robot
--
-- Base : `reviews_doublons_cleaned_all`, avis publiés (created_at) jusqu'au
-- 31 décembre 2025. Suppressions constatées pendant les 14 jours de suivi, du
-- 11 au 24 août 2026.
--
-- Un avis supprimé avant le 11 août n'est pas dans la base : on ne voit que
-- les avis encore en ligne au premier passage.
--
-- `pour_10000_par_jour` se compare aux barres de sql/03D_supprime_peu_recents.sql.
-- Une ligne par périmètre et par année de publication, plus une ligne « total ». Les années 2004 à 2013
-- sont regroupées (aucune suppression).
-- ============================================================================

WITH avis AS (
  SELECT
    r.cid,
    s.cid IS NOT NULL AS enseigne_signalee,
    r.deleted_detected_at IS NOT NULL AS supprime,
    CASE
      WHEN EXTRACT(YEAR FROM r.created_at) <= 2013 THEN "2004 à 2013"
      ELSE CAST(EXTRACT(YEAR FROM r.created_at) AS STRING)
    END AS publication
  FROM `client-divers.reviewflowz.reviews_doublons_cleaned_all` r
  LEFT JOIN `client-divers.reviewflowz.biz_surveillance` s USING (cid)
  WHERE DATE(r.created_at) < DATE "2026-01-01"
)

SELECT
  perimetre,
  publication_vue                                  AS publication,
  COUNT(*)                                         AS avis,
  COUNTIF(supprime)                                AS suppressions,
  COUNT(DISTINCT IF(supprime, cid, NULL))          AS fiches_touchees,
  ROUND(10000 * COUNTIF(supprime) / COUNT(*), 1)   AS pour_10000,
  -- Ramené à une journée : 14 passages, soit 13 jours où une disparition
  -- peut être constatée (du 12 au 24 août).
  ROUND(10000 * COUNTIF(supprime) / COUNT(*) / 13, 2) AS pour_10000_par_jour
FROM avis,
     UNNEST(["tous", "sans_enseignes"]) AS perimetre,
     UNNEST([publication, "total"])     AS publication_vue
WHERE perimetre = "tous" OR NOT enseigne_signalee
GROUP BY perimetre, publication
ORDER BY perimetre, publication
