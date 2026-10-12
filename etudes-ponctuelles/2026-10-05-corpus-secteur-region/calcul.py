#!/usr/bin/env python3
"""Le corpus en une matrice : avis par secteur et région, fiches suivies dessous.

    PYTHONPATH=".venv/Lib/site-packages;outils" <python uv> etudes-ponctuelles/2026-10-05-corpus-secteur-region/calcul.py

Demande de Matthieu du 2026-10-05, pour la partie 1 de la consolidation (le
tableau des avis par secteur et région devient une matrice colorée).

  avis      data/bigquery/reviews_doublons_cleaned_all.parquet, toutes notes,
            une ligne par avis ; le total doit retomber sur 4 876 933.
  fiches    data/bigquery/businesses.parquet : les 9 048 fiches du panel, y
            compris les 51 sans aucun avis.
  région    États-Unis, ou Europe pour tout autre pays.

Même construction que la matrice de `2026-10-02-pertes-secteur-taille` : fond
de case du presque blanc au bleu moyen selon le nombre d'avis, totaux en gris.

Sorties : livrables/restitution_finale/graphiques/corpus_secteur_region.png et
livrables/restitution_finale/donnees/corpus_secteur_region.csv.
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "outils"))
from local import connexion  # noqa: E402

FINALE = RACINE / "livrables" / "restitution_finale"
DONNEES = FINALE / "donnees" / "corpus_secteur_region.csv"
MATRICE = FINALE / "graphiques" / "corpus_secteur_region.png"
ENCRE, ENCRE_2, GRILLE, FOND, GRIS_TOTAL = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb", "#ecebe7"
AVIS_ATTENDUS = 4_876_933

SECTEURS = {"automotive": "Automobile", "food_beverage": "Restauration",
            "healthcare": "Santé", "home_services": "Services à domicile",
            "hospitality": "Hôtellerie", "travel": "Voyage",
            "wellness_fitness": "Sport et bien-être"}
REGIONS = {"US": "États-Unis", "Europe": "Europe"}

SQL = """
WITH fiches AS (
  SELECT cid, industry, IF(country = 'US', 'US', 'Europe') AS region FROM businesses
),
avis AS (
  SELECT f.industry, f.region, count(*) AS avis
  FROM reviews_doublons_cleaned_all r JOIN fiches f USING (cid)
  GROUP BY CUBE (f.industry, f.region)
),
nb_fiches AS (
  SELECT industry, region, count(*) AS fiches FROM fiches GROUP BY CUBE (industry, region)
)
-- Les lignes de total du CUBE portent des NULL : jointure NULL-sûre.
SELECT n.industry, n.region, coalesce(a.avis, 0) AS avis, n.fiches
FROM nb_fiches n LEFT JOIN avis a
  ON a.industry IS NOT DISTINCT FROM n.industry AND a.region IS NOT DISTINCT FROM n.region
