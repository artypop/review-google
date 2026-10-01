"""5b. Graphiques de la réponse du propriétaire selon son délai, à partir du point 5.

    uv run python consolidation/5b_graphique_delai.py

Aucune requête : lit `sorties/5_effets.csv`, produit par `5_reponse_jour_par_jour.py`.
Deux passages du point 5 : mono + small (« tous » et « sans enseignes » y sont
identiques, les 95 fiches signalées étant toutes large) et large sans enseignes.

L'axe se lit en écart de taux : 0 % = même taux de suppression avec ou sans
réponse ; −64 % = l'avis répondu disparaît 64 % de moins que l'avis du même âge
encore sans réponse. Un effet non citable (règle de `commun.py` : 10
suppressions, 5 fiches, aucune fiche au-delà du quart) est hachuré, sans valeur.

Produit :
  sorties/figures/5b_delai_reponse.png   fiches qui répondent à plus de 75 %, par délai
  sorties/figures/5b_habitude.png        la même chose face aux fiches qui répondent moins
"""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Patch
from matplotlib.ticker import FuncFormatter

from commun import ENCRE, ENCRE_SECONDAIRE, FIGURES, SORTIES, figure

PASSAGES = {"mono + small, tous": "Mono + small", "large, sans_enseignes": "Large, sans enseignes"}
DELAIS = {"jour même": "Réponse\nle jour même", "1 jour": "Réponse\nle lendemain",
          "2 jours": "Réponse\nà 2 jours"}
HABITUDES = {"plus de 75 %": "fiche qui répond à plus de 75 %",
             "75 % ou moins": "fiche qui répond à 75 % ou moins"}
BLEU, VERT, GRIS = "#2a78d6", "#1baf7a", "#8a8984"
SOUS_TITRE = ("Panel 03B : avis publiés du 4 au 17 août 2026, suivis jour par jour jusqu'au 24 août. "
              "Chaque avis répondu est comparé à un avis du même âge encore sans réponse,\n"
              "à note et région égales. La réponse compte à partir du lendemain de sa date. "
              "Trait : fourchette à 95 %. Hachuré : trop peu de suppressions pour citer un chiffre.")

e = pd.read_csv(SORTIES / "5_effets.csv", sep=";", decimal=",")
e["citable"] = e["citable"] == "oui"


def effet(passage, delai, habitude):
    ligne = e[(e["passage"] == passage) & (e["colonne"] == f"réponse {delai}, {HABITUDES[habitude]}")]
    return ligne.iloc[0]


def en_pourcentage(rapport):
    ecart = round(100 * (rapport - 1))
    return "0 %" if ecart == 0 else f"{ecart:+d} %".replace("-", "−")


def barre(ax, x, r, couleur, largeur):
    """Une barre partant de 1 (pas d'effet), avec sa fourchette si l'effet est citable."""
    n = f"{int(r['suppressions'])} suppr., {int(r['fiches_touchees'])} fiches" \
        if pd.notna(r["fiches_touchees"]) else f"{int(r['suppressions'])} suppr."
    if pd.isna(r["risque_relatif"]):
        ax.text(x, 1.04, f"trop peu de\nsuppressions\n({n})", ha="center", va="bottom",
                fontsize=7.5, color=GRIS, style="italic")
        return
    rr = r["risque_relatif"]
    if not r["citable"]:
        ax.bar(x, rr - 1, bottom=1, width=largeur, facecolor="none", edgecolor=GRIS,
               hatch="///", linewidth=0.8, zorder=2)
        y, va = (rr - 0.03, "top") if rr < 1 else (rr + 0.03, "bottom")
        ax.text(x, y, f"non citable\n({n})", ha="center", va=va, fontsize=7.5, color=GRIS,
                style="italic")
        return
    bas, haut = r["fourchette_basse"], r["fourchette_haute"]
    ax.bar(x, rr - 1, bottom=1, width=largeur, color=couleur, zorder=2)
    ax.errorbar(x, rr, yerr=[[rr - bas], [haut - rr]], fmt="none", ecolor=ENCRE, elinewidth=1.2,
                capsize=4, zorder=3)
    ax.text(x, bas - 0.03, en_pourcentage(rr), ha="center", va="top", fontsize=10,
            fontweight="bold", color=ENCRE)
    ax.text(x, bas - 0.11, f"({n})", ha="center", va="top", fontsize=7.5, color=GRIS)


