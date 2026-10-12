#!/usr/bin/env python3
"""
==============================================================================
Script : 07D_regression_signaux_texte.py
Table source : data/local/reviews_panel_features_03B.parquet (03B_features_local.py)

La régression réduite du 07C, avec deux signaux tirés des textes, demandée par
Matthieu le 2026-09-29 après les études d'embeddings du 21 au 29 septembre.

    PYTHONPATH=.venv/Lib/site-packages <python uv> logistic-regression-study/python/07D_regression_signaux_texte.py
    ... 07D_regression_signaux_texte.py --valider-07C
    ... 07D_regression_signaux_texte.py --min-caracteres 30

Écrit sans pandas ni statsmodels : depuis le 2026-09-29 vers 12h44, la règle
Windows de contrôle des applications bloque `pyarrow.compute`, dont pandas
dépend. L'ajustement reprend celui de `glm_numpy.py` (Newton, marges groupées
par fiche avec la correction de petit échantillon de statsmodels) en numpy
seul. `--valider-07C` rejoue le 07C sans les signaux et compare aux sorties du
2026-09-28.

------------------------------------------------------------------------------
LES DEUX SIGNAUX
------------------------------------------------------------------------------
Longueur du texte, en trois cas (référence : texte de 60 caractères ou plus)
  sans_texte     aucun texte (l'avis n'a pas de vecteur)
  texte_court    texte de moins de 60 caractères, espaces de bord retirés
                 (`n_caracteres` des vecteurs). Mesure simple de l'« éloge
                 court » des études du 29/09 : elle ne dit pas si le texte est
                 générique.

Copie
  copie_ou_quasi texte d'au moins 80 caractères (ou `--min-caracteres`) dont
                 l'avis le plus proche du panel a une similarité de 0,97 ou
                 plus. À 80, ce sont les classes « copie » et « quasi-copie »
                 de l'étude du 28/09. La similarité vient de sa colonne
                 `sim_max`, calculée sur tous les textes, courts compris
                 (etudes-ponctuelles/2026-09-28-embeddings-further/sorties/
                 A5-similarite-avis.csv). Le voisin peut être sur une autre
                 fiche ou du même auteur.

Le reste est le 07C à l'identique : note, pic d'avis de la fiche, photo,
photos de l'auteur, Local Guide 4 et plus, réponse du propriétaire (état au
dernier passage, à lire comme une association), secteur (sous 1 % : « autres »,
référence automobile), contrôles d'exposition, région.

------------------------------------------------------------------------------
LES SIX PASSAGES
------------------------------------------------------------------------------
US, Europe, tous ; complet, puis sans les 2 salles de sport espagnoles et sans
toutes les fiches américaines de traitement antiparasitaire (`antiparasitaire_us`
de la table locale, 165 fiches), comme le 07C.

Sorties : output-study/<date>-sorties-07D/, ou <date>-sorties-07D-min<N>/ quand
`--min-caracteres` vaut autre chose que 80.
==============================================================================
"""
from __future__ import annotations

import argparse
import csv
import sys
from datetime import date
from math import erfc, sqrt
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RACINE = Path(__file__).resolve().parents[2]
TABLE = RACINE / "data" / "local" / "reviews_panel_features_03B.parquet"
VECTEURS = RACINE / "data" / "embeddings" / "03B_e5base.parquet"
SIMILARITES = (RACINE / "etudes-ponctuelles" / "2026-09-28-embeddings-further" / "sorties"
               / "A5-similarite-avis.csv")
REF_07C = (RACINE / "logistic-regression-study" / "output-study" / "2026-09-28-sorties-07C"
           / "07C_effets_6_passages.csv")
SORTIES_BASE = RACINE / "logistic-regression-study" / "output-study"

CID_SALLES_ATTAQUEES = ("3163466139043001754", "10346942689164695031")
SEUIL_VU_TARDIVEMENT = 8
SEUIL_SECTEUR_RARE = 0.01
MIN_CAS_PAR_COLONNE = 30
MIN_SUPPRESSIONS_PAR_COLONNE = 5
COURT = 60
SEUIL_COPIE = 0.97
MIN_CARACTERES_COPIE = 80   # règle du 28/09
Z_95 = 1.959963984540054

