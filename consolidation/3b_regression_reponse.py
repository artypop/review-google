"""3b. Réponse du propriétaire : délai de réponse et habitude de la fiche, par régression.

    uv run python consolidation/3b_regression_reponse.py

LA QUESTION
  Un avis qui a reçu une réponse le jour même, à 1 jour ou à 2 jours
  disparaît-il moins souvent du 3e au 8e jour qu'un avis sans réponse au
  2e jour ? Et la réponse joue-t-elle pareil sur une fiche qui répond à plus de
  75 % de ses avis et sur une fiche qui répond moins ?

POURQUOI UN JALON AU 2e JOUR
  Un avis supprimé au 3e jour ne peut plus recevoir de réponse au 5e. On ne
  regarde donc que les avis encore en ligne au 2e jour, on lit leur réponse à
  cette date, puis on compte ceux qui disparaissent ensuite. Une réponse
  arrivée plus tard compte comme « pas de réponse au 2e jour ».

LES COLONNES DU MODÈLE
  - une colonne oui / non par délai et par habitude : « réponse le jour même,
    fiche qui répond à plus de 75 % », etc. Chacune se compare aux avis sans
    réponse au 2e jour des fiches de même habitude ;
  - l'habitude elle-même ;
  - la note, en trois groupes : 1-2, 3-4, 5 étoiles (référence) ;
  - la région : États-Unis, Europe (référence).
  Avec deux colonnes séparées, délai et habitude, le modèle donnerait un seul
  effet de la réponse, le même pour tous les types de fiches.

LECTURE D'UN RÉSULTAT
  « ×0,40 » : à note et région égales, l'avis répondu disparaît 2,5 fois moins
  souvent que l'avis sans réponse au 2e jour, sur le même type de fiche. La
  fourchette donne les valeurs compatibles avec les données ; quand elle
  contient 1, les données ne tranchent pas. Les avis d'une même fiche se
  ressemblent : la fourchette en tient compte, comme dans le 08B.

GARDE-FOU
  Une case délai × habitude avec moins de 5 suppressions ne permet aucune
  estimation. Ses avis sortent du passage, et la ligne le dit dans
  `3b_effets.csv`.

Produit :
  sorties/3b_effectifs.csv   avis et suppressions par délai × habitude, avant tout modèle
  sorties/3b_fiches_par_case.csv  les fiches derrière les suppressions de chaque case :
                             cid, enseigne, dates de publication et de suppression
  sorties/3b_effets.csv      risque relatif, fourchette, effectifs, par passage
                             (mono + small et large, tous et sans enseignes ; puis mono
                             seul et small seul, pour contrôle)
  sorties/figures/3b_effets.png
"""
import numpy as np
from matplotlib.ticker import FuncFormatter, NullFormatter
import pandas as pd
import statsmodels.api as sm

from commun import COULEURS, ecrire_csv, enregistrer, figure, requete

DELAIS = ["jour même", "1 jour", "2 jours"]
HABITUDES = ["plus de 75 %", "75 % ou moins"]
MIN_SUPPRESSIONS = 5

pop = requete("3b_population")
pop["y"] = pop["supprime_3_8"].astype(int)

# Les quatre passages du plan, puis mono seul et small seul pour contrôler
# mono + small. Les 95 fiches signalées sont toutes `large` : pour mono et
# small, « tous » et « sans enseignes » sont identiques.
PASSAGES = [(taille, perimetre) for taille in ["mono + small", "large"]
            for perimetre in ["tous", "sans_enseignes"]] + [("mono", "tous"), ("small", "tous")]


def selection(taille, perimetre):
    colonne = "taille_detail" if taille in ("mono", "small") else "taille"
    d = pop[pop[colonne] == taille]
    return d if perimetre == "tous" else d[~d["enseigne_signalee"]]


# --- Effectifs, avant tout modèle -------------------------------------------
lignes = []
for taille, perimetre in PASSAGES:
    d = selection(taille, perimetre)
    for (habitude, delai), g in d.groupby(["habitude", "delai"]):
        lignes.append({
            "taille": taille, "perimetre": perimetre, "habitude": habitude, "delai": delai,
            "avis": len(g), "suppressions_3_8": int(g["y"].sum()),
            "fiches_touchees": g.loc[g["y"] == 1, "cid"].nunique(),
            "pour_10000": round(10000 * g["y"].mean()),
            "moins_de_5_suppressions": "oui" if g["y"].sum() < MIN_SUPPRESSIONS else "",
        })
effectifs = pd.DataFrame(lignes)
ordre_delai = {d: i for i, d in enumerate(DELAIS + ["pas de réponse au 2e jour"])}
ordre_passage = {p: i for i, p in enumerate(PASSAGES)}
effectifs["rang"] = [ordre_passage[(t, p)] for t, p in zip(effectifs["taille"], effectifs["perimetre"])]
effectifs = (effectifs.sort_values(["rang", "habitude", "delai"],
                                   key=lambda c: c.map(ordre_delai) if c.name == "delai" else c,
                                   ascending=[True, False, True])
             .drop(columns="rang"))
