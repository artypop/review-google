-- ============================================================================
-- 2.2f. Avis publiés et avis supprimés, par jour de publication, sur les fiches
-- des deux phénomènes
--
-- Mêmes groupes que `2_2a_calendrier.sql` : les fiches de `biz_surveillance`,
-- les 2 salles espagnoles repérées par leur cid, les autres étant les 4 chaînes
-- antiparasitaires américaines. Base complète `reviews_doublons_cleaned_all`.
--
-- Avis publiés du 1er juillet au 23 août 2026. Une ligne par groupe, jour de
-- publication et classe de note : avis publiés, avis supprimés pendant le suivi
-- (du 12 au 24 août).
--
-- Un avis publié avant le 11 août et supprimé avant le 11 août n'est pas dans
-- la base : pour ces jours, les publications sont sous-comptées.
-- ============================================================================

SELECT
  IF(r.cid IN ("3163466139043001754", "10346942689164695031"),
     "salles_espagnoles", "chaines_antiparasitaires") AS groupe,
  DATE(r.created_at)                                AS jour_publication,
  CASE r.star WHEN 1 THEN "1 étoile" WHEN 5 THEN "5 étoiles" ELSE "2 à 4 étoiles" END
                                                    AS classe,
  COUNT(*)                                          AS avis_publies,
  COUNTIF(r.deleted_detected_at IS NOT NULL)        AS avis_supprimes
FROM `client-divers.reviewflowz.reviews_doublons_cleaned_all` r
JOIN `client-divers.reviewflowz.biz_surveillance` s USING (cid)
WHERE DATE(r.created_at) BETWEEN DATE "2026-07-01" AND DATE "2026-08-23"
GROUP BY groupe, jour_publication, classe
ORDER BY groupe, jour_publication, classe
