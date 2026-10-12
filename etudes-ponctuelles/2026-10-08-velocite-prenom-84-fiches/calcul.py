#!/usr/bin/env python3
"""Le graphique « vitesse de collecte et part de prénoms » du 2026-10-06, refait sur les
seules 84 fiches (1 %) qui ont perdu le plus d'avis du 11 au 24 août.

    PYTHONPATH=".venv/Lib/site-packages;outils" <python uv> etudes-ponctuelles/2026-10-08-velocite-prenom-84-fiches/calcul.py

Demande de Matthieu du 2026-10-08. Données, fiches retenues et modèles repris tels quels de
`2026-10-06-velocite-prenom/calcul.py` (rien n'y est réécrit) :

  les 84 fiches  le 1 % de fiches qui ont le plus de suppressions du 11 au 24 août parmi
                 les avis de tous âges de l'étape 3, même tri que le 2026-10-06 ; le
                 script vérifie qu'il retrouve 84 fiches et 1 043 suppressions.
  1 à 3          M1, M2, M3 du 2026-10-06, sur les avis de tous âges de ces fiches.
  4              M4 du 2026-10-06 (avis neufs de 03C, jour par jour), sur ces fiches.

La barre « sans les fiches les plus touchées » du graphique d'origine n'a pas d'équivalent
ici et disparaît.

Ces fiches sont choisies sur le nombre d'avis qu'elles ont perdu, c'est-à-dire sur ce que
les modèles cherchent à expliquer : les écarts entre elles ne se lisent pas comme ceux de
l'ensemble des fiches.

Sorties : livrables/restitution_finale/graphiques/faits-saignants/
  graphiques/velocite_prenom_modeles_84_fiches.png
  donnees/velocite_prenom_modeles_84_fiches.csv, velocite_prenom_fiches_84_fiches.csv
"""
import importlib.util
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

RACINE = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location(
    "v06", RACINE / "etudes-ponctuelles" / "2026-10-06-velocite-prenom" / "calcul.py")
v06 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(v06)
from local import connexion  # noqa: E402  (chemin posé par le script du 2026-10-06)

sys.stdout.reconfigure(encoding="utf-8")
SORTIE = v06.SORTIE
GRAPHIQUE = SORTIE / "graphiques" / "velocite_prenom_modeles_84_fiches.png"
MODELES = SORTIE / "donnees" / "velocite_prenom_modeles_84_fiches.csv"
CLASSES = SORTIE / "donnees" / "velocite_prenom_fiches_84_fiches.csv"
ATTENDU = (84, 1043)  # fiches et suppressions retirées dans le calcul du 2026-10-06

M1, M2, M3, M4 = ("M1 secteur, taille, région égaux", "M2 + vitesse égale",
                  "M3 + âge des avis égal", "M4 avis neufs (03C)")
PANNEAUX = [
    ("p_50_100", "Fiche dont 50 % et plus des avis citent un prénom,\nface à moins de 10 %",
     [(M1, "1. brut"), (M2, "2. à vitesse\négale"), (M3, "3. à vitesse et\nâge égaux"),
      (M4, "4. avis neufs,\nmême âge")]),
    ("log2_vitesse", "Vitesse de collecte de la fiche multipliée par 2",
     [(M2, "2. à part de\nprénoms égale"), (M3, "3. + âge\négal"),
      (M4, "4. avis neufs,\nmême âge")])]
BLEU, GRIS = v06.BLEU, v06.GRIS
ENCRE, ENCRE_2, GRILLE, FOND = v06.ENCRE, v06.ENCRE_2, v06.GRILLE, v06.FOND
virgule, espace = v06.virgule, v06.espace


