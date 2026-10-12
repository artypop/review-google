#!/usr/bin/env python3
"""Les avis supprimés des antiparasitaires forment-ils un groupe de textes à part ?

    PYTHONPATH=.venv/Lib/site-packages <python uv> etudes-ponctuelles/2026-09-30-avis-antiparasitaires/calcul_regroupement.py

Demande de Matthieu du 2026-09-30 : refaire le zoom home services du
2026-09-29 sur tous les avis des fiches antiparasitaires américaines.

------------------------------------------------------------------------------
LES DONNÉES
------------------------------------------------------------------------------
  avis      data/local/reviews_pest_all.parquet (extraire.py) : 174 fiches US
            home_services (« pest » dans le nom, plus Bulwark Exterminating),
            259 901 avis avec texte, 1 086 supprimés pendant le suivi du 11 au
            24 août 2026.
  vecteurs  data/embeddings/pest_e5base.parquet, calculés sur Colab le
            2026-09-30 (colab_embedding.ipynb), contrôlés par verifier_colab.py.

Seuls les avis 5 étoiles sont gardés : ils portent 1 035 des 1 086
suppressions ; les autres notes en ont 51 à elles toutes.

------------------------------------------------------------------------------
L'ÂGE DE L'AVIS
------------------------------------------------------------------------------
Le taux de suppression va de 12 % (avis publiés en août 2026) à 0,06 % (avant
2023). Sans contrôle, un groupe d'avis récents paraîtrait isoler les
suppressions. Huit périodes de publication : août, juillet, juin, janvier à
mai 2026, puis 2025, 2024, 2023, avant 2023.
  attendus            somme, sur les avis du groupe, du taux de suppression
                      de leur période
  hasard à période    étiquettes « supprimé » redistribuées entre avis de la
  égale               même période, 2 000 fois
  hasard à fiche      redistribuées entre avis de la même fiche et de la même
  égale               période : chaque fiche garde ses suppressions de chaque
                      période

------------------------------------------------------------------------------
LES DEUX POPULATIONS
------------------------------------------------------------------------------
  cinq_etoiles           tous les avis 5 étoiles ; KMeans K = 2 à 10 sur l'ACP
                         à 50 dimensions
  cinq_etoiles_recents   avis 5 étoiles publiés depuis le 1er juin 2026 ; les
                         mêmes KMeans, HDBSCAN (t-SNE, sélection « leaf »,
                         30 avis au moins, 10 voisins, réglage du 29/09) et
                         les 10 voisins de texte pris hors de la fiche

------------------------------------------------------------------------------
LES MESURES
------------------------------------------------------------------------------
Par groupe : avis, supprimés, part supprimée, attendus, seuils des deux
hasards (97,5 %), fiches touchées, part des suppressions sur la fiche la plus
touchée, longueur médiane, part des avis d'août 2026, part de chaque chaîne.
Par découpage : excès du groupe le plus supprimé (supprimés − attendus) et sa
place dans les deux tirages ; part supprimée du groupe le plus « pur ».
Voisins : part de supprimés parmi les voisins d'un supprimé, moins celle
parmi les voisins d'un resté.

Sorties : `sorties/regroupement/*.csv`, identifiants seulement.
"""
from __future__ import annotations

import csv
import sys
import time
import warnings
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq
from sklearn.cluster import HDBSCAN, KMeans
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.neighbors import NearestNeighbors

warnings.filterwarnings("ignore", category=FutureWarning)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DOSSIER = Path(__file__).resolve().parent
RACINE = DOSSIER.parents[1]
SORTIES = DOSSIER / "sorties" / "regroupement"
AVIS = RACINE / "data" / "local" / "reviews_pest_all.parquet"
VECTEURS = RACINE / "data" / "embeddings" / "pest_e5base.parquet"

GRAINE = 20260930
N_TIRAGES = 2000
VALEURS_K = range(2, 11)
N_ACP = 50
N_VOISINS = 10
SEUIL = 97.5
RECENTS_DEPUIS = datetime(2026, 6, 1, tzinfo=timezone.utc)
PERIODES = [(datetime(2026, 8, 1, tzinfo=timezone.utc), "août 2026"),
            (datetime(2026, 7, 1, tzinfo=timezone.utc), "juillet 2026"),
            (datetime(2026, 6, 1, tzinfo=timezone.utc), "juin 2026"),
            (datetime(2026, 1, 1, tzinfo=timezone.utc), "janvier à mai 2026"),
            (datetime(2025, 1, 1, tzinfo=timezone.utc), "2025"),
            (datetime(2024, 1, 1, tzinfo=timezone.utc), "2024"),
            (datetime(2023, 1, 1, tzinfo=timezone.utc), "2023"),
            (datetime(1990, 1, 1, tzinfo=timezone.utc), "avant 2023")]
CHAINES = {"ecoshield pest": "EcoShield", "insight pest": "Insight",
           "pointe pest control": "Pointe", "bulwark exterminating": "Bulwark"}


def journal(message):
    print(f"[{time.strftime('%H:%M:%S')}] {message}", flush=True)


