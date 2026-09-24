#!/usr/bin/env python3
"""Les trois figures de la note sur les réapparitions.

    python etudes-ponctuelles/2026-09-18-reapparitions/graphiques.py

Lit les CSV de `sorties/` et écrit les PNG dans `sorties/figures/`. Aucun
chiffre n'est calculé ici.

Couleurs : palette de référence de la compétence dataviz, slots 1 à 3, dont le
fichier de palette documente qu'ils passent tous les contrôles de lisibilité en
mode clair. Le validateur n'a pas pu être exécuté sur cette machine, Node
n'y étant pas installé ; aucune valeur n'a donc été réinventée.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

DOSSIER = Path(__file__).resolve().parent
SORTIES = DOSSIER / "sorties"
FIGURES = SORTIES / "figures"

SURFACE = "#fcfcfb"
ENCRE = "#0b0b0b"
ENCRE_DOUCE = "#52514e"
GRILLE = "#e4e3df"
BLEU = "#2a78d6"      # slot 1
ORANGE = "#eb6834"    # slot 2

SECTEURS_FR = {
    "home_services": "Services à domicile",
    "healthcare": "Santé",
    "automotive": "Automobile",
    "wellness_fitness": "Sport et bien-être",
    "travel": "Voyage",
    "food_beverage": "Restauration",
    "hospitality": "Hôtellerie",
}


def csv(nom):
    return pd.read_csv(SORTIES / nom)


def base(largeur, hauteur):
    fig, ax = plt.subplots(figsize=(largeur, hauteur), dpi=150)
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)
    for cote in ("top", "right", "left"):
        ax.spines[cote].set_visible(False)
    ax.spines["bottom"].set_color(GRILLE)
    ax.spines["bottom"].set_linewidth(1)
    ax.tick_params(colors=ENCRE_DOUCE, labelsize=8.5, length=0)
    return fig, ax


def titrer(ax, titre, sous_titre=None):
    """Titre au-dessus du sous-titre, tous deux calés à gauche de la zone tracée.

    `ax.set_title` et un texte posé en coordonnées d'axes se chevauchent dès que
    le sous-titre tient sur deux lignes. Les deux sont donc posés à la main, la
    hauteur du titre étant calculée d'après le nombre de lignes du sous-titre.
    """
    lignes = sous_titre.count("\n") + 1 if sous_titre else 0
    y_titre = 1.03 + 0.075 * lignes
    ax.text(0, y_titre, titre, transform=ax.transAxes, fontsize=11,
            color=ENCRE, va="bottom")
    if sous_titre:
        ax.text(0, 1.03, sous_titre, transform=ax.transAxes, fontsize=8.5,
                color=ENCRE_DOUCE, va="bottom", linespacing=1.4)


def enregistrer(fig, nom):
    FIGURES.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURES / nom, facecolor=SURFACE, bbox_inches="tight")
    plt.close(fig)
    print(f"  {nom}")


# ---------------------------------------------------------------------------
# Figure 1 — la durée d'absence
# ---------------------------------------------------------------------------
def figure1():
    d = csv("B1-duree-absence.csv")
    libelles = ["1 jour", "2 à 3 jours", "4 à 7 jours", "8 jours et plus"]
    valeurs = d["episodes"].tolist()

    fig, ax = base(6.3, 2.5)
    y = range(len(valeurs))
    ax.barh(list(y), valeurs, height=0.55, color=BLEU)
    ax.set_yticks(list(y), libelles, fontsize=9, color=ENCRE)
    ax.invert_yaxis()
    ax.xaxis.grid(True, color=GRILLE, linewidth=1, zorder=0)
    ax.set_axisbelow(True)
    ax.set_xlim(0, max(valeurs) * 1.15)
    for i, v in enumerate(valeurs):
        ax.text(v + max(valeurs) * 0.015, i, f"{v}", va="center", fontsize=9, color=ENCRE)
    titrer(ax, "Combien de temps l'avis est resté invisible",
           "617 épisodes de disparition suivie d'un retour. Les absences d'une seule "
           "journée sont comptées\ncomme un raté du robot par la règle du projet.")
    enregistrer(fig, "figure1-duree-absence.png")


# ---------------------------------------------------------------------------
# Figure 2 — les secteurs, tous retours confondus
#
# Deux figures pour la même population : l'une rapporte le compte à la taille
# du secteur, l'autre le laisse brut. Le classement change entre les deux, et
# c'est la raison de les donner toutes les deux.
# ---------------------------------------------------------------------------
def _barres_secteurs(colonne, titre, sous_titre, etiquette, nom, largeur_marge=1.22):
    d = csv("K1-secteurs-tous-retours.csv").sort_values(colonne)
    libelles = [SECTEURS_FR.get(s, s) for s in d["secteur"]]
    valeurs = d[colonne].tolist()

    fig, ax = base(6.3, 3.0)
    y = range(len(valeurs))
    ax.barh(list(y), valeurs, height=0.55, color=BLEU)
    ax.set_yticks(list(y), libelles, fontsize=9, color=ENCRE)
    ax.xaxis.grid(True, color=GRILLE, linewidth=1, zorder=0)
    ax.set_axisbelow(True)
    ax.set_xlim(0, max(valeurs) * largeur_marge)
    for i, (_, r) in enumerate(d.iterrows()):
        ax.text(r[colonne] + max(valeurs) * 0.02, i, etiquette(r),
                va="center", fontsize=8.5, color=ENCRE)
    titrer(ax, titre, sous_titre)
    enregistrer(fig, nom)


def figure2a():
    _barres_secteurs(
        "avis_revenus_par_million",
        "Sur un million d'avis du secteur, combien ont clignoté",
        "568 avis revenus au total, quelle que soit la durée de l'absence.\n"
        "Le compte d'avis figure à côté de chaque barre.",
        lambda r: "{:.0f}  ({} avis)".format(r["avis_revenus_par_million"],
                                             int(r["avis_revenus"])),
        "figure2a-secteurs-par-million.png")


def figure2b():
    _barres_secteurs(
        "avis_revenus",
        "Combien d'avis ont clignoté, sans rapporter à la taille du secteur",
        "Les mêmes 568 avis. Le classement diffère de la figure précédente :\n"
        "la restauration remonte par son volume, le voyage descend par le sien.",
        lambda r: "{} avis, {} fiches".format(int(r["avis_revenus"]),
                                              int(r["fiches_touchees"])),
        "figure2b-secteurs-en-volume.png",
        largeur_marge=1.32)


# ---------------------------------------------------------------------------
# Figure 3 — le calendrier
# ---------------------------------------------------------------------------
def figure3():
    d = csv("H1-calendrier.csv").dropna(subset=["disparu_le"]).copy()
    d["jour"] = pd.to_datetime(d["disparu_le"]).dt.strftime("%d/%m")
    d["ep_2j"] = d["ep_2_jours_et_plus"].astype(int)
    d["ep_1j"] = d["episodes"] - d["ep_2j"]

    fig, ax = base(6.3, 2.9)
    x = range(len(d))
    hauteur_max = d["episodes"].max()
    ecart = hauteur_max * 0.006          # le blanc de 2 px entre les deux segments
    ax.bar(list(x), d["ep_1j"], width=0.6, color=BLEU, label="Absence d'un jour")
    ax.bar(list(x), d["ep_2j"], width=0.6, bottom=d["ep_1j"] + ecart, color=ORANGE,
           label="Absence de 2 jours ou plus")
    ax.set_xticks(list(x), d["jour"], fontsize=8.5, color=ENCRE_DOUCE)
    ax.yaxis.grid(True, color=GRILLE, linewidth=1, zorder=0)
    ax.set_axisbelow(True)
    ax.set_ylim(0, hauteur_max * 1.12)
    ax.text(0, d.iloc[0]["episodes"] + hauteur_max * 0.03, f"{int(d.iloc[0]['episodes'])}",
            ha="center", fontsize=9, color=ENCRE)
    leg = ax.legend(frameon=False, fontsize=8.5, loc="upper right",
                    labelcolor=ENCRE_DOUCE, handlelength=1.2)
    for t in leg.get_texts():
        t.set_color(ENCRE_DOUCE)
    titrer(ax, "Le jour où le robot a cessé de voir l'avis",
           "Le 12 août porte 240 des 617 épisodes, dont 185 reviennent dès le lendemain.")
    enregistrer(fig, "figure3-calendrier.png")


if __name__ == "__main__":
    figure1()
    figure2a()
    figure2b()
    figure3()
    print(f"\nFigures dans {FIGURES}")
