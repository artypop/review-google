"""4b. Dans une fiche qui perd des avis, lequel tombe ? Comparaison dans la même fiche, le même jour.

    uv run python consolidation/4b_quel_avis.py

LA QUESTION
  Un jour où une fiche perd des avis, lesquels de ses avis en ligne
  disparaissent ? Exemple : chez Cedar Park Overhead Doors, le 16 août, parmi
  les avis en ligne la veille, lesquels ont disparu ? On pose la même question
  pour chaque fiche et chaque jour, et on additionne.

  Comme on ne compare que des avis de la même fiche le même jour, tout ce qui
  tient à la fiche s'annule : secteur, pays, taille, politique de modération,
  et le fait d'être une des chaînes ou des salles. Ces caractéristiques ne
  peuvent donc pas figurer ici : c'est le rôle de 4a.

LES COLONNES (référence entre parenthèses)
  note (5 étoiles) ; âge de l'avis ce jour-là, jour par jour jusqu'au 8e
  (9 à 13 jours) ; niveau Local Guide : sans niveau, 5 et plus (1 à 4) ;
  photo jointe (sans) ; longueur du texte (sans texte) ; photos publiées par
  l'auteur (0) ; avis déclarés par l'auteur (1 ou moins) ; réponse du
  propriétaire déjà là la veille, selon l'habitude de la fiche (pas de
  réponse).

LECTURE
  « ×2 » : dans la même fiche, le même jour, cet avis disparaît deux fois plus
  souvent que l'avis de référence. La fourchette traite les journées d'une
  même fiche comme indépendantes : la règle de citation (`commun.py`) garde
  contre les effets portés par quelques fiches.

GARDE-FOU
  Une modalité avec moins de 5 suppressions ne permet aucune estimation : ses
  lignes sortent du passage, et `4b_effets.csv` le dit.

Produit :
  sorties/4b_effectifs.csv       avis-jours, suppressions, fiches, enseignes, par case
  sorties/4b_effets.csv          risque relatif, fourchette, citable, par passage
  sorties/4b_fiches_par_case.csv les fiches derrière les suppressions de chaque case
  sorties/figures/4b_effets.png
"""
import warnings

import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter, NullFormatter
from statsmodels.discrete.conditional_models import ConditionalLogit
from statsmodels.tools.sm_exceptions import ConvergenceWarning

from commun import COULEURS, ecrire_csv, effectifs, enregistrer, figure, requete

MIN_SUPPRESSIONS = 5

d0 = requete("4b_jours")
d0["y"] = d0["y"].astype(int)
# BigQuery rend des entiers « à trous » : on passe en nombres ordinaires pour
# que les comparaisons ci-dessous donnent vrai ou faux, jamais « inconnu ».
for col in ["star", "age", "local_guide_level", "text_chars", "reviewer_photo_count",
            "reviewer_review_count", "taux_reponse"]:
    d0[col] = d0[col].astype("float")
for col in ["has_photo", "has_text", "enseigne_signalee", "reponse_la_veille"]:
    d0[col] = d0[col].fillna(False).astype(bool)

# --- Les modalités de chaque caractéristique ---------------------------------
d0["note"] = d0["star"].astype(int).astype(str) + " étoile(s)"
d0["age_cat"] = np.select([d0["age"] <= 8, d0["age"] <= 13],
                          [d0["age"].astype(int).astype(str) + " jour(s)", "9 à 13 jours"], "14 jours et plus")
d0["local_guide"] = np.select([d0["local_guide_level"].isna(), d0["local_guide_level"] <= 4],
                              ["sans niveau", "niveau 1 à 4"], "niveau 5 et plus")
d0["photo_jointe"] = np.where(d0["has_photo"], "avec photo", "sans photo")
d0["texte"] = np.select([~d0["has_text"], d0["text_chars"] <= 50, d0["text_chars"] <= 200],
                        ["sans texte", "1 à 50 caractères", "51 à 200 caractères"],
                        "plus de 200 caractères")
d0["photos_auteur"] = np.select([d0["reviewer_photo_count"] == 0, d0["reviewer_photo_count"] <= 20],
                                ["0 photo", "1 à 20 photos"], "plus de 20 photos")
