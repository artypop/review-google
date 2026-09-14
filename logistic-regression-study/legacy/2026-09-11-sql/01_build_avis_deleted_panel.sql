-- ============================================================================
-- Table de panel pour la régression logistique.
--
-- Une ligne = un avis, à une vague où il est encore en ligne. La colonne
-- `deleted` vaut 1 la vague où l'avis disparaît pour de bon, 0 avant. Une
-- fois qu'un avis a une ligne à 1, il n'a plus aucune ligne après : le 1 ne
-- redevient jamais 0, et il ne se répète pas non plus.
--
-- Pourquoi une correction est nécessaire avant de compter une "suppression" :
-- `deleted_detected_at`, dans la table brute, veut seulement dire que notre
-- robot ne retrouve plus l'avis à une vague. Ce n'est pas Google qui annonce
-- une suppression, c'est nous qui en déduisons une parce que l'avis n'est
-- plus dans ce que le robot a vu. Deux situations font que cette déduction
-- est fausse :
--
--   1. Bug d'édition (24 avis identifiés) : le même auteur, la même note,
--      la même date de dépôt, mais un texte totalement différent d'une
--      ligne à l'autre. C'est une modification d'avis mal enregistrée par
--      le robot, pas une suppression suivie d'un retour.
--
--   2. Raté de collecte (avis absent un seul jour) : sur les avis qui
--      disparaissent puis reviennent avec un texte identique, 71 % sont
--      absents un seul jour avant de réapparaître. Un vrai retrait revu par
--      Google après contestation prend en général plusieurs jours, pas
--      vingt-quatre heures. Ces cas-là sont donc traités comme des ratés du
--      robot, pas comme de vraies suppressions.
--
-- Les avis qui disparaissent 2 jours ou plus avant de revenir restent
-- comptés comme supprimés, à la date de leur première disparition : c'est
-- le signal le plus intéressant pour l'étude, celui d'un avis que Google a
-- réellement retiré puis remis en ligne.
-- ============================================================================

CREATE OR REPLACE TABLE `client-divers`.reviewflowz.avis_deleted_panel AS

-- Une ligne par enregistrement de base (on écarte les lignes d'édition, qui
-- ne concernent que 2 012 avis et dupliqueraient le compte).
WITH base AS (
  SELECT review_id, cid, star, text, created_at, first_seen_at, last_seen_at, deleted_detected_at
  FROM `client-divers`.reviewflowz.reviews
  WHERE NOT is_update
),

-- Pour chaque avis (identifié par review_id) : a-t-on vu une disparition, a-t-on
-- vu un retour, et combien de textes différents porte-t-il au total ?
flags AS (
  SELECT
    review_id,
    LOGICAL_OR(deleted_detected_at IS NOT NULL) AS a_disparu,
    LOGICAL_OR(deleted_detected_at IS NULL)     AS a_un_retour,
    COUNT(DISTINCT text)                        AS n_textes
  FROM base
  GROUP BY review_id
),

