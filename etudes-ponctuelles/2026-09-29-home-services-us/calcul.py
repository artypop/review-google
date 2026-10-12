#!/usr/bin/env python3
"""Les avis supprimés s'isolent-ils dans une catégorie de textes ? Home services US.

    PYTHONPATH=.venv/Lib/site-packages <python uv> etudes-ponctuelles/2026-09-29-home-services-us/calcul.py

Demande de Matthieu du 2026-09-29. Écrit sans pandas : depuis le 2026-09-29
vers 12h44, la règle Windows de contrôle des applications bloque le lanceur
`.venv/Scripts/python.exe` et la bibliothèque `pyarrow.compute`, dont pandas
dépend. Lancer l'interpréteur uv avec `PYTHONPATH` pointé sur le `.venv`.

------------------------------------------------------------------------------
LA POPULATION
------------------------------------------------------------------------------
Fiches américaines (`businesses.country = 'US'`), secteur `home_services`, avis
en anglais avec texte. Vecteurs e5-base bruts (`data/embeddings/03B_e5base.parquet`) :
un seul secteur, donc rien à retirer. Quatre populations :
  tous_home_services            toutes les fiches, les quatre chaînes
                                antiparasitaires américaines comprises
                                (population principale, demande du 2026-09-30)
  sans_chaines                  sans les quatre chaînes (`chaine_us` des
                                vecteurs, repérées sur le début du nom)
  ..._5_etoiles                 les mêmes réduites aux avis 5 étoiles
Les deux salles de sport espagnoles ne sont pas en home services : aucun de
leurs avis n'entre ici. Le découpage des populations toutes notes mélange les
notes et fait un groupe des plaintes ; les 5 étoiles seules vérifient que le
résultat tient à note unique.

------------------------------------------------------------------------------
LES CATÉGORIES
------------------------------------------------------------------------------
  KMeans     K = 2 à 10, sur l'ACP à 50 dimensions des vecteurs. Chaque avis
             est rangé dans un groupe.
  HDBSCAN    sélection « leaf », 30 avis au moins, 10 voisins, sur une carte
             t-SNE à 2 dimensions (perplexité 30, départ ACP). Les avis isolés
             restent hors groupe ; ils forment une ligne à part.

------------------------------------------------------------------------------
LA MESURE
------------------------------------------------------------------------------
Attendus d'un groupe : somme, sur ses avis, du taux de suppression de leur
note (1 à 5) dans la population.

Corrigé le 2026-09-29 : la première version regroupait les notes 2 à 4,
choix repris de l'étude sur tous les secteurs sans revérification. Dans ce
sous-ensemble, les avis 4 étoiles sont supprimés à 15 %, contre environ 5 %
pour les autres notes. L'effet du regroupement sur les attendus est faible
(éloges courts, K = 4 : 19,7 attendues avant, 20,3 après) ; les populations
5 étoiles seules mesurent ce qui tient aux autres notes.

Deux mesures par découpage :
  écart global    somme sur les groupes de (supprimés − attendus)² / attendus :
                  grande si les suppressions se répartissent inégalement
  excès du pire   supprimés − attendus du groupe qui en a le plus

Chacune est comparée à 2 000 tirages de deux sortes :
  à note égale    les étiquettes « supprimé » sont mélangées entre avis de même
                  note
  à fiche égale   mélangées entre avis de même fiche et même note.
                  Chaque fiche garde son nombre de suppressions. Les avis d'une
                  fiche se ressemblent (même métier, mêmes prénoms) : sans ce
                  tirage, un effet de fiche passerait pour un effet de texte.
Part des tirages qui font moins que l'observé : au-dessus de 97,5 %, le
découpage isole les suppressions plus que ce tirage.

------------------------------------------------------------------------------
LE COMPLÉMENT SANS CATÉGORIES
------------------------------------------------------------------------------
Pour chaque avis, ses 10 voisins de texte les plus proches (similarité cosinus)
pris hors de sa propre fiche. Mesure : part de supprimés parmi les voisins
d'un avis supprimé, moins la même part pour un avis resté. Mêmes tirages.

Contrôle de longueur (C1) : dans le groupe le plus supprimé de K = 4, part
supprimée des textes de moins de 60 caractères, comparée aux textes courts des
autres groupes.

Sorties : `sorties/*.csv`, identifiants seulement, aucun texte, aucun nom
d'auteur, aucun lien d'avis.
"""
from __future__ import annotations

