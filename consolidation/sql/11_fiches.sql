-- ============================================================================
-- 11. Une ligne par fiche : catégorie de suppressions, part de prénoms,
-- vélocité, et avis / suppressions par tranche d'âge
--
-- Base : `reviews_doublons_cleaned_all` (base complète nettoyée, 4 590
-- suppressions). Le marquage « l'avis cite un nom » vient d'Axel :
-- `reviews_name_enriched` (avis 4 et 5 étoiles avec texte), joint par
-- review_id ; l'état supprimé reste celui de notre base.
--
--   categorie        suppressions de la fiche en 14 jours : aucune / 1 à 10 /
--                    11 et plus (seuil d'Axel)
--   avis_45_texte    avis 4 et 5 étoiles présents dans `reviews_name_enriched`
--   part_noms        part de ces avis qui citent un nom
--   velocite_mois    avis publiés du 11 août 2025 au 10 août 2026, divisés par 12
--   habitude         part des avis de cette même année qui avaient une réponse
--                    avant le 11 août ; « inconnue » sous 10 avis
--   avis_<tranche>, supp_<tranche>
--                    avis et suppressions par âge au 11 août : publiés pendant
--                    le suivi, moins de 30 jours, 30 à 90, 90 à 365, 1 à 3 ans,
--                    plus de 3 ans
--
-- Un avis supprimé avant le 11 août n'est dans aucune table : la vélocité et le
-- stock d'avis récents sont un peu sous-comptés.
-- ============================================================================

WITH noms AS (
  SELECT review_id, LOGICAL_OR(has_name) AS a_un_nom
  FROM `client-divers.reviewflowz.reviews_name_enriched`
  GROUP BY review_id
),

avis AS (
  SELECT
    r.cid,
    r.star,
    r.deleted_detected_at IS NOT NULL AS supprime,
    DATE(r.created_at) AS publication,
    r.reply_date IS NOT NULL AND DATE(r.reply_date) < DATE "2026-08-11" AS repondu_avant_suivi,
    n.a_un_nom,
    CASE
      WHEN DATE(r.created_at) >= DATE "2026-08-11"                         THEN "pendant"
      WHEN DATE_DIFF(DATE "2026-08-11", DATE(r.created_at), DAY) <= 30   THEN "m30j"
      WHEN DATE_DIFF(DATE "2026-08-11", DATE(r.created_at), DAY) <= 90   THEN "30_90j"
      WHEN DATE_DIFF(DATE "2026-08-11", DATE(r.created_at), DAY) <= 365  THEN "90_365j"
      WHEN DATE_DIFF(DATE "2026-08-11", DATE(r.created_at), DAY) <= 1095 THEN "1_3ans"
      ELSE "p3ans"
    END AS age
  FROM `client-divers.reviewflowz.reviews_doublons_cleaned_all` r
  LEFT JOIN noms n USING (review_id)
),

fiche AS (
  SELECT
    cid,
    COUNT(*)                                                     AS avis,
    COUNTIF(supprime)                                            AS suppressions,
    COUNTIF(a_un_nom IS NOT NULL)                                AS avis_45_texte,
    COUNTIF(a_un_nom)                                            AS avis_avec_nom,
    COUNTIF(publication BETWEEN DATE "2025-08-11" AND DATE "2026-08-10") / 12
                                                                 AS velocite_mois,
    COUNTIF(publication BETWEEN DATE "2025-08-11" AND DATE "2026-08-10")
                                                                 AS avis_annee_avant,
    COUNTIF(publication BETWEEN DATE "2025-08-11" AND DATE "2026-08-10" AND repondu_avant_suivi)
                                                                 AS repondus_annee_avant,
    COUNTIF(star <= 2) / COUNT(*)                                AS part_1_2_etoiles,
    COUNTIF(publication >= DATE "2026-07-12")                    AS avis_recents,
    COUNTIF(publication >= DATE "2026-07-12" AND supprime)       AS supp_recents,
    COUNTIF(age = "pendant") AS avis_pendant, COUNTIF(age = "pendant" AND supprime) AS supp_pendant,
    COUNTIF(age = "m30j")    AS avis_m30j,    COUNTIF(age = "m30j" AND supprime)    AS supp_m30j,
    COUNTIF(age = "30_90j")  AS avis_30_90j,  COUNTIF(age = "30_90j" AND supprime)  AS supp_30_90j,
    COUNTIF(age = "90_365j") AS avis_90_365j, COUNTIF(age = "90_365j" AND supprime) AS supp_90_365j,
    COUNTIF(age = "1_3ans")  AS avis_1_3ans,  COUNTIF(age = "1_3ans" AND supprime)  AS supp_1_3ans,
    COUNTIF(age = "p3ans")   AS avis_p3ans,   COUNTIF(age = "p3ans" AND supprime)   AS supp_p3ans
  FROM avis
  GROUP BY cid
)

SELECT
  f.*,
  CASE WHEN f.suppressions > 10 THEN "11 et plus" WHEN f.suppressions >= 1 THEN "1 à 10"
       ELSE "aucune" END                                         AS categorie,
  SAFE_DIVIDE(f.avis_avec_nom, f.avis_45_texte)                  AS part_noms,
  CASE WHEN f.avis_annee_avant < 10 THEN "inconnue"
       WHEN f.repondus_annee_avant / f.avis_annee_avant > 0.75 THEN "plus de 75 %"
       ELSE "75 % ou moins" END                                  AS habitude,
  CASE WHEN f.cid IN ("3163466139043001754", "10346942689164695031") THEN "salles_espagnoles"
       WHEN s.cid IS NOT NULL THEN "chaines_antiparasitaires"
       ELSE "autres" END                                         AS groupe,
  b.industry                                                     AS secteur,
  IF(b.country = "US", "US", "Europe")                           AS region,
  b.bucket                                                       AS taille
FROM fiche f
LEFT JOIN `client-divers.reviewflowz.businesses` b USING (cid)
LEFT JOIN `client-divers.reviewflowz.biz_surveillance` s USING (cid)
