#!/usr/bin/env python3
"""Les avis qui ont un jumeau sont-ils plus supprimés chez les antiparasitaires ?

    PYTHONPATH=.venv/Lib/site-packages <python uv> etudes-ponctuelles/2026-09-30-avis-antiparasitaires/calcul_copies.py

Demande de Matthieu du 2026-09-30 : reprendre la règle des copies du panel 03B
(texte d'au moins 80 caractères dont un autre avis a une similarité de 0,97 ou
plus ; 149 avis, 38 % supprimés, risque ×12 dans le 07D) sur tous les avis des
fiches antiparasitaires américaines.

------------------------------------------------------------------------------
LES DONNÉES
------------------------------------------------------------------------------
  avis      data/local/reviews_pest_all.parquet (extraire.py) : 174 fiches,
            259 901 avis avec texte, 1 086 supprimés du 11 au 24 août 2026.
  vecteurs  data/embeddings/pest_e5base.parquet (Colab, verifier_colab.py).
  auteur    hachage, en mémoire seulement, du lien de profil (`review_link`,
            de la forme /maps/contrib/<id>/reviews), comme `author_key` du 03B.

------------------------------------------------------------------------------
LES JUMEAUX
------------------------------------------------------------------------------
Les avis d'au moins 30 caractères sont comparés entre eux (textes identiques
regroupés : ils ont le même vecteur). Un jumeau est un autre avis de similarité
0,97 ou plus. Contrairement au 03B, où seul le plus proche voisin était décrit,
tous les jumeaux d'un avis sont gardés. Le type retenu est le plus précis :
  doublon                     même auteur, même fiche
  un auteur, plusieurs fiches même auteur, autre fiche
  gabarit sur une fiche       autre auteur, même fiche
  gabarit sur une enseigne    autre auteur, autre fiche de la même enseigne
                              (deux premiers mots du nom, comme au 03B)
  rencontre                   autre auteur, autre enseigne

Deux longueurs minimales pour l'avis étudié : 80 caractères (règle du 28/09)
et 30 caractères (variante du 29/09).

------------------------------------------------------------------------------
LA COMPARAISON
------------------------------------------------------------------------------
Parmi les avis de la longueur minimale, la part supprimée dépend beaucoup de
l'âge (12 % en août 2026, 0,06 % avant 2023) et un peu de la note.
  attendus         somme, sur les avis du groupe, du taux de suppression de
                   leur période × note (8 périodes, celles du regroupement)
  hasard à         étiquettes « supprimé » redistribuées 2 000 fois entre avis
  période égale    de même période × note
  hasard à         redistribuées entre avis de même fiche × période × note :
  fiche égale      chaque fiche garde ses suppressions ; seul compte le fait
                   d'être une copie à l'intérieur de la fiche
Rang : part des tirages où le groupe a moins de supprimés que l'observé. Au
delà de 97,5 %, le hasard ne l'explique pas.

------------------------------------------------------------------------------
LES SORTIES (sorties/copies/, identifiants seulement, aucun texte ni nom)
------------------------------------------------------------------------------
  C1-types.csv       par longueur minimale et type : avis, supprimés, part,
                     attendus, rapport, rangs, seuils ; plus « toutes copies »
  C2-chaines.csv     copies de 80 caractères et plus, par chaîne
  C3-periodes.csv    copies de 80 caractères et plus, par période de publication
  C4-seuils.csv      a un avis de similarité ≥ 0,95 / 0,97 / 0,99 (sans type)
  C5-ordre.csv       dans un groupe de jumeaux, le premier déposé est-il plus
                     supprimé que les suivants ; les jumeaux d'un supprimé le
                     sont-ils aussi
  C6-avis-copies.csv un avis par ligne (review_id, cid, type, supprimé)
"""
from __future__ import annotations

import csv
import hashlib
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DOSSIER = Path(__file__).resolve().parent
RACINE = DOSSIER.parents[1]
SORTIES = DOSSIER / "sorties" / "copies"
AVIS = RACINE / "data" / "local" / "reviews_pest_all.parquet"
VECTEURS = RACINE / "data" / "embeddings" / "pest_e5base.parquet"

