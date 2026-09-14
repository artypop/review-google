-- ============================================================================
-- Contrôle A — les suppressions certaines écartées par HAVING COUNT(*) = 1
--
-- Pourquoi ce contrôle existe
-- ---------------------------
-- `01_selection_panel.sql` ne garde que les avis ayant exactement une ligne
-- dans `reviews`. Ce n'est pas un dédoublonnage : c'est une exclusion. Sur la
-- fenêtre du panel (13 mai -> 16 août), il écarte 731 avis sur 226 488.
--
-- Parmi ces 731, deux familles :
--   A. 74 avis qui ont disparu et ne sont JAMAIS revenus. Toutes leurs lignes
--      portent une date de disparition. Ce sont des suppressions certaines :
--      la règle des 2 jours n'a rien à corriger chez eux. Le panel les perd.
--   B. 135 avis qui ont disparu PUIS sont revenus. Traités dans le contrôle B.
--
-- Le filtre écarte 0,3 % des avis mais au moins 2,8 % des suppressions. Il
-- trie donc en partie sur le résultat qu'on cherche à prédire.
--
-- Ce fichier sert à regarder ces avis un par un, pour décider s'il s'agit de
-- vraies suppressions ou de défauts du robot de collecte.
--
-- Les colonnes `text`, `reviewer_name` et `review_link` sont des données
-- personnelles : à lire à l'écran, jamais à exporter.
-- ============================================================================


-- ---------------------------------------------------------------------------
-- REQUÊTE 1 — Triage. Les 731 écartés, rangés par motif.
--             À lancer en premier : elle donne la vue d'ensemble.
-- ---------------------------------------------------------------------------
WITH fenetre AS (
  SELECT *
  FROM `client-divers`.reviewflowz.reviews
  WHERE CAST(created_at AS DATE) BETWEEN "2026-05-13" AND "2026-08-16"
),
par_avis AS (
  SELECT
    review_id,
    COUNT(*)                                                  AS n_lignes,
    COUNTIF(is_update)                                        AS n_lignes_edition,
    COUNTIF(deleted_detected_at IS NOT NULL)                  AS n_lignes_disparition,
    COUNTIF(deleted_detected_at IS NULL)                      AS n_lignes_presence,
    COUNT(DISTINCT CAST(deleted_detected_at AS DATE))         AS n_dates_disparition,
    COUNT(DISTINCT text)                                      AS n_textes,
    COUNT(DISTINCT star)                                      AS n_notes
  FROM fenetre
  GROUP BY review_id
)
SELECT
  CASE
    WHEN n_lignes_presence = 0                    THEN 'A. disparu, jamais revenu'
    WHEN n_lignes_disparition = 0                 THEN 'C. jamais disparu (doublon pur)'
    ELSE                                               'B. disparu puis revenu'
  END                                             AS famille,
  CASE WHEN n_lignes_edition > 0 THEN "avec ligne d'édition"
       ELSE "sans ligne d'édition" END           AS edition,
  CASE WHEN n_dates_disparition > 1 THEN 'plusieurs dates de disparition'
       ELSE 'une seule date de disparition' END   AS disparitions,
  CASE WHEN n_notes > 1 THEN 'la note a changé'
       ELSE 'note stable' END                     AS note,
  CASE WHEN n_textes > 1 THEN 'le texte a changé'
       ELSE 'texte stable' END                    AS texte,
  COUNT(*)                                        AS n_avis,
  MIN(n_lignes)                                   AS lignes_min,
  MAX(n_lignes)                                   AS lignes_max
FROM par_avis
WHERE n_lignes > 1
GROUP BY famille, edition, disparitions, note, texte
ORDER BY famille, n_avis DESC;


