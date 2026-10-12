#!/usr/bin/env python3
"""Prénoms, vitesse de collecte et suppressions : la question d'Axel du 2026-10-06.

    PYTHONPATH=".venv/Lib/site-packages;outils" <python uv> etudes-ponctuelles/2026-10-06-velocite-prenom/calcul.py

Axel (mail du 2026-10-06) : à fiche égale, un avis qui cite un prénom n'est pas plus
supprimé ; mais les fiches dont beaucoup d'avis citent un prénom perdent plus d'avis, ce
qu'il attribue à leur vitesse de collecte. A-t-on testé l'effet de la vitesse seule ?

------------------------------------------------------------------------------
LES DONNÉES
------------------------------------------------------------------------------
Prénom : data/local/axel_file/reviews_name_enriched.parquet (annotation d'Axel,
  has_name), avis 4-5 étoiles avec texte, joint par review_id à
  data/local/features_reviews_doublons_cleaned_all.parquet (2 675 178 avis).
Suppression : `supprime` de notre base (absent 2 jours de suite ou plus, fiche relevée),
  du 11 au 24 août 2026 ; pas la colonne `deleted` d'Axel, qui compte 388 doublons.
Écartés : les six enseignes, les fiches qui ne sont plus relevées, les avis dont la
  fenêtre d'observation est nulle.

Par fiche, calculé sur ce qui précède le corpus 03C (avant le 7 août 2026) :
  part de prénoms   part de ses avis 4-5 étoiles avec texte qui citent un prénom ;
                    classes d'Axel : moins de 10 %, 10-25 %, 25-50 %, 50 % et plus ;
                    au moins 20 avis annotés, sinon la fiche sort des étapes 1 à 3
                    (et forme une classe à part, non affichée, à l'étape 4)
  vitesse           avis reçus par mois, toutes notes, du 7 août 2025 au 6 août 2026
                    (définition d'Axel), dans reviews_doublons_cleaned_all ; en
                    log2 dans les modèles (+1 = la vitesse double), plancher à
                    1 avis par an

------------------------------------------------------------------------------
LES ÉTAPES
------------------------------------------------------------------------------
1. Le constat d'Axel : taux de suppression sur deux semaines par classe de part de
   prénoms, tous âges d'avis confondus.
2. Graphique 1 : le même taux, par quart de vitesse et par classe de part de prénoms.
3. Régressions logistiques, avis de tous âges, regroupés par fiche et classe d'âge
   (même résultat qu'avis par avis, plus léger), erreurs groupées par fiche, à
   secteur, taille et région égaux :
     M1  part de prénoms
     M2  + vitesse
     M3  + âge de l'avis au 11 août (publié pendant le suivi, 0-30 j, 31-90 j,
         91-365 j, 1-3 ans, plus de 3 ans)
4. Avis neufs (03C, publiés du 7 au 17 août, sans les enseignes), tous du même âge :
   modèle habituel du 07G, jour par jour (prénom de l'avis, photo, pic, réponse ;
   secteur, taille, région), avec le jour d'âge, + part de prénoms de la fiche
   + vitesse.

Sorties : livrables/restitution_finale/graphiques/faits-saignants/
  graphiques/velocite_prenom_taux.png, velocite_prenom_modeles.png
  donnees/velocite_prenom_taux.csv, velocite_prenom_modeles.csv, velocite_prenom_fiches.csv
"""
import importlib.util
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

RACINE = Path(__file__).resolve().parents[2]
PY = RACINE / "logistic-regression-study" / "python"
_spec = importlib.util.spec_from_file_location("h07", PY / "07H_reponse_vite_souvent.py")
h07 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(h07)
g07, f07, sm = h07.g07, h07.f07, h07.sm
from local import connexion  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
AXEL = RACINE / "data" / "local" / "axel_file" / "reviews_name_enriched.parquet"
FEATURES = RACINE / "data" / "local" / "features_reviews_doublons_cleaned_all.parquet"
SORTIE = RACINE / "livrables" / "restitution_finale" / "graphiques" / "faits-saignants"
MIN_AVIS = 20
CLASSES_PRENOM = ["moins de 10 %", "10-25 %", "25-50 %", "50 % et plus"]
CODES_PRENOM = {"10-25 %": "p_10_25", "25-50 %": "p_25_50", "50 % et plus": "p_50_100"}
AGES = ["plus de 3 ans", "1-3 ans", "91-365 j", "31-90 j", "0-30 j", "publié pendant le suivi"]

