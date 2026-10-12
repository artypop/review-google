#!/usr/bin/env python3
"""Groupes de textes après retrait du secteur et de la note, avis américains.

    .venv/Scripts/python.exe etudes-ponctuelles/2026-09-29-hdbscan-residus-us/calcul.py

Demande de Matthieu du 2026-09-29, d'après la remarque de Romain : les groupes
du KMeans du 2026-09-28 suivent le secteur et la longueur des textes. On
cherche des groupes de forme (prénom du technicien, éloge court…), donc on
retire aux vecteurs ce qui tient au secteur et à la note avant de regrouper.

------------------------------------------------------------------------------
LA POPULATION
------------------------------------------------------------------------------
Avis de fiches américaines (`businesses.country = 'US'`), en anglais, avec
texte. Vecteurs : `data/embeddings/03B_e5base.parquet` (e5-base, norme 1).
Deux versions : toutes les fiches, puis sans les six enseignes signalées
(colonne `enseigne_signalee` des vecteurs).

------------------------------------------------------------------------------
LE RETRAIT DU SECTEUR ET DE LA NOTE
------------------------------------------------------------------------------
Case = secteur (`businesses.industry`) × tranche de note (1 ; 2 à 4 ; 5).
Une case de moins de 30 avis rejoint la case « tous secteurs » de sa tranche.
Chaque vecteur perd le vecteur moyen de sa case (supprimés compris), puis est
remis à norme 1. La longueur du texte n'est pas retirée : l'éloge court est un
des motifs cherchés.

Centrer par fiche a été écarté : un prénom répété sur les avis d'une fiche
entre dans le vecteur moyen de la fiche et disparaîtrait avec lui.

------------------------------------------------------------------------------
LE REGROUPEMENT
------------------------------------------------------------------------------
ACP à 50 dimensions, t-SNE à 2 dimensions, HDBSCAN (min_cluster_size = 30,
min_samples = 10, sélection « leaf »), tout scikit-learn 1.9.

Écartés le 2026-09-29, essais consignés dans la note :
  UMAP          installé, mais Windows bloque la bibliothèque compilée numba
  ACP 50 seule  HDBSCAN laisse 76 à 87 % des avis sans groupe, 2 à 4 groupes
  ACP 10 seule  2 à 11 groupes
  « eom »       sur les restes, 2 groupes qui réunissent 99 % des avis

t-SNE dépend de son point de départ : trois passages sur les vecteurs corrigés,
le premier parti de l'ACP, les deux autres d'un départ au hasard. Un groupe
de la graine 0 est dit stable si, pour chacune des deux autres graines, un
groupe partage avec lui au moins la moitié de ses avis (indice de Jaccard ≥ 0,5).
Les vecteurs bruts, sans retrait, passent une seule fois, pour comparaison.

------------------------------------------------------------------------------
LES MESURES PAR GROUPE (graine 0)
------------------------------------------------------------------------------
Avis, suppressions, part supprimée. Attendu par case : somme, sur les avis du
groupe, du taux de suppression de leur case. Fourchette du hasard : 2 000
tirages d'avis au hasard avec la même composition par case que le groupe
(2,5 % – 97,5 %). Fiches, part des suppressions portée par la fiche la plus
touchée, longueur médiane, note moyenne, secteur principal et sa part, part
des enseignes signalées, stabilité.

Par regroupement : nombre de groupes, part d'avis sans groupe, taille médiane,
part des avis d'un groupe qui viennent de son secteur principal (moyenne
pondérée par la taille), et la même part pour des groupes tirés au hasard.

Sorties : `sorties/*.csv`, identifiants d'avis et de fiche seulement, aucun
texte, aucun nom d'auteur, aucun lien d'avis.
"""
from __future__ import annotations

import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import HDBSCAN
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE

warnings.filterwarnings("ignore", category=FutureWarning)

DOSSIER = Path(__file__).resolve().parent
RACINE = DOSSIER.parents[1]
SORTIES = DOSSIER / "sorties"
VECTEURS = RACINE / "data" / "embeddings" / "03B_e5base.parquet"
BUSINESSES = RACINE / "data" / "bigquery" / "businesses.parquet"

GRAINES = (0, 1, 2)
N_TIRAGES = 2000
CASE_MIN = 30
N_ACP = 50
PERPLEXITE = 30
TAILLE_MIN, VOISINS_MIN = 30, 10
SEUIL_STABLE = 0.5
N_FILS = 6


