#!/usr/bin/env python3
"""Concentration des suppressions sur quelques fiches, fiche n° 9 des faits saignants.

    PYTHONPATH=".venv/Lib/site-packages;outils" <python uv> etudes-ponctuelles/2026-10-06-concentration-03C/graphique.py

Même base que les graphiques n° 2, 7 et 8 : avis 4-5 étoiles de 03C publiés du 7 au
17 août, supprimés au plus tard au 7e jour (corpus et définitions de 07F, importés tels
quels). Les chiffres de la trame (905 fiches sur 8 997, 17 fiches pour le quart)
venaient de deux autres périmètres : toute la base sur deux semaines, et l'étude
2026-09-28-secteurs-et-concentration (avis publiés du 4 au 24 août, toutes notes).

Les fiches sont classées de la plus touchée à la moins touchée (nombre d'avis supprimés,
puis nombre de nouveaux avis à égalité). Pour les N premières, on suit la part des
suppressions qu'elles portent et la part des nouveaux avis qu'elles ont reçus.

Sorties :
  livrables/restitution_finale/graphiques/faits-saignants/graphiques/concentration_fiches.png
  livrables/restitution_finale/graphiques/faits-saignants/donnees/concentration_fiches.csv
  livrables/restitution_finale/graphiques/faits-saignants/donnees/concentration_fiches_seuils.csv
"""
import importlib
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "logistic-regression-study" / "python"))
m = importlib.import_module("07F_regression_03C_prenom")

SORTIE = RACINE / "livrables" / "restitution_finale" / "graphiques" / "faits-saignants"
GRAPHIQUE = SORTIE / "graphiques" / "concentration_fiches.png"
DONNEES = SORTIE / "donnees" / "concentration_fiches.csv"
SEUILS = SORTIE / "donnees" / "concentration_fiches_seuils.csv"

# Palette des graphiques de la restitution (2026-10-05-phenomenes-par-jour).
BLEU, GRIS = "#2a78d6", "#a3a297"
ENCRE, ENCRE_2, GRILLE, FOND = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
POPULATION = ("Nouveaux avis 4-5 étoiles publiés du 7 au 17 août 2026, sans les six enseignes, "
              "supprimés au plus tard au 7e jour.\nFiches classées de la plus touchée à la moins "
              "touchée ; seules les fiches qui ont perdu au moins un avis apparaissent.")


def virgule(x: float, d: int = 0) -> str:
    return f"{x:.{d}f}".replace(".", ",")


def espace(n: float) -> str:
    return f"{n:,.0f}".replace(",", " ")


def courbe(s: pd.DataFrame, enseignes: str) -> pd.DataFrame:
    f = (s.groupby("cid").agg(avis=("supprime", "size"), supprimes=("supprime", "sum"))
         .sort_values(["supprimes", "avis"], ascending=[False, True]).reset_index())
    f = f[f["supprimes"] > 0].copy()
    f["n_fiches"] = range(1, len(f) + 1)
    f["part_suppressions_pct"] = 100 * f["supprimes"].cumsum() / s["supprime"].sum()
    f["part_nouveaux_avis_pct"] = 100 * f["avis"].cumsum() / len(s)
    f["enseignes"] = enseignes
    return f


def seuils(s: pd.DataFrame, c: pd.DataFrame, enseignes: str) -> list[dict]:
    lignes = [{"enseignes": enseignes, "mesure": "fiches du corpus", "valeur": s["cid"].nunique()},
              {"enseignes": enseignes, "mesure": "nouveaux avis", "valeur": len(s)},
              {"enseignes": enseignes, "mesure": "avis supprimés", "valeur": int(s["supprime"].sum())},
              {"enseignes": enseignes, "mesure": "fiches qui ont perdu au moins un avis", "valeur": len(c)}]
    for part in (25, 50, 75):
        r = c[c["part_suppressions_pct"] >= part - 1e-9].iloc[0]
        lignes.append({"enseignes": enseignes, "mesure": f"fiches portant {part} % des suppressions",
                       "valeur": int(r["n_fiches"]),
                       "part_nouveaux_avis_pct": round(r["part_nouveaux_avis_pct"], 2)})
    return lignes


