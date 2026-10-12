#!/usr/bin/env python3
"""
==============================================================================
Script : 07G_regression_03C_jour_par_jour.py
Entrée : data/local/03C_7_17_aout_prenom.parquet, lu par le 07F (même
         population, mêmes variables)

Suite du 07F, écrite le 2026-10-05 à la demande de Matthieu. Le 07F et ses
sorties ne sont pas modifiés.

    PYTHONPATH=".venv/Lib/site-packages;outils" <python uv> logistic-regression-study/python/07G_regression_03C_jour_par_jour.py

------------------------------------------------------------------------------
CE QUI CHANGE PAR RAPPORT AU 07F
------------------------------------------------------------------------------
1. TOUT LE SUIVI, JOUR PAR JOUR
   Le 07F ne regarde que les 7 premiers jours et rate 272 des 903 suppressions.
   Ici, chaque avis compte une ligne par jour où il était en ligne et observé :
   du lendemain de sa première observation jusqu'à sa suppression, ou jusqu'au
   24 août. Le robot ne passe qu'à partir du 11 août : un avis compte au plus
   13 jours observés. Un avis du 7 août est observé de son 5e à son 17e jour
   (ses 4 premiers jours sont invisibles), un avis du 17 août de son 2e à son
   7e jour. Mesuré le 2026-10-05 : 13 jours au plus pour les avis publiés du
   7 au 11 août, puis un de moins par jour de publication jusqu'à 7 jours.
   La différence de durée et d'âge observé est prise en compte ligne par ligne.

2. LA RÉPONSE NE COMPTE QUE SI ELLE EST DÉJÀ ARRIVÉE
   Pour un jour donné, l'avis a une réponse si elle est arrivée la veille ou
   avant. Un avis supprimé tôt n'est plus compté « sans réponse » faute de
   temps (biais de survie du 07F).

3. TROIS CONTRÔLES, DANS LE MODÈLE ET JAMAIS AFFICHÉS
   secteur   référence : automobile
   taille    référence : mono
   région    passage « les deux » seulement
   Sans eux, le prénom paraissait dangereux (1,68) parce que les avis
   américains et ceux des services à domicile citent plus de prénoms et sont
   plus supprimés. Mesuré le 2026-10-05 : 0,98 avec ces contrôles.

   Le jour d'âge de l'avis n'est PAS dans le modèle principal (décision de
   Matthieu du 2026-10-05). Il est ajouté dans un contrôle.

------------------------------------------------------------------------------
LES QUATRE CARACTÉRISTIQUES AFFICHÉES
------------------------------------------------------------------------------
Mêmes caractéristiques, même sens et même ordre que la figure du 07F (demande
de Matthieu du 2026-10-05) :
  prenom        le texte cite un prénom                 référence : non
  photo         au moins une photo jointe               référence : non
  sans_reponse  pas de réponse du propriétaire reçue
                la veille ou avant                      référence : réponse
                                                        reçue
                Le 07F prenait pour référence la modalité la plus fréquente
                (réponse, 50,1 % des avis). Ici, 48,4 % des avis-jours ont
                déjà une réponse : la référence est gardée pour que les deux
                figures se lisent de la même façon.
  pic           publié un jour de pic sur la fiche      référence : non
                (au moins 3 avis 4-5 étoiles ce jour-là ET au moins 4 fois la
                moyenne journalière des 365 jours avant le 11 août, voir 07F)

------------------------------------------------------------------------------
LES CONTRÔLES (07G_controles.csv)
------------------------------------------------------------------------------
  + jour d'âge       un indicateur par jour d'âge (12 et plus regroupés)
  même fiche         un indicateur par fiche à la place du secteur, de la
                     taille et de la région, sur les fiches qui ont au moins
                     une suppression (les autres n'apportent rien à cette
                     comparaison)
  sans enseignes     US et les deux, sans les 6 enseignes signalées

------------------------------------------------------------------------------
SORTIES
------------------------------------------------------------------------------
output-study/<date>-sorties-07G-03C-jour-par-jour/
  07G_rapports_de_cotes.csv, 07G_effectifs.csv, 07G_controles.csv,
  07G_summary_<passage>.txt (contrôles compris)
livrables/restitution_finale/ (sans écraser les fichiers du 07F)
  graphiques/regression_03C_suivi_complet.png
  donnees/regression_03C_suivi_complet_{rapports_de_cotes,effectifs,controles}.csv
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
_spec = importlib.util.spec_from_file_location("f07", ICI / "07F_regression_03C_prenom.py")
f07 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(f07)
sm = f07.sm
from local import DERNIERE_VAGUE, connexion  # noqa: E402  (chemin posé par le 07F)

SORTIES = (ICI.parent / "output-study"
           / f"{date.today():%Y-%m-%d}-sorties-07G-03C-jour-par-jour")
GRAPHIQUE = f07.FINALE / "graphiques" / "regression_03C_suivi_complet.png"
DONNEES = f07.DONNEES

VARIABLES = ["prenom", "photo", "sans_reponse", "pic"]
LIBELLES = {"prenom": "prénom cité dans l'avis", "photo": "photo jointe",
            "sans_reponse": "pas de réponse du propriétaire (reçue la veille ou avant)",
            "pic": "publié un jour de pic sur la fiche"}
REF_SECTEUR, REF_TAILLE = "automotive", "mono"
JOUR_MAX = 12
PASSAGES = ["US", "Europe", "tous"]


# ---------------------------------------------------------------------------
# Données
# ---------------------------------------------------------------------------

def avis() -> pd.DataFrame:
    """Les avis du 07F, avec secteur, taille et durée de suivi."""
    df = f07.charger()
    con = connexion("2GB")
    fiches = con.execute("SELECT cid, industry, bucket FROM businesses").df()
    df = df.merge(fiches, on="cid", how="left")
    if df[["industry", "bucket"]].isna().any().any():
        raise SystemExit("Des avis n'ont pas de secteur ou de taille.")
    df["j_fin"] = (pd.Timestamp(DERNIERE_VAGUE) - pd.to_datetime(df["created_at"])).dt.days
    df["supprime_tout"] = df["j_suppression"].notna().astype(int)
    print(f"  suppressions sur tout le suivi : {int(df['supprime_tout'].sum())} "
          f"(dont {int(df['supprime'].sum())} au plus tard au 7e jour)")
    return df


def avis_jours(df: pd.DataFrame) -> pd.DataFrame:
    """Une ligne par avis et par jour d'âge où il était en ligne et observé."""
    debut = np.maximum(1, df["j_premiere_vue"].to_numpy() + 1)
    fin = np.where(df["supprime_tout"] == 1, df["j_suppression"].fillna(0),
                   df["j_fin"]).astype(int)
    n = np.clip(fin - debut + 1, 0, None)
    idx = np.repeat(np.arange(len(df)), n)
    p = df.iloc[idx][["review_id", "cid", "region", "enseigne", "industry", "bucket",
                      "prenom", "photo", "pic", "j_reponse",
                      "supprime_tout"]].reset_index(drop=True)
    p["jour"] = np.concatenate([np.arange(a, b + 1) for a, b in zip(debut, fin) if b >= a])
    p["sans_reponse"] = 1 - (p["j_reponse"] <= p["jour"] - 1).fillna(False).astype(int)
    p["y"] = ((p["supprime_tout"] == 1) & (p["jour"] == np.repeat(fin, n))).astype(int)
    if int(p["y"].sum()) != int(df["supprime_tout"].sum()):
        raise SystemExit("Des suppressions se sont perdues dans le passage aux avis-jours.")
    print(f"  {len(p):,} avis-jours, {int(p['y'].sum())} suppressions".replace(",", " "))
    return p


