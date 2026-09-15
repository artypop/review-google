-- Contrôle préalable : les `cid` des six enseignes signalées.
--
-- Lecture seule. Ne crée aucune table.
--
-- Les quatre chaînes antiparasitaires se repèrent par le nom de l'enseigne :
-- `docs/02-donnees.md` § 4 juge ce repérage correct, toutes les succursales
-- étant recherchées, et donne les comptes 26, 19, 19 et 24 fiches.
--
-- Ces comptes sont ceux du PANEL. La table `businesses` en porte 5 de plus :
-- 27, 21, 20 et 25. Ces cinq fiches existent et appartiennent aux mêmes
-- chaînes ; elles sont sorties à la sélection du panel, qui ne retient que les
-- fiches ayant entre 100 et 10 000 avis (`sql/01_selection_panel.sql`).
--
-- Cette étude lit `reviews`, donc elle écarte les 93 fiches de `businesses`.
-- La colonne `fiches_dans_le_panel` rejoue le compte documenté, pour vérifier
-- que le repérage par nom n'a pas bougé.
--
-- Les deux salles de sport espagnoles ne passent pas par le nom : leurs `cid`
-- sont écrits en dur dans `lancer.py`, décision de Romain du 2026-09-14.
--
-- Le nom sert ici de clé de regroupement et ne sort pas dans le CSV.

WITH panel AS (
  SELECT DISTINCT cid
  FROM `client-divers`.reviewflowz.reviews_panel_features
  WHERE chaine_antiparasitaire_us
)

SELECT
  CASE b.name
    WHEN "EcoShield Pest Solutions"  THEN "chaine_1"
    WHEN "Insight Pest Solutions"    THEN "chaine_2"
    WHEN "Pointe Pest Control"       THEN "chaine_3"
    WHEN "Bulwark Exterminating"     THEN "chaine_4"
  END                AS chaine,
  COUNT(DISTINCT b.cid)                      AS fiches_businesses,
  COUNT(DISTINCT p.cid)                      AS fiches_dans_le_panel
FROM `client-divers`.reviewflowz.businesses AS b
LEFT JOIN panel AS p USING (cid)
WHERE b.name IN ("EcoShield Pest Solutions", "Insight Pest Solutions",
                 "Pointe Pest Control", "Bulwark Exterminating")
GROUP BY chaine
ORDER BY chaine;
