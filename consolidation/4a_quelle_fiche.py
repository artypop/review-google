"""4a. Quelle fiche se fait toucher ? Une ligne par fiche, panel 03B.

    uv run python consolidation/4a_quelle_fiche.py

LA QUESTION
  Parmi les fiches qui ont reçu au moins 5 avis du 4 au 17 août, qu'est-ce qui
  distingue celles qui en perdent au moins un ? Chaque fiche compte une fois,
  qu'elle perde 1 avis ou 30. Les fiches purgées en masse ne pèsent donc pas
  plus que les autres.

LES COLONNES
  secteur (référence : automobile), taille (référence : mono),
  région (référence : Europe, passage « ensemble » seulement),
  habitude de réponse (référence : 75 % ou moins),
  afflux : avis reçus du 4 au 17 août, comparés à ce que la fiche reçoit
  d'habitude en 14 jours (référence : pas plus que d'habitude).
  Contrôle, qui ne se cite pas : le nombre d'avis de la fiche dans le panel.
  Les fiches sans historique l'année précédente sortent : 7 fiches, aucune
  touchée (mesuré le 2026-09-29).
  Une fiche qui reçoit 40 avis a plus de chances d'en perdre un qu'une fiche
  qui en reçoit 5, quoi qu'il arrive.

LA RÈGLE DE CITATION (voir `commun.py`)
  Ici une case est un groupe de fiches (par exemple « services à domicile »).
  Elle est citable si ses fiches perdent au moins 10 avis, sur au moins
  5 fiches, sans qu'une fiche en porte plus du quart. La case de référence
  doit l'être aussi.

Produit :
  sorties/4a_effectifs.csv        fiches, fiches touchées, suppressions par case
  sorties/4a_effets.csv           risque relatif, fourchette, citable, par passage
  sorties/4a_fiches_touchees.csv  les fiches touchées : cid, enseigne, dates
  sorties/figures/4a_effets.png
"""
import numpy as np
import pandas as pd
import statsmodels.api as sm
from matplotlib.ticker import FuncFormatter, NullFormatter

from commun import (COULEURS, MIN_FICHES_CITABLE, MIN_SUPPRESSIONS_CITABLE,
                    PART_MAX_PREMIERE_FICHE, ecrire_csv, enregistrer, figure, requete)

SECTEURS = {"automotive": "Automobile", "home_services": "Services à domicile",
            "healthcare": "Santé", "wellness_fitness": "Sport et bien-être",
            "food_beverage": "Restauration", "travel": "Voyage", "hospitality": "Hôtellerie"}

fiches = requete("4a_fiches")
# Les fiches sans historique (moins de 10 avis l'année précédente, ou aucun
# avis) n'ont ni habitude de réponse ni rythme habituel. Elles sont trop peu
# nombreuses pour former une case : elles sortent, et leur nombre est imprimé.
sans_historique = fiches["taux_reponse"].isna() | fiches["rythme"].isna()
print(f"  fiches sans historique, retirées : {int(sans_historique.sum())}, "
      f"dont touchées : {int((sans_historique & (fiches['suppressions'] > 0)).sum())}")
fiches = fiches[~sans_historique].copy()
fiches["touchee"] = (fiches["suppressions"] > 0).astype(int)
fiches["secteur"] = fiches["secteur"].map(SECTEURS)
fiches["habitude"] = np.where(fiches["taux_reponse"] > 0.75, "plus de 75 %", "75 % ou moins")
# Afflux : avis reçus en 14 jours comparés à 14 jours de rythme habituel.
attendu = 14 * fiches["rythme"]
ratio = fiches["avis"] / attendu
fiches["afflux"] = np.select(
    [ratio <= 1, ratio <= 2],
    ["pas plus que d'habitude", "1 à 2 fois l'habitude"], "plus de 2 fois l'habitude")

ecrire_csv(fiches[fiches["touchee"] == 1]
           .sort_values(["suppressions", "cid"], ascending=[False, True])
           .drop(columns=["touchee", "taux_reponse", "rythme"]), "4a_fiches_touchees")

# Chaque caractéristique : (colonne, référence, modalités dans l'ordre d'affichage).
CARACTERISTIQUES = {
    "secteur": ("Automobile", list(SECTEURS.values())),
    "taille": ("mono", ["mono", "small", "large"]),
    "region": ("Europe", ["Europe", "US"]),
    "habitude": ("75 % ou moins", ["75 % ou moins", "plus de 75 %"]),
    "afflux": ("pas plus que d'habitude", ["pas plus que d'habitude", "1 à 2 fois l'habitude",
                                           "plus de 2 fois l'habitude"]),
}


