#!/usr/bin/env python3
"""Les deux figures de la note sur l'antiparasitaire dans les home services US.

    python etudes-ponctuelles/2026-09-18-antiparasitaire-home-services/graphiques.py

Lit les CSV de `sorties/` et écrit les PNG dans `sorties/figures/`. Aucun
chiffre n'est calculé ici.

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
SORTIES = DOSSIER / "sorties"
FIGURES = SORTIES / "figures"

SURFACE = "#fcfcfb"
ENCRE = "#0b0b0b"
ENCRE_DOUCE = "#52514e"
GRILLE = "#e4e3df"
BLEU = "#2a78d6"      # slot 1
ORANGE = "#eb6834"    # slot 2

GROUPES_FR = {
    "a. les 4 chaines signalees": "Les 4 chaînes signalées",
    "b. variante de nom de ces 4 chaines": "Variantes de nom de ces 4 chaînes",
    "c. autre enseigne antiparasitaire": "Autres enseignes antiparasitaires",
    "d. autres services a domicile": "Autres services à domicile",
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
    lignes = sous_titre.count("\n") + 1 if sous_titre else 0
    ax.text(0, 1.03 + 0.075 * lignes, titre, transform=ax.transAxes,
            fontsize=11, color=ENCRE, va="bottom")
    if sous_titre:
        ax.text(0, 1.03, sous_titre, transform=ax.transAxes, fontsize=8.5,
                color=ENCRE_DOUCE, va="bottom", linespacing=1.4)


def enregistrer(fig, nom):
    FIGURES.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURES / nom, facecolor=SURFACE, bbox_inches="tight")
    plt.close(fig)
    print(f"  {nom}")


def figure5():
    """L'escalier : un tiers des fiches, deux tiers des avis, quatre cinquièmes
    des suppressions."""
    d = csv("C1-small-large.csv").set_index("activite")
    p = d.loc["antiparasitaire"]

    libelles = ["Suppressions", "Avis", "Fiches"]
    parts = [p["part_suppr_pct"], p["part_avis_pct"], p["part_fiches_pct"]]
    effectifs = [
        "{:,.0f} sur {:,.0f}".format(d.loc["antiparasitaire", "suppressions"],
                                     d["suppressions"].sum()).replace(",", " "),
        "{:,.0f} sur {:,.0f}".format(d.loc["antiparasitaire", "avis"],
                                     d["avis"].sum()).replace(",", " "),
        "{:,.0f} sur {:,.0f}".format(d.loc["antiparasitaire", "fiches"],
                                     d["fiches"].sum()).replace(",", " "),
    ]

    fig, ax = base(6.3, 2.7)
    y = range(len(parts))
    ecart = 0.6                      # le blanc de 2 px entre les deux segments
    ax.barh(list(y), parts, height=0.55, color=BLEU, label="Antiparasitaire")
    ax.barh(list(y), [100 - v - ecart for v in parts], height=0.55,
            left=[v + ecart for v in parts], color=ORANGE,
            label="Autres services à domicile")
    ax.set_yticks(list(y), libelles, fontsize=9.5, color=ENCRE)
    ax.set_xlim(0, 100)
    ax.set_xticks(range(0, 101, 25), [f"{v} %" for v in range(0, 101, 25)])
    ax.xaxis.grid(True, color=GRILLE, linewidth=1, zorder=0)
    ax.set_axisbelow(True)

    for i, (v, n) in enumerate(zip(parts, effectifs)):
        ax.text(v / 2, i, "{:.0f} %".format(v).replace(".", ","), ha="center",
                va="center", fontsize=9.5, color="white", fontweight="bold")
        ax.text(101, i, n, va="center", fontsize=8, color=ENCRE_DOUCE)

    leg = ax.legend(frameon=False, fontsize=8.5, ncol=2, handlelength=1.2,
                    loc="upper left", bbox_to_anchor=(0, -0.14))
    for t in leg.get_texts():
        t.set_color(ENCRE_DOUCE)

    titrer(ax, "La place de l'antiparasitaire dans les home services américains",
           "Fiches de taille « small » et « large » réunies. La part de l'antiparasitaire "
           "monte des fiches\naux avis, puis des avis aux suppressions.")
    enregistrer(fig, "figure5-part-antiparasitaire.png")


def figure6():
    """Le taux de suppression par groupe : le phénomène suit l'activité."""
    d = csv("D1-quatre-groupes.csv").sort_values("taux_pct")
    libelles = [GROUPES_FR.get(g, g) for g in d["groupe"]]
    valeurs = d["taux_pct"].tolist()

    fig, ax = base(6.3, 2.7)
    y = range(len(valeurs))
    ax.barh(list(y), valeurs, height=0.55, color=BLEU)
    ax.set_yticks(list(y), libelles, fontsize=9, color=ENCRE)
    ax.xaxis.grid(True, color=GRILLE, linewidth=1, zorder=0)
    ax.set_axisbelow(True)
    ax.set_xlim(0, max(valeurs) * 1.30)
    # Les deux remplacements se font séparément : un `.replace(",", " ")` sur la
    # chaîne entière effacerait la virgule décimale posée juste avant.
    for i, (_, r) in enumerate(d.iterrows()):
        taux = "{:.2f}".format(r["taux_pct"]).replace(".", ",")
        avis = "{:,.0f}".format(r["avis"]).replace(",", " ")
        ax.text(r["taux_pct"] + max(valeurs) * 0.02, i, f"{taux} %  ({avis} avis)",
                va="center", fontsize=8.5, color=ENCRE)
    graduations = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6]
    ax.set_xticks(graduations,
                  ["{:.1f} %".format(v).replace(".", ",") for v in graduations])
    titrer(ax, "Part des avis supprimés, par groupe d'enseignes",
           "Les autres enseignes antiparasitaires sont au-dessus des quatre chaînes "
           "signalées.\nLe phénomène suit l'activité.")
    enregistrer(fig, "figure6-taux-par-groupe.png")


if __name__ == "__main__":
    figure5()
    figure6()
    print(f"\nFigures dans {FIGURES}")
