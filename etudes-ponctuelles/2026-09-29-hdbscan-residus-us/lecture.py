#!/usr/bin/env python3
"""Lecture des groupes produits par calcul.py, pour les nommer.

    .venv/Scripts/python.exe etudes-ponctuelles/2026-09-29-hdbscan-residus-us/lecture.py [--exemples N]

Écran seulement : mots les plus caractéristiques de chaque groupe (c-TF-IDF,
comme BERTopic) et, avec --exemples, N textes tirés au hasard par groupe. Rien
de ce qui s'affiche n'est écrit sur disque : les mots peuvent contenir des
prénoms d'employés.

Écrit un seul fichier, `sorties/A5-marqueurs.csv`, des parts par groupe, sans
aucun mot :
  prenom_cite   un mot à majuscule suit « tech », « technician », « thanks
                to », « ask for », « shout out to », « with » ou « by », ou
                ouvre une phrase et précède « was », « did », « helped »…
                (repérage grossier : il sert à nommer les groupes)
  court         moins de 60 caractères
  exclamation   au moins un point d'exclamation
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer

DOSSIER = Path(__file__).resolve().parent
RACINE = DOSSIER.parents[1]
SORTIES = DOSSIER / "sorties"
PANEL = RACINE / "data" / "bigquery" / "03B_reviews_panel_filtered_08_04_to_08_26.parquet"

PRENOM = re.compile(r"\b(?:tech|technician|thanks to|thank you|ask for|shout ?out to|with|by)"
                    r"\s+([A-Z][a-z]{2,})\b"
                    r"|(?:^|[.!?]\s+)([A-Z][a-z]{2,})(?:\s+[A-Z][a-z]*\.?)?"
                    r"\s+(?:was|did|is|went|made|helped|came|provided|explained)\b")
NON_PRENOMS = {"The", "Their", "They", "This", "That", "Great", "Very", "Such", "Our", "My",
               "His", "Her", "All", "Everyone", "Excellent", "Amazing"}


def prenom_cite(texte: str) -> bool:
    return any(m and m not in NON_PRENOMS
               for paire in PRENOM.findall(texte) for m in paire)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--exemples", type=int, default=0)
    ap.add_argument("--groupes", type=str, default="",
                    help="population:vecteurs:groupe,... pour limiter l'affichage")
    args = ap.parse_args()

    m = pd.read_csv(SORTIES / "A3-appartenance-avis.csv", dtype={"review_id": str, "cid": str})
    con = duckdb.connect(config={"memory_limit": "2GB", "threads": 4})
    textes = con.execute("SELECT review_id, TRIM(text) AS texte FROM read_parquet(?) "
                         "WHERE text IS NOT NULL", [PANEL.as_posix()]).df()
    con.close()
    m = m.merge(textes, on="review_id", how="left", validate="many_to_one")
    m["prenom_cite"] = m["texte"].map(prenom_cite)
    m["court"] = m["texte"].str.len() < 60
    m["exclamation"] = m["texte"].str.contains("!", regex=False)

    cles = ["population", "vecteurs", "groupe"]
    marq = m.groupby(cles).agg(n_avis=("texte", "size"),
                               prenom_cite_pct=("prenom_cite", "mean"),
                               court_pct=("court", "mean"),
                               exclamation_pct=("exclamation", "mean"),
                               prenom_cite_supprimes_pct=("prenom_cite",
                                                          lambda s: s[m.loc[s.index, "supprime"]].mean()))
    marq = (100 * marq.drop(columns="n_avis")).round(1).join(marq["n_avis"]).reset_index()
    base = (m.groupby(["population", "vecteurs"])[["prenom_cite", "court", "exclamation"]]
            .mean().mul(100).round(1).reset_index().assign(groupe="population"))
    pd.concat([marq, base], ignore_index=True).to_csv(SORTIES / "A5-marqueurs.csv", index=False)

    choix = {tuple(x.split(":")) for x in args.groupes.split(",") if x}
    rng = np.random.default_rng(0)
    for (pop, vec), bloc in m[m["groupe"] >= 0].groupby(["population", "vecteurs"]):
        docs = bloc.groupby("groupe")["texte"].apply(" ".join)
        cv = CountVectorizer(stop_words="english", min_df=5, token_pattern=r"(?u)\b[a-zA-Z]{3,}\b")
        x = cv.fit_transform(docs.to_numpy()).astype(float)
        tf = x.multiply(1 / x.sum(axis=1)).tocsr()
        idf = np.log(1 + x.sum() / x.sum(axis=0).A1 / len(docs))
        score = tf.multiply(idf).tocsr()
        mots = np.array(cv.get_feature_names_out())
        for i, g in enumerate(docs.index):
            if choix and (pop, vec, str(g)) not in choix:
                continue
            ligne = score[i].toarray().ravel()
            b = bloc[bloc["groupe"] == g]
            print(f"\n{pop} {vec} groupe {g} : {len(b)} avis, {int(b['supprime'].sum())} supprimés")
            print("   ", ", ".join(mots[np.argsort(ligne)[::-1][:15]]))
            for t in b["texte"].sample(min(args.exemples, len(b)), random_state=rng.integers(1e9)):
                print("     -", t[:220].replace("\n", " "))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
