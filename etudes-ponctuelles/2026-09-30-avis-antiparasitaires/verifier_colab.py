#!/usr/bin/env python3
"""Contrôle des vecteurs calculés sur Colab : data/embeddings/pest_e5base.parquet

    PYTHONPATH=.venv/Lib/site-packages <python uv> etudes-ponctuelles/2026-09-30-avis-antiparasitaires/verifier_colab.py

À lancer après avoir placé le fichier produit par `colab_embedding.ipynb` dans
`data/embeddings/`. Quatre contrôles :
  1. un vecteur par avis exporté, et aucun autre ;
  2. des vecteurs de norme 1 (à la précision du float16) ;
  3. deux avis au texte identique ont le même vecteur ;
  4. sur les avis déjà encodés en local le 21/09 (`03B_e5base.parquet`) avec le même
     texte, la similarité entre le vecteur Colab et le vecteur local, qui doit être
     proche de 1 (GPU et CPU ne font pas les calculs dans le même ordre).
"""
from __future__ import annotations

import sys
from pathlib import Path

import duckdb
import numpy as np
import pyarrow.parquet as pq

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RACINE = Path(__file__).resolve().parents[2]
COLAB = RACINE / "data" / "embeddings" / "pest_e5base.parquet"
EXPORT = RACINE / "data" / "local" / "pest_textes_colab.parquet"
LOCAL = RACINE / "data" / "embeddings" / "03B_e5base.parquet"
PANEL = RACINE / "data" / "bigquery" / "03B_reviews_panel_filtered_08_04_to_08_26.parquet"
SEUIL_CONCORDANCE = 0.999


def vecteurs(chemin):
    t = pq.read_table(chemin, columns=["review_id", "vecteur"])
    col = t.column("vecteur").combine_chunks()
    v = col.flatten().to_numpy(zero_copy_only=False).reshape(len(col), -1).astype("float32")
    return t.column("review_id").to_pylist(), v, t.schema.metadata or {}


def main() -> int:
    ids, v, meta = vecteurs(COLAB)
    print({k.decode(): x.decode() for k, x in meta.items()})
    ex = pq.read_table(EXPORT)
    ids_ex, textes = ex.column("review_id").to_pylist(), ex.column("texte").to_pylist()
    ok = True

    unique = len(set(ids)) == len(ids)
    meme = set(ids) == set(ids_ex)
    print(f"1. {len(ids):,} vecteurs, {v.shape[1]} dimensions ; identifiants uniques : {unique} ; "
          f"mêmes avis que l'export : {meme}".replace(",", " "))
    ok &= unique and meme and v.shape[1] == 768

    normes = np.linalg.norm(v, axis=1)
    print(f"2. normes entre {normes.min():.4f} et {normes.max():.4f}")
    ok &= bool(np.all(np.abs(normes - 1) < 5e-3))

    rang = {r: i for i, r in enumerate(ids)}
    premier, ecart = {}, 0.0
    for r, t in zip(ids_ex, textes):
        if t in premier:
            ecart = max(ecart, float(np.abs(v[rang[r]] - v[rang[premier[t]]]).max()))
        else:
            premier[t] = r
    print(f"3. textes identiques : écart maximal entre leurs vecteurs {ecart:.2e}")
    ok &= ecart == 0.0

    ids_l, v_l, _ = vecteurs(LOCAL)
    rang_l = {r: i for i, r in enumerate(ids_l)}
    con = duckdb.connect()
    con.execute("CREATE TEMP TABLE ids(review_id VARCHAR)")
    communs = [r for r in ids if r in rang_l]
    con.executemany("INSERT INTO ids VALUES (?)", [(r,) for r in communs])
    texte_03b = dict(con.execute(f"SELECT review_id, TRIM(text) FROM read_parquet('{PANEL.as_posix()}') "
                                 "JOIN ids USING (review_id)").fetchall())
    texte_ex = dict(zip(ids_ex, textes))
    memes = [r for r in communs if texte_03b.get(r) == texte_ex[r]]
    sims = np.array([float(v[rang[r]] @ v_l[rang_l[r]]) for r in memes])
    print(f"4. {len(communs)} avis déjà encodés le 21/09, dont {len(memes)} au texte inchangé : "
          f"similarité Colab / local min {sims.min():.5f}, médiane {np.median(sims):.5f} ; "
          f"{int((sims < SEUIL_CONCORDANCE).sum())} sous {SEUIL_CONCORDANCE}")
    ok &= bool(sims.min() >= SEUIL_CONCORDANCE)

    print("\nVECTEURS CONFORMES" if ok else "\nÉCART : ne pas utiliser ces vecteurs avant explication")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
