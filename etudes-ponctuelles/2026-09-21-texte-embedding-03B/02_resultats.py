"""
Premiers resultats sur les vecteurs produits par 01_embedding.py.

Route A : regrouper les avis par ce que leur texte raconte, puis regarder la
          part supprimee de chaque groupe.
Route B : a note et langue egales, mesurer l'ecart entre le centre des textes
          supprimes et le centre des textes restes en ligne, et le comparer a
          ce que donne un tirage au hasard de deux groupes de memes tailles
          dans la meme case.

Les routes C et D sont reportees, cf. la lecture de l'etape 0.

Lecture de la route B. Deux points normalises etant compares par leur produit,
l'ecart entre deux centres se lit directement. Il diminue mecaniquement quand
un des deux groupes est petit, donc il ne veut rien dire tout seul. Le tirage
au hasard donne la valeur qu'on obtiendrait si le sort de l'avis n'avait aucun
rapport avec son texte, sur les memes effectifs. Ce sont les deux qu'il faut
lire ensemble.

Sorties : sorties/2026-09-21-B*.csv et sorties/2026-09-21-C*.csv
Aucun texte, aucun nom d'auteur, aucun lien d'avis.
"""

from __future__ import annotations

import time
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[2]
VECTEURS = RACINE / "data" / "embeddings" / "03B_e5base.parquet"
SORTIES = Path(__file__).resolve().parent / "sorties"
DATE = "2026-09-21"

GRAINE = 20260921
N_TIRAGES = 2000
MIN_SUPPRIMES = 20      # en dessous, la case ne porte rien
K_GROUPES_TOUT = 30
K_GROUPES_CASE = 20
LANGUES_GRANDES = ("en", "fr", "de", "es", "it", "nl")


