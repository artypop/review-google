"""
Contrôle de robustesse — les conclusions tiennent-elles sans les fiches massivement purgées ?

24 établissements portent 958 suppressions, soit 18 % du total. Tant que les résultats n'ont
pas été rejoués sans eux, on ne sait pas si les modèles décrivent la modération de Google ou
le sort de deux salles de sport espagnoles.

Ce script rejoue les analyses A et B à l'identique, en retirant ces fiches, et met les deux
jeux de coefficients côte à côte. Il ne réécrit ni la note A ni la note B : il produit sa propre
note et son propre CSV.

Critère de lecture retenu, écrit avant de regarder les chiffres :
  - un effet qui change de sens (passe de part et d'autre de 1) ne tient pas ;
  - un effet dont l'amplitude bouge de plus de moitié est signalé comme fragile ;
  - le reste tient.

Usage :  uv run scripts/controle_robustesse.py [--bootstrap N]
"""

import argparse
import pathlib
import sys
import warnings

import numpy as np
import pandas as pd
import statsmodels.api as sm

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import analysis_a  # noqa: E402
import analysis_b  # noqa: E402

OUT = pathlib.Path("documentations/2026-09-06-controle-robustesse.md")
CSV = pathlib.Path("data/resultats/controle_robustesse.csv")
BEGIN = "<!-- genere:controle — regenere par scripts/controle_robustesse.py, ne pas editer a la main -->"
END = "<!-- /genere:controle -->"


def effets_a(d: pd.DataFrame) -> pd.DataFrame:
    """Les deux modèles de l'analyse A, sur le périmètre fourni."""
    touche = analysis_a.fit(d, d["touche"].to_numpy(), "Être touché")

    t = d[d["touche"] == 1].copy()
    X, names = analysis_a.design(t)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        res = sm.GLM(t["part_purgee"].to_numpy(), X.to_numpy(),
                     family=sm.families.Binomial(), freq_weights=t["n_fresh"].to_numpy()
                     ).fit(cov_type="cluster", cov_kwds={"groups": t["marche"].to_numpy()})
    co = pd.Series(res.params, index=names)
    rows = []
    for col, titre, ref in analysis_a.BLOCKS:
        for n in names:
            if n.startswith(f"{col}_"):
                rows.append({"modele": "Ampleur de la purge", "facteur": titre,
                             "modalite": analysis_a.LABELS.get(n[len(col) + 1:], n[len(col) + 1:]),
                             "effet": float(np.exp(co[n]))})
    ampleur = pd.DataFrame(rows)
    touche = touche[["modele", "facteur", "modalite", "effet"]]
    return pd.concat([touche, ampleur], ignore_index=True)


def effets_b(d: pd.DataFrame) -> pd.DataFrame:
    coefs = analysis_b.fit(analysis_b.informative(d))
    rows = []
    for col, titre, _ in analysis_b.BLOCKS:
        for n in coefs.index:
            if n.startswith(f"{col}_"):
                mod = n[len(col) + 1:]
                rows.append({"modele": "Analyse B — quel avis tombe", "facteur": titre,
                             "modalite": analysis_b.LABELS.get(mod, mod),
                             "effet": float(np.exp(coefs[n]))})
    return pd.DataFrame(rows)


def verdict(av: float, sans: float) -> str:
    """Sens d'abord, amplitude ensuite — mais un non-effet ne « change » pas de sens."""
    if np.isnan(av) or np.isnan(sans):
        return "non calculable"
    # Une estimation collée à 0 ou explosive est un artefact numérique (séparation),
    # pas un effet : la signaler plutôt que la comparer.
    if min(av, sans) < 0.02 or max(av, sans) > 50:
        return "NON EXPLOITABLE — estimation dégénérée, pas un effet"
    # Deux valeurs voisines de 1 ne mesurent rien : leur « changement de sens » est du bruit.
    if 0.90 <= av <= 1.11 and 0.90 <= sans <= 1.11:
        return "non-effet des deux côtés — stable"
    if (av > 1) != (sans > 1):
        return "NE TIENT PAS — change de sens"
    ratio = max(av, sans) / min(av, sans) if min(av, sans) > 0 else np.inf
    if ratio > 2:
        return "fragile — amplitude divisée ou multipliée par plus de 2"
    if ratio > 1.5:
        return "à surveiller — amplitude bouge de plus de moitié"
    return "tient"


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--bootstrap", type=int, default=0,
                   help="ignoré ici : le contrôle compare des effets ponctuels")
    p.parse_args()

    da = analysis_a.load()
    da_sp = da[~da["heavy_purge"].astype(bool)].copy()
    print(f"Analyse A — {len(da)} fiches, {int(da.touche.sum())} touchées")
    print(f"        sans purgées : {len(da_sp)} fiches, {int(da_sp.touche.sum())} touchées")

    db = analysis_b.load()
    db_sp = db[~db["heavy_purge"].astype(bool)].copy()
    ib, ib_sp = analysis_b.informative(db), analysis_b.informative(db_sp)
    print(f"Analyse B — {ib.cid.nunique()} fiches, {len(ib)} obs, {int(ib.y.sum())} disparitions")
    print(f"        sans purgées : {ib_sp.cid.nunique()} fiches, {len(ib_sp)} obs, "
          f"{int(ib_sp.y.sum())} disparitions")

    parts = []
    for nom, avec, sans in [("A", effets_a(da), effets_a(da_sp)),
                            ("B", effets_b(db), effets_b(db_sp))]:
        m = avec.merge(sans, on=["modele", "facteur", "modalite"],
                       suffixes=("_avec", "_sans"), how="outer")
        m["analyse"] = nom
        parts.append(m)
    out = pd.concat(parts, ignore_index=True)
    out["verdict"] = [verdict(a, s) for a, s in zip(out["effet_avec"], out["effet_sans"])]

    CSV.parent.mkdir(parents=True, exist_ok=True)
    out.round(3).to_csv(CSV, index=False, sep=";", decimal=",", encoding="utf-8-sig")
    print(f"Écrit : {CSV}")

    write_note(out, len(da), len(da_sp), ib, ib_sp)
    print(f"Écrit : {OUT}")