def enregistrer(fig, nom):
    """Comme `commun.enregistrer`, sans refaire la mise en page : le sous-titre
    garde sa place entre le titre et les graphiques."""
    FIGURES.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURES / f"{nom}.png", dpi=130)
    plt.close(fig)
    print(f"  sorties/figures/{nom}.png")


def axe(ax, haut):
    ax.axhline(1, color=ENCRE, linestyle="--", linewidth=1.2, zorder=1)
    ax.set_xticks(range(len(DELAIS)), list(DELAIS.values()))
    ax.set_yticks(np.arange(0, haut - 0.05, 0.2))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: en_pourcentage(v)))
    ax.set_ylim(-0.25, haut)
    ax.set_xlim(-0.6, len(DELAIS) - 0.4)
    ax.grid(axis="x", visible=False)


# ---------------------------------------------------------------------------
# 1. Fiches qui répondent à plus de 75 % : l'effet selon le délai de réponse.
# ---------------------------------------------------------------------------
fig, axes = figure(1, 1, largeur=10, hauteur=6)
ax = axes[0][0]
for i, (passage, nom) in enumerate(PASSAGES.items()):
    for j, delai in enumerate(DELAIS):
        barre(ax, j + (i - 0.5) * 0.38, effet(passage, delai, "plus de 75 %"), [BLEU, VERT][i], 0.34)
axe(ax, 1.3)
ax.text(len(DELAIS) - 0.45, 1.02, "pas d'effet", ha="right", va="bottom", fontsize=9, color=ENCRE)
ax.set_ylabel("Écart du taux de suppression")
ax.legend(handles=[Patch(color=BLEU, label="Mono + small"), Patch(color=VERT, label="Large, sans enseignes")],
          loc="upper left", ncol=2, fontsize=9)
fig.suptitle("Fiches qui répondent à plus de 75 % de leurs avis : l'avis répondu disparaît beaucoup moins,\n"
             "que la réponse arrive le jour même, le lendemain ou à 2 jours",
             x=0.02, ha="left", fontsize=12, color=ENCRE)
fig.text(0.02, 0.86, SOUS_TITRE, ha="left", va="top", fontsize=7.5, color=ENCRE_SECONDAIRE)
fig.tight_layout(rect=(0, 0, 1, 0.83))
enregistrer(fig, "5b_delai_reponse")

# ---------------------------------------------------------------------------
# 2. La même mesure selon l'habitude de la fiche, un panneau par taille.
# ---------------------------------------------------------------------------
fig, axes = figure(1, 2, largeur=13, hauteur=6)
for ax, (passage, nom) in zip(axes[0], PASSAGES.items()):
    for i, habitude in enumerate(HABITUDES):
        for j, delai in enumerate(DELAIS):
            barre(ax, j + (i - 0.5) * 0.38, effet(passage, delai, habitude), [BLEU, GRIS][i], 0.34)
    axe(ax, 2.6)
    ax.set_title(nom, loc="left", fontsize=11, color=ENCRE)
axes[0][0].set_ylabel("Écart du taux de suppression")
axes[0][1].legend(handles=[Patch(color=BLEU, label="fiche qui répond à plus de 75 %"),
                           Patch(facecolor="none", edgecolor=GRIS, hatch="///",
                                 label="fiche qui répond à 75 % ou moins")],
                  loc="upper right", fontsize=9)
fig.suptitle("La réponse protège sur les fiches qui ont l'habitude de répondre. Sur les autres, "
             "trop peu de suppressions pour conclure",
             x=0.02, ha="left", fontsize=12, color=ENCRE)
fig.text(0.02, 0.915, SOUS_TITRE, ha="left", va="top", fontsize=7.5, color=ENCRE_SECONDAIRE)
fig.tight_layout(rect=(0, 0, 1, 0.87))
enregistrer(fig, "5b_habitude")