def journal(message: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {message}", flush=True)


def charger() -> tuple[pd.DataFrame, np.ndarray]:
    df = pd.read_parquet(VECTEURS)
    v = np.vstack(df["vecteur"].to_numpy()).astype("float32")
    df = df.drop(columns=["vecteur"]).reset_index(drop=True)
    df["groupe_langue"] = np.where(df["langue"].isin(LANGUES_GRANDES),
                                   df["langue"], "autres_langues")
    return df, v


# ---------------------------------------------------------------------------
# Route B
# ---------------------------------------------------------------------------

def ecart_centres(v: np.ndarray, masque_a: np.ndarray) -> float:
    """Distance entre le centre du groupe A et le centre du groupe B.

    Les vecteurs sont deja ramenes a la meme echelle. On renvoie 1 moins le
    produit des deux centres remis a l'echelle : 0 si les deux groupes disent
    la meme chose en moyenne, et d'autant plus grand qu'ils s'eloignent.
    """
    a = v[masque_a].mean(axis=0)
    b = v[~masque_a].mean(axis=0)
    a = a / np.linalg.norm(a)
    b = b / np.linalg.norm(b)
    return float(1.0 - a @ b)


def route_b(df: pd.DataFrame, v: np.ndarray, hors_enseignes: bool) -> pd.DataFrame:
    rng = np.random.default_rng(GRAINE)
    sous = df if not hors_enseignes else df[~df["enseigne_signalee"]]
    lignes = []
    for (note, langue), bloc in sous.groupby(["note", "groupe_langue"]):
        n_supp = int(bloc["supprime"].sum())
        if n_supp < MIN_SUPPRIMES:
            continue
        idx = bloc.index.to_numpy()
        vv = v[idx]
        masque = bloc["supprime"].to_numpy()
        observe = ecart_centres(vv, masque)

        n = len(idx)
        tirages = np.empty(N_TIRAGES, dtype="float64")
        for t in range(N_TIRAGES):
            faux = np.zeros(n, dtype=bool)
            faux[rng.choice(n, n_supp, replace=False)] = True
            tirages[t] = ecart_centres(vv, faux)

        bas, haut = np.percentile(tirages, [2.5, 97.5])
        lignes.append({
            "perimetre": "sans_enseignes" if hors_enseignes else "complet",
            "note": int(note),
            "langue": langue,
            "n_supprimes": n_supp,
            "n_restes": n - n_supp,
            "ecart_observe": round(observe, 4),
            "hasard_moyen": round(float(tirages.mean()), 4),
            "hasard_borne_basse": round(float(bas), 4),
            "hasard_borne_haute": round(float(haut), 4),
            "au_dessus_du_hasard": bool(observe > haut),
            "rapport_observe_sur_hasard": round(observe / tirages.mean(), 2),
        })
    return pd.DataFrame(lignes)


# ---------------------------------------------------------------------------
# Route A
# ---------------------------------------------------------------------------

def decrire_groupes(df: pd.DataFrame, etiquettes: np.ndarray) -> pd.DataFrame:
    t = df.copy()
    t["groupe"] = etiquettes
    agg = t.groupby("groupe").agg(
        n_avis=("review_id", "size"),
        n_supprimes=("supprime", "sum"),
        n_fiches=("cid", "nunique"),
        note_moyenne=("note", "mean"),
        longueur_mediane=("n_caracteres", "median"),
    ).reset_index()
    agg["part_supprimee_pct"] = (100 * agg["n_supprimes"] / agg["n_avis"]).round(2)
    agg["note_moyenne"] = agg["note_moyenne"].round(2)

    dominante = (t.groupby(["groupe", "langue"]).size().reset_index(name="n")
                 .sort_values(["groupe", "n"], ascending=[True, False])
                 .groupby("groupe").first().reset_index())
    agg = agg.merge(dominante[["groupe", "langue"]], on="groupe")
    agg = agg.rename(columns={"langue": "langue_dominante"})

    part5 = t.groupby("groupe")["note"].apply(lambda s: 100 * (s == 5).mean()).round(1)
    agg["part_5_etoiles_pct"] = agg["groupe"].map(part5)

    # Part du groupe portee par les enseignes signalees. Sans cette colonne, un
    # groupe tres supprime peut n'etre qu'une enseigne.
    part_ens = t.groupby("groupe")["enseigne_signalee"].apply(lambda s: 100 * s.mean()).round(1)
    agg["part_enseignes_pct"] = agg["groupe"].map(part_ens)
    return agg.sort_values("part_supprimee_pct", ascending=False).reset_index(drop=True)


def route_a(df: pd.DataFrame, v: np.ndarray, masque: np.ndarray, k: int,
            etiquette: str) -> pd.DataFrame:
    from sklearn.cluster import KMeans
    idx = np.where(masque)[0]
    journal(f"route A, {etiquette} : {len(idx)} textes, {k} groupes")
    km = KMeans(n_clusters=k, n_init=10, random_state=GRAINE)
    labels = km.fit_predict(v[idx])
    out = decrire_groupes(df.iloc[idx], labels)
    out.insert(0, "population", etiquette)
    return out


def main() -> None:
    SORTIES.mkdir(parents=True, exist_ok=True)
    journal("lecture des vecteurs")
    df, v = charger()
    journal(f"{len(df)} vecteurs, {v.shape[1]} dimensions")

    journal(f"route B : {N_TIRAGES} tirages par case")
    b = pd.concat([route_b(df, v, False), route_b(df, v, True)], ignore_index=True)
    b.to_csv(SORTIES / f"{DATE}-B1-ecart-centres.csv", index=False)
    print("\n===== B1 : ecart entre les deux populations, a note et langue egales =====")
    print(b.to_string(index=False))

    hors = (~df["enseigne_signalee"]).to_numpy()
    cas_en5 = hors & (df["note"] == 5).to_numpy() & (df["langue"] == "en").to_numpy()
    cas_en1 = hors & (df["note"] == 1).to_numpy() & (df["langue"] == "en").to_numpy()

    a = pd.concat([
        route_a(df, v, np.ones(len(df), dtype=bool), K_GROUPES_TOUT, "tout_le_panel"),
        route_a(df, v, hors, K_GROUPES_TOUT, "hors_enseignes"),
        route_a(df, v, cas_en5, K_GROUPES_CASE, "5_etoiles_anglais_hors_enseignes"),
        route_a(df, v, cas_en1, K_GROUPES_CASE, "1_etoile_anglais_hors_enseignes"),
    ], ignore_index=True)
    a.to_csv(SORTIES / f"{DATE}-C1-groupes-de-textes.csv", index=False)

    for pop in a["population"].unique():
        print(f"\n===== C1 : groupes de textes, {pop} (10 premiers) =====")
        print(a[a["population"] == pop].head(10).to_string(index=False))


if __name__ == "__main__":
    main()