BLEU, GRIS = "#2a78d6", "#c3c2b7"
SEQ = ["#c6dbf2", "#86b4e6", "#2a78d6", "#0e3f7e"]
ENCRE, ENCRE_2, GRILLE, FOND = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"


def virgule(x: float, d: int = 0) -> str:
    return f"{x:.{d}f}".replace(".", ",").replace("-", "−")


def espace(n: float) -> str:
    return f"{n:,.0f}".replace(",", " ")


# ---------------------------------------------------------------------------
# Données
# ---------------------------------------------------------------------------

def fiches(con) -> pd.DataFrame:
    f = con.execute(f"""
        WITH prenom AS (
          SELECT cid, count(*) AS avis_annotes, avg(has_name::INT) AS part_prenom
          FROM '{AXEL.as_posix()}'
          WHERE CAST(created_at AS DATE) < DATE '2026-08-07'
          GROUP BY cid),
        vitesse AS (
          SELECT cid, count(*) / 12.0 AS avis_par_mois
          FROM reviews_doublons_cleaned_all
          WHERE CAST(created_at AS DATE) BETWEEN DATE '2025-08-07' AND DATE '2026-08-06'
          GROUP BY cid)
        SELECT b.cid, b.industry, b.bucket, if(b.country = 'US', 'US', 'Europe') AS region,
               coalesce(p.avis_annotes, 0) AS avis_annotes, p.part_prenom,
               coalesce(v.avis_par_mois, 0) AS avis_par_mois
        FROM businesses b
        LEFT JOIN prenom p USING (cid) LEFT JOIN vitesse v USING (cid)""").df()
    f["classe_prenom"] = pd.cut(f["part_prenom"], [-1, 0.10, 0.25, 0.50, 2],
                                right=False, labels=CLASSES_PRENOM).astype(str)
    f.loc[f["avis_annotes"] < MIN_AVIS, "classe_prenom"] = "moins de 20 avis"
    f["log2_vitesse"] = np.log2(f["avis_par_mois"].clip(lower=1 / 12))
    return f


def avis_tous_ages(con) -> pd.DataFrame:
    return con.execute(f"""
        SELECT a.cid, a.has_name, f.supprime,
               date_diff('day', f.created_at_day, DATE '2026-08-11') AS age_j
        FROM '{AXEL.as_posix()}' a
        JOIN '{FEATURES.as_posix()}' f USING (review_id)
        WHERE NOT (f.chaine_antiparasitaire OR f.salle_espagnole)
          AND NOT f.fiche_plus_relevee AND f.fenetre_observation_j > 0""").df()


def classe_age(age: pd.Series) -> pd.Series:
    return pd.Series(np.select(
        [age < 0, age <= 30, age <= 90, age <= 365, age <= 1095],
        ["publié pendant le suivi", "0-30 j", "31-90 j", "91-365 j", "1-3 ans"],
        "plus de 3 ans"), index=age.index)


# ---------------------------------------------------------------------------
# Modèles
# ---------------------------------------------------------------------------

def indicatrices(d: pd.DataFrame, col: str, ref: str, prefixe: str) -> pd.DataFrame:
    x = pd.get_dummies(d[col].astype(str), prefix=prefixe, dtype=float)
    return x.drop(columns=f"{prefixe}_{ref}", errors="ignore")


def modele_tous_ages(g: pd.DataFrame, vitesse: bool, age: bool):
    """Binomiale sur les cellules fiche x classe d'âge."""
    X = [g[list(CODES_PRENOM.values())].astype(float),
         indicatrices(g, "industry", "automotive", "secteur"),
         indicatrices(g, "bucket", "mono", "taille"),
         (g["region"] == "US").astype(float).rename("region_US").to_frame()]
    if vitesse:
        X.append(g[["log2_vitesse"]])
    if age:
        X.append(indicatrices(g, "classe_age", "plus de 3 ans", "age"))
    X = sm.add_constant(pd.concat(X, axis=1), has_constant="add")
    y = np.column_stack([g["supprimes"], g["avis"] - g["supprimes"]]).astype(float)
    return sm.GLM(y, X, family=sm.families.Binomial()).fit(
        cov_type="cluster", cov_kwds={"groups": g["cid"].factorize()[0]})