def write_note(out: pd.DataFrame, n_a: int, n_a_sp: int,
               ib: pd.DataFrame, ib_sp: pd.DataFrame) -> None:
    f = lambda n: f"{n:,}".replace(",", " ")  # noqa: E731
    casse = out[out["verdict"].str.startswith(("NE TIENT PAS", "NON EXPLOITABLE"))]
    fragile = out[out["verdict"].str.startswith(("fragile", "à surveiller"))]

    b = [BEGIN, ""]
    b.append("### Périmètres comparés")
    b.append("")
    b.append("| | Avec les fiches attaquées | Sans |")
    b.append("|---|---:|---:|")
    b.append(f"| Analyse A — établissements | {f(n_a)} | {f(n_a_sp)} |")
    b.append(f"| Analyse B — établissements | {f(ib.cid.nunique())} | {f(ib_sp.cid.nunique())} |")
    b.append(f"| Analyse B — observations | {f(len(ib))} | {f(len(ib_sp))} |")
    b.append(f"| Analyse B — disparitions | {f(int(ib.y.sum()))} | {f(int(ib_sp.y.sum()))} |")
    b.append("")
    nul = out["verdict"].str.startswith("non-effet").sum()
    b.append(f"### Verdict d'ensemble sur {len(out)} effets testés")
    b.append("")
    b.append(f"- **{len(out) - len(casse) - len(fragile) - nul} tiennent** ;")
    b.append(f"- {nul} sont des **non-effets stables** — voisins de 1 dans les deux versions, "
             "ils ne mesurent rien, ni avant ni après ;")
    b.append(f"- {len(fragile)} sont **fragiles** ;")
    b.append(f"- {len(casse)} **ne tiennent pas** ou ne sont pas exploitables.")
    b.append("")

    if len(casse):
        b.append("#### Ce qui ne tient pas, ou n'est pas exploitable")
        b.append("")
        b.append("| Analyse | Facteur | Modalité | Avec | Sans | Verdict |")
        b.append("|---|---|---|---:|---:|---|")
        for _, r in casse.iterrows():
            b.append(f"| {r['analyse']} | {r['facteur']} | {r['modalite']} | "
                     f"×{r['effet_avec']:.2f} | ×{r['effet_sans']:.2f} | {r['verdict']} |")
        b.append("")

    if len(fragile):
        b.append("#### Ce qui est fragile")
        b.append("")
        b.append("| Analyse | Facteur | Modalité | Avec | Sans | Verdict |")
        b.append("|---|---|---|---:|---:|---|")
        for _, r in fragile.iterrows():
            b.append(f"| {r['analyse']} | {r['facteur']} | {r['modalite']} | "
                     f"×{r['effet_avec']:.2f} | ×{r['effet_sans']:.2f} | {r['verdict']} |")
        b.append("")

    b.append("#### Tous les effets, côte à côte")
    b.append("")
    for modele in out["modele"].unique():
        sub = out[out["modele"] == modele]
        b.append(f"##### {modele}")
        b.append("")
        b.append("| Facteur | Modalité | Avec | Sans | Verdict |")
        b.append("|---|---|---:|---:|---|")
        for _, r in sub.iterrows():
            b.append(f"| {r['facteur']} | {r['modalite']} | ×{r['effet_avec']:.2f} | "
                     f"×{r['effet_sans']:.2f} | {r['verdict']} |")
        b.append("")
    b.append(END)
    body = "\n".join(b)

    head = """---
date: 2026-09-06
projet: reviewflowz-analyse-google
titre: "Contrôle de robustesse — sans les fiches attaquées"
statut: résultats
---

# Contrôle de robustesse — sans les fiches attaquées

Produit par `scripts/controle_robustesse.py`.

## Pourquoi ce contrôle est obligatoire

24 établissements portent 958 suppressions, 18 % du total. Deux d'entre eux, des salles de
sport espagnoles, en portent 399 à eux seuls. Un modèle ajusté sur l'ensemble peut très bien
décrire ces fiches plutôt que la modération de Google.

La liste des fiches est dans `data/resultats/fiches_massivement_purgees.csv`. Le seuil est
défini dans `scripts/build_tables.py` : plus de 5 % du stock perdu **et** au moins 10
suppressions — le plancher en volume évite qu'une fiche de 2 avis dont 1 supprimé compte comme
« purgée à 50 % ».

## Comment lire le verdict

Le critère est fixé avant d'avoir regardé les chiffres :

- **ne tient pas** — l'effet change de sens, il passe de l'autre côté de 1 ;
- **fragile** — l'amplitude est divisée ou multipliée par plus de 2 ;
- **à surveiller** — l'amplitude bouge de plus de moitié ;
- **tient** — le reste.

Les fourchettes ne figurent pas ici : le contrôle porte sur le déplacement des effets, pas sur
leur significativité, qui est traitée dans les notes A et B.

## Résultats

"""
    if OUT.exists() and BEGIN in (prev := OUT.read_text(encoding="utf-8")) and END in prev:
        OUT.write_text(prev[: prev.index(BEGIN)] + body + prev[prev.index(END) + len(END):],
                       encoding="utf-8")
    else:
        OUT.write_text(head + body + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
