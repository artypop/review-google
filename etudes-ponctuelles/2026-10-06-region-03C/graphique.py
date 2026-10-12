#!/usr/bin/env python3
"""Graphique de la fiche « aux États-Unis, Google a la main lourde » des faits saignants (n° 8).

    PYTHONPATH=".venv/Lib/site-packages;outils" <python uv> etudes-ponctuelles/2026-10-06-region-03C/graphique.py

Même base que les graphiques n° 2 et n° 7 : avis 4-5 étoiles de 03C publiés du 7 au
17 août, supprimés au plus tard au 7e jour (corpus et définitions de 07F, importés tels
quels). Deux versions : avec et sans les six enseignes. Aucun avis des enseignes n'est
européen dans 03C : l'Europe est la même dans les deux.

Écart entre régions : un indicateur États-Unis, à secteur, taille et jour de publication
égaux ; avis d'une même fiche regroupés pour les marges d'incertitude.

Sorties :
  livrables/restitution_finale/graphiques/faits-saignants/graphiques/region_us_europe.png
  livrables/restitution_finale/graphiques/faits-saignants/donnees/region_us_europe.csv
"""
import importlib
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import statsmodels.api as sm  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "logistic-regression-study" / "python"))
m = importlib.import_module("07F_regression_03C_prenom")

SORTIE = RACINE / "livrables" / "restitution_finale" / "graphiques" / "faits-saignants"
GRAPHIQUE = SORTIE / "graphiques" / "region_us_europe.png"
DONNEES = SORTIE / "donnees" / "region_us_europe.csv"

# Palette des graphiques de la restitution (2026-10-05-phenomenes-par-jour).
BLEU, GRIS = "#2a78d6", "#c3c2b7"
ENCRE, ENCRE_2, GRILLE, FOND = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
POPULATION = ("Nouveaux avis 4-5 étoiles publiés du 7 au 17 août 2026, supprimés au plus tard "
              "au 7e jour.\nLes six enseignes n'ont aucun avis européen sur cette période : "
              "l'Europe est la même dans les deux groupes.")


def espace(n: float) -> str:
    return f"{n:,.0f}".replace(",", " ")


def virgule(x: float, d: int = 1) -> str:
    return f"{x:.{d}f}".replace(".", ",")


def ecart_us(s: pd.DataFrame):
    """×US à secteur, taille et jour de publication égaux."""
    X = pd.concat([(s["region"] == "US").astype(float).rename("US"),
                   pd.get_dummies(s["industry"].astype(str), prefix="sect", dtype=float)
                   .drop(columns=f"sect_{m.REF_SECTEUR}"),
                   pd.get_dummies(s["bucket"].astype(str), prefix="taille", dtype=float)
                   .drop(columns=f"taille_{m.REF_TAILLE}"),
                   pd.get_dummies(pd.to_datetime(s["created_at"]).dt.day, prefix="jour",
                                  drop_first=True, dtype=float)], axis=1)
    X = sm.add_constant(X.loc[:, X.std() > 0], has_constant="add")
    res = sm.GLM(s["supprime"].astype(float), X, family=sm.families.Binomial()).fit(
        cov_type="cluster", cov_kwds={"groups": s["cid"].factorize()[0]})
    ic = res.conf_int().loc["US"]
    return np.exp(res.params["US"]), np.exp(ic[0]), np.exp(ic[1])


def preparer():
    df = m.charger()
    lignes = []
    for enseignes, s in [("avec", df), ("sans", df[~df["enseigne"]])]:
        effet, bas, haut = ecart_us(s)
        for region, nom in [("US", "États-Unis"), ("Europe", "Europe")]:
            g = s[s["region"] == region]
            lignes.append({"enseignes": enseignes, "region": nom, "avis": len(g),
                           "supprimes": int(g["supprime"].sum()),
                           "pour_1000": 1000 * g["supprime"].mean(),
                           "effet_us_secteur_taille_jour_egaux": effet,
                           "borne_basse": bas, "borne_haute": haut})
    return lignes