def effectifs_case(d):
    touchees = d[d["touchee"] == 1]
    n = int(touchees["suppressions"].sum())
    part = float(touchees["suppressions"].max() / n) if n else None
    return {"fiches": len(d), "fiches_touchees": len(touchees), "suppressions": n,
            "enseignes_touchees": touchees["enseigne"].nunique(),
            "part_de_la_premiere_fiche": round(part, 2) if part is not None else None,
            "case_citable": bool(n >= MIN_SUPPRESSIONS_CITABLE and len(touchees) >= MIN_FICHES_CITABLE
                                 and part is not None and part <= PART_MAX_PREMIERE_FICHE)}


PASSAGES = [(region, perimetre) for region in ["ensemble", "US", "Europe"]
            for perimetre in ["tous", "sans_enseignes"]]
lignes_effectifs, lignes_effets = [], []

for region, perimetre in PASSAGES:
    passage = f"{region}, {perimetre}"
    d = fiches if region == "ensemble" else fiches[fiches["region"] == region]
    if perimetre == "sans_enseignes":
        d = d[~d["enseigne_signalee"]]

    X = pd.DataFrame(index=d.index)
    cases = {}
    for car, (reference, modalites) in CARACTERISTIQUES.items():
        if car == "region" and region != "ensemble":
            continue
        for m in modalites:
            e = effectifs_case(d[d[car] == m])
            cases[(car, m)] = e
            lignes_effectifs.append({"passage": passage, "caracteristique": car, "modalite": m,
                                     "reference": m == reference, **e})
            if m != reference and e["fiches"] > 0:
                X[f"{car} : {m}"] = (d[car] == m).astype(float)
    X["contrôle : nombre d'avis de la fiche (log)"] = np.log(d["avis"])
    X = sm.add_constant(X)
    modele = sm.GLM(d["touchee"], X, family=sm.families.Binomial()).fit()
    marges = modele.conf_int()
    print(f"  {passage} : {len(d)} fiches, {int(d['touchee'].sum())} touchées")

    for col in X.columns.drop("const"):
        ligne = {"passage": passage, "colonne": col,
                 "risque_relatif": round(float(np.exp(modele.params[col])), 2),
                 "fourchette_basse": round(float(np.exp(marges.loc[col, 0])), 2),
                 "fourchette_haute": round(float(np.exp(marges.loc[col, 1])), 2)}
        if col.startswith("contrôle"):
            ligne["citable"] = "contrôle, ne se cite pas"
        else:
            car, m = col.split(" : ", 1)
            e, ref = cases[(car, m)], cases[(car, CARACTERISTIQUES[car][0])]
            ligne.update({k: e[k] for k in ["fiches", "fiches_touchees", "suppressions",
                                            "enseignes_touchees", "part_de_la_premiere_fiche"]})
            ligne["citable"] = "oui" if e["case_citable"] and ref["case_citable"] else "non"
        lignes_effets.append(ligne)

ecrire_csv(pd.DataFrame(lignes_effectifs), "4a_effectifs")
effets = pd.DataFrame(lignes_effets)
for col in ["fiches", "fiches_touchees", "suppressions", "enseignes_touchees"]:
    effets[col] = effets[col].astype("Int64")
ecrire_csv(effets, "4a_effets")

fig, axes = figure(3, 2, largeur=12, hauteur=13)
for ax, (region, perimetre) in zip(axes.flat, PASSAGES):
    e = effets[(effets["passage"] == f"{region}, {perimetre}")
               & ~effets["colonne"].str.startswith("contrôle")].reset_index(drop=True)
    y = np.arange(len(e))
    couleurs = [COULEURS["ensemble"] if c == "oui" else "#b0afa9" for c in e["citable"]]
    ax.errorbar(e["risque_relatif"], y, xerr=[e["risque_relatif"] - e["fourchette_basse"],
                                              e["fourchette_haute"] - e["risque_relatif"]],
                fmt="none", ecolor="#999999", elinewidth=1.5)
    ax.scatter(e["risque_relatif"], y, color=couleurs, s=40, zorder=3)
    ax.axvline(1, color="#52514e", linewidth=1)
    ax.set_xscale("log")
    ax.set_xticks([0.1, 0.2, 0.5, 1, 2, 5, 10])
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"×{v:g}".replace(".", ",")))
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.set_xlim(0.05, 20)
    ax.set_yticks(y, e["colonne"])
    ax.invert_yaxis()
    ax.set_title(f"{region}, {perimetre}")
fig.suptitle("Chance qu'une fiche perde au moins un avis — vert : citable, gris : non citable")
enregistrer(fig, "4a_effets")