-- ---------------------------------------------------------------------------
-- REQUÊTE 2 — Les 74 suppressions certaines, une ligne par avis.
--             Résumé : combien de lignes, quoi a bougé, quelles dates.
-- ---------------------------------------------------------------------------
WITH fenetre AS (
  SELECT *
  FROM `client-divers`.reviewflowz.reviews
  WHERE CAST(created_at AS DATE) BETWEEN "2026-05-13" AND "2026-08-16"
),
par_avis AS (
  SELECT
    review_id,
    COUNT(*)                                          AS n_lignes,
    COUNTIF(is_update)                                AS n_lignes_edition,
    COUNTIF(deleted_detected_at IS NULL)              AS n_lignes_presence,
    COUNT(DISTINCT CAST(deleted_detected_at AS DATE)) AS n_dates_disparition,
    COUNT(DISTINCT text)                              AS n_textes,
    COUNT(DISTINCT star)                              AS n_notes,
    ANY_VALUE(cid)                                    AS cid,
    MIN(CAST(created_at AS DATE))                     AS depose_le,
    MIN(CAST(first_seen_at AS DATE))                  AS premiere_vue,
    MIN(CAST(deleted_detected_at AS DATE))            AS premiere_disparition,
    MAX(CAST(deleted_detected_at AS DATE))            AS derniere_disparition,
    STRING_AGG(DISTINCT CAST(star AS STRING) ORDER BY CAST(star AS STRING)) AS notes_vues,
    STRING_AGG(DISTINCT changed_fields)               AS champs_modifies
  FROM fenetre
  GROUP BY review_id
)
SELECT
  a.review_id,
  a.cid,
  b.name                                        AS fiche,
  b.country,
  a.n_lignes,
  a.n_lignes_edition,
  a.n_dates_disparition,
  a.n_notes,
  a.notes_vues,
  a.n_textes,
  a.champs_modifies,
  a.depose_le,
  a.premiere_vue,
  a.premiere_disparition,
  a.derniere_disparition,
  DATE_DIFF(a.premiere_disparition, a.depose_le, DAY)   AS jours_en_ligne,
  DATE_DIFF(a.derniere_disparition, a.premiere_disparition, DAY) AS etalement_des_disparitions
FROM par_avis a
LEFT JOIN `client-divers`.reviewflowz.businesses b ON a.cid = b.cid
WHERE a.n_lignes > 1
  AND a.n_lignes_presence = 0          -- jamais revu en ligne
ORDER BY a.n_lignes DESC, a.review_id;


-- ---------------------------------------------------------------------------
-- REQUÊTE 3 — Les mêmes 74 avis, mais ligne par ligne.
--             Chaque enregistrement du robot, dans l'ordre où il l'a écrit.
--             C'est ici qu'on voit le comportement du crawler.
-- ---------------------------------------------------------------------------
WITH fenetre AS (
  SELECT *
  FROM `client-divers`.reviewflowz.reviews
  WHERE CAST(created_at AS DATE) BETWEEN "2026-05-13" AND "2026-08-16"
),
cibles AS (
  SELECT review_id
  FROM fenetre
  GROUP BY review_id
  HAVING COUNT(*) > 1 AND COUNTIF(deleted_detected_at IS NULL) = 0
)
SELECT
  f.review_id,
  f.id                                    AS ligne_id,
  f.is_update,
  f.changed_fields,
  f.star,
  SUBSTR(f.text, 1, 120)                  AS debut_du_texte,
  LENGTH(f.text)                          AS longueur_texte,
  f.n_photos,
  f.reviewer_review_count,
  f.local_guide_level,
  f.reply_text IS NOT NULL                AS a_une_reponse,
  CAST(f.created_at AS DATE)              AS depose_le,
  CAST(f.updated_at AS DATE)              AS modifie_le,
  CAST(f.first_seen_at AS DATE)           AS vu_pour_la_1ere_fois,
  CAST(f.last_seen_at AS DATE)            AS vu_pour_la_derniere_fois,
  CAST(f.deleted_detected_at AS DATE)     AS disparu_le
FROM fenetre f
JOIN cibles USING (review_id)
ORDER BY f.review_id, f.first_seen_at, f.id;
