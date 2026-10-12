#!/usr/bin/env python3
"""Qui sont les copies et quasi-copies (similarité ≥ 0,97) du panel 03B ?

    PYTHONPATH=.venv/Lib/site-packages <python uv> etudes-ponctuelles/2026-09-29-quasi-copies/calcul.py [--min-caracteres 30] [--exemples N]

Demande de Matthieu du 2026-09-29, après la section 5 de
`livrables/regroupement-textes-us.docx` (copie : risque ×12).

Population : les avis dont le plus proche voisin du panel a une similarité de
0,97 ou plus (`sim_max` de `2026-09-28-embeddings-further/sorties/
A5-similarite-avis.csv`) et dont le texte fait au moins 80 caractères (règle du
28/09 : 149 avis) ou `--min-caracteres`.

Pour chacun, son plus proche voisin est recalculé sur les 26 168 vecteurs, puis
la paire est décrite :
  même auteur        même `author_key` (table locale 03B, hachage du lien)
  même fiche         même `cid`
  même enseigne      mêmes deux premiers mots du nom de fiche, en minuscules
  texte identique    textes égaux après passage en minuscules et retrait des
                     espaces et de la ponctuation
  écart de dépôt     jours entre les deux `created_at`
  même note

Type de paire, du plus précis au plus large :
  même auteur, même fiche            doublon
  même auteur, autre fiche           un auteur, plusieurs fiches
  autre auteur, même fiche           gabarit sur une fiche
  autre auteur, même enseigne        gabarit sur une enseigne
  autre auteur, autre enseigne       rencontre

Sorties : `sorties/` (80 caractères) ou `sorties/min<N>/` : `A1-types.csv`, `sorties/A2-paires.csv` (identifiants et
drapeaux, aucun texte, aucun nom). `--exemples N` affiche N textes par type à
l'écran, sans rien écrire.
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

import duckdb
import numpy as np
import pyarrow.parquet as pq

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DOSSIER = Path(__file__).resolve().parent
RACINE = DOSSIER.parents[1]
SORTIES = DOSSIER / "sorties"
VECTEURS = RACINE / "data" / "embeddings" / "03B_e5base.parquet"
CLASSES = RACINE / "etudes-ponctuelles" / "2026-09-28-embeddings-further" / "sorties" / "A5-similarite-avis.csv"
LOCALE = RACINE / "data" / "local" / "reviews_panel_features_03B.parquet"
PANEL = RACINE / "data" / "bigquery" / "03B_reviews_panel_filtered_08_04_to_08_26.parquet"
BUSINESSES = RACINE / "data" / "bigquery" / "businesses.parquet"
TYPES = ["doublon", "un auteur, plusieurs fiches", "gabarit sur une fiche",
         "gabarit sur une enseigne", "rencontre"]


def normaliser(t: str) -> str:
    return re.sub(r"[\W_]+", "", t.lower())


def enseigne(nom: str | None) -> str:
    return " ".join((nom or "").lower().split()[:2])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--exemples", type=int, default=0)
    ap.add_argument("--min-caracteres", type=int, default=80)
    args = ap.parse_args()
    sorties = SORTIES if args.min_caracteres == 80 else SORTIES / f"min{args.min_caracteres}"

    t = pq.read_table(VECTEURS, columns=["review_id", "cid", "note", "supprime",
                                         "enseigne_signalee", "n_caracteres", "vecteur"])
    rid = t.column("review_id").to_pylist()
    vec = t.column("vecteur").combine_chunks()
    v = vec.flatten().to_numpy(zero_copy_only=False).reshape(len(vec), -1).astype("float32")
    with CLASSES.open(encoding="utf-8") as f:
        sim_max = {r["review_id"]: float(r["sim_max"]) for r in csv.DictReader(f)}
    longueur = t.column("n_caracteres").to_pylist()
    cibles = [i for i, r in enumerate(rid)
              if sim_max[r] >= 0.97 and longueur[i] >= args.min_caracteres]
    print(f"{len(cibles)} avis : similarité ≥ 0,97, au moins {args.min_caracteres} caractères")

    sims = v[cibles] @ v.T
    sims[np.arange(len(cibles)), cibles] = -1
    voisin = sims.argmax(axis=1)
    sim = sims[np.arange(len(cibles)), voisin]

    loc = pq.read_table(LOCALE, columns=["review_id", "author_key", "region"])
    auteur = dict(zip(loc.column("review_id").to_pylist(), loc.column("author_key").to_pylist()))
    region = dict(zip(loc.column("review_id").to_pylist(), loc.column("region").to_pylist()))
    b = pq.read_table(BUSINESSES, columns=["cid", "name", "industry"])
    nom = dict(zip(b.column("cid").to_pylist(), b.column("name").to_pylist()))
    secteur = dict(zip(b.column("cid").to_pylist(), b.column("industry").to_pylist()))
    ids = sorted({rid[i] for i in cibles} | {rid[j] for j in voisin})
    con = duckdb.connect(config={"memory_limit": "2GB", "threads": 4})
    con.execute("CREATE TEMP TABLE ids(review_id VARCHAR)")
    con.executemany("INSERT INTO ids VALUES (?)", [(i,) for i in ids])
    info = {r[0]: r[1:] for r in con.execute(
        f"SELECT p.review_id, TRIM(p.text), epoch(p.created_at) FROM read_parquet('{PANEL.as_posix()}') p "
        "JOIN ids USING (review_id)").fetchall()}

    cid = t.column("cid").to_pylist()
    note = t.column("note").to_pylist()
    supp = t.column("supprime").to_pylist()
    ens_sig = t.column("enseigne_signalee").to_pylist()
    paires = []
    for k, i in enumerate(cibles):
        j = int(voisin[k])
        a, bb = rid[i], rid[j]
        meme_auteur = auteur.get(a) is not None and auteur.get(a) == auteur.get(bb)
        meme_fiche = cid[i] == cid[j]
        meme_enseigne = meme_fiche or enseigne(nom.get(cid[i])) == enseigne(nom.get(cid[j]))
        type_ = (TYPES[0] if meme_auteur and meme_fiche else TYPES[1] if meme_auteur
                 else TYPES[2] if meme_fiche else TYPES[3] if meme_enseigne else TYPES[4])
        ta, tb = info[a][0], info[bb][0]
        premier_est_a = info[a][1] <= info[bb][1]
        paires.append({
            "review_id": a, "voisin": bb, "similarite": round(float(sim[k]), 4), "type": type_,
            "texte_identique": normaliser(ta) == normaliser(tb),
            "ecart_depot_jours": round(abs(info[a][1] - info[bb][1]) / 86400, 2),
            "meme_note": note[i] == note[j], "note": note[i],
            "n_caracteres": longueur[i],
            "region": region.get(a), "secteur": secteur.get(cid[i]),
            "enseigne_signalee": ens_sig[i],
            "supprime": supp[i], "voisin_supprime": supp[j],
            "est_le_premier_depose": premier_est_a, "_texte": ta, "_voisin_texte": tb,
        })

    sorties.mkdir(parents=True, exist_ok=True)
    garde = [k for k in paires[0] if not k.startswith("_")]
    with (sorties / "A2-paires.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=garde)
        w.writeheader(); w.writerows({k: p[k] for k in garde} for p in paires)

    lignes = []
    for ty in TYPES + ["tous"]:
        g = [p for p in paires if ty in ("tous", p["type"])]
        if not g:
            continue
        ecarts = sorted(p["ecart_depot_jours"] for p in g)
        lignes.append({
            "type": ty, "avis": len(g), "supprimes": sum(p["supprime"] for p in g),
            "part_supprimee_pct": round(100 * np.mean([p["supprime"] for p in g]), 1),
            "texte_identique_pct": round(100 * np.mean([p["texte_identique"] for p in g]), 1),
            "meme_note_pct": round(100 * np.mean([p["meme_note"] for p in g]), 1),
            "note_5_pct": round(100 * np.mean([p["note"] == 5 for p in g]), 1),
            "ecart_depot_median_jours": round(float(np.median(ecarts)), 2),
            "ecart_moins_d_un_jour_pct": round(100 * np.mean([e < 1 for e in ecarts]), 1),
            "US_pct": round(100 * np.mean([p["region"] == "US" for p in g]), 1),
            "enseignes_signalees_pct": round(100 * np.mean([p["enseigne_signalee"] for p in g]), 1),
            "supprime_si_premier_depose_pct": round(100 * np.mean(
                [p["supprime"] for p in g if p["est_le_premier_depose"]] or [np.nan]), 1),
            "supprime_si_second_depose_pct": round(100 * np.mean(
                [p["supprime"] for p in g if not p["est_le_premier_depose"]] or [np.nan]), 1),
        })
    with (sorties / "A1-types.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(lignes[0]))
        w.writeheader(); w.writerows(lignes)
    for l in lignes:
        print(l)

    if args.exemples:
        rng = np.random.default_rng(0)
        vus = set()
        for ty in TYPES:
            g = [p for p in paires if p["type"] == ty and frozenset((p["review_id"], p["voisin"])) not in vus]
            print(f"\n===== {ty} : {len(g)} avis =====")
            for k in rng.permutation(len(g))[:args.exemples]:
                p = g[k]; vus.add(frozenset((p["review_id"], p["voisin"])))
                print(f"-- sim {p['similarite']}, {p['note']}★ {p['secteur']} {p['region']}, écart "
                      f"{p['ecart_depot_jours']} j, supprimé {p['supprime']} / voisin {p['voisin_supprime']}")
                print("   A:", p["_texte"][:260].replace("\n", " "))
                print("   B:", p["_voisin_texte"][:260].replace("\n", " "))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
