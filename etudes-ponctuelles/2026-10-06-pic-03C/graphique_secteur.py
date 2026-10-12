#!/usr/bin/env python3
"""Écart du taux de suppression un jour de pic, par secteur : fiche n° 7 des faits saignants.

    PYTHONPATH=".venv/Lib/site-packages;outils" <python uv> etudes-ponctuelles/2026-10-06-pic-03C/graphique_secteur.py

Demande de Matthieu du 2026-10-06 : refaire le graphique de la fiche n° 7 sur le modèle de
« Écart direct du taux de suppression quand le propriétaire répond, par secteur » (collé
dans 6. faits-saignants.docx), pour remplacer pic_jour.png.

Mêmes avis et mêmes définitions que graphique.py (corpus et définitions de 07F) : avis
4-5 étoiles de 03C publiés du 7 au 17 août, sans les six enseignes, supprimés au plus tard
au 7e jour. Jour de pic : la fiche reçoit ce jour-là au moins 3 avis 4-5 étoiles, et au
moins 4 fois sa moyenne quotidienne de l'année précédente.

Barre : écart des taux comptés directement, rien n'est tenu égal, comme le modèle.
(taux un jour de pic / taux un jour normal - 1). Fourchette à 95 % : 2 000 tirages des
fiches avec remise, dans chaque secteur, parce que les avis d'un même jour de pic viennent
de la même fiche. L'écart à secteur et taille égaux (07F) est rappelé dans le sous-titre.

Sorties :
  livrables/restitution_finale/graphiques/faits-saignants/graphiques/pic_jour_par_secteur.png
  livrables/restitution_finale/graphiques/faits-saignants/donnees/pic_jour_par_secteur.csv
"""
import importlib
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "logistic-regression-study" / "python"))
m = importlib.import_module("07F_regression_03C_prenom")

SORTIE = RACINE / "livrables" / "restitution_finale" / "graphiques" / "faits-saignants"
GRAPHIQUE = SORTIE / "graphiques" / "pic_jour_par_secteur.png"
DONNEES = SORTIE / "donnees" / "pic_jour_par_secteur.csv"

BLEU, BLEU_FONCE = "#2a78d6", "#0e3f7e"
ENCRE, ENCRE_2, GRILLE, FOND = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
SECTEURS = {"automotive": "Automobile", "food_beverage": "Restauration", "healthcare": "Santé",
            "home_services": "Services\nà domicile", "hospitality": "Hôtellerie",
            "travel": "Voyage", "wellness_fitness": "Sport\net bien-être"}
PLAFOND = 400  # haut de l'axe, en % ; au-delà, la fourchette est coupée et sa borne écrite
TIRAGES = 2000
GRAINE = 20261006


def espace(n: float) -> str:
    return f"{n:,.0f}".replace(",", " ")


def virgule(x: float, d: int = 0) -> str:
    return f"{x:.{d}f}".replace(".", ",").replace("-", "−")


def signe(x: float) -> str:
    return f"{'+' if x > 0 else ''}{virgule(x)} %"