d0["avis_auteur"] = np.select([d0["reviewer_review_count"].fillna(0) <= 1,
                               d0["reviewer_review_count"] <= 20],
                              ["1 avis ou moins", "2 à 20 avis"], "plus de 20 avis")
habitude = np.select([d0["taux_reponse"].isna(), d0["taux_reponse"] > 0.75],
                     ["habitude inconnue", "fiche qui répond à plus de 75 %"],
                     "fiche qui répond à 75 % ou moins")
d0["reponse"] = np.where(d0["reponse_la_veille"], "réponse déjà là, " + habitude,
                         "pas de réponse, " + habitude)

# (colonne, référence, modalités). Pour la réponse, la référence dépend de
# l'habitude : on compare un avis répondu aux avis non répondus de fiches de
# même habitude — dans la même fiche, l'habitude est la même.
CARACTERISTIQUES = {
    "note": ("5 étoile(s)", ["1 étoile(s)", "2 étoile(s)", "3 étoile(s)", "4 étoile(s)", "5 étoile(s)"]),
    "age_cat": ("9 à 13 jours", [f"{i} jour(s)" for i in range(1, 9)] + ["9 à 13 jours", "14 jours et plus"]),
    "local_guide": ("niveau 1 à 4", ["sans niveau", "niveau 1 à 4", "niveau 5 et plus"]),
    "photo_jointe": ("sans photo", ["sans photo", "avec photo"]),
    "texte": ("sans texte", ["sans texte", "1 à 50 caractères", "51 à 200 caractères", "plus de 200 caractères"]),
    "photos_auteur": ("0 photo", ["0 photo", "1 à 20 photos", "plus de 20 photos"]),
    "avis_auteur": ("1 avis ou moins", ["1 avis ou moins", "2 à 20 avis", "plus de 20 avis"]),
}
HABITUDES = ["fiche qui répond à 75 % ou moins", "fiche qui répond à plus de 75 %", "habitude inconnue"]


def reference_de(car, modalite):
    if car == "reponse":
        return modalite.replace("réponse déjà là", "pas de réponse")
    return CARACTERISTIQUES[car][0]


def colonnes(d):
    """Les colonnes du modèle : une par modalité hors référence."""
    X = pd.DataFrame(index=d.index)
    for car, (reference, modalites) in CARACTERISTIQUES.items():
        for m in modalites:
            if m != reference:
                X[f"{car} : {m}"] = (d[car] == m).astype(float)
    for h in HABITUDES:
        X[f"reponse : réponse déjà là, {h}"] = (d["reponse"] == f"réponse déjà là, {h}").astype(float)
    return X


PASSAGES = [(region, perimetre) for region in ["ensemble", "US", "Europe"]
            for perimetre in ["tous", "sans_enseignes"]]
lignes_effectifs, lignes_effets = [], []