import csv
import time
import warnings
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq
from sklearn.cluster import HDBSCAN, KMeans
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.neighbors import NearestNeighbors

warnings.filterwarnings("ignore", category=FutureWarning)

DOSSIER = Path(__file__).resolve().parent
RACINE = DOSSIER.parents[1]
SORTIES = DOSSIER / "sorties"
VECTEURS = RACINE / "data" / "embeddings" / "03B_e5base.parquet"
BUSINESSES = RACINE / "data" / "bigquery" / "businesses.parquet"

GRAINE = 20260929
N_TIRAGES = 2000
VALEURS_K = range(2, 11)
N_ACP = 50
N_VOISINS = 10
COURT = 60  # caractères : seuil « texte court » du contrôle de longueur


def journal(message: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {message}", flush=True)


def colonne(t, nom):
    return t.column(nom).to_numpy(zero_copy_only=False)


def charger() -> tuple[dict, np.ndarray]:
    t = pq.read_table(VECTEURS)
    b = pq.read_table(BUSINESSES, columns=["cid", "country", "industry"])
    pays = dict(zip(colonne(b, "cid"), colonne(b, "country")))
    secteur = dict(zip(colonne(b, "cid"), colonne(b, "industry")))
    cid = colonne(t, "cid")
    garde = ((colonne(t, "langue") == "en")
             & np.array([pays.get(c) == "US" and secteur.get(c) == "home_services" for c in cid]))
    idx = np.where(garde)[0]
    vec = t.column("vecteur").combine_chunks()
    v = vec.flatten().to_numpy(zero_copy_only=False).reshape(len(vec), -1)[idx].astype("float32")
    d = {n: colonne(t, n)[idx] for n in ("review_id", "cid", "note", "supprime",
                                         "chaine_us", "n_caracteres")}
    return d, v


def sous(d: dict, masque: np.ndarray) -> dict:
    return {k: x[masque] for k, x in d.items()}


def codes(*colonnes) -> np.ndarray:
    cle = np.array(["|".join(map(str, t)) for t in zip(*colonnes)])
    return np.unique(cle, return_inverse=True)[1]


def tirages(supp: np.ndarray, code: np.ndarray, rng) -> np.ndarray:
    """N_TIRAGES mélanges de `supp` à l'intérieur de chaque valeur de `code`."""
    base = np.argsort(code, kind="stable")
    out = np.empty((N_TIRAGES, len(supp)), dtype=bool)
    for i in range(N_TIRAGES):
        o = np.lexsort((rng.random(len(supp)), code))
        out[i, base] = supp[o]
    return out


def mesures(groupe: np.ndarray, supp: np.ndarray, att: np.ndarray) -> tuple[float, float]:
    obs = np.bincount(groupe, weights=supp.astype(float), minlength=len(att))
    garde = att > 0
    ecart = float((((obs - att) ** 2)[garde] / att[garde]).sum())
    return ecart, float((obs - att).max())


def rang(observe: float, valeurs: np.ndarray) -> float:
    return round(100 * float((valeurs < observe).mean()), 1)


def decrire(nom, methode, k, g, d, taux, t_note, t_fiche):
    """`g` : numéro de groupe, −1 hors groupe (HDBSCAN)."""
    supp = d["supprime"]
    g2 = np.where(g < 0, g.max() + 1, g)           # hors groupe en dernier
    n_g = g2.max() + 1
    att = np.bincount(g2, weights=taux, minlength=n_g)
    ecart, exces = mesures(g2, supp, att)
    sim_note = np.array([mesures(g2, s, att) for s in t_note])
    sim_fiche = np.array([mesures(g2, s, att) for s in t_fiche])
    resume = {
        "population": nom, "methode": methode, "k": k,
        "n_groupes": int(g.max() + 1), "part_hors_groupe_pct": round(100 * (g < 0).mean(), 1),
        "ecart_global": round(ecart, 1),
        "ecart_global_rang_note_pct": rang(ecart, sim_note[:, 0]),
        "ecart_global_rang_fiche_pct": rang(ecart, sim_fiche[:, 0]),
        "exces_du_pire": round(exces, 1),
        "exces_du_pire_hasard_note_moyen": round(float(sim_note[:, 1].mean()), 1),
        "exces_du_pire_rang_note_pct": rang(exces, sim_note[:, 1]),
        "exces_du_pire_hasard_fiche_moyen": round(float(sim_fiche[:, 1].mean()), 1),
        "exces_du_pire_rang_fiche_pct": rang(exces, sim_fiche[:, 1]),
    }
    lignes = []
    for x in range(n_g):
        m = g2 == x
        s = supp[m]
        fiches_supp = np.unique(d["cid"][m][s], return_counts=True)[1]
        obs_note = t_note[:, m].sum(axis=1)
        obs_fiche = t_fiche[:, m].sum(axis=1)
        lignes.append({
            "population": nom, "methode": methode, "k": k,
            "groupe": -1 if (g < 0).any() and x == n_g - 1 else x,
            "n_avis": int(m.sum()), "n_supprimes": int(s.sum()),
            "part_supprimee_pct": round(100 * s.mean(), 2),
            "attendus": round(float(att[x]), 1),
            "rapport": round(float(s.sum() / att[x]), 2) if att[x] > 0 else "",
            "hasard_note_haut": int(np.percentile(obs_note, 97.5)),
            "hasard_fiche_haut": int(np.percentile(obs_fiche, 97.5)),
            "au_dessus_note": bool(s.sum() > np.percentile(obs_note, 97.5)),
            "au_dessus_fiche": bool(s.sum() > np.percentile(obs_fiche, 97.5)),
            "n_fiches": int(len(np.unique(d["cid"][m]))),
            "fiches_touchees": int(len(fiches_supp)),
            "part_supp_fiche_la_plus_touchee_pct":
                round(100 * fiches_supp.max() / s.sum(), 1) if s.sum() else "",
            "longueur_mediane": int(np.median(d["n_caracteres"][m])),
            "part_5_etoiles_pct": round(100 * (d["note"][m] == 5).mean(), 1),
            "part_chaines_pct": round(100 * d["chaine_us"][m].mean(), 1),
        })
    return resume, lignes


def voisins(z: np.ndarray, cid: np.ndarray) -> np.ndarray:
    """Les N_VOISINS plus proches voisins de chaque avis, hors de sa fiche."""
    nn = NearestNeighbors(n_neighbors=min(len(z), 200), metric="cosine").fit(z)
    ind = nn.kneighbors(z, return_distance=False)
    out = np.empty((len(z), N_VOISINS), dtype=int)
    for i, ligne in enumerate(ind):
        autres = ligne[cid[ligne] != cid[i]][:N_VOISINS]
        if len(autres) < N_VOISINS:
            raise SystemExit(f"avis {i} : moins de {N_VOISINS} voisins hors fiche parmi 200")
        out[i] = autres
    return out


def ecart_voisins(nb: np.ndarray, supp: np.ndarray) -> float:
    part = supp[nb].mean(axis=1)
    return float(part[supp].mean() - part[~supp].mean())


def ecrire(chemin: Path, lignes: list[dict]) -> None:
    with chemin.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(lignes[0]))
        w.writeheader(); w.writerows(lignes)


