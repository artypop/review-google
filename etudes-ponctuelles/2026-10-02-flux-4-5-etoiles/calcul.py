#!/usr/bin/env python3
"""Suppressions des avis 4 et 5 étoiles par secteur : flux, pertes de la période, stock.

    PYTHONPATH=".venv/Lib/site-packages;outils" <python uv> etudes-ponctuelles/2026-10-02-flux-4-5-etoiles/calcul.py

Demande d'Axel (réunion du 2026-10-01), cadrée avec Matthieu le 2026-10-02 :
« ce mois-ci j'ai collecté X avis et j'en ai perdu Y », par secteur, sur les
avis 4 et 5 étoiles.

  corpus       data/bigquery/reviews_doublons_cleaned_all.parquet, une ligne
               par avis. Avis 4 et 5 étoiles seulement.
  suppression  `deleted_detected_at` renseigné (décision de Matthieu du
               2026-10-02 : la table est dédoublonnée, la règle des deux jours
               d'absence du 03C ne s'applique pas). Vérifié le 2026-10-02 :
               `deleted_detected_at` vaut toujours le lendemain de
               `last_seen_at`, aucun avis n'est revu après sa disparition.
  fiches       les 3 fiches qui ne sont plus relevées avant le 24 août (fin de
               suivi le 17, 18 ou 22) sont écartées des trois mesures.

Trois mesures, chacune pour 100 avis :
  A. flux      avis publiés du 11 au 17 août ; part disparue au plus tard 7
               jours après la publication. Le 17 août est la dernière date qui
               laisse 7 jours avant le dernier relevé du 24.
  B. pertes    avis disparus du 11 au 24 août, quel que soit leur âge,
               rapportés aux avis publiés du 11 au 24 août.
  stock        avis vus pendant le relevé, toutes dates de publication ; part
               disparue du 11 au 24 août.

Découpage : par secteur, avec et sans les 6 enseignes (4 chaînes
antiparasitaires repérées sur le début du nom, 2 salles espagnoles sur leur
`cid`, comme le 03C), plus une ligne pour les 4 chaînes seules.

Sortie : `sorties/flux-4-5-etoiles.csv`. Aucun texte, nom d'auteur ni lien.
"""
from __future__ import annotations

import sys
from pathlib import Path

DOSSIER = Path(__file__).resolve().parent
RACINE = DOSSIER.parents[1]
sys.path.insert(0, str(RACINE / "outils"))
from local import connexion  # noqa: E402

SORTIES = DOSSIER / "sorties"
FLUX_DEBUT, FLUX_FIN, JOURS = "2026-08-11", "2026-08-17", 7
RELEVE_DEBUT, RELEVE_FIN = "2026-08-11", "2026-08-24"

CHAINES_ANTIPARASITAIRES = ("ecoshield pest solutions", "insight pest solutions",
                            "pointe pest control", "bulwark exterminating")
CID_SALLES_ESPAGNOLES = ("3163466139043001754", "10346942689164695031")
SECTEURS = {"automotive": "Automobile", "home_services": "Services à domicile",
            "healthcare": "Santé", "wellness_fitness": "Sport et bien-être",
            "food_beverage": "Restauration", "travel": "Voyage", "hospitality": "Hôtellerie"}

SQL_AVIS = """
CREATE TEMP TABLE avis AS
WITH fin_suivi AS (
  SELECT cid, max(CAST(last_seen_at AS DATE)) AS fin_suivi
  FROM reviews_doublons_cleaned_all GROUP BY cid
)
SELECT r.review_id, r.cid, b.industry,
       CAST(r.created_at AS DATE)          AS publie,
       CAST(r.deleted_detected_at AS DATE) AS disparu,
       COALESCE({chaines}, FALSE)          AS chaine,
       r.cid IN ({salles})                 AS salle
FROM reviews_doublons_cleaned_all r
JOIN fin_suivi f USING (cid)
LEFT JOIN businesses b ON b.cid = r.cid
WHERE r.star >= 4 AND f.fin_suivi = DATE '{fin}'
"""

