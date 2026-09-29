"""5. Réponse du propriétaire, une ligne par avis et par jour.

    uv run python consolidation/5_reponse_jour_par_jour.py

LA QUESTION
  Un avis qui a déjà reçu sa réponse disparaît-il moins, les jours suivants,
  qu'un avis du même âge encore sans réponse ? Selon le délai de la réponse
  et selon l'habitude de la fiche ?

LE MONTAGE, ET CE QU'IL CHANGE PAR RAPPORT AU 3b
  Chaque avis compte une ligne par jour où il pouvait disparaître. La réponse
  entre le lendemain du jour où elle arrive. Exemple : un avis publié le
  12 août et répondu le 15 compte « sans réponse » les 13, 14 et 15 août, puis
  « réponse à 3 jours » à partir du 16. Il n'y a plus de jalon au 2e jour : les
  avis supprimés avant restent dans le calcul, et les réponses de 3 jours et
  plus se mesurent.

LES COLONNES (décidées par Romain le 2026-09-29)
  - délai de la réponse × habitude de la fiche : une colonne par délai (jour
    même, 1 jour, 2 jours, 3 jours et plus) et par habitude (75 % ou moins,
    plus de 75 %). Chacune se compare aux avis encore sans réponse, ce jour-là,
    sur des fiches de même habitude ;
  - l'habitude elle-même ;
  - la note : 1-2, 3-4, 5 étoiles (référence) ;
  - la région : États-Unis, Europe (référence) ;
  - l'âge de l'avis ce jour-là, jour par jour jusqu'au 8e (référence : 9 à
    13 jours). L'étude exploratoire avait réuni 0 à 6 jours en un bloc et
    brouillé ainsi l'effet de la réponse.

LECTURE ET CITATION
  « ×0,40 » : à âge, note et région égaux, l'avis répondu disparaît 0,40 fois
  autant que l'avis encore sans réponse. La fourchette tient compte de ce que
  les avis d'une même fiche se ressemblent. Un effet se cite selon la règle de
  `commun.py` : 20 suppressions, 10 fiches, aucune fiche au-delà du quart.

Produit :
  sorties/5_effectifs.csv        avis-jours et suppressions par case, avant le modèle
  sorties/5_effets.csv           risque relatif, fourchette, citable, par passage
  sorties/5_fiches_par_case.csv  les fiches derrière les suppressions de chaque case
  sorties/figures/5_effets.png
"""
import numpy as np
import pandas as pd
import statsmodels.api as sm
from matplotlib.ticker import FuncFormatter, NullFormatter

from commun import COULEURS, ecrire_csv, effectifs, enregistrer, figure, requete

DELAIS = ["jour même", "1 jour", "2 jours", "3 jours et plus"]
HABITUDES = ["75 % ou moins", "plus de 75 %"]
MIN_SUPPRESSIONS = 5

d0 = requete("5_jours")
for col in ["star", "age", "delai_reponse_j", "taux_reponse"]:
    d0[col] = d0[col].astype("float")
for col in ["enseigne_signalee", "reponse_la_veille"]:
    d0[col] = d0[col].fillna(False).astype(bool)
d0["y"] = d0["y"].astype(int)
d0["taille"] = np.where(d0["taille_detail"] == "large", "large", "mono + small")
d0["habitude"] = np.where(d0["taux_reponse"] > 0.75, "plus de 75 %", "75 % ou moins")
delai = np.select([d0["delai_reponse_j"] <= 0, d0["delai_reponse_j"] == 1, d0["delai_reponse_j"] == 2],
                  ["jour même", "1 jour", "2 jours"], "3 jours et plus")
# La case de chaque ligne : la réponse déjà là (et son délai), ou pas encore.
d0["reponse"] = np.where(d0["reponse_la_veille"], delai, "pas encore de réponse")
d0["case"] = d0["reponse"] + ", fiche qui répond à " + d0["habitude"]
d0["age_cat"] = np.select([d0["age"] <= 8, d0["age"] <= 13],
                          [d0["age"].astype(int).astype(str) + " jour(s)", "9 à 13 jours"],
                          "14 jours et plus")
print(f"  {len(d0)} avis-jours, {int(d0['y'].sum())} suppressions")

PASSAGES = [("mono + small", "tous"), ("mono + small", "sans_enseignes"),
            ("large", "tous"), ("large", "sans_enseignes"), ("mono", "tous"), ("small", "tous")]


def selection(taille, perimetre):
    colonne = "taille_detail" if taille in ("mono", "small") else "taille"
    d = d0[d0[colonne] == taille]
    return d if perimetre == "tous" else d[~d["enseigne_signalee"]]


def colonnes(d):
    X = pd.DataFrame(index=d.index)
    for h in HABITUDES:
        for dl in DELAIS:
            X[f"réponse {dl}, fiche qui répond à {h}"] = (d["case"] == f"{dl}, fiche qui répond à {h}").astype(float)
    X["fiche qui répond à plus de 75 %"] = (d["habitude"] == "plus de 75 %").astype(float)
    X["note 1 ou 2 étoiles"] = d["star"].isin([1, 2]).astype(float)
    X["note 3 ou 4 étoiles"] = d["star"].isin([3, 4]).astype(float)
    X["fiche aux États-Unis"] = (d["region"] == "US").astype(float)
    for a in [f"{i} jour(s)" for i in range(1, 9)] + ["14 jours et plus"]:
        X[f"âge : {a}"] = (d["age_cat"] == a).astype(float)
    return sm.add_constant(X)


