-- Délai entre la publication d'un avis et sa disparition, avis publiés du
-- 11 au 17 août 2026.
--
-- Lecture seule. Ne crée aucune table.
--
-- Ce que compte chaque ligne
-- --------------------------
--   perimetre       `complet` = tous les avis ; `sans_enseignes` = les avis
--                   des fiches qui n'appartiennent à aucune des six enseignes.
--   jour_creation   la date de publication de l'avis.
--   delai_j         le nombre de jours entre la publication et la date à
--                   laquelle le robot ne l'a plus vu. NULL = l'avis était
--                   encore en ligne au dernier passage, le 24 août.
--   avis            le nombre d'avis dans la case. Une ligne = un avis.
--
-- La somme des lignes d'une même journée, `delai_j` NULL compris, donne le
-- nombre d'avis publiés ce jour-là.
--
-- Suppression = `deleted_detected_at` renseigné
-- --------------------------------------------
-- Sans la règle des deux jours d'absence utilisée ailleurs dans le projet.
-- Même justification que `sql/02_adding_features.sql:169` : le filtre
-- `HAVING COUNT(*) = 1` ci-dessous a déjà écarté tout avis disparu puis revenu,
-- donc il ne reste aucune résurrection à trier.
--
-- Durée d'observation inégale
-- ---------------------------
-- Le dernier passage du robot est le 24 août. Un avis du 11 août a donc été
-- observé 13 jours, un avis du 17 août seulement 7. Les colonnes J+8 et
-- au-delà sont incomplètes pour les dernières journées de publication.
--
-- Le paramètre @cid_exclus
-- ------------------------
-- Les `cid` des six enseignes : les succursales des quatre chaînes
-- antiparasitaires, lues dans `businesses` par `lancer.py`, et les deux fiches
-- de salle de sport attaquées, écrites en dur.

WITH avis_a_un_seul_enregistrement AS (
  SELECT review_id
  FROM `client-divers`.reviewflowz.reviews
  GROUP BY review_id
  HAVING COUNT(*) = 1
),

base AS (
  SELECT
    CAST(r.created_at AS DATE)                AS jour_creation,
    DATE_DIFF(CAST(r.deleted_detected_at AS DATE),
              CAST(r.created_at AS DATE), DAY) AS delai_j,
    r.cid IN UNNEST(@cid_exclus)              AS enseigne_signalee
  FROM `client-divers`.reviewflowz.reviews AS r
  JOIN avis_a_un_seul_enregistrement USING (review_id)
  WHERE CAST(r.created_at AS DATE)
        BETWEEN DATE "2026-08-11" AND DATE "2026-08-17"
),

-- Un avis d'enseigne signalée ne compte que dans le périmètre complet.
par_perimetre AS (
  SELECT b.* EXCEPT (enseigne_signalee), perimetre
  FROM base AS b,
       UNNEST(IF(b.enseigne_signalee, ["complet"], ["complet", "sans_enseignes"]))
         AS perimetre
)

SELECT
  perimetre,
  jour_creation,
  delai_j,
  COUNT(*) AS avis
FROM par_perimetre
GROUP BY perimetre, jour_creation, delai_j
ORDER BY perimetre, jour_creation, delai_j NULLS LAST;
