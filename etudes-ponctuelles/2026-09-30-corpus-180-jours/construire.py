#!/usr/bin/env python3
"""Corpus des avis récents : data/local/reviews_doublons_cleaned_180.parquet

    PYTHONPATH=.venv/Lib/site-packages <python uv> etudes-ponctuelles/2026-09-30-corpus-180-jours/construire.py

Demande de Matthieu du 2026-09-30.

  source   data/bigquery/reviews_doublons_cleaned.parquet : copie locale de la
           table BigQuery du 2026-09-17, une ligne par avis.
  borne    avis créés au plus 180 jours avant la première vague de scraping.
           Première vague : 2026-08-11 (table `waves`, vague 1). Borne basse :
           2026-08-11 - 180 jours = 2026-02-12, incluse. Aucune borne haute :
           les avis publiés pendant la collecte, jusqu'au 2026-08-24, restent.
  dates    règle de Matthieu du 2026-09-30 : toute colonne horodatée devient une
           DATE, l'heure est retirée. Le passage en date se fait en UTC
           (`connexion()`), comme BigQuery. Colonnes concernées : created_at,
           updated_at, reply_date, first_seen_at, last_seen_at,
           deleted_detected_at.

Sortie : toutes les colonnes de la source, dans le même ordre. Le fichier porte
le texte des avis, les noms et les liens des auteurs : il reste dans `data/`,
couvert par .gitignore, et ne doit jamais entrer dans un fichier versionné.
"""
from __future__ import annotations

import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "outils"))
from local import PREMIERE_VAGUE, connexion  # noqa: E402

JOURS = 180
SORTIE = RACINE / "data" / "local" / f"reviews_doublons_cleaned_{JOURS}.parquet"
HORODATAGES = ["created_at", "updated_at", "reply_date",
               "first_seen_at", "last_seen_at", "deleted_detected_at"]


def main() -> int:
    con = connexion("4GB")
    colonnes = [c for c, *_ in con.execute("DESCRIBE reviews_doublons_cleaned").fetchall()]
    assert set(HORODATAGES) <= set(colonnes), set(HORODATAGES) - set(colonnes)
    reste = [c for c, t, *_ in con.execute("DESCRIBE reviews_doublons_cleaned").fetchall()
             if "TIMESTAMP" in t and c not in HORODATAGES]
    assert not reste, f"colonnes horodatées non prévues : {reste}"

    premiere = con.execute(
        "SELECT CAST(MIN(started_at) AS DATE) FROM waves WHERE wave = 1").fetchone()[0]
    assert str(premiere) == PREMIERE_VAGUE, premiere
    borne = con.execute(
        f"SELECT DATE '{PREMIERE_VAGUE}' - INTERVAL {JOURS} DAY").fetchone()[0].date()

    select = ", ".join(f"CAST({c} AS DATE) AS {c}" if c in HORODATAGES else c
                       for c in colonnes)
    sql = f"""
        SELECT {select}
        FROM reviews_doublons_cleaned
        WHERE CAST(created_at AS DATE) >= DATE '{borne}'
    """
    SORTIE.parent.mkdir(parents=True, exist_ok=True)
    con.execute(f"COPY ({sql}) TO '{SORTIE.as_posix()}' (FORMAT parquet, COMPRESSION zstd)")

    avis, distincts, fiches, supprimes, debut, fin = con.execute(f"""
        SELECT COUNT(*), COUNT(DISTINCT review_id), COUNT(DISTINCT cid),
               COUNT_IF(deleted_detected_at IS NOT NULL),
               MIN(created_at), MAX(created_at)
        FROM read_parquet('{SORTIE.as_posix()}')""").fetchone()
    n = lambda x: f"{x:,}".replace(",", " ")
    total = con.execute("SELECT COUNT(*) FROM reviews_doublons_cleaned").fetchone()[0]
    print(f"première vague {premiere}, borne basse {borne} incluse\n"
          f"écrit : {SORTIE} ({SORTIE.stat().st_size / 1024**2:.0f} Mo)\n"
          f"  {n(avis)} avis ({n(distincts)} distincts) sur {n(total)} dans la source, "
          f"{n(fiches)} fiches, {n(supprimes)} avec deleted_detected_at\n"
          f"  created_at du {debut} au {fin}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
