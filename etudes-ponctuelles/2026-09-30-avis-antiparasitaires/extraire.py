#!/usr/bin/env python3
"""Avis avec texte des fiches antiparasitaires : data/local/reviews_pest_all.parquet

    PYTHONPATH=.venv/Lib/site-packages <python uv> etudes-ponctuelles/2026-09-30-avis-antiparasitaires/extraire.py

Demande de Matthieu du 2026-09-30.

  source   data/bigquery/reviews_doublons_cleaned_all.parquet : toute la base, sans
           les avis qui ont clignoté, une ligne par avis (la dernière). Tirée de
           BigQuery le 2026-09-30.
  fiches   `businesses.industry = 'home_services'` et « pest » dans le nom, sans
           tenir compte de la casse, plus la chaîne Bulwark Exterminating (nom
           commençant par « bulwark exterminating »), ajoutée par Matthieu le
           2026-09-30 : c'est l'une des quatre chaînes du projet et son nom ne
           porte pas « pest ». Au 2026-09-30 : 148 + 26 fiches, toutes
           américaines. Le repérage plus large du rapport (exterminat, termite,
           mosquito…) ajouterait encore 8 petites fiches, laissées de côté.
  avis     texte non vide après retrait des espaces de bord.

Sortie : toutes les colonnes de la source, plus `business_name`. Le fichier porte
le texte des avis, les noms et les liens des auteurs : il reste dans `data/`,
couvert par .gitignore, et ne doit jamais entrer dans un fichier versionné.
"""
from __future__ import annotations

import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "outils"))
from local import connexion  # noqa: E402

SOURCE = RACINE / "data" / "bigquery" / "reviews_doublons_cleaned_all.parquet"
BUSINESSES = RACINE / "data" / "bigquery" / "businesses.parquet"
SORTIE = RACINE / "data" / "local" / "reviews_pest_all.parquet"

SQL = f"""
SELECT r.*, b.name AS business_name
FROM read_parquet('{SOURCE.as_posix()}') r
JOIN read_parquet('{BUSINESSES.as_posix()}') b USING (cid)
WHERE b.industry = 'home_services'
  AND (b.name ILIKE '%pest%' OR lower(b.name) LIKE 'bulwark exterminating%')
  AND r.text IS NOT NULL AND TRIM(r.text) <> ''
"""


def main() -> int:
    con = connexion()
    con.execute("SET memory_limit='3GB'")
    SORTIE.parent.mkdir(parents=True, exist_ok=True)
    con.execute(f"COPY ({SQL}) TO '{SORTIE.as_posix()}' (FORMAT parquet, COMPRESSION zstd)")
    avis, distincts, supprimes, fiches, pays = con.execute(f"""
        SELECT COUNT(*), COUNT(DISTINCT review_id), COUNT_IF(deleted_detected_at IS NOT NULL),
               COUNT(DISTINCT cid),
               (SELECT string_agg(DISTINCT b.country, ', ')
                FROM read_parquet('{BUSINESSES.as_posix()}') b
                WHERE b.cid IN (SELECT cid FROM read_parquet('{SORTIE.as_posix()}')))
        FROM read_parquet('{SORTIE.as_posix()}')""").fetchone()
    print(f"écrit : {SORTIE} ({SORTIE.stat().st_size / 1024**2:.0f} Mo)\n"
          f"  {avis:,} avis ({distincts:,} distincts), {supprimes:,} supprimés, "
          f"{fiches} fiches, pays : {pays}".replace(",", " "))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