def graphique(lignes):
    l = {(x["enseignes"], x["region"]): x for x in lignes}
    groupes = [("avec", "Avec les six enseignes"), ("sans", "Sans les six enseignes")]
    fig, ax = plt.subplots(figsize=(8.5, 4.8), dpi=150)
    fig.patch.set_facecolor(FOND)
    ax.set_facecolor(FOND)
    largeur, ecart = 0.34, 0.02
    for i, (cle, _) in enumerate(groupes):
        for decal, region, couleur in [(-1, "États-Unis", BLEU), (1, "Europe", GRIS)]:
            xi = i + decal * (largeur + ecart) / 2
            v = l[(cle, region)]["pour_1000"]
            ax.bar(xi, v, width=largeur, color=couleur, zorder=3, edgecolor=FOND, linewidth=1)
            ax.annotate(virgule(v), (xi, v), xytext=(0, 4), textcoords="offset points",
                        ha="center", fontsize=9, fontweight="bold", color=ENCRE, zorder=5)
    ax.set_xticks(range(2))
    ax.set_xticklabels([f"{nom}\nÉtats-Unis {espace(l[(cle, 'États-Unis')]['avis'])} avis, "
                        f"Europe {espace(l[(cle, 'Europe')]['avis'])} avis" for cle, nom in groupes])
    ax.set_xlim(-0.6, 1.6)
    ax.tick_params(colors=ENCRE_2, labelsize=8, length=0)
    ax.set_ylim(0, max(x["pour_1000"] for x in lignes) * 1.2)
    ax.grid(axis="y", color=GRILLE, lw=0.8, zorder=0)
    for cote in ["top", "right", "left"]:
        ax.spines[cote].set_visible(False)
    ax.spines["bottom"].set_color(GRILLE)
    ax.set_ylabel("avis supprimés pour 1 000", color=ENCRE_2, fontsize=8)

    us, eu = l[("sans", "États-Unis")], l[("sans", "Europe")]
    avec = l[("avec", "États-Unis")]
    fig.text(0.01, 0.97, f"Sans les enseignes : {virgule(us['pour_1000'], 0)} avis supprimés pour 1 000 "
                         f"aux États-Unis, {virgule(eu['pour_1000'], 0)} en Europe",
             va="top", fontsize=11, color=ENCRE)
    fig.text(0.01, 0.905, POPULATION, va="top", fontsize=7.5, color=ENCRE_2, linespacing=1.5)
    fig.text(0.01, 0.02, f"À secteur, taille et jour de publication égaux, avis américain : "
                         f"×{virgule(us['effet_us_secteur_taille_jour_egaux'], 2)} sans les enseignes "
                         f"(entre ×{virgule(us['borne_basse'], 2)} et ×{virgule(us['borne_haute'], 2)}, "
                         f"écart incertain) ; "
                         f"×{virgule(avec['effet_us_secteur_taille_jour_egaux'], 2)} avec.",
             va="bottom", fontsize=7.5, color=ENCRE_2)
    fig.legend(handles=[Patch(color=BLEU, label="États-Unis"), Patch(color=GRIS, label="Europe")],
               loc="upper left", bbox_to_anchor=(0.005, 0.81), ncol=2, frameon=False,
               fontsize=8, labelcolor=ENCRE, handlelength=1.6)
    fig.tight_layout(rect=(0, 0.06, 1, 0.76))
    fig.savefig(GRAPHIQUE, facecolor=FOND)
    plt.close(fig)


def main():
    lignes = preparer()
    GRAPHIQUE.parent.mkdir(parents=True, exist_ok=True)
    DONNEES.parent.mkdir(parents=True, exist_ok=True)
    cles = list(lignes[0])
    with DONNEES.open("w", encoding="utf-8") as f:
        f.write(",".join(cles) + "\n")
        for x in lignes:
            f.write(",".join(f"{x[k]:.4f}" if isinstance(x[k], float) else str(x[k])
                             for k in cles) + "\n")
    for x in lignes:
        print(f"{x['enseignes']} enseignes, {x['region']:10s} : {x['avis']:>6} avis, "
              f"{x['supprimes']:>4} supprimés, {x['pour_1000']:5.1f} pour 1 000 | ×US à secteur, "
              f"taille, jour égaux {x['effet_us_secteur_taille_jour_egaux']:.2f} "
              f"[{x['borne_basse']:.2f} ; {x['borne_haute']:.2f}]")
    graphique(lignes)
    print(f"écrit : {GRAPHIQUE}\nécrit : {DONNEES}")


if __name__ == "__main__":
    main()
