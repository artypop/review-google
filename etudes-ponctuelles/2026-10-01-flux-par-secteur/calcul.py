#!/usr/bin/env python3
"""Suppressions par secteur sur le flux des nouveaux avis, comparées au stock.

    PYTHONPATH=.venv/Lib/site-packages <python uv> etudes-ponctuelles/2026-10-01-flux-par-secteur/calcul.py

Demande d'Axel (réunion du 2026-10-01), transmise par Matthieu : « sur 100
nouveaux avis, combien j'en perds », par secteur.

  corpus       reviews_doublons_cleaned_all, caractéristiques de
               `03C_features_corpus.py` (suppression : absent deux jours de
               suite ou plus).
  flux         avis publiés du 11 au 15 août 2026, chacun suivi 8 jours après
               sa publication. Le 15 août est la dernière date possible : une
               disparition doit commencer au plus tard le 23 pour être
               confirmée au relevé du 24.
  supprimés    disparition commencée au plus tard 8 jours après la publication.
  stock        tous les avis qui pouvaient être vus disparaître pendant le
               relevé, toutes dates de publication ; part supprimée du 11 au
               24 août.
Les avis des 3 fiches qui ne sont plus relevées avant le 24 août sont écartés
du flux (leur suivi s'arrête avant les 8 jours).

Sortie : `sorties/flux-par-secteur.csv`, avec et sans les 6 enseignes.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import duckdb

DOSSIER = Path(__file__).resolve().parent
RACINE = DOSSIER.parents[1]
SORTIES = DOSSIER / "sorties"
CORPUS = RACINE / "data" / "bigquery" / "reviews_doublons_cleaned_all.parquet"
FLUX_DEBUT, FLUX_FIN, JOURS = "2026-08-11", "2026-08-15", 8
SECTEURS = {"automotive": "Automobile", "home_services": "Services à domicile",
            "healthcare": "Santé", "wellness_fitness": "Sport et bien-être",
            "food_beverage": "Restauration", "travel": "Voyage", "hospitality": "Hôtellerie"}


def features() -> Path:
    chemin = RACINE / "logistic-regression-study" / "python" / "03C_features_corpus.py"
    spec = importlib.util.spec_from_file_location("features_corpus", chemin)
    f03c = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(f03c)
    table = f03c.chemin_features(CORPUS)
    if not table.exists() or any(table.stat().st_mtime < s.stat().st_mtime
                                 for s in f03c.sources(CORPUS)):
        f03c.construire(CORPUS)
    return table


def main() -> int:
    SORTIES.mkdir(exist_ok=True)
    con = duckdb.connect(config={"memory_limit": "4GB"})
    con.execute(f"CREATE VIEW f AS SELECT * FROM read_parquet('{features().as_posix()}')")
    sql = f"""
    WITH base AS (
      SELECT industry, chaine_antiparasitaire OR salle_espagnole AS enseigne, supprime,
             created_at_day BETWEEN DATE '{FLUX_DEBUT}' AND DATE '{FLUX_FIN}'
               AND fin_suivi_ok                                        AS flux,
             supprime AND date_diff('day', created_at_day, date_suppression) <= {JOURS}
                                                                       AS supprime_8j,
             fenetre_observation_j > 0                                 AS exposable
      FROM (SELECT *, NOT fiche_plus_relevee AS fin_suivi_ok FROM f)
    )
    SELECT jeu, industry,
           COUNT(*) FILTER (flux)                AS nouveaux_avis,
           COUNT(*) FILTER (flux AND supprime_8j) AS supprimes_8j,
           COUNT(*) FILTER (exposable)           AS avis_stock,
           COUNT(*) FILTER (exposable AND supprime) AS supprimes_stock
    FROM base, (VALUES ('toutes les fiches'), ('sans les 6 enseignes')) j(jeu)
    WHERE jeu = 'toutes les fiches' OR NOT enseigne
    GROUP BY GROUPING SETS ((jeu, industry), (jeu))
    ORDER BY jeu DESC, industry NULLS LAST
    """
    lignes = con.execute(sql).fetchall()
    with (SORTIES / "flux-par-secteur.csv").open("w", encoding="utf-8") as sortie:
        sortie.write("jeu,secteur,nouveaux_avis,supprimes_8j,pour_100_nouveaux,"
                     "avis_stock,supprimes_stock,pour_100_stock\n")
        for jeu, ind, n, s, ns, ss in lignes:
            nom = SECTEURS.get(ind, "Total") if ind else "Total"
            sortie.write(f"{jeu},{nom},{n},{s},{100 * s / n:.2f},{ns},{ss},{100 * ss / ns:.3f}\n")
            print(f"{jeu:22s} {nom:20s} {n:6d} {s:4d} {100 * s / n:5.2f} % | "
                  f"{ns:8d} {ss:5d} {100 * ss / ns:6.3f} %")
    print(f"\nécrit : {SORTIES / 'flux-par-secteur.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