CARACTERISTIQUES_07C = ["etoiles_1", "etoiles_2", "etoiles_3", "etoiles_4",
                        "log_ratio_pic_journalier_fiche", "has_photo",
                        "log_photos_auteur", "guide_4_et_plus", "a_une_reponse"]
SIGNAUX = ["sans_texte", "texte_court", "copie_ou_quasi"]
CONTROLES = ["age_a_la_premiere_observation_j", "fenetre_observation_j",
             "vu_tardivement", "region_US"]


# ---------------------------------------------------------------------------
# Lecture et préparation
# ---------------------------------------------------------------------------

def colonne(t, nom):
    return t.column(nom).to_numpy(zero_copy_only=False)


def lire(min_caracteres: int = MIN_CARACTERES_COPIE) -> dict:
    t = pq.read_table(TABLE)
    d = {n: colonne(t, n) for n in ("review_id", "cid", "region", "industry", "supprime",
                                     "star", "has_photo", "reviewer_photo_count",
                                     "palier_local_guide", "a_une_reponse",
                                     "log_ratio_pic_journalier_fiche",
                                     "age_a_la_premiere_observation_j",
                                     "fenetre_observation_j", "antiparasitaire_us")}
    d["cid"] = d["cid"].astype(str)
    v = pq.read_table(VECTEURS, columns=["review_id", "n_caracteres"])
    longueur = dict(zip(colonne(v, "review_id"), colonne(v, "n_caracteres")))
    with SIMILARITES.open(encoding="utf-8") as f:
        sim = {r["review_id"]: float(r["sim_max"]) for r in csv.DictReader(f)}
    n = np.array([longueur.get(r, -1) for r in d["review_id"]])
    d["sans_texte"] = (n < 0).astype(float)
    d["texte_court"] = ((n >= 0) & (n < COURT)).astype(float)
    s = np.array([sim.get(r, 0.0) for r in d["review_id"]])
    d["copie_ou_quasi"] = ((s >= SEUIL_COPIE) & (n >= min_caracteres)).astype(float)
    if (d["sans_texte"] == 0).sum() != len(sim):
        raise SystemExit("avis avec texte et fichier des similarités ne se recouvrent pas")
    return d


def preparer(d: dict) -> dict:
    def nul(x, defaut):
        x = np.asarray(x, dtype=object)
        return np.where(np.array([e is None or (isinstance(e, float) and np.isnan(e))
                                  for e in x]), defaut, x)

    d["y"] = d["supprime"].astype(float)
    etoiles = nul(d["star"], 0).astype(int)
    for k in range(1, 5):
        d[f"etoiles_{k}"] = (etoiles == k).astype(float)
    d["has_photo"] = nul(d["has_photo"], False).astype(bool).astype(float)
    d["a_une_reponse"] = nul(d["a_une_reponse"], False).astype(bool).astype(float)
    d["guide_4_et_plus"] = (d["palier_local_guide"] == "4_et_plus").astype(float)
    d["log_photos_auteur"] = np.log1p(np.clip(nul(d["reviewer_photo_count"], 0)
                                              .astype(float), 0, None))
    d["log_ratio_pic_journalier_fiche"] = nul(d["log_ratio_pic_journalier_fiche"], 0).astype(float)
    for c in ("age_a_la_premiere_observation_j", "fenetre_observation_j"):
        d[c] = np.clip(nul(d[c], 0).astype(float), 0, None)
    d["vu_tardivement"] = (d["age_a_la_premiere_observation_j"] >= SEUIL_VU_TARDIVEMENT).astype(float)
    d["region_US"] = (d["region"] == "US").astype(float)
    d["industry"] = nul(d["industry"], "inconnu").astype(str)
    d["retire"] = (np.isin(d["cid"], CID_SALLES_ATTAQUEES)
                   | nul(d["antiparasitaire_us"], False).astype(bool))
    return d


def sous(d: dict, m: np.ndarray) -> dict:
    return {k: x[m] for k, x in d.items()}


