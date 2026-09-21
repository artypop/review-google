#!/usr/bin/env python3
"""Copie locale de tables BigQuery, en parquet, sans aucune transformation.

    python outils/tirer_tables.py reviews avis_features

Les tables descendent telles que BigQuery les construit. Aucune définition
n'est recalculée ici : `sql/01` et `sql/02` restent la seule source des
colonnes du panel. C'est la lecture qui devient locale.

Le tirage passe en flux : les lots arrivent de l'API Storage Read et partent au
fichier l'un après l'autre, donc une table de 3 Go ne monte jamais en mémoire.

Identifiants : ceux de la machine (`gcloud auth application-default login`).
Rien n'est lu dans le dépôt.

Destination : `data/bigquery/`, couvert par `.gitignore`. `reviews` porte le
texte des avis, les noms d'auteurs et les liens de profil, et ne doit jamais
entrer dans un fichier versionné.
"""

from __future__ import annotations

import argparse
import time

import pyarrow.parquet as pq
from google.cloud import bigquery

from local import COPIES

PROJET = "client-divers"
DATASET = "reviewflowz"


def tirer(client: bigquery.Client, nom: str) -> None:
    cible = COPIES / f"{nom}.parquet"
    depart, lignes, writer = time.time(), 0, None
    source = f"{PROJET}.{DATASET}.{nom}"

    for lot in client.list_rows(source).to_arrow_iterable():
        if writer is None:
            writer = pq.ParquetWriter(cible, lot.schema, compression="zstd")
        writer.write_batch(lot)
        lignes += lot.num_rows
        if lignes % 500_000 < lot.num_rows:
            print(f"  {nom} : {lignes:,} lignes", flush=True)

    if writer is None:
        print(f"{nom} : table vide, aucun fichier écrit")
        return
    writer.close()
    mo = cible.stat().st_size / 1024**2
    print(f"{nom:34s} {lignes:>10,} lignes  {mo:8.0f} Mo  {time.time() - depart:5.0f} s")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tables", nargs="+", help="noms des tables du dataset reviewflowz")
    args = parser.parse_args()

    COPIES.mkdir(parents=True, exist_ok=True)
    client = bigquery.Client(project=PROJET)
    for nom in args.tables:
        tirer(client, nom)


if __name__ == "__main__":
    main()