"""


def nombre(n: int) -> str:
    return f"{n:,}".replace(",", " ")


def teinte(v: float, v_max: float) -> tuple:
    """Du presque blanc au bleu moyen de la rampe dataviz (pas 350), assez clair
    pour garder le texte en encre, comme la matrice secteur × taille."""
    a = np.array(matplotlib.colors.to_rgb("#f2f7fd"))
    b = np.array(matplotlib.colors.to_rgb("#5598e7"))
    return tuple(a + (b - a) * min(v / v_max, 1))


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    con = connexion("4GB")
    total_table = con.execute("SELECT count(*) FROM reviews_doublons_cleaned_all").fetchone()[0]
    cases = {(i, r): (a, f) for i, r, a, f in con.execute(SQL).fetchall()}
    if total_table != AVIS_ATTENDUS or cases[(None, None)][0] != AVIS_ATTENDUS:
        raise SystemExit(f"Total inattendu : table {total_table}, matrice {cases[(None, None)][0]}, "
                         f"attendu {AVIS_ATTENDUS}.")
    inconnus = {k[0] for k in cases if k[0] is not None and k[0] not in SECTEURS}
    if inconnus:
        raise SystemExit(f"secteurs inattendus : {inconnus}")

    lignes = list(SECTEURS) + [None]
    colonnes = list(REGIONS) + [None]
    DONNEES.parent.mkdir(parents=True, exist_ok=True)
    with DONNEES.open("w", encoding="utf-8") as fh:
        fh.write("secteur,region,avis,fiches\n")
        for i in lignes:
            for r in colonnes:
                a, f = cases[(i, r)]
                fh.write(f"{SECTEURS.get(i, 'Total')},{REGIONS.get(r, 'Total')},{a},{f}\n")
                print(f"{SECTEURS.get(i, 'Total'):20s} {REGIONS.get(r, 'Total'):11s} "
                      f"{nombre(a):>10} avis  {f:>5} fiches")
    matrice(cases, lignes, colonnes)
    print(f"\nécrit : {DONNEES}\nécrit : {MATRICE}")
    return 0


def matrice(cases: dict, lignes: list, colonnes: list) -> None:
    v_max = max(a for (i, r), (a, f) in cases.items() if i is not None and r is not None)
    larg_sect, larg_case, haut_ent, haut = 2.1, 1.75, 0.45, 0.56
    largeur = larg_sect + larg_case * len(colonnes)
    hauteur = haut_ent + haut * len(lignes)
    fig = plt.figure(figsize=(largeur + 0.3, hauteur + 0.75), dpi=150)
    fig.patch.set_facecolor(FOND)
    ax = fig.add_axes((0.15 / (largeur + 0.3), 0.1 / (hauteur + 0.75),
                       largeur / (largeur + 0.3), hauteur / (hauteur + 0.75)))
    ax.set_xlim(0, largeur)
    ax.set_ylim(hauteur, 0)
    ax.axis("off")

    for k, r in enumerate(colonnes):
        ax.text(larg_sect + larg_case * (k + 0.5), haut_ent * 0.5, REGIONS.get(r, "Total"),
                ha="center", va="center", fontsize=9, color=ENCRE, fontweight="bold")
    for n_ligne, i in enumerate(lignes):
        y = haut_ent + haut * n_ligne
        ligne_total = i is None
        ax.text(0.08, y + haut / 2, SECTEURS.get(i, "Total"), ha="left", va="center",
                fontsize=8.5, color=ENCRE, fontweight="bold" if ligne_total else "normal")
        for k, r in enumerate(colonnes):
            x = larg_sect + larg_case * k
            a, f = cases[(i, r)]
            total = ligne_total or r is None
            fond = GRIS_TOTAL if total else teinte(a, v_max)
            ax.add_patch(Rectangle((x + 0.03, y + 0.03), larg_case - 0.06, haut - 0.06,
                                   facecolor=fond, edgecolor="none"))
            ax.text(x + larg_case / 2, y + haut * 0.38, nombre(a), ha="center", va="center",
                    fontsize=9.5, color=ENCRE, fontweight="bold" if total else "normal")
            ax.text(x + larg_case / 2, y + haut * 0.72, f"{nombre(f)} fiches", ha="center",
                    va="center", fontsize=7, color=ENCRE_2)
        ax.plot([0, largeur], [y, y], color=GRILLE, lw=0.6)

    part = lambda secteurs: 100 * sum(cases[(s, None)][0] for s in secteurs) / AVIS_ATTENDUS
    titre = (f"La restauration et l'hôtellerie apportent {part(['food_beverage', 'hospitality']):.0f} % "
             f"des avis du corpus, le voyage {part(['travel']):.0f} %").replace(".", ",")
    fig.text(0.15 / (largeur + 0.3), 1 - 0.1 / (hauteur + 0.75), titre, va="top",
             fontsize=10.5, color=ENCRE)
    fig.text(0.15 / (largeur + 0.3), 1 - 0.42 / (hauteur + 0.75),
             "Avis du corpus nettoyé, toutes notes ; fiches suivies sous chaque nombre. "
             "Voyage : entreprises à un seul établissement uniquement.",
             va="top", fontsize=7.5, color=ENCRE_2)
    MATRICE.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(MATRICE, facecolor=FOND)
    plt.close(fig)


if __name__ == "__main__":
    raise SystemExit(main())
