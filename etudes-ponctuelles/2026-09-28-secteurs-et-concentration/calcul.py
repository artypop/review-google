#!/usr/bin/env python3
"""Suppressions par secteur, et concentration des suppressions sur un panel récent.

    python etudes-ponctuelles/2026-09-28-secteurs-et-concentration/calcul.py

Produit les CSV de `sorties/`. La figure et le document Word sont assemblés
ensuite par `note.py`, qui ne calcule rien.

------------------------------------------------------------------------------
DEUX QUESTIONS
------------------------------------------------------------------------------
A. Sur toute la base (4,88 millions d'avis, toutes dates de publication) :
   combien d'avis et de suppressions par secteur, et quelle part des avis du
   secteur est supprimée ?

B. Sur les avis publiés du 4 au 24 août 2026 (7 jours avant le premier relevé
   du 11 août, jusqu'au dernier relevé) : les suppressions sont-elles
   concentrées sur quelques fiches ? Même calcul que la figure 4 du rapport
   (`2026-09-18-concentration-suppressions`), sur ce périmètre.

------------------------------------------------------------------------------
LA COURBE DE COMPARAISON, CORRIGÉE
------------------------------------------------------------------------------
La figure 4 d'origine comparait les N fiches les plus touchées aux N plus
grosses fiches, sous la légende « si les suppressions suivaient la taille des
fiches ». Ce ne sont pas les mêmes fiches. Ce script écrit trois courbes :

  part_observee          part des suppressions des N fiches les plus touchées ;
  part_avis_plus_grosses part des avis des N fiches qui ont le plus d'avis ;
  part_avis_touchees     part des avis des N fiches les plus touchées elles-mêmes.

------------------------------------------------------------------------------
DÉFINITIONS
------------------------------------------------------------------------------
Suppression : `creer_vue_avis()` de `etude-exploratoire/scripts/suppressions_
corrigees.py`, importée telle quelle, comme la figure 4. Le dossier est gelé :
le module est lu, rien n'y est écrit ni relancé.

Enseignes signalées : les deux salles de sport attaquées, repérées sur leur
`cid` (décision du 2026-09-14), et les quatre chaînes antiparasitaires
américaines, repérées sur le début du nom comme dans l'étude embedding, ce qui
attrape aussi leurs succursales à suffixe (« EcoShield Pest Solutions
Houston »).

Date de publication : `created_at` lue en UTC (`outils/local.py`).

------------------------------------------------------------------------------
L'OPTION --doublons-cleaned (2026-09-28)
------------------------------------------------------------------------------
Refait les mêmes mesures sur les seuls avis de `reviews_doublons_cleaned`
(copie locale de la table BigQuery du 2026-09-17, 4 751 680 avis, une ligne
chacun). Décision de Matthieu du 2026-09-28 : la suppression garde la
définition du rapport, calculée sur `reviews` comme ci-dessus, puis le corpus
est restreint aux avis présents dans `reviews_doublons_cleaned`. 125 854 avis
de `reviews` en sont absents ; la règle qui les a écartés n'est pas documentée
dans le dépôt.

Mesuré le 2026-09-28 : 4 003 suppressions retenues. La colonne brute
`deleted_detected_at` de la table en compte 4 035 ; les 32 d'écart sont des
absences d'un jour ou des bugs de réécriture, que la définition du rapport
écarte. Sorties dans `sorties/doublons-cleaned/`.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

DOSSIER = Path(__file__).resolve().parent
RACINE = DOSSIER.parent.parent
SORTIES = DOSSIER / "sorties"
sys.path.insert(0, str(RACINE / "outils"))
sys.path.insert(0, str(RACINE / "etude-exploratoire" / "scripts"))

from local import connexion  # noqa: E402
from suppressions_corrigees import creer_vue_avis  # noqa: E402

PANEL_DEBUT = "2026-08-04"   # 7 jours avant le premier relevé du 11 août
PANEL_FIN = "2026-08-24"     # dernier relevé

CID_SALLES_ATTAQUEES = ("3163466139043001754", "10346942689164695031")
RACINES_CHAINES_US = ("ecoshield pest solutions", "insight pest",
                      "pointe pest control", "bulwark exterminating")

SECTEURS = {
    "automotive": "Automobile", "home_services": "Services à domicile",
    "healthcare": "Santé", "wellness_fitness": "Sport et bien-être",
    "food_beverage": "Restauration", "travel": "Voyage", "hospitality": "Hôtellerie",
}

RANGS = (1, 5, 10, 20, 50, 100, 200, 500)


def ecrire(df, nom):
    SORTIES.mkdir(parents=True, exist_ok=True)
    df.to_csv(SORTIES / nom, index=False)
    print(f"  {nom:40s} {len(df):>6} lignes")
    return df


def main() -> int:
    global SORTIES
    ap = argparse.ArgumentParser()
    ap.add_argument("--doublons-cleaned", action="store_true",
                    help="restreint le corpus aux avis de reviews_doublons_cleaned")
    args = ap.parse_args()

    con = connexion("1500MB")
    con.execute("SET threads=2")
    con.execute("SET enable_progress_bar=false")
    creer_vue_avis(con, source="reviews")
    perimetre = "TRUE"
    if args.doublons_cleaned:
        SORTIES = SORTIES / "doublons-cleaned"
        perimetre = "a.review_id IN (SELECT review_id FROM reviews_doublons_cleaned)"
        print("Corpus : avis de reviews_doublons_cleaned")

    chaines = " OR ".join(f"lower(b.name) LIKE '{r}%'" for r in RACINES_CHAINES_US)
    con.execute(f"""
        CREATE TEMP TABLE av AS
        SELECT a.cid,
               b.name     AS enseigne,
               b.industry AS secteur,
               b.country  AS pays,
               (a.cid IN {CID_SALLES_ATTAQUEES} OR {chaines}) AS enseigne_signalee,
               CAST(a.created_at AS DATE) AS jour_publication,
               a.death_at IS NOT NULL     AS supprime
        FROM avis a LEFT JOIN businesses b USING (cid)
        WHERE {perimetre}
    """)

    # ------------------------------------------------------------------
    print("\nA. Les secteurs, toute la base")
    for suffixe, filtre in (("", "TRUE"), ("-sans-enseignes", "NOT enseigne_signalee")):
        d = con.execute(f"""
            SELECT secteur,
                   COUNT(*)                     AS avis,
                   ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS part_corpus_pct,
                   COUNT(*) FILTER (supprime)   AS suppressions,
                   ROUND(100.0 * COUNT(*) FILTER (supprime) / COUNT(*), 3) AS part_supprimee_pct
            FROM av WHERE {filtre}
            GROUP BY secteur ORDER BY part_supprimee_pct DESC
        """).df()
        d.insert(0, "secteur_fr", d["secteur"].map(SECTEURS))
        ecrire(d, f"A1-secteurs{suffixe}.csv")

    # ------------------------------------------------------------------
    print(f"\nB. La concentration, avis publiés du {PANEL_DEBUT} au {PANEL_FIN}")
    con.execute(f"""
        CREATE TEMP TABLE fiches AS
        SELECT cid, any_value(enseigne) AS enseigne, any_value(secteur) AS secteur,
               any_value(pays) AS pays, bool_or(enseigne_signalee) AS enseigne_signalee,
               COUNT(*) AS avis, COUNT(*) FILTER (supprime) AS suppressions
        FROM av
        WHERE jour_publication BETWEEN DATE '{PANEL_DEBUT}' AND DATE '{PANEL_FIN}'
        GROUP BY cid
    """)

    for suffixe, filtre in (("", "TRUE"), ("-sans-enseignes", "NOT enseigne_signalee")):
        con.execute(f"CREATE OR REPLACE TEMP TABLE f AS SELECT * FROM fiches WHERE {filtre}")

        ecrire(con.execute("""
            SELECT 'fiches ayant au moins un avis publié dans la période' AS mesure,
                   COUNT(*) AS valeur FROM f
            UNION ALL SELECT 'fiches ayant perdu au moins un avis',
                   COUNT(*) FILTER (suppressions > 0) FROM f
            UNION ALL SELECT 'avis', SUM(avis) FROM f
            UNION ALL SELECT 'suppressions', SUM(suppressions) FROM f
        """).df(), f"B1-cadre{suffixe}.csv")

        con.execute("""
            CREATE OR REPLACE TEMP TABLE courbes AS
            WITH obs AS (
              SELECT ROW_NUMBER() OVER (ORDER BY suppressions DESC, avis DESC, cid) AS rang,
                     suppressions, avis
              FROM f
            ),
            gros AS (
              SELECT ROW_NUMBER() OVER (ORDER BY avis DESC, cid) AS rang, avis
              FROM f
            ),
            tot AS (SELECT SUM(suppressions) AS s, SUM(avis) AS a FROM f)
            SELECT o.rang,
                   100.0 * SUM(o.suppressions) OVER (ORDER BY o.rang) / tot.s AS part_observee,
                   100.0 * SUM(g.avis)         OVER (ORDER BY o.rang) / tot.a AS part_avis_plus_grosses,
                   100.0 * SUM(o.avis)         OVER (ORDER BY o.rang) / tot.a AS part_avis_touchees
            FROM obs o JOIN gros g ON g.rang = o.rang CROSS JOIN tot
        """)

        # Au-delà des fiches touchées, le classement passe aux fiches sans
        # suppression, rangées par taille : les rangs fixes s'arrêtent avant, et
        # la dernière ligne est le nombre exact de fiches touchées.
        touchees = con.execute("SELECT COUNT(*) FROM f WHERE suppressions > 0").fetchone()[0]
        rangs = tuple(r for r in RANGS if r < touchees) + (touchees,)
        ecrire(con.execute(f"""
            SELECT rang AS fiches_les_plus_touchees,
                   ROUND(part_observee, 1)          AS part_suppressions_pct,
                   ROUND(part_avis_touchees, 2)     AS part_avis_de_ces_fiches_pct,
                   ROUND(part_avis_plus_grosses, 1) AS part_avis_plus_grosses_fiches_pct
            FROM courbes WHERE rang IN {rangs} ORDER BY rang
        """).df(), f"B2-concentration{suffixe}.csv")

        ecrire(con.execute("""
            SELECT 'fiches portant le quart des suppressions' AS mesure,
                   MIN(rang) FILTER (part_observee >= 25) AS valeur FROM courbes
            UNION ALL SELECT 'fiches portant la moitié des suppressions',
                   MIN(rang) FILTER (part_observee >= 50) FROM courbes
            UNION ALL SELECT 'fiches portant les trois quarts des suppressions',
                   MIN(rang) FILTER (part_observee >= 75) FROM courbes
        """).df(), f"B3-seuils{suffixe}.csv")

        ecrire(con.execute("""
            SELECT rang, ROUND(part_observee, 3) AS part_observee,
                   ROUND(part_avis_plus_grosses, 3) AS part_avis_plus_grosses,
                   ROUND(part_avis_touchees, 3) AS part_avis_touchees
            FROM courbes WHERE rang <= 100 OR rang % 5 = 0 ORDER BY rang
        """).df(), f"B4-courbe{suffixe}.csv")

        ecrire(con.execute("""
            SELECT CASE WHEN suppressions = 1 THEN 'a. 1 suppression'
                        WHEN suppressions BETWEEN 2 AND 3  THEN 'b. 2 à 3'
                        WHEN suppressions BETWEEN 4 AND 9  THEN 'c. 4 à 9'
                        WHEN suppressions BETWEEN 10 AND 49 THEN 'd. 10 à 49'
                        ELSE 'e. 50 et plus' END AS paquet,
                   COUNT(*) AS fiches, SUM(suppressions) AS suppressions,
                   ROUND(100.0 * SUM(suppressions) / (SELECT SUM(suppressions) FROM f), 1)
                       AS part_des_suppressions_pct
            FROM f WHERE suppressions > 0 GROUP BY 1 ORDER BY 1
        """).df(), f"B5-paquets{suffixe}.csv")

        ecrire(con.execute("""
            SELECT enseigne, secteur, pays, avis, suppressions,
                   ROUND(100.0 * suppressions / avis, 1) AS part_de_ses_avis_pct,
                   ROUND(100.0 * suppressions / (SELECT SUM(suppressions) FROM f), 2)
                       AS part_des_suppressions_pct
            FROM f WHERE suppressions > 0
            ORDER BY suppressions DESC, avis DESC, enseigne LIMIT 10
        """).df(), f"B6-fiches{suffixe}.csv")

    con.close()
    print(f"\nCSV dans {SORTIES}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