def graphique(c: pd.DataFrame, s: pd.DataFrame, rep: list[dict]):
    fig, ax = plt.subplots(figsize=(8.5, 4.8), dpi=150)
    fig.patch.set_facecolor(FOND)
    ax.set_facecolor(FOND)
    x = [0] + list(c["n_fiches"])
    ax.plot(x, [0] + list(c["part_suppressions_pct"]), color=BLEU, lw=2, zorder=4)
    ax.plot(x, [0] + list(c["part_nouveaux_avis_pct"]), color=GRIS, lw=2, zorder=3)
    for r in rep:
        if not r["mesure"].startswith("fiches portant") or "75" in r["mesure"]:
            continue
        n = r["valeur"]
        y = c.loc[c["n_fiches"] == n, "part_suppressions_pct"].iloc[0]
        ax.plot([n], [y], "o", ms=6, color=BLEU, mec=FOND, mew=1.5, zorder=5)
        ax.annotate(f"{n} fiches : {virgule(y)} % des suppressions,\n"
                    f"{virgule(r['part_nouveaux_avis_pct'], 1)} % des nouveaux avis",
                    (n, y), xytext=(10, -4), textcoords="offset points", va="top",
                    fontsize=8, color=ENCRE, zorder=6)
    ax.set_xlim(0, len(c) * 1.02)
    ax.set_ylim(0, 105)
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0f} %")
    ax.tick_params(colors=ENCRE_2, labelsize=8, length=0)
    ax.grid(axis="y", color=GRILLE, lw=0.8, zorder=0)
    for cote in ["top", "right", "left"]:
        ax.spines[cote].set_visible(False)
    ax.spines["bottom"].set_color(GRILLE)
    ax.set_xlabel(f"nombre de fiches, les plus touchées d'abord ({len(c)} fiches ont perdu au moins "
                  f"un avis, sur {espace(s['cid'].nunique())})", color=ENCRE_2, fontsize=8)
    ax.set_ylabel("part cumulée", color=ENCRE_2, fontsize=8)

    d = {r["mesure"]: r for r in rep}
    q = d["fiches portant 25 % des suppressions"]
    fig.text(0.01, 0.97, f"{q['valeur']} fiches portent le quart des suppressions, avec "
                         f"{virgule(q['part_nouveaux_avis_pct'], 1)} % des nouveaux avis",
             va="top", fontsize=11, color=ENCRE)
    fig.text(0.01, 0.905, POPULATION, va="top", fontsize=7.5, color=ENCRE_2, linespacing=1.5)
    fig.legend(handles=[Line2D([0], [0], color=BLEU, lw=2, label="part des avis supprimés"),
                        Line2D([0], [0], color=GRIS, lw=2,
                               label="part des nouveaux avis reçus par ces mêmes fiches")],
               loc="upper left", bbox_to_anchor=(0.005, 0.81), ncol=2, frameon=False,
               fontsize=8, labelcolor=ENCRE, handlelength=1.6)
    fig.tight_layout(rect=(0, 0, 1, 0.76))
    fig.savefig(GRAPHIQUE, facecolor=FOND)
    plt.close(fig)


def main():
    df = m.charger()
    courbes, rep = [], []
    for enseignes, s in [("sans", df[~df["enseigne"]]), ("avec", df)]:
        c = courbe(s, enseignes)
        courbes.append(c)
        rep += seuils(s, c, enseignes)
    GRAPHIQUE.parent.mkdir(parents=True, exist_ok=True)
    DONNEES.parent.mkdir(parents=True, exist_ok=True)
    pd.concat(courbes)[["enseignes", "n_fiches", "supprimes", "avis", "part_suppressions_pct",
                        "part_nouveaux_avis_pct"]].round(2).to_csv(DONNEES, index=False)
    pd.DataFrame(rep).to_csv(SEUILS, index=False)
    print(pd.DataFrame(rep).to_string(index=False))
    sans = df[~df["enseigne"]]
    graphique(courbes[0], sans, [r for r in rep if r["enseignes"] == "sans"])
    print(f"écrit : {GRAPHIQUE}\nécrit : {DONNEES}\nécrit : {SEUILS}")


if __name__ == "__main__":
    main()
