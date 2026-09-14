-- ============================================================================
-- Contrôle B — les avis disparus puis revenus, écartés par HAVING COUNT(*) = 1
--
-- Pourquoi ce contrôle existe
-- ---------------------------
-- Ce sont les 135 avis de la fenêtre du panel (13 mai -> 16 août) qui ont au
-- moins une ligne portant une date de disparition ET au moins une ligne sans.
-- Le robot les a donc perdus de vue, puis retrouvés.
--
-- C'est exactement la population sur laquelle repose la règle de comptage du
-- projet : absent 1 jour = raté de collecte, absent 2 jours ou plus = vraie
-- suppression suivie d'un retour. Voir `../../CLAUDE.md`, point 4.
--
-- `01_selection_panel.sql` les écarte tous, sans distinguer les deux cas. La
-- règle des 2 jours n'est donc plus appliquée nulle part dans ce panel.
--
-- Ce fichier sert à juger, avis par avis, si le robot a bugué ou si Google a
-- réellement retiré puis remis l'avis.
--
-- ATTENTION à la façon de mesurer l'écart. Les deux moteurs ne comptent pas
-- pareil, et 6 avis du corpus complet basculent d'un côté à l'autre selon la
-- convention :
--   DATE_DIFF(..., DAY) sur des DATE  -> compte les passages de minuit
--   TIMESTAMP_DIFF(..., HOUR) / 24    -> compte la durée réelle
-- Les deux sont calculées ci-dessous, côte à côte.
--
-- Les colonnes `text` et `review_link` sont des données personnelles : à lire
-- à l'écran, jamais à exporter.
-- ============================================================================


-- ---------------------------------------------------------------------------
-- REQUÊTE 1 — Une ligne par avis. Combien de temps a duré l'absence,
--             mesurée des deux façons, et qu'est-ce qui a changé entre les
--             deux passages.
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
  HAVING COUNT(*) > 1
     AND COUNTIF(deleted_detected_at IS NOT NULL) > 0
     AND COUNTIF(deleted_detected_at IS NULL)     > 0
),
-- Première date à laquelle le robot ne retrouve plus l'avis.
partis AS (
  SELECT review_id, MIN(deleted_detected_at) AS parti_le
  FROM fenetre JOIN cibles USING (review_id)
  WHERE deleted_detected_at IS NOT NULL
  GROUP BY review_id
),
-- Première date à laquelle il le revoit en ligne après cette disparition.
revenus AS (
  SELECT f.review_id, MIN(f.first_seen_at) AS revenu_le
  FROM fenetre f
  JOIN partis p ON f.review_id = p.review_id
  WHERE f.deleted_detected_at IS NULL
    AND f.first_seen_at > p.parti_le
  GROUP BY f.review_id
),
resume AS (
  SELECT
    review_id,
    ANY_VALUE(cid)                                    AS cid,
    COUNT(*)                                          AS n_lignes,
    COUNTIF(is_update)                                AS n_lignes_edition,
    COUNT(DISTINCT CAST(deleted_detected_at AS DATE)) AS n_disparitions,
    COUNT(DISTINCT text)                              AS n_textes,
    COUNT(DISTINCT star)                              AS n_notes,
    STRING_AGG(DISTINCT CAST(star AS STRING) ORDER BY CAST(star AS STRING)) AS notes_vues,
    MIN(CAST(created_at AS DATE))                     AS depose_le
  FROM fenetre JOIN cibles USING (review_id)
  GROUP BY review_id
)
SELECT
  r.review_id,
  r.cid,
  b.name                                              AS fiche,
  b.country,
  r.n_lignes,
  r.n_lignes_edition,
  r.n_disparitions,
  r.n_notes,
  r.notes_vues,
  r.n_textes,

  -- Le verdict de la règle du projet dépend de ces trois colonnes.
  CASE
    WHEN r.n_textes = 2 THEN "bug d'édition : deux textes différents"
    WHEN rv.revenu_le IS NULL THEN 'aucun retour daté après la disparition'
    ELSE "disparition puis retour à l'identique"
  END                                                 AS cas,

  r.depose_le,
  CAST(p.parti_le AS DATE)                            AS parti_le,
  CAST(rv.revenu_le AS DATE)                          AS revenu_le,

  -- Les deux conventions de mesure, côte à côte.
  DATE_DIFF(CAST(rv.revenu_le AS DATE), CAST(p.parti_le AS DATE), DAY)
                                                      AS absence_passages_de_minuit,
  TIMESTAMP_DIFF(rv.revenu_le, p.parti_le, HOUR)      AS absence_en_heures,
  TIMESTAMP_DIFF(rv.revenu_le, p.parti_le, HOUR) / 24.0
                                                      AS absence_en_jours_reels,

  -- Ce que chaque convention décide.
  DATE_DIFF(CAST(rv.revenu_le AS DATE), CAST(p.parti_le AS DATE), DAY) >= 2
                                                      AS supprime_selon_duckdb,
  TIMESTAMP_DIFF(rv.revenu_le, p.parti_le, HOUR) >= 48
                                                      AS supprime_selon_bigquery