-- Avis disparus puis revenus, texte identique ou absent des deux côtés
-- (donc PAS les 24 cas de bug d'édition, qui ont deux textes différents).
resurrected AS (
  SELECT review_id FROM flags WHERE a_disparu AND a_un_retour AND n_textes <= 1
),

-- Les 24 cas confirmés de bug d'édition : à exclure des suppressions, quelle
-- que soit la durée de l'écart entre les deux lignes.
edit_bugs AS (
  SELECT review_id FROM flags WHERE a_disparu AND a_un_retour AND n_textes = 2
),

-- Pour chaque avis, la date à laquelle il a été revu en ligne (première
-- vague, parmi celles où il est présent, qui suit sa disparition).
retours AS (
  SELECT review_id, MIN(first_seen_at) AS reapparu_le
  FROM base
  WHERE deleted_detected_at IS NULL
  GROUP BY review_id
),

-- Chaque disparition d'un avis "resurrected", associée à sa date de retour.
instances AS (
  SELECT b.review_id, b.deleted_detected_at, ret.reapparu_le
  FROM base b
  JOIN resurrected res USING (review_id)
  JOIN retours ret USING (review_id)
  WHERE b.deleted_detected_at IS NOT NULL
),

-- Parmi ces disparitions, celles qui ont duré 2 jours ou plus : on les garde
-- comme une vraie suppression, à la date de la première d'entre elles.
mort_reelle AS (
  SELECT review_id, MIN(deleted_detected_at) AS death_at
  FROM instances
  WHERE TIMESTAMP_DIFF(reapparu_le, deleted_detected_at, DAY) >= 2
  GROUP BY review_id
),

-- Une ligne par avis, en fusionnant ses éventuels enregistrements multiples.
-- `created_at` : vraie date de publication (donnée par Google).
-- `first_seen_at` : date où NOTRE robot l'a vu pour la première fois — pour
--   un avis déjà en ligne avant le 11 août, c'est la date du premier passage,
--   pas sa vraie date de publication.
canon AS (
  SELECT
    review_id,
    ANY_VALUE(cid) AS cid,
    MIN(first_seen_at) AS first_seen_at,
    MIN(created_at) AS created_at,
    MAX(deleted_detected_at) AS raw_deleted_at  -- MAX ignore déjà les valeurs vides tout seul
  FROM base
  GROUP BY review_id
),

-- La date de suppression corrigée, avis par avis.
reviews_corriges AS (
  SELECT
    c.review_id, c.cid, c.first_seen_at, c.created_at,
    CASE
      WHEN eb.review_id IS NOT NULL THEN NULL          -- bug d'édition : jamais supprimé
      WHEN res.review_id IS NOT NULL THEN mr.death_at  -- ressuscité : date corrigée (NULL si simple raté)
      ELSE c.raw_deleted_at                            -- cas normal : la date telle quelle
    END AS death_at
  FROM canon c
  LEFT JOIN edit_bugs eb USING (review_id)
  LEFT JOIN resurrected res USING (review_id)
  LEFT JOIN mort_reelle mr USING (review_id)
),

-- La vague pendant laquelle la suppression corrigée a été détectée.
avec_vague_de_mort AS (
  SELECT r.review_id, r.cid, r.first_seen_at, r.created_at, r.death_at,
    (SELECT MAX(w2.wave) FROM `client-divers.reviewflowz.waves` w2
     WHERE w2.started_at <= r.death_at) AS death_wave
  FROM reviews_corriges r
)

-- Le tableau final : une ligne par avis et par vague où il est encore en vie.
-- On part de la vague 2 : la vague 1 est le premier passage, celui qui
-- découvre tous les avis existants, donc il n'y a rien à comparer avant elle.
SELECT
  r.review_id,
  r.cid,
  w.wave,
  COALESCE(r.death_wave = w.wave, FALSE) AS deleted,

  -- Vélocité 1 : jours en ligne avant suppression, depuis la vraie date de
  -- publication (Google). Vide si l'avis n'est jamais supprimé.
  CASE WHEN r.death_at IS NOT NULL
       THEN TIMESTAMP_DIFF(r.death_at, r.created_at, DAY)
  END AS jours_en_ligne_avant_suppression,

  -- Vélocité 2 : jours sous surveillance avant suppression, depuis le
  -- premier passage de NOTRE robot. Identique à la première colonne pour un
  -- avis posté pendant le suivi ; plus courte pour un avis déjà ancien au
  -- démarrage, puisqu'on ne le surveille que depuis le 11 août.
  CASE WHEN r.death_at IS NOT NULL
       THEN TIMESTAMP_DIFF(r.death_at, r.first_seen_at, DAY)
  END AS jours_sous_surveillance_avant_suppression

FROM avec_vague_de_mort r
JOIN `client-divers`.reviewflowz.waves w
  ON w.wave >= 2
  AND r.first_seen_at < w.started_at
  AND (r.death_wave IS NULL OR w.wave <= r.death_wave)
ORDER BY r.review_id, w.wave;