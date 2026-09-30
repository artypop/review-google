-- ============================================================================
-- 7. Contrôles du point 7 : les totaux de la base, et le rapprochement avec
-- les comptages faits à la main dans la console
--
-- Base : `reviews_doublons_cleaned`. Une ligne par contrôle : avis et
-- suppressions.
--
-- Deux façons de compter « un avis avec réponse » :
--   au dernier passage   `reply_date` rempli, quelle que soit sa date ;
--   avant le 11 août     `reply_date` antérieure au 11 août : c'est la
--                        définition du point 7.
-- ============================================================================

WITH base AS (
  SELECT
    deleted_detected_at IS NOT NULL                                AS supprime,
    CAST(created_at AS DATE)                                       AS publie_le,
    reply_date IS NOT NULL                                         AS reponse_au_dernier_passage,
    reply_date IS NOT NULL AND CAST(reply_date AS DATE) < DATE "2026-08-11" AS reponse_avant_le_11_aout
  FROM `client-divers.reviewflowz.reviews_doublons_cleaned`
)

SELECT 1 AS ordre, "base complète" AS controle, COUNT(*) AS avis, COUNTIF(supprime) AS suppressions FROM base
UNION ALL
SELECT 2, "publiés avant le 11 août (population du point 7)", COUNT(*), COUNTIF(supprime)
  FROM base WHERE publie_le < DATE "2026-08-11"
UNION ALL
SELECT 3, "publiés à partir du 11 août (hors du point 7)", COUNT(*), COUNTIF(supprime)
  FROM base WHERE publie_le >= DATE "2026-08-11"
UNION ALL
SELECT 4, "point 7 : répondus avant le 11 août", COUNT(*), COUNTIF(supprime)
  FROM base WHERE publie_le < DATE "2026-08-11" AND reponse_avant_le_11_aout
UNION ALL
SELECT 5, "point 7 : sans réponse au 11 août", COUNT(*), COUNTIF(supprime)
  FROM base WHERE publie_le < DATE "2026-08-11" AND NOT reponse_avant_le_11_aout
UNION ALL
SELECT 6, "point 7 : dont réponse arrivée le 11 août ou après", COUNT(*), COUNTIF(supprime)
  FROM base WHERE publie_le < DATE "2026-08-11" AND reponse_au_dernier_passage
                  AND NOT reponse_avant_le_11_aout
UNION ALL
SELECT 7, "base complète : avis avec réponse au dernier passage", COUNT(*), COUNTIF(supprime)
  FROM base WHERE reponse_au_dernier_passage
UNION ALL
SELECT 8, "publiés après le 1er août, avec réponse au dernier passage", COUNT(*), COUNTIF(supprime)
  FROM base WHERE publie_le > DATE "2026-08-01" AND reponse_au_dernier_passage
ORDER BY ordre
