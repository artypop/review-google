#!/usr/bin/env python3
"""
==============================================================================
Script : 07F_regression_03C_prenom.py
Entrée : data/local/03C_7_17_aout_prenom.parquet (03C_ajout_prenom.py)
         reviews_doublons_cleaned_all, pour le rythme habituel des fiches

Régression logistique réduite à quatre caractéristiques sur le corpus 03C,
avis 4 et 5 étoiles. Écrit le 2026-10-05 à la demande de Matthieu.

    PYTHONPATH=".venv/Lib/site-packages;outils" <python uv> logistic-regression-study/python/07F_regression_03C_prenom.py

------------------------------------------------------------------------------
LA SUPPRESSION
------------------------------------------------------------------------------
Dans 03C, les doublons sont déjà retirés : un avis disparu
(`deleted_detected_at` renseigné) est supprimé, sans attendre deux jours
d'absence (règle de Matthieu du 2026-10-05). Il compte comme supprimé si la
disparition est notée au plus tard 7 jours après la publication. Tous les avis
du corpus (publiés du 7 au 17 août) sont suivis au moins 7 jours.

------------------------------------------------------------------------------
LES QUATRE CARACTÉRISTIQUES, ET RIEN D'AUTRE
------------------------------------------------------------------------------
  prenom        le texte cite un prénom (annotation d'Axel)  référence : non
                Un avis sans texte compte « sans prénom ».
  photo         au moins une photo jointe                    référence : non
  reponse_j7    réponse du propriétaire au plus tard le 7e jour
                après la publication ; pas de réponse ou
                réponse plus tardive = non                   référence : la
                                                             modalité la plus
                                                             fréquente
  pic           au moins 3 avis 4-5 étoiles publiés sur la fiche ce jour-là,
                avis étudié compris, ET au moins 4 fois la moyenne journalière
                des avis 4-5 étoiles de la fiche sur les 365 jours avant le
                11 août                                      référence : non

Pas de contrôle (ni région, ni âge, ni secteur) : choix de Matthieu.

ATTENTION sur la réponse. La règle ne traite pas l'avis supprimé avant le
7e jour : il n'a eu que le temps de sa vie en ligne pour recevoir une réponse,
et compte « sans réponse » faute de temps. « Répondu au plus tard au 7e jour »
compte donc en partie qui a survécu (voir le 08B). Mesuré le 2026-10-05 : 20 %
des avis supprimés au 2e jour avaient une réponse, contre 50 % des avis restés
en ligne. Deux contrôles le corrigent (voir controles()) :
  jalon au 2e jour   réponse au plus tard au 2e jour, suppression comptée du
                     3e au 7e jour, avis disparus avant le jalon retirés ;
  jour par jour      une ligne par avis et par jour en ligne ; la réponse ne
                     compte que si elle est arrivée la veille ou avant, et un
                     indicateur par jour d'âge absorbe le pic des 6e-7e jours.

------------------------------------------------------------------------------
LES PASSAGES
------------------------------------------------------------------------------
US, Europe, tous. Écartés : les 55 avis sans annotation de prénom et les avis
des fiches qui ne sont plus relevées avant le 24 août. Marges d'incertitude
groupées par fiche.

Sorties : output-study/<date>-sorties-07F-03C-prenom/
  07F_risques_relatifs.csv   rapport de cotes, fourchette, p, par passage
  07F_effectifs.csv          avis, suppressions et taux par valeur et passage
  07F_controles.csv          les variantes de contrôle (voir controles())
  07F_summary_<passage>.txt  sortie complète de l'ajustement
Même modèle, mêmes avis, même fenêtre de 7 jours, avec en plus le secteur,
la taille et (pour « les deux ») la région en contrôle, non affichés (demande
de Matthieu du 2026-10-05, pour comparer en ne changeant qu'une chose) :
  07F_rapports_secteur_taille.csv, 07F_summary_secteur_taille_<passage>.txt
Copiés pour la restitution finale (livrables/restitution_finale/) :
  graphiques/regression_03C_prenom.png
  graphiques/regression_03C_prenom_secteur_taille.png
  donnees/regression_03C_prenom_secteur_taille_rapports_de_cotes.csv
  donnees/regression_03C_prenom_{rapports_de_cotes,effectifs,controles}.csv
==============================================================================
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "outils"))
from local import DERNIERE_VAGUE, PREMIERE_VAGUE, connexion  # noqa: E402

try:
    import statsmodels.api as sm
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import glm_numpy
    glm_numpy.installer()
    import statsmodels.api as sm

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CORPUS = RACINE / "data" / "local" / "03C_7_17_aout_prenom.parquet"
SORTIES = (Path(__file__).resolve().parent.parent / "output-study"
           / f"{date.today():%Y-%m-%d}-sorties-07F-03C-prenom")

HORIZON_J = 7
JALON_J = 2
PIC_MIN_AVIS = 3
PIC_MULTIPLE = 4

# Les 6 enseignes signalées, repérées comme dans le 03C.
CHAINES_ANTIPARASITAIRES = ("ecoshield pest solutions", "insight pest solutions",
                            "pointe pest control", "bulwark exterminating")
CID_SALLES_ESPAGNOLES = ("3163466139043001754", "10346942689164695031")

FINALE = RACINE / "livrables" / "restitution_finale"
GRAPHIQUE = FINALE / "graphiques" / "regression_03C_prenom.png"
GRAPHIQUE_CONTROLES = FINALE / "graphiques" / "regression_03C_prenom_secteur_taille.png"
REF_SECTEUR, REF_TAILLE = "automotive", "mono"
DONNEES = FINALE / "donnees"

# Palette de référence du skill dataviz, comme les autres graphiques de la restitution.
BLEU = "#2a78d6"
ENCRE, ENCRE_2, GRILLE, FOND = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
EFFECTIFS: dict[str, dict] = {}

LIBELLES = {
    "prenom": "prénom cité dans l'avis",
    "photo": "photo jointe",
    "reponse_j7": "réponse du propriétaire au plus tard au 7e jour",
    "sans_reponse_j7": "pas de réponse au 7e jour (ou plus tard)",
    "pic": "publié un jour de pic sur la fiche",
}

SQL = f"""
WITH
fin_suivi AS (
  SELECT cid, max(CAST(last_seen_at AS DATE)) AS fin_suivi
  FROM reviews_doublons_cleaned_all GROUP BY cid
),
avis_45 AS (
  SELECT cid, CAST(created_at AS DATE) AS jour
  FROM reviews_doublons_cleaned_all WHERE star >= 4
),
rythme AS (
  SELECT cid, count(*) / 365.0 AS par_jour
  FROM avis_45
  WHERE jour BETWEEN DATE '{PREMIERE_VAGUE}' - INTERVAL 365 DAY
                 AND DATE '{PREMIERE_VAGUE}' - INTERVAL 1 DAY
  GROUP BY cid
),
fiche_jour AS (
  SELECT cid, jour, count(*) AS n_jour FROM avis_45 GROUP BY cid, jour
)
SELECT c.review_id, c.cid, c.star, c.prenom, c.prenom_source,
       c.created_at, c.first_seen_at, c.deleted_detected_at, c.reply_date,
       if(b.country = 'US', 'US', 'Europe')                       AS region,
       b.industry, b.bucket,
       COALESCE({{condition_chaines}}, FALSE)
         OR c.cid IN ({{cid_salles}})                              AS enseigne,
       f.fin_suivi < DATE '{DERNIERE_VAGUE}'                     AS plus_relevee,
       coalesce(c.n_photos, 0) > 0                                 AS photo,
       date_diff('day', c.created_at, c.deleted_detected_at)       AS j_suppression,
       date_diff('day', c.created_at, c.reply_date)                AS j_reponse,
       date_diff('day', c.created_at, c.first_seen_at)             AS j_premiere_vue,
       coalesce(fj.n_jour, 0)                                      AS n_jour,
       coalesce(r.par_jour, 0)                                     AS par_jour