SQL_MESURES = f"""
WITH base AS (
  SELECT *, industry AS groupe FROM avis
  UNION ALL
  SELECT *, 'chaines' FROM avis WHERE chaine
),
jeux AS (
  SELECT 'toutes les fiches' AS jeu, * FROM base
  UNION ALL
  SELECT 'sans les 6 enseignes', * FROM base WHERE NOT (chaine OR salle)
)
SELECT jeu, CASE WHEN groupe = 'chaines' THEN 'chaines' END AS ligne, groupe,
  COUNT(*) FILTER (publie BETWEEN DATE '{FLUX_DEBUT}' AND DATE '{FLUX_FIN}')     AS flux_avis,
  COUNT(*) FILTER (publie BETWEEN DATE '{FLUX_DEBUT}' AND DATE '{FLUX_FIN}'
                   AND date_diff('day', publie, disparu) <= {JOURS})            AS flux_supprimes,
  COUNT(*) FILTER (publie BETWEEN DATE '{RELEVE_DEBUT}' AND DATE '{RELEVE_FIN}') AS nouveaux_periode,
  COUNT(*) FILTER (disparu BETWEEN DATE '{RELEVE_DEBUT}' AND DATE '{RELEVE_FIN}') AS pertes_periode,
  COUNT(*)                                                                      AS stock
FROM jeux
GROUP BY GROUPING SETS ((jeu, ligne, groupe), (jeu, ligne))
HAVING NOT (ligne IS NOT DISTINCT FROM 'chaines' AND groupe IS NULL)
ORDER BY jeu DESC, ligne NULLS FIRST, groupe NULLS LAST
"""


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    SORTIES.mkdir(exist_ok=True)
    con = connexion("4GB")
    con.execute("SET threads=4")
    chaines = " OR ".join(f"lower(b.name) LIKE '{n}%'" for n in CHAINES_ANTIPARASITAIRES)
    con.execute(SQL_AVIS.format(chaines=chaines, fin=RELEVE_FIN,
                                salles=", ".join(f"'{c}'" for c in CID_SALLES_ESPAGNOLES)))

    n, distincts, sans_secteur, fiches_chaines = con.execute(
        "SELECT COUNT(*), COUNT(DISTINCT review_id), COUNT(*) FILTER (industry IS NULL), "
        "COUNT(DISTINCT cid) FILTER (chaine) FROM avis").fetchone()
    if n != distincts:
        raise SystemExit("La jointure a dupliqué des avis.")
    if sans_secteur:
        raise SystemExit(f"{sans_secteur} avis sans fiche dans businesses.")
    print(f"avis 4-5 étoiles retenus : {n:,}, fiches des chaînes : {fiches_chaines}"
          .replace(",", " "))

    pct = lambda s, d: f"{100 * s / d:.2f}" if d else ""
    with (SORTIES / "flux-4-5-etoiles.csv").open("w", encoding="utf-8") as sortie:
        sortie.write("jeu,secteur,flux_nouveaux_avis,flux_supprimes_7j,flux_pour_100,"
                     "periode_nouveaux_avis,periode_pertes,pertes_pour_100_nouveaux,"
                     "stock_avis,stock_pour_100\n")
        for jeu, ligne, groupe, fa, fs, np_, pp, st in con.execute(SQL_MESURES).fetchall():
            nom = ("Chaînes antiparasitaires" if ligne == "chaines"
                   else SECTEURS.get(groupe, groupe) if groupe else "Total")
            sortie.write(f"{jeu},{nom},{fa},{fs},{pct(fs, fa)},{np_},{pp},"
                         f"{pct(pp, np_)},{st},{pct(pp, st)}\n")
            print(f"{jeu:20s} {nom:25s} flux {fs:4d}/{fa:5d} = {pct(fs, fa):>5s} % | "
                  f"pertes {pp:4d}/{np_:5d} = {pct(pp, np_):>6s} % | "
                  f"stock {pp:4d}/{st:8d} = {pct(pp, st):>5s} %")
    print(f"\nécrit : {SORTIES / 'flux-4-5-etoiles.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