def journal(message: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {message}", flush=True)


def charger() -> tuple[pd.DataFrame, np.ndarray]:
    df = pd.read_parquet(VECTEURS)
    pays = pd.read_parquet(BUSINESSES, columns=["cid", "country", "industry"])
    df = df.merge(pays, on="cid", how="left", validate="many_to_one")
    df = df[(df["country"] == "US") & (df["langue"] == "en")].reset_index(drop=True)
    v = np.vstack(df["vecteur"].to_numpy()).astype("float32")
    df = df.drop(columns=["vecteur"])
    df["tranche"] = np.select([df["note"] == 1, df["note"] == 5], ["1", "5"], "2-4")
    return df, v


def cases(t: pd.DataFrame) -> pd.Series:
    case = t["industry"] + " | " + t["tranche"]
    petites = case.map(case.value_counts()) < CASE_MIN
    return case.where(~petites, "tous secteurs | " + t["tranche"])


def retirer_cases(v: np.ndarray, case: pd.Series) -> np.ndarray:
    moyennes = pd.DataFrame(v).groupby(case.to_numpy()).transform("mean").to_numpy()
    r = v - moyennes
    return (r / np.linalg.norm(r, axis=1, keepdims=True)).astype("float32")


def regrouper(v: np.ndarray, graine: int) -> np.ndarray:
    z = PCA(N_ACP, random_state=graine).fit_transform(v)
    # Départ ACP pour la graine 0, départ au hasard pour les autres : avec un
    # départ ACP, t-SNE est déterministe et la graine ne change rien.
    y = TSNE(2, perplexity=PERPLEXITE, init="pca" if graine == 0 else "random",
             random_state=graine, n_jobs=N_FILS).fit_transform(z)
    return HDBSCAN(min_cluster_size=TAILLE_MIN, min_samples=VOISINS_MIN,
                   cluster_selection_method="leaf", copy=True).fit_predict(y)


def stabilite(ref: np.ndarray, autres: list[np.ndarray]) -> dict[int, float]:
    """Pour chaque groupe de `ref`, le plus faible des meilleurs Jaccard obtenus
    dans les autres regroupements."""
    out = {}
    for g in range(ref.max() + 1):
        a = ref == g
        meilleurs = []
        for autre in autres:
            cand = np.unique(autre[a & (autre >= 0)])
            meilleurs.append(max((np.sum(a & (autre == c)) / np.sum(a | (autre == c))
                                  for c in cand), default=0.0))
        out[g] = float(min(meilleurs))
    return out


def purete(t: pd.DataFrame, groupe: np.ndarray) -> float:
    m = groupe >= 0
    x = pd.crosstab(groupe[m], t["industry"].to_numpy()[m])
    return float(x.max(axis=1).sum() / x.to_numpy().sum())


def decrire(t: pd.DataFrame, groupe: np.ndarray, stable: dict[int, float],
            rng) -> pd.DataFrame:
    t = t.assign(groupe=groupe)
    par_case = t.groupby("case")["supprime"].agg(["sum", "count"])
    t["taux_case"] = t["case"].map(par_case["sum"] / par_case["count"])
    lignes = []
    for g, bloc in t.groupby("groupe"):
        s = int(bloc["supprime"].sum())
        tirages = np.zeros(N_TIRAGES)
        for c, n_c in bloc["case"].value_counts().items():
            k, n = int(par_case.at[c, "sum"]), int(par_case.at[c, "count"])
            tirages += rng.hypergeometric(k, n - k, n_c, size=N_TIRAGES)
        bas, haut = np.percentile(tirages, [2.5, 97.5])
        par_fiche = bloc.loc[bloc["supprime"], "cid"].value_counts()
        secteurs = bloc["industry"].value_counts(normalize=True)
        lignes.append({
            "groupe": int(g), "n_avis": len(bloc), "n_supprimes": s,
            "part_supprimee_pct": round(100 * s / len(bloc), 2),
            "attendu_par_case": round(float(bloc["taux_case"].sum()), 1),
            "rapport_observe_attendu": round(s / bloc["taux_case"].sum(), 2)
            if bloc["taux_case"].sum() > 0 else np.nan,
            "hasard_borne_basse": int(bas), "hasard_borne_haute": int(haut),
            "hors_du_hasard": "plus" if s > haut else ("moins" if s < bas else ""),
            "n_fiches": bloc["cid"].nunique(),
            "fiches_touchees": int(len(par_fiche)),
            "part_supp_fiche_la_plus_touchee_pct":
                round(100 * par_fiche.iloc[0] / s, 1) if s else np.nan,
            "longueur_mediane": int(bloc["n_caracteres"].median()),
            "note_moyenne": round(float(bloc["note"].mean()), 2),
            "secteur_principal": secteurs.index[0],
            "part_secteur_principal_pct": round(100 * secteurs.iloc[0], 1),
            "part_enseignes_pct": round(100 * bloc["enseigne_signalee"].mean(), 1),
            "stabilite_jaccard": round(stable.get(int(g), np.nan), 2) if g >= 0 else np.nan,
        })
    return pd.DataFrame(lignes)


def resume(nom: str, vecteurs: str, t: pd.DataFrame, groupe: np.ndarray,
           stable: dict[int, float], rng) -> dict:
    m = groupe >= 0
    tailles = np.bincount(groupe[m])
    melange = groupe.copy()
    melange[m] = rng.permutation(groupe[m])
    hasard = purete(t, melange)
    stables = [g for g, j in stable.items() if j >= SEUIL_STABLE]
    enseignes = t["enseigne_signalee"].to_numpy()
    part_ens = pd.Series(enseignes[m]).groupby(groupe[m]).mean()
    groupes_ens = part_ens.index[part_ens >= 0.5]
    return {
        "population": nom, "vecteurs": vecteurs, "n_avis": len(t),
        "n_supprimes": int(t["supprime"].sum()),
        "n_groupes": int(groupe.max() + 1),
        "n_groupes_stables": len(stables) if stable else np.nan,
        "part_sans_groupe_pct": round(100 * (~m).mean(), 1),
        "taille_mediane": int(np.median(tailles)),
        "part_secteur_principal_pct": round(100 * purete(t, groupe), 1),
        "part_secteur_principal_hasard_pct": round(100 * hasard, 1),
        "n_groupes_enseignes_majoritaires": len(groupes_ens),
        "part_avis_enseignes_dans_ces_groupes_pct":
            round(100 * np.isin(groupe[enseignes], groupes_ens).mean(), 1)
            if enseignes.any() else np.nan,
    }


def main() -> int:
    SORTIES.mkdir(parents=True, exist_ok=True)
    df, v = charger()
    rng = np.random.default_rng(20260929)
    resumes, groupes, membres, cases_out = [], [], [], []

    for nom, garde in (("toutes_fiches", np.ones(len(df), bool)),
                       ("sans_enseignes", ~df["enseigne_signalee"].to_numpy())):
        t = df[garde].reset_index(drop=True)
        t["case"] = cases(t)
        x = v[garde]
        r = retirer_cases(x, t["case"])
        cases_out.append(t.groupby("case").agg(n_avis=("supprime", "size"),
                                               n_supprimes=("supprime", "sum"))
                         .reset_index().assign(population=nom))
        journal(f"{nom} : {len(t)} avis, {int(t['supprime'].sum())} supprimés, "
                f"{t['case'].nunique()} cases")

        journal("  vecteurs bruts, graine 0")
        g_brut = regrouper(x, 0)
        resumes.append(resume(nom, "bruts", t, g_brut, {}, rng))

        par_graine = []
        for graine in GRAINES:
            journal(f"  vecteurs corrigés, graine {graine}")
            par_graine.append(regrouper(r, graine))
        stable = stabilite(par_graine[0], par_graine[1:])
        resumes.append(resume(nom, "corriges", t, par_graine[0], stable, rng))

        for vec, g, st in (("bruts", g_brut, {}), ("corriges", par_graine[0], stable)):
            d = decrire(t, g, st, rng)
            d.insert(0, "vecteurs", vec); d.insert(0, "population", nom)
            groupes.append(d)
            membres.append(t[["review_id", "cid", "supprime"]]
                           .assign(population=nom, vecteurs=vec, groupe=g))

    pd.DataFrame(resumes).to_csv(SORTIES / "A1-regroupements.csv", index=False)
    g = pd.concat(groupes, ignore_index=True)
    g.to_csv(SORTIES / "A2-groupes.csv", index=False)
    (pd.concat(membres, ignore_index=True)
     [["population", "vecteurs", "groupe", "review_id", "cid", "supprime"]]
     .to_csv(SORTIES / "A3-appartenance-avis.csv", index=False))
    pd.concat(cases_out, ignore_index=True).to_csv(SORTIES / "A4-cases.csv", index=False)

    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
    print(pd.DataFrame(resumes).to_string(index=False))
    h = g[(g["vecteurs"] == "corriges") & (g["hors_du_hasard"] != "")]
    print(h.to_string(index=False))
    journal("terminé")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
