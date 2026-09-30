"""8. La réponse du propriétaire sur toute la base, à caractéristiques égales.

    nice -n 19 uv run python consolidation/8_regression_reponse_base.py

LA QUESTION
  À note, profil d'auteur, secteur, taille, région et âge égaux, un avis déjà
  répondu le 11 août disparaît-il moins, du 12 au 24 août, qu'un avis sans
  réponse ?

LA POPULATION
  Les avis publiés avant le 4 août 2026, sur les fiches dont l'habitude de
  réponse est connue. Le panel 03B (4 au 17 août) les laisse de côté : le
  point 5 et celui-ci ne partagent aucun avis. Le point 7 compte les mêmes
  avis, sans tenir les autres caractéristiques égales.

LES COLONNES
  - réponse avant le 11 août : une colonne par âge de l'avis (8 à 30 jours,
    31 à 90, 91 à 365, plus d'un an) et par habitude de la fiche (75 % ou
    moins, plus de 75 %). Chacune se compare aux avis sans réponse de même âge,
    sur des fiches de même habitude ;
  - contrôles, qui ne se citent pas : l'âge et l'habitude eux-mêmes ; la note,
    le niveau Local Guide, la photo jointe, la longueur du texte, les photos et
    les avis de l'auteur (paliers du 4b) ; le secteur, la taille, la région.

LECTURE ET CITATION
  « ×0,50 » : toutes les autres colonnes égales, l'avis répondu disparaît deux
  fois moins que l'avis sans réponse. La fourchette tient compte de ce que les
  avis d'une même fiche se ressemblent. Un effet se cite selon la règle de
  `commun.py` : 10 suppressions, 5 fiches, aucune fiche au-delà du quart, pour
  les avis répondus et pour les avis sans réponse.

GARDE-FOU
  Une case avec moins de 5 suppressions ne permet aucune estimation. Ses avis
  sortent du passage, et `8_effets.csv` le dit. Pour la réponse, la case est
  l'âge × l'habitude : elle sort si les répondus ou les sans réponse sont sous
  le seuil.

LE CALCUL
  BigQuery regroupe les avis par fiche et par combinaison de caractéristiques
  (`sql/8_avis_regroupes.sql`, moins d'un million de lignes pour 4,6 millions
  d'avis). Le modèle est d'abord calculé sur les combinaisons seules, toutes
  fiches réunies (100 000 lignes), puis repris par fiche à partir de ce
  résultat : les effets sont les mêmes, et la fourchette a besoin des fiches.

Produit :
  sorties/8_effectifs.csv        avis et suppressions par case, avant le modèle
  sorties/8_effets.csv           risque relatif, fourchette, citable, par passage
  sorties/8_fiches_par_case.csv  les fiches derrière les suppressions de chaque case
  sorties/8_notes_par_case.csv   la note des avis répondus et sans réponse, case par case
  sorties/figures/8_effets.png
"""
import gc

import numpy as np
import pandas as pd
import statsmodels.api as sm
from matplotlib.ticker import FuncFormatter, NullFormatter

from commun import (COULEURS, MIN_FICHES_CITABLE, MIN_SUPPRESSIONS_CITABLE, PART_MAX_PREMIERE_FICHE,
                    ecrire_csv, enregistrer, figure, habitude, noms_habitudes, requete)

AGES = ["8 à 30 jours", "31 à 90 jours", "91 à 365 jours", "plus d'un an"]
# Les tranches d'habitude de `commun.py` : « 75 % ou moins », « plus de 75 % ».
HABITUDES = noms_habitudes()
MIN_SUPPRESSIONS = 5