def charger():
    a = pq.read_table(AVIS, columns=["review_id", "cid", "star", "created_at",
                                     "deleted_detected_at", "business_name", "text"])
    v = pq.read_table(VECTEURS)
    rang = {r: i for i, r in enumerate(v.column("review_id").to_pylist())}
    ids = a.column("review_id").to_pylist()
    idx = np.array([rang[r] for r in ids])
    col = v.column("vecteur").combine_chunks()
    vec = col.flatten().to_numpy(zero_copy_only=False).reshape(len(col), -1)
    cree = a.column("created_at").to_pylist()
    periode = np.array([next(k for k, (borne, _) in enumerate(PERIODES) if c >= borne)
                        for c in cree])
    nom = [(n or "").lower() for n in a.column("business_name").to_pylist()]
    chaine = np.array([next((c for p, c in CHAINES.items() if n.startswith(p)), "autres")
                       for n in nom])
    d = {"review_id": np.array(ids), "cid": np.array(a.column("cid").to_pylist()),
         "note": np.array(a.column("star").to_pylist()),
         "supprime": np.array([x is not None for x in a.column("deleted_detected_at").to_pylist()]),
         "periode": periode, "recent": np.array([c >= RECENTS_DEPUIS for c in cree]),
         "chaine": chaine,
         "longueur": np.array([len((t or "").strip()) for t in a.column("text").to_pylist()])}
    return d, vec, idx


def sous(d, m):
    return {k: x[m] for k, x in d.items()}


def codes(*colonnes):
    return np.unique(np.array(["|".join(map(str, t)) for t in zip(*colonnes)]),
                     return_inverse=True)[1]


def tirages(supp, strate, rng):
    """N_TIRAGES jeux d'indices « supprimés », redistribués dans chaque strate.
    Trier par (strate, clé au hasard) et prendre, dans chaque strate, autant
    d'avis qu'elle compte de suppressions."""
    ordre_fixe = np.argsort(strate, kind="stable")
    strate_triee = strate[ordre_fixe]
    debut = np.searchsorted(strate_triee, np.arange(strate.max() + 1))
    rang = np.arange(len(strate)) - debut[strate_triee]
    k = np.bincount(strate, weights=supp.astype(float), minlength=strate.max() + 1).astype(int)
    garde = rang < k[strate_triee]
    out = np.empty((N_TIRAGES, int(supp.sum())), dtype=np.int64)
    for i in range(N_TIRAGES):
        out[i] = np.lexsort((rng.random(len(strate)), strate))[garde]
    return out


def compter(groupe, indices, n_g):
    return np.stack([np.bincount(groupe[t], minlength=n_g) for t in indices])


def rang_pct(observe, valeurs):
    return round(100 * float((valeurs < observe).mean()), 1)


def decrire(nom, methode, k, g, d, taux, t_per, t_fic):
    g2 = np.where(g < 0, g.max() + 1, g)
    n_g = g2.max() + 1
    supp = d["supprime"]
    obs = np.bincount(g2, weights=supp.astype(float), minlength=n_g)
    att = np.bincount(g2, weights=taux, minlength=n_g)
    sim_p, sim_f = compter(g2, t_per, n_g), compter(g2, t_fic, n_g)
    exces = float((obs - att).max())
    parts = obs / np.bincount(g2, minlength=n_g)
    resume = {"population": nom, "methode": methode, "k": k, "n_groupes": int(g.max() + 1),
              "avis": len(g), "supprimes": int(supp.sum()),
              "part_supprimee_pct": round(100 * supp.mean(), 2),
              "part_hors_groupe_pct": round(100 * (g < 0).mean(), 1),
              "exces_du_pire": round(exces, 1),
              "rang_periode_pct": rang_pct(exces, (sim_p - att).max(axis=1)),
              "rang_fiche_pct": rang_pct(exces, (sim_f - att).max(axis=1)),
              "part_supprimee_max_pct": round(100 * float(parts[:g.max() + 1].max()), 2)}
    lignes = []
    for x in range(n_g):
        m = g2 == x
        s = supp[m]
        fs = np.unique(d["cid"][m][s], return_counts=True)[1]
        ligne = {"population": nom, "methode": methode, "k": k,
                 "groupe": -1 if (g < 0).any() and x == n_g - 1 else x,
                 "avis": int(m.sum()), "supprimes": int(s.sum()),
                 "part_supprimee_pct": round(100 * s.mean(), 2),
                 "attendus": round(float(att[x]), 1),
                 "seuil_periode": int(np.percentile(sim_p[:, x], SEUIL)),
                 "seuil_fiche": int(np.percentile(sim_f[:, x], SEUIL)),
                 "fiches_touchees": len(fs),
                 "part_fiche_la_plus_touchee_pct": round(100 * fs.max() / s.sum(), 1) if s.sum() else "",
                 "longueur_mediane": int(np.median(d["longueur"][m])),
                 "part_aout_2026_pct": round(100 * (d["periode"][m] == 0).mean(), 1)}
        for c in list(CHAINES.values()) + ["autres"]:
            ligne[f"part_{c}_pct"] = round(100 * (d["chaine"][m] == c).mean(), 1)
        lignes.append(ligne)
    return resume, lignes


