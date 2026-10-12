#!/usr/bin/env python3
"""
==============================================================================
Script : 07H_reponse_vite_souvent.py
Entrée : data/local/03C_7_17_aout_prenom.parquet, lu par le 07F puis le 07G
         (même population, même découpage en avis-jours)
         reviews_doublons_cleaned_all, pour le taux de réponse de chaque fiche

Écrit le 2026-10-06 à la demande de Matthieu, après la réunion avec Romain, pour
la piste n° 2 des faits saignants (« Vous avez 2 jours pour répondre – et il
faut répondre souvent »). Le 07F et le 07G ne sont pas modifiés.

    PYTHONPATH=".venv/Lib/site-packages;outils" <python uv> logistic-regression-study/python/07H_reponse_vite_souvent.py

------------------------------------------------------------------------------
LES AVIS
------------------------------------------------------------------------------
Avis 4-5 étoiles de 03C, publiés du 7 au 17 août 2026, tels que les garde le
07F (24 191 avis), SANS les six enseignes (4 chaînes antiparasitaires, 2 salles
espagnoles) : 22 378 avis. Analyse principale sans les enseignes ; avec, en
contrôle. Un avis disparu est supprimé (deleted_detected_at, sans règle des
2 jours). Suivi complet jusqu'au 24 août, comme le 07G.

Dates au jour près : reply_date et created_at sont tous à minuit, et les relevés
quotidiens ne notent pas l'apparition d'une réponse. « Le jour même » = même
date calendaire que la publication.

------------------------------------------------------------------------------
LE MODÈLE : UNE LIGNE PAR AVIS ET PAR JOUR (07G)
------------------------------------------------------------------------------
Chaque avis compte une ligne par jour où il était en ligne et observé. La
réponse ne compte qu'à partir du lendemain de son arrivée : un avis répondu au
6e jour n'est pas « répondu » pendant les jours où il aurait pu être supprimé
sans réponse. Sans cela, les réponses tardives paraissent protéger parfaitement
(1 suppression sur 743 avis répondus au 6e jour ou après), ce qui est mécanique.

Régression logistique sur les avis-jours, erreurs groupées par fiche. Contrôles
toujours présents, jamais affichés : secteur, taille, région, jour d'âge de
l'avis (un indicateur par jour, 12 et plus regroupés), et les trois autres
caractéristiques du 07G (prénom, photo, pic). Le jour d'âge est dans le modèle
principal, contrairement au 07G : une réponse tardive n'est active qu'aux âges
du pic de suppressions (6e-7e jour) ; sans lui, on comparerait des âges
différents.

------------------------------------------------------------------------------
1. RÉPONDRE VITE : Y A-T-IL UN SEUIL ?
------------------------------------------------------------------------------
L'état de réponse de l'avis, jour par jour :
  pas encore de réponse (référence)
  répondu le jour même / le lendemain / au 2e jour / au 3e jour ou après
Tests : les quatre effets sont-ils égaux ? « au 2e jour » = « 3e jour ou après » ?

------------------------------------------------------------------------------
2. RÉPONDRE SOUVENT : LE TAUX DE RÉPONSE DE LA FICHE
------------------------------------------------------------------------------
Part des avis 4-5 étoiles de la fiche, publiés du 7 août 2025 au 6 août 2026
(l'année avant le corpus, avis étudiés exclus), qui ont une réponse. Classes :
0 % (référence), 1-25 %, 25-75 %, 75 % et plus ; les fiches de moins de 10 avis
dans l'année forment une classe à part, affichée dans les CSV seulement.
  B1  taux seul                       les fiches qui répondent souvent
                                      perdent-elles moins d'avis ?
  B2  taux + réponse à l'avis         l'habitude compte-t-elle au-delà de la
      (reçue la veille ou avant)      réponse à cet avis ?
  B3  réponse à l'avis, par classe    l'effet de la réponse change-t-il avec le
                                      taux (ancien corpus : protège au-delà de
                                      75 %, s'inverse entre 25 et 75 %) ?

------------------------------------------------------------------------------
3. JALONS AU 1er, 2e ET 3e JOUR (illustration)
------------------------------------------------------------------------------
Même montage que etudes-ponctuelles/2026-10-06-reponse-jalon-03C : avis vus et
en ligne à la fin du jour k, répondus ou non au plus tard au jour k, suppression
comptée du jour k+1 au 7e jour. Un avis par ligne. Rapport de cotes à secteur et
taille égaux (07F).

------------------------------------------------------------------------------
SORTIES
------------------------------------------------------------------------------
output-study/<date>-sorties-07H-reponse/
  07H_vite.csv, 07H_souvent.csv, 07H_jalons.csv, 07H_tests.csv,
  07H_summary_<modèle>.txt
livrables/restitution_finale/graphiques/faits-saignants/
  graphiques/reponse_delai.png, reponse_taux_fiche.png, reponse_jalons.png
  donnees/reponse_delai.csv, reponse_taux_fiche.csv, reponse_jalons.csv
  graphiques/regression_03C_reponse_delai_taux.png (+ _avec_enseignes) : figure habituelle
    du 07G, un seul modèle avec prénom, photo, pic, délai de réponse et taux de la fiche
    (voir complet()) ; donnees/regression_03C_reponse_delai_taux.csv
==============================================================================
"""
from __future__ import annotations

