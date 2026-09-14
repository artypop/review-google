-- ============================================================================
-- File: sql/controle_C_reponses_au_jalon.sql
-- Lecture seule. Ne crée aucune table.
--
-- À EXÉCUTER AVANT `08_effet_reponse_commercant.py`.
--
-- Le montage de `08` compare, parmi les avis encore en ligne à la fin de leur
-- 2e jour, ceux qui avaient déjà une réponse du commerçant et ceux qui n'en
-- avaient pas. Si une des quatre cases du croisement est trop maigre, il n'y a
-- rien à estimer et le script ne doit pas être lancé.
--
-- Seuil de décision : moins de 30 avis dans une case, ou moins de 5
-- suppressions d'un côté -> on s'arrête et on l'écrit. Ce sont les mêmes
-- seuils que les garde-fous de `07_regression_panel.py`
-- (MIN_CAS_PAR_COLONNE, MIN_SUPPRESSIONS_PAR_COLONNE).
--
-- ----------------------------------------------------------------------------
-- LE MONTAGE, EN UNE PHRASE
-- ----------------------------------------------------------------------------
-- On fixe un jalon à la fin du 2e jour de vie de l'avis. On ne garde que les
-- avis encore en ligne à ce moment. On note s'ils ont déjà une réponse. Puis on
-- regarde qui disparaît entre le 3e et le 8e jour.
--
-- Pourquoi ce détour : figer la réponse à son état final fait dire « avoir une
-- réponse » là où les données disent « avoir survécu assez longtemps pour en
-- recevoir une ». Avec un jalon fixe, tout le monde est vivant au même moment,
-- la réponse est connue à ce moment, et la suppression est comptée après. Les
-- deux ne peuvent plus se mélanger.
--
-- ----------------------------------------------------------------------------
-- POURQUOI LA POPULATION EST CELLE-LÀ
-- ----------------------------------------------------------------------------
-- Seuls les avis publiés pendant la surveillance ont leurs premiers jours
-- observés. Pour un avis déjà en ligne au 11 août, on ne sait pas ce qui s'est
-- passé pendant ses 48 premières heures : ni s'il a reçu une réponse, ni s'il a
-- failli disparaître. `ne_pendant_la_surveillance` les écarte.
--
-- Fenêtre de publication : du 2026-08-11 au 2026-08-16 (la borne haute de
-- `01_selection_panel.sql`). Le dernier entrant, publié le 16, atteint son
-- 8e jour le 24 août, jour du dernier passage du robot. Tous les avis de la
-- population ont donc bien 8 jours d'observation, et pas un de moins.
--
-- ATTENTION À UN ÉCART DE COMPTAGE CONNU
-- `ne_pendant_la_surveillance` vaut TRUE pour 15 248 avis (créés du 11 au 16).
-- Le tableau de `07_regression_panel.py:28-33` affiche 12 664 pour la ligne
-- « né pendant » : il y range les avis dont l'âge à la vague 1 est strictement
-- négatif, donc créés du 12 au 16. Les 2 584 avis du 11 août y sont comptés
-- dans « 0 à 7 j ». Les deux chiffres sont justes. C'est 15 248 qui sert ici.
-- ============================================================================


-- ----------------------------------------------------------------------------
-- 1. La population, étape par étape.
--    Chaque ligne retire un groupe. Le dernier compte est le dénominateur
--    de toute l'étude.
-- ----------------------------------------------------------------------------
WITH nes_pendant AS (
  SELECT
    review_id,
    cid,
    supprime,
    reponse_dans_les_2_jours,
    age_a_la_suppression_j
  FROM `client-divers.reviewflowz.reviews_panel_features`
  WHERE ne_pendant_la_surveillance
),

au_jalon AS (
  SELECT *
  FROM nes_pendant
  -- Encore en ligne à la fin du 2e jour : soit jamais supprimé, soit supprimé
  -- plus tard. Un avis supprimé au 1er ou au 2e jour n'a pas atteint le jalon
  -- et n'a donc rien à nous apprendre sur ce qui se passe après.
  WHERE NOT supprime OR age_a_la_suppression_j > 2
)

SELECT
  'population'                                            AS etape,
  (SELECT COUNT(*) FROM nes_pendant)                      AS avis_nes_pendant,
  (SELECT COUNT(*) FROM nes_pendant
    WHERE supprime AND age_a_la_suppression_j <= 2)       AS perdus_avant_le_jalon,
  (SELECT COUNT(*) FROM au_jalon)                         AS denominateur_de_l_etude,
  (SELECT COUNT(DISTINCT cid) FROM au_jalon)              AS fiches;


