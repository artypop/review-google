-- Passage 1 : les effectifs seuls, aucun taux.
--
-- Lecture seule. Ne crée aucune table.
--
-- Ce que compte chaque ligne
-- --------------------------
--   avis          les avis du panel publiés du 11 au 16 août 2026 portant cette
--                 note, dans cette zone et ce périmètre. Une ligne du panel est
--                 un avis.
--   supprimes_8j  ceux d'entre eux que le robot n'a plus vus au plus tard
--                 8 jours après leur publication.
--
-- Pourquoi 8 jours
-- ----------------
-- Le dernier passage du robot est le 24 août. Un avis publié le 16 août n'a donc
-- pu être observé que 8 jours, un avis du 11 août en a été observé 13. Couper à
-- 8 jours pour tous donne à chaque avis la même chance d'être vu disparaître.
-- Une suppression survenue au 10e jour de vie est ici comptée comme une absence
-- de suppression.
--
-- Pourquoi `ne_pendant_la_surveillance`
-- ------------------------------------
-- Cette colonne vaut `created_at_day >= 2026-08-11`, et `sql/01_selection_panel.sql`
-- arrête le corpus au 16 août en publication. Elle donne donc exactement les
-- avis publiés pendant les six premières journées de suivi.
--
-- Le paramètre @cid_gym
-- ---------------------
-- Les fiches de salle de sport attaquées, repérées par leur `cid`. Le flag
-- `salle_de_sport_attaquee` de la table marque sur le nom de l'enseigne et
-- retient 13 fiches pour 2 attaquées : il ne sert pas ici. Voir
-- `controle_cid_fiches_attaquees.sql`.
--
-- `chaine_antiparasitaire_us` garde son repérage par nom : `docs/02-donnees.md`
-- § 4 le juge correct, toutes les succursales étant recherchées.
--
-- La ligne où `star` est vide est le total de la zone et du périmètre.

WITH base AS (
  SELECT
    star,
    region,
    -- `age_a_la_suppression_j` est NULL pour un avis resté en ligne : COALESCE
    -- le ramène à FALSE plutôt que de laisser un NULL se propager dans COUNTIF.
    COALESCE(supprime AND age_a_la_suppression_j <= 8, FALSE) AS supprime_8j,
    (chaine_antiparasitaire_us OR cid IN UNNEST(@cid_gym))    AS enseigne_signalee
  FROM `client-divers`.reviewflowz.reviews_panel_features
  WHERE ne_pendant_la_surveillance
),

-- Chaque avis compte dans sa zone et dans « les_deux ».
par_zone AS (
  SELECT b.* EXCEPT (region), zone
  FROM base AS b, UNNEST([b.region, "les_deux"]) AS zone
),

-- Un avis d'enseigne signalée ne compte que dans le périmètre complet.
par_perimetre AS (
  SELECT z.* EXCEPT (enseigne_signalee), perimetre
  FROM par_zone AS z,
       UNNEST(IF(z.enseigne_signalee, ["complet"], ["complet", "sans_enseignes"]))
         AS perimetre
)

SELECT
  perimetre,
  zone,
  star,
  COUNT(*)              AS avis,
  COUNTIF(supprime_8j)  AS supprimes_8j
FROM par_perimetre
GROUP BY GROUPING SETS ((perimetre, zone, star), (perimetre, zone))
ORDER BY perimetre, zone, star NULLS FIRST;