import importlib.util
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("g07", ICI / "07G_regression_03C_jour_par_jour.py")
g07 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(g07)
f07, sm = g07.f07, g07.sm
from local import connexion  # noqa: E402  (chemin posé par le 07F)

SORTIES = ICI.parent / "output-study" / f"{date.today():%Y-%m-%d}-sorties-07H-reponse"
FAITS = f07.FINALE / "graphiques" / "faits-saignants"

TAUX_DEBUT, TAUX_FIN = "2025-08-07", "2026-08-06"
TAUX_MIN_AVIS = 10
DELAIS = ["rep_j0", "rep_j1", "rep_j2", "rep_j3plus"]
NOMS_DELAIS = {"rep_j0": "répondu\nle jour même", "rep_j1": "répondu\nle lendemain",
               "rep_j2": "répondu\nau 2e jour", "rep_j3plus": "répondu au 3e\njour ou après"}
CLASSES = ["t_1_25", "t_25_75", "t_75_100", "t_moins_10_avis"]
NOMS_CLASSES = {"t_0": "0 %", "t_1_25": "1 à 25 %", "t_25_75": "25 à 75 %",
                "t_75_100": "75 % et plus", "t_moins_10_avis": "moins de 10 avis"}
JALONS = [1, 2, 3]
CONTROLES_CARAC = ["prenom", "photo", "pic"]

BLEU, GRIS = f07.BLEU, "#c3c2b7"
ENCRE, ENCRE_2, GRILLE, FOND = f07.ENCRE, f07.ENCRE_2, f07.GRILLE, f07.FOND


def espace(n: float) -> str:
    return f"{n:,.0f}".replace(",", " ")


def virgule(x: float, d: int = 0) -> str:
    return f"{x:.{d}f}".replace(".", ",").replace("-", "−")


# ---------------------------------------------------------------------------
# Données
# ---------------------------------------------------------------------------

def taux_fiches() -> pd.DataFrame:
    con = connexion("4GB")
    return con.execute(f"""
        SELECT cid, count(*) AS avis_annee,
               avg((reply_date IS NOT NULL)::INT) AS taux_reponse
        FROM reviews_doublons_cleaned_all
        WHERE star >= 4
          AND CAST(created_at AS DATE) BETWEEN DATE '{TAUX_DEBUT}' AND DATE '{TAUX_FIN}'
        GROUP BY cid""").df()


def classe_taux(t: pd.DataFrame) -> pd.Series:
    n, x = t["avis_annee"].fillna(0), t["taux_reponse"]
    return pd.Series(np.select(
        [n < TAUX_MIN_AVIS, x == 0, x < 0.25, x < 0.75],
        ["t_moins_10_avis", "t_0", "t_1_25", "t_25_75"], "t_75_100"), index=t.index)


def avis() -> pd.DataFrame:
    """g07.avis(), sans sa jointure sur `businesses` : le 07F donne désormais le
    secteur et la taille, et la jointure les doublait (constaté le 2026-10-06)."""
    df = f07.charger()
    if df[["industry", "bucket"]].isna().any().any():
        raise SystemExit("Des avis n'ont pas de secteur ou de taille.")
    df["j_fin"] = (pd.Timestamp(g07.DERNIERE_VAGUE) - pd.to_datetime(df["created_at"])).dt.days
    df["supprime_tout"] = df["j_suppression"].notna().astype(int)
    return df


def preparer() -> tuple[pd.DataFrame, pd.DataFrame]:
    df = avis()
    t = taux_fiches()
    df = df.merge(t, on="cid", how="left")
    df["classe_taux"] = classe_taux(df)
    p = g07.avis_jours(df)
    p = p.merge(df[["review_id", "classe_taux", "taux_reponse"]], on="review_id", how="left")
    repondu = (p["j_reponse"] <= p["jour"] - 1).fillna(False)
    p["repondu"] = repondu.astype(int)
    for v, cond in [("rep_j0", p["j_reponse"] == 0), ("rep_j1", p["j_reponse"] == 1),
                    ("rep_j2", p["j_reponse"] == 2), ("rep_j3plus", p["j_reponse"] >= 3)]:
        p[v] = (repondu & cond).astype(int)
    for c in CLASSES:
        p[c] = (p["classe_taux"] == c).astype(int)
    return df, p


