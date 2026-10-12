-- =============================================================================
-- Les features des régressions sur la suppression des avis (DuckDB)
--
-- Construit les deux fichiers :
--   features_regression_reviews_doublons_cleaned_all.parquet   toute la base
--   features_03C_7_17_aout.parquet                              les avis des régressions
--                                                               livrées (filtre du premier)
--
-- Entrées, dans le dossier d'où la requête est lancée :
--   reviews_doublons_cleaned_all.parquet   la base (BigQuery, client-divers.reviewflowz)
--   businesses.parquet                     les fiches : pays, secteur, taille, nom
--   reviews_name_enriched.parquet          l'annotation des prénoms d'Axel (has_name)
--
-- Lancer :   duckdb < features_regression.sql
--   ou, en Python :   import duckdb; duckdb.connect().execute(open("features_regression.sql").read())
--
-- Écrit le 2026-10-12 à partir des scripts du dépôt (07F_regression_03C_prenom.py,
-- 2026-10-09-regression-texte-local-guide, 03C_ajout_prenom.py). Vérifié le 2026-10-12 :
-- redonne à l'identique les deux fichiers livrés.
-- =============================================================================

-- Indispensable : les dates sont prises en UTC, comme BigQuery. Sans cette ligne, DuckDB
-- passe en heure de Paris et une partie des avis change de jour.
SET TimeZone = 'UTC';
-- SET memory_limit = '6GB';   -- à décommenter sur une machine à 8-16 Go

-- -----------------------------------------------------------------------------
-- LA VARIABLE EXPLIQUÉE
-- Le robot relève les fiches du 11 au 24 août 2026. « Supprimé au plus tard au 7e jour »
-- ne s'observe que pour un avis publié pendant le relevé : un avis de 2025 supprimé à son
-- 3e jour n'est pas dans la base. D'où deux colonnes :
--   supprime   disparu au plus tard 7 jours après la publication. Rempli seulement pour
--              les avis publiés du 7 au 17 août (corpus 03C), vide ailleurs.
--   disparu    deleted_detected_at renseigné : disparu pendant le relevé, toute la base.
--              À utiliser avec j_premiere_vue (âge à la première observation) et
--              jours_de_suivi en contrôle.
-- Un avis disparu compte comme supprimé : les doublons sont déjà retirés de la base.
--
-- LES AUTRES COLONNES
--   prenom, prenom_source   prénom cité dans le texte, d'après has_name d'Axel.
--       axel                 avis retrouvé, texte identique
--       axel_texte_modifie   avis retrouvé, texte changé entre les deux extractions
--       sans_texte           4-5 étoiles sans texte : FALSE
--       introuvable          4-5 étoiles avec texte absent chez Axel : NULL
--       hors_annotation      1 à 3 étoiles, non annotés : NULL
--   region                  US ou Europe
--   industry, bucket        secteur et taille de la fiche
--   enseigne                une des 6 enseignes signalées (4 chaînes antiparasitaires
--                           américaines, 2 salles espagnoles)
--   fin_suivi               dernier jour où la fiche a été relevée
--   fiche_plus_relevee      fiche plus relevée avant le 24 août
--   j_premiere_vue, j_reponse, j_suppression
--                           jours entre la publication et first_seen_at, reply_date,
--                           deleted_detected_at
--   jours_de_suivi          jours entre first_seen_at et fin_suivi
--   n_jour                  avis 4-5 étoiles publiés sur la fiche le même jour
--   par_jour                moyenne journalière des avis 4-5 étoiles de la fiche sur les
--                           365 jours avant le 11 août
--   pic                     n_jour >= 3 ET n_jour >= 4 x par_jour
--   photo                   au moins une photo jointe
--   reponse_j7              réponse du propriétaire au plus tard au 7e jour
--   sans_reponse_j7         son contraire (la référence des régressions est « réponse »)
--   longueur_texte          caractères du texte sans les espaces de début et de fin
--   tranche_texte           sans, 1_40, 41_80, 81_130, 131_240, 241_plus
--   tranche_guide           local_guide_level en 1_3, 4_6, 7_10 ; vide sans niveau
-- -----------------------------------------------------------------------------