# Les contrôles : (référence, modalités dans l'ordre d'affichage).
CONTROLES = {
    "note": ("5 étoile(s)", ["1 étoile(s)", "2 étoile(s)", "3 étoile(s)", "4 étoile(s)", "5 étoile(s)"]),
    "local_guide": ("niveau 1 à 4", ["sans niveau", "niveau 1 à 4", "niveau 5 et plus"]),
    "photo_jointe": ("sans photo", ["sans photo", "avec photo"]),
    "texte": ("sans texte", ["sans texte", "1 à 50 caractères", "51 à 200 caractères", "plus de 200 caractères"]),
    "photos_auteur": ("0 photo", ["0 photo", "1 à 20 photos", "plus de 20 photos"]),
    "avis_auteur": ("1 avis ou moins", ["1 avis ou moins", "2 à 20 avis", "plus de 20 avis"]),
    "secteur": ("Automobile", ["Automobile", "Services à domicile", "Santé", "Sport et bien-être",
                               "Restauration", "Voyage", "Hôtellerie"]),
    "taille": ("mono", ["mono", "small", "large"]),
    "region": ("Europe", ["Europe", "US"]),
}
CASES = [f"{a}, fiche qui répond à {h}" for h in HABITUDES for a in AGES]
MOTIF = ["case", "repondu"] + list(CONTROLES)

d0 = requete("8_avis_regroupes")
for col in ["n", "k"]:
    d0[col] = d0[col].astype(int)
for col in ["repondu", "enseigne_signalee"]:
    d0[col] = d0[col].astype(bool)
d0["reponse"] = np.where(d0["repondu"], "répondu avant le 11 août", "sans réponse")
d0["habitude"] = habitude(d0["taux_reponse"])
d0["case"] = d0["age"] + ", fiche qui répond à " + d0["habitude"]
# Un million de lignes de texte pèsent lourd : chaque colonne devient une liste
# de modalités, et la ligne n'en garde que le numéro.
for col in ["cid", "region", "reponse", "case", "age", "habitude"] + [c for c in CONTROLES if c != "region"]:
    d0[col] = d0[col].astype("category")
print(f"  {len(d0)} lignes, {int(d0['n'].sum())} avis, {int(d0['k'].sum())} suppressions, "
      f"{d0['cid'].nunique()} fiches")


def effectifs(d):
    """Les effectifs d'une case, à partir des lignes regroupées (n avis, k suppressions)."""
    touchees = d[d["k"] > 0]
    avis, n = int(d["n"].sum()), int(touchees["k"].sum())
    par_fiche = touchees.groupby("cid", observed=True)["k"].sum()
    part = float(par_fiche.max() / n) if n else None
    return {"avis": avis, "suppressions": n,
            "pour_10000": round(10000 * n / avis, 1) if avis else None,
            "fiches": int(d["cid"].nunique()), "fiches_touchees": int(par_fiche.size),
            "enseignes_touchees": int(touchees["enseigne"].nunique()),
            "part_de_la_premiere_fiche": round(part, 2) if part is not None else None,
            "citable": bool(n >= MIN_SUPPRESSIONS_CITABLE and par_fiche.size >= MIN_FICHES_CITABLE
                            and part is not None and part <= PART_MAX_PREMIERE_FICHE)}


def effectifs_reponse(cases, col):
    """Les avis répondus d'une case et, à côté, les avis sans réponse auxquels ils se comparent."""
    c = col.removeprefix("réponse : avis de ")
    e, ref = cases[(c, "répondu avant le 11 août")], cases[(c, "sans réponse")]
    return {"avis": e["avis"], "suppressions": e["suppressions"],
            "fiches_touchees": e["fiches_touchees"], "enseignes_touchees": e["enseignes_touchees"],
            "part_de_la_premiere_fiche": e["part_de_la_premiere_fiche"],
            "avis_sans_reponse": ref["avis"], "suppressions_sans_reponse": ref["suppressions"],
            "fiches_touchees_sans_reponse": ref["fiches_touchees"],
            "part_de_la_premiere_fiche_sans_reponse": ref["part_de_la_premiere_fiche"],
            # Le rapport des deux taux, sans rien tenir égal : celui du point 7.
            "rapport_direct": (round(e["suppressions"] / e["avis"] / (ref["suppressions"] / ref["avis"]), 2)
                               if e["avis"] and ref["suppressions"] else None),
            "citable": "oui" if e["citable"] and ref["citable"] else "non"}