# ---------------------------------------------------------------------------
# Ajustement
# ---------------------------------------------------------------------------

def ajuster(d: pd.DataFrame, variables: list[str], age: bool = True):
    morceaux = [d[variables + CONTROLES_CARAC].astype(float),
                g07.indicateurs(d, "industry", g07.REF_SECTEUR, "secteur"),
                g07.indicateurs(d, "bucket", g07.REF_TAILLE, "taille"),
                (d["region"] == "US").astype(float).rename("region_US").to_frame()]
    if age:
        morceaux.append(g07.indicateurs(d.assign(j=d["jour"].clip(upper=g07.JOUR_MAX)),
                                        "j", "1", "jour"))
    X = pd.concat(morceaux, axis=1)
    X = sm.add_constant(X.loc[:, X.std() > 0], has_constant="add")
    return sm.GLM(d["y"].astype(float), X, family=sm.families.Binomial()).fit(
        cov_type="cluster", cov_kwds={"groups": d["cid"].factorize()[0]})


def lignes(res, variables: list[str], modele: str, d: pd.DataFrame) -> pd.DataFrame:
    ic = res.conf_int()
    t = pd.DataFrame({
        "modele": modele, "variable": variables,
        "rapport_de_cotes": np.exp(res.params[variables]).values,
        "borne_basse": np.exp(ic.loc[variables, 0]).values,
        "borne_haute": np.exp(ic.loc[variables, 1]).values,
        "p_value": res.pvalues[variables].values})
    t["avis"] = [int(d.loc[d[v] == 1, "review_id"].nunique()) for v in variables]
    t["avis_jours"] = [int((d[v] == 1).sum()) for v in variables]
    t["suppressions"] = [int(d.loc[d[v] == 1, "y"].sum()) for v in variables]
    for c in ["rapport_de_cotes", "borne_basse", "borne_haute"]:
        t[c.replace("rapport_de_cotes", "ecart") + "_pct"] = 100 * (t[c] - 1)
    return t


def test(res, contrainte: str, nom: str, modele: str) -> dict:
    w = res.wald_test(contrainte, scalar=True)
    return {"modele": modele, "test": nom, "contrainte": contrainte,
            "statistique": float(w.statistic), "p_value": float(w.pvalue)}


def ecrire_summary(res, nom: str, d: pd.DataFrame) -> None:
    (SORTIES / f"07H_summary_{nom}.txt").write_text(
        f"Modèle : {nom}\n{len(d)} avis-jours, {d['review_id'].nunique()} avis, "
        f"{int(d['y'].sum())} suppressions, {d['cid'].nunique()} fiches\n"
        "secteur_*, taille_*, region_US, jour_*, prenom, photo, pic : contrôles.\n\n"
        f"{res.summary()}", encoding="utf-8")


def vite(p: pd.DataFrame) -> tuple[pd.DataFrame, list[dict]]:
    sorties, tests = [], []
    passages = [("sans enseignes", p[~p["enseigne"]], True),
                ("sans enseignes, sans jour d'âge", p[~p["enseigne"]], False),
                ("avec enseignes", p, True),
                ("sans enseignes, US", p[~p["enseigne"] & (p["region"] == "US")], True),
                ("sans enseignes, Europe", p[~p["enseigne"] & (p["region"] == "Europe")], True)]
    for nom, d, age in passages:
        res = ajuster(d, DELAIS, age=age)
        sorties.append(lignes(res, DELAIS, nom, d))
        tests.append(test(res, "rep_j0 = rep_j1, rep_j1 = rep_j2, rep_j2 = rep_j3plus",
                          "les quatre délais ont le même effet", nom))
        tests.append(test(res, "rep_j2 = rep_j3plus", "2e jour = 3e jour ou après", nom))
        if nom == "sans enseignes":
            ecrire_summary(res, "vite", d)
    return pd.concat(sorties), tests


