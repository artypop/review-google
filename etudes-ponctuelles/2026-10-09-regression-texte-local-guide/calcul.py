#!/usr/bin/env python3
"""La régression « tous paramètres » du 2026-10-07, avec la longueur du texte et le niveau Local Guide en plus.

    PYTHONPATH=".venv/Lib/site-packages;outils" <python uv> etudes-ponctuelles/2026-10-09-regression-texte-local-guide/calcul.py

Demande de Matthieu du 2026-10-09, suite à la réunion avec Romain du 08/10 : régression de
contrôle interne, une pour l'Europe et une pour les États-Unis, six enseignes comprises.

Modèle et avis repris du 07F (`charger()`, `variable_reponse()`, `ajuster(...,
secteur_taille=True)`) : avis 4-5 étoiles de 03C publiés du 7 au 17 août, supprimés au plus
tard au 7e jour, marges d'incertitude groupées par fiche. Références du 07F : sans prénom,
sans photo, avis répondu au plus tard au 7e jour, jour normal, automobile, un seul
établissement. Pas de note (5 étoiles face à 4) : retirée à la demande de Matthieu.

Ajouts :
  longueur du texte   caractères du texte sans les espaces de début et de fin, comme
                      2026-10-06-longueur-texte-03C ; tranches 1-40, 41-80, 81-130,
                      131-240, 241+ ; référence : sans texte.
  niveau Local Guide  1-3 (référence), 4-6, 7-10 ; les avis sans niveau sont écartés.

Sorties : livrables/restitution_finale_v2/regression_logistique/
  regression_texte_local_guide_{us,europe}.png
  regression_texte_local_guide_us_europe.png      les deux régions côte à côte
  regression_texte_local_guide_{us,europe}.csv   tous les paramètres, constante comprise
  regression_texte_local_guide_effectifs.csv      avis et suppressions par modalité
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

SORTIE = RACINE / "livrables" / "restitution_finale_v2" / "regression_logistique"
BLEU, ENCRE, ENCRE_2, GRILLE, FOND = m.BLEU, m.ENCRE, m.ENCRE_2, m.GRILLE, m.FOND
X_MIN, X_MAX = 0.03, 64

BORNES_TEXTE = [-1, 0, 40, 80, 130, 240, 10**9]
TEXTE = ["sans", "1_40", "41_80", "81_130", "131_240", "241_plus"]
GUIDE = {"1_3": (1, 3), "4_6": (4, 6), "7_10": (7, 10)}

BLOCS = [
    ("Caractéristiques de l'avis", [
        ("prenom", "Prénom cité dans l'avis"),
        ("photo", "Photo jointe"),
        ("sans_reponse_j7", "Pas de réponse du\npropriétaire au 7e jour"),
        ("reponse_j7", "Réponse du propriétaire\nau plus tard au 7e jour"),
        ("pic", "Publié un jour de pic\nsur la fiche")]),
    ("Longueur du texte (face à sans texte)", [
        ("texte_1_40", "1 à 40 caractères"),
        ("texte_41_80", "41 à 80 caractères"),
        ("texte_81_130", "81 à 130 caractères"),
        ("texte_131_240", "131 à 240 caractères"),
        ("texte_241_plus", "241 caractères et plus")]),
    ("Niveau Local Guide (face à 1 à 3)", [
        ("guide_4_6", "Niveau 4 à 6"),
        ("guide_7_10", "Niveau 7 à 10")]),
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
]
PASSAGES = {"US": ("États-Unis", "us"), "Europe": ("Europe", "europe")}


def completer(df: pd.DataFrame) -> pd.DataFrame:
    """Ajoute la longueur du texte et le niveau Local Guide aux avis du 07F."""
    con = m.connexion("4GB")
    extra = con.execute(f"""
        SELECT review_id, COALESCE(length(trim(text)), 0) AS longueur, local_guide_level
        FROM '{m.CORPUS.as_posix()}' WHERE star >= 4""").df()
    if extra["review_id"].duplicated().any():
        raise SystemExit("Avis dupliqué dans 03C.")
    n0 = len(df)
    df = df.merge(extra, on="review_id", how="left", validate="one_to_one")
    if len(df) != n0 or df["longueur"].isna().any():
        raise SystemExit("Jointure de la longueur incomplète.")

    df["tranche_texte"] = pd.cut(df["longueur"], BORNES_TEXTE, labels=TEXTE).astype(str)
    for t in TEXTE[1:]:
        df[f"texte_{t}"] = (df["tranche_texte"] == t).astype(int)

    sans_niveau = df["local_guide_level"].isna()
    print(f"  écartés, sans niveau Local Guide : {int(sans_niveau.sum())} avis, "
          f"{int(df.loc[sans_niveau, 'supprime'].sum())} supprimés")
    df = df[~sans_niveau].copy()
    niveau = df["local_guide_level"].astype(int)
    if not niveau.between(1, 10).all():
        raise SystemExit("Niveau Local Guide hors de 1 à 10.")
    df["tranche_guide"] = ""
    for nom, (a, b) in GUIDE.items():
        df.loc[niveau.between(a, b), "tranche_guide"] = nom
    for nom in list(GUIDE)[1:]:
        df[f"guide_{nom}"] = (df["tranche_guide"] == nom).astype(int)
    print(f"  gardés : {len(df)} avis, {int(df['supprime'].sum())} suppressions")
    return df


def effectifs(df: pd.DataFrame) -> pd.DataFrame:
    lignes = []
    for passage in PASSAGES:
        d = df[df["region"] == passage]
        for col in ["tranche_texte", "tranche_guide"]:
            for valeur, g in d.groupby(col):
                lignes.append({"passage": passage, "variable": col, "valeur": valeur,
                               "avis": len(g), "suppressions": int(g["supprime"].sum()),
                               "taux_pour_1000": round(1000 * g["supprime"].mean(), 1)})
    return pd.DataFrame(lignes)


def ajuster_region(df: pd.DataFrame, variables: list[str], passage: str) -> pd.DataFrame:
    d = df[df["region"] == passage]
    res = m.ajuster(d, variables, secteur_taille=True)
    ic = res.conf_int()
    return pd.DataFrame({"passage": passage, "parametre": res.params.index,
                         "rapport_de_cotes": np.exp(res.params.values),
                         "borne_basse": np.exp(ic[0].values),
                         "borne_haute": np.exp(ic[1].values),
                         "p_value": res.pvalues.values,
                         "avis": len(d), "suppressions": int(d["supprime"].sum())})


def virgule(x: float) -> str:
    return f"{x:.2f}".replace(".", ",")


def espace(n: int) -> str:
    return f"{n:,}".replace(",", " ")


def figure(rr: pd.DataFrame, rep: str, chemin: Path, titre: str) -> None:
    t = rr.set_index("parametre")
    blocs = [(b, [(v, n) for v, n in lignes if v in t.index or v.startswith(("industry", "bucket"))])
             for b, lignes in BLOCS]
    pos, entetes, y = {}, [], 0.0
    for b, lignes in blocs:
        entetes.append((y, b))
        y += 0.85
        for v, n in lignes:
            pos[v] = (y, n)
            y += 1
        y += 0.35
    hauteur = y
    haut_fig = 0.36 * hauteur + 1.9

    fig, ax = plt.subplots(figsize=(8, haut_fig), dpi=150)
    fig.patch.set_facecolor(FOND)
    ax.set_facecolor(FOND)
    ax.axvline(1, color=ENCRE_2, lw=1, zorder=1)
    for v, (yi, _) in pos.items():
        if v not in t.index:
            ax.text(1, yi, "aucun avis", ha="center", va="center", fontsize=7,
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
    graduations = [0.0625, 0.125, 0.25, 0.5, 1, 2, 4, 8, 16, 32]
    ax.xaxis.set_major_locator(FixedLocator(graduations))
    ax.xaxis.set_minor_locator(NullLocator())
    ax.set_xticklabels([f"{g:g}".replace(".", ",") for g in graduations])
    ax.grid(axis="x", color=GRILLE, lw=0.8, zorder=0)
    ax.tick_params(colors=ENCRE_2, labelsize=7.5, length=0)
    for cote in ["top", "right", "left"]:
        ax.spines[cote].set_visible(False)
    ax.spines["bottom"].set_color(GRILLE)
    ax.set_ylim(hauteur - 0.2, -0.5)
    ax.set_yticks([yi for yi, _ in pos.values()])
    ax.set_yticklabels([n for _, n in pos.values()], fontsize=8.5, color=ENCRE)
    bord_gauche = blended_transform_factory(fig.transFigure, ax.transData)
    for ye, b in entetes:
        ax.text(0.01, ye, b, transform=bord_gauche, ha="left", va="center",
                fontsize=8.5, color=ENCRE_2, fontweight="bold")
    ax.set_xlabel("risque de suppression (1 = pas d'effet)", color=ENCRE_2, fontsize=8)
    n_avis, n_supp = int(rr["avis"].iloc[0]), int(rr["suppressions"].iloc[0])

    fig.text(0.01, 1 - 0.12 / haut_fig, titre, va="top", fontsize=11.5, color=ENCRE)
    fig.text(0.01, 1 - 0.62 / haut_fig, f"{espace(n_avis)} avis, {espace(n_supp)} supprimés",
             va="top", fontsize=8, color=ENCRE_2)
    legende = [Line2D([0], [0], marker="o", color=BLEU, mfc=BLEU, ms=7, lw=2,
                      label="significatif (p < 0,05)"),
               Line2D([0], [0], marker="o", color=BLEU, mfc=FOND, ms=7, mew=2, lw=2,
                      label="non significatif")]
    fig.legend(handles=legende, loc="upper left", bbox_to_anchor=(0.005, 1 - 0.8 / haut_fig),
               frameon=False, fontsize=8, labelcolor=ENCRE, ncol=2, handlelength=2)
    reference = ("avis répondu au plus tard au 7e jour" if rep == "sans_reponse_j7"
                 else "avis sans réponse au 7e jour")
    fig.text(0.01, 0.1 / haut_fig,
             "Avis 4-5 étoiles de 03C publiés du 7 au 17 août 2026, supprimés au plus tard au 7e jour, "
             "six enseignes comprises.\nAvis sans niveau Local Guide écartés. "
             "Un seul modèle : tous les paramètres sont estimés ensemble.\n"
             f"Références : sans prénom, sans photo, {reference}, jour normal, "
             "sans texte, niveau 1 à 3,\nautomobile, un seul établissement.",
             fontsize=7, color=ENCRE_2, va="bottom")
    fig.subplots_adjust(left=0.3, right=0.97, top=1 - 1.3 / haut_fig,
                        bottom=1.15 / haut_fig)
    fig.savefig(chemin, facecolor=FOND)
    plt.close(fig)


def figure_cote_a_cote(rrs: dict[str, pd.DataFrame], rep: str, chemin: Path, titre: str) -> None:
    """Les deux régressions côte à côte, un panneau par région (demande de Matthieu du 2026-10-09)."""
    index = set().union(*(rr["parametre"] for rr in rrs.values()))
    blocs = [(b, [(v, n) for v, n in lignes if v in index]) for b, lignes in BLOCS]
    pos, entetes, y = {}, [], 0.0
    for b, lignes in blocs:
        entetes.append((y, b))
        y += 0.85
        for v, n in lignes:
            pos[v] = (y, n)
            y += 1
        y += 0.35
    hauteur = y
    haut_fig = 0.36 * hauteur + 2.1

    fig, axes = plt.subplots(1, len(rrs), figsize=(10.5, haut_fig), dpi=150, sharey=True)
    fig.patch.set_facecolor(FOND)
    for ax, (passage, rr) in zip(axes, rrs.items()):
        t = rr.set_index("parametre")
        ax.set_facecolor(FOND)
        ax.axvline(1, color=ENCRE_2, lw=1, zorder=1)
        for v, (yi, _) in pos.items():
            if v not in t.index:
                ax.text(1, yi, "aucun avis", ha="center", va="center", fontsize=7,
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
        n_avis, n_supp = int(rr["avis"].iloc[0]), int(rr["suppressions"].iloc[0])
        ax.set_title(f"{PASSAGES[passage][0]}\n", fontsize=10, color=ENCRE, loc="left")
        ax.text(0, 1.005, f"{espace(n_avis)} avis, {espace(n_supp)} supprimés",
                transform=ax.transAxes, fontsize=7.5, color=ENCRE_2, va="bottom")
        ax.set_xlabel("risque de suppression (1 = pas d'effet)", color=ENCRE_2, fontsize=8)

    ax0 = axes[0]
    ax0.set_yticks([yi for yi, _ in pos.values()])
    ax0.set_yticklabels([n for _, n in pos.values()], fontsize=8.5, color=ENCRE)
    bord_gauche = blended_transform_factory(fig.transFigure, ax0.transData)
    for ye, b in entetes:
        ax0.text(0.01, ye, b, transform=bord_gauche, ha="left", va="center",
                 fontsize=8.5, color=ENCRE_2, fontweight="bold")

    fig.text(0.01, 1 - 0.12 / haut_fig, titre, va="top", fontsize=11.5, color=ENCRE)
    legende = [Line2D([0], [0], marker="o", color=BLEU, mfc=BLEU, ms=7, lw=2,
                      label="significatif (p < 0,05)"),
               Line2D([0], [0], marker="o", color=BLEU, mfc=FOND, ms=7, mew=2, lw=2,
                      label="non significatif")]
    fig.legend(handles=legende, loc="upper left", bbox_to_anchor=(0.005, 1 - 0.62 / haut_fig),
               frameon=False, fontsize=8, labelcolor=ENCRE, ncol=2, handlelength=2)
    reference = ("avis répondu au plus tard au 7e jour" if rep == "sans_reponse_j7"
                 else "avis sans réponse au 7e jour")
    fig.text(0.01, 0.1 / haut_fig,
             "Données : corpus 03C (03C_7_17_aout_prenom.parquet), avis 4-5 étoiles publiés du 7 au 17 août 2026, "
             "suivis 7 jours ; supprimé = disparu au plus tard au 7e jour.\n"
             "Six enseignes comprises, avis sans niveau Local Guide écartés. "
             "Un modèle par région : tous les paramètres d'un panneau sont estimés ensemble.\n"
             f"Références : sans prénom, sans photo, {reference}, jour normal, sans texte, "
             "niveau 1 à 3, automobile, un seul établissement.",
             fontsize=7, color=ENCRE_2, va="bottom")
    fig.subplots_adjust(left=0.22, right=0.985, top=1 - 1.25 / haut_fig,
                        bottom=1.15 / haut_fig, wspace=0.08)
    fig.savefig(chemin, facecolor=FOND)
    plt.close(fig)


def main() -> None:
    df = m.charger()
    rep = m.variable_reponse(df)
    df = completer(df)
    variables = (["prenom", "photo", rep, "pic"]
                 + [f"texte_{t}" for t in TEXTE[1:]] + [f"guide_{g}" for g in list(GUIDE)[1:]])

    SORTIE.mkdir(parents=True, exist_ok=True)
    ef = effectifs(df)
    ef.to_csv(SORTIE / "regression_texte_local_guide_effectifs.csv", index=False)
    print("\n== Effectifs ==\n" + ef.to_string(index=False))

    pd.set_option("display.width", 200)
    fmt = {c: "{:.2f}".format for c in ["rapport_de_cotes", "borne_basse", "borne_haute"]}
    fmt["p_value"] = "{:.3f}".format
    rrs = {}
    for passage, (nom, suffixe) in PASSAGES.items():
        rr = rrs[passage] = ajuster_region(df, variables, passage)
        rr.to_csv(SORTIE / f"regression_texte_local_guide_{suffixe}.csv", index=False)
        figure(rr, rep, SORTIE / f"regression_texte_local_guide_{suffixe}.png",
               f"{nom} : risque de suppression d'un avis 4-5 étoiles dans les 7 jours,\n"
               "avec la longueur du texte et le niveau Local Guide")
        print(f"\n== {nom} ==\n"
              + rr.drop(columns=["avis", "suppressions"]).to_string(index=False, formatters=fmt))
    figure_cote_a_cote(rrs, rep, SORTIE / "regression_texte_local_guide_us_europe.png",
                       "Risque de suppression d'un avis 4-5 étoiles dans les 7 jours, "
                       "avec la longueur du texte et le niveau Local Guide\n"
                       "États-Unis et Europe, tous les paramètres du modèle")
    print(f"\nécrit dans {SORTIE}")


if __name__ == "__main__":
    main()