def graphique(m: pd.DataFrame, titre: str, sous_titre: str) -> None:
    """La figure des modèles du 2026-10-06, sans sa barre 4."""
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.8), dpi=150,
                             gridspec_kw={"width_ratios": [4, 3]}, sharey=True)
    fig.patch.set_facecolor(FOND)
    toutes = m[m["variable"].isin(["p_50_100", "log2_vitesse"])]
    hi = 100 * (toutes["borne_haute"].max() - 1)
    lo = min(-30, 100 * (toutes["borne_basse"].min() - 1))
    for ax, (variable, titre_p, modeles) in zip(axes, PANNEAUX):
        ax.set_facecolor(FOND)
        for i, (mod, _) in enumerate(modeles):
            r = m[(m["modele"] == mod) & (m["variable"] == variable)].iloc[0]
            e, b, h = (100 * (r[c] - 1) for c in ("rapport_de_cotes", "borne_basse", "borne_haute"))
            net = r["p_value"] < 0.05
            ax.bar(i, e, width=0.6, color=BLEU if net else GRIS, zorder=2)
            ax.plot([i, i], [b, h], color=ENCRE, lw=1.2, zorder=3)
            for v in (b, h):
                ax.plot([i - 0.06, i + 0.06], [v, v], color=ENCRE, lw=1.2, zorder=3)
            etiquette = "0 %" if round(e) == 0 else f"{'+' if e > 0 else ''}{virgule(e)} %"
            ax.annotate(etiquette, (i, h if e >= 0 else b),
                        xytext=(0, 4 if e >= 0 else -4), textcoords="offset points",
                        ha="center", va="bottom" if e >= 0 else "top", fontsize=9,
                        fontweight="bold" if net else "normal", color=ENCRE)
        ax.axhline(0, color=ENCRE_2, lw=0.9, ls=(0, (4, 3)), zorder=1)
        ax.set_xticks(range(len(modeles)))
        ax.set_xticklabels([nom for _, nom in modeles], fontsize=7.5, color=ENCRE)
        ax.set_title(titre_p, fontsize=9, color=ENCRE, loc="left")
        ax.tick_params(colors=ENCRE_2, labelsize=8, length=0)
        ax.grid(axis="y", color=GRILLE, lw=0.8, zorder=0)
        for cote in ["top", "right", "left"]:
            ax.spines[cote].set_visible(False)
        ax.spines["bottom"].set_color(GRILLE)
        ax.set_xlim(-0.6, len(modeles) - 0.4)
    axes[0].set_ylim(lo - 0.12 * (hi - lo), hi + 0.15 * (hi - lo))
    axes[0].yaxis.set_major_formatter(lambda v, _: f"{'+' if v > 0 else ''}{v:.0f} %".replace("-", "−"))
    axes[0].set_ylabel("écart du risque de suppression", color=ENCRE_2, fontsize=8)
    fig.text(0.01, 0.975, titre, va="top", fontsize=11, color=ENCRE)
    fig.text(0.01, 0.915, sous_titre, va="top", fontsize=7.5, color=ENCRE_2, linespacing=1.5)
    fig.tight_layout(rect=(0, 0, 1, 0.74), w_pad=2)
    fig.savefig(GRAPHIQUE, facecolor=FOND)
    plt.close(fig)