def souvent(p: pd.DataFrame) -> tuple[pd.DataFrame, list[dict]]:
    sorties, tests = [], []
    d = p[~p["enseigne"]].copy()
    for nom, variables in [("B1 taux seul", CLASSES),
                           ("B2 taux + réponse à l'avis", CLASSES + ["repondu"])]:
        res = ajuster(d, variables)
        sorties.append(lignes(res, variables, nom, d))
        tests.append(test(res, "t_1_25 = 0, t_25_75 = 0, t_75_100 = 0",
                          "le taux n'a aucun effet (hors moins de 10 avis)", nom))
        ecrire_summary(res, nom.split()[0], d)
    # B3 : l'effet de la réponse à l'avis, classe par classe.
    inter = []
    for c in ["t_0", "t_1_25", "t_25_75", "t_75_100", "t_moins_10_avis"]:
        v = f"repondu_x_{c}"
        d[v] = d["repondu"] * (d["classe_taux"] == c).astype(int)
        if d.loc[d[v] == 1, "y"].sum() > 0:
            inter.append(v)
    res = ajuster(d, CLASSES + inter)
    sorties.append(lignes(res, CLASSES + inter, "B3 réponse par classe", d))
    ecrire_summary(res, "B3", d)
    # Avec les enseignes, en contrôle.
    res = ajuster(p, CLASSES + ["repondu"])
    sorties.append(lignes(res, CLASSES + ["repondu"], "B2 avec enseignes", p))
    return pd.concat(sorties), tests