-- ----------------------------------------------------------------------------
-- 2. LE CROISEMENT QUI DÉCIDE. Quatre cases.
--
--    Lecture d'une case : la ligne « avec réponse » et la colonne
--    « supprimé entre le 3e et le 8e jour » donnent le nombre d'avis qui
--    avaient une réponse au jalon ET qui ont disparu dans la fenêtre.
--
--    Si une des quatre cases est sous 30, ou si un des deux groupes porte
--    moins de 5 suppressions, ne pas lancer `08`.
-- ----------------------------------------------------------------------------
WITH nes_pendant AS (
  SELECT supprime, reponse_dans_les_2_jours, age_a_la_suppression_j
  FROM `client-divers.reviewflowz.reviews_panel_features`
  WHERE ne_pendant_la_surveillance
),
au_jalon AS (
  SELECT * FROM nes_pendant
  WHERE NOT supprime OR age_a_la_suppression_j > 2
)
SELECT
  CASE WHEN reponse_dans_les_2_jours
       THEN 'reponse presente au jalon'
       ELSE 'pas de reponse au jalon' END                 AS groupe,
  COUNT(*)                                                AS avis,
  COUNTIF(supprime AND age_a_la_suppression_j BETWEEN 3 AND 8)
                                                          AS supprimes_3e_au_8e_jour,
  COUNT(*) - COUNTIF(supprime AND age_a_la_suppression_j BETWEEN 3 AND 8)
                                                          AS restes_en_ligne,
  ROUND(1000 * COUNTIF(supprime AND age_a_la_suppression_j BETWEEN 3 AND 8)
        / COUNT(*), 1)                                    AS pour_1000_avis_du_groupe
FROM au_jalon
GROUP BY groupe
ORDER BY groupe;


-- ----------------------------------------------------------------------------
-- 3. Le seuil du jalon est un choix arbitraire. Voici de quoi le juger.
--
--    Répartition du délai entre la publication de l'avis et la réponse du
--    commerçant, sur les seuls avis nés pendant la surveillance.
--
--    Ce que ce tableau sert à décider : si presque toutes les réponses
--    arrivent le jour même, un jalon à 2 jours laisse passer très peu de
--    monde du mauvais côté, et le montage est solide. Si elles s'étalent, le
--    jalon coupe au milieu d'un phénomène en cours et `--jalon-jours` mérite
--    d'être bougé.
-- ----------------------------------------------------------------------------
SELECT
  CASE
    WHEN delai_reponse_j IS NULL THEN 'z. aucune reponse a ce jour'
    WHEN delai_reponse_j <= 0    THEN 'a. le jour meme'
    WHEN delai_reponse_j = 1     THEN 'b. 1 jour'
    WHEN delai_reponse_j = 2     THEN 'c. 2 jours'
    WHEN delai_reponse_j <= 5    THEN 'd. 3 a 5 jours'
    WHEN delai_reponse_j <= 8    THEN 'e. 6 a 8 jours'
    ELSE                              'f. plus de 8 jours'
  END                                                     AS delai_de_reponse,
  COUNT(*)                                                AS avis,
  ROUND(100 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)        AS pct_des_avis_nes_pendant
FROM `client-divers.reviewflowz.reviews_panel_features`
WHERE ne_pendant_la_surveillance
GROUP BY delai_de_reponse
ORDER BY delai_de_reponse;


-- ----------------------------------------------------------------------------
-- 4. Les six enseignes signalées portent 39,3 % des suppressions du panel.
--    Ce comptage dit si elles pèsent aussi sur cette population-ci, donc si le
--    passage `--sans-enseignes-signalees` de `08` aura de quoi tourner.
-- ----------------------------------------------------------------------------
WITH au_jalon AS (
  SELECT *
  FROM `client-divers.reviewflowz.reviews_panel_features`
  WHERE ne_pendant_la_surveillance
    AND (NOT supprime OR age_a_la_suppression_j > 2)
)
SELECT
  CASE
    WHEN chaine_antiparasitaire_us THEN 'chaine antiparasitaire US'
    WHEN salle_de_sport_attaquee   THEN 'salle de sport attaquee'
    ELSE                                'reste du panel'
  END                                                     AS groupe,
  COUNT(*)                                                AS avis,
  COUNTIF(reponse_dans_les_2_jours)                       AS avec_reponse_au_jalon,
  COUNTIF(supprime AND age_a_la_suppression_j BETWEEN 3 AND 8)
                                                          AS supprimes_3e_au_8e_jour
FROM au_jalon
GROUP BY groupe
ORDER BY avis DESC;
