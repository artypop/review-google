-- ============================================================================
-- 7. La réponse du propriétaire sur toute la base : taux directs
--
-- Base : `reviews_doublons_cleaned`, avis publiés avant le 11 août 2026, donc
-- déjà en ligne au premier passage du robot. Suppressions : du 12 au 24 août.
-- Un calcul direct, sans modèle : pour chaque case, combien d'avis, combien
-- supprimés.
--
-- Lecture d'une ligne : « parmi les avis de 31 à 90 jours, sur les fiches qui
-- répondent à plus de 75 %, N avis répondus sur 10 000 ont disparu ».
--
--   repondu    le propriétaire avait répondu AVANT le 11 août. Une réponse
--              arrivée pendant le suivi ne compte pas : l'avis est « sans
--              réponse au 11 août ».
--   age        âge de l'avis le 11 août. Un avis publié le 10 août a 1 jour.
--   habitude   part des avis de la fiche, publiés du 2025-08-11 au 2026-08-03,
--              qui avaient une réponse avant le 11 août. Inconnue sous 10 avis.
--              Bloc repris tel quel de
--              `logistic-regression-study/sql/03B_adding_features.bqsql`
--              (`habitude_reponse_fiche`) : même définition qu'aux points 3 et 5.
--   fiches_touchees, suppressions_de_la_premiere_fiche
--              30 suppressions sur 3 fiches ne se lisent pas comme
--              30 suppressions sur 30 fiches.
--
-- Chaque dimension a aussi sa ligne d'ensemble : « tous âges », habitude
-- « toutes », taille « toutes », région « ensemble ».
-- ============================================================================

WITH habitude_reponse_fiche AS (
  SELECT
    cid,
    COUNT(*) AS n_avis,
    COUNTIF(reply_date IS NOT NULL
            AND CAST(reply_date AS DATE) < DATE "2026-08-11") / COUNT(*) AS taux
  FROM `client-divers.reviewflowz.01_reviews_avis_update_et_unique`
  WHERE CAST(created_at AS DATE) BETWEEN DATE "2025-08-11" AND DATE "2026-08-03"
  GROUP BY cid
),

avis AS (
  SELECT
    r.cid,
    r.deleted_detected_at IS NOT NULL AS supprime,
    r.reply_date IS NOT NULL AND CAST(r.reply_date AS DATE) < DATE "2026-08-11" AS repondu,
    DATE_DIFF(DATE "2026-08-11", CAST(r.created_at AS DATE), DAY) AS age_j,
    IF(b.country = "US", "US", "Europe") AS region,
    IF(b.bucket = "large", "large", "mono + small") AS taille,
    s.cid IS NOT NULL AS enseigne_signalee,
    CASE WHEN COALESCE(h.n_avis, 0) < 10 THEN "inconnue"
         WHEN h.taux > 0.75 THEN "plus de 75 %"
         ELSE "75 % ou moins" END AS habitude
  FROM `client-divers.reviewflowz.reviews_doublons_cleaned` r
  LEFT JOIN `client-divers.reviewflowz.businesses` b USING (cid)
  LEFT JOIN `client-divers.reviewflowz.biz_surveillance` s USING (cid)
  LEFT JOIN habitude_reponse_fiche h USING (cid)
  WHERE CAST(r.created_at AS DATE) < DATE "2026-08-11"
),

-- Une ligne par fiche, tranche d'âge et état de la réponse.
par_fiche AS (
  SELECT
    cid, region, taille, habitude, enseigne_signalee, repondu,
    CASE WHEN age_j <= 7 THEN "1. 1 à 7 jours"
         WHEN age_j <= 30 THEN "2. 8 à 30 jours"
         WHEN age_j <= 90 THEN "3. 31 à 90 jours"
         WHEN age_j <= 365 THEN "4. 91 à 365 jours"
         ELSE "5. plus d'un an" END AS age,
    COUNT(*) AS n,
    COUNTIF(supprime) AS k
  FROM avis
  GROUP BY cid, region, taille, habitude, enseigne_signalee, repondu, age
),

-- Chaque fiche compte dans sa case et dans les lignes d'ensemble.
par_fiche_et_case AS (
  SELECT
    perimetre, region_vue, taille_vue, habitude_vue, age_vue, repondu, cid,
    SUM(n) AS n,
    SUM(k) AS k
  FROM par_fiche,
       UNNEST(["tous", "sans_enseignes"]) AS perimetre,
       UNNEST([region, "ensemble"])       AS region_vue,
       UNNEST([taille, "toutes"])         AS taille_vue,
       UNNEST([habitude, "toutes"])       AS habitude_vue,
       UNNEST([age, "0. tous âges"])      AS age_vue
  WHERE perimetre = "tous" OR NOT enseigne_signalee
  GROUP BY perimetre, region_vue, taille_vue, habitude_vue, age_vue, repondu, cid
)

SELECT
  perimetre,
  region_vue                                  AS region,
  taille_vue                                  AS taille,
  habitude_vue                                AS habitude,
  age_vue                                     AS age,
  IF(repondu, "repondu", "sans_reponse")      AS reponse,
  SUM(n)                                      AS avis,
  SUM(k)                                      AS suppressions,
  COUNT(*)                                    AS fiches,
  COUNTIF(k > 0)                              AS fiches_touchees,
  MAX(k)                                      AS suppressions_de_la_premiere_fiche
FROM par_fiche_et_case
GROUP BY perimetre, region, taille, habitude, age, reponse