CREATE TEMP TABLE features AS
WITH
r AS (
  -- Les horodatages passent en DATE (UTC).
  SELECT * REPLACE (
    CAST(created_at AS DATE)          AS created_at,
    CAST(updated_at AS DATE)          AS updated_at,
    CAST(reply_date AS DATE)          AS reply_date,
    CAST(first_seen_at AS DATE)       AS first_seen_at,
    CAST(last_seen_at AS DATE)        AS last_seen_at,
    CAST(deleted_detected_at AS DATE) AS deleted_detected_at)
  FROM 'reviews_doublons_cleaned_all.parquet'
),
axel AS (
  -- 333 review_id sont en double chez Axel : on garde la ligne dont le texte est le
  -- même, sinon le OU des lignes.
  SELECT r.review_id,
         bool_or(a.has_name) FILTER (a.text = r.text) AS prenom_meme_texte,
         bool_or(a.has_name)                          AS prenom_tout_texte
  FROM r JOIN 'reviews_name_enriched.parquet' a USING (review_id)
  GROUP BY r.review_id
),
fin AS (
  SELECT cid, max(last_seen_at) AS fin_suivi FROM r GROUP BY cid
),
avis_45 AS (
  SELECT cid, created_at AS jour FROM r WHERE star >= 4
),
rythme AS (
  SELECT cid, count(*) / 365.0 AS par_jour
  FROM avis_45
  WHERE jour BETWEEN DATE '2026-08-11' - INTERVAL 365 DAY AND DATE '2026-08-11' - INTERVAL 1 DAY
  GROUP BY cid
),
fiche_jour AS (
  SELECT cid, jour, count(*) AS n_jour FROM avis_45 GROUP BY cid, jour
),
base AS (
  SELECT r.*,
    CASE WHEN r.star <= 3                            THEN NULL
         WHEN length(trim(coalesce(r.text, ''))) = 0 THEN FALSE
         ELSE coalesce(x.prenom_meme_texte, x.prenom_tout_texte) END AS prenom,
    CASE WHEN r.star <= 3                            THEN 'hors_annotation'
         WHEN length(trim(coalesce(r.text, ''))) = 0 THEN 'sans_texte'
         WHEN x.prenom_meme_texte IS NOT NULL        THEN 'axel'
         WHEN x.prenom_tout_texte IS NOT NULL        THEN 'axel_texte_modifie'
         ELSE 'introuvable' END                                      AS prenom_source,
    if(b.country = 'US', 'US', 'Europe')                             AS region,
    b.industry, b.bucket,
    COALESCE(lower(b.name) LIKE 'ecoshield pest solutions%'
             OR lower(b.name) LIKE 'insight pest solutions%'
             OR lower(b.name) LIKE 'pointe pest control%'
             OR lower(b.name) LIKE 'bulwark exterminating%', FALSE)
      OR r.cid IN ('3163466139043001754', '10346942689164695031')    AS enseigne,
    f.fin_suivi,
    f.fin_suivi < DATE '2026-08-24'                                  AS fiche_plus_relevee,
    date_diff('day', r.created_at, r.first_seen_at)                  AS j_premiere_vue,
    date_diff('day', r.created_at, r.reply_date)                     AS j_reponse,
    date_diff('day', r.created_at, r.deleted_detected_at)            AS j_suppression,
    date_diff('day', r.first_seen_at, f.fin_suivi)                   AS jours_de_suivi,
    coalesce(fj.n_jour, 0)                                           AS n_jour,
    coalesce(ry.par_jour, 0)                                         AS par_jour,
    COALESCE(length(trim(r.text)), 0)                                AS longueur_texte
  FROM r
  LEFT JOIN axel x                     ON x.review_id = r.review_id
  LEFT JOIN 'businesses.parquet' b     ON b.cid = r.cid
  LEFT JOIN fin f                      ON f.cid = r.cid
  LEFT JOIN rythme ry                  ON ry.cid = r.cid
  LEFT JOIN fiche_jour fj              ON fj.cid = r.cid AND fj.jour = r.created_at
),
calcul AS (
  SELECT *,
    CASE WHEN created_at BETWEEN DATE '2026-08-07' AND DATE '2026-08-17'
         THEN coalesce(j_suppression <= 7, FALSE)::INT END            AS supprime,
    (deleted_detected_at IS NOT NULL)::INT                           AS disparu,
    (n_jour >= 3 AND n_jour >= 4 * par_jour)::INT                    AS pic,
    (coalesce(n_photos, 0) > 0)::INT                                 AS photo,
    coalesce(j_reponse <= 7, FALSE)::INT                             AS reponse_j7,
    1 - coalesce(j_reponse <= 7, FALSE)::INT                         AS sans_reponse_j7,
    CASE WHEN longueur_texte = 0    THEN 'sans'
         WHEN longueur_texte <= 40  THEN '1_40'
         WHEN longueur_texte <= 80  THEN '41_80'
         WHEN longueur_texte <= 130 THEN '81_130'
         WHEN longueur_texte <= 240 THEN '131_240'
         ELSE '241_plus' END                                         AS tranche_texte,
    CASE WHEN local_guide_level BETWEEN 1 AND 3  THEN '1_3'
         WHEN local_guide_level BETWEEN 4 AND 6  THEN '4_6'
         WHEN local_guide_level BETWEEN 7 AND 10 THEN '7_10' END    AS tranche_guide
  FROM base
)
SELECT * EXCLUDE (region, industry, bucket, enseigne, fin_suivi, fiche_plus_relevee,
                  j_premiere_vue, j_reponse, j_suppression, jours_de_suivi, n_jour,
                  par_jour, supprime, disparu, photo, reponse_j7, sans_reponse_j7, pic,
                  longueur_texte, tranche_texte, tranche_guide),
       region, industry, bucket, enseigne, fin_suivi, fiche_plus_relevee,
       j_premiere_vue, j_reponse, j_suppression, jours_de_suivi, n_jour, par_jour,
       supprime, disparu, photo, reponse_j7, sans_reponse_j7, pic,
       longueur_texte, tranche_texte, tranche_guide
FROM calcul;

-- Toute la base : 4 876 933 avis, 4 590 disparus.
COPY features TO 'features_regression_reviews_doublons_cleaned_all.parquet'
  (FORMAT parquet, COMPRESSION zstd);

-- Les avis des régressions livrées : 4-5 étoiles publiés du 7 au 17 août, prénom connu,
-- fiche relevée jusqu'au 24 août. 24 191 avis, 631 supprimés au plus tard au 7e jour.
-- La régression texte + Local Guide écarte en plus les avis sans tranche_guide.
COPY (
  SELECT * EXCLUDE (fin_suivi, fiche_plus_relevee, jours_de_suivi, disparu)
  REPLACE (CAST(supprime AS BIGINT)        AS supprime,
           CAST(photo AS BIGINT)           AS photo,
           CAST(reponse_j7 AS BIGINT)      AS reponse_j7,
           CAST(sans_reponse_j7 AS BIGINT) AS sans_reponse_j7,
           CAST(pic AS BIGINT)             AS pic)
  FROM features
  WHERE supprime IS NOT NULL AND star >= 4 AND prenom IS NOT NULL AND NOT fiche_plus_relevee
) TO 'features_03C_7_17_aout.parquet' (FORMAT parquet, COMPRESSION zstd);