def lire(res, variables, modele) -> list[dict]:
    ic = res.conf_int()
    return [{"modele": modele, "variable": v, "rapport_de_cotes": float(np.exp(res.params[v])),
             "borne_basse": float(np.exp(ic.loc[v, 0])), "borne_haute": float(np.exp(ic.loc[v, 1])),
             "p_value": float(res.pvalues[v])} for v in variables if v in res.params]


def modele_avis_neufs(fi: pd.DataFrame, exclues=(), nom="M4 avis neufs (03C)"):
    df = h07.avis()
    df = df[~df["enseigne"] & ~df["cid"].isin(exclues)].merge(
        fi[["cid", "classe_prenom", "log2_vitesse"]], on="cid", how="left")
    p = g07.avis_jours(df)
    p = p.merge(df[["review_id", "classe_prenom", "log2_vitesse"]], on="review_id", how="left")
    p["repondu"] = 1 - p["sans_reponse"]
    for classe, code in CODES_PRENOM.items():
        p[code] = (p["classe_prenom"] == classe).astype(int)
    p["p_moins_20"] = (p["classe_prenom"] == "moins de 20 avis").astype(int)
    variables = ["repondu"] + list(CODES_PRENOM.values()) + ["p_moins_20", "log2_vitesse"]
    res = h07.ajuster(p, variables, age=True)
    info = {"avis": int(df["review_id"].nunique()), "suppressions": int(p["y"].sum()),
            "fiches": int(df["cid"].nunique())}
    return lire(res, ["prenom"] + list(CODES_PRENOM.values()) + ["log2_vitesse"], nom), info


# ---------------------------------------------------------------------------
# Graphiques
# ---------------------------------------------------------------------------

def graphique_taux(t: pd.DataFrame, titre: str, sous_titre: str, chemin: Path) -> None:
    fig, ax = plt.subplots(figsize=(8.5, 4.6), dpi=150)
    fig.patch.set_facecolor(FOND)
    ax.set_facecolor(FOND)
    quarts = list(t["quart_vitesse"].cat.categories)
    largeur = 0.2
    for j, (classe, couleur) in enumerate(zip(CLASSES_PRENOM, SEQ)):
        for i, q in enumerate(quarts):
            r = t[(t["quart_vitesse"] == q) & (t["classe_prenom"] == classe)]
            if r.empty:
                continue
            r = r.iloc[0]
            x = i + (j - 1.5) * largeur
            ax.bar(x, r["pour_1000"], width=largeur * 0.92, color=couleur, zorder=2)
            ax.annotate(virgule(r["pour_1000"], 1), (x, r["pour_1000"]), xytext=(0, 2),
                        textcoords="offset points", ha="center", fontsize=6.5, color=ENCRE)
    ax.set_xticks(range(len(quarts)))
    ax.set_xticklabels(quarts, fontsize=8, color=ENCRE)
    ax.set_ylabel("avis supprimés pour 1 000, du 11 au 24 août", color=ENCRE_2, fontsize=8)
    ax.tick_params(colors=ENCRE_2, labelsize=8, length=0)
    ax.grid(axis="y", color=GRILLE, lw=0.8, zorder=0)
    for cote in ["top", "right", "left"]:
        ax.spines[cote].set_visible(False)
    ax.spines["bottom"].set_color(GRILLE)
    from matplotlib.patches import Patch
    fig.legend(handles=[Patch(color=c, label=f"fiche dont {k} des avis citent un prénom")
                        for k, c in zip(CLASSES_PRENOM, SEQ)],
               loc="upper left", bbox_to_anchor=(0.005, 0.80), ncol=2, frameon=False,
               fontsize=7.5, labelcolor=ENCRE)
    fig.text(0.01, 0.975, titre, va="top", fontsize=11, color=ENCRE)
    fig.text(0.01, 0.91, sous_titre, va="top", fontsize=7.5, color=ENCRE_2, linespacing=1.5)
    fig.tight_layout(rect=(0, 0, 1, 0.70))
    fig.savefig(chemin, facecolor=FOND)
    plt.close(fig)