# ---------------------------------------------------------------------------
# Ajustement
# ---------------------------------------------------------------------------

def indicateurs(d: pd.DataFrame, colonne: str, reference: str, prefixe: str) -> pd.DataFrame:
    x = pd.get_dummies(d[colonne].astype(str), prefix=prefixe, dtype=float)
    return x.drop(columns=f"{prefixe}_{reference}", errors="ignore")


def matrice(d: pd.DataFrame, region: bool, controles=("secteur", "taille"),
            jour: bool = False, fiche: bool = False) -> pd.DataFrame:
    morceaux = [d[VARIABLES].astype(float)]
    if "secteur" in controles:
        morceaux.append(indicateurs(d, "industry", REF_SECTEUR, "secteur"))
    if "taille" in controles:
        morceaux.append(indicateurs(d, "bucket", REF_TAILLE, "taille"))
    if region:
        morceaux.append((d["region"] == "US").astype(float).rename("region_US").to_frame())
    if jour:
        morceaux.append(indicateurs(d.assign(j=d["jour"].clip(upper=JOUR_MAX)), "j", "1", "jour"))
    if fiche:
        morceaux.append(indicateurs(d, "cid", d["cid"].iloc[0], "fiche"))
    X = pd.concat(morceaux, axis=1)
    X = X.loc[:, X.std() > 0]           # un secteur absent d'un passage, par exemple
    return sm.add_constant(X, has_constant="add")


