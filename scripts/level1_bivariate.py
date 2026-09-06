"""
Niveau 1 — bivariés stratifiés sur l'âge, périmètre frais.

Remplace les bivariés en marge de la note du 2026-09-04, qui sont confondus par l'âge.

Méthode. L'unité est la ligne avis x vague de `fresh_hazard`, donc la grandeur mesurée est le
risque par vague (probabilité qu'un avis vivant disparaisse au passage suivant), et non une part
de suppressions. Deux chiffres par modalité :

  - risque brut          : morts / expositions, toutes tranches d'âge confondues ;
  - risque standardisé   : même calcul par tranche d'âge, puis repondéré sur la distribution
                           d'âge de l'ensemble du périmètre frais.

L'écart entre les deux mesure exactement la part de composition par âge. Le rapport de risque
est toujours donné sur la version standardisée.

Limite assumée : les intervalles sont poissoniens et ignorent le regroupement par établissement.
Ils servent à repérer les cellules trop minces, pas à conclure. L'inférence vient des modèles
A et B, avec erreurs-types groupées.

Usage :  .venv/bin/python scripts/level1_bivariate.py
"""

import pathlib
import sys

import duckdb
import numpy as np
import pandas as pd

SRC = pathlib.Path("data/build/fresh_hazard.parquet")
BIZ = pathlib.Path("data/build/business_features.parquet")
OUT = pathlib.Path("documentations/2026-09-06-premiers-resultats-facteur-par-facteur.md")
CSV = pathlib.Path("data/resultats/niveau1_facteur_par_facteur.csv")
BEGIN = "<!-- genere:level1 — regenere par scripts/level1_bivariate.py, ne pas editer a la main -->"
END = "<!-- /genere:level1 -->"
THIN = 20  # sous ce nombre de morts, la cellule est signalée comme peu fiable

AGE_BAND = """CASE WHEN age_days < 3 THEN '0-2j' WHEN age_days < 7 THEN '3-6j'
   WHEN age_days < 14 THEN '7-13j' WHEN age_days < 21 THEN '14-20j'
   WHEN age_days < 30 THEN '21-29j' ELSE '30j+' END"""

# (titre, expression SQL de la modalité, modalité de référence ou None pour la plus exposée)
FACTORS = [
    ("Note", "star::VARCHAR", "4"),
    ("Présence de texte",
     "CASE WHEN has_text THEN 'avec texte' ELSE 'note seule' END", "note seule"),
    ("Longueur du texte",
     """CASE WHEN NOT has_text THEN 'a. note seule' WHEN text_chars <= 50 THEN 'b. 1-50'
        WHEN text_chars <= 150 THEN 'c. 51-150' WHEN text_chars <= 400 THEN 'd. 151-400'
        ELSE 'e. 400+' END""", "a. note seule"),
    ("Photos jointes",
     """CASE WHEN n_photos = 0 THEN 'aucune' WHEN n_photos = 1 THEN '1'
        ELSE '2+' END""", "aucune"),
    ("Réponse du propriétaire",
     "CASE WHEN has_reply THEN 'avec réponse' ELSE 'sans réponse' END", "sans réponse"),
    ("Langue hors langue dominante de la fiche",
     "CASE WHEN lang_off_modal THEN 'langue étrangère' ELSE 'langue locale' END", "langue locale"),
    ("Avis édité depuis publication",
     "CASE WHEN was_edited THEN 'édité' ELSE 'non édité' END", "non édité"),
    ("Niveau Local Guide",
     """CASE WHEN lg_level_missing THEN 'a. absent' WHEN local_guide_level <= 3 THEN 'b. 1-3'
        WHEN local_guide_level <= 5 THEN 'c. 4-5' ELSE 'd. 6+' END""", "b. 1-3"),
    ("Signature compte neuf (niveau absent + compteur 0)",
     "CASE WHEN new_account THEN 'compte neuf' ELSE 'autre' END", "autre"),
    ("Nombre d'avis de l'auteur",
     """CASE WHEN rc_zero THEN 'a. compteur 0' WHEN reviewer_review_count <= 2 THEN 'b. 1-2'
        WHEN reviewer_review_count <= 20 THEN 'c. 3-20'
        WHEN reviewer_review_count <= 100 THEN 'd. 21-100' ELSE 'e. 100+' END""", "c. 3-20"),
    ("Présence de l'auteur sur plusieurs fiches du panel",
     """CASE WHEN author_n_panel_biz = 1 THEN '1 fiche' ELSE '2 fiches ou plus' END""", "1 fiche"),
    ("Rafale auteur (plusieurs avis le même jour)",
     "CASE WHEN author_same_day_burst THEN 'rafale' ELSE 'non' END", "non"),
    ("Région", "region", "EU"),
    ("Secteur", "industry", "food_beverage"),
    ("Taille du groupe", "bucket", "mono"),
]


