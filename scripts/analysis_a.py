"""
Analyse A — quel établissement subit une intervention de Google ?

L'unité est l'établissement, pas l'avis. C'est le pendant de l'analyse B : celle-ci compare des
avis à l'intérieur d'une fiche, celle-là compare des fiches entre elles. C'est donc ici, et
seulement ici, que le secteur, la région et la taille du groupe peuvent être mesurés.

Deux questions posées séparément, parce qu'elles n'ont pas la même réponse :

  1. **Être touché** — la fiche a-t-elle perdu au moins un avis récent ? Modèle sur les
     9 048 établissements.
  2. **L'ampleur** — parmi les fiches touchées, quelle part du stock récent est partie ?
     Modèle sur les seules fiches touchées.

Une fiche peut être fréquemment effleurée sans jamais être purgée, et l'inverse existe. Les
mélanger produirait un résultat ininterprétable.

La trajectoire de note n'entre pas au modèle : elle est mesurée pendant la fenêtre
d'observation, or supprimer des avis fait mécaniquement bouger la note. Elle serait donc
potentiellement une conséquence de la purge, pas une cause. Elle est reportée à part, en
description, avec cette réserve.

Erreurs-types groupées par pays x secteur : les établissements d'un même marché partagent des
conditions que le modèle ne voit pas. Faute d'identifiant d'enseigne dans l'export, c'est le
regroupement le plus englobant disponible.

Usage :  uv run scripts/analysis_a.py
"""

import pathlib
import sys
import warnings

import duckdb
import numpy as np
import pandas as pd
import statsmodels.api as sm

BIZ = pathlib.Path("data/build/business_features.parquet")
OUT = pathlib.Path("documentations/2026-09-06-analyse-a-quel-etablissement.md")
CSV = pathlib.Path("data/resultats/analyse_a_effets.csv")
BEGIN = "<!-- genere:analysea — regenere par scripts/analysis_a.py, ne pas editer a la main -->"
END = "<!-- /genere:analysea -->"

SQL = """
SELECT cid, region, country, industry, bucket,
       n_reviews_panel, n_fresh, n_fresh_deleted, velocity_30d,
       mean_star_panel, mean_star_delta,
       (n_fresh_deleted > 0)::INT AS touche,
       n_fresh_deleted::DOUBLE / nullif(n_fresh, 0) AS part_purgee
FROM 'BIZ'
WHERE n_fresh >= 10          -- sous 10 avis récents, « touché » est du bruit
"""

# (colonne, libellé, modalité de référence)
BLOCKS = [
    ("vitesse", "Vitesse de collecte — part du stock reçue en 30 jours", "b_1_3pct"),
    ("secteur", "Secteur", "food_beverage"),
    ("taille", "Taille du groupe", "mono"),
    ("region", "Région", "EU"),
    ("volume", "Nombre total d'avis de la fiche", "c_250_1000"),
    ("note", "Note moyenne de la fiche", "c_4_5_a_4_8"),
    ("exposition", "Nombre d'avis récents de la fiche", "b_25_60"),
]

LABELS = {
    "a_moins_1pct": "moins de 1 %", "b_1_3pct": "1 à 3 %", "c_3_10pct": "3 à 10 %",
    "d_10pct_plus": "10 % et plus",
    "mono": "site unique", "small": "groupe de 4 à 10 sites", "large": "groupe de 20 à 50 sites",
    "EU": "Europe", "US": "États-Unis",
    "a_moins_100": "moins de 100", "b_100_250": "100 à 250", "c_250_1000": "250 à 1 000",
    "d_1000_plus": "plus de 1 000",
    "a_moins_4": "moins de 4,0", "b_4_a_4_5": "4,0 à 4,5", "c_4_5_a_4_8": "4,5 à 4,8",
    "d_4_8_plus": "4,8 et plus",
    "a_10_25": "10 à 25 avis récents", "b_25_60": "25 à 60", "c_60_150": "60 à 150",
    "d_150_plus": "plus de 150",
}


