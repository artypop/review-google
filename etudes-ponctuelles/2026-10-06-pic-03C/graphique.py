#!/usr/bin/env python3
"""Graphiques de la fiche « demandez vos avis au compte-gouttes » des faits saignants (n° 7).

    PYTHONPATH=".venv/Lib/site-packages;outils" <python uv> etudes-ponctuelles/2026-10-06-pic-03C/graphique.py

Corpus et définitions de 07F, importés tels quels : avis 4-5 étoiles de 03C publiés du
7 au 17 août, supprimés au plus tard au 7e jour. Jour de pic : la fiche reçoit ce jour-là
au moins 3 avis 4-5 étoiles, et au moins 4 fois sa moyenne quotidienne de l'année
précédente. Sans les six enseignes (aucun de leurs avis n'est européen dans 03C, l'Europe
est donc entière). Le script imprime aussi les chiffres avec les enseignes.

Sorties :
  livrables/restitution_finale/graphiques/faits-saignants/graphiques/pic_jour.png             deux barres
  livrables/restitution_finale/graphiques/faits-saignants/graphiques/pic_jour_par_region.png  ensemble, US, Europe
  livrables/restitution_finale/graphiques/faits-saignants/donnees/pic_jour.csv
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
GRAPHIQUE = SORTIE / "graphiques" / "pic_jour.png"
GRAPHIQUE_REGIONS = SORTIE / "graphiques" / "pic_jour_par_region.png"
DONNEES = SORTIE / "donnees" / "pic_jour.csv"

# Palette des graphiques de la restitution (2026-10-05-phenomenes-par-jour).
BLEU, GRIS = "#2a78d6", "#c3c2b7"
ENCRE, ENCRE_2, GRILLE, FOND = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
POPULATION = ("Nouveaux avis 4-5 étoiles publiés du 7 au 17 août 2026, sans les six enseignes, "
              "supprimés au plus tard au 7e jour.\nJour de pic : la fiche reçoit au moins 3 avis "
              "4-5 étoiles et au moins 4 fois sa moyenne quotidienne de l'année précédente.")


def espace(n: float) -> str:
    return f"{n:,.0f}".replace(",", " ")


def virgule(x: float, d: int = 1) -> str:
    return f"{x:.{d}f}".replace(".", ",")


def preparer():
    df = m.charger()
    rep = m.variable_reponse(df)
    variables = ["prenom", "photo", rep, "pic"]

    def ligne(groupe, s, enseignes):
        t = m.tableau(m.ajuster(s, variables, secteur_taille=True), groupe, variables)
        r = t[t["variable"] == "pic"].iloc[0]
        return [{"groupe": groupe, "enseignes": enseignes, "jour_de_pic": "oui" if valeur else "non",
                 "avis": int((s["pic"] == valeur).sum()),
                 "supprimes": int(s.loc[s["pic"] == valeur, "supprime"].sum()),
                 "pour_1000": 1000 * s.loc[s["pic"] == valeur, "supprime"].mean(),
                 "effet_secteur_taille_egaux": r["rapport_de_cotes"],
                 "borne_basse": r["borne_basse"], "borne_haute": r["borne_haute"]}
                for valeur in (0, 1)]

    d = df[~df["enseigne"]]
    lignes = []
    for groupe, s in [("Ensemble", d), ("États-Unis", d[d["region"] == "US"]),
                      ("Europe", d[d["region"] == "Europe"])]:
        lignes += ligne(groupe, s, "sans")
    for groupe, s in [("Ensemble", df), ("États-Unis", df[df["region"] == "US"])]:
        lignes += ligne(groupe, s, "avec")
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


def deux_barres(l):
    normal, pic = l[("Ensemble", "non")], l[("Ensemble", "oui")]
    fig, ax = plt.subplots(figsize=(8.5, 4.8), dpi=150)
    fig.patch.set_facecolor(FOND)
    x = [0, 1]
    valeurs = [normal["pour_1000"], pic["pour_1000"]]
    ax.bar(x, valeurs, width=0.55, color=[GRIS, BLEU], zorder=3, edgecolor=FOND, linewidth=1)
    for xi, v in zip(x, valeurs):
        etiquette(ax, xi, v)
    ax.set_xticks(x)
    ax.set_xticklabels([f"publié un jour normal\n{espace(normal['avis'])} avis",
                        f"publié un jour de pic de la fiche\n{espace(pic['avis'])} avis"])
    ax.set_xlim(-0.7, 1.7)
    habiller(ax, max(valeurs) * 1.2)
    titres(fig, f"Publié un jour de pic, un avis disparaît plus souvent : {virgule(pic['pour_1000'], 0)} "
                f"sur 1 000 en 7 jours, contre {virgule(normal['pour_1000'], 0)}",
           f"À secteur et taille égaux, l'avis publié un jour de pic est supprimé "
           f"×{virgule(pic['effet_secteur_taille_egaux'], 2)} (entre ×{virgule(pic['borne_basse'], 2)} "
           f"et ×{virgule(pic['borne_haute'], 2)}).")
    fig.tight_layout(rect=(0, 0.06, 1, 0.80))
    fig.savefig(GRAPHIQUE, facecolor=FOND)
    plt.close(fig)


def par_region(l):
    groupes = ["Ensemble", "États-Unis", "Europe"]
    fig, ax = plt.subplots(figsize=(8.5, 4.8), dpi=150)
    fig.patch.set_facecolor(FOND)
    largeur, ecart = 0.36, 0.02
    ymax = max(l[(g, v)]["pour_1000"] for g in groupes for v in ("oui", "non")) * 1.2
    for i, g in enumerate(groupes):
        for decal, valeur, couleur in [(-1, "non", GRIS), (1, "oui", BLEU)]:
            xi = i + decal * (largeur + ecart) / 2
            v = l[(g, valeur)]["pour_1000"]
            ax.bar(xi, v, width=largeur, color=couleur, zorder=3, edgecolor=FOND, linewidth=1)
            etiquette(ax, xi, v)
    ax.set_xticks(range(3))
    ax.set_xticklabels([f"{g}\n{espace(l[(g, 'oui')]['avis'] + l[(g, 'non')]['avis'])} avis, "
                        f"{l[(g, 'oui')]['supprimes'] + l[(g, 'non')]['supprimes']} supprimés"
                        for g in groupes])
    habiller(ax, ymax)
    eu = (l[("Europe", "non")], l[("Europe", "oui")])
    effets = " ; ".join(f"{g.lower() if g == 'Ensemble' else g} ×{virgule(l[(g, 'oui')]['effet_secteur_taille_egaux'], 2)}"
                        for g in groupes)
    titres(fig, f"En Europe, {virgule(eu[1]['pour_1000'], 0)} avis sur 1 000 publiés un jour de pic "
                f"disparaissent en 7 jours, contre {virgule(eu[0]['pour_1000'], 0)} un jour normal",
           f"À secteur et taille égaux : {effets}. "
           f"Aux États-Unis, l'écart est trop incertain pour être affirmé.")
    fig.legend(handles=[Patch(color=GRIS, label="publié un jour normal"),
                        Patch(color=BLEU, label="publié un jour de pic de la fiche")],
               loc="upper left", bbox_to_anchor=(0.005, 0.81), ncol=2, frameon=False,
               fontsize=8, labelcolor=ENCRE, handlelength=1.6)
    fig.tight_layout(rect=(0, 0.06, 1, 0.76))
    fig.savefig(GRAPHIQUE_REGIONS, facecolor=FOND)
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
        print(f"{x['groupe']:11s} {x['enseignes']} enseignes, pic {x['jour_de_pic']} : "
              f"{x['avis']:>6} avis, {x['supprimes']:>4} supprimés, {x['pour_1000']:5.1f} pour 1 000 | "
              f"secteur et taille égaux ×{x['effet_secteur_taille_egaux']:.2f} "
              f"[{x['borne_basse']:.2f} ; {x['borne_haute']:.2f}]")
    sans = {(x["groupe"], x["jour_de_pic"]): x for x in lignes if x["enseignes"] == "sans"}
    deux_barres(sans)
    par_region(sans)
    print(f"écrit : {GRAPHIQUE}\nécrit : {GRAPHIQUE_REGIONS}\nécrit : {DONNEES}")


if __name__ == "__main__":
    main()