FROM '{CORPUS.as_posix()}' c
LEFT JOIN businesses b  ON b.cid = c.cid
LEFT JOIN fin_suivi  f  ON f.cid = c.cid
LEFT JOIN rythme     r  ON r.cid = c.cid
LEFT JOIN fiche_jour fj ON fj.cid = c.cid AND fj.jour = c.created_at
WHERE c.star >= 4
"""


def charger() -> pd.DataFrame:
    con = connexion("4GB")
    condition_chaines = " OR ".join(f"lower(b.name) LIKE '{nom}%'"
                                    for nom in CHAINES_ANTIPARASITAIRES)
    df = con.execute(SQL.format(
        condition_chaines=condition_chaines,
        cid_salles=", ".join(f"'{c}'" for c in CID_SALLES_ESPAGNOLES))).df()
    n0 = len(df)
    if df["region"].isna().any() or df["review_id"].duplicated().any():
        raise SystemExit("Fiche sans région ou avis dupliqué par la jointure.")

    sans_prenom = df["prenom"].isna()
    plus_relevee = df["plus_relevee"].fillna(False).astype(bool)
    print(f"[07F] {n0} avis 4-5 étoiles dans 03C\n"
          f"  écartés, prénom inconnu          : {int(sans_prenom.sum())}\n"
          f"  écartés, fiche plus relevée      : {int((plus_relevee & ~sans_prenom).sum())}"
          f" ({df.loc[plus_relevee, 'cid'].nunique()} fiches)")
    df = df[~sans_prenom & ~plus_relevee].copy()

    if (df["n_jour"] < 1).any():
        raise SystemExit("Un avis n'est pas compté dans le jour de sa fiche.")
    df["supprime"] = (df["j_suppression"] <= HORIZON_J).fillna(False).astype(int)
    df["prenom"] = df["prenom"].astype(int)
    df["photo"] = df["photo"].astype(int)
    df["reponse_j7"] = (df["j_reponse"] <= HORIZON_J).fillna(False).astype(int)
    df["pic"] = ((df["n_jour"] >= PIC_MIN_AVIS)
                 & (df["n_jour"] >= PIC_MULTIPLE * df["par_jour"])).astype(int)
    print(f"  gardés : {len(df)} avis, {df['cid'].nunique()} fiches, "
          f"{int(df['supprime'].sum())} suppressions au plus tard au {HORIZON_J}e jour")
    return df


def variable_reponse(df: pd.DataFrame) -> str:
    """Référence = la modalité la plus fréquente, mesurée sur tout le corpus
    gardé et appliquée aux trois passages pour qu'ils se comparent."""
    part = df["reponse_j7"].mean()
    print(f"  réponse au plus tard au {HORIZON_J}e jour : {part:.1%} des avis -> "
          f"référence : {'réponse' if part > 0.5 else 'pas de réponse'}")
    if part > 0.5:
        df["sans_reponse_j7"] = 1 - df["reponse_j7"]
        return "sans_reponse_j7"
    return "reponse_j7"