def cases_presentes(d):
    """Les cases âge × habitude qui restent dans le passage, dans l'ordre d'affichage."""
    return [c for c in CASES if (d["case"] == c).any()]


def colonnes(d, avec_region):
    X = pd.DataFrame(index=d.index)
    for c in CASES:
        X[f"réponse : avis de {c}"] = (d["repondu"] & (d["case"] == c)).astype(float)
    # L'âge et l'habitude eux-mêmes, case par case : la colonne de réponse se
    # lit ainsi face aux avis sans réponse de la même case. La référence est la
    # première case qui reste dans le passage.
    for c in cases_presentes(d)[1:]:
        X[f"âge et habitude : {c}"] = (d["case"] == c).astype(float)
    for car, (reference, modalites) in CONTROLES.items():
        if car == "region" and not avec_region:
            continue
        for m in modalites:
            if m != reference:
                X[f"{car} : {m}"] = (d[car] == m).astype(float)
    X = X.loc[:, (X != 0).any()]
    return sm.add_constant(X)


def modele(d, avec_region):
    """Les effets, puis la fourchette par fiche.

    Premier calcul sur les combinaisons de caractéristiques, toutes fiches
    réunies : dix fois moins de lignes. Second calcul par fiche, qui part du
    premier et n'a plus qu'à établir la fourchette.
    """
    m = d.groupby(MOTIF, observed=True)[["n", "k"]].sum().reset_index()
    depart = sm.GLM(np.column_stack([m["k"], m["n"] - m["k"]]), colonnes(m, avec_region),
                    family=sm.families.Binomial()).fit()
    X = colonnes(d, avec_region)
    return X, sm.GLM(np.column_stack([d["k"], d["n"] - d["k"]]), X, family=sm.families.Binomial()).fit(
        start_params=depart.params.reindex(X.columns).to_numpy(),
        cov_type="cluster", cov_kwds={"groups": pd.factorize(d["cid"])[0]})


PASSAGES = [(region, perimetre) for region in ["ensemble", "US", "Europe"]
            for perimetre in ["tous", "sans_enseignes"]]
lignes_effectifs, lignes_effets, lignes_notes = [], [], []

