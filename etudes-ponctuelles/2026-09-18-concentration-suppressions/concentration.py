#!/usr/bin/env python3
"""Les suppressions se concentrent-elles sur quelques fiches ?

    python etudes-ponctuelles/2026-09-18-concentration-suppressions/concentration.py

Produit les CSV de `sorties/`. La figure et le document sont assemblés ensuite
par `note.py`.

------------------------------------------------------------------------------
LA QUESTION, ET POURQUOI IL FAUT UN POINT DE COMPARAISON
------------------------------------------------------------------------------
« Quelques fiches portent une grande part des suppressions » ne veut rien dire
seul. Les fiches n'ont pas la même taille : celle qui porte 9 000 avis en perd
mécaniquement plus que celle qui en porte 100, sans qu'il se passe rien de
particulier chez elle.

Le script calcule donc deux courbes sur les mêmes fiches :

  observé      la part des suppressions réellement portée par les N fiches les
               plus touchées ;
  attendu      la part que ces mêmes N fiches porteraient si les suppressions
               tombaient au hasard, proportionnellement au nombre d'avis de
               chaque fiche.

L'écart entre les deux est la réponse. Sans la seconde courbe, le premier
chiffre décrirait surtout la répartition des tailles de fiches.

Le tirage attendu est calculé sans simulation : les fiches sont rangées par
nombre d'avis décroissant, et la part cumulée de leurs avis donne directement
la part de suppressions qu'un tirage proportionnel leur attribuerait.

------------------------------------------------------------------------------
DÉFINITION D'UNE SUPPRESSION
------------------------------------------------------------------------------
`etude-exploratoire/scripts/suppressions_corrigees.py`, importée telle quelle :
absence de deux jours ou plus, bugs d'enregistrement retirés. Le dossier est
gelé ; le module est lu, rien n'y est écrit ni relancé.
"""
from __future__ import annotations

import sys
from pathlib import Path

DOSSIER = Path(__file__).resolve().parent
RACINE = DOSSIER.parent.parent
SORTIES = DOSSIER / "sorties"
sys.path.insert(0, str(RACINE / "outils"))
sys.path.insert(0, str(RACINE / "etude-exploratoire" / "scripts"))

from local import connexion  # noqa: E402
from suppressions_corrigees import creer_vue_avis  # noqa: E402


def ecrire(df, nom):
    SORTIES.mkdir(parents=True, exist_ok=True)
    df.to_csv(SORTIES / nom, index=False)
    print(f"  {nom:46s} {len(df):>6} lignes")
    return df