def load() -> pd.DataFrame:
    if not BIZ.exists():
        sys.exit(f"Table absente : {BIZ}. Lancer d'abord : uv run scripts/build_tables.py")
    d = duckdb.connect(config={'memory_limit': '1GB'}).sql(SQL.replace("'BIZ'", f"'{BIZ.as_posix()}'")).df()

    d["vitesse"] = pd.cut(d["velocity_30d"], [-1, .01, .03, .10, 9],
                          labels=["a_moins_1pct", "b_1_3pct", "c_3_10pct", "d_10pct_plus"])
    d["volume"] = pd.cut(d["n_reviews_panel"], [-1, 100, 250, 1000, 10**9],
                         labels=["a_moins_100", "b_100_250", "c_250_1000", "d_1000_plus"])
    d["note"] = pd.cut(d["mean_star_panel"], [0, 4.0, 4.5, 4.8, 5.01],
                       labels=["a_moins_4", "b_4_a_4_5", "c_4_5_a_4_8", "d_4_8_plus"])
    # Exposition : sans ce contrôle, « être touché » mesurerait surtout la taille du stock récent.
    d["exposition"] = pd.cut(d["n_fresh"], [-1, 25, 60, 150, 10**9],
                             labels=["a_10_25", "b_25_60", "c_60_150", "d_150_plus"])
    d = d.rename(columns={"industry": "secteur", "bucket": "taille"})
    # regroupement pour les erreurs-types : le marché, faute d'identifiant d'enseigne
    d["marche"] = d["country"] + "_" + d["secteur"]
    return d.dropna(subset=["vitesse", "volume", "note", "exposition"])


