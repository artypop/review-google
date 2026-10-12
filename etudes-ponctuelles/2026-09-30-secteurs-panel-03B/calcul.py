#!/usr/bin/env python3
"""Avis et suppressions par secteur, sur le panel 03B.

    PYTHONPATH=.venv/Lib/site-packages <python uv> etudes-ponctuelles/2026-09-30-secteurs-panel-03B/calcul.py

Demande de Matthieu du 2026-09-30 : refaire les tableaux 1 et 2 de
`livrables/analyses-complémentaires.docx` (partie 1, toute la base) sur le
panel 03B. Écrit sans pandas : la règle Windows de contrôle des applications
bloque `pyarrow.compute` depuis le 2026-09-29.

------------------------------------------------------------------------------
LA POPULATION
------------------------------------------------------------------------------
`data/local/reviews_panel_features_03B.parquet` : avis publiés du 4 au 17 août
2026, suivis jusqu'au relevé du 24 août. 35 751 avis, 5 566 fiches, 1 355
suppressions (colonne `supprime`), identique à la table BigQuery (vérifié le
2026-09-28 par `03B_features_local.py`).

Secteur : colonne `industry` de la table.

Enseignes signalées : repérage du tableau 2 d'origine
(`2026-09-28-secteurs-et-concentration/calcul.py`), refait ici sur
`businesses.parquet` : les 2 salles espagnoles sur leur `cid`, les 4 chaînes
antiparasitaires sur le début du nom, ce qui attrape leurs succursales à
suffixe. Les colonnes du panel ne sont pas reprises : `chaine_antiparasitaire_us`
compare le nom exact et manque 9 succursales (342 avis, 9 suppressions),
`salle_de_sport_attaquee` compare le nom et prend 4 fiches de plus (13 avis,
0 suppression). Mesuré le 2026-09-30. Le 07C (section 4 du document) retire un
périmètre plus large, les 165 fiches antiparasitaires américaines.

Sorties : `sorties/A1-secteurs.csv`, `sorties/A1-secteurs-sans-enseignes.csv`.
"""
from __future__ import annotations

import csv
from pathlib import Path

import duckdb

DOSSIER = Path(__file__).resolve().parent
RACINE = DOSSIER.parent.parent
SORTIES = DOSSIER / "sorties"
PANEL = RACINE / "data" / "local" / "reviews_panel_features_03B.parquet"
FICHES = RACINE / "data" / "bigquery" / "businesses.parquet"

CID_SALLES_ATTAQUEES = ("3163466139043001754", "10346942689164695031")
RACINES_CHAINES_US = ("ecoshield pest solutions", "insight pest",
                      "pointe pest control", "bulwark exterminating")

ATTENDU = {"avis": 35_751, "suppressions": 1_355}

SECTEURS = {
    "automotive": "Automobile", "home_services": "Services à domicile",
    "healthcare": "Santé", "wellness_fitness": "Sport et bien-être",
    "food_beverage": "Restauration", "travel": "Voyage", "hospitality": "Hôtellerie",
}


def ecrire(con, sql, nom):
    rel = con.execute(sql)
    entetes = [c[0] for c in rel.description]
    lignes = rel.fetchall()
    SORTIES.mkdir(parents=True, exist_ok=True)
    with open(SORTIES / nom, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["secteur_fr"] + entetes)
        for l in lignes:
            w.writerow([SECTEURS[l[0]]] + list(l))
    print(f"  {nom:40s} {len(lignes):>6} lignes")


def main() -> int:
    con = duckdb.connect()
    con.execute("SET threads=2")
    chaines = " OR ".join(f"lower(b.name) LIKE '{r}%'" for r in RACINES_CHAINES_US)
    con.execute(f"""
        CREATE TEMP TABLE av AS
        SELECT a.industry, a.supprime,
               (a.cid IN {CID_SALLES_ATTAQUEES} OR {chaines}) AS enseigne_signalee
        FROM read_parquet('{PANEL.as_posix()}') a
        LEFT JOIN read_parquet('{FICHES.as_posix()}') b USING (cid)
    """)

    avis, supp = con.execute("SELECT COUNT(*), COUNT(*) FILTER (supprime) FROM av").fetchone()
    assert (avis, supp) == (ATTENDU["avis"], ATTENDU["suppressions"]), (avis, supp)

    for suffixe, filtre in (("", "TRUE"),
                            ("-sans-enseignes", "NOT enseigne_signalee")):
        ecrire(con, f"""
            SELECT industry AS secteur,
                   COUNT(*)                     AS avis,
                   ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS part_corpus_pct,
                   COUNT(*) FILTER (supprime)   AS suppressions,
                   ROUND(100.0 * COUNT(*) FILTER (supprime) / COUNT(*), 3) AS part_supprimee_pct
            FROM av WHERE {filtre}
            GROUP BY industry ORDER BY part_supprimee_pct DESC
        """, f"A1-secteurs{suffixe}.csv")

    con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
