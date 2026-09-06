"""
Interroger les tables d'analyse en SQL, sans rien installer de plus.

Les trois tables construites par build_tables.py sont déjà chargées sous les noms
`avis`, `etablissements` et `suivi`. Les fichiers bruts de l'export le sont aussi, sous
`reviews_brut`, `businesses_brut`, `histograms_brut`, `waves_brut`.

    # voir ce qui existe et à quoi ça sert
    uv run scripts/query.py --tables
    uv run scripts/query.py --colonnes avis

    # poser une question
    uv run scripts/query.py "SELECT star, count(*) FROM avis WHERE is_fresh GROUP BY 1"

    # rejouer une requête d'exemple (les mêmes que dans le README)
    uv run scripts/query.py --exemple note

    # sortir un CSV pour Excel
    uv run scripts/query.py "SELECT ..." --csv data/exports_manuels/ma_question.csv

    # console interactive : on tape du SQL, ligne à ligne, jusqu'à "quit"
    uv run scripts/query.py
"""

import argparse
import pathlib
import sys

import duckdb
import pandas as pd

BUILD = pathlib.Path("data/build")
RAW = pathlib.Path("data/exports/exports")

TABLES = {
    "avis": (BUILD / "reviews_features.parquet",
             "1 ligne par avis (4,88 M). Corpus entier. `is_fresh` = avis de moins de 30 jours."),
    "etablissements": (BUILD / "business_features.parquet",
                       "1 ligne par établissement (9 048). Vélocité, intensité de purge, note."),
    "suivi": (BUILD / "fresh_hazard.parquet",
              "1 ligne par avis frais ET par passage du robot. `died` = a disparu à ce passage."),
    "reviews_brut": (RAW / "reviews.parquet", "Export d'origine, non filtré. Voir le README de l'export."),
    "businesses_brut": (RAW / "businesses.parquet", "Export d'origine."),
    "histograms_brut": (RAW / "histograms.parquet", "Répartition des étoiles par passage."),
    "waves_brut": (RAW / "waves.parquet", "Les 14 passages du robot, avec leurs dates."),
}

EXEMPLES = {
    "note": ("Risque de suppression par note, sur les avis frais", """
        SELECT star AS note,
               count(*)                        AS avis,
               count(*) FILTER (deleted)       AS supprimes,
               round(100.0 * count(*) FILTER (deleted) / count(*), 2) AS pct
        FROM avis WHERE is_fresh GROUP BY 1 ORDER BY 1"""),
    "age": ("Risque par passage selon l'âge de l'avis — la courbe centrale de l'étude", """
        SELECT CASE WHEN age_days < 3 THEN '0-2 j'   WHEN age_days < 7  THEN '3-6 j'
                    WHEN age_days < 14 THEN '7-13 j' WHEN age_days < 21 THEN '14-20 j'
                    WHEN age_days < 30 THEN '21-29 j' ELSE '30 j et plus' END AS age,
               count(*)                        AS observations,
               sum(died::INT)                  AS disparitions,
               round(100.0 * sum(died::INT) / count(*), 4) AS risque_pct
        FROM suivi GROUP BY 1 ORDER BY min(age_days)"""),
    "rafale": ("Le résultat principal : auteurs publiant plusieurs avis le même jour", """
        SELECT author_same_day_burst          AS rafale,
               count(*)                        AS observations,
               sum(died::INT)                  AS disparitions,
               round(100.0 * sum(died::INT) / count(*), 3) AS risque_pct
        FROM suivi GROUP BY 1 ORDER BY 1"""),
    "concentration": ("Combien d'établissements concentrent les suppressions", """
        SELECT CASE WHEN n_deleted = 0 THEN 'aucune suppression'
                    WHEN purge_share < 0.01 THEN 'moins de 1 % de ses avis'
                    WHEN purge_share < 0.05 THEN '1 à 5 %'
                    WHEN purge_share < 0.20 THEN '5 à 20 %'
                    ELSE '20 % et plus' END    AS intensite,
               count(*)                        AS etablissements,
               sum(n_deleted)                  AS suppressions,
               round(100.0 * sum(n_deleted) / 5230.0, 1) AS pct_du_total
        FROM etablissements GROUP BY 1 ORDER BY 2 DESC"""),
    "velocite": ("Vitesse de collecte des avis et suppressions, au niveau établissement", """
        SELECT CASE WHEN velocity_30d < 0.01 THEN 'moins de 1 %' WHEN velocity_30d < 0.03 THEN '1 à 3 %'
                    WHEN velocity_30d < 0.10 THEN '3 à 10 %' ELSE '10 % et plus' END AS vitesse,
               count(*)                        AS etablissements,
               round(100.0 * avg(touched::INT), 1) AS pct_touches,
               round(100.0 * sum(n_deleted) / sum(n_reviews_panel), 4) AS pct_avis_supprimes
        FROM etablissements WHERE n_reviews_panel >= 100 GROUP BY 1 ORDER BY min(velocity_30d)"""),
    "top": ("Les établissements les plus purgés (sans nom : données personnelles)", """
        SELECT region, industry AS secteur, bucket AS taille, country AS pays,
               n_reviews_panel AS avis, n_deleted AS supprimes,
               round(100.0 * purge_share, 1) AS pct_de_la_fiche
        FROM etablissements ORDER BY n_deleted DESC LIMIT 15"""),
}