def jalons(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    s0 = df[~df["enseigne"]]
    for k in JALONS:
        d = s0[(s0["j_premiere_vue"] <= k) & ~(s0["j_suppression"] <= k).fillna(False)].copy()
        d[f"reponse_j{k}"] = (d["j_reponse"] <= k).fillna(False).astype(int)
        d["y_jalon"] = d["j_suppression"].between(k + 1, f07.HORIZON_J).fillna(False).astype(int)
        v = CONTROLES_CARAC + [f"reponse_j{k}"]
        t = f07.tableau(f07.ajuster(d, v, "y_jalon", secteur_taille=True), "sans enseignes", v)
        r = t[t.variable == f"reponse_j{k}"].iloc[0]
        for rep in (0, 1):
            g = d[d[f"reponse_j{k}"] == rep]
            rows.append({"jalon_j": k, "repondu_au_jalon": "oui" if rep else "non",
                         "avis": len(g), "supprimes": int(g["y_jalon"].sum()),
                         "pour_1000": 1000 * g["y_jalon"].mean(),
                         "rapport_de_cotes_secteur_taille": r.rapport_de_cotes,
                         "borne_basse": r.borne_basse, "borne_haute": r.borne_haute,
                         "p_value": r.p_value})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Modèle complet, figure habituelle (demande de Matthieu du 2026-10-06)
# ---------------------------------------------------------------------------
# Les paramètres habituels du 07G (prénom, photo, pic ; secteur, taille et, pour « les
# deux », région en contrôle ; pas de jour d'âge, décision du 2026-10-05), avec la
# réponse détaillée par délai à la place de « pas de réponse », et le taux de réponse de
# la fiche en plus, dans UNE seule régression par passage.

AFFICHEES = CONTROLES_CARAC + DELAIS + ["t_1_25", "t_25_75", "t_75_100"]
NOMS_COMPLET = {
    "prenom": "Prénom cité dans l'avis", "photo": "Photo jointe",
    "pic": "Publié un jour de pic\nsur la fiche",
    "rep_j0": "Réponse le jour même", "rep_j1": "Réponse le lendemain",
    "rep_j2": "Réponse au 2e jour", "rep_j3plus": "Réponse au 3e jour\nou après",
    "t_1_25": "Fiche qui répond\nà 1-25 % des avis", "t_25_75": "Fiche qui répond\nà 25-75 % des avis",
    "t_75_100": "Fiche qui répond\nà 75 % et plus"}
PASSAGES = [("US", "États-Unis"), ("Europe", "Europe"), ("tous", "Les deux")]


def complet(p: pd.DataFrame) -> tuple[pd.DataFrame, list[dict]]:
    sorties, tests = [], []
    for population, base in [("sans enseignes", p[~p["enseigne"]]), ("avec enseignes", p)]:
        for passage, _ in PASSAGES:
            d = base if passage == "tous" else base[base["region"] == passage]
            for age in (False, True):
                nom = f"complet, {population}, {passage}" + (", + jour d'âge" if age else "")
                res = ajuster(d, DELAIS + CLASSES, age=age)
                t = lignes(res, AFFICHEES, nom, d)
                t["population"], t["passage"], t["jour_age"] = population, passage, age
                sorties.append(t)
                tests.append(test(res, "rep_j0 = rep_j1, rep_j1 = rep_j2, rep_j2 = rep_j3plus",
                                  "les quatre délais ont le même effet", nom))
                tests.append(test(res, "t_1_25 = 0, t_25_75 = 0, t_75_100 = 0",
                                  "le taux n'a aucun effet (hors moins de 10 avis)", nom))
                if not age:
                    ecrire_summary(res, f"complet_{population.replace(' ', '_')}_{passage}", d)
    return pd.concat(sorties), tests


def figure_habituelle(t: pd.DataFrame, population: str, chemin: Path) -> None:
    """Même construction que la figure du 07G : un panneau par passage, rapport de cotes
    et fourchette à 95 %, échelle logarithmique, point plein si p < 0,05."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.ticker import FixedLocator, NullLocator

    XMIN, XMAX = 0.06, 8
    groupes = [CONTROLES_CARAC, DELAIS, ["t_1_25", "t_25_75", "t_75_100"]]
    y, pos = {}, 0.0
    for g in groupes:
        for v in g:
            y[v] = -pos
            pos += 1
        pos += 0.6
    fig, axes = plt.subplots(1, 3, figsize=(11, 6.6), dpi=150, sharey=True)
    fig.patch.set_facecolor(FOND)
    for ax, (passage, titre) in zip(axes, PASSAGES):
        s = t[(t["population"] == population) & (t["passage"] == passage) & ~t["jour_age"]]
        s = s.set_index("variable")
        ax.set_facecolor(FOND)
        ax.axvline(1, color=ENCRE_2, lw=1, zorder=1)
        for limite in (y["pic"] - 0.8, y["rep_j3plus"] - 0.8):
            ax.axhline(limite, color=GRILLE, lw=0.8, zorder=0)
        for v in AFFICHEES:
            r = s.loc[v]
            net = r["p_value"] < 0.05
            bas, haut = max(r["borne_basse"], XMIN * 1.05), min(r["borne_haute"], XMAX / 1.05)
            ax.plot([bas, haut], [y[v]] * 2, color=BLEU, lw=2, solid_capstyle="round", zorder=2)
            for borne, lim, m in [(r["borne_basse"], bas, "<"), (r["borne_haute"], haut, ">")]:
                if borne != lim:
                    ax.plot(lim, y[v], marker=m, ms=5, color=BLEU, zorder=2)
            ax.plot(r["rapport_de_cotes"], y[v], "o", ms=8, mew=2, zorder=3, mec=BLEU,
                    mfc=BLEU if net else FOND)
            ax.annotate(virgule(r["rapport_de_cotes"], 2), (r["rapport_de_cotes"], y[v]),
                        xytext=(0, 8), textcoords="offset points", ha="center", fontsize=8,
                        color=ENCRE, fontweight="bold" if net else "normal")
        ax.set_xscale("log")
        ax.set_xlim(XMIN, XMAX)
        graduations = [0.125, 0.25, 0.5, 1, 2, 4]
        ax.xaxis.set_major_locator(FixedLocator(graduations))
        ax.xaxis.set_minor_locator(NullLocator())
        ax.set_xticklabels([f"{g:g}".replace(".", ",") for g in graduations])
        ax.grid(axis="x", color=GRILLE, lw=0.8, zorder=0)
        ax.tick_params(colors=ENCRE_2, labelsize=8, length=0)
        for cote in ["top", "right", "left"]:
            ax.spines[cote].set_visible(False)
        ax.spines["bottom"].set_color(GRILLE)
        ax.set_ylim(min(y.values()) - 0.6, 0.6)
        ax.set_title(titre, fontsize=10, color=ENCRE, loc="left")
    axes[0].set_yticks(list(y.values()))
    axes[0].set_yticklabels([NOMS_COMPLET[v] for v in y], fontsize=9, color=ENCRE)
    axes[1].set_xlabel("risque de suppression (1 = pas d'effet)", color=ENCRE_2, fontsize=8)
    enseignes = "sans les six enseignes" if population == "sans enseignes" else "six enseignes comprises"
    fig.text(0.01, 0.975, "Risque de suppression d'un avis 4-5 étoiles, à secteur et taille égaux "
             f"(suivi complet, {enseignes})", va="top", fontsize=12, color=ENCRE)
    fig.text(0.01, 0.025, "Références : pour la réponse, un avis pas encore répondu (la réponse "
             "compte à partir du lendemain de son arrivée) ; pour le taux de réponse de la fiche, "
             "une fiche qui ne répond jamais.\nTaux de la fiche : part de ses avis 4-5 étoiles "
             "publiés du 7 août 2025 au 6 août 2026 qui ont une réponse. Avis 4-5 étoiles de 03C "
             "publiés du 7 au 17 août 2026, suivis jusqu'au 24 août.",
             va="bottom", fontsize=7.5, color=ENCRE_2, linespacing=1.5)
    legende = [Line2D([0], [0], marker="o", color=BLEU, mfc=BLEU, ms=7, lw=2,
                      label="significatif (p < 0,05)"),
               Line2D([0], [0], marker="o", color=BLEU, mfc=FOND, ms=7, mew=2, lw=2,
                      label="non significatif")]
    fig.legend(handles=legende, loc="upper left", bbox_to_anchor=(0.005, 0.945),
               frameon=False, fontsize=8, labelcolor=ENCRE, ncol=2, handlelength=2)
    fig.subplots_adjust(left=0.17, right=0.985, top=0.855, bottom=0.16, wspace=0.08)
    fig.savefig(chemin, facecolor=FOND)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Graphiques
# ---------------------------------------------------------------------------

def _style(ax):
    ax.set_facecolor(FOND)
    ax.tick_params(colors=ENCRE_2, labelsize=8, length=0)
    ax.grid(axis="y", color=GRILLE, lw=0.8, zorder=0)
    for cote in ["top", "right", "left"]:
        ax.spines[cote].set_visible(False)
    ax.spines["bottom"].set_color(GRILLE)


def barres_ecart(t: pd.DataFrame, noms: dict, titre: str, sous_titre: str, chemin: Path,
                 sous_barre, x=None) -> None:
    """Écart du risque en %, fourchette à 95 %, une barre par catégorie (format du
    graphique « par secteur » que Matthieu a collé dans le Word)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(8.5, 4.6), dpi=150)
    fig.patch.set_facecolor(FOND)
    _style(ax)
    x = np.arange(len(t)) if x is None else np.asarray(x)
    for xi, (_, r) in zip(x, t.iterrows()):
        net = r["p_value"] < 0.05
        ax.bar(xi, r["ecart_pct"], width=0.55, color=BLEU if net else GRIS, zorder=2)
        ax.plot([xi, xi], [r["borne_basse_pct"], r["borne_haute_pct"]], color=ENCRE, lw=1.2,
                zorder=3)
        for b in (r["borne_basse_pct"], r["borne_haute_pct"]):
            ax.plot([xi - 0.06, xi + 0.06], [b, b], color=ENCRE, lw=1.2, zorder=3)
        # Étiquettes au-delà de la fourchette, du côté de la barre.
        valeur = f"{'+' if r['ecart_pct'] > 0 else ''}{virgule(r['ecart_pct'])} %"
        poids = "bold" if net else "normal"
        if r["ecart_pct"] < 0:
            ax.annotate(valeur, (xi, r["borne_basse_pct"]), xytext=(0, -4),
                        textcoords="offset points", ha="center", va="top", fontsize=9,
                        color=ENCRE, fontweight=poids, zorder=4)
            ax.annotate(sous_barre(r), (xi, r["borne_basse_pct"]), xytext=(0, -17),
                        textcoords="offset points", ha="center", va="top", fontsize=7,
                        color=ENCRE_2, zorder=4)
        else:
            ax.annotate(sous_barre(r), (xi, r["borne_haute_pct"]), xytext=(0, 4),
                        textcoords="offset points", ha="center", va="bottom", fontsize=7,
                        color=ENCRE_2, zorder=4)
            ax.annotate(valeur, (xi, r["borne_haute_pct"]), xytext=(0, 26),
                        textcoords="offset points", ha="center", va="bottom", fontsize=9,
                        color=ENCRE, fontweight=poids, zorder=4)
    ax.axhline(0, color=ENCRE_2, lw=0.9, ls=(0, (4, 3)), zorder=1)
    ax.annotate("pas d'effet", (x.max() + 0.45, 0), xytext=(0, 3), textcoords="offset points",
                ha="right", va="bottom", fontsize=7.5, color=ENCRE_2)
    ax.set_xticks(x)
    ax.set_xticklabels([noms[v] for v in t["variable"]], fontsize=8, color=ENCRE)
    ax.yaxis.set_major_formatter(lambda v, _: f"{'+' if v > 0 else ''}{v:.0f} %".replace("-", "−"))
    hi, lo = max(0, t["borne_haute_pct"].max()), min(0, t["borne_basse_pct"].min())
    marge = 0.3 * (hi - lo)
    ax.set_ylim(lo - (marge if lo < 0 else 5), hi + (marge if hi > 0 else 10))
    ax.set_xlim(x.min() - 0.5, x.max() + 0.5)
    ax.set_ylabel("écart du risque de suppression", color=ENCRE_2, fontsize=8)
    fig.text(0.01, 0.975, titre, va="top", fontsize=11, color=ENCRE)
    fig.text(0.01, 0.905, sous_titre, va="top", fontsize=7.5, color=ENCRE_2, linespacing=1.5)
    fig.tight_layout(rect=(0, 0, 1, 0.76))
    fig.savefig(chemin, facecolor=FOND)
    plt.close(fig)


