#!/usr/bin/env python3
"""Les deux figures de la note sur la régression du panel 03B.

    python etudes-ponctuelles/2026-09-21-regression-03B/graphiques.py

Lit les CSV de `sorties/`, écrits par `resultats.py`, et dépose les PNG dans
`sorties/figures/`. Aucun chiffre n'est calculé ici.

Couleurs : palette de référence de la compétence dataviz, slots 1 et 2, comme
les figures des notes précédentes. Le validateur n'a pas pu être exécuté, Node
n'étant pas installé sur cette machine ; aucune valeur n'a été réinventée.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

DOSSIER = Path(__file__).resolve().parent
SORTIES = DOSSIER / "sorties"
FIGURES = SORTIES / "figures"

SURFACE = "#fcfcfb"
ENCRE = "#0b0b0b"
ENCRE_DOUCE = "#52514e"
GRILLE = "#e4e3df"
BLEU = "#2a78d6"      # slot 1 — l'écart est tranché
ORANGE = "#eb6834"    # slot 2 — repère, ou courbe de comparaison
GRIS = "#9b9a96"      # l'écart n'est pas tranché

# Au-delà, les barres sont trop longues pour que le reste de la figure se lise.
PLAFOND_RISQUE = 30


def habiller(ax):
    for cote in ("top", "right"):
        ax.spines[cote].set_visible(False)
    for cote in ("left", "bottom"):
        ax.spines[cote].set_color(GRILLE)
        ax.spines[cote].set_linewidth(1)
    ax.tick_params(colors=ENCRE_DOUCE, labelsize=8.5, length=0)
    ax.set_axisbelow(True)


def titrer(fig, titre, sous_titre, haut=0.985, gauche=0.012):
    """Titre et sous-titre calés sur le bord gauche de l'image.

    Posés en coordonnées de figure et non d'axes : sur la figure 1, les
    libellés occupent la moitié gauche, et un titre calé sur les axes
    partirait du milieu de l'image.

    `set_title` ne convient pas non plus : il empile les deux textes et le
    sous-titre passe sous le titre.
    """
    fig.text(gauche, haut, titre, fontsize=11, color=ENCRE, va="top")
    fig.text(gauche, haut - 0.052, sous_titre, fontsize=8.5, color=ENCRE_DOUCE,
             va="top", linespacing=1.5)


def virgule(x, decimales=1):
    return ("{:." + str(decimales) + "f}").format(x).replace(".", ",")


def pourcent(part):
    """Une part de 0 à 1, en pourcentage, avec l'espace insécable du français.

    `{:.0%}` écrit « 20% », collé, qui n'est pas la typographie française.
    """
    return "{:.0f} %".format(part * 100)


# ---------------------------------------------------------------------------
# Figure 1 — les risques relatifs ajustés, avec leurs fourchettes
# ---------------------------------------------------------------------------

def figure1():
    d = pd.read_csv(SORTIES / "B1-risques-relatifs.csv")
    d = d.sort_values("risque_relatif")          # le plus fort en haut
    y = np.arange(len(d))

    fig, ax = plt.subplots(figsize=(7.6, 6.6), dpi=150)
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)
    # Marges posées à la main : les libellés sont longs, et `tight_layout`
    # leur donnait les deux tiers de la largeur.
    fig.subplots_adjust(left=0.385, right=0.985, top=0.80, bottom=0.085)
    habiller(ax)
    ax.grid(True, axis="x", color=GRILLE, linewidth=1, zorder=0)

    # Le 1 : ni plus ni moins de risque que la référence.
    ax.axvline(1, color=ENCRE_DOUCE, linewidth=1, linestyle="--", zorder=2)

    for i, (_, r) in enumerate(d.iterrows()):
        couleur = BLEU if r["tranche"] else GRIS
        haute = min(r["borne_haute"], PLAFOND_RISQUE)
        ax.plot([r["borne_basse"], haute], [i, i], color=couleur,
                linewidth=2, solid_capstyle="round", zorder=3)
        ax.plot([r["risque_relatif"]], [i], marker="o", markersize=6.5,
                color=couleur, markeredgecolor=SURFACE, markeredgewidth=1.5,
                zorder=4)
        # La fourchette du premier dépasse le cadre : une flèche le dit.
        if r["borne_haute"] > PLAFOND_RISQUE:
            ax.annotate("", xy=(PLAFOND_RISQUE, i), xytext=(PLAFOND_RISQUE * 0.8, i),
                        arrowprops=dict(arrowstyle="->", color=couleur, linewidth=2))

    ax.set_yticks(y, d["libelle"], fontsize=8.5)
    for etiquette, tranche in zip(ax.get_yticklabels(), d["tranche"]):
        etiquette.set_color(ENCRE if tranche else ENCRE_DOUCE)

    ax.set_xscale("log")
    ax.set_xlim(0.25, PLAFOND_RISQUE)
    ax.set_xticks([0.5, 1, 2, 5, 10, 20],
                  ["÷2", "1", "×2", "×5", "×10", "×20"])
    ax.set_xlabel("Risque de suppression, par rapport à la situation de référence",
                  fontsize=8.5, color=ENCRE_DOUCE, labelpad=8)

    titrer(fig, "Ce que le modèle retient, une fois tout le reste tenu constant",
           "35 751 avis, 1 355 suppressions. En bleu, les écarts tranchés : leur "
           "fourchette ne contient pas 1 ; en gris,\nceux que les données ne "
           "tranchent pas. Référence : avis 5 étoiles sans texte, auteur Local "
           "Guide de niveau 1 à 3,\nfiche mono, Europe.")

    FIGURES.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURES / "figure7-risques-relatifs-03B.png",
                dpi=150, facecolor=SURFACE)
    plt.close(fig)
    print("  figure7-risques-relatifs-03B.png")


# ---------------------------------------------------------------------------
# Figure 2 — la courbe de ciblage
# ---------------------------------------------------------------------------

def figure2():
    d = pd.read_csv(SORTIES / "E1-ciblage.csv")
    a = pd.read_csv(SORTIES / "A1-passages.csv").set_index("suffixe")
    auc = float(a.loc["tous", "auc"])

    fig, ax = plt.subplots(figsize=(6.6, 4.4), dpi=150)
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)
    fig.subplots_adjust(left=0.10, right=0.955, top=0.775, bottom=0.135)
    habiller(ax)
    ax.grid(True, color=GRILLE, linewidth=1, zorder=0)

    ax.plot([0, 1], [0, 1], color=ORANGE, linewidth=2, linestyle="--",
            label="Si on tirait les avis au hasard", zorder=3)
    ax.plot(d["part_avis"], d["part_suppressions"], color=BLEU, linewidth=2,
            label="Avis rangés par le modèle, du plus risqué au moins risqué",
            zorder=4)

    # Les repères, lus dans le CSV que le 07B écrit à part avec leurs valeurs
    # exactes. Les relire sur la courbe ci-dessus, enregistrée en 200 points,
    # donnait 31 % à 10 % là où le passage annonce 32 %.
    reperes = pd.read_csv(SORTIES / "E2-reperes-ciblage.csv")
    for _, r in reperes[reperes["part_avis"] <= 0.2].iterrows():
        part, trouve = float(r["part_avis"]), float(r["part_suppressions"])
        ax.plot([part], [trouve], marker="o", markersize=7, color=BLEU,
                markeredgecolor=SURFACE, markeredgewidth=2, zorder=5)
        ax.annotate("{} des avis, {} des suppressions".format(
                        pourcent(part), pourcent(trouve)),
                    xy=(part, trouve), xytext=(part + 0.05, trouve - 0.09),
                    fontsize=8.5, color=ENCRE,
                    arrowprops=dict(arrowstyle="-", color=ENCRE_DOUCE, linewidth=1))

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.02)
    graduations = [0, 0.25, 0.5, 0.75, 1.0]
    ax.set_xticks(graduations, [pourcent(v) for v in graduations])
    ax.set_yticks(graduations, [pourcent(v) for v in graduations])
    ax.set_xlabel("Part des avis examinés", fontsize=8.5, color=ENCRE_DOUCE,
                  labelpad=8)

    leg = ax.legend(frameon=False, fontsize=8.5, loc="lower right", handlelength=1.6)
    for t in leg.get_texts():
        t.set_color(ENCRE_DOUCE)

    titrer(fig, "Part des suppressions retrouvée en examinant les avis les plus risqués",
           "35 751 avis, 1 355 suppressions. Cinq tours par établissement : chaque "
           "avis est noté par un modèle\nqui n'a jamais vu sa fiche. Capacité à "
           "classer : {}.".format(virgule(auc, 3)),
           haut=0.975)

    FIGURES.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURES / "figure8-ciblage-03B.png",
                dpi=150, facecolor=SURFACE)
    plt.close(fig)
    print("  figure8-ciblage-03B.png")


if __name__ == "__main__":
    print(f"\nFigures dans {FIGURES}")
    figure1()
    figure2()