def compute(c: duckdb.DuckDBPyConnection, expr: str) -> pd.DataFrame:
    """Risque brut et risque standardisé sur l'âge, par modalité."""
    d = c.sql(f"""
        SELECT {expr} AS modalite, {AGE_BAND} AS age_band,
               count(*) AS expo, sum(died::INT) AS morts,
               count(*) FILTER (NOT heavy_purge)               AS expo_hp,
               sum(CASE WHEN NOT heavy_purge THEN died::INT ELSE 0 END) AS morts_hp
        FROM h GROUP BY 1, 2
    """).df()
    d["modalite"] = d["modalite"].fillna("(non renseigné)")

    # poids de standardisation : distribution d'âge de tout le périmètre frais
    w = d.groupby("age_band")["expo"].sum()
    w = w / w.sum()

    rows = []
    for m, g in d.groupby("modalite", sort=True):
        g = g.set_index("age_band")
        expo, morts = int(g["expo"].sum()), int(g["morts"].sum())
        # repondération sur les seules tranches où la modalité est présente, puis renormalisation
        wm = w.reindex(g.index).fillna(0.0)
        haz_band = g["morts"] / g["expo"]
        std = float((haz_band * wm).sum() / wm.sum()) if wm.sum() > 0 else np.nan
        # même standardisation, en retirant les fiches ayant perdu plus de 5 % de leurs avis
        hb_hp = g["morts_hp"] / g["expo_hp"].replace(0, np.nan)
        w_hp = wm.where(g["expo_hp"] > 0, 0.0)
        std_hp = float((hb_hp.fillna(0) * w_hp).sum() / w_hp.sum()) if w_hp.sum() > 0 else np.nan
        rows.append({
            "modalite": m, "expo": expo, "morts": morts,
            "brut_pct": 100.0 * morts / expo if expo else np.nan,
            "std_pct": 100.0 * std,
            "std_hp_pct": 100.0 * std_hp,
            "morts_hp": int(g["morts_hp"].sum()),
            "couverture_age": f"{len(g)}/6",
        })
    return pd.DataFrame(rows)


def render(title: str, df: pd.DataFrame, ref: str | None) -> str:
    df = df.copy()
    if ref is None or ref not in set(df["modalite"]):
        ref = df.loc[df["expo"].idxmax(), "modalite"]
    base = df.loc[df["modalite"] == ref, "std_pct"].iloc[0]
    df["ratio"] = df["std_pct"] / base if base else np.nan
    base_hp = df.loc[df["modalite"] == ref, "std_hp_pct"].iloc[0]
    df["ratio_hp"] = df["std_hp_pct"] / base_hp if base_hp else np.nan

    out = [f"### {title}\n",
           "| | Observations | Disparitions | Risque brut | Risque à âge comparable | Écart | "
           "Écart hors 24 fiches purgées |",
           "|---|---:|---:|---:|---:|---:|---:|"]
    for _, r in df.iterrows():
        flag = " (trop peu pour conclure)" if r["morts"] < THIN else ""
        name = f"**{r['modalite']}** (réf.)" if r["modalite"] == ref else r["modalite"]
        ratio = "réf." if r["modalite"] == ref else f"×{r['ratio']:.2f}"
        if r["modalite"] == ref:
            ratio_hp = "réf."
        elif r["morts_hp"] < THIN:
            ratio_hp = "—"
        else:
            ratio_hp = f"×{r['ratio_hp']:.2f}"
        out.append(
            f"| {name} | {r['expo']:,} | {r['morts']:,}{flag} | {r['brut_pct']:.3f} % "
            f"| {r['std_pct']:.3f} % | {ratio} | {ratio_hp} |".replace(",", "\u202f"))

    # signaler les modalités où la composition par âge portait l'essentiel de l'écart
    drift = df[(df["morts"] >= THIN) & (df["brut_pct"] > 0)].copy()
    drift["ecart"] = (drift["std_pct"] - drift["brut_pct"]).abs() / drift["brut_pct"]
    big = drift[drift["ecart"] > 0.25]
    if len(big):
        items = ", ".join(
            f"{r['modalite']} ({r['brut_pct']:.3f} % → {r['std_pct']:.3f} %)"
            for _, r in big.iterrows())
        out.append(f"\nLe recalcul à âge comparable déplace nettement le chiffre : {items}. "
                   f"Une partie de l'effet apparent n'était que de la différence d'âge.")
    out.append("")
    return "\n".join(out)


