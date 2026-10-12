#!/usr/bin/env python3
"""La régression « à secteur et taille égaux » du 07F (graphique 3.1), contrôles cachés puis affichés.

    PYTHONPATH=".venv/Lib/site-packages;outils" <python uv> etudes-ponctuelles/2026-10-09-regression-secteur-taille-controles/calcul.py

Demande de Matthieu du 2026-10-09 : la régression existe déjà (07F, `ajuster(...,
secteur_taille=True)`) ; le secteur, la taille et, pour « les deux », la région y sont en
contrôle et ne sont pas affichés. On en sort le CSV de tous les paramètres et deux
graphiques : l'un sans les contrôles (comme le graphique 3.1), l'autre avec.

Rien n'est réécrit : avis, modèle et références du 07F. Pas de note dans le modèle. Le
script vérifie d'abord qu'il retrouve les rapports de cotes du graphique 3.1
(donnees/regression_03C_prenom_secteur_taille_rapports_de_cotes.csv).

Sorties : livrables/restitution_finale_v2/regression_logistique_2/
  regression_secteur_taille.csv                    tous les paramètres, constante comprise
  regression_secteur_taille_controles_caches.png
  regression_secteur_taille_controles_affiches.png
"""
import importlib
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.ticker import FixedLocator, NullLocator  # noqa: E402
from matplotlib.transforms import blended_transform_factory  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "logistic-regression-study" / "python"))
m = importlib.import_module("07F_regression_03C_prenom")

SORTIE = RACINE / "livrables" / "restitution_finale_v2" / "regression_logistique_2"
BLEU, ENCRE, ENCRE_2, GRILLE, FOND = m.BLEU, m.ENCRE, m.ENCRE_2, m.GRILLE, m.FOND
X_MIN, X_MAX = 0.06, 40

CARACTERISTIQUES = ("Caractéristiques de l'avis", [
    ("prenom", "Prénom cité dans l'avis"),
    ("photo", "Photo jointe"),
    ("sans_reponse_j7", "Pas de réponse du\npropriétaire au 7e jour"),
    ("reponse_j7", "Réponse du propriétaire\nau plus tard au 7e jour"),
    ("pic", "Publié un jour de pic\nsur la fiche")])
CONTROLES = [
    ("Secteur, en contrôle (face à l'automobile)", [
        ("industry_food_beverage", "Restauration"),
        ("industry_healthcare", "Santé"),
        ("industry_home_services", "Services à domicile"),
        ("industry_hospitality", "Hôtellerie"),
        ("industry_travel", "Voyage"),
        ("industry_wellness_fitness", "Sport et bien-être")]),
    ("Taille, en contrôle (face à un seul établissement)", [
        ("bucket_small", "Groupe de 4 à 10\nétablissements"),
        ("bucket_large", "Groupe de 20 à 50\nétablissements")]),
    ("Région, en contrôle (face à l'Europe)", [
        ("region_US", "États-Unis")]),
]
PASSAGES = {"US": "États-Unis", "Europe": "Europe", "tous": "Les deux"}


def ajuster_tout(df: pd.DataFrame, variables: list[str]) -> pd.DataFrame:
    lignes = []
    for passage in PASSAGES:
        d = df if passage == "tous" else df[df["region"] == passage]
        res = m.ajuster(d, variables, secteur_taille=True)
        ic = res.conf_int()
        for nom in res.params.index:
            lignes.append({"passage": passage, "parametre": nom,
                           "role": ("constante" if nom == "const"
                                    else "affiché" if nom in variables else "contrôle"),
                           "rapport_de_cotes": np.exp(res.params[nom]),
                           "borne_basse": np.exp(ic.loc[nom, 0]),
                           "borne_haute": np.exp(ic.loc[nom, 1]),
                           "p_value": res.pvalues[nom],
                           "avis": len(d), "suppressions": int(d["supprime"].sum())})
    return pd.DataFrame(lignes)


def virgule(x: float) -> str:
    return f"{x:.2f}".replace(".", ",")


def espace(n: int) -> str:
    return f"{n:,}".replace(",", " ")


