#!/usr/bin/env python3
"""Suppressions de chaque jour du relevé sur 03C, comparées à l'attendu (fiche n° 11).

    PYTHONPATH=".venv/Lib/site-packages;outils" <python uv> etudes-ponctuelles/2026-10-06-balai-03C/graphique.py

Demande de Matthieu du 2026-10-06 : refaire `phenomenes_disparitions_par_jour.png` (toute
la base, avis de tous âges) sur 03C.

  corpus      avis 4-5 étoiles de 03C publiés du 7 au 17 août, filtres de 07F importés
              tels quels (prénom connu, fiche relevée jusqu'au 24 août) : 24 191 avis.
  suppressions TOUTES celles constatées du 12 au 24 août (903, comme 07G), sans la
              coupure au 7e jour des autres fiches : un avis épargné à son 7e jour puis
              retiré au 9e doit compter le jour où il disparaît.
  jour        passage du robot qui constate la disparition. Les 14 passages sont
              complets (9 045 à 9 048 fiches, table `waves`). Le passage du 12 août finit
              le 13 à 05:00 UTC : une partie de ses constats est datée du 13.
  attendu     03C ne contient que des avis de quelques jours, et le risque dépend
              surtout de l'âge (pic aux 6e et 7e jours). Le nombre brut de chaque jour
              suit donc le nombre d'avis qui atteignent cet âge ce jour-là. L'attendu
              d'un jour = somme, sur les avis encore en ligne la veille, du risque moyen
              des avis de leur âge sur tout le suivi, calculé à part pour les chaînes et
              pour les autres fiches. Le jour étudié entre dans ce risque moyen : l'écart
              d'un jour exceptionnel est donc plutôt sous-estimé.
  fiches      les quatre chaînes antiparasitaires à part. Les deux salles espagnoles n'ont
              aucun avis dans 03C : les six enseignes se réduisent aux quatre chaînes.

Sorties :
  livrables/restitution_finale/graphiques/faits-saignants/graphiques/suppressions_par_jour_03C.png
  livrables/restitution_finale/graphiques/faits-saignants/donnees/suppressions_par_jour_03C.csv
"""
import importlib
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "logistic-regression-study" / "python"))
m = importlib.import_module("07F_regression_03C_prenom")

SORTIE = RACINE / "livrables" / "restitution_finale" / "graphiques" / "faits-saignants"
GRAPHIQUE = SORTIE / "graphiques" / "suppressions_par_jour_03C.png"
DONNEES = SORTIE / "donnees" / "suppressions_par_jour_03C.csv"
JOURS = pd.date_range("2026-08-12", "2026-08-24")

# Palette des graphiques de la restitution (2026-10-05-phenomenes-par-jour).
BLEU, GRIS = "#2a78d6", "#c3c2b7"
ENCRE, ENCRE_2, GRILLE, FOND = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
POPULATION = ("Avis 4-5 étoiles publiés du 7 au 17 août 2026 : 24 191 avis, dont 903 supprimés du 12 au "
              "24 août, entre 1 et 17 jours après leur publication.\nAttendu : si chaque avis en ligne "
              "avait, ce jour-là, le risque moyen des avis de son âge sur tout le suivi.")


def calculer() -> pd.DataFrame:
    df = m.charger()
    cree = pd.to_datetime(df["created_at"])
    vu = pd.to_datetime(df["first_seen_at"])
    supprime = pd.to_datetime(df["deleted_detected_at"])
    if supprime.notna().sum() != ((supprime >= JOURS[0]) & (supprime <= JOURS[-1])).sum():
        raise SystemExit("Une suppression tombe hors du 12-24 août.")

    lignes = []
    for jour in JOURS:
        age = (jour - cree).dt.days
        en_ligne = (vu <= jour - pd.Timedelta(days=1)) & (supprime.isna() | (supprime >= jour))
        t = pd.DataFrame({"chaine": df["enseigne"], "age": age, "en_ligne": en_ligne,
                          "supprime": en_ligne & (supprime == jour)})[en_ligne]
        g = t.groupby(["chaine", "age"]).agg(en_ligne=("en_ligne", "size"),
                                             supprimes=("supprime", "sum")).reset_index()
        g["jour"] = jour
        lignes.append(g)
    t = pd.concat(lignes)
    risque = t.groupby(["chaine", "age"])[["en_ligne", "supprimes"]].sum()
    t = t.join((risque["supprimes"] / risque["en_ligne"]).rename("risque"), on=["chaine", "age"])
    t["attendu"] = t["en_ligne"] * t["risque"]

    j = t.pivot_table(index="jour", columns="chaine", values=["supprimes", "attendu", "en_ligne"],
                      aggfunc="sum")
    out = pd.DataFrame({
        "jour": j.index.strftime("%Y-%m-%d"),
        "chaines": j[("supprimes", True)].astype(int).values,
        "autres": j[("supprimes", False)].astype(int).values,
        "attendu_chaines": j[("attendu", True)].values,
        "attendu_autres": j[("attendu", False)].values,
        "avis_en_ligne_la_veille": (j[("en_ligne", True)] + j[("en_ligne", False)]).astype(int).values,
    })
    out["total"] = out["chaines"] + out["autres"]
    out["attendu_total"] = out["attendu_chaines"] + out["attendu_autres"]
    if out["total"].sum() != supprime.notna().sum():
        raise SystemExit("Le total par jour ne retombe pas sur le nombre de suppressions.")

    seize = pd.Timestamp("2026-08-16")
    ages = (seize - cree[supprime == seize]).dt.days.value_counts().sort_index()
    p = out[out["jour"].between("2026-08-14", "2026-08-16")]
    print(f"16 août, âge des avis supprimés : {ages.to_dict()} ; 8e jour ou plus : {int(ages[ages.index >= 8].sum())}")
    print(f"14-16 août : {p['total'].sum()} supprimés pour {p['attendu_total'].sum():.0f} attendus")
    return out