def design(d: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    parts, names = [], []
    for col, _, ref in BLOCKS:
        du = pd.get_dummies(d[col].astype(str), prefix=col, dtype=float)
        refcol = f"{col}_{ref}"
        if refcol in du.columns:
            du = du.drop(columns=[refcol])
        parts.append(du)
        names += list(du.columns)
    X = pd.concat(parts, axis=1)
    X.insert(0, "constante", 1.0)
    return X, ["constante"] + names


def fit(d: pd.DataFrame, y: np.ndarray, label: str) -> pd.DataFrame:
    X, names = design(d)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        res = sm.Logit(y, X.to_numpy()).fit(disp=False, maxiter=200, cov_type="cluster",
                                            cov_kwds={"groups": d["marche"].to_numpy()})
    co, se = pd.Series(res.params, index=names), pd.Series(res.bse, index=names)
    rows = []
    for col, titre, ref in BLOCKS:
        for n in names:
            if not n.startswith(f"{col}_"):
                continue
            mod = n[len(col) + 1:]
            lo, hi = np.exp(co[n] - 1.96 * se[n]), np.exp(co[n] + 1.96 * se[n])
            rows.append({"modele": label, "facteur": titre,
                         "modalite": LABELS.get(mod, mod), "reference": LABELS.get(ref, ref),
                         "effet": np.exp(co[n]), "borne_basse": lo, "borne_haute": hi,
                         "ecart_net": "oui" if (lo > 1 or hi < 1) else "non"})
    return pd.DataFrame(rows)


def main() -> None:
    d = load()
    print(f"Établissements retenus (au moins 10 avis récents) : {len(d)}")
    print(f"  dont touchés : {int(d.touche.sum())}")

    a = fit(d, d["touche"].to_numpy(), "Être touché")

    # Ampleur : parmi les fiches touchées, part du stock récent perdue.
    # Logistique sur proportion, pondérée par le nombre d'avis récents.
    t = d[d["touche"] == 1].copy()
    print(f"  fiches touchées retenues pour l'ampleur : {len(t)}")
    X, names = design(t)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        res = sm.GLM(t["part_purgee"].to_numpy(), X.to_numpy(),
                     family=sm.families.Binomial(), freq_weights=t["n_fresh"].to_numpy()
                     ).fit(cov_type="cluster", cov_kwds={"groups": t["marche"].to_numpy()})
    co, se = pd.Series(res.params, index=names), pd.Series(res.bse, index=names)
    rows = []
    for col, titre, ref in BLOCKS:
        for n in names:
            if not n.startswith(f"{col}_"):
                continue
            mod = n[len(col) + 1:]
            lo, hi = np.exp(co[n] - 1.96 * se[n]), np.exp(co[n] + 1.96 * se[n])
            rows.append({"modele": "Ampleur de la purge", "facteur": titre,
                         "modalite": LABELS.get(mod, mod), "reference": LABELS.get(ref, ref),
                         "effet": np.exp(co[n]), "borne_basse": lo, "borne_haute": hi,
                         "ecart_net": "oui" if (lo > 1 or hi < 1) else "non"})
    b = pd.DataFrame(rows)

    out = pd.concat([a, b], ignore_index=True)
    CSV.parent.mkdir(parents=True, exist_ok=True)
    out.round(3).to_csv(CSV, index=False, sep=";", decimal=",", encoding="utf-8-sig")
    print(f"Écrit : {CSV}")
    write_note(out, len(d), int(d.touche.sum()), len(t))
    print(f"Écrit : {OUT}")


def write_note(out: pd.DataFrame, n: int, n_touche: int, n_ampleur: int) -> None:
    f = lambda x: f"{x:,}".replace(",", " ")  # noqa: E731
    blocks = [BEGIN]
    for modele in out["modele"].unique():
        blocks.append(f"## {modele}\n")
        sub = out[out["modele"] == modele]
        for titre in sub["facteur"].unique():
            g = sub[sub["facteur"] == titre]
            blocks.append(f"### {titre}\n")
            blocks.append(f"Comparé à : **{g['reference'].iloc[0]}**.\n")
            blocks.append("| Modalité | Effet | Fourchette | Écart net ? |")
            blocks.append("|---|---:|---:|---|")
            for _, r in g.iterrows():
                blocks.append(f"| {r['modalite']} | ×{r['effet']:.2f} | "
                              f"{r['borne_basse']:.2f} à {r['borne_haute']:.2f} | "
                              f"{r['ecart_net']} |")
            blocks.append("")
    blocks.append(END)
    body = "\n".join(blocks)

    head = f"""---
date: 2026-09-06
projet: reviewflowz-analyse-google
titre: "Analyse A — quel établissement subit une intervention ?"
statut: résultats
---

# Analyse A — quel établissement subit une intervention ?

Produit par `scripts/analysis_a.py`.

## Ce que compare cette analyse

**Des établissements entre eux**, et non des avis. C'est le pendant de l'analyse B : celle-ci
regarde ce qui distingue deux avis d'une même fiche, celle-là ce qui distingue deux fiches.

C'est donc **ici, et seulement ici, que le secteur, la région et la taille du groupe peuvent
être mesurés**. Dans l'analyse B ils sont identiques pour tous les avis d'une même fiche, donc
invisibles.

## Deux questions, deux modèles

Elles n'ont pas la même réponse, et les mélanger donnerait un résultat ininterprétable.

**Être touché** — la fiche a-t-elle perdu au moins un avis récent ? Sur {f(n)} établissements,
dont {f(n_touche)} touchés.

**L'ampleur** — parmi les fiches touchées, quelle part du stock récent est partie ? Sur les
{f(n_ampleur)} fiches concernées, pondéré par leur nombre d'avis récents.

Une fiche peut être effleurée en permanence sans jamais être purgée, et l'inverse existe.

## Comment lire

**L'effet** se lit comme un rapport, la modalité de référence valant 1. « ×2 » signifie deux
fois plus de risque d'être touché, ou une purge deux fois plus étendue, toutes les autres
caractéristiques étant égales.

**La fourchette** tient compte du fait que les établissements d'un même marché — même pays,
même secteur — partagent des conditions que le modèle ne voit pas. Sans cette correction les
fourchettes seraient trop étroites. Faute d'identifiant d'enseigne dans l'export, le marché est
le regroupement le plus englobant disponible.

**Écart net** vaut « oui » quand la fourchette ne contient pas 1.

## Périmètre

Les fiches de moins de 10 avis récents sont écartées : sur trois avis, « touché » relève du
hasard. C'est la même correction que celle appliquée au seuil de fiche purgée.

## Résultats

"""
    if OUT.exists() and BEGIN in (prev := OUT.read_text(encoding="utf-8")) and END in prev:
        OUT.write_text(prev[: prev.index(BEGIN)] + body + prev[prev.index(END) + len(END):],
                       encoding="utf-8")
    else:
        OUT.write_text(head + body + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
