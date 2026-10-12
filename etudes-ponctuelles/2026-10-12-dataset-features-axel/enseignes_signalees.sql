-- Les « 6 enseignes » signalées (BigQuery) : 104 fiches de `businesses`.
--   4 chaînes antiparasitaires américaines, repérées par le début du nom   102 fiches
--   The Boxer Club, 2 salles de sport espagnoles, repérées par leur cid       2 fiches
-- Comparé le 2026-10-12 à `biz_surveillance` (95 fiches) : ses 95 fiches sont toutes ici. Les
-- 9 en plus sont des fiches dont le nom continue après celui de la chaîne (8 « EcoShield Pest
-- Solutions <ville> », 1 « Bulwark Exterminating Corporate »).
SELECT
  cid, name, country, industry, bucket,
  CASE
    WHEN LOWER(name) LIKE 'ecoshield pest solutions%' THEN 'EcoShield Pest Solutions'
    WHEN LOWER(name) LIKE 'insight pest solutions%'   THEN 'Insight Pest Solutions'
    WHEN LOWER(name) LIKE 'pointe pest control%'      THEN 'Pointe Pest Control'
    WHEN LOWER(name) LIKE 'bulwark exterminating%'    THEN 'Bulwark Exterminating'
    ELSE 'The Boxer Club'
  END AS enseigne,
  cid IN (SELECT cid FROM `client-divers.reviewflowz.biz_surveillance`) AS dans_biz_surveillance
FROM `client-divers.reviewflowz.businesses`
WHERE LOWER(name) LIKE 'ecoshield pest solutions%'
   OR LOWER(name) LIKE 'insight pest solutions%'
   OR LOWER(name) LIKE 'pointe pest control%'
   OR LOWER(name) LIKE 'bulwark exterminating%'
   OR cid IN ('3163466139043001754', '10346942689164695031')
ORDER BY enseigne, name;
