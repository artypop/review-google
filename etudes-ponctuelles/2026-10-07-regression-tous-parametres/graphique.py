#!/usr/bin/env python3
"""La régression « à secteur et taille égaux » du 07F, avec tous ses paramètres affichés.

    PYTHONPATH=".venv/Lib/site-packages;outils" <python uv> etudes-ponctuelles/2026-10-07-regression-tous-parametres/graphique.py

Demande de Matthieu du 2026-10-07 : le graphique regression_03C_prenom_secteur_taille.png
(graphique 3.1 des faits saignants) montre quatre caractéristiques ; le modèle contient
aussi le secteur, la taille et, pour « les deux », la région. Ce script les affiche tous.

Modèle et avis repris tels quels du 07F (`charger()`, `variable_reponse()`, `ajuster(...,
secteur_taille=True)`), rien n'est réécrit : avis 4-5 étoiles de 03C publiés du 7 au 17
août, supprimés au plus tard au 7e jour, marges d'incertitude groupées par fiche.
Références : secteur automobile, un seul établissement, Europe, sans prénom, sans photo,
avis répondu au plus tard au 7e jour (la modalité la plus fréquente), jour normal.

Ajout du 2026-10-07 (Matthieu) : la note, 5 étoiles face à 4 étoiles. Le modèle n'est
donc plus celui du graphique 3.1 ; le script vérifie d'abord que, sans la note, il le
retrouve.

Deux versions : six enseignes comprises (celle du graphique 3.1), et sans les six
enseignes. Les enseignes n'ont aucun avis européen dans 03C : le panneau Europe est le
même dans les deux.

La constante (le risque de l'avis de référence) n'est pas sur le graphique, qui montre
des multiplicateurs ; elle est dans le CSV.

Sorties :
  livrables/restitution_finale/graphiques/regression_03C_prenom_tous_parametres.png
  livrables/restitution_finale/graphiques/regression_03C_prenom_tous_parametres_sans_enseignes.png
  livrables/restitution_finale/donnees/regression_03C_prenom_tous_parametres.csv
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

FINALE = RACINE / "livrables" / "restitution_finale"
GRAPHIQUES = {"avec": FINALE / "graphiques" / "regression_03C_prenom_tous_parametres.png",
              "sans": FINALE / "graphiques" / "regression_03C_prenom_tous_parametres_sans_enseignes.png"}
DONNEES = FINALE / "donnees" / "regression_03C_prenom_tous_parametres.csv"
BLEU, ENCRE, ENCRE_2, GRILLE, FOND = m.BLEU, m.ENCRE, m.ENCRE_2, m.GRILLE, m.FOND
X_MIN, X_MAX = 0.06, 40

# Lignes du graphique, par bloc : (nom de la colonne du modèle, libellé).
BLOCS = [
    ("Caractéristiques de l'avis", [
        ("prenom", "Prénom cité dans l'avis"),
        ("photo", "Photo jointe"),
        ("sans_reponse_j7", "Pas de réponse du\npropriétaire au 7e jour"),
        ("reponse_j7", "Réponse du propriétaire\nau plus tard au 7e jour"),
        ("pic", "Publié un jour de pic\nsur la fiche")]),
    ("Note (face à 4 étoiles)", [
        ("cinq_etoiles", "5 étoiles")]),
    ("Secteur (face à l'automobile)", [
        ("industry_food_beverage", "Restauration"),
        ("industry_healthcare", "Santé"),
        ("industry_home_services", "Services à domicile"),
        ("industry_hospitality", "Hôtellerie"),
        ("industry_travel", "Voyage"),
        ("industry_wellness_fitness", "Sport et bien-être")]),
    ("Taille (face à un seul établissement)", [
        ("bucket_small", "Groupe de 4 à 10\nétablissements"),
        ("bucket_large", "Groupe de 20 à 50\nétablissements")]),
    ("Région (face à l'Europe)", [
        ("region_US", "États-Unis")]),
]
PASSAGES = {"US": "États-Unis", "Europe": "Europe", "tous": "Les deux"}


def ajuster_tout(df: pd.DataFrame, variables: list[str], jeu: str) -> pd.DataFrame:
    lignes = []
    for passage in PASSAGES:
        d = df if passage == "tous" else df[df["region"] == passage]
        res = m.ajuster(d, variables, secteur_taille=True)
        ic = res.conf_int()
        for nom in res.params.index:
            lignes.append({"jeu": jeu, "passage": passage, "parametre": nom,
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


def figure(rr: pd.DataFrame, rep: str, chemin: Path, titre: str) -> None:
    blocs = [(t, [(v, n) for v, n in lignes if v in ("prenom", "photo", rep, "pic")
                  or not v.startswith(("sans_reponse", "reponse"))])
             for t, lignes in BLOCS]
    # Positions : un titre de bloc, puis ses lignes, de haut en bas.
    pos, entetes, y = {}, [], 0.0
    for t, lignes in blocs:
        entetes.append((y, t))
        y += 0.85
        for v, n in lignes:
            pos[v] = (y, n)
            y += 1
        y += 0.35
    hauteur = y

    fig, axes = plt.subplots(1, 3, figsize=(11.5, 0.36 * hauteur + 1.7), dpi=150, sharey=True)
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
    for ye, t in entetes:
        ax0.text(0.01, ye, t, transform=bord_gauche, ha="left", va="center",
                 fontsize=8.5, color=ENCRE_2, fontweight="bold")
    axes[1].set_xlabel("risque de suppression (1 = pas d'effet)", color=ENCRE_2, fontsize=8)

    fig.text(0.01, 0.99, titre, va="top", fontsize=12, color=ENCRE)
    legende = [Line2D([0], [0], marker="o", color=BLEU, mfc=BLEU, ms=7, lw=2,
                      label="significatif (p < 0,05)"),
               Line2D([0], [0], marker="o", color=BLEU, mfc=FOND, ms=7, mew=2, lw=2,
                      label="non significatif")]
    fig.legend(handles=legende, loc="upper left", bbox_to_anchor=(0.005, 0.965),
               frameon=False, fontsize=8, labelcolor=ENCRE, ncol=2, handlelength=2)
    reference = ("avis répondu au plus tard au 7e jour" if rep == "sans_reponse_j7"
                 else "avis sans réponse au 7e jour")
    fig.text(0.01, 0.012,
             f"Avis 4-5 étoiles de 03C publiés du 7 au 17 août 2026, supprimés au plus tard au 7e jour. "
             f"Un seul modèle par panneau : tous les paramètres sont estimés ensemble.\n"
             f"Références : sans prénom, sans photo, {reference}, jour normal, 4 étoiles, automobile, "
             f"un seul établissement, Europe. La région n'est dans le modèle que pour « les deux ».",
             fontsize=7, color=ENCRE_2, va="bottom")
    fig.subplots_adjust(left=0.2, right=0.985, top=1 - 1.05 / (0.36 * hauteur + 1.7),
                        bottom=0.75 / (0.36 * hauteur + 1.7), wspace=0.08)
    chemin.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(chemin, facecolor=FOND)
    plt.close(fig)


def main() -> None:
    df = m.charger()
    rep = m.variable_reponse(df)
    variables = ["prenom", "photo", rep, "pic"]

    # Contrôle : sans la note, le modèle avec enseignes retombe sur le graphique 3.1.
    attendu = pd.read_csv(m.DONNEES / "regression_03C_prenom_secteur_taille_rapports_de_cotes.csv")
    avec = ajuster_tout(df, variables, "").set_index(["passage", "parametre"])
    for _, a in attendu.iterrows():
        if abs(avec.loc[(a["passage"], a["variable"]), "rapport_de_cotes"] - a["rapport_de_cotes"]) > 1e-6:
            raise SystemExit(f"Écart avec le graphique 3.1 : {a['passage']} {a['variable']}")

    # Demande de Matthieu du 2026-10-07 : la note en plus, 4 étoiles en référence.
    if not df["star"].isin([4, 5]).all():
        raise SystemExit("Note hors de 4 et 5 étoiles.")
    df["cinq_etoiles"] = (df["star"] == 5).astype(int)
    for jeu, s in [("six enseignes comprises", df), ("sans les six enseignes", df[~df["enseigne"]])]:
        for note, g in s.groupby("star"):
            print(f"{jeu:24s} {note} étoiles : {len(g):6d} avis, {int(g['supprime'].sum()):4d} supprimés "
                  f"({1000 * g['supprime'].mean():.1f} pour 1 000)")
    variables = variables + ["cinq_etoiles"]
    rr = pd.concat([ajuster_tout(df, variables, "six enseignes comprises"),
                    ajuster_tout(df[~df["enseigne"]], variables, "sans les six enseignes")])

    DONNEES.parent.mkdir(parents=True, exist_ok=True)
    rr.to_csv(DONNEES, index=False)
    for cle, jeu in [("avec", "six enseignes comprises"), ("sans", "sans les six enseignes")]:
        figure(rr[rr["jeu"] == jeu], rep, GRAPHIQUES[cle],
               "Risque de suppression d'un avis 4-5 étoiles dans les 7 jours : "
               f"tous les paramètres du modèle ({jeu})")

    pd.set_option("display.width", 200)
    fmt = {c: "{:.2f}".format for c in ["rapport_de_cotes", "borne_basse", "borne_haute"]}
    fmt["p_value"] = "{:.3f}".format
    print(rr.drop(columns=["avis", "suppressions"]).to_string(index=False, formatters=fmt))
    print(f"\nécrit : {GRAPHIQUES['avec']}\nécrit : {GRAPHIQUES['sans']}\nécrit : {DONNEES}")


if __name__ == "__main__":
    main()