def ajuster(df: pd.DataFrame, variables: list[str], y: str = "supprime",
            secteur_taille: bool = False):
    """`secteur_taille` : ajoute en contrôle le secteur, la taille et, si le
    passage mélange les deux régions, la région. Ils ne sont pas affichés."""
    morceaux = [df[variables].astype(float)]
    if secteur_taille:
        for col, ref in [("industry", REF_SECTEUR), ("bucket", REF_TAILLE)]:
            morceaux.append(pd.get_dummies(df[col].astype(str), prefix=col, dtype=float)
                            .drop(columns=f"{col}_{ref}"))
        if df["region"].nunique() > 1:
            morceaux.append((df["region"] == "US").astype(float).rename("region_US").to_frame())
    X = pd.concat(morceaux, axis=1)
    X = sm.add_constant(X.loc[:, X.std() > 0], has_constant="add")
    return sm.GLM(df[y].astype(float), X, family=sm.families.Binomial()).fit(
        cov_type="cluster", cov_kwds={"groups": df["cid"].factorize()[0]})


def tableau(res, passage: str, variables: list[str]) -> pd.DataFrame:
    ic = res.conf_int()
    return pd.DataFrame({
        "passage": passage, "variable": variables,
        "libelle": [LIBELLES.get(v, v) for v in variables],
        "rapport_de_cotes": np.exp(res.params[variables]).values,
        "borne_basse": np.exp(ic.loc[variables, 0]).values,
        "borne_haute": np.exp(ic.loc[variables, 1]).values,
        "p_value": res.pvalues[variables].values,
    })