ecrire_csv(effectifs, "3b_effectifs")
ecrire_csv(requete("3b_fiches_par_case"), "3b_fiches_par_case")


# --- Régression, un passage par taille et par périmètre -----------------------
def colonnes_du_modele(d):
    X = pd.DataFrame(index=d.index)
    for habitude in HABITUDES:
        for delai in DELAIS:
            X[f"réponse {delai}, fiche qui répond à {habitude}"] = (
                (d["habitude"] == habitude) & (d["delai"] == delai)).astype(float)
    X["fiche qui répond à plus de 75 %"] = (d["habitude"] == "plus de 75 %").astype(float)
    X["note 1 ou 2 étoiles"] = d["star"].isin([1, 2]).astype(float)
    X["note 3 ou 4 étoiles"] = d["star"].isin([3, 4]).astype(float)
    X["fiche aux États-Unis"] = (d["region"] == "US").astype(float)
    return sm.add_constant(X)


resultats = []
for taille, perimetre in PASSAGES:
    passage = f"{taille}, {perimetre}"
    d = selection(taille, perimetre)

    # Garde-fou : une case délai × habitude trop maigre sort du passage.
    ecartees = []
    for habitude in HABITUDES:
        for delai in DELAIS:
            case = (d["habitude"] == habitude) & (d["delai"] == delai)
            if d.loc[case, "y"].sum() < MIN_SUPPRESSIONS:
                ecartees.append((habitude, delai, int(case.sum()), int(d.loc[case, "y"].sum())))
                d = d[~case]

    X = colonnes_du_modele(d)
    X = X.loc[:, (X != 0).any() | (X.columns == "const")]
    modele = sm.GLM(d["y"], X, family=sm.families.Binomial()).fit(
        cov_type="cluster", cov_kwds={"groups": pd.factorize(d["cid"])[0]})
    marges = modele.conf_int()
    print(f"  {passage} : {len(d)} avis, {int(d['y'].sum())} suppressions, "
          f"{d['cid'].nunique()} fiches")

    for col in X.columns.drop("const"):
        concernes = X[col] == 1
        resultats.append({
            "passage": passage, "colonne": col,
            "risque_relatif": round(float(np.exp(modele.params[col])), 2),
            "fourchette_basse": round(float(np.exp(marges.loc[col, 0])), 2),
            "fourchette_haute": round(float(np.exp(marges.loc[col, 1])), 2),
            "avis": int(concernes.sum()), "suppressions_3_8": int(d.loc[concernes, "y"].sum()),
            "remarque": "",
        })
    for habitude, delai, n_avis, n_suppr in ecartees:
        resultats.append({
            "passage": passage, "colonne": f"réponse {delai}, fiche qui répond à {habitude}",
            "risque_relatif": None, "fourchette_basse": None, "fourchette_haute": None,
            "avis": n_avis, "suppressions_3_8": n_suppr,
            "remarque": f"écartée : moins de {MIN_SUPPRESSIONS} suppressions",
        })
    resultats.append({
        "passage": passage, "colonne": "total du passage", "risque_relatif": None,
        "fourchette_basse": None, "fourchette_haute": None,
        "avis": len(d), "suppressions_3_8": int(d["y"].sum()),
        "remarque": f"{d['cid'].nunique()} fiches",
    })

effets = pd.DataFrame(resultats)
ecrire_csv(effets, "3b_effets")

# --- Contrôle : les effets de la réponse et leur fourchette, un panneau par passage.
fig, axes = figure(3, 2, largeur=12, hauteur=11)
for ax, (taille, perimetre) in zip(axes.flat, PASSAGES):
    e = effets[(effets["passage"] == f"{taille}, {perimetre}")
               & effets["colonne"].str.startswith("réponse")].reset_index(drop=True)
    y = np.arange(len(e))
    couleurs = [COULEURS["ensemble"] if "plus de 75" in c else COULEURS["Europe"]
                for c in e["colonne"]]
    ok = e["risque_relatif"].notna()
    ax.errorbar(e.loc[ok, "risque_relatif"], y[ok],
                xerr=[e.loc[ok, "risque_relatif"] - e.loc[ok, "fourchette_basse"],
                      e.loc[ok, "fourchette_haute"] - e.loc[ok, "risque_relatif"]],
                fmt="none", ecolor="#999999", elinewidth=1.5)
    ax.scatter(e.loc[ok, "risque_relatif"], y[ok], color=[c for c, k in zip(couleurs, ok) if k],
               s=40, zorder=3)
    ax.axvline(1, color="#52514e", linewidth=1)
    ax.set_xscale("log")
    ax.set_xticks([0.1, 0.2, 0.5, 1, 2, 5, 10])
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"×{v:g}".replace(".", ",")))
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.set_xlim(0.08, 15)
    ax.set_yticks(y, e["colonne"].str.replace("réponse ", "").str.replace(", fiche qui répond à", " —"))
    ax.invert_yaxis()
    ax.set_title(f"{taille}, {perimetre}")
fig.suptitle("Risque de suppression du 3e au 8e jour, face à un avis sans réponse au 2e jour")
enregistrer(fig, "3b_effets")