def connect() -> duckdb.DuckDBPyConnection:
    c = duckdb.connect(config={'memory_limit': '1GB'})
    missing = []
    for name, (path, _) in TABLES.items():
        if path.exists():
            c.sql(f"CREATE VIEW {name} AS SELECT * FROM '{path.as_posix()}'")
        else:
            missing.append((name, path))
    if missing:
        for name, path in missing:
            print(f"  (absent : {name} -> {path})", file=sys.stderr)
        if not (BUILD / "reviews_features.parquet").exists():
            sys.exit("Tables non construites. Lancer : uv run scripts/build_tables.py")
    return c


def show_tables(c: duckdb.DuckDBPyConnection) -> None:
    print("\nTables disponibles :\n")
    for name, (path, desc) in TABLES.items():
        if not path.exists():
            print(f"  {name:18} (absent)")
            continue
        n = c.sql(f"SELECT count(*) FROM {name}").fetchone()[0]
        nf = f"{n:,}".replace(",", " ")
        print(f"  {name:18} {nf:>11} lignes   {desc}")
    print("\n  Détail des colonnes :  uv run scripts/query.py --colonnes avis\n")


def show_columns(c: duckdb.DuckDBPyConnection, table: str) -> None:
    if table not in TABLES:
        sys.exit(f"Table inconnue : {table}. Connues : {', '.join(TABLES)}")
    df = c.sql(f"DESCRIBE SELECT * FROM {table}").df()[["column_name", "column_type"]]
    print(f"\n{table} — {TABLES[table][1]}\n")
    print(df.to_string(index=False))
    print()


def run(c: duckdb.DuckDBPyConnection, sql: str, csv: str | None) -> None:
    try:
        df = c.sql(sql).df()
    except Exception as exc:  # noqa: BLE001 — on veut afficher l'erreur SQL telle quelle
        print(f"Erreur SQL : {exc}", file=sys.stderr)
        return
    if csv:
        out = pathlib.Path(csv)
        out.parent.mkdir(parents=True, exist_ok=True)
        # séparateur ; et virgule décimale : Excel francophone ouvre le fichier directement
        df.to_csv(out, index=False, sep=";", decimal=",", encoding="utf-8-sig")
        print(f"Écrit : {out}  ({len(df)} lignes)")
        return
    with pd.option_context("display.max_rows", 200, "display.width", 200):
        print(df.to_string(index=False))


def interactive(c: duckdb.DuckDBPyConnection) -> None:
    show_tables(c)
    print("Tapez du SQL puis Entrée. « quit » pour sortir.\n")
    while True:
        try:
            sql = input("sql> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if sql.lower() in {"quit", "exit", "q"}:
            return
        if sql:
            run(c, sql, None)


def main() -> None:
    p = argparse.ArgumentParser(
        description="Interroger les tables d'analyse en SQL.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__)
    p.add_argument("sql", nargs="?", help="requête SQL ; sans argument, ouvre la console")
    p.add_argument("--tables", action="store_true", help="lister les tables")
    p.add_argument("--colonnes", metavar="TABLE", help="lister les colonnes d'une table")
    p.add_argument("--exemple", metavar="NOM", help=f"exécuter un exemple : {', '.join(EXEMPLES)}")
    p.add_argument("--exemples", action="store_true", help="lister les exemples disponibles")
    p.add_argument("--csv", metavar="CHEMIN", help="écrire le résultat en CSV au lieu de l'afficher")
    a = p.parse_args()

    if a.exemples:
        print("\nExemples disponibles :\n")
        for k, (desc, _) in EXEMPLES.items():
            print(f"  {k:15} {desc}")
        print("\n  uv run scripts/query.py --exemple note\n")
        return

    c = connect()
    if a.tables:
        show_tables(c)
    elif a.colonnes:
        show_columns(c, a.colonnes)
    elif a.exemple:
        if a.exemple not in EXEMPLES:
            sys.exit(f"Exemple inconnu. Connus : {', '.join(EXEMPLES)}")
        desc, sql = EXEMPLES[a.exemple]
        print(f"\n{desc}\n{sql.strip()}\n")
        run(c, sql, a.csv)
    elif a.sql:
        run(c, a.sql, a.csv)
    else:
        interactive(c)


if __name__ == "__main__":
    main()
