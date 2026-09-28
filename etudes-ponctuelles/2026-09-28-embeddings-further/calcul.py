#!/usr/bin/env python3
"""Deux usages des embeddings après la section 5 d'analyses-complémentaires.

    .venv/Scripts/python.exe etudes-ponctuelles/2026-09-28-embeddings-further/calcul.py

Demande de Matthieu du 2026-09-28. Vecteurs : `data/embeddings/03B_e5base.parquet`
(panel 03B, 26 168 avis avec texte, toutes régions, modèle e5-base, vecteurs de
norme 1 : le produit de deux vecteurs est leur similarité).

------------------------------------------------------------------------------
A. LES AVIS PRESQUE IDENTIQUES
------------------------------------------------------------------------------
Pour chaque avis, l'avis le plus proche parmi les 26 167 autres, et leur
similarité. Calibration faite le 2026-09-28 en lisant des paires (hors dépôt) :
avec ce modèle les similarités sont tassées, 0,95 à 0,97 réunit des avis sur le
même sujet et la même fiche, pas des copies. D'où quatre classes :

  copie                 similarité ≥ 0,99   81 % des paires ont un texte identique
  quasi-copie           0,97 à 0,99         même texte réécrit, gabarit commun
  même sujet            0,94 à 0,97         deux avis différents sur le même sujet,
                                            souvent la même fiche (ajouté le 2026-09-28)
  sans jumeau           < 0,94

Seuls les textes d'au moins 80 caractères sont classés : deux « Great
service » sont identiques sans rien dire d'une campagne. Les textes plus courts
sont comptés à part.

Rapport au taux de la fiche (ajouté le 2026-09-28) : pour chaque avis d'une
classe, le taux de suppression des avis « ordinaires » de sa fiche (sans jumeau
à 0,94 ou plus, texte long ou court, l'avis lui-même exclu). Leur somme donne
les suppressions attendues si la classe était supprimée comme le reste de sa
fiche. Rapport observé / attendu, fourchette à 95 % par 2 000 tirages des
fiches avec remise. Un avis dont la fiche n'a aucun avis ordinaire est écarté
du calcul, et compté.

Contrôles : sans les six enseignes signalées ; part des suppressions portée par
la fiche la plus touchée ; comparaison, dans les seules fiches qui ont au moins
une copie, des copies et des autres avis ; qui du premier ou du second avis de
la paire est supprimé (un avis supprimé puis republié par son auteur ferait
apparaître une copie à cause de la suppression, et non l'inverse).

------------------------------------------------------------------------------
B. SUPPRIMÉS ET RESTÉS SUR UNE MÊME FICHE
------------------------------------------------------------------------------
Cases fiche × note ayant au moins 2 avis supprimés et 1 resté en ligne. Dans
chaque case : similarité moyenne d'un supprimé aux autres supprimés, moins sa
similarité moyenne aux restés. Positif si les supprimés d'une fiche se
ressemblent plus entre eux qu'ils ne ressemblent aux restés. Moyenne sur les
cases, pondérée par le nombre de supprimés. Comparaison à 2 000 permutations
des étiquettes à l'intérieur de chaque case : secteur, fiche et note sont
identiques par construction.

Variante : même calcul après retrait des avis classés copie ou quasi-copie,
pour savoir si l'écart tient aux seules copies.

Sorties : `sorties/*.csv`, sans texte, sans nom, sans lien d'avis.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

DOSSIER = Path(__file__).resolve().parent
RACINE = DOSSIER.parents[1]
SORTIES = DOSSIER / "sorties"
VECTEURS = RACINE / "data" / "embeddings" / "03B_e5base.parquet"
PANEL = RACINE / "data" / "bigquery" / "03B_reviews_panel_filtered_08_04_to_08_26.parquet"
BUSINESSES = RACINE / "data" / "bigquery" / "businesses.parquet"

GRAINE = 20260928
N_TIRAGES = 2000
MIN_CARACTERES = 80
SEUIL_COPIE, SEUIL_QUASI, SEUIL_SUJET = 0.99, 0.97, 0.94
CLASSES = ["copie", "quasi-copie", "même sujet", "sans jumeau", "texte de moins de 80 caractères"]


def charger():
    df = pd.read_parquet(VECTEURS)
    v = np.vstack(df["vecteur"].to_numpy()).astype("float32")
    df = df.drop(columns=["vecteur"]).reset_index(drop=True)
    # Auteur et date : lus pour les contrôles, jamais écrits. `review_link` n'est
    # gardé que sous forme de hachage.
    brut = pd.read_parquet(PANEL, columns=["review_id", "review_link", "created_at"])
    brut["auteur"] = pd.util.hash_pandas_object(brut["review_link"], index=False)
    df = df.merge(brut[["review_id", "auteur", "created_at"]], on="review_id",
                  how="left", validate="one_to_one")
    b = pd.read_parquet(BUSINESSES, columns=["cid", "country", "industry"])
    df = df.merge(b, on="cid", how="left", validate="many_to_one")
    df["region"] = np.where(df["country"] == "US", "US", "Europe")
    return df, v


# ---------------------------------------------------------------------------
# A
# ---------------------------------------------------------------------------

def plus_proche(v: np.ndarray, pas: int = 2000):
    n = len(v)
    sim, voisin = np.empty(n, dtype="float32"), np.empty(n, dtype="int64")
    for i in range(0, n, pas):
        s = v[i:i + pas] @ v.T
        s[np.arange(s.shape[0]), np.arange(i, i + s.shape[0])] = -1
        voisin[i:i + pas], sim[i:i + pas] = s.argmax(1), s.max(1)
    return sim, voisin


def classer(df: pd.DataFrame) -> pd.Series:
    c = np.where(df["sim_max"] >= SEUIL_COPIE, "copie",
                 np.where(df["sim_max"] >= SEUIL_QUASI, "quasi-copie",
                          np.where(df["sim_max"] >= SEUIL_SUJET, "même sujet", "sans jumeau")))
    return pd.Series(np.where(df["n_caracteres"] < MIN_CARACTERES, CLASSES[4], c), index=df.index)


def resume_classes(df: pd.DataFrame, perimetre: str) -> pd.DataFrame:
    lignes = []
    for classe in CLASSES:
        d = df[df["classe"] == classe]
        supp = d.loc[d["supprime"], "cid"].value_counts()
        lignes.append({
            "perimetre": perimetre, "classe": classe, "avis": len(d),
            "supprimes": int(d["supprime"].sum()),
            "part_supprimee_pct": round(100 * d["supprime"].mean(), 1) if len(d) else np.nan,
            "fiches": d["cid"].nunique(), "fiches_touchees": len(supp),
            "part_supp_fiche_la_plus_touchee_pct":
                round(100 * supp.iloc[0] / supp.sum(), 1) if len(supp) else np.nan,
            "voisin_meme_fiche_pct": round(100 * d["voisin_meme_fiche"].mean(), 1) if len(d) else np.nan,
            "voisin_meme_auteur_pct": round(100 * d["voisin_meme_auteur"].mean(), 1) if len(d) else np.nan,
        })
    return pd.DataFrame(lignes)


def dans_les_memes_fiches(df: pd.DataFrame, perimetre: str) -> pd.DataFrame:
    """Dans les fiches qui ont au moins une copie ou quasi-copie : ces avis contre
    les autres avis longs des mêmes fiches."""
    jumeau = df["classe"].isin(["copie", "quasi-copie"])
    fiches = df.loc[jumeau, "cid"].unique()
    d = df[df["cid"].isin(fiches) & (df["n_caracteres"] >= MIN_CARACTERES)]
    lignes = []
    for nom, masque in (("copie ou quasi-copie", d["classe"].isin(["copie", "quasi-copie"])),
                        ("autres avis des mêmes fiches",
                         ~d["classe"].isin(["copie", "quasi-copie"]))):
        x = d[masque]
        lignes.append({"perimetre": perimetre, "groupe": nom, "fiches": x["cid"].nunique(),
                       "avis": len(x), "supprimes": int(x["supprime"].sum()),
                       "part_supprimee_pct": round(100 * x["supprime"].mean(), 1)})
    return pd.DataFrame(lignes)


def ordre_dans_la_paire(df: pd.DataFrame) -> pd.DataFrame:
    """Paires copie ou quasi-copie (avis et son plus proche voisin) : le premier
    publié et le second sont-ils supprimés ? Chaque paire comptée une fois, sur
    tout le panel puis sans les paires qui touchent une enseigne signalée."""
    d = df[df["classe"].isin(["copie", "quasi-copie"])]
    vus, lignes = set(), []
    for i, r in d.iterrows():
        j = int(r["voisin"])
        cle = tuple(sorted((i, j)))
        if cle in vus:
            continue
        vus.add(cle)
        a, b = df.loc[i], df.loc[j]
        premier, second = (a, b) if a["created_at"] <= b["created_at"] else (b, a)
        lignes.append({"premier_supprime": bool(premier["supprime"]),
                       "second_supprime": bool(second["supprime"]),
                       "enseigne": bool(a["enseigne_signalee"] or b["enseigne_signalee"])})
    t = pd.DataFrame(lignes)
    out = []
    for perimetre, x in (("tout le panel", t), ("sans les six enseignes", t[~t["enseigne"]])):
        g = x.groupby(["premier_supprime", "second_supprime"]).size().reset_index(name="paires")
        g.insert(0, "perimetre", perimetre)
        out.append(g)
    return pd.concat(out, ignore_index=True)


def rapport_a_la_fiche(df: pd.DataFrame, perimetre: str, rng) -> pd.DataFrame:
    """Suppressions observées / attendues au taux des avis ordinaires de la fiche."""
    ordinaire = df["sim_max"] < SEUIL_SUJET          # sans jumeau, long ou court
    g = df[ordinaire].groupby("cid")["supprime"].agg(n="size", s="sum")
    n = df["cid"].map(g["n"]).fillna(0).to_numpy()
    s = df["cid"].map(g["s"]).fillna(0).to_numpy()
    moi = ordinaire.to_numpy()
    sup = df["supprime"].to_numpy().astype(float)
    # L'avis lui-même est retiré de sa fiche quand il en fait partie.
    n_hors = n - moi
    s_hors = s - moi * sup
    attendu = np.divide(s_hors, n_hors, out=np.full(len(df), np.nan), where=n_hors > 0)
    lignes = []
    for classe in CLASSES[:4]:
        m = (df["classe"] == classe).to_numpy() & ~np.isnan(attendu)
        d = pd.DataFrame({"cid": df["cid"].to_numpy()[m], "o": sup[m], "e": attendu[m]})
        par_fiche = d.groupby("cid")[["o", "e"]].sum()
        o, e = par_fiche["o"].to_numpy(), par_fiche["e"].to_numpy()
        tir = rng.integers(0, len(o), size=(N_TIRAGES, len(o)))
        ratios = o[tir].sum(1) / np.maximum(e[tir].sum(1), 1e-9)
        bas, haut = np.percentile(ratios, [2.5, 97.5])
        lignes.append({
            "perimetre": perimetre, "classe": classe, "avis": int(m.sum()),
            "avis_ecartes_sans_fiche_ordinaire": int(((df["classe"] == classe).to_numpy()
                                                      & np.isnan(attendu)).sum()),
            "fiches": len(o), "supprimes": int(o.sum()),
            "attendus_au_taux_de_la_fiche": round(float(e.sum()), 1),
            "rapport_observe_attendu": round(float(o.sum() / e.sum()), 2) if e.sum() else np.nan,
            "borne_basse": round(float(bas), 2), "borne_haute": round(float(haut), 2)})
    return pd.DataFrame(lignes)


# ---------------------------------------------------------------------------
# B
# ---------------------------------------------------------------------------

def cases(df: pd.DataFrame, garde: np.ndarray):
    d = df[garde]
    out = []
    for (cid, note), bloc in d.groupby(["cid", "note"]):
        s = int(bloc["supprime"].sum())
        if s >= 2 and len(bloc) - s >= 1:
            out.append(bloc.index.to_numpy())
    return out


def contraste(S: np.ndarray, lab: np.ndarray) -> float:
    d, k = lab, ~lab
    nd = d.sum()
    dd = (S[np.ix_(d, d)].sum() - nd) / (nd * (nd - 1))   # diagonale (=1) retirée
    dk = S[np.ix_(d, k)].mean()
    return dd - dk


def route_intra_fiche(df: pd.DataFrame, v: np.ndarray, garde: np.ndarray, rng) -> dict:
    liste = cases(df, garde)
    if not liste:
        return {}
    mats = [v[idx] @ v[idx].T for idx in liste]
    labs = [df.loc[idx, "supprime"].to_numpy() for idx in liste]
    poids = np.array([l.sum() for l in labs], dtype=float)
    observe = np.average([contraste(S, l) for S, l in zip(mats, labs)], weights=poids)
    tirages = np.empty(N_TIRAGES)
    for t in range(N_TIRAGES):
        tirages[t] = np.average([contraste(S, rng.permutation(l)) for S, l in zip(mats, labs)],
                                weights=poids)
    haut = np.percentile(tirages, 97.5)
    return {"cases": len(liste), "fiches": df.loc[np.concatenate(liste), "cid"].nunique(),
            "supprimes": int(poids.sum()),
            "restes": int(sum(len(l) - l.sum() for l in labs)),
            "contraste_observe": round(float(observe), 5),
            "hasard_moyen": round(float(tirages.mean()), 5),
            "hasard_borne_haute": round(float(haut), 5),
            "part_tirages_au_dessus_pct": round(100 * float((tirages >= observe).mean()), 2),
            "au_dessus_du_hasard": bool(observe > haut)}


def main() -> int:
    SORTIES.mkdir(parents=True, exist_ok=True)
    df, v = charger()
    df["sim_max"], df["voisin"] = plus_proche(v)
    voisin = df.loc[df["voisin"].to_numpy()].reset_index(drop=True)
    df["voisin_meme_fiche"] = df["cid"].to_numpy() == voisin["cid"].to_numpy()
    df["voisin_meme_auteur"] = df["auteur"].to_numpy() == voisin["auteur"].to_numpy()
    df["classe"] = classer(df)

    hors = ~df["enseigne_signalee"]
    perimetres = {"tout le panel": df, "sans les six enseignes": df[hors],
                  "US": df[df["region"] == "US"], "Europe": df[df["region"] == "Europe"],
                  "US sans les six enseignes": df[hors & (df["region"] == "US")]}

    pd.concat([resume_classes(d, p) for p, d in perimetres.items()]).to_csv(
        SORTIES / "A1-classes.csv", index=False)
    pd.concat([dans_les_memes_fiches(d, p) for p, d in list(perimetres.items())[:2]]).to_csv(
        SORTIES / "A2-memes-fiches.csv", index=False)
    ordre_dans_la_paire(df).to_csv(SORTIES / "A3-ordre-dans-la-paire.csv", index=False)
    rng_a = np.random.default_rng(GRAINE + 1)
    pd.concat([rapport_a_la_fiche(d.reset_index(drop=True), p, rng_a)
               for p, d in list(perimetres.items())[:2]]).to_csv(
        SORTIES / "A7-rapport-a-la-fiche.csv", index=False)
    notes = (df[df["classe"].isin(["copie", "quasi-copie"])]
             .groupby(["classe", "note"])["supprime"].agg(avis="size", supprimes="sum")
             .reset_index())
    notes.to_csv(SORTIES / "A4-classes-par-note.csv", index=False)
    (df[["review_id", "cid", "note", "supprime", "sim_max", "classe"]]
     .to_csv(SORTIES / "A5-similarite-avis.csv", index=False))
    bornes = [0, 0.93, 0.95, 0.96, 0.97, 0.98, 0.99, 1.01]
    noms = ["< 0,93", "0,93 à 0,95", "0,95 à 0,96", "0,96 à 0,97", "0,97 à 0,98",
            "0,98 à 0,99", "0,99 et plus"]
    tranches = []
    for p, d in list(perimetres.items())[:2]:
        d = d[d["n_caracteres"] >= MIN_CARACTERES]
        t = (d.assign(tranche=pd.cut(d["sim_max"], bornes, labels=noms, right=False))
             .groupby("tranche", observed=False)["supprime"].agg(avis="size", supprimes="sum")
             .reset_index())
        t["part_supprimee_pct"] = (100 * t["supprimes"] / t["avis"]).round(1)
        t.insert(0, "perimetre", p)
        tranches.append(t)
    pd.concat(tranches).to_csv(SORTIES / "A6-tranches-similarite.csv", index=False)

    rng = np.random.default_rng(GRAINE)
    jumeau = df["classe"].isin(["copie", "quasi-copie"]).to_numpy()
    lignes = []
    for nom, garde in (("tout le panel", np.ones(len(df), bool)),
                       ("sans les six enseignes", hors.to_numpy()),
                       ("tout le panel, sans copies ni quasi-copies", ~jumeau),
                       ("sans les six enseignes, sans copies ni quasi-copies",
                        hors.to_numpy() & ~jumeau)):
        for note_nom, masque_note in (("toutes notes", np.ones(len(df), bool)),
                                      ("1 étoile", (df["note"] == 1).to_numpy()),
                                      ("5 étoiles", (df["note"] == 5).to_numpy())):
            r = route_intra_fiche(df, v, garde & masque_note, rng)
            lignes.append({"perimetre": nom, "note": note_nom, **r})
            print(nom, note_nom, r)
    pd.DataFrame(lignes).to_csv(SORTIES / "B1-intra-fiche.csv", index=False)
    print(pd.read_csv(SORTIES / "A1-classes.csv").to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