def main():
    con = connexion("6GB")
    fi = v06.fiches(con)
    a = v06.avis_tous_ages(con).merge(fi, on="cid", how="left")
    a = a[a["classe_prenom"].isin(v06.CLASSES_PRENOM)].copy()
    a["classe_age"] = v06.classe_age(a["age_j"])

    # Les 84 fiches, triées comme le 2026-10-06.
    par_fiche = a.groupby("cid")["supprime"].sum().sort_values(ascending=False)
    top = par_fiche.head(int(np.ceil(0.01 * len(par_fiche)))).index
    trouve = (len(top), int(par_fiche.loc[top].sum()))
    if trouve != ATTENDU:
        raise SystemExit(f"fiches les plus touchées : {trouve}, attendu {ATTENDU}")
    a = a[a["cid"].isin(top)].copy()
    ft = fi[fi["cid"].isin(top)]
    print(f"84 fiches : {len(a)} avis de tous âges, {int(a['supprime'].sum())} suppressions")
    for col in ["industry", "bucket", "region"]:
        print(f"\n{ft[col].value_counts().to_string()}")

    # Les classes de part de prénoms parmi ces fiches.
    e1 = a.groupby("classe_prenom").agg(fiches=("cid", "nunique"), avis=("supprime", "size"),
                                         supprimes=("supprime", "sum")).reindex(v06.CLASSES_PRENOM)
    e1["pour_100000"] = 1e5 * e1["supprimes"] / e1["avis"]
    e1["vitesse_mediane"] = ft.groupby("classe_prenom")["avis_par_mois"].median()
    e1["part_avis_moins_90j"] = a.groupby("classe_prenom")["classe_age"].apply(
        lambda s: s.isin(["publié pendant le suivi", "0-30 j", "31-90 j"]).mean())
    print("\n== Classes ==\n" + e1.round(3).to_string())

    # Modèles 1 à 3, avis de tous âges.
    g = (a.groupby(["cid", "classe_age"])
         .agg(avis=("supprime", "size"), supprimes=("supprime", "sum")).reset_index()
         .merge(fi[["cid", "industry", "bucket", "region", "classe_prenom", "log2_vitesse"]],
                on="cid"))
    for code_classe, code in v06.CODES_PRENOM.items():
        g[code] = (g["classe_prenom"] == code_classe).astype(int)
    for col, ref in [("industry", "automotive"), ("bucket", "mono")]:
        if ref not in set(g[col]):
            raise SystemExit(f"aucune des 84 fiches n'a la référence {col} = {ref}")
    lignes = []
    for nom, vit, age in [(M1, False, False), (M2, True, False), (M3, True, True)]:
        lignes += v06.lire(v06.modele_tous_ages(g, vit, age),
                           list(v06.CODES_PRENOM.values()) + ["log2_vitesse"], nom)

    # Modèle 4, avis neufs de ces fiches : on écarte toutes les autres.
    l4, info4 = v06.modele_avis_neufs(fi, exclues=set(fi["cid"]) - set(top), nom=M4)
    lignes += l4
    m = pd.DataFrame(lignes)
    m["ecart_pct"] = 100 * (m["rapport_de_cotes"] - 1)
    print(f"\n== Modèles == (03C : {info4})\n" + m.round(3).to_string(index=False))

    MODELES.parent.mkdir(parents=True, exist_ok=True)
    m.to_csv(MODELES, index=False)
    e1.reset_index().to_csv(CLASSES, index=False)

    n_ref = int(e1.loc["moins de 10 %", "fiches"])
    graphique(
        m, titre(m),
        f"Mêmes calculs que le graphique précédent, sur les 84 fiches (1 %) qui ont perdu le plus "
        f"d'avis du 11 au 24 août 2026, sans les six enseignes.\n1 à 3 : leurs {espace(len(a))} "
        f"avis 4-5 étoiles avec texte, tous âges ({espace(a['supprime'].sum())} supprimés). "
        f"4 : leurs {espace(info4['avis'])} avis 4-5 étoiles de 03C publiés du 7 au 17 août "
        f"({info4['suppressions']} supprimés), tous du même âge.\nFiches choisies sur le nombre "
        f"d'avis perdus ; {n_ref} seulement citent un prénom dans moins de 10 % de leurs avis. "
        f"Trait : fourchette à 95 %.\nBarre grise : écart trop incertain pour être affirmé.")
    print("écrit :", GRAPHIQUE)
    print("écrit :", MODELES)
    print("écrit :", CLASSES)


def titre(m: pd.DataFrame) -> str:
    p = m[m["variable"] == "p_50_100"]
    if ((p["p_value"] < 0.05) & (p["rapport_de_cotes"] > 1)).any():
        return "Parmi les 84 fiches les plus touchées : part de prénoms, vitesse de collecte et suppressions"
    return ("Parmi les 84 fiches les plus touchées, citer beaucoup de prénoms ne fait pas "
            "perdre plus d'avis")


if __name__ == "__main__":
    main()
