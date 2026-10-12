#!/usr/bin/env python3
"""Textes à encoder sur Colab : data/local/pest_textes_colab.parquet

    PYTHONPATH=.venv/Lib/site-packages <python uv> etudes-ponctuelles/2026-09-30-avis-antiparasitaires/exporter_pour_colab.py

Ne sort de `reviews_pest_all.parquet` que ce dont l'encodage a besoin :
`review_id` et le texte, espaces de bord retirés (comme `01_embedding.py` du
21/09). Ni nom d'auteur, ni lien d'avis, ni lien de profil. Le texte reste une
donnée du client : le fichier se dépose sur le Drive du compte Cartelis et
s'efface de Colab et du Drive une fois les vecteurs récupérés.
"""
from __future__ import annotations

from pathlib import Path

import duckdb

RACINE = Path(__file__).resolve().parents[2]
SOURCE = RACINE / "data" / "local" / "reviews_pest_all.parquet"
SORTIE = RACINE / "data" / "local" / "pest_textes_colab.parquet"


def main() -> int:
    con = duckdb.connect(config={"memory_limit": "3GB"})
    con.execute(f"""COPY (SELECT review_id, TRIM(text) AS texte
                          FROM read_parquet('{SOURCE.as_posix()}') ORDER BY review_id)
                    TO '{SORTIE.as_posix()}' (FORMAT parquet, COMPRESSION zstd)""")
    n, distincts, textes = con.execute(
        f"SELECT COUNT(*), COUNT(DISTINCT review_id), COUNT(DISTINCT texte) "
        f"FROM read_parquet('{SORTIE.as_posix()}')").fetchone()
    print(f"écrit : {SORTIE} ({SORTIE.stat().st_size / 1024**2:.0f} Mo)\n"
          f"  {n:,} avis ({distincts:,} distincts), {textes:,} textes différents"
          .replace(",", " "))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