lignes_effectifs, lignes_effets = [], []
for taille, perimetre in PASSAGES:
    passage = f"{taille}, {perimetre}"
    d = selection(taille, perimetre)

    # Effectifs de chaque case, avant tout modèle. Un avis répondu au 3e jour
    # compte dans « pas encore de réponse » les premiers jours, puis dans sa
    # case de réponse : les avis d'une ligne à l'autre ne s'additionnent pas.
    lignes_effectifs.append({"passage": passage, "habitude": "toutes", "reponse": "total du passage",
                             **effectifs(d)})
    cases = {}
    for h in HABITUDES:
        for r in DELAIS + ["pas encore de réponse"]:
            e = effectifs(d[d["case"] == f"{r}, fiche qui répond à {h}"])
            cases[(r, h)] = e
            lignes_effectifs.append({"passage": passage, "habitude": h, "reponse": r, **e})

    # Garde-fou : une case de réponse trop maigre sort du passage.
    ecartees = []
    for h in HABITUDES:
        for dl in DELAIS:
            case = d["case"] == f"{dl}, fiche qui répond à {h}"
            if d.loc[case, "y"].sum() < MIN_SUPPRESSIONS:
                ecartees.append((dl, h, int(case.sum()), int(d.loc[case, "y"].sum())))
                d = d[~case]

    X = colonnes(d)
    X = X.loc[:, (X != 0).any() | (X.columns == "const")]
    modele = sm.GLM(d["y"], X, family=sm.families.Binomial()).fit(
        cov_type="cluster", cov_kwds={"groups": pd.factorize(d["cid"])[0]})
    marges = modele.conf_int()
    print(f"  {passage} : {len(d)} avis-jours, {int(d['y'].sum())} suppressions, {d['cid'].nunique()} fiches")

    for col in X.columns.drop("const"):
        ligne = {"passage": passage, "colonne": col,
                 "risque_relatif": round(float(np.exp(modele.params[col])), 2),
                 "fourchette_basse": round(float(np.exp(marges.loc[col, 0])), 2),
                 "fourchette_haute": round(float(np.exp(marges.loc[col, 1])), 2), "remarque": ""}
        if col.startswith("réponse "):
            dl, h = col.removeprefix("réponse ").split(", fiche qui répond à ")
            e, ref = cases[(dl, h)], cases[("pas encore de réponse", h)]
            ligne.update({"avis_jours": e["lignes"], "suppressions": e["suppressions"],
                          "fiches_touchees": e["fiches_touchees"],
                          "enseignes_touchees": e["enseignes_touchees"],
                          "part_de_la_premiere_fiche": e["part_de_la_premiere_fiche"],
                          "citable": "oui" if e["citable"] and ref["citable"] else "non"})
        else:
            ligne["citable"] = "contrôle"
        lignes_effets.append(ligne)
    for dl, h, n_lignes, n_suppr in ecartees:
        lignes_effets.append({"passage": passage, "colonne": f"réponse {dl}, fiche qui répond à {h}",
                              "avis_jours": n_lignes, "suppressions": n_suppr, "citable": "non",
                              "remarque": f"écartée : moins de {MIN_SUPPRESSIONS} suppressions"})

ecrire_csv(pd.DataFrame(lignes_effectifs), "5_effectifs")
effets = pd.DataFrame(lignes_effets)
for col in ["avis_jours", "suppressions", "fiches_touchees", "enseignes_touchees"]:
    effets[col] = effets[col].astype("Int64")
ecrire_csv(effets, "5_effets")

# Les fiches derrière chaque case, toutes tailles, avec les dates de suppression.
f = (d0[d0["y"] == 1]
     .groupby(["taille_detail", "habitude", "reponse", "cid", "enseigne", "region", "enseigne_signalee"])
     .agg(suppressions=("y", "sum"),
          jours_de_suppression=("jour", lambda s: ", ".join(sorted(set(map(str, s))))))
     .reset_index()
     .sort_values(["taille_detail", "habitude", "reponse", "suppressions"],
                  ascending=[True, True, True, False]))
ecrire_csv(f, "5_fiches_par_case")

fig, axes = figure(3, 2, largeur=12, hauteur=11)
for ax, (taille, perimetre) in zip(axes.flat, PASSAGES):
    e = effets[(effets["passage"] == f"{taille}, {perimetre}")
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
    ax.set_yticks(y, e["colonne"].str.replace("réponse ", "").str.replace(", fiche qui répond à", " —"))
    ax.invert_yaxis()
    ax.set_title(f"{taille}, {perimetre}")
fig.suptitle("Avis déjà répondu face à un avis encore sans réponse — vert : citable, gris : non citable")
enregistrer(fig, "5_effets")