def effectifs(df: pd.DataFrame, passage: str, variables: list[str]) -> pd.DataFrame:
    lignes = []
    for v in variables:
        for valeur, g in df.groupby(v):
            lignes.append({"passage": passage, "variable": v, "valeur": "oui" if valeur else "non",
                           "avis": len(g), "suppressions": int(g["supprime"].sum()),
                           "taux_pour_1000": round(1000 * g["supprime"].mean(), 1)})
    return pd.DataFrame(lignes)


def jour_par_jour(df: pd.DataFrame) -> pd.DataFrame:
    """Une ligne par avis et par jour d'âge où il était en ligne et observé,
    du lendemain de sa première observation jusqu'à sa suppression ou au
    7e jour. La réponse compte si elle est arrivée la veille ou avant."""
    debut = np.maximum(1, df["j_premiere_vue"].to_numpy() + 1)
    fin = np.where(df["supprime"] == 1, df["j_suppression"].fillna(HORIZON_J), HORIZON_J)
    fin = fin.astype(int)
    n = np.clip(fin - debut + 1, 0, None)
    idx = np.repeat(np.arange(len(df)), n)
    jour = np.concatenate([np.arange(a, b + 1) for a, b in zip(debut, fin) if b >= a])
    p = df.iloc[idx][["cid", "region", "enseigne", "prenom", "photo", "pic",
                      "j_reponse", "supprime"]].reset_index(drop=True)
    p["jour"] = jour
    p["deja_repondu"] = (p["j_reponse"] <= p["jour"] - 1).fillna(False).astype(int)
    p["y"] = ((p["supprime"] == 1) & (p["jour"] == np.repeat(fin, n))).astype(int)
    return p


def controles(df: pd.DataFrame, variables: list[str], rep: str) -> pd.DataFrame:
    """Les variantes de contrôle, pour voir ce qui tient."""
    sorties = []

    # 0. Sans les 6 enseignes (aucun de leurs avis n'est européen dans 03C).
    for passage in ["US", "tous"]:
        d = df[~df["enseigne"]]
        d = d if passage == "tous" else d[d["region"] == passage]
        sorties.append(tableau(ajuster(d, variables), f"{passage}, sans enseignes", variables))

    # 1. Avis avec texte seulement : « sans prénom » ne mélange plus les avis sans texte.
    d = df[df["prenom_source"].isin(["axel", "axel_texte_modifie"])]
    sorties.append(tableau(ajuster(d, variables), "tous, avis avec texte", variables))

    # 2. Région ajoutée en contrôle (non affichée).
    d = df.assign(region_US=(df["region"] == "US").astype(int))
    sorties.append(tableau(ajuster(d, variables + ["region_US"]), "tous, + région", variables))

    # 3. Jalon fixe au 2e jour pour la réponse (montage du 08B).
    d = df[(df["j_premiere_vue"] <= JALON_J)
           & ~(df["j_suppression"] <= JALON_J).fillna(False)].copy()
    d["reponse_j2"] = (d["j_reponse"] <= JALON_J).fillna(False).astype(int)
    d["supprime_j3_j7"] = (d["j_suppression"].between(JALON_J + 1, HORIZON_J)
                           .fillna(False).astype(int))
    v = [x for x in variables if x != rep] + ["reponse_j2"]
    t = tableau(ajuster(d, v, "supprime_j3_j7"), "tous, jalon au 2e jour", v)
    t.loc[t["variable"] == "reponse_j2", "libelle"] = "réponse au plus tard au 2e jour"
    print(f"  jalon : {len(d)} avis vus et en ligne au {JALON_J}e jour, "
          f"{int(d['supprime_j3_j7'].sum())} supprimés du 3e au {HORIZON_J}e jour, "
          f"{d['reponse_j2'].mean():.1%} répondus au {JALON_J}e jour")
    sorties.append(t)

    # 4. Jour par jour : la réponse n'est comptée que si elle précède le jour
    #    regardé. Indicateurs de jour d'âge en contrôle, non affichés.
    p = jour_par_jour(df)
    print(f"  jour par jour : {len(p)} avis-jours, {int(p['y'].sum())} suppressions")
    v = [x for x in variables if x != rep] + ["deja_repondu"]
    for passage in ["US", "Europe", "tous"]:
        d = p if passage == "tous" else p[p["region"] == passage]
        jours = pd.get_dummies(d["jour"], prefix="jour", drop_first=True, dtype=float)
        d = pd.concat([d, jours], axis=1)
        t = tableau(ajuster(d, v + list(jours.columns), "y"),
                    f"{passage}, jour par jour", v)
        t.loc[t["variable"] == "deja_repondu", "libelle"] = "réponse déjà reçue la veille"
        sorties.append(t)
    return pd.concat(sorties)