for region, perimetre in PASSAGES:
    passage = f"{region}, {perimetre}"
    d = d0 if region == "ensemble" else d0[d0["region"] == region]
    if perimetre == "sans_enseignes":
        d = d[~d["enseigne_signalee"]]

    # Effectifs de chaque case, avant tout modèle et avant le garde-fou.
    lignes_effectifs.append({"passage": passage, "caracteristique": "total du passage",
                             "modalite": "", "reponse": "", **effectifs(d)})
    cases = {}
    for c in CASES:
        for r in ["répondu avant le 11 août", "sans réponse"]:
            e = effectifs(d[(d["case"] == c) & (d["reponse"] == r)])
            cases[(c, r)] = e
            lignes_effectifs.append({"passage": passage, "caracteristique": "réponse",
                                     "modalite": c, "reponse": r, **e})
    for car, (_, modalites) in CONTROLES.items():
        for m in modalites:
            lignes_effectifs.append({"passage": passage, "caracteristique": car, "modalite": m,
                                     "reponse": "", **effectifs(d[d[car] == m])})

    # La note des avis répondus et des avis sans réponse, case par case. Les
    # avis sans réponse portent plus souvent 1 étoile : c'est ce qui sépare le
    # rapport direct du point 7 de l'effet calculé ici.
    g = d.groupby(["case", "reponse", "note"], observed=True)[["n", "k"]].sum().reset_index()
    g["part_des_avis_pct"] = (100 * g["n"] / g.groupby(["case", "reponse"], observed=True)["n"]
                              .transform("sum")).round(1)
    g.insert(0, "passage", passage)
    lignes_notes.append(g.rename(columns={"n": "avis", "k": "suppressions"}))

    # Garde-fou : une case trop maigre sort du passage.
    ecartees = []
    for c in CASES:
        if min(cases[(c, r)]["suppressions"] for r in ["répondu avant le 11 août", "sans réponse"]) < MIN_SUPPRESSIONS:
            ecartees.append(f"réponse : avis de {c}")
            d = d[d["case"] != c]
    for car, (reference, modalites) in CONTROLES.items():
        for m in modalites:
            case = d[car] == m
            if m != reference and case.any() and d.loc[case, "k"].sum() < MIN_SUPPRESSIONS:
                ecartees.append(f"{car} : {m}")
                d = d[~case]

    X, resultat = modele(d, avec_region=region == "ensemble")
    marges = resultat.conf_int()
    print(f"  {passage} : {len(d)} lignes, {int(d['n'].sum())} avis, {int(d['k'].sum())} suppressions, "
          f"{d['cid'].nunique()} fiches, {len(ecartees)} case(s) écartée(s)")

    for col in X.columns.drop("const"):
        ligne = {"passage": passage, "colonne": col,
                 "risque_relatif": round(float(np.exp(resultat.params[col])), 2),
                 "fourchette_basse": round(float(np.exp(marges.loc[col, 0])), 2),
                 "fourchette_haute": round(float(np.exp(marges.loc[col, 1])), 2), "remarque": ""}
        if col.startswith("réponse : "):
            ligne.update(effectifs_reponse(cases, col))
        else:
            ligne["citable"] = "contrôle"
            if col.startswith("âge et habitude : "):
                ligne["remarque"] = f"face aux avis sans réponse de {cases_presentes(d)[0]}"
        lignes_effets.append(ligne)
    for col in ecartees:
        ligne = {"passage": passage, "colonne": col,
                 "remarque": f"écartée : moins de {MIN_SUPPRESSIONS} suppressions"}
        if col.startswith("réponse : "):
            ligne.update(effectifs_reponse(cases, col))
        lignes_effets.append({**ligne, "citable": "non"})
    # Le passage suivant repart d'une mémoire libérée.
    del X, resultat, marges, d
    gc.collect()

ecrire_csv(pd.DataFrame(lignes_effectifs), "8_effectifs")
effets = pd.DataFrame(lignes_effets)
for col in ["avis", "suppressions", "fiches_touchees", "enseignes_touchees", "avis_sans_reponse",
            "suppressions_sans_reponse", "fiches_touchees_sans_reponse"]:
    effets[col] = effets[col].astype("Int64")
ecrire_csv(effets, "8_effets")
notes = pd.concat(lignes_notes)
notes["case"] = pd.Categorical(notes["case"], CASES, ordered=True)
ecrire_csv(notes.sort_values(["passage", "case", "reponse", "note"], kind="stable"), "8_notes_par_case")

# Les fiches derrière chaque case, avec les jours de suppression.
f = (d0[d0["k"] > 0]
     .groupby(["age", "habitude", "reponse", "cid", "enseigne", "region", "taille", "enseigne_signalee"],
              observed=True)
     .agg(suppressions=("k", "sum"),
          jours_de_suppression=("jours_de_suppression",
                                lambda s: ", ".join(sorted(set(", ".join(s).split(", "))))))
     .reset_index())
f["age"] = pd.Categorical(f["age"], AGES, ordered=True)
ecrire_csv(f.sort_values(["age", "habitude", "reponse", "suppressions"],
                         ascending=[True, True, True, False]), "8_fiches_par_case")

fig, axes = figure(3, 2, largeur=12, hauteur=11)
for ax, (region, perimetre) in zip(axes.flat, PASSAGES):
    e = effets[(effets["passage"] == f"{region}, {perimetre}")
               & effets["colonne"].str.startswith("réponse") & effets["risque_relatif"].notna()
               ].reset_index(drop=True)
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
    ax.set_yticks(y, e["colonne"].str.replace("réponse : avis de ", "").str.replace(", fiche qui répond à", " —"))
    ax.invert_yaxis()
    ax.set_title(f"{region}, {perimetre}")
fig.suptitle("Avis répondu avant le 11 août face à un avis sans réponse, toute la base — "
             "vert : citable, gris : non citable")
enregistrer(fig, "8_effets")