GRAINE = 20260930
N_TIRAGES = 2000
SEUIL_RANG = 97.5
SEUIL_COPIE = 0.97
SEUILS_VARIANTES = (0.95, 0.97, 0.99)
LONGUEUR_COMPAREE = 30
LONGUEURS_ETUDIEES = (80, 30)
BLOC = 512
TYPES = ["doublon", "un auteur, plusieurs fiches", "gabarit sur une fiche",
         "gabarit sur une enseigne", "rencontre"]
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


def micro(t):
    return int(t.timestamp() * 1_000_000)


def charger():
    a = pq.read_table(AVIS, columns=["review_id", "cid", "star", "created_at", "deleted_detected_at",
                                     "business_name", "text", "review_link"])
    cree = a.column("created_at").cast(pa.int64()).to_numpy(zero_copy_only=False)
    bornes = [micro(b) for b, _ in PERIODES]
    periode = np.array([next(k for k, b in enumerate(bornes) if c >= b) for c in cree])
    nom = [(n or "").lower() for n in a.column("business_name").to_pylist()]
    textes = [(t or "").strip() for t in a.column("text").to_pylist()]
    d = {"review_id": np.array(a.column("review_id").to_pylist()),
         "cid": np.array(a.column("cid").to_pylist()),
         "note": np.array(a.column("star").to_pylist()),
         "cree": cree, "periode": periode,
         "supprime": np.array([x is not None for x in a.column("deleted_detected_at").to_pylist()]),
         "auteur": np.array([hashlib.sha1((l or "").encode()).hexdigest()[:16]
                             for l in a.column("review_link").to_pylist()]),
         "enseigne": np.array([" ".join(n.split()[:2]) for n in nom]),
         "chaine": np.array([next((c for p, c in CHAINES.items() if n.startswith(p)), "autres")
                             for n in nom]),
         "longueur": np.array([len(t) for t in textes])}
    v = pq.read_table(VECTEURS)
    rang = {r: i for i, r in enumerate(v.column("review_id").to_pylist())}
    col = v.column("vecteur").combine_chunks()
    vec = col.flatten().to_numpy(zero_copy_only=False).reshape(len(col), -1)
    vec = vec[np.array([rang[r] for r in d["review_id"]])]
    return d, textes, vec