def graphique_modeles(m: pd.DataFrame, titre: str, sous_titre: str, chemin: Path) -> None:
    R3 = "R3 tous âges, sans le 1 % de fiches les plus touchées"
    panneaux = [
        ("p_50_100", "Fiche dont 50 % et plus des avis citent un prénom,\nface à moins de 10 %",
         ["M1 secteur, taille, région égaux", "M2 + vitesse égale", "M3 + âge des avis égal",
          R3, "M4 avis neufs (03C)"]),
        ("log2_vitesse", "Vitesse de collecte de la fiche multipliée par 2",
         ["M2 + vitesse égale", "M3 + âge des avis égal", R3, "M4 avis neufs (03C)"])]
    noms = {"M1 secteur, taille, région égaux": "1. brut",
            "M2 + vitesse égale": "2. à vitesse\négale",
            "M3 + âge des avis égal": "3. à vitesse et\nâge égaux",
            R3: "4. idem, sans\nles fiches les\nplus touchées",
            "M4 avis neufs (03C)": "5. avis neufs,\nmême âge"}
    noms_v = {"M2 + vitesse égale": "2. à part de\nprénoms égale",
              "M3 + âge des avis égal": "3. + âge\négal",
              R3: "4. idem, sans\nles fiches les\nplus touchées",
              "M4 avis neufs (03C)": "5. avis neufs,\nmême âge"}
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.8), dpi=150,
                             gridspec_kw={"width_ratios": [5, 4]}, sharey=True)
    fig.patch.set_facecolor(FOND)
    toutes = m[m["variable"].isin(["p_50_100", "log2_vitesse"])]
    hi = 100 * (toutes["borne_haute"].max() - 1)
    lo = min(-30, 100 * (toutes["borne_basse"].min() - 1))
    for ax, (variable, titre_p, modeles) in zip(axes, panneaux):
        ax.set_facecolor(FOND)
        for i, mod in enumerate(modeles):
            r = m[(m["modele"] == mod) & (m["variable"] == variable)].iloc[0]
            e, b, h = (100 * (r[c] - 1) for c in ("rapport_de_cotes", "borne_basse", "borne_haute"))
            net = r["p_value"] < 0.05
            ax.bar(i, e, width=0.6, color=BLEU if net else GRIS, zorder=2)
            ax.plot([i, i], [b, h], color=ENCRE, lw=1.2, zorder=3)
            for v in (b, h):
                ax.plot([i - 0.06, i + 0.06], [v, v], color=ENCRE, lw=1.2, zorder=3)
            ax.annotate(f"{'+' if e > 0 else ''}{virgule(e)} %", (i, h if e >= 0 else b),
                        xytext=(0, 4 if e >= 0 else -4), textcoords="offset points",
                        ha="center", va="bottom" if e >= 0 else "top", fontsize=9,
                        fontweight="bold" if net else "normal", color=ENCRE)
        ax.axhline(0, color=ENCRE_2, lw=0.9, ls=(0, (4, 3)), zorder=1)
        ax.set_xticks(range(len(modeles)))
        ax.set_xticklabels([(noms if variable == "p_50_100" else noms_v)[mo] for mo in modeles],
                           fontsize=7.5, color=ENCRE)
        ax.set_title(titre_p, fontsize=9, color=ENCRE, loc="left")
        ax.tick_params(colors=ENCRE_2, labelsize=8, length=0)
        ax.grid(axis="y", color=GRILLE, lw=0.8, zorder=0)
        for cote in ["top", "right", "left"]:
            ax.spines[cote].set_visible(False)
        ax.spines["bottom"].set_color(GRILLE)
        ax.set_xlim(-0.6, len(modeles) - 0.4)
    axes[0].set_ylim(lo - 0.12 * (hi - lo), hi + 0.15 * (hi - lo))
    axes[0].yaxis.set_major_formatter(lambda v, _: f"{'+' if v > 0 else ''}{v:.0f} %".replace("-", "−"))
    axes[0].set_ylabel("écart du risque de suppression", color=ENCRE_2, fontsize=8)
    fig.text(0.01, 0.975, titre, va="top", fontsize=11, color=ENCRE)
    fig.text(0.01, 0.915, sous_titre, va="top", fontsize=7.5, color=ENCRE_2, linespacing=1.5)
    fig.tight_layout(rect=(0, 0, 1, 0.74), w_pad=2)
    fig.savefig(chemin, facecolor=FOND)
    plt.close(fig)


