"""
Etape 3 : quel avis appartient a quel groupe de textes, pour les deux
regroupements de la figure 9 du rapport.

    python etudes-ponctuelles/2026-09-21-texte-embedding-03B/03_appartenance_groupes.py

`02_resultats.py` regroupe les avis (route A) mais n'ecrit que le resume par
groupe, `C1-groupes-de-textes.csv`. On y lit qu'un groupe compte 75 avis dont
14 supprimes, sans savoir lesquels. Ce script refait les deux regroupements
utilises par la figure 9 et ecrit l'appartenance de chaque avis.

Populations, identiques a 02_resultats.py :
  1_etoile_anglais_hors_enseignes     1 114 avis, 20 groupes
  5_etoiles_anglais_hors_enseignes   12 042 avis, 20 groupes
Les deux regroupements a 30 groupes (tout le panel, hors enseignes) ne sont
pas repris : la figure 9 ne les utilise pas.

Le regroupement doit etre celui de 02_resultats.py, a l'identique. Le script
utilise scikit-learn quand il se charge. Sur le poste Windows du 2026-09-25,
scipy est bloque par la politique de securite ; le script bascule alors sur une
reecriture numpy du KMeans de scikit-learn 1.9 (initialisation k-means++, meme
graine, 10 departs, iterations de Lloyd). Dans les deux cas, il compare ses
effectifs et ses suppressions par groupe a C1 et s'arrete si un seul differe.
Verifie le 2026-09-25 : les 40 groupes retombent exactement sur C1.

Etiquettes : etablies le 2026-09-25 en lisant des textes de chaque groupe
(mots caracteristiques, 10 textes tires au hasard, jusqu'a 10 textes
supprimes). Seuls les 14 groupes de la figure 9 ont ete lus. Les autres
gardent leur numero et une etiquette vide.

Sortie : sorties/2026-09-25-C2-appartenance-avis.csv
  review_id, cid, population, groupe, etiquette, note, supprime, n_caracteres
Aucun texte, aucun nom d'auteur, aucun lien d'avis.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[2]
VECTEURS = RACINE / "data" / "embeddings" / "03B_e5base.parquet"
SORTIES = Path(__file__).resolve().parent / "sorties"
C1 = SORTIES / "2026-09-21-C1-groupes-de-textes.csv"
SORTIE = SORTIES / "2026-09-25-C2-appartenance-avis.csv"

GRAINE = 20260921        # celle de 02_resultats.py
K_GROUPES_CASE = 20      # idem
N_DEPARTS = 10           # idem

POPULATIONS = {
    "1_etoile_anglais_hors_enseignes": 1,
    "5_etoiles_anglais_hors_enseignes": 5,
}

# (population, groupe) -> etiquette. Les 14 groupes de la figure 9.
ETIQUETTES = {
    ("1_etoile_anglais_hors_enseignes", 0): "Équipements en panne (climatisation, casiers, machines)",
    ("1_etoile_anglais_hors_enseignes", 11): "Location de voiture : frais imposés, arnaque dénoncée",
    ("1_etoile_anglais_hors_enseignes", 14): "Location de voiture à l'aéroport : attente, surfacturation",
    ("1_etoile_anglais_hors_enseignes", 17): "Conflits avec le personnel ou la sécurité",
    ("1_etoile_anglais_hors_enseignes", 5): "Urgences vétérinaires et soins médicaux",
    ("1_etoile_anglais_hors_enseignes", 19): "Restaurant : service et plats",
    ("1_etoile_anglais_hors_enseignes", 7): "Loisirs et hébergement : accueil, organisation",
    ("5_etoiles_anglais_hors_enseignes", 2): "Éloges très courts et génériques",
    ("5_etoiles_anglais_hors_enseignes", 1): "Soins : esthétique, dentaire, massage",
    ("5_etoiles_anglais_hors_enseignes", 3): "Interventions à domicile (garage, climatisation, nuisibles)",
    ("5_etoiles_anglais_hors_enseignes", 15): "Employé nommé, serviable et compétent",
    ("5_etoiles_anglais_hors_enseignes", 10): "Activités de loisirs : croisières, visites, tyrolienne",
    ("5_etoiles_anglais_hors_enseignes", 14): "Éloges courts sur un lieu (restaurant, bar, chambre)",
    ("5_etoiles_anglais_hors_enseignes", 0): "Avis détaillés de séjour (hôtel, camping)",
}


# ---------------------------------------------------------------------------
# KMeans : scikit-learn si disponible, sinon sa reecriture numpy
# ---------------------------------------------------------------------------

def _distances_upcast(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Distances au carre calculees en float64 et rendues en float32, comme
    scikit-learn le fait pour des donnees float32."""
    a64, b64 = a.astype(np.float64), b.astype(np.float64)
    d = (a64 ** 2).sum(1)[:, None] - 2 * a64 @ b64.T + (b64 ** 2).sum(1)[None, :]
    d = d.astype(np.float32)
    np.maximum(d, 0, out=d)
    return d