def figure(rr: pd.DataFrame, rep: str, controles: bool, chemin: Path, titre: str) -> None:
    caracteristiques = (CARACTERISTIQUES[0],
                        [(v, n) for v, n in CARACTERISTIQUES[1] if v in ("prenom", "photo", rep, "pic")])
    blocs = [caracteristiques] + (CONTROLES if controles else [])
    pos, entetes, y = {}, [], 0.0
    for b, lignes in blocs:
        entetes.append((y, b))
        y += 0.85
        for v, n in lignes:
            pos[v] = (y, n)
            y += 1
        y += 0.35
    hauteur = y
    haut_fig = 0.36 * hauteur + 2.2

    fig, axes = plt.subplots(1, 3, figsize=(11.5, haut_fig), dpi=150, sharey=True)
    fig.patch.set_facecolor(FOND)
    for ax, (passage, titre_panneau) in zip(axes, PASSAGES.items()):
        t = rr[rr["passage"] == passage].set_index("parametre")
        ax.set_facecolor(FOND)
        ax.axvline(1, color=ENCRE_2, lw=1, zorder=1)
        for v, (yi, _) in pos.items():
            if v not in t.index:
                ax.text(1, yi, "sans objet", ha="center", va="center", fontsize=7,
                        color=ENCRE_2, style="italic",
                        bbox=dict(facecolor=FOND, edgecolor="none", pad=1))
                continue
            r = t.loc[v]
            net = r["p_value"] < 0.05
            bas, haut = max(r["borne_basse"], X_MIN), min(r["borne_haute"], X_MAX)
            ax.plot([bas, haut], [yi, yi], color=BLEU, lw=2, solid_capstyle="round", zorder=2)
            for borne, limite, sens in [(r["borne_basse"], X_MIN, "<"), (r["borne_haute"], X_MAX, ">")]:
                if (sens == "<" and borne < limite) or (sens == ">" and borne > limite):
                    ax.plot(limite, yi, marker=sens, color=BLEU, ms=6, zorder=2)
            ax.plot(r["rapport_de_cotes"], yi, "o", ms=7, mew=2, zorder=3,
                    mec=BLEU, mfc=BLEU if net else FOND)
            ax.annotate(virgule(r["rapport_de_cotes"]), (r["rapport_de_cotes"], yi),
                        xytext=(0, 6), textcoords="offset points", ha="center",
                        fontsize=7.5, color=ENCRE, fontweight="bold" if net else "normal")
        for ye, _ in entetes[1:]:
            ax.axhline(ye - 0.3, color=GRILLE, lw=0.8, zorder=0)
        ax.set_xscale("log")
        ax.set_xlim(X_MIN, X_MAX)
        graduations = [0.125, 0.25, 0.5, 1, 2, 4, 8, 16, 32]
        ax.xaxis.set_major_locator(FixedLocator(graduations))
        ax.xaxis.set_minor_locator(NullLocator())
        ax.set_xticklabels([f"{g:g}".replace(".", ",") for g in graduations])
        ax.grid(axis="x", color=GRILLE, lw=0.8, zorder=0)
        ax.tick_params(colors=ENCRE_2, labelsize=7.5, length=0)
        for cote in ["top", "right", "left"]:
            ax.spines[cote].set_visible(False)
        ax.spines["bottom"].set_color(GRILLE)
        ax.set_ylim(hauteur - 0.2, -0.5)
        n_avis, n_supp = int(t["avis"].iloc[0]), int(t["suppressions"].iloc[0])
        ax.set_title(f"{titre_panneau}\n", fontsize=10, color=ENCRE, loc="left")
        ax.text(0, 1.005, f"{espace(n_avis)} avis, {espace(n_supp)} supprimés",
                transform=ax.transAxes, fontsize=7.5, color=ENCRE_2, va="bottom")

    ax0 = axes[0]
    ax0.set_yticks([yi for yi, _ in pos.values()])
    ax0.set_yticklabels([n for _, n in pos.values()], fontsize=8.5, color=ENCRE)
    bord_gauche = blended_transform_factory(fig.transFigure, ax0.transData)
    for ye, b in entetes:
        ax0.text(0.01, ye, b, transform=bord_gauche, ha="left", va="center",
                 fontsize=8.5, color=ENCRE_2, fontweight="bold")
    axes[1].set_xlabel("risque de suppression (1 = pas d'effet)", color=ENCRE_2, fontsize=8)

    fig.text(0.01, 1 - 0.12 / haut_fig, titre, va="top", fontsize=11.5, color=ENCRE)
    legende = [Line2D([0], [0], marker="o", color=BLEU, mfc=BLEU, ms=7, lw=2,
                      label="significatif (p < 0,05)"),
               Line2D([0], [0], marker="o", color=BLEU, mfc=FOND, ms=7, mew=2, lw=2,
                      label="non significatif")]
    fig.legend(handles=legende, loc="upper left", bbox_to_anchor=(0.005, 1 - 0.62 / haut_fig),
               frameon=False, fontsize=8, labelcolor=ENCRE, ncol=2, handlelength=2)
    reference = ("avis répondu au plus tard au 7e jour" if rep == "sans_reponse_j7"
                 else "avis sans réponse au 7e jour")
    cache = ("" if controles else
             " Le secteur, la taille et, pour « les deux », la région sont dans le modèle en contrôle, non affichés.")
    fig.text(0.01, 0.1 / haut_fig,
             "Données : corpus 03C (03C_7_17_aout_prenom.parquet), avis 4-5 étoiles publiés du 7 au 17 août 2026, "
             "suivis 7 jours ; supprimé = disparu au plus tard au 7e jour.\n"
             "Six enseignes comprises. Un seul modèle par panneau : tous les paramètres sont estimés ensemble."
             f"{cache}\n"
             f"Références : sans prénom, sans photo, {reference}, jour normal, automobile, "
             "un seul établissement, Europe.",
             fontsize=7, color=ENCRE_2, va="bottom")
    fig.subplots_adjust(left=0.2, right=0.985, top=1 - 1.25 / haut_fig,
                        bottom=1.05 / haut_fig, wspace=0.08)
    fig.savefig(chemin, facecolor=FOND)
    plt.close(fig)