# ---------------------------------------------------------------------------

def main():
    con = connexion("6GB")
    fi = fiches(con)
    a = avis_tous_ages(con).merge(fi, on="cid", how="left")
    a = a[a["classe_prenom"].isin(CLASSES_PRENOM)].copy()
    a["classe_age"] = classe_age(a["age_j"])
    fa = fi[fi["cid"].isin(a["cid"])].copy()
    fa["quart_vitesse"] = pd.qcut(fa["avis_par_mois"], 4)
    bornes = fa["quart_vitesse"].cat.categories
    noms_q = [f"{q}e quart\n{virgule(b.left if i else 0, 1)} à {virgule(b.right, 1)} avis/mois"
              .replace("1e", "1er") for i, (q, b) in enumerate(zip(range(1, 5), bornes))]
    fa["quart_vitesse"] = fa["quart_vitesse"].cat.rename_categories(noms_q)
    a = a.merge(fa[["cid", "quart_vitesse"]], on="cid", how="left")
    print(f"avis de tous âges : {len(a)} avis, {a['cid'].nunique()} fiches, "
          f"{int(a['supprime'].sum())} suppressions")

    # Étape 1 : le constat d'Axel.
    e1 = a.groupby("classe_prenom").agg(fiches=("cid", "nunique"), avis=("supprime", "size"),
                                         supprimes=("supprime", "sum")).reindex(CLASSES_PRENOM)
    e1["pour_100000"] = 1e5 * e1["supprimes"] / e1["avis"]
    e1["vitesse_mediane"] = fa.groupby("classe_prenom")["avis_par_mois"].median()
    e1["part_avis_moins_90j"] = a.groupby("classe_prenom")["classe_age"].apply(
        lambda s: s.isin(["publié pendant le suivi", "0-30 j", "31-90 j"]).mean())
    print("\n== Étape 1 ==\n" + e1.round(3).to_string())

    # Étape 2 : par quart de vitesse et classe de prénoms.
    t = (a.groupby(["quart_vitesse", "classe_prenom"], observed=True)
         .agg(fiches=("cid", "nunique"), avis=("supprime", "size"), supprimes=("supprime", "sum"))
         .reset_index())
    t["pour_1000"] = 1000 * t["supprimes"] / t["avis"]
    t["classe_prenom"] = pd.Categorical(t["classe_prenom"], CLASSES_PRENOM)
    print("\n== Étape 2 ==\n" + t.round(2).to_string(index=False))

    # Étape 3 : modèles tous âges.
    for code_classe, code in CODES_PRENOM.items():
        a[code] = (a["classe_prenom"] == code_classe).astype(int)
    g = (a.groupby(["cid", "classe_age"])
         .agg(avis=("supprime", "size"), supprimes=("supprime", "sum")).reset_index()
         .merge(fi[["cid", "industry", "bucket", "region", "classe_prenom", "log2_vitesse"]],
                on="cid"))
    for code_classe, code in CODES_PRENOM.items():
        g[code] = (g["classe_prenom"] == code_classe).astype(int)
    lignes = []
    for nom, vit, age in [("M1 secteur, taille, région égaux", False, False),
                          ("M2 + vitesse égale", True, False),
                          ("M3 + âge des avis égal", True, True)]:
        lignes += lire(modele_tous_ages(g, vit, age),
                       list(CODES_PRENOM.values()) + ["log2_vitesse"], nom)

    # Étape 4 : avis neufs.
    l4, info4 = modele_avis_neufs(fi)
    lignes += l4

    # Robustesse (comme Axel) : sans le 1 % de fiches qui ont perdu le plus d'avis.
    par_fiche = a.groupby("cid")["supprime"].sum().sort_values(ascending=False)
    top = par_fiche.head(int(np.ceil(0.01 * len(par_fiche)))).index
    print(f"\nrobustesse : {len(top)} fiches retirées, {int(par_fiche.loc[top].sum())} des "
          f"{int(par_fiche.sum())} suppressions ; classes de prénoms de ces fiches :\n"
          + fi[fi["cid"].isin(top)]["classe_prenom"].value_counts().to_string())
    gr = g[~g["cid"].isin(top)]
    lignes += lire(modele_tous_ages(gr, True, True), list(CODES_PRENOM.values()) + ["log2_vitesse"],
                   "R3 tous âges, sans le 1 % de fiches les plus touchées")
    l4r, info4r = modele_avis_neufs(fi, exclues=top,
                                    nom="R4 avis neufs, sans le 1 % de fiches les plus touchées")
    lignes += l4r
    print(f"robustesse 03C : {info4r}")
    m = pd.DataFrame(lignes)
    m["ecart_pct"] = 100 * (m["rapport_de_cotes"] - 1)
    print(f"\n== Modèles == (03C : {info4})\n" + m.round(3).to_string(index=False))

    (SORTIE / "donnees").mkdir(parents=True, exist_ok=True)
    e1.reset_index().to_csv(SORTIE / "donnees" / "velocite_prenom_fiches.csv", index=False)
    t.to_csv(SORTIE / "donnees" / "velocite_prenom_taux.csv", index=False)
    m.to_csv(SORTIE / "donnees" / "velocite_prenom_modeles.csv", index=False)

    n_avis, n_sup, n_fi = len(a), int(a["supprime"].sum()), a["cid"].nunique()
    graphique_taux(
        t, TITRES["taux"](t),
        f"{espace(n_avis)} avis 4-5 étoiles avec texte de {espace(n_fi)} fiches (au moins 20 avis "
        f"annotés), tous âges, sans les six enseignes ; {espace(n_sup)} supprimés du 11 au 24 "
        f"août 2026.\nVitesse : avis reçus par mois, toutes notes, du 7 août 2025 au 6 août 2026 ; "
        f"les fiches sont coupées en quatre groupes de même taille.\nPart de prénoms : part des "
        f"avis 4-5 étoiles de la fiche, publiés avant le 7 août, qui citent un prénom "
        f"(annotation d'Axel).",
        SORTIE / "graphiques" / "velocite_prenom_taux.png")
    graphique_modeles(
        m, TITRES["modeles"](m),
        f"Régressions logistiques à secteur, taille et région égaux, erreurs groupées par fiche. "
        f"1 à 4 : les {espace(n_avis)} avis du graphique précédent.\n4 : sans les {len(top)} "
        f"fiches (1 %) qui portent {100 * par_fiche.loc[top].sum() / par_fiche.sum():.0f} % des "
        f"suppressions. 5 : {espace(info4['avis'])} avis 4-5 étoiles de 03C publiés du 7 au 17 "
        f"août 2026, sans les enseignes\n({info4['suppressions']} supprimés), tous du même âge, "
        f"avec en plus le prénom de l'avis, la photo, le jour de pic et la réponse. Trait : "
        f"fourchette à 95 %.\nBarre grise : écart trop incertain pour être affirmé.",
        SORTIE / "graphiques" / "velocite_prenom_modeles.png")
    print("écrit :", SORTIE / "graphiques" / "velocite_prenom_taux.png")
    print("écrit :", SORTIE / "graphiques" / "velocite_prenom_modeles.png")