def main() -> int:
    SORTIES.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(GRAINE)
    d0, v0 = charger()
    resumes, groupes, membres, knn, longueur = [], [], [], [], []

    cinq = d0["note"] == 5
    for nom, masque in (("tous_home_services", np.ones(len(v0), bool)),
                        ("sans_chaines", ~d0["chaine_us"]),
                        ("tous_home_services_5_etoiles", cinq),
                        ("sans_chaines_5_etoiles", cinq & ~d0["chaine_us"])):
        d, v = sous(d0, masque), v0[masque]
        supp = d["supprime"]
        notes = np.unique(d["note"])
        taux = np.zeros(len(supp))
        for n in notes:
            taux[d["note"] == n] = supp[d["note"] == n].mean()
        journal(f"{nom} : {len(v)} avis, {int(supp.sum())} supprimés, "
                f"{len(np.unique(d['cid']))} fiches")
        t_note = tirages(supp, d["note"], rng)
        t_fiche = tirages(supp, codes(d["cid"], d["note"]), rng)

        z = PCA(N_ACP, random_state=0).fit_transform(v)
        decoupages = [("kmeans", k, KMeans(k, n_init=10, random_state=0).fit_predict(z))
                      for k in VALEURS_K]
        carte = TSNE(2, perplexity=30, init="pca", random_state=0, n_jobs=6).fit_transform(z)
        decoupages.append(("hdbscan", "", HDBSCAN(min_cluster_size=30, min_samples=10,
                                                  cluster_selection_method="leaf",
                                                  copy=True).fit_predict(carte)))
        for methode, k, g in decoupages:
            r, lignes = decrire(nom, methode, k, g, d, taux, t_note, t_fiche)
            resumes.append(r); groupes += lignes
            membres += [{"population": nom, "methode": methode, "k": k, "groupe": int(x),
                         "review_id": rid, "cid": c, "supprime": bool(s)}
                        for x, rid, c, s in zip(g, d["review_id"], d["cid"], supp)]
            journal(f"  {methode} {k} : {r['n_groupes']} groupes, écart global au rang "
                    f"{r['ecart_global_rang_note_pct']} % (note) / "
                    f"{r['ecart_global_rang_fiche_pct']} % (fiche)")

        # Longueur : dans le groupe le plus supprimé de K = 4, les textes courts
        # sont-ils plus supprimés que les textes courts des autres groupes ?
        g4 = next(g for methode, k, g in decoupages if methode == "kmeans" and k == 4)
        rapports = [supp[g4 == x].sum() / taux[g4 == x].sum() for x in range(4)]
        pire = int(np.argmax(rapports))
        court = d["n_caracteres"] < COURT
        for nom_c, m in (("courts du groupe", court & (g4 == pire)),
                         ("courts des autres groupes", court & (g4 != pire)),
                         ("longs du groupe", ~court & (g4 == pire)),
                         ("longs des autres groupes", ~court & (g4 != pire))):
            longueur.append({"population": nom, "k": 4, "groupe": pire, "textes": nom_c,
                             "n_avis": int(m.sum()), "n_supprimes": int(supp[m].sum()),
                             "part_supprimee_pct": round(100 * supp[m].mean(), 1)})
        for n in notes:
            m = (g4 == pire) & (d["note"] == n)
            if m.any():
                longueur.append({"population": nom, "k": 4, "groupe": pire,
                                 "textes": f"note {n} du groupe", "n_avis": int(m.sum()),
                                 "n_supprimes": int(supp[m].sum()),
                                 "part_supprimee_pct": round(100 * supp[m].mean(), 1)})

        nb = voisins(v, d["cid"])
        obs = ecart_voisins(nb, supp)
        sn = np.array([ecart_voisins(nb, s) for s in t_note])
        sf = np.array([ecart_voisins(nb, s) for s in t_fiche])
        part = supp[nb].mean(axis=1)
        knn.append({"population": nom, "n_avis": len(v), "n_supprimes": int(supp.sum()),
                    "part_supprimee_pct": round(100 * supp.mean(), 2),
                    "voisins_supprimes_si_supprime_pct": round(100 * part[supp].mean(), 2),
                    "voisins_supprimes_si_reste_pct": round(100 * part[~supp].mean(), 2),
                    "ecart_points": round(100 * obs, 2),
                    "hasard_note_moyen_points": round(100 * sn.mean(), 2),
                    "rang_note_pct": rang(obs, sn),
                    "hasard_fiche_moyen_points": round(100 * sf.mean(), 2),
                    "rang_fiche_pct": rang(obs, sf)})
        journal(f"  voisins : écart {100 * obs:.2f} points ; hasard note {100 * sn.mean():.2f}, "
                f"fiche {100 * sf.mean():.2f}")

    ecrire(SORTIES / "A1-decoupages.csv", resumes)
    ecrire(SORTIES / "A2-groupes.csv", groupes)
    ecrire(SORTIES / "A3-appartenance-avis.csv", membres)
    ecrire(SORTIES / "B1-voisins.csv", knn)
    ecrire(SORTIES / "C1-longueur.csv", longueur)
    journal("terminé")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
