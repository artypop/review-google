-- ============================================================================
-- 2.2. Les deux phénomènes, en chiffres — base complète
--
-- Groupes :
--   chaines_antiparasitaires  les 93 fiches des 4 chaînes US de `biz_surveillance`
--   salles_espagnoles         les 2 salles de sport attaquées, repérées par leur cid
-- Base : `reviews_doublons_cleaned_all`, toutes dates de publication. Les
-- suppressions ont toutes été constatées du 12 au 24 août 2026.
-- `delai` = jours entre la publication de l'avis et la constatation de sa
-- disparition.
-- Une ligne par enseigne, puis une ligne « total » par groupe.
-- ============================================================================

WITH avis AS (
  SELECT
    IF(r.cid IN ("3163466139043001754", "10346942689164695031"),
       "salles_espagnoles", "chaines_antiparasitaires") AS groupe,
    s.name AS enseigne,
    r.cid,
    r.star,
    DATE(r.created_at) AS jour_publication,
    r.deleted_detected_at IS NOT NULL AS supprime,
    DATE_DIFF(DATE(r.deleted_detected_at), DATE(r.created_at), DAY) AS delai
  FROM `client-divers.reviewflowz.reviews_doublons_cleaned_all` r
  JOIN `client-divers.reviewflowz.biz_surveillance` s USING (cid)
)

SELECT
  groupe,
  enseigne_vue                                          AS enseigne,
  COUNT(DISTINCT cid)                                   AS fiches,
  COUNT(*)                                              AS avis,
  COUNTIF(supprime)                                     AS suppressions,
  COUNTIF(supprime AND star = 5)                        AS suppressions_5_etoiles,
  COUNTIF(supprime AND star = 4)                        AS suppressions_4_etoiles,
  COUNTIF(supprime AND star <= 3 AND star >= 2)         AS suppressions_2_3_etoiles,
  COUNTIF(supprime AND star = 1)                        AS suppressions_1_etoile,
  COUNTIF(supprime AND jour_publication >= DATE "2026-08-04")
                                                        AS suppressions_avis_publies_depuis_j_moins_7,
  COUNTIF(supprime AND delai BETWEEN 1 AND 5)           AS suppressions_a_1_5_jours,
  COUNTIF(supprime AND delai BETWEEN 6 AND 7)           AS suppressions_a_6_7_jours,
  COUNTIF(supprime AND delai BETWEEN 8 AND 30)          AS suppressions_a_8_30_jours,
  COUNTIF(supprime AND delai > 30)                      AS suppressions_a_plus_de_30_jours
FROM avis, UNNEST([enseigne, "total"]) AS enseigne_vue
GROUP BY groupe, enseigne
ORDER BY groupe, enseigne = "total", suppressions DESC
