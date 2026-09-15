-- Passage 2 : la part supprimée de chaque note.
--
-- Lecture seule. Ne crée aucune table.
--
-- Même population et même fenêtre que `01_effectifs.sql`, dont l'en-tête porte
-- le détail : avis du panel publiés du 11 au 16 août 2026, disparition comptée
-- dans les 8 jours qui suivent la publication de l'avis.
--
-- Ce que compte chaque ligne
-- --------------------------
--   avis                les avis de cette note, dans cette zone et ce périmètre
--   supprimes_8j        ceux d'entre eux disparus au plus tard 8 jours après
--                       leur publication
--   part_supprimee_pct  `supprimes_8j / avis`, en pourcentage. Le dénominateur
--                       est la colonne `avis` de la même ligne.
--   rr_vs_5_etoiles     part_supprimee_pct de la ligne, divisée par celle des
--                       5 étoiles de la même zone et du même périmètre.
--                       « 2,0 » se lit : deux fois plus supprimé qu'un avis
--                       5 étoiles du même marché.
--   citable             faux si la case tombe sous 300 avis ou sous
--                       10 suppressions. Une case non citable garde ses
--                       valeurs dans ce fichier et ne sort nulle part ailleurs.
--
-- La ligne où `star` est vide est le total de la zone et du périmètre.

WITH base AS (
  SELECT
    star,
    region,
    COALESCE(supprime AND age_a_la_suppression_j <= 8, FALSE) AS supprime_8j,
    (chaine_antiparasitaire_us OR cid IN UNNEST(@cid_gym))    AS enseigne_signalee
  FROM `client-divers`.reviewflowz.reviews_panel_features
  WHERE ne_pendant_la_surveillance
),

par_zone AS (
  SELECT b.* EXCEPT (region), zone
  FROM base AS b, UNNEST([b.region, "les_deux"]) AS zone
),

par_perimetre AS (
  SELECT z.* EXCEPT (enseigne_signalee), perimetre
  FROM par_zone AS z,
       UNNEST(IF(z.enseigne_signalee, ["complet"], ["complet", "sans_enseignes"]))
         AS perimetre
),

agrege AS (
  SELECT
    perimetre,
    zone,
    star,
    COUNT(*)              AS avis,
    COUNTIF(supprime_8j)  AS supprimes_8j
  FROM par_perimetre
  GROUP BY GROUPING SETS ((perimetre, zone, star), (perimetre, zone))
)

SELECT
  perimetre,
  zone,
  star,
  avis,
  supprimes_8j,
  ROUND(supprimes_8j / avis * 100, 2) AS part_supprimee_pct,
  -- Part des 5 étoiles de la même zone et du même périmètre, prise comme point
  -- de comparaison. La ligne de total et la ligne des 5 étoiles la reçoivent
  -- aussi : la seconde vaut 1 par construction.
  ROUND(SAFE_DIVIDE(
          supprimes_8j / avis,
          MAX(IF(star = 5, supprimes_8j / avis, NULL))
            OVER (PARTITION BY perimetre, zone)), 2) AS rr_vs_5_etoiles,
  (avis >= 300 AND supprimes_8j >= 10)               AS citable
FROM agrege
ORDER BY perimetre, zone, star NULLS FIRST;