def figure(rr: pd.DataFrame, rep: str, chemin: Path, titre: str) -> None:
    """Trois panneaux côte à côte, un par passage : rapport de cotes et
    fourchette à 95 %, sur une échelle logarithmique centrée sur 1."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.ticker import FixedLocator, NullLocator

    lignes = ["prenom", "photo", rep, "pic"]
    noms = {"prenom": "Prénom cité dans l'avis", "photo": "Photo jointe",
            "sans_reponse_j7": "Pas de réponse du\npropriétaire au 7e jour",
            "reponse_j7": "Réponse du propriétaire\nau plus tard au 7e jour",
            "pic": "Publié un jour de pic\nsur la fiche"}
    titres = {"US": "États-Unis", "Europe": "Europe", "tous": "Les deux"}

    fig, axes = plt.subplots(1, 3, figsize=(11, 4.2), dpi=150, sharey=True)
    fig.patch.set_facecolor(FOND)
    y = np.arange(len(lignes))[::-1]
    for ax, passage in zip(axes, ["US", "Europe", "tous"]):
        t = rr[rr["passage"] == passage].set_index("variable").loc[lignes]
        ax.set_facecolor(FOND)
        ax.axvline(1, color=ENCRE_2, lw=1, zorder=1)
        for yi, (_, r) in zip(y, t.iterrows()):
            net = r["p_value"] < 0.05
            ax.plot([r["borne_basse"], r["borne_haute"]], [yi, yi], color=BLEU,
                    lw=2, solid_capstyle="round", zorder=2)
            ax.plot(r["rapport_de_cotes"], yi, "o", ms=8, mew=2, zorder=3,
                    mec=BLEU, mfc=BLEU if net else FOND)
            ax.annotate(f"{r['rapport_de_cotes']:.2f}".replace(".", ","),
                        (r["rapport_de_cotes"], yi), xytext=(0, 8),
                        textcoords="offset points", ha="center", fontsize=8,
                        color=ENCRE, fontweight="bold" if net else "normal")
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
        ax.set_ylim(-0.6, len(lignes) - 0.4)
        ax.set_title(titres[passage], fontsize=10, color=ENCRE, loc="left")
    axes[0].set_yticks(y)
    axes[0].set_yticklabels([noms[v] for v in lignes], fontsize=9, color=ENCRE)
    axes[1].set_xlabel("risque de suppression (1 = pas d'effet)", color=ENCRE_2, fontsize=8)

    # Titre, légende et graphique seulement (demande de Matthieu du 2026-10-05) :
    # la méthode et les contrôles sont dans l'en-tête de ce script.
    fig.text(0.01, 0.975, titre,
             va="top", fontsize=12, color=ENCRE)
    legende = [Line2D([0], [0], marker="o", color=BLEU, mfc=BLEU, ms=7, lw=2,
                      label="significatif (p < 0,05)"),
               Line2D([0], [0], marker="o", color=BLEU, mfc=FOND, ms=7, mew=2, lw=2,
                      label="non significatif")]
    fig.legend(handles=legende, loc="upper right", bbox_to_anchor=(0.995, 0.985),
               frameon=False, fontsize=8, labelcolor=ENCRE, ncol=2, handlelength=2)
    fig.subplots_adjust(left=0.17, right=0.985, top=0.83, bottom=0.12, wspace=0.08)
    chemin.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(chemin, facecolor=FOND)
    plt.close(fig)


def main() -> None:
    SORTIES.mkdir(parents=True, exist_ok=True)
    df = charger()
    rep = variable_reponse(df)
    variables = ["prenom", "photo", rep, "pic"]

    resultats, effs = [], []
    for passage in ["US", "Europe", "tous"]:
        d = df if passage == "tous" else df[df["region"] == passage]
        res = ajuster(d, variables)
        resultats.append(tableau(res, passage, variables))
        effs.append(effectifs(d, passage, variables))
        (SORTIES / f"07F_summary_{passage}.txt").write_text(
            f"Passage : {passage}\n{len(d)} avis, {int(d['supprime'].sum())} suppressions, "
            f"{d['cid'].nunique()} fiches\n\n{res.summary()}", encoding="utf-8")

    rr = pd.concat(resultats)
    rr.to_csv(SORTIES / "07F_risques_relatifs.csv", index=False)
    ef = pd.concat(effs)
    ef.to_csv(SORTIES / "07F_effectifs.csv", index=False)
    ctl = controles(df, variables, rep)
    ctl.to_csv(SORTIES / "07F_controles.csv", index=False)

    for passage in ["US", "Europe", "tous"]:
        d = df if passage == "tous" else df[df["region"] == passage]
        EFFECTIFS[passage] = {"avis": len(d), "suppressions": int(d["supprime"].sum())}
    figure(rr, rep, GRAPHIQUE, "Risque de suppression d'un avis 4-5 étoiles dans les 7 jours")

    # Même chose, avec secteur, taille et région en contrôle.
    rr_st = []
    for passage in ["US", "Europe", "tous"]:
        d = df if passage == "tous" else df[df["region"] == passage]
        res = ajuster(d, variables, secteur_taille=True)
        rr_st.append(tableau(res, passage, variables))
        (SORTIES / f"07F_summary_secteur_taille_{passage}.txt").write_text(
            f"Passage : {passage}, secteur et taille en contrôle (et région pour tous)\n"
            f"{len(d)} avis, {int(d['supprime'].sum())} suppressions\n\n{res.summary()}",
            encoding="utf-8")
    rr_st = pd.concat(rr_st)
    rr_st.to_csv(SORTIES / "07F_rapports_secteur_taille.csv", index=False)
    figure(rr_st, rep, GRAPHIQUE_CONTROLES,
           "Risque de suppression d'un avis 4-5 étoiles dans les 7 jours, "
           "à secteur et taille égaux")
    DONNEES.mkdir(parents=True, exist_ok=True)
    rr.to_csv(DONNEES / "regression_03C_prenom_rapports_de_cotes.csv", index=False)
    ef.to_csv(DONNEES / "regression_03C_prenom_effectifs.csv", index=False)
    ctl.to_csv(DONNEES / "regression_03C_prenom_controles.csv", index=False)
    rr_st.to_csv(DONNEES / "regression_03C_prenom_secteur_taille_rapports_de_cotes.csv",
                 index=False)

    pd.set_option("display.width", 200)
    fmt = {"rapport_de_cotes": "{:.2f}".format, "borne_basse": "{:.2f}".format,
           "borne_haute": "{:.2f}".format, "p_value": "{:.3f}".format}
    print("\n== Effectifs ==\n" + ef.to_string(index=False))
    print("\n== Rapports de cotes ==\n" + rr.drop(columns="variable").to_string(index=False, formatters=fmt))
    print("\n== Contrôles ==\n" + ctl.drop(columns="variable").to_string(index=False, formatters=fmt))
    print(f"\nSorties : {SORTIES}\nRestitution : {GRAPHIQUE}\n              {DONNEES}")


if __name__ == "__main__":
    main()