def main() -> None:
    if not SRC.exists():
        sys.exit(f"Table absente : {SRC}. Lancer d'abord scripts/build_tables.py")
    c = duckdb.connect(config={'memory_limit': '1GB'})
    c.sql(f"CREATE VIEW h0 AS SELECT * FROM '{SRC}'")
    c.sql(f"CREATE VIEW b AS SELECT cid, heavy_purge FROM '{BIZ}'")
    # heavy_purge = plus de 5 % des avis perdus ET au moins 10 suppressions. 24 fiches.
    c.sql("CREATE VIEW h AS SELECT h0.*, coalesce(b.heavy_purge, FALSE) AS heavy_purge "
          "FROM h0 LEFT JOIN b USING (cid)")

    expo, morts = c.sql("SELECT count(*), sum(died::INT) FROM h").fetchone()
    n_rev, n_del = c.sql("""
        SELECT count(DISTINCT row_id), count(DISTINCT row_id) FILTER (died) FROM h""").fetchone()

    fmt = lambda n: f"{n:,}".replace(",", "\u202f")
    head = f"""---
date: 2026-09-06
projet: reviewflowz-analyse-google
titre: "Premiers résultats, facteur par facteur"
statut: résultats
---

# Premiers résultats, facteur par facteur

Sur les **{fmt(n_rev)} avis de moins de 30 jours** du panel, dont **{fmt(n_del)} ont été
supprimés** pendant les quatorze jours de collecte.

Tableaux produits par `scripts/level1_bivariate.py`. Ils remplacent ceux de la note du
4 septembre, qui comparaient des avis d'âges différents et donnaient des résultats faussés.

## Comment lire ces tableaux

**Le risque quotidien.** Chaque avis a été observé à chaque passage du robot. La question posée
est : à ce passage, est-il encore là ? Le risque est la part d'avis qui disparaissent d'un
passage au suivant. Un risque de 0,5 % veut dire : sur 1 000 avis en ligne, 5 auront disparu au
passage suivant.

Ce n'est pas la probabilité qu'un avis finisse par être supprimé — celle-là s'accumule sur
plusieurs jours et elle est bien plus élevée.

**Les colonnes.**

- *Observations* : le nombre de fois où un avis a été vérifié. Un avis vu à dix passages compte
  pour dix. C'est ce qui permet de comparer équitablement des avis suivis plus ou moins
  longtemps.
- *Disparitions* : le nombre d'avis effectivement supprimés.
- *Risque brut* : disparitions divisées par observations.
- *Risque à âge comparable* : le même calcul, mais refait tranche d'âge par tranche d'âge, puis
  recombiné comme si tous les groupes avaient la même répartition d'âge. **C'est la colonne à
  lire.**
- *Écart* : le rapport entre le risque du groupe et celui de la ligne de référence, signalée en
  gras. « ×2 » se lit « deux fois plus supprimé ».

**Quand les deux colonnes de risque diffèrent, l'écart entre elles mesure exactement ce que la
différence d'âge apportait.** Une ligne signalée « trop peu pour conclure » compte moins de
{THIN} disparitions.

**Ce que ces tableaux ne font pas.** Ils regardent un facteur à la fois. Deux facteurs liés — par
exemple le niveau Local Guide et le nombre d'avis de l'auteur — se comptent donc deux fois. Il
faut les modèles A et B pour savoir lequel compte vraiment. Aucune marge d'erreur n'est donnée
ici : elle serait trompeuse tant que le regroupement par établissement n'est pas traité, ce que
seuls les modèles font.

## Résultats

"""

    blocs, lignes = [], []
    for title, expr, ref in FACTORS:
        df = compute(c, expr)
        blocs.append(render(title, df, ref))
        lignes.append(df.assign(facteur=title))
    tables = "\n".join(blocs)

    # Même contenu que les tableaux, en CSV ouvrable dans Excel.
    CSV.parent.mkdir(parents=True, exist_ok=True)
    (pd.concat(lignes)
       .rename(columns={"expo": "observations", "morts": "disparitions",
                        "brut_pct": "risque_brut_pct", "std_pct": "risque_age_comparable_pct",
                        "std_hp_pct": "risque_hors_fiches_purgees_pct",
                        "morts_hp": "disparitions_hors_fiches_purgees"})
       [["facteur", "modalite", "observations", "disparitions",
         "risque_brut_pct", "risque_age_comparable_pct",
         "disparitions_hors_fiches_purgees", "risque_hors_fiches_purgees_pct",
         "couverture_age"]]
       .round({"risque_brut_pct": 4, "risque_age_comparable_pct": 4,
               "risque_hors_fiches_purgees_pct": 4})
       .to_csv(CSV, index=False, sep=";", decimal=",", encoding="utf-8-sig"))
    print(f"Écrit : {CSV}")
    block = f"{BEGIN}\n{tables}\n{END}"

    # La partie générée vit entre marqueurs ; tout ce qui est écrit à la main autour survit
    # à un re-run (même convention que les blocs orga:auto des notes du projet).
    if OUT.exists() and BEGIN in (prev := OUT.read_text(encoding="utf-8")) and END in prev:
        head_part = prev[: prev.index(BEGIN)]
        tail_part = prev[prev.index(END) + len(END) :]
        OUT.write_text(head_part + block + tail_part, encoding="utf-8")
    else:
        OUT.write_text(head + block + "\n", encoding="utf-8")
    print(f"Écrit : {OUT}")
    print(f"Périmètre : {n_rev} avis, {n_del} supprimés, {expo} expositions, {morts} morts")


if __name__ == "__main__":
    main()
