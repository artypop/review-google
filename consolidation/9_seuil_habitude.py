"""9. Le seuil de 75 % sur l'habitude de réponse : le résultat en dépend-il ?

    nice -n 19 uv run python consolidation/9_seuil_habitude.py      # les deux points, environ 3 minutes
    nice -n 19 uv run python consolidation/9_seuil_habitude.py 5    # le point 5 seul, 30 secondes
    nice -n 19 uv run python consolidation/9_seuil_habitude.py 8    # le point 8 seul, 2 min 15, 4 Go de mémoire
    uv run python consolidation/9_seuil_habitude.py figures         # retrace les figures depuis les CSV

LA QUESTION
  Les points 5 et 8 séparent les fiches qui répondent à plus de 75 % de leurs
  avis des autres. Ce 75 % vient de l'étude 08B et n'a jamais été comparé à une
  autre coupure. L'effet de la réponse grandit-il régulièrement avec l'habitude
  de la fiche, ou dépend-il de l'endroit où l'on coupe ?

CE QUE FAIT CE SCRIPT
  Il relance les scripts des points 5 et 8 tels quels, quatre fois, en ne
  changeant que les coupures de l'habitude (`commun.COUPURES_HABITUDE`) :
    - 75 % : le réglage des points 5 et 8, pour mémoire ;
    - 25, 50 et 75 % : quatre tranches ;
    - 50 % ;
    - 90 %.
  Mêmes avis, mêmes colonnes de contrôle, même règle de citation. Les sorties
  des points 5 et 8 ne sont pas réécrites : ce script ne garde que les effets de
  la réponse et les range dans un CSV par point.

LECTURE
  Si l'effet descend par paliers d'une tranche à l'autre, l'habitude joue de
  façon continue et 75 % n'est qu'un repère. S'il saute d'une coupure à
  l'autre, le résultat des points 5 et 8 tient au réglage.

Produit :
  sorties/9_seuil_habitude_point5.csv   les effets de la réponse du point 5, par découpage
  sorties/9_seuil_habitude_point8.csv   ceux du point 8
  sorties/figures/9_seuil_habitude_point5.png, 9_seuil_habitude_point8.png
"""
import gc
import runpy
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter, NullFormatter

import commun

DECOUPAGES = {
    "coupure à 75 % (points 5 et 8)": [0.75],
    "quatre tranches : 25, 50, 75 %": [0.25, 0.50, 0.75],
    "coupure à 50 %": [0.50],
    "coupure à 90 %": [0.90],
}
# (script, séparateur entre le début de la colonne et l'habitude, début à retirer)
POINTS = {"5": ("5_reponse_jour_par_jour", "réponse "),
          "8": ("8_regression_reponse_base", "réponse : avis de ")}
# Ce que montre la figure : le découpage en quatre tranches, sur ces passages.
PASSAGES_FIGURE = {"5": ["mono + small, tous", "large, sans_enseignes"],
                   "8": ["ensemble, sans_enseignes", "ensemble, tous"]}
SERIES_FIGURE = {"5": ["jour même", "1 jour", "2 jours", "3 jours et plus"],
                 "8": ["8 à 30 jours", "31 à 90 jours", "91 à 365 jours", "plus d'un an"]}
COULEURS_SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#8a5cd0"]

ecrire_csv, enregistrer, requete_bigquery = commun.ecrire_csv, commun.enregistrer, commun.requete
tables, lues = {}, {}


def requete(nom):
    """Une seule lecture de BigQuery par requête : les quatre découpages lisent les mêmes lignes."""
    if nom not in lues:
        lues[nom] = requete_bigquery(nom)
    return lues[nom].copy()


# Les scripts des points 5 et 8 écrivent dans `tables` au lieu de réécrire leurs CSV et leur figure.
commun.requete = requete
commun.ecrire_csv = lambda df, nom: tables.__setitem__(nom, df)
commun.enregistrer = lambda fig, nom: plt.close(fig)