# ---------------------------------------------------------------------------
# Modèle
# ---------------------------------------------------------------------------

def matrice(d: dict, avec_signaux: bool) -> tuple[np.ndarray, list[str]]:
    secteurs, n = np.unique(d["industry"], return_counts=True)
    rares = set(secteurs[n / len(d["y"]) < SEUIL_SECTEUR_RARE])
    secteur = np.array(["autres" if s in rares else s for s in d["industry"]])
    noms = [c for c in CARACTERISTIQUES_07C]
    if avec_signaux:
        noms += SIGNAUX
    colonnes = [d[c] for c in noms]
    for s in sorted(set(secteur) - {"automotive"}):
        noms.append(f"secteur_{s}")
        colonnes.append((secteur == s).astype(float))
    for c in CONTROLES:
        if c != "region_US" or len(np.unique(d["region"])) > 1:
            noms.append(c)
            colonnes.append(d[c])
    return np.column_stack([np.ones(len(d["y"]))] + colonnes), ["const"] + noms


def ecarter(X, noms, y):
    """Garde-fou du 07C : colonne oui/non trop rare ou sans variation."""
    garde, jetees = [0], []
    for j in range(1, X.shape[1]):
        x = X[:, j]
        if len(np.unique(x)) > 2:
            garde.append(j); continue
        m = x > 0
        s = int(y[m].sum())
        if m.sum() < MIN_CAS_PAR_COLONNE or s < MIN_SUPPRESSIONS_PAR_COLONNE or s == m.sum():
            jetees.append(noms[j])
        else:
            garde.append(j)
    return X[:, garde], [noms[j] for j in garde], jetees


def ajuster(X, y, groupes):
    n, k = X.shape
    b = np.zeros(k)
    dev_avant = np.inf
    for _ in range(100):
        p = 1 / (1 + np.exp(-(X @ b)))
        H = X.T @ (X * (p * (1 - p))[:, None])
        b = b + np.linalg.solve(H, X.T @ (y - p))
        p = np.clip(1 / (1 + np.exp(-(X @ b))), 1e-300, 1 - 1e-16)
        dev = -2 * np.sum(y * np.log(p) + (1 - y) * np.log1p(-p))
        if abs(dev_avant - dev) <= 1e-12 * (abs(dev) + 1):
            break
        dev_avant = dev
    else:
        raise RuntimeError("l'ajustement n'a pas convergé")
    p = 1 / (1 + np.exp(-(X @ b)))
    H_inv = np.linalg.inv(X.T @ (X * (p * (1 - p))[:, None]))
    g = np.unique(groupes, return_inverse=True)[1]
    scores = np.zeros((g.max() + 1, k))
    np.add.at(scores, g, X * (y - p)[:, None])
    G = scores.shape[0]
    cov = H_inv @ (scores.T @ scores) @ H_inv * (G / (G - 1)) * ((n - 1) / (n - k))
    return b, np.sqrt(np.diag(cov))


def un_passage(d, nom, avec_signaux):
    X, noms = matrice(d, avec_signaux)
    X, noms, jetees = ecarter(X, noms, d["y"])
    if jetees:
        print(f"  [{nom}] colonnes écartées : {', '.join(jetees)}")
    b, se = ajuster(X, d["y"], d["cid"])
    lignes = []
    for nm, c, s in zip(noms, b, se):
        z = c / s
        lignes.append({"passage": nom, "avis": len(d["y"]), "suppressions": int(d["y"].sum()),
                       "fiches": len(np.unique(d["cid"])), "variable": nm,
                       "coefficient": c, "std_err": s, "risque_relatif": np.exp(c),
                       "borne_basse": np.exp(c - Z_95 * s), "borne_haute": np.exp(c + Z_95 * s),
                       "p_value": erfc(abs(z) / sqrt(2)),
                       "role": "controle" if nm in CONTROLES or nm == "const" else "resultat"})
    return lignes