def _ecart(m, modele, variable):
    r = m[(m["modele"] == modele) & (m["variable"] == variable)].iloc[0]
    return r["rapport_de_cotes"], r["p_value"]


def _titre_taux(t):
    # Dans chaque quart de vitesse, les fiches à 50 % et plus perdent-elles plus que
    # celles à moins de 10 % ?
    p = t.pivot(index="quart_vitesse", columns="classe_prenom", values="pour_1000")
    if (p["50 % et plus"] > p["moins de 10 %"]).all():
        return "À vitesse égale, les fiches qui citent beaucoup de prénoms perdent toujours plus d'avis"
    return "Taux de suppression selon la vitesse de collecte et la part de prénoms"


def _titre_modeles(m):
    rc_p, p_p = _ecart(m, "R3 tous âges, sans le 1 % de fiches les plus touchées", "p_50_100")
    rc_v, _ = _ecart(m, "R3 tous âges, sans le 1 % de fiches les plus touchées", "log2_vitesse")
    if p_p < 0.05 and rc_p > 1 and rc_v <= 1:
        return "La vitesse de collecte n'explique pas l'écart des fiches qui citent beaucoup de prénoms"
    return "Part de prénoms et vitesse de collecte : effet sur le risque de suppression"


TITRES = {"taux": _titre_taux, "modeles": _titre_modeles}


if __name__ == "__main__":
    main()