def calculer(point):
    """Relance le script du point avec chaque découpage et garde les effets de la réponse."""
    script, debut = POINTS[point]
    morceaux = []
    for decoupage, coupures in DECOUPAGES.items():
        print(f"--- point {point}, {decoupage}")
        commun.COUPURES_HABITUDE = coupures
        runpy.run_path(str(commun.DOSSIER / f"{script}.py"), run_name="__main__")
        e = tables[f"{point}_effets"]
        e = e[e["colonne"].str.startswith(debut)].copy()
        # « réponse 1 jour, fiche qui répond à plus de 75 % » -> case « 1 jour », habitude « plus de 75 % »
        decoupe = e["colonne"].str.removeprefix(debut).str.split(", fiche qui répond à ", expand=True)
        e.insert(0, "decoupage", decoupage)
        e.insert(2, "habitude", decoupe[1])
        e.insert(3, "delai_de_la_reponse" if point == "5" else "age_de_l_avis", decoupe[0])
        morceaux.append(e.drop(columns="colonne"))
        gc.collect()
    lues.clear()
    ecrire_csv(pd.concat(morceaux, ignore_index=True), f"9_seuil_habitude_point{point}")


def tracer(point):
    """Contrôle : les quatre tranches, de la fiche qui répond le moins à celle qui répond le plus."""
    effets = pd.read_csv(commun.SORTIES / f"9_seuil_habitude_point{point}.csv", sep=";", decimal=",")
    commun.COUPURES_HABITUDE = DECOUPAGES["quatre tranches : 25, 50, 75 %"]
    tranches = commun.noms_habitudes()
    q = effets[(effets["decoupage"] == "quatre tranches : 25, 50, 75 %") & effets["risque_relatif"].notna()]
    serie = q.columns[3]
    fig, axes = commun.figure(1, 2, largeur=13, hauteur=4.8)
    for ax, passage in zip(axes.flat, PASSAGES_FIGURE[point]):
        p = q[q["passage"] == passage]
        for i, (case, couleur) in enumerate(zip(SERIES_FIGURE[point], COULEURS_SERIES)):
            c = p[p[serie] == case]
            x = np.array([tranches.index(h) for h in c["habitude"]]) + 0.12 * (i - 1.5)
            ax.errorbar(x, c["risque_relatif"], yerr=[c["risque_relatif"] - c["fourchette_basse"],
                                                      c["fourchette_haute"] - c["risque_relatif"]],
                        fmt="none", ecolor="#bdbcb6", elinewidth=1.2)
            ax.plot(x, c["risque_relatif"], color=couleur, linewidth=1, alpha=0.5)
            # Point plein : citable. Point vide : non citable.
            ax.scatter(x, c["risque_relatif"], s=42, zorder=3, edgecolors=couleur,
                       facecolors=[couleur if v == "oui" else commun.FOND for v in c["citable"]])
            ax.scatter([], [], s=42, color=couleur, label=case)
        ax.axhline(1, color="#52514e", linewidth=1)
        ax.set_yscale("log")
        ax.set_yticks([0.1, 0.2, 0.5, 1, 2, 5])
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"×{v:g}".replace(".", ",")))
        ax.yaxis.set_minor_formatter(NullFormatter())
        ax.set_ylim(0.04, 12)
        ax.set_xticks(range(len(tranches)), [f"répond à\n{h}" for h in tranches])
        ax.set_xlim(-0.5, len(tranches) - 0.5)
        ax.set_title(passage)
        ax.legend(loc="upper left", ncols=2, fontsize=8)
    fig.suptitle(f"Point {point} — avis répondu face à un avis sans réponse, selon l'habitude de la fiche "
                 "(point plein : citable)")
    enregistrer(fig, f"9_seuil_habitude_point{point}")


demande = sys.argv[1:] or list(POINTS)
for point in POINTS:
    if point in demande:
        calculer(point)
    if point in demande or "figures" in demande:
        tracer(point)
