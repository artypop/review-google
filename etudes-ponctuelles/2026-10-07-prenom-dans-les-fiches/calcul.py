#!/usr/bin/env python3
"""Dans les fiches riches en prénoms, Google supprime-t-il plus souvent les avis qui en citent un ?

    PYTHONPATH=".venv/Lib/site-packages;outils" <python uv> etudes-ponctuelles/2026-10-07-prenom-dans-les-fiches/calcul.py

Question de Matthieu du 2026-10-07 : les fiches où beaucoup d'avis citent un prénom perdent
plus d'avis (piste 3, 148 contre 26 pour 100 000). Dans ces fiches, les avis supprimés
citent-ils un prénom plus souvent que l'ensemble des avis de la fiche ?

Données et définitions de `2026-10-06-velocite-prenom/calcul.py`, importées telles
quelles : prénom annoté par Axel (avis 4-5 étoiles avec texte), suppression du 11 au 24
août 2026 dans notre base, sans les six enseignes ; classes d'Axel sur la part de
prénoms de la fiche avant le 7 août, fiches d'au moins 20 avis annotés.

Pour chaque classe :
  attendus   pour chaque fiche, ses suppressions × sa part d'avis avec prénom, sommé ;
             c'est le nombre d'avis supprimés avec prénom si Google tirait au hasard
             dans la fiche.
  observés   avis supprimés qui citent un prénom.
  rapport    rapport de cotes de Mantel-Haenszel, une strate par fiche, fourchette à 95 %
             de Robins, Breslow et Greenland. Ne compare que des avis d'une même fiche.

Deux découpages : par fiche, puis par fiche et classe d'âge de l'avis au 11 août (classes
de l'étude du 2026-10-06). Le second compare des avis d'une même fiche et du même âge :
si les avis avec prénom d'une fiche sont plus récents, ils sont plus exposés, les
suppressions frappant surtout les avis récents.

Sortie : `sorties/prenom_dans_les_fiches.csv`. Aucun texte, nom d'auteur ni lien.
"""
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd

DOSSIER = Path(__file__).resolve().parent
RACINE = DOSSIER.parents[1]
sys.path.insert(0, str(RACINE / "outils"))
_spec = importlib.util.spec_from_file_location(
    "velocite", RACINE / "etudes-ponctuelles" / "2026-10-06-velocite-prenom" / "calcul.py")
v = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(v)
from local import connexion  # noqa: E402

SORTIE = DOSSIER / "sorties" / "prenom_dans_les_fiches.csv"
# Effectifs de velocite_prenom_fiches.csv (étude du 2026-10-06), pour contrôle.
ATTENDU = {"moins de 10 %": (1_037_605, 267), "10-25 %": (532_340, 253),
           "25-50 %": (420_876, 486), "50 % et plus": (453_466, 670)}


def mantel_haenszel(t: pd.DataFrame) -> tuple[float, float, float]:
    """t : une ligne par fiche, colonnes a (supprimé, prénom), b (gardé, prénom),
    c (supprimé, sans prénom), d (gardé, sans prénom)."""
    n = t[["a", "b", "c", "d"]].sum(axis=1).astype(float)
    R, S = t["a"] * t["d"] / n, t["b"] * t["c"] / n
    P, Q = (t["a"] + t["d"]) / n, (t["b"] + t["c"]) / n
    sr, ss = R.sum(), S.sum()
    var = ((P * R).sum() / (2 * sr ** 2) + (P * S + Q * R).sum() / (2 * sr * ss)
           + (Q * S).sum() / (2 * ss ** 2))
    rc = sr / ss
    return rc, rc * np.exp(-1.96 * np.sqrt(var)), rc * np.exp(1.96 * np.sqrt(var))


def main() -> None:
    con = connexion("4GB")
    con.execute("SET threads=4")
    fi = v.fiches(con)
    av = v.avis_tous_ages(con)
    av = av.merge(fi[["cid", "classe_prenom"]], on="cid", how="left")
    av["has_name"] = av["has_name"].astype(bool)
    av["supprime"] = av["supprime"].astype(bool)
    av["classe_age"] = v.classe_age(av["age_j"])
    lignes = []
    for decoupage, strate in [("même fiche", ["cid"]), ("même fiche et même âge", ["cid", "classe_age"])]:
        lignes += comparer(av, decoupage, strate)
    res = pd.DataFrame(lignes)
    SORTIE.parent.mkdir(exist_ok=True)
    res.to_csv(SORTIE, index=False)
    pd.set_option("display.width", 250)
    print(res.to_string(index=False, float_format=lambda x: f"{x:.3f}"))
    print(f"\nécrit : {SORTIE}")


def comparer(av: pd.DataFrame, decoupage: str, strate: list[str]) -> list[dict]:
    par_fiche = (av.assign(a=av.supprime & av.has_name, b=~av.supprime & av.has_name,
                           c=av.supprime & ~av.has_name, d=~av.supprime & ~av.has_name)
                 .groupby(["classe_prenom"] + strate)[["a", "b", "c", "d"]].sum().reset_index())
    par_fiche["avis"] = par_fiche[["a", "b", "c", "d"]].sum(axis=1)
    par_fiche["supprimes"] = par_fiche["a"] + par_fiche["c"]
    par_fiche["attendus"] = par_fiche["supprimes"] * (par_fiche["a"] + par_fiche["b"]) / par_fiche["avis"]

    lignes = []
    for classe in v.CLASSES_PRENOM + ["toutes classes"]:
        t = par_fiche if classe == "toutes classes" else par_fiche[par_fiche["classe_prenom"] == classe]
        if classe == "toutes classes":
            t = t[t["classe_prenom"].isin(v.CLASSES_PRENOM)]
        avis, supp = int(t["avis"].sum()), int(t["supprimes"].sum())
        if classe in ATTENDU and (avis, supp) != ATTENDU[classe]:
            raise SystemExit(f"{classe} : {avis} avis, {supp} supprimés ; attendu {ATTENDU[classe]}.")
        rc, bas, haut = mantel_haenszel(t)
        lignes.append({
            "decoupage": decoupage, "classe_prenom": classe, "fiches": t["cid"].nunique(),
            "fiches_avec_suppression": t.loc[t["supprimes"] > 0, "cid"].nunique(),
            "avis": avis, "avis_avec_prenom": int(t["a"].sum() + t["b"].sum()),
            "supprimes": supp, "supprimes_avec_prenom": int(t["a"].sum()),
            "supprimes_avec_prenom_attendus": t["attendus"].sum(),
            "part_prenom_avis": (t["a"].sum() + t["b"].sum()) / avis,
            "part_prenom_supprimes": t["a"].sum() / supp,
            "observes_sur_attendus": t["a"].sum() / t["attendus"].sum(),
            "rapport_de_cotes": rc, "borne_basse": bas, "borne_haute": haut})
    return lignes


if __name__ == "__main__":
    main()
