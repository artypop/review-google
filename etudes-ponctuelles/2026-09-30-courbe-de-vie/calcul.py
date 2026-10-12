#!/usr/bin/env python3
"""Survie des avis publiés pendant le relevé, jour d'existence par jour d'existence.

    PYTHONPATH=.venv/Lib/site-packages <python uv> etudes-ponctuelles/2026-09-30-courbe-de-vie/calcul.py
    PYTHONPATH=.venv/Lib/site-packages <python uv> etudes-ponctuelles/2026-09-30-courbe-de-vie/ajout_word.py

Demande de Matthieu du 2026-10-01, sur le modèle de
`livrables/restitution/taux de survie.png`. Deux figures dans `sorties/` :

  taux_survie.png             part des avis encore en ligne à chaque jour
                              d'existence ;
  suppressions_par_jour.png   suppressions de chaque jour d'existence, pour
                              10 000 avis ayant atteint ce jour.

------------------------------------------------------------------------------
LES AVIS
------------------------------------------------------------------------------
`reviews_doublons_cleaned_all`, avis publiés du 11 au 24 août 2026 : 32 997.
Suppression : absent deux jours de suite ou plus (`03C_features_corpus.py`).
Jour d'existence d'une suppression : premier jour d'absence moins jour de
publication.

------------------------------------------------------------------------------
LE CALCUL
------------------------------------------------------------------------------
Pour chaque jour d'existence k :
  avis ayant atteint k   avis encore en ligne au jour k, pendant la période où
                         une disparition pouvait être constatée (du lendemain de
                         leur premier relevé à la veille du dernier relevé de
                         leur fiche) ;
  supprimés au jour k    ceux d'entre eux dont la disparition commence ce jour.
Le taux du jour est leur rapport. La survie au jour k est le produit des parts
gardées des jours 1 à k : un avis publié le 20 août ne compte que pour ses
premiers jours, sans fausser les suivants.

Jour 12 au plus : un avis publié le 11 août atteint son 13e jour le 24, dernier
relevé, où deux jours d'absence ne peuvent plus être constatés.

Au jour 1, seuls les avis relevés le jour même de leur publication comptent
(3 428) : les autres sont vus pour la première fois à 1 jour, et ne peuvent
disparaître qu'à partir du 2e.

Mesuré le 2026-10-01 : le pic du 7e jour se répète chaque jour du 18 au 23 août,
sur 13 à 29 fiches chaque fois. Il ne vient pas d'une purge datée.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import duckdb
import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

DOSSIER = Path(__file__).resolve().parent
RACINE = DOSSIER.parent.parent
SORTIES = DOSSIER / "sorties"
CORPUS = RACINE / "data" / "bigquery" / "reviews_doublons_cleaned_all.parquet"
PUBLICATION_DEBUT, PUBLICATION_FIN = "2026-08-11", "2026-08-24"
JOURS = range(1, 13)

# Mêmes couleurs que les figures du 07E.
COULEUR_FIGURE = "#2a78d6"
NOM = {"sans_enseignes": "sans les 6 enseignes", "toutes_fiches": "tous les avis"}
ENCRE, ENCRE_2, GRILLE, FOND = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"


def features() -> Path:
    """La table de `03C_features_corpus.py` pour le corpus, construite si besoin."""
    chemin = RACINE / "logistic-regression-study" / "python" / "03C_features_corpus.py"
    spec = importlib.util.spec_from_file_location("features_corpus", chemin)
    f03c = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(f03c)
    table = f03c.chemin_features(CORPUS)
    if not table.exists() or any(table.stat().st_mtime < s.stat().st_mtime
                                 for s in f03c.sources(CORPUS)):
        f03c.construire(CORPUS)
    return table


def par_jour(con, filtre: str) -> pd.DataFrame:
    lignes, survie = [], 1.0
    for k in JOURS:
        atteint, supprimes = con.execute(f"""
            SELECT COUNT(*) FILTER (a0 <= {k} AND {k} <= a1),
                   COUNT(*) FILTER (a_evt = {k})
            FROM r WHERE {filtre}""").fetchone()
        taux = supprimes / atteint if atteint else 0.0
        survie *= 1 - taux
        lignes.append({"jour": k, "avis_ayant_atteint_ce_jour": atteint,
                       "supprimes_ce_jour": supprimes,
                       "pour_10000": round(1e4 * taux, 1),
                       "survie_pct": round(100 * survie, 2)})
    return pd.DataFrame(lignes)


def barres(ax, series: dict, colonne: str, etiquette) -> None:
    """Une seule série sur les figures : tous les avis (décision de Matthieu du
    2026-10-01). La version sans les 6 enseignes reste dans le CSV."""
    d = series["toutes_fiches"]
    ax.bar(d["jour"], d[colonne], width=0.66, color=COULEUR_FIGURE, label="tous les avis",
           zorder=3, edgecolor=FOND, linewidth=1)
    for x, v in zip(d["jour"], d[colonne]):
        ax.annotate(etiquette(v), (x, v), xytext=(0, 3), textcoords="offset points",
                    ha="center", fontsize=7, color=ENCRE)
    ax.set_xticks(list(JOURS))
    ax.tick_params(colors=ENCRE_2, labelsize=8, length=0)
    ax.grid(axis="y", color=GRILLE, lw=0.8, zorder=0)
    for cote in ["top", "right", "left"]:
        ax.spines[cote].set_visible(False)
    ax.spines["bottom"].set_color(GRILLE)
    ax.set_xlabel("jour d'existence de l'avis", color=ENCRE_2, fontsize=8)


def entete(fig, ax, titre: str, sous_titre: str) -> None:
    hauteur = fig.get_figheight()
    fig.text(0.01, 1 - 0.18 / hauteur, titre, va="top", fontsize=11, color=ENCRE)
    fig.text(0.01, 1 - 0.44 / hauteur, sous_titre, va="top", fontsize=8, color=ENCRE_2)
    poignees, textes = ax.get_legend_handles_labels()
    fig.legend(poignees, textes, loc="upper left", bbox_to_anchor=(0.005, 1 - 0.60 / hauteur),
               ncol=2, frameon=False, fontsize=8, labelcolor=ENCRE, handlelength=1.4)
    fig.tight_layout(rect=(0, 0, 1, 1 - 0.95 / hauteur))


def main() -> int:
    SORTIES.mkdir(exist_ok=True)
    table = features()
    con = duckdb.connect(config={"memory_limit": "4GB"})
    # a0 : premier jour d'existence où une disparition peut commencer ;
    # a1 : dernier jour où l'avis est à risque, jour de sa disparition compris ;
    # a_evt : jour d'existence de la disparition.
    con.execute(f"""
        CREATE TABLE r AS SELECT
          date_diff('day', created_at_day, premier_jour_vu + 1) AS a0,
          date_diff('day', created_at_day,
                    LEAST(COALESCE(date_suppression, DATE '2100-01-01'),
                          premier_jour_vu + CAST(fenetre_observation_j AS INTEGER))) AS a1,
          CASE WHEN supprime THEN date_diff('day', created_at_day, date_suppression) END
                                                        AS a_evt,
          chaine_antiparasitaire OR salle_espagnole     AS enseigne,
          fenetre_observation_j > 0                     AS exposable
        FROM read_parquet('{table.as_posix()}')
        WHERE created_at_day BETWEEN DATE '{PUBLICATION_DEBUT}' AND DATE '{PUBLICATION_FIN}'""")
    hors = con.execute("""SELECT COUNT(*) FROM r WHERE exposable
                          AND (a_evt < a0 OR a_evt > a1 OR a1 < a0)""").fetchone()[0]
    if hors:
        raise SystemExit(f"{hors} avis avec une disparition hors de leur période d'exposition.")

    series = {"toutes_fiches": par_jour(con, "exposable"),
              "sans_enseignes": par_jour(con, "exposable AND NOT enseigne")}
    pd.concat([d.assign(jeu=j) for j, d in series.items()]).to_csv(
        SORTIES / "survie_par_jour.csv", index=False)

    sous_titre = (f"Avis de {CORPUS.stem} publiés du 11 au 24 août 2026. "
                  "Suppression : absent deux jours de suite ou plus.")
    fig, ax = plt.subplots(figsize=(8.5, 4.4), dpi=150)
    fig.patch.set_facecolor(FOND)
    ax.set_facecolor(FOND)
    barres(ax, series, "survie_pct", lambda v: f"{v:.1f}".replace(".", ","))
    ax.set_ylim(90, 100.6)
    ax.set_yticks([90, 92.5, 95, 97.5, 100])
    ax.set_yticklabels(["90 %", "92,5 %", "95 %", "97,5 %", "100 %"])
    ax.set_ylabel("avis encore en ligne (l'axe commence à 90 %)", color=ENCRE_2, fontsize=8)
    entete(fig, ax, "Taux de survie des avis par jour d'existence", sous_titre)
    fig.savefig(SORTIES / "taux_survie.png", facecolor=FOND)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8.5, 4.4), dpi=150)
    fig.patch.set_facecolor(FOND)
    ax.set_facecolor(FOND)
    barres(ax, series, "pour_10000", lambda v: f"{v:.0f}")
    ax.set_ylim(0, None)
    ax.set_ylabel("suppressions pour 10 000 avis ayant atteint ce jour", color=ENCRE_2,
                  fontsize=8)
    entete(fig, ax, "Suppressions de chaque jour d'existence", sous_titre)
    fig.savefig(SORTIES / "suppressions_par_jour.png", facecolor=FOND)
    plt.close(fig)

    avis, supprimes, exposables = con.execute(
        "SELECT COUNT(*), COUNT(a_evt), COUNT(*) FILTER (exposable) FROM r").fetchone()
    resume = {"corpus": CORPUS.stem, "avis_publies": avis, "avis_exposables": exposables,
              "suppressions": supprimes,
              "suppressions_sans_enseignes": con.execute(
                  "SELECT COUNT(a_evt) FROM r WHERE NOT enseigne").fetchone()[0]}
    (SORTIES / "resume.json").write_text(json.dumps(resume, ensure_ascii=False, indent=2),
                                         encoding="utf-8")
    print(json.dumps(resume, ensure_ascii=False))
    for jeu, d in series.items():
        print(f"\n{NOM[jeu]}\n{d.to_string(index=False)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