def effectifs(d, nom):
    out = []
    cas = {"sans_texte": d["sans_texte"] == 1, "texte_court": d["texte_court"] == 1,
           "texte_60_et_plus": (d["sans_texte"] == 0) & (d["texte_court"] == 0),
           "copie_ou_quasi": d["copie_ou_quasi"] == 1}
    for c, m in cas.items():
        out.append({"passage": nom, "cas": c, "avis": int(m.sum()),
                    "suppressions": int(d["y"][m].sum()),
                    "taux_pour_10000_avis": round(1e4 * d["y"][m].mean(), 1) if m.any() else ""})
    return out


def passages(d):
    for region in ("US", "Europe", "tous"):
        base = d if region == "tous" else sous(d, d["region"] == region)
        yield f"{region}_complet", base
        yield f"{region}_sans_retraits", sous(base, ~base["retire"])


def ecrire(chemin, lignes):
    with chemin.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(lignes[0]))
        w.writeheader(); w.writerows(lignes)


def valider_07c(d) -> None:
    with REF_07C.open(encoding="utf-8") as f:
        ref = {(r["passage"], r["variable"]): float(r["coefficient"])
               for r in csv.DictReader(f) if r["coefficient"] not in ("", "0.0")}
    ecart_max = 0.0
    for nom, s in passages(d):
        for l in un_passage(s, nom, avec_signaux=False):
            cle = (nom, l["variable"])
            if cle in ref:
                ecart_max = max(ecart_max, abs(l["coefficient"] - ref[cle]))
    print(f"[validation] écart maximal aux coefficients du 07C du 2026-09-28 : {ecart_max:.2e}")
    if ecart_max > 1e-6:
        raise SystemExit("le calcul numpy ne retombe pas sur le 07C")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--valider-07C", dest="valider", action="store_true")
    ap.add_argument("--min-caracteres", type=int, default=MIN_CARACTERES_COPIE,
                    help="longueur minimale d'un texte pour compter comme copie")
    args = ap.parse_args()
    suffixe = "" if args.min_caracteres == MIN_CARACTERES_COPIE else f"-min{args.min_caracteres}"
    SORTIES = SORTIES_BASE / f"{date.today():%Y-%m-%d}-sorties-07D{suffixe}"
    d = preparer(lire(args.min_caracteres))
    print(f"[copies] similarité ≥ {SEUIL_COPIE}, texte d'au moins {args.min_caracteres} "
          f"caractères : {int(d['copie_ou_quasi'].sum())} avis")
    print(f"[lecture] {len(d['y'])} avis, {int(d['y'].sum())} suppressions")
    valider_07c(d)
    if args.valider:
        return 0

    SORTIES.mkdir(parents=True, exist_ok=True)
    tout, eff, bilan = [], [], []
    for nom, s in passages(d):
        lignes = un_passage(s, nom, avec_signaux=True)
        tout += lignes; eff += effectifs(s, nom)
        bilan.append({"passage": nom, "avis": len(s["y"]), "suppressions": int(s["y"].sum()),
                      "fiches": len(np.unique(s["cid"]))})
        print(f"\n[{nom}] {len(s['y'])} avis, {int(s['y'].sum())} suppressions")
        for l in lignes:
            if l["variable"] in SIGNAUX:
                print(f"  {l['variable']:<16} ×{l['risque_relatif']:.2f} "
                      f"[{l['borne_basse']:.2f} – {l['borne_haute']:.2f}]  p={l['p_value']:.3f}")
    ecrire(SORTIES / "07D_effets_6_passages.csv", tout)
    ecrire(SORTIES / "07D_effectifs_signaux.csv", eff)
    ecrire(SORTIES / "07D_passages.csv", bilan)
    (SORTIES / "07D_source.txt").write_text(
        f"Copie : similarité ≥ {SEUIL_COPIE}, texte d'au moins {args.min_caracteres} caractères\n"
        f"Données : {TABLE.name}, signaux : {VECTEURS.name} (longueur) et "
        f"{SIMILARITES.relative_to(RACINE).as_posix()} (copies)\n"
        "Moteur : numpy (Newton, marges groupées par fiche), validé contre le 07C du 2026-09-28\n",
        encoding="utf-8")
    print(f"\nécrit dans {SORTIES}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