for region, perimetre in PASSAGES:
    passage = f"{region}, {perimetre}"
    d = d0 if region == "ensemble" else d0[d0["region"] == region]
    if perimetre == "sans_enseignes":
        d = d[~d["enseigne_signalee"]]

    # Garde-fou : une modalité trop maigre sort du passage.
    ecartees = []
    for col in colonnes(d).columns:
        car, m = col.split(" : ", 1)
        case = d[car] == m
        if case.any() and d.loc[case, "y"].sum() < MIN_SUPPRESSIONS:
            ecartees.append((col, int(case.sum()), int(d.loc[case, "y"].sum())))
            d = d[~case]

    X = colonnes(d)
    X = X.loc[:, X.sum() > 0]
    # Réglage par défaut : « US, tous » ne converge pas (vérifié le 2026-09-29).
    # Avec 3 000 itérations, les six passages convergent ; on le vérifie à
    # chaque lancement et on l'écrit dans `4b_effets.csv`.
    with warnings.catch_warnings(record=True) as alertes:
        warnings.simplefilter("always")
        modele = ConditionalLogit(d["y"], X, groups=d["strate"]).fit(
            disp=False, method="bfgs", maxiter=3000)
    converge = not any(issubclass(a.category, ConvergenceWarning) for a in alertes)
    if not converge:
        print(f"  ATTENTION : {passage} n'a pas convergé, ses effets ne se citent pas")
    marges = modele.conf_int()
    print(f"  {passage} : {len(d)} avis-jours, {int(d['y'].sum())} suppressions, "
          f"{d['strate'].nunique()} journées de fiche, {d['cid'].nunique()} fiches")

    lignes_effectifs.append({"passage": passage, "caracteristique": "total du passage",
                             "modalite": f"{d['strate'].nunique()} journées de fiche",
                             **effectifs(d)})
    cases = {}
    for car in list(CARACTERISTIQUES) + ["reponse"]:
        for m in sorted(d[car].unique()):
            e = effectifs(d[d[car] == m])
            cases[(car, m)] = e
            lignes_effectifs.append({"passage": passage, "caracteristique": car, "modalite": m, **e})

    for col in X.columns:
        car, m = col.split(" : ", 1)
        e, ref = cases[(car, m)], cases.get((car, reference_de(car, m)))
        lignes_effets.append({
            "passage": passage, "colonne": col,
            "risque_relatif": round(float(np.exp(modele.params[col])), 2),
            "fourchette_basse": round(float(np.exp(marges.loc[col, 0])), 2),
            "fourchette_haute": round(float(np.exp(marges.loc[col, 1])), 2),
            "avis_jours": e["lignes"], "suppressions": e["suppressions"],
            "fiches_touchees": e["fiches_touchees"], "enseignes_touchees": e["enseignes_touchees"],
            "part_de_la_premiere_fiche": e["part_de_la_premiere_fiche"],
            "citable": "oui" if converge and e["citable"] and ref and ref["citable"] else "non",
            "remarque": "" if converge else "calcul non convergé"})
    for col, n_lignes, n_suppr in ecartees:
        lignes_effets.append({"passage": passage, "colonne": col, "avis_jours": n_lignes,
                              "suppressions": n_suppr, "citable": "non",
                              "remarque": f"écartée : moins de {MIN_SUPPRESSIONS} suppressions"})

ecrire_csv(pd.DataFrame(lignes_effectifs), "4b_effectifs")
effets = pd.DataFrame(lignes_effets)
for col in ["avis_jours", "suppressions", "fiches_touchees", "enseignes_touchees"]:
    effets[col] = effets[col].astype("Int64")
ecrire_csv(effets, "4b_effets")

# --- Les fiches derrière chaque case, sur le passage « ensemble, tous » ------
lignes = []
for car in list(CARACTERISTIQUES) + ["reponse"]:
    g = (d0[d0["y"] == 1].groupby([car, "cid", "enseigne", "region", "enseigne_signalee"])
         .agg(suppressions=("y", "sum"),
              jours_de_suppression=("jour", lambda s: ", ".join(sorted(set(map(str, s))))))
         .reset_index().rename(columns={car: "modalite"}))
    g.insert(0, "caracteristique", car)
    lignes.append(g)
ecrire_csv(pd.concat(lignes).sort_values(["caracteristique", "modalite", "suppressions"],
                                         ascending=[True, True, False]), "4b_fiches_par_case")

# --- Contrôle : les effets et leur fourchette, un panneau par passage --------
fig, axes = figure(3, 2, largeur=13, hauteur=20)
for ax, (region, perimetre) in zip(axes.flat, PASSAGES):
    e = effets[(effets["passage"] == f"{region}, {perimetre}")
               & effets["risque_relatif"].notna()].reset_index(drop=True)
    y = np.arange(len(e))
    couleurs = [COULEURS["ensemble"] if c == "oui" else "#b0afa9" for c in e["citable"]]
    ax.errorbar(e["risque_relatif"], y, xerr=[e["risque_relatif"] - e["fourchette_basse"],
                                              e["fourchette_haute"] - e["risque_relatif"]],
                fmt="none", ecolor="#999999", elinewidth=1.5)
    ax.scatter(e["risque_relatif"], y, color=couleurs, s=36, zorder=3)
    ax.axvline(1, color="#52514e", linewidth=1)
    ax.set_xscale("log")
    ax.set_xticks([0.1, 0.2, 0.5, 1, 2, 5, 10])
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"×{v:g}".replace(".", ",")))
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.set_xlim(0.05, 20)
    ax.set_yticks(y, e["colonne"], fontsize=7)
    ax.invert_yaxis()
    ax.set_title(f"{region}, {perimetre}")
fig.suptitle("Dans la même fiche, le même jour : quel avis tombe — vert : citable, gris : non citable")
enregistrer(fig, "4b_effets")
