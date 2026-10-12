#!/usr/bin/env python3
"""Graphiques de la fiche « répondre vite » des faits saignants (n° 2).

    PYTHONPATH=".venv/Lib/site-packages;outils" <python uv> etudes-ponctuelles/2026-10-06-reponse-jalon-03C/graphique.py

Même montage que `calcul.py` à côté : avis 4-5 étoiles de 03C vus et en ligne à la fin
de leur 2e jour, réponse au plus tard au 2e jour, suppression du 3e au 7e jour. Sans les
six enseignes (aucun de leurs avis n'est européen dans 03C, l'Europe est donc entière).

Sorties :
  livrables/restitution_finale/graphiques/faits-saignants/graphiques/reponse_2e_jour.png             deux barres
  livrables/restitution_finale/graphiques/faits-saignants/graphiques/reponse_2e_jour_par_region.png  ensemble, US, Europe
  livrables/restitution_finale/graphiques/faits-saignants/donnees/reponse_2e_jour.csv
"""
import importlib
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "logistic-regression-study" / "python"))
m = importlib.import_module("07F_regression_03C_prenom")

SORTIE = RACINE / "livrables" / "restitution_finale" / "graphiques" / "faits-saignants"
GRAPHIQUE = SORTIE / "graphiques" / "reponse_2e_jour.png"
GRAPHIQUE_REGIONS = SORTIE / "graphiques" / "reponse_2e_jour_par_region.png"
DONNEES = SORTIE / "donnees" / "reponse_2e_jour.csv"

# Palette des graphiques de la restitution (2026-10-05-phenomenes-par-jour).
BLEU, GRIS = "#2a78d6", "#c3c2b7"
ENCRE, ENCRE_2, GRILLE, FOND = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
POPULATION = ("Nouveaux avis 4-5 étoiles publiés du 7 au 17 août 2026, encore en ligne à la fin "
              "de leur 2e jour, sans les six enseignes.\nSuppressions comptées du 3e au 7e jour.")


def espace(n: float) -> str:
    return f"{n:,.0f}".replace(",", " ")


def virgule(x: float, d: int = 1) -> str:
    return f"{x:.{d}f}".replace(".", ",")


def preparer():
    df = m.charger()
    rep = m.variable_reponse(df)
    J = m.JALON_J
    d = df[(df["j_premiere_vue"] <= J) & ~(df["j_suppression"] <= J).fillna(False)
           & ~df["enseigne"]].copy()
    d["reponse_j2"] = (d["j_reponse"] <= J).fillna(False).astype(int)
    d["supprime_j3_j7"] = d["j_suppression"].between(J + 1, m.HORIZON_J).fillna(False).astype(int)
    variables = [x for x in ["prenom", "photo", rep, "pic"] if x != rep] + ["reponse_j2"]

    lignes = []
    for groupe, s in [("Ensemble", d), ("États-Unis", d[d["region"] == "US"]),
                      ("Europe", d[d["region"] == "Europe"])]:
        t = m.tableau(m.ajuster(s, variables, "supprime_j3_j7", secteur_taille=True),
                      groupe, variables)
        r = t[t["variable"] == "reponse_j2"].iloc[0]
        for valeur in (1, 0):
            g = s[s["reponse_j2"] == valeur]
            lignes.append({"groupe": groupe, "reponse_2e_jour": "oui" if valeur else "non",
                           "avis": len(g), "supprimes": int(g["supprime_j3_j7"].sum()),
                           "pour_1000": 1000 * g["supprime_j3_j7"].mean(),
                           "effet_secteur_taille_egaux": r["rapport_de_cotes"],
                           "borne_basse": r["borne_basse"], "borne_haute": r["borne_haute"]})
    return lignes


def habiller(ax, ymax):
    ax.set_facecolor(FOND)
    ax.tick_params(colors=ENCRE_2, labelsize=8, length=0)
    ax.set_ylim(0, ymax)
    ax.grid(axis="y", color=GRILLE, lw=0.8, zorder=0)
    for cote in ["top", "right", "left"]:
        ax.spines[cote].set_visible(False)
    ax.spines["bottom"].set_color(GRILLE)
    ax.set_ylabel("avis supprimés pour 1 000", color=ENCRE_2, fontsize=8)


def etiquette(ax, x, y):
    ax.annotate(virgule(y), (x, y), xytext=(0, 4), textcoords="offset points", ha="center",
                fontsize=9, fontweight="bold", color=ENCRE, zorder=5)


def titres(fig, titre, note):
    fig.text(0.01, 0.97, titre, va="top", fontsize=11, color=ENCRE)
    fig.text(0.01, 0.905, POPULATION, va="top", fontsize=7.5, color=ENCRE_2, linespacing=1.5)
    fig.text(0.01, 0.02, note, va="bottom", fontsize=7.5, color=ENCRE_2)