def graphique_jalons(j: pd.DataFrame, titre: str, sous_titre: str, chemin: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch

    fig, ax = plt.subplots(figsize=(8.5, 4.4), dpi=150)
    fig.patch.set_facecolor(FOND)
    _style(ax)
    for i, k in enumerate(JALONS):
        for dx, rep, couleur in [(-0.19, "non", GRIS), (0.19, "oui", BLEU)]:
            r = j[(j["jalon_j"] == k) & (j["repondu_au_jalon"] == rep)].iloc[0]
            ax.bar(i + dx, r["pour_1000"], width=0.36, color=couleur, zorder=2)
            ax.annotate(virgule(r["pour_1000"], 1), (i + dx, r["pour_1000"]), xytext=(0, 3),
                        textcoords="offset points", ha="center", fontsize=9,
                        fontweight="bold", color=ENCRE)
        r = j[j["jalon_j"] == k].iloc[0]
        ax.annotate(f"à secteur et taille égaux : ×{virgule(r['rapport_de_cotes_secteur_taille'], 2)}"
                    f" [{virgule(r['borne_basse'], 2)} ; {virgule(r['borne_haute'], 2)}]",
                    (i, 0), xytext=(0, -30), textcoords="offset points", ha="center",
                    fontsize=7, color=ENCRE_2, annotation_clip=False)
    ax.set_xticks(range(len(JALONS)))
    ax.set_xticklabels([f"réponse au plus tard au {'1er' if k == 1 else f'{k}e'} jour\n"
                        f"suppressions du {k + 1}e au 7e jour" for k in JALONS],
                       fontsize=8, color=ENCRE)
    ax.set_ylabel("avis supprimés pour 1 000", color=ENCRE_2, fontsize=8)
    ax.set_ylim(0, j["pour_1000"].max() * 1.25)
    fig.text(0.01, 0.975, titre, va="top", fontsize=11, color=ENCRE)
    fig.text(0.01, 0.905, sous_titre, va="top", fontsize=7.5, color=ENCRE_2, linespacing=1.5)
    fig.legend(handles=[Patch(color=GRIS, label="pas encore de réponse au jalon"),
                        Patch(color=BLEU, label="déjà répondu au jalon")],
               loc="upper left", bbox_to_anchor=(0.005, 0.80), ncol=2, frameon=False,
               fontsize=8, labelcolor=ENCRE)
    fig.tight_layout(rect=(0, 0.04, 1, 0.73))
    fig.savefig(chemin, facecolor=FOND)
    plt.close(fig)


# ---------------------------------------------------------------------------

def main() -> None:
    SORTIES.mkdir(parents=True, exist_ok=True)
    for sous in ("graphiques", "donnees"):
        (FAITS / sous).mkdir(parents=True, exist_ok=True)
    df, p = preparer()
    s = df[~df["enseigne"]]
    print(f"  sans enseignes : {len(s)} avis, {s['cid'].nunique()} fiches, "
          f"{int(s['supprime_tout'].sum())} suppressions sur tout le suivi")
    print("  classes de taux (sans enseignes) :\n"
          + s.groupby("classe_taux").agg(fiches=("cid", "nunique"), avis=("review_id", "size"),
                                         suppressions=("supprime_tout", "sum")).to_string())

    v, tests_v = vite(p)
    so, tests_s = souvent(p)
    co, tests_c = complet(p)
    jl = jalons(df)
    tests = pd.DataFrame(tests_v + tests_s + tests_c)
    for nom, table in [("vite", v), ("souvent", so), ("complet", co), ("jalons", jl),
                       ("tests", tests)]:
        table.to_csv(SORTIES / f"07H_{nom}.csv", index=False)
    co.to_csv(FAITS / "donnees" / "regression_03C_reponse_delai_taux.csv", index=False)
    figure_habituelle(co, "sans enseignes",
                      FAITS / "graphiques" / "regression_03C_reponse_delai_taux.png")
    figure_habituelle(co, "avec enseignes",
                      FAITS / "graphiques" / "regression_03C_reponse_delai_taux_avec_enseignes.png")

    pd.set_option("display.width", 220)
    fmt = {c: "{:.2f}".format for c in ["rapport_de_cotes", "borne_basse", "borne_haute",
                                        "rapport_de_cotes_secteur_taille"]}
    fmt.update({"p_value": "{:.3f}".format, "pour_1000": "{:.1f}".format,
                "ecart_pct": "{:.0f}".format, "borne_basse_pct": "{:.0f}".format,
                "borne_haute_pct": "{:.0f}".format, "statistique": "{:.2f}".format})
    for nom, table in [("VITE", v), ("SOUVENT", so), ("COMPLET", co), ("JALONS", jl),
                       ("TESTS", tests)]:
        print(f"\n== {nom} ==\n" + table.to_string(index=False, formatters=fmt))

    # Graphique 1 : délai de réponse.
    t = v[v["modele"] == "sans enseignes"].copy()
    t.to_csv(FAITS / "donnees" / "reponse_delai.csv", index=False)
    tg = tests[(tests["modele"] == "sans enseignes")].set_index("test")["p_value"]
    n_avis, n_sup = len(s), int(s["supprime_tout"].sum())
    barres_ecart(
        t, NOMS_DELAIS, TITRES["delai"](t, tg),
        f"Nouveaux avis 4-5 étoiles publiés du 7 au 17 août 2026, sans les six enseignes : "
        f"{espace(n_avis)} avis, {espace(n_sup)} supprimés, suivis jusqu'au 24 août.\n"
        "Chaque avis est comparé, jour par jour, aux avis du même âge pas encore répondus, "
        "à secteur, taille et région égaux.\nLa réponse compte à partir du lendemain de son "
        "arrivée. Trait : fourchette à 95 %. Barre grise : écart trop incertain pour être "
        "affirmé.",
        FAITS / "graphiques" / "reponse_delai.png",
        lambda r: f"{espace(r['avis'])} avis\n{r['suppressions']} supprimés après la réponse")

    # Graphique 2 : taux de réponse de la fiche, à réponse à l'avis égale (B2), et
    # l'effet de la réponse à l'avis elle-même, à part, à droite.
    t = so[(so["modele"] == "B2 taux + réponse à l'avis")
           & (so["variable"] != "t_moins_10_avis")].copy()
    so[so["modele"].str.startswith("B")].to_csv(FAITS / "donnees" / "reponse_taux_fiche.csv",
                                                index=False)
    ref = s[s["classe_taux"] == "t_0"]
    tb = tests[(tests["modele"] == "B2 taux + réponse à l'avis")]["p_value"].iloc[0]
    noms = {"t_1_25": "fiche qui répond\nà 1-25 % des avis", "t_25_75": "fiche qui répond\nà 25-75 % des avis",
            "t_75_100": "fiche qui répond\nà 75 % et plus", "repondu": "avis\nrépondu"}
    barres_ecart(
        t, noms, TITRES["taux"](t, tb),
        f"Mêmes avis. Taux de réponse de la fiche : part de ses avis 4-5 étoiles publiés du "
        f"7 août 2025 au 6 août 2026 qui ont une réponse.\nÀ gauche : face aux fiches qui "
        f"ne répondent jamais ({espace(ref['cid'].nunique())} fiches, {espace(len(ref))} avis, "
        f"{int(ref['supprime_tout'].sum())} supprimés), à réponse à l'avis égale. À droite : "
        f"avis répondu face à un avis\npas encore répondu, à taux de la fiche égal. À "
        f"secteur, taille, région et âge égaux. Trait : fourchette à 95 %. Barre grise : "
        f"écart trop incertain.",
        FAITS / "graphiques" / "reponse_taux_fiche.png",
        lambda r: f"{espace(r['avis'])} avis\n{r['suppressions']} supprimés", x=[0, 1, 2, 3.5])

    # Graphique 3 : jalons.
    jl.to_csv(FAITS / "donnees" / "reponse_jalons.csv", index=False)
    graphique_jalons(
        jl, TITRES["jalons"](jl),
        "Nouveaux avis 4-5 étoiles publiés du 7 au 17 août 2026, sans les six enseignes, vus "
        "par le robot et encore en ligne au jalon.\nOn compare les avis déjà répondus au "
        "jalon aux autres, sur les suppressions qui suivent, jusqu'au 7e jour.",
        FAITS / "graphiques" / "reponse_jalons.png")
    print(f"\nSorties : {SORTIES}\nRestitution : {FAITS}")


# Titres affirmatifs, écrits à partir des résultats (voir le compte rendu du
# 2026-10-06 dans 6. faits-saignants.docx).
TITRES = {
    "delai": lambda t, tg: (
        "Une réponse protège l'avis, qu'elle arrive le jour même ou plus tard"
        if tg["les quatre délais ont le même effet"] >= 0.05
        else "Plus la réponse arrive tôt, plus elle protège l'avis"),
    "taux": lambda t, p: (
        "Ce qui protège, c'est la réponse à l'avis, pas l'habitude de répondre de la fiche"
        if p >= 0.05 else "L'habitude de répondre de la fiche protège, en plus de la réponse"),
    "jalons": lambda j: (
        "Au 1er, au 2e ou au 3e jour, l'avis déjà répondu est moins supprimé"
        if (j["p_value"] < 0.05).all()
        else "L'avis déjà répondu n'est pas moins supprimé à tous les jalons"),
}


if __name__ == "__main__":
    main()