def ajuster(d: pd.DataFrame, **options):
    X = matrice(d, **options)
    return sm.GLM(d["y"].astype(float), X, family=sm.families.Binomial()).fit(
        cov_type="cluster", cov_kwds={"groups": d["cid"].factorize()[0]})


def tableau(res, passage: str) -> pd.DataFrame:
    ic = res.conf_int()
    return pd.DataFrame({
        "passage": passage, "variable": VARIABLES,
        "libelle": [LIBELLES[v] for v in VARIABLES],
        "rapport_de_cotes": np.exp(res.params[VARIABLES]).values,
        "borne_basse": np.exp(ic.loc[VARIABLES, 0]).values,
        "borne_haute": np.exp(ic.loc[VARIABLES, 1]).values,
        "p_value": res.pvalues[VARIABLES].values,
    })


def selection(p: pd.DataFrame, passage: str) -> pd.DataFrame:
    return p if passage == "tous" else p[p["region"] == passage]


def effectifs(p: pd.DataFrame, df: pd.DataFrame) -> pd.DataFrame:
    """Pour chaque variable : avis (au niveau de l'avis, la réponse comptée si
    elle est arrivée pendant le suivi), avis-jours, suppressions, taux."""
    lignes = []
    for passage in PASSAGES:
        d = selection(p, passage)
        a = df if passage == "tous" else df[df["region"] == passage]
        a = a.assign(sans_reponse=a["j_reponse"].isna().astype(int))
        for v in VARIABLES:
            for valeur, g in d.groupby(v):
                lignes.append({
                    "passage": passage, "variable": v, "valeur": "oui" if valeur else "non",
                    "avis": int((a[v] == valeur).sum()), "avis_jours": len(g),
                    "suppressions": int(g["y"].sum()),
                    "taux_pour_10000_avis_jours": round(1e4 * g["y"].mean(), 1)})
    return pd.DataFrame(lignes)


def controles(p: pd.DataFrame) -> pd.DataFrame:
    sorties = []
    for passage in PASSAGES:
        d = selection(p, passage)
        sorties.append(tableau(ajuster(d, region=passage == "tous", jour=True),
                               f"{passage}, + jour d'âge"))
    for passage in PASSAGES:
        d = selection(p, passage)
        d = d[d["cid"].isin(d.loc[d["y"] == 1, "cid"].unique())]
        t = tableau(ajuster(d, region=False, controles=(), fiche=True),
                    f"{passage}, même fiche")
        t["fiches"] = d["cid"].nunique()
        sorties.append(t)
    for passage in ["US", "tous"]:
        d = selection(p, passage)
        sorties.append(tableau(ajuster(d[~d["enseigne"]], region=passage == "tous"),
                               f"{passage}, sans enseignes"))
    return pd.concat(sorties)


# ---------------------------------------------------------------------------
# Figure
# ---------------------------------------------------------------------------

