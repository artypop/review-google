#!/usr/bin/env python3
"""Les avis supprimés se ressemblent-ils, à note égale, aux États-Unis ?

    .venv/Scripts/python.exe etudes-ponctuelles/2026-09-28-kmeans-us-1-5-etoiles/calcul.py

Demande de Matthieu du 2026-09-28. Reprend les vecteurs de l'étude embedding
(`data/embeddings/03B_e5base.parquet`, panel 03B, avis avec texte, modèle
e5-base) et les découpe en peu de groupes, K = 3 puis K = 4, pour voir si les
avis supprimés tombent davantage dans un groupe que les autres.

------------------------------------------------------------------------------
LES POPULATIONS
------------------------------------------------------------------------------
Avis de fiches américaines (`businesses.country = 'US'`), en anglais : 97,9 %
des avis américains avec texte. Une note à la fois, 1 étoile et 5 étoiles.
Chacune deux fois : toutes les fiches, puis sans les six enseignes signalées
(colonne `enseigne_signalee` des vecteurs, même repérage que la figure 9 du
rapport). Soit 4 populations × 2 valeurs de K = 8 regroupements.

------------------------------------------------------------------------------
LES MESURES
------------------------------------------------------------------------------
A. Par groupe : avis, suppressions, part supprimée, fiches, longueur médiane,
   part des enseignes signalées, et part des suppressions du groupe portée par
   sa fiche la plus touchée (un groupe très supprimé peut n'être qu'une fiche).

   Comparaison au hasard : 2 000 groupes de même taille tirés au hasard dans
   la même population donnent la fourchette du nombre de suppressions qu'on
   attendrait si le texte n'avait rien à voir avec la suppression. Un groupe
   hors de cette fourchette (2,5 % – 97,5 %) est marqué.

   Contrôle par secteur (ajouté le 2026-09-28 après lecture des groupes) :
   nombre de suppressions attendu si chaque avis avait le taux de suppression
   de son secteur dans la population, et écart à cet attendu en écarts-types
   (tirages indépendants, sans regroupement par fiche : l'écart-type est donc
   plutôt sous-estimé, ce qui rend le contrôle favorable aux groupes).

B. Par population, sans regroupement : écart entre le centre des textes
   supprimés et celui des textes restés en ligne, comparé à 2 000 partages au
   hasard de mêmes tailles. Même calcul que la route B du 02_resultats.py.

KMeans : celui du 03_appartenance_groupes.py (scikit-learn s'il se charge,
sinon sa réécriture numpy, vérifiée identique le 2026-09-25), même graine.

Sorties : `sorties/*.csv`. Identifiants d'avis et de fiche seulement, aucun
texte, aucun nom d'auteur, aucun lien d'avis.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

DOSSIER = Path(__file__).resolve().parent
RACINE = DOSSIER.parents[1]
SORTIES = DOSSIER / "sorties"
VECTEURS = RACINE / "data" / "embeddings" / "03B_e5base.parquet"
BUSINESSES = RACINE / "data" / "bigquery" / "businesses.parquet"
ETUDE_EMBEDDING = RACINE / "etudes-ponctuelles" / "2026-09-21-texte-embedding-03B"

GRAINE = 20260928
N_TIRAGES = 2000
VALEURS_K = (3, 4)


def charger_kmeans():
    spec = importlib.util.spec_from_file_location(
        "appartenance", ETUDE_EMBEDDING / "03_appartenance_groupes.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.regrouper


def populations(df: pd.DataFrame) -> dict[str, np.ndarray]:
    base = (df["pays"] == "US") & (df["langue"] == "en")
    out = {}
    for note in (1, 5):
        for nom, garde in (("toutes_fiches", True), ("sans_enseignes", ~df["enseigne_signalee"])):
            out[f"{note}_etoile{'s' if note > 1 else ''}_{nom}"] = \
                np.where(base & (df["note"] == note) & garde)[0]
    return out


def decrire(t: pd.DataFrame, rng) -> pd.DataFrame:
    n, n_supp = len(t), int(t["supprime"].sum())
    t = t.assign(taux_secteur=t["industry"].map(t.groupby("industry")["supprime"].mean()))
    lignes = []
    for g, bloc in t.groupby("groupe"):
        s = int(bloc["supprime"].sum())
        attendu_secteur = bloc["taux_secteur"].sum()
        sd_secteur = np.sqrt((bloc["taux_secteur"] * (1 - bloc["taux_secteur"])).sum())
        tirages = rng.hypergeometric(n_supp, n - n_supp, len(bloc), size=N_TIRAGES)
        bas, haut = np.percentile(tirages, [2.5, 97.5])
        par_fiche = bloc.loc[bloc["supprime"], "cid"].value_counts()
        lignes.append({
            "groupe": int(g), "n_avis": len(bloc), "n_supprimes": s,
            "part_supprimee_pct": round(100 * s / len(bloc), 2),
            "attendu_au_hasard": round(float(tirages.mean()), 1),
            "hasard_borne_basse": int(bas), "hasard_borne_haute": int(haut),
            "hors_du_hasard": "plus" if s > haut else ("moins" if s < bas else ""),
            "attendu_par_secteur": round(float(attendu_secteur), 1),
            "ecart_au_secteur_en_ecarts_types": round(float((s - attendu_secteur) / sd_secteur), 2),
            "n_fiches": bloc["cid"].nunique(),
            "fiches_touchees": int(len(par_fiche)),
            "part_supp_fiche_la_plus_touchee_pct":
                round(100 * par_fiche.iloc[0] / s, 1) if s else np.nan,
            "longueur_mediane": int(bloc["n_caracteres"].median()),
            "part_enseignes_pct": round(100 * bloc["enseigne_signalee"].mean(), 1),
        })
    return pd.DataFrame(lignes)


def ecart_centres(v: np.ndarray, masque: np.ndarray) -> float:
    a, b = v[masque].mean(axis=0), v[~masque].mean(axis=0)
    return float(1.0 - (a / np.linalg.norm(a)) @ (b / np.linalg.norm(b)))


def route_b(v: np.ndarray, supprime: np.ndarray, rng) -> dict:
    n, n_supp = len(supprime), int(supprime.sum())
    observe = ecart_centres(v, supprime)
    tirages = np.empty(N_TIRAGES)
    for i in range(N_TIRAGES):
        faux = np.zeros(n, dtype=bool)
        faux[rng.choice(n, n_supp, replace=False)] = True
        tirages[i] = ecart_centres(v, faux)
    bas, haut = np.percentile(tirages, [2.5, 97.5])
    return {"n_supprimes": n_supp, "n_restes": n - n_supp,
            "ecart_observe": round(observe, 4), "hasard_moyen": round(float(tirages.mean()), 4),
            "hasard_borne_haute": round(float(haut), 4),
            "rapport_observe_sur_hasard": round(observe / tirages.mean(), 2),
            "au_dessus_du_hasard": bool(observe > haut)}


def main() -> int:
    regrouper = charger_kmeans()
    df = pd.read_parquet(VECTEURS)
    v = np.vstack(df["vecteur"].to_numpy()).astype("float32")
    df = df.drop(columns=["vecteur"]).reset_index(drop=True)
    pays = pd.read_parquet(BUSINESSES, columns=["cid", "country", "industry"]).rename(
        columns={"country": "pays"})
    df = df.merge(pays, on="cid", how="left", validate="many_to_one")
    SORTIES.mkdir(parents=True, exist_ok=True)

    rng = np.random.default_rng(GRAINE)
    groupes, membres, centres = [], [], []
    for pop, idx in populations(df).items():
        t0 = df.iloc[idx][["review_id", "cid", "supprime", "n_caracteres", "enseigne_signalee",
                           "industry"]]
        centres.append({"population": pop, "n_fiches": t0["cid"].nunique(),
                        **route_b(v[idx], t0["supprime"].to_numpy(), rng)})
        for k in VALEURS_K:
            print(f"{pop} : {len(idx)} avis, K = {k}")
            t = t0.assign(groupe=regrouper(v[idx], k))
            d = decrire(t, rng)
            d.insert(0, "k", k); d.insert(0, "population", pop)
            groupes.append(d)
            membres.append(t[["review_id", "cid", "groupe", "supprime"]]
                           .assign(population=pop, k=k))

    g = pd.concat(groupes, ignore_index=True)
    g.to_csv(SORTIES / "A1-groupes.csv", index=False)
    pd.DataFrame(centres).to_csv(SORTIES / "B1-ecart-centres.csv", index=False)
    (pd.concat(membres, ignore_index=True)
     [["population", "k", "groupe", "review_id", "cid", "supprime"]]
     .to_csv(SORTIES / "A2-appartenance-avis.csv", index=False))
    pd.set_option("display.width", 220)
    print(g.to_string(index=False))
    print(pd.DataFrame(centres).to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