def deux_barres(lignes):
    l = {x["reponse_2e_jour"]: x for x in lignes if x["groupe"] == "Ensemble"}
    oui, non = l["oui"], l["non"]
    fig, ax = plt.subplots(figsize=(8.5, 4.8), dpi=150)
    fig.patch.set_facecolor(FOND)
    x = [0, 1]
    valeurs = [oui["pour_1000"], non["pour_1000"]]
    ax.bar(x, valeurs, width=0.55, color=[GRIS, BLEU], zorder=3, edgecolor=FOND, linewidth=1)
    for xi, v in zip(x, valeurs):
        etiquette(ax, xi, v)
    ax.set_xticks(x)
    ax.set_xticklabels([f"réponse au 2e jour\n{espace(oui['avis'])} avis",
                        f"pas de réponse au 2e jour\n{espace(non['avis'])} avis"])
    ax.set_xlim(-0.7, 1.7)
    habiller(ax, max(valeurs) * 1.2)
    titres(fig, f"Sans réponse au 2e jour, {virgule(non['pour_1000'], 0)} avis sur 1 000 disparaissent "
                f"avant le 7e jour, contre {virgule(oui['pour_1000'], 0)} avec réponse",
           f"À secteur et taille égaux, l'avis répondu est supprimé "
           f"×{virgule(oui['effet_secteur_taille_egaux'], 2)} (entre ×{virgule(oui['borne_basse'], 2)} "
           f"et ×{virgule(oui['borne_haute'], 2)}), soit deux fois moins souvent.")
    fig.tight_layout(rect=(0, 0.06, 1, 0.82))
    fig.savefig(GRAPHIQUE, facecolor=FOND)
    plt.close(fig)


def par_region(lignes):
    groupes = ["Ensemble", "États-Unis", "Europe"]
    fig, ax = plt.subplots(figsize=(8.5, 4.8), dpi=150)
    fig.patch.set_facecolor(FOND)
    l = {(x["groupe"], x["reponse_2e_jour"]): x for x in lignes}
    largeur, ecart = 0.36, 0.02
    ymax = max(x["pour_1000"] for x in lignes) * 1.2
    for i, g in enumerate(groupes):
        for decal, valeur, couleur in [(-1, "oui", GRIS), (1, "non", BLEU)]:
            xi = i + decal * (largeur + ecart) / 2
            v = l[(g, valeur)]["pour_1000"]
            ax.bar(xi, v, width=largeur, color=couleur, zorder=3, edgecolor=FOND, linewidth=1)
            etiquette(ax, xi, v)
    ax.set_xticks(range(3))
    ax.set_xticklabels([f"{g}\n{espace(l[(g, 'oui')]['avis'] + l[(g, 'non')]['avis'])} avis, "
                        f"{l[(g, 'oui')]['supprimes'] + l[(g, 'non')]['supprimes']} supprimés"
                        for g in groupes])
    habiller(ax, ymax)
    us = (l[("États-Unis", "oui")], l[("États-Unis", "non")])
    effets = " ; ".join(f"{g.lower() if g == 'Ensemble' else g} ×{virgule(l[(g, 'oui')]['effet_secteur_taille_egaux'], 2)}"
                        for g in groupes)
    titres(fig, f"Aux États-Unis, {virgule(us[1]['pour_1000'], 0)} avis sur 1 000 disparaissent sans "
                f"réponse au 2e jour, contre {virgule(us[0]['pour_1000'], 0)} avec réponse",
           f"À secteur et taille égaux, avis répondu : {effets}. "
           f"En Europe, trop peu de suppressions pour affirmer l'écart.")
    fig.legend(handles=[Patch(color=GRIS, label="réponse au 2e jour"),
                        Patch(color=BLEU, label="pas de réponse au 2e jour")],
               loc="upper left", bbox_to_anchor=(0.005, 0.81), ncol=2, frameon=False,
               fontsize=8, labelcolor=ENCRE, handlelength=1.6)
    fig.tight_layout(rect=(0, 0.06, 1, 0.76))
    fig.savefig(GRAPHIQUE_REGIONS, facecolor=FOND)
    plt.close(fig)


def main():
    lignes = preparer()
    GRAPHIQUE.parent.mkdir(parents=True, exist_ok=True)
    DONNEES.parent.mkdir(parents=True, exist_ok=True)
    with DONNEES.open("w", encoding="utf-8") as f:
        cles = list(lignes[0])
        f.write(",".join(cles) + "\n")
        for x in lignes:
            f.write(",".join(f"{x[k]:.4f}" if isinstance(x[k], float) else str(x[k])
                             for k in cles) + "\n")
            print(x)
    deux_barres(lignes)
    par_region(lignes)
    print(f"écrit : {GRAPHIQUE}\nécrit : {GRAPHIQUE_REGIONS}\nécrit : {DONNEES}")


if __name__ == "__main__":
    main()
