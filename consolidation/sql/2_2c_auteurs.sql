-- ============================================================================
-- 2.2c. Qui a écrit les avis supprimés ? Comparaison avec les avis conservés
--
-- Avis publiés de J-30 à J+13 (12 juillet au 24 août 2026), base complète.
-- Quatre groupes :
--   chaines_antiparasitaires   les 93 fiches des 4 chaînes US
--   autres_fiches_us           toutes les autres fiches américaines
--   salles_espagnoles          les 2 salles attaquées
--   autres_fiches_europe       toutes les autres fiches européennes
-- Pour chaque caractéristique de l'auteur, la répartition des avis supprimés
-- et celle des avis conservés, en nombre et en part du groupe.
--
-- Caractéristiques, telles que le robot les a lues au dernier passage :
--   niveau Local Guide ; photos publiées par l'auteur sur son profil ; nombre
--   d'avis déclaré par l'auteur ; avis publiés par le même auteur le même jour
--   sur les fiches du panel ; réponse du propriétaire présente au dernier
--   passage où l'avis a été vu ; note.
-- ============================================================================

WITH meme_jour AS (
  SELECT review_link, DATE(created_at) AS jour, COUNT(*) AS n
  FROM `client-divers.reviewflowz.reviews_doublons_cleaned`
  WHERE review_link IS NOT NULL
  GROUP BY review_link, jour
),

avis AS (
  SELECT
    CASE
      WHEN r.cid IN ("3163466139043001754", "10346942689164695031") THEN "salles_espagnoles"
      WHEN s.cid IS NOT NULL                                        THEN "chaines_antiparasitaires"
      WHEN b.country = "US"                                         THEN "autres_fiches_us"
      ELSE                                                               "autres_fiches_europe"
    END AS groupe,
    r.deleted_detected_at IS NOT NULL AS supprime,
    r.star,
    r.local_guide_level,
    COALESCE(r.reviewer_photo_count, 0) AS photos_auteur,
    r.reviewer_review_count,
    COALESCE(mj.n, 1) AS avis_meme_jour,
    r.reply_date IS NOT NULL AS reponse
  FROM `client-divers.reviewflowz.reviews_doublons_cleaned` r
  LEFT JOIN `client-divers.reviewflowz.businesses` b USING (cid)
  LEFT JOIN `client-divers.reviewflowz.biz_surveillance` s USING (cid)
  LEFT JOIN meme_jour mj
    ON mj.review_link = r.review_link AND mj.jour = DATE(r.created_at)
  WHERE DATE(r.created_at) BETWEEN DATE "2026-07-12" AND DATE "2026-08-24"
),

modalites AS (
  SELECT groupe, supprime, m.caracteristique, m.ordre, m.modalite
  FROM avis, UNNEST([
    STRUCT("1. note" AS caracteristique, 6 - star AS ordre,
           CONCAT(CAST(star AS STRING), " étoile(s)") AS modalite),
    STRUCT("2. niveau Local Guide",
           CASE WHEN local_guide_level IS NULL THEN 1 WHEN local_guide_level <= 3 THEN 2 ELSE 3 END,
           CASE WHEN local_guide_level IS NULL THEN "sans niveau"
                WHEN local_guide_level <= 3 THEN "niveau 1 à 3" ELSE "niveau 4 et plus" END),
    STRUCT("3. photos publiées par l'auteur",
           CASE WHEN photos_auteur = 0 THEN 1 WHEN photos_auteur <= 5 THEN 2
                WHEN photos_auteur <= 20 THEN 3 WHEN photos_auteur <= 100 THEN 4 ELSE 5 END,
           CASE WHEN photos_auteur = 0 THEN "0" WHEN photos_auteur <= 5 THEN "1 à 5"
                WHEN photos_auteur <= 20 THEN "6 à 20" WHEN photos_auteur <= 100 THEN "21 à 100"
                ELSE "plus de 100" END),
    STRUCT("4. avis déclarés par l'auteur",
           CASE WHEN reviewer_review_count IS NULL THEN 6 WHEN reviewer_review_count <= 1 THEN 1
                WHEN reviewer_review_count <= 5 THEN 2 WHEN reviewer_review_count <= 20 THEN 3
                WHEN reviewer_review_count <= 100 THEN 4 ELSE 5 END,
           CASE WHEN reviewer_review_count IS NULL THEN "inconnu" WHEN reviewer_review_count <= 1 THEN "1"
                WHEN reviewer_review_count <= 5 THEN "2 à 5" WHEN reviewer_review_count <= 20 THEN "6 à 20"
                WHEN reviewer_review_count <= 100 THEN "21 à 100" ELSE "plus de 100" END),
    STRUCT("5. avis du même auteur le même jour, sur le panel",
           CASE WHEN avis_meme_jour = 1 THEN 1 WHEN avis_meme_jour <= 3 THEN 2 ELSE 3 END,
           CASE WHEN avis_meme_jour = 1 THEN "1" WHEN avis_meme_jour <= 3 THEN "2 ou 3"
                ELSE "4 et plus" END),
    STRUCT("6. réponse du propriétaire", IF(reponse, 1, 2), IF(reponse, "oui", "non"))
  ]) AS m
)

SELECT
  groupe,
  caracteristique,
  ordre,
  modalite,
  COUNTIF(supprime)                                                         AS supprimes_avis,
  ROUND(100 * COUNTIF(supprime)
        / SUM(COUNTIF(supprime)) OVER (PARTITION BY groupe, caracteristique), 1)
                                                                            AS supprimes_part_pct,
  COUNTIF(NOT supprime)                                                     AS conserves_avis,
  ROUND(100 * COUNTIF(NOT supprime)
        / SUM(COUNTIF(NOT supprime)) OVER (PARTITION BY groupe, caracteristique), 1)
                                                                            AS conserves_part_pct
FROM modalites
GROUP BY groupe, caracteristique, ordre, modalite
ORDER BY groupe, caracteristique, ordre