def _kmeans_plusplus(x: np.ndarray, k: int, rs: np.random.RandomState) -> np.ndarray:
    n = x.shape[0]
    poids = np.ones(n, dtype=x.dtype)
    essais = 2 + int(np.log(k))
    centres = np.empty((k, x.shape[1]), dtype=x.dtype)
    premier = rs.choice(n, p=poids / poids.sum())
    centres[0] = x[premier]
    proche = _distances_upcast(x[[premier]], x)[0]
    potentiel = proche @ poids
    for c in range(1, k):
        tirages = rs.uniform(size=essais) * potentiel
        candidats = np.searchsorted(np.cumsum(poids * proche, dtype=np.float64), tirages)
        np.clip(candidats, None, proche.size - 1, out=candidats)
        d = _distances_upcast(x[candidats], x)
        np.minimum(proche, d, out=d)
        potentiels = d @ poids.reshape(-1, 1)
        meilleur = np.argmin(potentiels)
        potentiel = potentiels[meilleur]
        proche = d[meilleur]
        centres[c] = x[candidats[meilleur]]
    return centres


def _lloyd(x: np.ndarray, centres: np.ndarray, tol: float, max_iter: int = 300):
    avant = np.full(x.shape[0], -1)
    for _ in range(max_iter):
        labels = (-2 * x @ centres.T + (centres ** 2).sum(1)[None, :]).argmin(1)
        nouveaux = np.zeros_like(centres)
        for j in range(centres.shape[0]):
            m = labels == j
            nouveaux[j] = x[m].mean(0) if m.any() else centres[j]
        deplacement = ((nouveaux - centres) ** 2).sum()
        centres = nouveaux
        if (labels == avant).all() or deplacement <= tol:
            break
        avant = labels
    labels = (-2 * x @ centres.T + (centres ** 2).sum(1)[None, :]).argmin(1)
    inertie = ((x - centres[labels]) ** 2).sum(dtype=np.float64)
    return labels, inertie


def _kmeans_numpy(v: np.ndarray, k: int) -> np.ndarray:
    x = v - v.mean(axis=0)
    tol = np.mean(np.var(x, axis=0)) * 1e-4
    rs = np.random.RandomState(GRAINE)
    meilleur = None
    for _ in range(N_DEPARTS):
        labels, inertie = _lloyd(x, _kmeans_plusplus(x, k, rs), tol)
        if meilleur is None or inertie < meilleur[1]:
            meilleur = (labels, inertie)
    return meilleur[0]


def regrouper(v: np.ndarray, k: int) -> np.ndarray:
    try:
        from sklearn.cluster import KMeans
    except ImportError:
        print("  scikit-learn indisponible : reecriture numpy")
        return _kmeans_numpy(v, k)
    return KMeans(n_clusters=k, n_init=N_DEPARTS, random_state=GRAINE).fit_predict(v)


# ---------------------------------------------------------------------------

def main() -> int:
    df = pd.read_parquet(VECTEURS)
    v = np.vstack(df["vecteur"].to_numpy()).astype("float32")
    df = df.drop(columns=["vecteur"]).reset_index(drop=True)
    c1 = pd.read_csv(C1)

    hors = ~df["enseigne_signalee"]
    morceaux = []
    for population, note in POPULATIONS.items():
        masque = (hors & (df["note"] == note) & (df["langue"] == "en")).to_numpy()
        idx = np.where(masque)[0]
        print(f"{population} : {len(idx)} avis, {K_GROUPES_CASE} groupes")
        sous = df.iloc[idx][["review_id", "cid", "note", "supprime", "n_caracteres"]].copy()
        sous["groupe"] = regrouper(v[idx], K_GROUPES_CASE)
        sous["population"] = population

        # Controle : les effectifs doivent etre ceux de C1, groupe par groupe.
        attendu = (c1[c1["population"] == population]
                   .set_index("groupe")[["n_avis", "n_supprimes"]].sort_index())
        obtenu = (sous.groupby("groupe")
                  .agg(n_avis=("review_id", "size"), n_supprimes=("supprime", "sum"))
                  .sort_index().astype(attendu.dtypes.to_dict()))
        if not attendu.equals(obtenu):
            print("ARRET : les groupes different de C1.")
            print(pd.concat([attendu, obtenu], axis=1, keys=["C1", "ici"]).to_string())
            return 1
        print("  identique a C1")
        morceaux.append(sous)

    out = pd.concat(morceaux, ignore_index=True)
    out["etiquette"] = [ETIQUETTES.get((p, int(g)), "")
                        for p, g in zip(out["population"], out["groupe"])]
    out = out[["review_id", "cid", "population", "groupe", "etiquette", "note",
               "supprime", "n_caracteres"]].sort_values(["population", "groupe", "review_id"])
    out.to_csv(SORTIE, index=False, encoding="utf-8")
    print(f"ecrit : {SORTIE.name}, {len(out)} lignes, "
          f"{(out['etiquette'] != '').sum()} avis dans un groupe etiquete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