def main() -> None:
    df = m.charger()
    rep = m.variable_reponse(df)
    variables = ["prenom", "photo", rep, "pic"]
    rr = ajuster_tout(df, variables)

    # Contrôle : on retombe sur les rapports de cotes du graphique 3.1.
    attendu = pd.read_csv(m.DONNEES / "regression_03C_prenom_secteur_taille_rapports_de_cotes.csv")
    idx = rr.set_index(["passage", "parametre"])
    for _, a in attendu.iterrows():
        if abs(idx.loc[(a["passage"], a["variable"]), "rapport_de_cotes"] - a["rapport_de_cotes"]) > 1e-6:
            raise SystemExit(f"Écart avec le graphique 3.1 : {a['passage']} {a['variable']}")
    print(f"  contrôle : les {len(attendu)} rapports de cotes du graphique 3.1 sont retrouvés")

    SORTIE.mkdir(parents=True, exist_ok=True)
    rr.to_csv(SORTIE / "regression_secteur_taille.csv", index=False)
    titre = "Risque de suppression d'un avis 4-5 étoiles dans les 7 jours, à secteur et taille égaux"
    figure(rr, rep, False, SORTIE / "regression_secteur_taille_controles_caches.png",
           f"{titre}\nContrôles (secteur, taille, région) dans le modèle mais non affichés")
    figure(rr, rep, True, SORTIE / "regression_secteur_taille_controles_affiches.png",
           f"{titre}\nTous les paramètres du modèle, contrôles (secteur, taille, région) affichés")

    pd.set_option("display.width", 200)
    fmt = {c: "{:.2f}".format for c in ["rapport_de_cotes", "borne_basse", "borne_haute"]}
    fmt["p_value"] = "{:.3f}".format
    print(rr.drop(columns=["avis", "suppressions"]).to_string(index=False, formatters=fmt))
    print(f"\nécrit dans {SORTIE}")


if __name__ == "__main__":
    main()