def voisins(z, cid):
    nn = NearestNeighbors(n_neighbors=min(len(z), 300), metric="cosine").fit(z)
    ind = nn.kneighbors(z, return_distance=False)
    out = np.empty((len(z), N_VOISINS), dtype=int)
    for i, ligne in enumerate(ind):
        autres = ligne[cid[ligne] != cid[i]][:N_VOISINS]
        if len(autres) < N_VOISINS:
            raise SystemExit(f"avis {i} : moins de {N_VOISINS} voisins hors fiche parmi 300")
        out[i] = autres
    return out


def ecart_voisins(nb, supp):
    part = supp[nb].mean(axis=1)
    return float(part[supp].mean() - part[~supp].mean())


def ecrire(chemin, lignes):
    with chemin.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(lignes[0]))
        w.writeheader(); w.writerows(lignes)


def main() -> int:
    SORTIES.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(GRAINE)
    journal("lecture")
    d0, vec, idx = charger()
    cinq = d0["note"] == 5
    resumes, groupes, membres, vois, periodes = [], [], [], [], []

    for nom, masque in (("cinq_etoiles", cinq), ("cinq_etoiles_recents", cinq & d0["recent"])):
        d = sous(d0, masque)
        v = vec[idx[masque]].astype("float32")
        supp = d["supprime"]
        taux_p = np.array([supp[d["periode"] == p].mean() if (d["periode"] == p).any() else 0
                           for p in range(len(PERIODES))])
        taux = taux_p[d["periode"]]
        for p, (_, lib) in enumerate(PERIODES):
            m = d["periode"] == p
            if m.any():
                periodes.append({"population": nom, "periode": lib, "avis": int(m.sum()),
                                 "supprimes": int(supp[m].sum()),
                                 "part_supprimee_pct": round(100 * supp[m].mean(), 2)})
        journal(f"{nom} : {len(supp)} avis, {int(supp.sum())} supprimés ; tirages")
        t_per = tirages(supp, d["periode"], rng)
        t_fic = tirages(supp, codes(d["cid"], d["periode"]), rng)
        journal("  ACP")
        z = PCA(N_ACP, random_state=0).fit_transform(v)
        decoupages = []
        for k in VALEURS_K:
            decoupages.append(("kmeans", k, KMeans(k, n_init=10, random_state=0).fit_predict(z)))
            journal(f"  KMeans {k}")
        if nom == "cinq_etoiles_recents":
            carte = TSNE(2, perplexity=30, init="pca", random_state=0, n_jobs=6).fit_transform(z)
            decoupages.append(("hdbscan", "", HDBSCAN(min_cluster_size=30, min_samples=10,
                                                      cluster_selection_method="leaf",
                                                      copy=True).fit_predict(carte)))
            journal("  HDBSCAN")
        for methode, k, g in decoupages:
            r, lignes = decrire(nom, methode, k, g, d, taux, t_per, t_fic)
            resumes.append(r); groupes += lignes
            membres += [{"population": nom, "methode": methode, "k": k, "groupe": int(x),
                         "review_id": rid, "cid": c, "supprime": bool(s)}
                        for x, rid, c, s in zip(g, d["review_id"], d["cid"], supp)]
            journal(f"  {methode} {k} : excès {r['exces_du_pire']}, rang période "
                    f"{r['rang_periode_pct']} %, fiche {r['rang_fiche_pct']} %, "
                    f"part max {r['part_supprimee_max_pct']} %")
        if nom == "cinq_etoiles_recents":
            nb = voisins(v, d["cid"])
            obs = ecart_voisins(nb, supp)
            def etiquettes(t):
                e = np.zeros(len(supp), bool); e[t] = True; return e
            sp = np.array([ecart_voisins(nb, etiquettes(t)) for t in t_per])
            sf = np.array([ecart_voisins(nb, etiquettes(t)) for t in t_fic])
            part = supp[nb].mean(axis=1)
            vois.append({"population": nom, "avis": len(supp), "supprimes": int(supp.sum()),
                         "voisins_supprimes_si_supprime_pct": round(100 * part[supp].mean(), 2),
                         "voisins_supprimes_si_reste_pct": round(100 * part[~supp].mean(), 2),
                         "ecart_points": round(100 * obs, 2),
                         "hasard_periode_points": round(100 * sp.mean(), 2),
                         "rang_periode_pct": rang_pct(obs, sp),
                         "hasard_fiche_points": round(100 * sf.mean(), 2),
                         "rang_fiche_pct": rang_pct(obs, sf)})
            journal(f"  voisins : {vois[-1]}")

    ecrire(SORTIES / "A1-decoupages.csv", resumes)
    ecrire(SORTIES / "A2-groupes.csv", groupes)
    ecrire(SORTIES / "A3-appartenance-avis.csv", membres)
    ecrire(SORTIES / "A4-periodes.csv", periodes)
    ecrire(SORTIES / "B1-voisins.csv", vois)
    journal("terminé")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
