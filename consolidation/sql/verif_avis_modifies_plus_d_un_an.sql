-- ============================================================================
-- Vérification : les 555 avis supprimés que la règle des 365 jours retire
--
-- À lancer dans la console BigQuery. Le résultat contient le texte, le lien
-- et le nom de l'auteur : ne pas l'exporter dans un fichier du dépôt.
--
-- Ces avis passent les étapes 1 à 3 de `1b_entonnoir.sql` (dernière version,
-- pas de clignotement) et sortent à l'étape 4 : leur dernière modification
-- tombe plus de 365 jours après leur publication. 125 253 avis sont dans ce
-- cas, dont 555 supprimés pendant le suivi.
--
-- Une ligne par avis supprimé. Les colonnes `suppressions_de_la_fiche` et
-- `avis_retires_de_la_fiche` disent si ces avis se concentrent sur quelques
-- fiches. Tri : les fiches qui en perdent le plus d'abord.
--
-- Pour voir les 125 253 avis, supprimés ou non : retirer la dernière
-- condition du bloc `retires`.
-- ============================================================================

WITH classement AS (
  SELECT
    r.*,
    COUNT(*) OVER (PARTITION BY r.review_id) AS nb_lignes,
    ROW_NUMBER() OVER (
      PARTITION BY r.review_id
      ORDER BY r.updated_at DESC, r.last_seen_at DESC, r.id DESC
    ) AS rang
  FROM `client-divers.reviewflowz.reviews` r
),

retires AS (
  SELECT *
  FROM classement
  WHERE rang = 1
    AND (nb_lignes = 1 OR is_update = TRUE)
    AND TIMESTAMP_DIFF(updated_at, created_at, DAY) > 365
    AND deleted_detected_at IS NOT NULL
),

-- Combien d'avis chaque fiche perd à cause de la règle, supprimés ou non.
retires_par_fiche AS (
  SELECT cid, COUNT(*) AS avis_retires_de_la_fiche
  FROM classement
  WHERE rang = 1
    AND (nb_lignes = 1 OR is_update = TRUE)
    AND TIMESTAMP_DIFF(updated_at, created_at, DAY) > 365
  GROUP BY cid
)

SELECT
  -- la fiche
  b.name                                                      AS enseigne,
  b.country                                                   AS pays,
  b.industry                                                  AS secteur,
  b.bucket                                                    AS taille,
  r.cid,
  COUNT(*) OVER (PARTITION BY r.cid)                          AS suppressions_de_la_fiche,
  rf.avis_retires_de_la_fiche,
  s.cid IS NOT NULL                                           AS enseigne_signalee,

  -- l'avis
  r.star                                                      AS note,
  r.text                                                      AS texte,
  r.`language`                                                AS langue,
  DATE(r.created_at)                                          AS publie_le,
  DATE(r.updated_at)                                          AS modifie_le,
  TIMESTAMP_DIFF(r.updated_at, r.created_at, DAY)             AS jours_entre_publication_et_modification,
  r.is_update                                                 AS modifie_pendant_le_suivi,
  r.changed_fields                                            AS ce_qui_a_change,
  r.nb_lignes,
  DATE(r.first_seen_at)                                       AS vu_la_premiere_fois,
  DATE(r.deleted_detected_at)                                 AS disparu_le,

  -- l'auteur et la réponse
  r.reviewer_name                                             AS auteur,
  r.reviewer_review_count                                     AS avis_declares_par_l_auteur,
  r.local_guide_level                                         AS niveau_local_guide,
  r.reply_date IS NOT NULL                                    AS reponse_du_proprietaire,
  DATE(r.reply_date)                                          AS repondu_le,
  r.review_link                                               AS lien
FROM retires r
LEFT JOIN `client-divers.reviewflowz.businesses` b USING (cid)
LEFT JOIN `client-divers.reviewflowz.biz_surveillance` s USING (cid)
LEFT JOIN retires_par_fiche rf USING (cid)
ORDER BY suppressions_de_la_fiche DESC, r.cid, publie_le
