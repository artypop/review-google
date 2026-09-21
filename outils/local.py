#!/usr/bin/env python3
"""Le socle du travail en local : où sont les copies, et comment les ouvrir.

Tout script local passe par `connexion()`. Une seule raison à cela, et elle
vaut d'être lue avant de s'en écarter.

------------------------------------------------------------------------------
LE FUSEAU HORAIRE, ET POURQUOI IL EST POSÉ ICI
------------------------------------------------------------------------------
BigQuery convertit un TIMESTAMP en date sur UTC. DuckDB utilise le fuseau de la
session, Europe/Paris sur nos machines. Un avis déposé le 12 mai à 23 h UTC
devient un avis du 13 mai en heure de Paris.

Mesuré le 2026-09-15 en rejouant `sql/01_selection_panel.sql` sur la copie
locale de `reviews` :

    sans SET TimeZone='UTC'   225 807 avis, 2 589 suppressions
    avec                      225 757 avis, 2 595 suppressions

202 avis entraient par la borne basse, 152 sortaient par la borne haute. Les
deux totaux paraissent justes et ne le sont pas tous les deux. `connexion()`
pose le fuseau, ce qui évite d'avoir à y penser à chaque script.
"""

from __future__ import annotations

from pathlib import Path

import duckdb

# La racine du dossier d'étude, quel que soit l'endroit d'où le script est lancé.
RACINE = Path(__file__).resolve().parent.parent
COPIES = RACINE / "data" / "bigquery"

# Les deux bornes de `sql/01_selection_panel.sql`, recopiées ici pour que les
# reconstructions locales n'aient pas à les redéfinir chacune de leur côté.
PUBLICATION_DEBUT = "2026-05-13"
PUBLICATION_FIN = "2026-08-16"
PREMIERE_VAGUE = "2026-08-11"
DERNIERE_VAGUE = "2026-08-24"


def connexion(memoire: str = "6GB") -> duckdb.DuckDBPyConnection:
    """Une connexion DuckDB en UTC, avec une limite de mémoire explicite.

    Les tables présentes dans `data/bigquery/` sont exposées comme des vues
    portant le nom de la table BigQuery d'origine.

    Le nom de vue est entre guillemets. BigQuery accepte un nom de table qui
    commence par un chiffre, DuckDB le refuse sans guillemets, et la connexion
    échouait alors pour TOUS les scripts du projet dès qu'un tel fichier était
    présent dans `data/bigquery/` — constaté le 2026-09-21 avec
    `03_reviews_panel_filtered_08_05_to_08_26`.

    Conséquence à connaître : une vue dont le nom commence par un chiffre
    s'interroge elle aussi entre guillemets.

        SELECT * FROM "03_reviews_panel_filtered_08_05_to_08_26"
    """
    con = duckdb.connect(config={"memory_limit": memoire})
    con.execute("SET TimeZone='UTC'")
    for fichier in sorted(COPIES.glob("*.parquet")):
        chemin = fichier.as_posix()
        con.execute(
            f'CREATE VIEW "{fichier.stem}" AS SELECT * FROM read_parquet(\'{chemin}\')')
    return con


def tables_disponibles() -> list[str]:
    return sorted(f.stem for f in COPIES.glob("*.parquet"))


if __name__ == "__main__":
    con = connexion()
    print(f"Copies dans {COPIES}\n")
    for nom in tables_disponibles():
        n = con.execute(f'SELECT COUNT(*) FROM "{nom}"').fetchone()[0]
        mo = (COPIES / f"{nom}.parquet").stat().st_size / 1024**2
        print(f"  {nom:34s} {n:>10,} lignes  {mo:7.1f} Mo")