def jumeaux(d, textes, vec):
    """Paires d'avis (i, j), i < j, de similarité ≥ SEUIL_COPIE parmi les avis
    d'au moins LONGUEUR_COMPAREE caractères, et similarité maximale de chaque avis."""
    compares = np.flatnonzero(d["longueur"] >= LONGUEUR_COMPAREE)
    code = {}
    unique_de = np.array([code.setdefault(textes[i], len(code)) for i in compares])
    n_u = len(code)
    premier = np.zeros(n_u, dtype=np.int64)
    premier[unique_de[::-1]] = compares[::-1]
    u = vec[premier].astype("float32")
    journal(f"{len(compares)} avis d'au moins {LONGUEUR_COMPAREE} caractères, {n_u} textes différents")
    sim_max_u = np.full(n_u, -1.0, dtype="float32")
    paires_u = []
    debut = time.time()
    for a in range(0, n_u, BLOC):
        s = u[a:a + BLOC] @ u.T
        s[np.arange(len(s)), np.arange(a, a + len(s))] = -1
        sim_max_u[a:a + BLOC] = s.max(axis=1)
        i, j = np.nonzero(s >= SEUIL_COPIE)
        i = i + a
        garde = i < j
        paires_u.append(np.stack([i[garde], j[garde]], axis=1))
        if (a // BLOC) % 50 == 0:
            journal(f"  {a + len(s)}/{n_u} textes, {time.time() - debut:.0f} s")
    paires_u = np.concatenate(paires_u)
    # retour aux avis : membres de chaque texte, paires entre textes, paires dans un texte
    membres = [[] for _ in range(n_u)]
    for r, x in zip(compares, unique_de):
        membres[x].append(r)
    paires = [(p, q) for m in membres if len(m) > 1 for k, p in enumerate(m) for q in m[k + 1:]]
    paires += [(p, q) for x, y in paires_u for p in membres[x] for q in membres[y]]
    sim_max = np.full(len(d["review_id"]), -1.0, dtype="float32")
    compte = np.bincount(unique_de, minlength=n_u)
    sim_max[compares] = np.where(compte[unique_de] > 1, 1.0, sim_max_u[unique_de])
    journal(f"{len(paires_u)} paires de textes différents, {len(paires)} paires d'avis")
    return np.array(paires, dtype=np.int64).reshape(-1, 2), sim_max


def typer(d, paires):
    """Type le plus précis de chaque avis parmi ses jumeaux (-1 : sans jumeau),
    et, pour l'ordre de dépôt, la liste des jumeaux de chaque avis."""
    n = len(d["review_id"])
    type_ = np.full(n, len(TYPES), dtype=int)
    voisins = {}
    for i, j in paires:
        meme_auteur = d["auteur"][i] == d["auteur"][j]
        meme_fiche = d["cid"][i] == d["cid"][j]
        if meme_auteur:
            t = 0 if meme_fiche else 1
        elif meme_fiche:
            t = 2
        else:
            t = 3 if d["enseigne"][i] == d["enseigne"][j] else 4
        for a, b in ((i, j), (j, i)):
            type_[a] = min(type_[a], t)
            voisins.setdefault(int(a), []).append(int(b))
    type_[type_ == len(TYPES)] = -1
    return type_, voisins


def codes(*colonnes):
    return np.unique(np.array(["|".join(map(str, t)) for t in zip(*colonnes)]),
                     return_inverse=True)[1]


def tirages(supp, strate, rng):
    """Jeux d'indices « supprimés » redistribués dans chaque strate (voir
    calcul_regroupement.py)."""
    strate_triee = strate[np.argsort(strate, kind="stable")]
    debut = np.searchsorted(strate_triee, np.arange(strate.max() + 1))
    rang = np.arange(len(strate)) - debut[strate_triee]
    k = np.bincount(strate, weights=supp.astype(float), minlength=strate.max() + 1).astype(int)
    garde = rang < k[strate_triee]
    out = np.empty((N_TIRAGES, int(supp.sum())), dtype=np.int64)
    for i in range(N_TIRAGES):
        out[i] = np.lexsort((rng.random(len(strate)), strate))[garde]
    return out


def mesurer(masque, supp, taux, t_per, t_fic):
    obs = int(supp[masque].sum())
    att = float(taux[masque].sum())
    sim_p = masque[t_per].sum(axis=1)
    sim_f = masque[t_fic].sum(axis=1)
    return {"avis": int(masque.sum()), "supprimes": obs,
            "part_supprimee_pct": round(100 * obs / masque.sum(), 2) if masque.any() else "",
            "attendus_periode_note": round(att, 1),
            "rapport_observe_attendu": round(obs / att, 1) if att > 0 else "",
            "hasard_fiche_moyenne": round(float(sim_f.mean()), 1),
            "rang_periode_pct": round(100 * float((sim_p < obs).mean()), 1),
            "seuil_periode": int(np.percentile(sim_p, SEUIL_RANG)),
            "rang_fiche_pct": round(100 * float((sim_f < obs).mean()), 1),
            "seuil_fiche": int(np.percentile(sim_f, SEUIL_RANG))}


def ecrire(chemin, lignes):
    with chemin.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(lignes[0]))
        w.writeheader(); w.writerows(lignes)