def figure(rr: pd.DataFrame, ctl: pd.DataFrame, comptes: dict) -> None:
    """Même construction que la figure du 07F : un panneau par passage,
    rapport de cotes et fourchette à 95 %, échelle logarithmique."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.ticker import FixedLocator, NullLocator

    BLEU, ENCRE, ENCRE_2, GRILLE, FOND = f07.BLEU, f07.ENCRE, f07.ENCRE_2, f07.GRILLE, f07.FOND
    noms = {"prenom": "Prénom cité dans l'avis", "photo": "Photo jointe",
            "sans_reponse": "Pas de réponse du\npropriétaire",
            "pic": "Publié un jour de pic\nsur la fiche"}
    titres = {"US": "États-Unis", "Europe": "Europe", "tous": "Les deux"}
    virgule = lambda x: f"{x:.2f}".replace(".", ",")

    fig, axes = plt.subplots(1, 3, figsize=(11, 4.2), dpi=150, sharey=True)
    fig.patch.set_facecolor(FOND)
    y = np.arange(len(VARIABLES))[::-1]
    for ax, passage in zip(axes, PASSAGES):
        t = rr[rr["passage"] == passage].set_index("variable").loc[VARIABLES]
        ax.set_facecolor(FOND)
        ax.axvline(1, color=ENCRE_2, lw=1, zorder=1)
        for yi, (_, r) in zip(y, t.iterrows()):
            net = r["p_value"] < 0.05
            ax.plot([r["borne_basse"], r["borne_haute"]], [yi, yi], color=BLEU,
                    lw=2, solid_capstyle="round", zorder=2)
            ax.plot(r["rapport_de_cotes"], yi, "o", ms=8, mew=2, zorder=3,
                    mec=BLEU, mfc=BLEU if net else FOND)
            ax.annotate(virgule(r["rapport_de_cotes"]), (r["rapport_de_cotes"], yi),
                        xytext=(0, 8), textcoords="offset points", ha="center",
                        fontsize=8, color=ENCRE, fontweight="bold" if net else "normal")
        ax.set_xscale("log")
        ax.set_xlim(0.12, 8)
        graduations = [0.25, 0.5, 1, 2, 4]
        ax.xaxis.set_major_locator(FixedLocator(graduations))
        ax.xaxis.set_minor_locator(NullLocator())
        ax.set_xticklabels([f"{g:g}".replace(".", ",") for g in graduations])
        ax.grid(axis="x", color=GRILLE, lw=0.8, zorder=0)
        ax.tick_params(colors=ENCRE_2, labelsize=8, length=0)
        for cote in ["top", "right", "left"]:
            ax.spines[cote].set_visible(False)
        ax.spines["bottom"].set_color(GRILLE)
        ax.set_ylim(-0.6, len(VARIABLES) - 0.4)
        ax.set_title(titres[passage], fontsize=10, color=ENCRE, loc="left")
    axes[0].set_yticks(y)
    axes[0].set_yticklabels([noms[v] for v in VARIABLES], fontsize=9, color=ENCRE)
    axes[1].set_xlabel("risque de suppression (1 = pas d'effet)", color=ENCRE_2, fontsize=8)

    # Titre, légende et graphique seulement (demande de Matthieu du 2026-10-05) :
    # la méthode, les contrôles et la vérification à fiche égale sont dans
    # l'en-tête de ce script et dans 07G_controles.csv.
    fig.text(0.01, 0.975, "Risque de suppression d'un avis 4-5 étoiles, "
             "à secteur et taille égaux (suivi complet)",
             va="top", fontsize=12, color=ENCRE)
    legende = [Line2D([0], [0], marker="o", color=BLEU, mfc=BLEU, ms=7, lw=2,
                      label="significatif (p < 0,05)"),
               Line2D([0], [0], marker="o", color=BLEU, mfc=FOND, ms=7, mew=2, lw=2,
                      label="non significatif")]
    fig.legend(handles=legende, loc="upper right", bbox_to_anchor=(0.995, 0.985),
               frameon=False, fontsize=8, labelcolor=ENCRE, ncol=2, handlelength=2)
    fig.subplots_adjust(left=0.17, right=0.985, top=0.83, bottom=0.12, wspace=0.08)
    GRAPHIQUE.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(GRAPHIQUE, facecolor=FOND)
    plt.close(fig)


# ---------------------------------------------------------------------------

def main() -> None:
    SORTIES.mkdir(parents=True, exist_ok=True)
    df = avis()
    p = avis_jours(df)

    resultats, comptes = [], {}
    for passage in PASSAGES:
        d = selection(p, passage)
        res = ajuster(d, region=passage == "tous")
        resultats.append(tableau(res, passage))
        comptes[passage] = (int(d["review_id"].nunique()), int(d["y"].sum()))
        (SORTIES / f"07G_summary_{passage}.txt").write_text(
            f"Passage : {passage}\n{len(d)} avis-jours, {comptes[passage][0]} avis, "
            f"{comptes[passage][1]} suppressions, {d['cid'].nunique()} fiches\n"
            "secteur_*, taille_* et region_US sont des contrôles, non affichés.\n\n"
            f"{res.summary()}", encoding="utf-8")
    rr = pd.concat(resultats)
    ef = effectifs(p, df)
    ctl = controles(p)

    for nom, table in [("rapports_de_cotes", rr), ("effectifs", ef), ("controles", ctl)]:
        table.to_csv(SORTIES / f"07G_{nom}.csv", index=False)
        table.to_csv(DONNEES / f"regression_03C_suivi_complet_{nom}.csv", index=False)
    figure(rr, ctl, comptes)

    pd.set_option("display.width", 200)
    fmt = {"rapport_de_cotes": "{:.2f}".format, "borne_basse": "{:.2f}".format,
           "borne_haute": "{:.2f}".format, "p_value": "{:.3f}".format}
    print("\n== Rapports de cotes ==\n"
          + rr.drop(columns="variable").to_string(index=False, formatters=fmt))
    print("\n== Contrôles ==\n"
          + ctl.drop(columns="variable").to_string(index=False, formatters=fmt))
    print(f"\nSorties : {SORTIES}\nRestitution : {GRAPHIQUE}\n              {DONNEES}")


if __name__ == "__main__":
    main()