def graphique(d: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(8.5, 4.8), dpi=150)
    fig.patch.set_facecolor(FOND)
    ax.set_facecolor(FOND)
    x = range(len(d))
    ax.bar(x, d["autres"], width=0.72, color=GRIS, zorder=3, edgecolor=FOND, linewidth=1)
    ax.bar(x, d["chaines"], width=0.72, bottom=d["autres"], color=BLEU, zorder=3,
           edgecolor=FOND, linewidth=1)
    ax.hlines(d["attendu_total"], [i - 0.36 for i in x], [i + 0.36 for i in x], color=ENCRE,
              lw=2, zorder=4)
    seize = d.index[d["jour"] == "2026-08-16"][0]
    for i, r in d.iterrows():
        # Au-dessus du trait de l'attendu seulement s'il touche le haut de la barre.
        proche = 0 <= r["attendu_total"] - r["total"] <= 8
        haut = r["attendu_total"] if proche else r["total"]
        ax.annotate(f"{r['total']}", (i, haut), xytext=(0, 4), textcoords="offset points",
                    ha="center", fontsize=8, color=ENCRE, zorder=5,
                    fontweight="bold" if i == seize else "normal")
    ax.set_xticks(list(x))
    ax.set_xticklabels([j[-2:] for j in d["jour"]])
    ax.tick_params(colors=ENCRE_2, labelsize=8, length=0)
    ax.set_ylim(0, max(d["total"].max(), d["attendu_total"].max()) * 1.15)
    ax.grid(axis="y", color=GRILLE, lw=0.8, zorder=0)
    for cote in ["top", "right", "left"]:
        ax.spines[cote].set_visible(False)
    ax.spines["bottom"].set_color(GRILLE)
    ax.set_xlabel("jour d'août où le robot constate la suppression", color=ENCRE_2, fontsize=8)
    ax.set_ylabel("nouveaux avis 4-5 étoiles supprimés", color=ENCRE_2, fontsize=8)

    s = d.loc[seize]
    creux = d[d["jour"].isin(["2026-08-14", "2026-08-15"])]
    fig.text(0.01, 0.97, f"16 août : {s['total']} nouveaux avis supprimés pour {s['attendu_total']:.0f} "
                         f"attendus, après deux jours presque vides", va="top", fontsize=11, color=ENCRE)
    fig.text(0.01, 0.905, POPULATION, va="top", fontsize=7.5, color=ENCRE_2, linespacing=1.5)
    fig.legend(handles=[Patch(color=BLEU, label="4 chaînes antiparasitaires"),
                        Patch(color=GRIS, label="autres fiches"),
                        Line2D([0], [0], color=ENCRE, lw=2,
                               label=f"attendu d'après l'âge des avis (14 et 15 août : "
                                     f"{creux['total'].sum()} supprimés pour "
                                     f"{creux['attendu_total'].sum():.0f} attendus)")],
               loc="upper left", bbox_to_anchor=(0.005, 0.81), ncol=3, frameon=False,
               fontsize=8, labelcolor=ENCRE, handlelength=1.6)
    fig.tight_layout(rect=(0, 0, 1, 0.76))
    fig.savefig(GRAPHIQUE, facecolor=FOND)
    plt.close(fig)


def main():
    d = calculer()
    GRAPHIQUE.parent.mkdir(parents=True, exist_ok=True)
    DONNEES.parent.mkdir(parents=True, exist_ok=True)
    d.round(1).to_csv(DONNEES, index=False)
    print(d.round(1).to_string(index=False))
    graphique(d)
    print(f"écrit : {GRAPHIQUE}\nécrit : {DONNEES}")


if __name__ == "__main__":
    main()