def ecart(s: pd.DataFrame, nom: str, rng) -> dict:
    """Écart des taux un jour de pic face à un jour normal, et sa fourchette par tirage des
    fiches avec remise."""
    f = s.groupby("cid").apply(lambda g: pd.Series({
        "n_pic": (g["pic"] == 1).sum(), "s_pic": g.loc[g["pic"] == 1, "supprime"].sum(),
        "n_norm": (g["pic"] == 0).sum(), "s_norm": g.loc[g["pic"] == 0, "supprime"].sum()}),
        include_groups=False).to_numpy(dtype=float)
    tot = f.sum(axis=0)
    rr = (tot[1] / tot[0]) / (tot[3] / tot[2])
    tirages = f[rng.integers(0, len(f), size=(TIRAGES, len(f)))].sum(axis=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        rr_t = (tirages[:, 1] / tirages[:, 0]) / (tirages[:, 3] / tirages[:, 2])
    rr_t = rr_t[np.isfinite(rr_t)]
    bas, haut = np.percentile(rr_t, [2.5, 97.5])
    return {"secteur": nom, "fiches": len(f), "avis": int(tot[0] + tot[2]),
            "avis_jour_de_pic": int(tot[0]), "supprimes_jour_de_pic": int(tot[1]),
            "avis_jour_normal": int(tot[2]), "supprimes_jour_normal": int(tot[3]),
            "pour_1000_jour_de_pic": 1000 * tot[1] / tot[0],
            "pour_1000_jour_normal": 1000 * tot[3] / tot[2],
            "ecart_pct": 100 * (rr - 1), "borne_basse_pct": 100 * (bas - 1),
            "borne_haute_pct": 100 * (haut - 1), "tirages_valides": len(rr_t)}


def graphique(t: pd.DataFrame, ajuste: dict) -> None:
    secteurs = t[t["secteur"] != "tous"].sort_values("ecart_pct")
    tous = t[t["secteur"] == "tous"].iloc[0]
    lignes = list(secteurs.itertuples()) + [tous]
    x = list(range(len(secteurs))) + [len(secteurs) + 0.6]

    fig, ax = plt.subplots(figsize=(10, 5.8), dpi=150)
    fig.patch.set_facecolor(FOND)
    ax.set_facecolor(FOND)
    for xi, r in zip(x, lignes):
        r = r._asdict() if hasattr(r, "_asdict") else r
        couleur = BLEU_FONCE if r["secteur"] == "tous" else BLEU
        ax.bar(xi, r["ecart_pct"], width=0.62, color=couleur, zorder=2)
        # Fourchette plafonnée à l'axe : flèche et borne réelle au-dessus.
        haut = min(r["borne_haute_pct"], PLAFOND)
        coupe = r["borne_haute_pct"] > PLAFOND
        ax.plot([xi, xi], [r["borne_basse_pct"], haut], color=ENCRE, lw=1.2, zorder=3)
        ax.plot([xi - 0.09, xi + 0.09], [r["borne_basse_pct"]] * 2, color=ENCRE, lw=1.2,
                zorder=3)
        if coupe:
            ax.plot([xi], [haut], marker="^", ms=6, color=ENCRE, zorder=3)
        else:
            ax.plot([xi - 0.09, xi + 0.09], [haut] * 2, color=ENCRE, lw=1.2, zorder=3)
        detail = (f"{espace(r['avis'])} avis\n"
                  f"{r['supprimes_jour_de_pic'] + r['supprimes_jour_normal']} supprimés")
        if coupe:
            detail = f"fourchette jusqu'à {signe(r['borne_haute_pct'])}\n" + detail
        if r["ecart_pct"] < 0:
            ax.annotate(signe(r["ecart_pct"]), (xi, r["borne_basse_pct"]), xytext=(0, -4),
                        textcoords="offset points", ha="center", va="top", fontsize=10,
                        fontweight="bold", color=ENCRE)
            ax.annotate(detail, (xi, r["borne_basse_pct"]), xytext=(0, -18),
                        textcoords="offset points", ha="center", va="top", fontsize=7,
                        color=ENCRE_2, linespacing=1.3)
        else:
            ax.annotate(detail, (xi, haut), xytext=(0, 6), textcoords="offset points",
                        ha="center", va="bottom", fontsize=7, color=ENCRE_2, linespacing=1.3)
            lignes_detail = detail.count("\n") + 1
            ax.annotate(signe(r["ecart_pct"]), (xi, haut), xytext=(0, 8 + 10 * lignes_detail),
                        textcoords="offset points", ha="center", va="bottom", fontsize=10,
                        fontweight="bold", color=ENCRE)
    ax.axhline(0, color=ENCRE, lw=0.9, ls=(0, (5, 3)), zorder=1)
    ax.annotate("pas d'effet", ((x[-2] + x[-1]) / 2, 0), xytext=(0, 4),
                textcoords="offset points", ha="center", va="bottom", fontsize=8, color=ENCRE)
    ax.set_xticks(x)
    ax.set_xticklabels([SECTEURS[r.secteur] for r in secteurs.itertuples()] + ["Tous secteurs"],
                       fontsize=9, color=ENCRE)
    ax.set_xlim(-0.6, x[-1] + 0.6)
    hi = min(PLAFOND, t["borne_haute_pct"].max())
    lo = min(0, t["borne_basse_pct"].min())
    ax.set_ylim(lo - 0.22 * (hi - lo), hi + 0.25 * (hi - lo))
    ax.set_yticks([v for v in range(-100, int(hi) + 1, 100)])
    ax.yaxis.set_major_formatter(lambda v, _: signe(v) if v else "0 %")
    ax.tick_params(colors=ENCRE, labelsize=9, length=0)
    ax.grid(axis="y", color=GRILLE, lw=0.8, zorder=0)
    for cote in ["top", "right"]:
        ax.spines[cote].set_visible(False)
    ax.set_ylabel("Écart du taux de suppression, avis publié un jour de pic\nface à un avis "
                  "publié un jour normal", color=ENCRE, fontsize=9)

    n_plus = int((secteurs["ecart_pct"] > 0).sum())
    nets = [SECTEURS[r.secteur].replace("\n", " ").lower() for r in secteurs.itertuples()
            if r.borne_basse_pct > 0 or r.borne_haute_pct < 0]
    fin = ("mais aucun écart n'est net secteur par secteur" if not nets
           else f"mais l'écart n'est net qu'en {nets[0]}" if len(nets) == 1
           else f"net dans {len(nets)} d'entre eux")
    fig.text(0.01, 0.975, f"Un jour de pic, le taux de suppression monte dans {n_plus} secteurs "
             f"sur {len(secteurs)}, {fin}", va="top", fontsize=12, color=ENCRE)
    fig.text(0.01, 0.925,
             f"{espace(tous['avis'])} avis 4-5 étoiles publiés du 7 au 17 août 2026, sans les six "
             f"enseignes, dont {tous['supprimes_jour_de_pic'] + tous['supprimes_jour_normal']} "
             f"supprimés au plus tard au 7e jour. Jour de pic : la fiche reçoit au moins 3 avis\n"
             f"4-5 étoiles et au moins 4 fois sa moyenne quotidienne de l'année précédente "
             f"({espace(tous['avis_jour_de_pic'])} avis). Barre : écart des taux comptés "
             f"directement, rien n'est tenu égal.\n+100 % : l'avis publié un jour de pic disparaît "
             f"deux fois plus. Trait : fourchette à 95 % (fiches tirées au hasard avec remise), "
             f"coupée à {signe(PLAFOND)}.\nTous secteurs, à secteur et taille égaux (régression) : "
             f"×{virgule(ajuste['rc'], 2)}, soit {signe(100 * (ajuste['rc'] - 1))} "
             f"[{signe(100 * (ajuste['bas'] - 1))} ; {signe(100 * (ajuste['haut'] - 1))}].",
             va="top", fontsize=8, color="#7a7974", linespacing=1.55)
    fig.tight_layout(rect=(0, 0, 1, 0.80))
    fig.savefig(GRAPHIQUE, facecolor=FOND)
    plt.close(fig)


def main():
    df = m.charger()
    rep = m.variable_reponse(df)
    s = df[~df["enseigne"]].copy()
    rng = np.random.default_rng(GRAINE)
    t = pd.DataFrame([ecart(g, secteur, rng) for secteur, g in s.groupby("industry")]
                     + [ecart(s, "tous", rng)])
    variables = ["prenom", "photo", rep, "pic"]
    r = m.tableau(m.ajuster(s, variables, secteur_taille=True), "sans enseignes", variables)
    r = r[r["variable"] == "pic"].iloc[0]
    ajuste = {"rc": r["rapport_de_cotes"], "bas": r["borne_basse"], "haut": r["borne_haute"]}
    GRAPHIQUE.parent.mkdir(parents=True, exist_ok=True)
    t.round(2).to_csv(DONNEES, index=False)
    print(t.round(1).to_string(index=False))
    print(f"à secteur et taille égaux : ×{ajuste['rc']:.2f} [{ajuste['bas']:.2f} ; {ajuste['haut']:.2f}]")
    graphique(t, ajuste)
    print(f"écrit : {GRAPHIQUE}\nécrit : {DONNEES}")


if __name__ == "__main__":
    main()
