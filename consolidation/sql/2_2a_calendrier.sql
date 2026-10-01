-- ============================================================================
-- 2.2a. Date de publication et vague de suppression des avis supprimés
--
-- Mêmes groupes et même base que `2_2_resume.sql`. Seuls les avis supprimés.
-- Une ligne = un couple (jour de publication, vague de suppression) pour une
-- enseigne et une note, avec le nombre d'avis supprimés.
--
-- Vague : numéro du passage du robot où l'avis manque pour la première fois.
-- Un passage par jour, du 11 août (vague 1) au 24 août (vague 14) : une
-- suppression constatée le 12 août est en vague 2.
-- ============================================================================

SELECT
  IF(r.cid IN ("3163466139043001754", "10346942689164695031"),
     "salles_espagnoles", "chaines_antiparasitaires") AS groupe,
  s.name                                            AS enseigne,
  DATE(r.created_at)                                AS jour_publication,
  DATE_DIFF(DATE(r.deleted_detected_at), DATE "2026-08-11", DAY) + 1
                                                    AS vague_suppression,
  r.star                                            AS note,
  COUNT(*)                                          AS avis_supprimes
FROM `client-divers.reviewflowz.reviews_doublons_cleaned_all` r
JOIN `client-divers.reviewflowz.biz_surveillance` s USING (cid)
WHERE r.deleted_detected_at IS NOT NULL
GROUP BY groupe, enseigne, jour_publication, vague_suppression, note
ORDER BY groupe, enseigne, jour_publication, vague_suppression, note
