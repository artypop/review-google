#!/usr/bin/env python3
"""La figure de concentration des suppressions.

    python etudes-ponctuelles/2026-09-18-concentration-suppressions/graphiques.py

Lit `sorties/B3-courbe.csv` et écrit le PNG dans `matthieu/figures/`.
Aucun chiffre n'est calculé ici.

Couleurs : palette de référence de la compétence dataviz, slots 1 et 2. Le
validateur n'a pas pu être exécuté, Node n'étant pas installé sur cette
machine ; aucune valeur n'a été réinventée.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

DOSSIER = Path(__file__).resolve().parent
RACINE = DOSSIER.parent.parent
SORTIES = DOSSIER / "sorties"
FIGURES = RACINE / "matthieu" / "figures"

SURFACE = "#fcfcfb"
ENCRE = "#0b0b0b"
ENCRE_DOUCE = "#52514e"
GRILLE = "#e4e3df"
BLEU = "#2a78d6"      # slot 1 — observé
ORANGE = "#eb6834"    # slot 2 — attendu

BORNE = 500           # au-delà, les deux courbes sont plates et n'apprennent rien


def figure():
    d = pd.read_csv(SORTIES / "B3-courbe.csv")
    d = d[d["rang"] <= BORNE]
    seuils = pd.read_csv(SORTIES / "B2-seuils.csv").set_index("mesure")["valeur"]
    moitie = int(seuils["fiches portant la moitié des suppressions"])

    fig, ax = plt.subplots(figsize=(6.3, 3.4), dpi=150)
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)
    for cote in ("top", "right"):
        ax.spines[cote].set_visible(False)
    for cote in ("left", "bottom"):
        ax.spines[cote].set_color(GRILLE)
        ax.spines[cote].set_linewidth(1)
    ax.tick_params(colors=ENCRE_DOUCE, labelsize=8.5, length=0)
    ax.grid(True, color=GRILLE, linewidth=1, zorder=0)
    ax.set_axisbelow(True)

    ax.plot(d["rang"], d["part_observee"], color=BLEU, linewidth=2,
            label="Observé", zorder=3)
    ax.plot(d["rang"], d["part_attendue"], color=ORANGE, linewidth=2,
            label="Si les suppressions suivaient la taille des fiches", zorder=3)

    # Le point de lecture : les fiches qui portent la moitié des suppressions.
    ax.plot([moitie], [50], marker="o", markersize=8, color=BLEU,
            markeredgecolor=SURFACE, markeredgewidth=2, zorder=4)
    ax.annotate("{} fiches portent\nla moitié des suppressions".format(moitie),
                xy=(moitie, 50), xytext=(moitie + 45, 33),
                fontsize=8.5, color=ENCRE,
                arrowprops=dict(arrowstyle="-", color=ENCRE_DOUCE, linewidth=1))

    ax.set_xlim(0, BORNE)
    ax.set_ylim(0, 100)
    ax.set_yticks(range(0, 101, 25), [f"{v} %" for v in range(0, 101, 25)])
    ax.set_xlabel("Nombre de fiches, rangées de la plus touchée à la moins touchée",
                  fontsize=8.5, color=ENCRE_DOUCE, labelpad=8)

    leg = ax.legend(frameon=False, fontsize=8.5, loc="lower right", handlelength=1.6)
    for t in leg.get_texts():
        t.set_color(ENCRE_DOUCE)

    # 1,03 pour le sous-titre, plus 0,075 par ligne : en deçà, le titre le recouvre.
    ax.text(0, 1.18, "Part des 4 747 suppressions portée par les fiches les plus touchées",
            transform=ax.transAxes, fontsize=11, color=ENCRE, va="bottom")
    ax.text(0, 1.03,
            "Sur les 8 997 fiches qui portent au moins un avis. Les 500 premières suffisent :\n"
            "au-delà, les deux courbes sont plates.",
            transform=ax.transAxes, fontsize=8.5, color=ENCRE_DOUCE, va="bottom",
            linespacing=1.4)

    FIGURES.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURES / "figure4-concentration-suppressions.png",
                facecolor=SURFACE, bbox_inches="tight")
    plt.close(fig)
    print("  figure4-concentration-suppressions.png")


if __name__ == "__main__":
    figure()
    print(f"\nFigure dans {FIGURES}")