def main() -> int:
    con = connexion("4GB")
    creer_vue_avis(con, source="reviews")

    # Une ligne par fiche : son stock d'avis, ses suppressions.
    con.execute("""
        CREATE TEMP TABLE fiches AS
        SELECT a.cid,
               b.name     AS enseigne,
               b.industry AS secteur,
               b.country  AS pays,
               COUNT(*)                                        AS avis,
               SUM(CASE WHEN a.death_at IS NOT NULL THEN 1 ELSE 0 END) AS suppressions
        FROM avis a LEFT JOIN businesses b USING (cid)
        GROUP BY a.cid, b.name, b.industry, b.country
    """)

    print("\nA. Le cadre")
    ecrire(con.execute("""
        SELECT 'fiches suivies' AS mesure, COUNT(*) AS valeur FROM fiches
        UNION ALL SELECT 'fiches ayant perdu au moins un avis',
            (SELECT COUNT(*) FROM fiches WHERE suppressions > 0)
        UNION ALL SELECT 'avis suivis', (SELECT SUM(avis) FROM fiches)
        UNION ALL SELECT 'suppressions', (SELECT SUM(suppressions) FROM fiches)
    """).df(), "A1-cadre.csv")

    # Courbe observée : fiches rangées par suppressions décroissantes.
    # Courbe attendue : les mêmes fiches rangées par nombre d'avis décroissant,
    # la part cumulée des avis valant la part de suppressions d'un tirage
    # proportionnel à la taille.
    con.execute("""
        CREATE TEMP TABLE courbes AS
        WITH obs AS (
          SELECT ROW_NUMBER() OVER (ORDER BY suppressions DESC, avis DESC, cid) AS rang,
                 suppressions
          FROM fiches
        ),
        att AS (
          SELECT ROW_NUMBER() OVER (ORDER BY avis DESC, cid) AS rang, avis
          FROM fiches
        ),
        tot AS (SELECT SUM(suppressions) AS s, SUM(avis) AS a FROM fiches)
        SELECT o.rang,
               100.0 * SUM(o.suppressions) OVER (ORDER BY o.rang) / tot.s AS part_observee,
               100.0 * SUM(t.avis)         OVER (ORDER BY t.rang) / tot.a AS part_attendue
        FROM obs o JOIN att t ON t.rang = o.rang CROSS JOIN tot
    """)

    print("\nB. La concentration")
    ecrire(con.execute("""
        SELECT rang AS fiches_les_plus_touchees,
               ROUND(part_observee, 1) AS part_observee_pct,
               ROUND(part_attendue, 1) AS part_attendue_pct
        FROM courbes
        WHERE rang IN (1, 5, 10, 20, 50, 90, 100, 200, 452, 500, 905, 1000)
        ORDER BY rang
    """).df(), "B1-concentration.csv")

    ecrire(con.execute("""
        SELECT 'fiches portant la moitié des suppressions' AS mesure,
               (SELECT MIN(rang) FROM courbes WHERE part_observee >= 50) AS valeur
        UNION ALL SELECT 'fiches portant le quart des suppressions',
               (SELECT MIN(rang) FROM courbes WHERE part_observee >= 25)
        UNION ALL SELECT 'fiches portant les trois quarts des suppressions',
               (SELECT MIN(rang) FROM courbes WHERE part_observee >= 75)
    """).df(), "B2-seuils.csv")

    # La courbe entière, échantillonnée pour la figure.
    ecrire(con.execute("""
        SELECT rang, ROUND(part_observee, 3) AS part_observee,
               ROUND(part_attendue, 3) AS part_attendue
        FROM courbes
        WHERE rang <= 100 OR rang % 10 = 0
        ORDER BY rang
    """).df(), "B3-courbe.csv")

    print("\nC. Les fiches les plus touchées")
    ecrire(con.execute("""
        SELECT enseigne, secteur, pays, avis, suppressions,
               ROUND(100.0 * suppressions / avis, 1) AS part_du_stock_pct,
               ROUND(100.0 * suppressions
                     / (SELECT SUM(suppressions) FROM fiches), 2) AS part_du_total_pct
        FROM fiches WHERE suppressions > 0
        ORDER BY suppressions DESC, avis DESC, enseigne LIMIT 20
    """).df(), "C1-fiches.csv")

    print("\nD. Combien de suppressions par fiche touchée")
    ecrire(con.execute("""
        SELECT CASE WHEN suppressions = 1 THEN 'a. 1 suppression'
                    WHEN suppressions BETWEEN 2 AND 3  THEN 'b. 2 à 3'
                    WHEN suppressions BETWEEN 4 AND 9  THEN 'c. 4 à 9'
                    WHEN suppressions BETWEEN 10 AND 49 THEN 'd. 10 à 49'
                    ELSE 'e. 50 et plus' END AS paquet,
               COUNT(*) AS fiches, SUM(suppressions) AS suppressions,
               ROUND(100.0 * SUM(suppressions)
                     / (SELECT SUM(suppressions) FROM fiches), 1) AS part_du_total_pct
        FROM fiches WHERE suppressions > 0
        GROUP BY 1 ORDER BY 1
    """).df(), "D1-paquets.csv")

    con.close()
    print(f"\nCSV dans {SORTIES}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