def main() -> int:
    SORTIES.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(GRAINE)
    journal("lecture")
    d, textes, vec = charger()
    paires, sim_max = jumeaux(d, textes, vec)
    del vec
    type_, voisins = typer(d, paires)
    t1, c2, c3, c4, c5 = [], [], [], [], []

    for lmin in LONGUEURS_ETUDIEES:
        pop = d["longueur"] >= lmin
        supp = d["supprime"][pop]
        strate = codes(d["periode"][pop], d["note"][pop])
        taux_s = np.bincount(strate, weights=supp.astype(float)) / np.bincount(strate)
        taux = taux_s[strate]
        journal(f"{lmin} caractères et plus : {pop.sum()} avis, {supp.sum()} supprimés ; tirages")
        t_per = tirages(supp, strate, rng)
        t_fic = tirages(supp, codes(d["cid"][pop], d["periode"][pop], d["note"][pop]), rng)
        tp = type_[pop]
        cid = d["cid"][pop]
        groupes = [("tous les avis", np.ones(len(tp), bool)), ("toutes copies", tp >= 0)]
        groupes += [(t, tp == k) for k, t in enumerate(TYPES)]
        groupes += [("sans jumeau", tp < 0)]
        for nom, m in groupes:
            r = mesurer(m, supp, taux, t_per, t_fic)
            r["fiches"] = len(np.unique(cid[m]))
            r["fiches_avec_suppression"] = len(np.unique(cid[m & supp]))
            t1.append({"longueur_min": lmin, "groupe": nom, **r})
            journal(f"  {nom} : {r}")
        if lmin == 80:
            copie = tp >= 0
            for ch in list(CHAINES.values()) + ["autres"]:
                m = copie & (d["chaine"][pop] == ch)
                r = mesurer(m, supp, taux, t_per, t_fic)
                tous = d["chaine"][pop] == ch
                c2.append({"chaine": ch, "avis_de_la_chaine": int(tous.sum()),
                           "supprimes_de_la_chaine": int(supp[tous].sum()), "copies": r["avis"],
                           **{k: v for k, v in r.items() if k != "avis"}})
            for p, (_, lib) in enumerate(PERIODES):
                tous = d["periode"][pop] == p
                m = copie & tous
                c3.append({"periode": lib, "avis": int(tous.sum()),
                           "supprimes": int(supp[tous].sum()),
                           "part_supprimee_pct": round(100 * supp[tous].mean(), 2),
                           "copies": int(m.sum()), "copies_supprimees": int(supp[m].sum()),
                           "part_copies_supprimee_pct": round(100 * supp[m].mean(), 2) if m.any() else "",
                           "attendus_copies": round(float(taux[m].sum()), 1)})
        for s in SEUILS_VARIANTES:
            m = sim_max[pop] >= s
            c4.append({"longueur_min": lmin, "similarite_min": s,
                       **mesurer(m, supp, taux, t_per, t_fic)})
        idx_pop = np.flatnonzero(pop)
        journal(f"  sorties {lmin} faites")
        if lmin == 80:
            # ordre de dépôt : dans chaque groupe de jumeaux (l'avis et ses jumeaux),
            # l'avis est-il le premier déposé
            premier = np.array([d["cree"][i] <= min(d["cree"][j] for j in voisins[int(i)])
                                for i in idx_pop[tp >= 0]])
            s_c = d["supprime"][idx_pop[tp >= 0]]
            jum_supp = np.array([any(d["supprime"][j] for j in voisins[int(i)])
                                 for i in idx_pop[tp >= 0]])
            for lib, m in (("premier déposé", premier), ("déposé après un jumeau", ~premier)):
                c5.append({"cas": lib, "avis": int(m.sum()), "supprimes": int(s_c[m].sum()),
                           "part_supprimee_pct": round(100 * s_c[m].mean(), 1)})
            for lib, m in (("un jumeau supprimé", jum_supp), ("aucun jumeau supprimé", ~jum_supp)):
                c5.append({"cas": lib, "avis": int(m.sum()), "supprimes": int(s_c[m].sum()),
                           "part_supprimee_pct": round(100 * s_c[m].mean(), 1)})
            c6 = [{"review_id": d["review_id"][i], "cid": d["cid"][i],
                   "type": TYPES[type_[i]], "supprime": bool(d["supprime"][i]),
                   "similarite_max": round(float(sim_max[i]), 4)}
                  for i in idx_pop[tp >= 0]]

    ecrire(SORTIES / "C1-types.csv", t1)
    ecrire(SORTIES / "C2-chaines.csv", c2)
    ecrire(SORTIES / "C3-periodes.csv", c3)
    ecrire(SORTIES / "C4-seuils.csv", c4)
    ecrire(SORTIES / "C5-ordre.csv", c5)
    ecrire(SORTIES / "C6-avis-copies.csv", c6)
    journal("terminé")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