FROM resume r
LEFT JOIN partis  p  ON r.review_id = p.review_id
LEFT JOIN revenus rv ON r.review_id = rv.review_id
LEFT JOIN `client-divers`.reviewflowz.businesses b ON r.cid = b.cid
ORDER BY absence_en_heures, r.review_id;


-- ---------------------------------------------------------------------------
-- REQUÊTE 2 — Combien d'avis de chaque côté du seuil, et où les deux
--             conventions ne sont pas d'accord.
-- ---------------------------------------------------------------------------
WITH fenetre AS (
  SELECT *
  FROM `client-divers`.reviewflowz.reviews
  WHERE CAST(created_at AS DATE) BETWEEN "2026-05-13" AND "2026-08-16"
),
cibles AS (
  SELECT review_id FROM fenetre GROUP BY review_id
  HAVING COUNT(*) > 1
     AND COUNTIF(deleted_detected_at IS NOT NULL) > 0
     AND COUNTIF(deleted_detected_at IS NULL)     > 0
),
partis AS (
  SELECT review_id, MIN(deleted_detected_at) AS parti_le
  FROM fenetre JOIN cibles USING (review_id)
  WHERE deleted_detected_at IS NOT NULL GROUP BY review_id
),
revenus AS (
  SELECT f.review_id, MIN(f.first_seen_at) AS revenu_le
  FROM fenetre f JOIN partis p ON f.review_id = p.review_id
  WHERE f.deleted_detected_at IS NULL AND f.first_seen_at > p.parti_le
  GROUP BY f.review_id
),
textes AS (
  SELECT review_id, COUNT(DISTINCT text) AS n_textes
  FROM fenetre JOIN cibles USING (review_id) GROUP BY review_id
)
SELECT
  CASE WHEN t.n_textes = 2 THEN "bug d'édition (exclu des suppressions)"
       WHEN rv.revenu_le IS NULL THEN 'pas de retour daté'
       WHEN TIMESTAMP_DIFF(rv.revenu_le, p.parti_le, HOUR) < 24 THEN 'absent moins de 24 h'
       WHEN TIMESTAMP_DIFF(rv.revenu_le, p.parti_le, HOUR) < 48 THEN 'absent 24 à 48 h'
       WHEN TIMESTAMP_DIFF(rv.revenu_le, p.parti_le, HOUR) < 72 THEN 'absent 48 à 72 h'
       ELSE 'absent plus de 72 h' END                 AS tranche_d_absence,
  COUNT(*)                                            AS n_avis,
  COUNTIF(DATE_DIFF(CAST(rv.revenu_le AS DATE), CAST(p.parti_le AS DATE), DAY) >= 2)
                                                      AS comptes_supprimes_par_duckdb,
  COUNTIF(TIMESTAMP_DIFF(rv.revenu_le, p.parti_le, HOUR) >= 48)
                                                      AS comptes_supprimes_par_bigquery
FROM cibles c
LEFT JOIN partis  p  ON c.review_id = p.review_id
LEFT JOIN revenus rv ON c.review_id = rv.review_id
LEFT JOIN textes  t  ON c.review_id = t.review_id
GROUP BY tranche_d_absence
ORDER BY tranche_d_absence;


-- ---------------------------------------------------------------------------
-- REQUÊTE 3 — Les mêmes avis, ligne par ligne, dans l'ordre où le robot a
--             écrit chaque enregistrement. Pour voir le comportement brut.
-- ---------------------------------------------------------------------------
WITH fenetre AS (
  SELECT *
  FROM `client-divers`.reviewflowz.reviews
  WHERE CAST(created_at AS DATE) BETWEEN "2026-05-13" AND "2026-08-16"
),
cibles AS (
  SELECT review_id FROM fenetre GROUP BY review_id
  HAVING COUNT(*) > 1
     AND COUNTIF(deleted_detected_at IS NOT NULL) > 0
     AND COUNTIF(deleted_detected_at IS NULL)     > 0
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
  f.first_seen_at                         AS vu_pour_la_1ere_fois,
  f.last_seen_at                          AS vu_pour_la_derniere_fois,
  f.deleted_detected_at                   AS disparu_le
FROM fenetre f
JOIN cibles USING (review_id)
ORDER BY f.review_id, f.first_seen_at, f.id;
