#!/usr/bin/env python3
"""Pourquoi certaines fiches perdent-elles beaucoup de leurs nouveaux avis ?

    PYTHONPATH=".venv/Lib/site-packages;outils" <python uv> etudes-ponctuelles/2026-10-09-fiches-touchees/calcul.py

Demande de Matthieu du 2026-10-09 (question « Axel s'est-il emballé ? »). Les 84 fiches du
2026-10-08 étaient choisies sur le nombre d'avis perdus, tous âges confondus. Ici, seuls
les nouveaux avis comptent, et les fiches sont choisies sur leur taux de perte.

------------------------------------------------------------------------------
LA COHORTE
------------------------------------------------------------------------------
Avis 4-5 étoiles de 03C (data/local/03C_7_17_aout_prenom.parquet, doublons retirés)
publiés du 11 au 17 août 2026, sur les fiches relevées jusqu'au 24 août. Chaque avis est
suivi 7 jours. Supprimé = disparition notée (`deleted_detected_at`) au plus tard au 7e
jour, sans règle des 2 jours (règle de Matthieu pour 03C).

------------------------------------------------------------------------------
LES FICHES
------------------------------------------------------------------------------
  étudiées   au moins 5 avis publiés dans la cohorte, hors six enseignes
             (option --avec-chaines : quatre chaînes antiparasitaires comprises, sorties
             dans analyse_exploratoire/avec_chaines_antiparasitaires/)
  touchées   parmi elles, au moins 2 avis supprimés et au moins 10 % de leurs avis
  témoins    parmi elles, aucun avis supprimé

------------------------------------------------------------------------------
LES INDICATEURS (par fiche)
------------------------------------------------------------------------------
Sollicitation (sur la cohorte, rythme habituel = avis 4-5 étoiles des 365 jours avant le
11 août, plancher à 1 avis par an) :
  volume habituel        avis 4-5 étoiles par semaine, habituellement
  intensité              avis publiés dans la semaine / volume habituel
  jours de pic           jours de la semaine avec au moins 3 avis 4-5 étoiles et au moins
                         4 fois la moyenne journalière habituelle (définition du 07F)
  part du jour le plus chargé   part des avis de la semaine publiés le même jour
Auteurs :
  comptes neufs          auteur avec 2 avis ou moins au total (reviewer_review_count)
  sans niveau Local Guide
  auteur actif ailleurs le même jour   (au moins un cas sur la fiche) l'auteur a publié un autre avis 4-5 étoiles, sur
                         une autre fiche de la base, le même jour
Contenu :
  5 étoiles, sans texte, texte court (1 à 40 caractères), prénom cité, photo,
  texte en double    (au moins un cas sur la fiche) même texte (minuscules, sans ponctuation, au moins 20 caractères)
                     qu'un autre avis de la fiche dans la semaine
Propriétaire (sur les avis 4-5 étoiles des 365 jours avant le 11 août, pour ne pas
dépendre des suppressions de la cohorte) :
  taux de réponse, délai médian de réponse (jours),
  réponses standardisées  même texte de réponse qu'une autre réponse de la fiche

------------------------------------------------------------------------------
LES ÉTAPES
------------------------------------------------------------------------------
a. Sélection des fiches touchées, sur le taux.
b. Comparaison avec des témoins semblables : même région, même secteur, même quart de
   volume habituel. Pondération des témoins pour reproduire, strate par strate, la
   répartition des fiches touchées (appariement exact par strates).
c. Modèle au niveau de la fiche : régression binomiale (avis supprimés sur avis publiés),
   tous les indicateurs ensemble, à région, secteur, taille et volume habituel égaux ;
   marges d'incertitude robustes (sandwich). Fiches avec au moins 5 avis
   4-5 étoiles dans l'année précédente (sinon pas d'historique de réponse).

Sorties : livrables/restitution_finale_v2/analyse_exploratoire/
  fiches_indicateurs.csv        une ligne par fiche étudiée (et par fiche des six enseignes)
  selection_fiches.csv          effectifs de la sélection
  comparaison_touchees_temoins.csv, comparaison_touchees_temoins.png
  modele_fiche.csv, modele_fiche.png
"""
import re
import sys
import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import statsmodels.api as sm  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.ticker import FixedLocator, NullLocator  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "outils"))
from local import connexion  # noqa: E402

pd.set_option("display.width", 220)
CORPUS = RACINE / "data" / "local" / "03C_7_17_aout_prenom.parquet"
SORTIE = RACINE / "livrables" / "restitution_finale_v2" / "analyse_exploratoire"
# Variante demandée par Matthieu le 2026-10-09 : les quatre chaînes antiparasitaires
# comprises dans les fiches étudiées (les deux salles espagnoles n'ont aucun avis publié
# du 11 au 17 août). Sorties dans un sous-dossier, la version de base n'est pas touchée.
AVEC_CHAINES = "--avec-chaines" in sys.argv
if AVEC_CHAINES:
    SORTIE = SORTIE / "avec_chaines_antiparasitaires"
PERIMETRE = "quatre chaînes antiparasitaires comprises" if AVEC_CHAINES else "hors six enseignes"
DEBUT, FIN, DERNIER_RELEVE = "2026-08-11", "2026-08-17", "2026-08-24"
HORIZON_J = 7
MIN_PUBLIES, MIN_SUPPRIMES, MIN_TAUX = 5, 2, 0.10
MIN_HISTORIQUE = 5
PIC_MIN_AVIS, PIC_MULTIPLE = 3, 4

CHAINES_ANTIPARASITAIRES = ("ecoshield pest solutions", "insight pest solutions",
                            "pointe pest control", "bulwark exterminating")
CID_SALLES_ESPAGNOLES = ("3163466139043001754", "10346942689164695031")

# Palette de référence du skill dataviz : bleu (série 1), orange (série 2).
BLEU, ORANGE = "#2a78d6", "#eb6834"
ENCRE, ENCRE_2, GRILLE, FOND = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"

CONDITION_ENSEIGNE = (
    "(" + " OR ".join(f"lower(b.name) LIKE '{n}%'" for n in CHAINES_ANTIPARASITAIRES) + ")"
    + f" OR b.cid IN ({', '.join(repr(c) for c in CID_SALLES_ESPAGNOLES)})")

SQL_AVIS = f"""
WITH fin AS (SELECT cid, max(CAST(last_seen_at AS DATE)) AS fs
             FROM reviews_doublons_cleaned_all GROUP BY cid),
ailleurs AS (
  SELECT regexp_extract(review_link, 'contrib/([0-9]+)', 1) AS auteur,
         CAST(created_at AS DATE) AS jour, count(DISTINCT cid) AS n_fiches
  FROM reviews_doublons_cleaned_all
  WHERE star >= 4 AND CAST(created_at AS DATE) BETWEEN DATE '{DEBUT}' AND DATE '{FIN}'
  GROUP BY ALL
)
SELECT c.cid, c.review_id, c.star, c.text, c.created_at, c.prenom,
       coalesce(c.n_photos, 0) > 0 AS photo,
       c.reviewer_review_count, c.local_guide_level,
       coalesce(date_diff('day', c.created_at, c.deleted_detected_at) <= {HORIZON_J}, FALSE) AS supprime,
       coalesce(a.n_fiches, 1) > 1 AS auteur_ailleurs
FROM '{CORPUS.as_posix()}' c
JOIN fin f ON f.cid = c.cid
LEFT JOIN ailleurs a ON a.auteur = regexp_extract(c.review_link, 'contrib/([0-9]+)', 1)
                    AND a.jour = c.created_at
WHERE c.star >= 4 AND c.created_at BETWEEN DATE '{DEBUT}' AND DATE '{FIN}'
  AND f.fs >= DATE '{DERNIER_RELEVE}'
"""

SQL_FICHES = f"""
SELECT b.cid, b.name, if(b.country = 'US', 'US', 'Europe') AS region, b.industry, b.bucket,
       coalesce({CONDITION_ENSEIGNE}, FALSE) AS enseigne
FROM businesses b
"""

SQL_HISTORIQUE = f"""
SELECT cid, count(*) AS n_hist,
       avg((reply_text IS NOT NULL)::INT) AS taux_reponse,
       median(date_diff('day', CAST(created_at AS DATE), CAST(reply_date AS DATE)))
         FILTER (reply_text IS NOT NULL) AS delai_reponse_j,
       list(reply_text) FILTER (reply_text IS NOT NULL) AS reponses
FROM reviews_doublons_cleaned_all
WHERE star >= 4 AND CAST(created_at AS DATE) BETWEEN DATE '{DEBUT}' - INTERVAL 365 DAY
                                                 AND DATE '{DEBUT}' - INTERVAL 1 DAY
GROUP BY cid
"""

INDICATEURS = {
    # nom : (libellé, famille, unité de lecture dans le modèle)
    "log2_intensite": ("Intensité de la semaine\n(× le rythme habituel, en log2)", "Sollicitation", "doublement"),
    "jours_pic": ("Jours de pic dans la semaine", "Sollicitation", "1 jour"),
    "part_jour_max": ("Part du jour le plus chargé", "Sollicitation", "+10 points"),
    "part_comptes_neufs": ("Comptes neufs (2 avis ou moins)", "Auteurs", "+10 points"),
    "part_sans_niveau": ("Auteurs sans niveau Local Guide", "Auteurs", "+10 points"),
    "auteur_ailleurs": ("Au moins un auteur actif sur\nune autre fiche le même jour", "Auteurs", "oui / non"),
    "part_5_etoiles": ("Avis 5 étoiles", "Contenu", "+10 points"),
    "part_sans_texte": ("Avis sans texte", "Contenu", "+10 points"),
    "part_texte_court": ("Texte court (1 à 40 caractères)", "Contenu", "+10 points"),
    "part_prenom": ("Prénom cité", "Contenu", "+10 points"),
    "part_photo": ("Photo jointe", "Contenu", "+10 points"),
    "texte_double": ("Au moins deux avis au même texte", "Contenu", "oui / non"),
    "taux_reponse": ("Taux de réponse du propriétaire\n(année précédente)", "Propriétaire", "+10 points"),
    "part_reponses_standard": ("Réponses standardisées\n(année précédente)", "Propriétaire", "+10 points"),
}
AUTRES = {"au_moins_un_pic": "Au moins un jour de pic\ndans la semaine"}
DESCRIPTIFS = {"volume_semaine": "Volume habituel (avis par semaine)",
               "intensite": "Intensité de la semaine (× le rythme habituel)",
               "delai_reponse_j": "Délai médian de réponse (jours)"}


def normaliser(t) -> str:
    return re.sub(r"[\W_]+", " ", str(t).lower()).strip() if isinstance(t, str) else ""


def part_doublons(textes: pd.Series, min_car: int = 20) -> float:
    n = textes.map(normaliser)
    n = n[n.str.len() >= min_car]
    if len(textes) == 0:
        return np.nan
    return float(n.duplicated(keep=False).sum()) / len(textes)


def charger(con) -> tuple[pd.DataFrame, pd.DataFrame]:
    avis = con.execute(SQL_AVIS).df()
    if avis["review_id"].duplicated().any():
        raise SystemExit("Avis dupliqué dans la cohorte.")
    fiches = con.execute(SQL_FICHES).df()
    print(f"cohorte : {len(avis)} avis 4-5 étoiles publiés du {DEBUT} au {FIN}, "
          f"{int(avis['supprime'].sum())} supprimés au plus tard au {HORIZON_J}e jour, "
          f"{avis['cid'].nunique()} fiches")

    rythme = con.execute(f"""
        SELECT cid, count(*) / 365.0 AS par_jour FROM reviews_doublons_cleaned_all
        WHERE star >= 4 AND CAST(created_at AS DATE) BETWEEN DATE '{DEBUT}' - INTERVAL 365 DAY
                                                         AND DATE '{DEBUT}' - INTERVAL 1 DAY
        GROUP BY cid""").df()
    hist = con.execute(SQL_HISTORIQUE).df()
    hist["part_reponses_standard"] = hist["reponses"].map(
        lambda r: part_doublons(pd.Series(list(r)), min_car=1)
        if isinstance(r, (list, np.ndarray)) and len(r) else np.nan)
    hist = hist.drop(columns="reponses")
    fiches = fiches.merge(rythme, on="cid", how="left").merge(hist, on="cid", how="left")
    fiches["par_jour"] = fiches["par_jour"].fillna(0).clip(lower=1 / 365)
    fiches["n_hist"] = fiches["n_hist"].fillna(0).astype(int)
    return avis, fiches


def indicateurs(avis: pd.DataFrame, fiches: pd.DataFrame) -> pd.DataFrame:
    a = avis.merge(fiches[["cid", "par_jour"]], on="cid", how="left")
    a["longueur"] = a["text"].fillna("").str.strip().str.len()
    a["jour"] = pd.to_datetime(a["created_at"])
    par_jour = a.groupby(["cid", "jour"]).size().rename("n_jour").reset_index()
    par_jour = par_jour.merge(fiches[["cid", "par_jour"]], on="cid")
    par_jour["pic"] = (par_jour["n_jour"] >= PIC_MIN_AVIS) & (par_jour["n_jour"] >= PIC_MULTIPLE * par_jour["par_jour"])
    pics = par_jour.groupby("cid").agg(jours_pic=("pic", "sum"), n_jour_max=("n_jour", "max"))

    g = a.groupby("cid")
    f = pd.DataFrame({
        "publies": g.size(),
        "supprimes": g["supprime"].sum().astype(int),
        "part_comptes_neufs": g["reviewer_review_count"].apply(lambda s: (s <= 2).mean()),
        "part_sans_niveau": g["local_guide_level"].apply(lambda s: s.isna().mean()),
        "part_auteur_ailleurs": g["auteur_ailleurs"].mean(),
        "part_5_etoiles": g["star"].apply(lambda s: (s == 5).mean()),
        "part_sans_texte": g["longueur"].apply(lambda s: (s == 0).mean()),
        "part_texte_court": g["longueur"].apply(lambda s: s.between(1, 40).mean()),
        "part_prenom": g["prenom"].apply(lambda s: s.fillna(False).astype(bool).mean()),
        "part_photo": g["photo"].mean(),
        "part_texte_double": g["text"].apply(part_doublons),
    }).join(pics)
    # Cas rares (moins de 1 % des avis) : lus en présence sur la fiche plutôt qu'en part.
    f["auteur_ailleurs"] = (f["part_auteur_ailleurs"] > 0).astype(int)
    f["texte_double"] = (f["part_texte_double"] > 0).astype(int)
    f["au_moins_un_pic"] = (f["jours_pic"] > 0).astype(int)
    f["taux_suppression"] = f["supprimes"] / f["publies"]
    f["part_jour_max"] = f["n_jour_max"] / f["publies"]
    f = f.reset_index().merge(fiches, on="cid", how="left")
    f["volume_semaine"] = 7 * f["par_jour"]
    f["intensite"] = f["publies"] / f["volume_semaine"]
    f["log2_intensite"] = np.log2(f["intensite"])
    f["log2_volume"] = np.log2(f["volume_semaine"])
    return f


def selection(f: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    etudiees = f[(f["publies"] >= MIN_PUBLIES) & (AVEC_CHAINES | ~f["enseigne"])].copy()
    etudiees["groupe"] = np.select(
        [(etudiees["supprimes"] >= MIN_SUPPRIMES) & (etudiees["taux_suppression"] >= MIN_TAUX),
         etudiees["supprimes"] == 0],
        ["touchée", "témoin"], default="entre les deux")
    ens = f[f["enseigne"] & (f["publies"] >= 1) & (not AVEC_CHAINES)].copy()
    ens["groupe"] = "six enseignes"
    lignes = [("fiches de la cohorte", f["cid"].nunique(), int(f["publies"].sum()), int(f["supprimes"].sum())),
              ("dont quatre chaînes antiparasitaires" if AVEC_CHAINES else "dont six enseignes",
               len(f[f["enseigne"]]), int(f.loc[f["enseigne"], "publies"].sum()),
               int(f.loc[f["enseigne"], "supprimes"].sum())),
              (f"étudiées (au moins {MIN_PUBLIES} avis publiés, "
               f"{'chaînes antiparasitaires comprises' if AVEC_CHAINES else 'hors enseignes'})", len(etudiees),
               int(etudiees["publies"].sum()), int(etudiees["supprimes"].sum()))]
    for gr in ["touchée", "entre les deux", "témoin"]:
        d = etudiees[etudiees["groupe"] == gr]
        lignes.append((f"  {gr}", len(d), int(d["publies"].sum()), int(d["supprimes"].sum())))
    sel = pd.DataFrame(lignes, columns=["etape", "fiches", "avis_publies", "avis_supprimes"])
    sel["supprimes_pour_100"] = (100 * sel["avis_supprimes"] / sel["avis_publies"]).round(1)
    return pd.concat([etudiees, ens]), sel


def comparaison(etudiees: pd.DataFrame) -> pd.DataFrame:
    """Témoins pondérés pour reproduire, strate par strate, la répartition des fiches touchées."""
    d = etudiees[etudiees["groupe"].isin(["touchée", "témoin"])].copy()
    d["quart_volume"] = pd.qcut(etudiees["log2_volume"], 4, labels=False).loc[d.index]
    d["strate"] = d["region"] + "|" + d["industry"] + "|" + d["quart_volume"].astype(str)
    n = d.groupby(["strate", "groupe"]).size().unstack(fill_value=0)
    communes = n[(n.get("touchée", 0) > 0) & (n.get("témoin", 0) > 0)].index
    t_total = int((d["groupe"] == "touchée").sum())
    t_gardees = int(n.loc[communes, "touchée"].sum())
    print(f"\nappariement : {t_gardees} fiches touchées sur {t_total} ont des témoins dans leur strate "
          f"({len(communes)} strates, {int(n.loc[communes, 'témoin'].sum())} témoins)")
    d = d[d["strate"].isin(communes)].copy()
    d["poids"] = 1.0
    temoin = d["groupe"] == "témoin"
    d.loc[temoin, "poids"] = d.loc[temoin, "strate"].map(n.loc[communes, "touchée"] / n.loc[communes, "témoin"])

    lignes = []
    for var in list(DESCRIPTIFS) + ["au_moins_un_pic"] + [v for v in INDICATEURS if v != "log2_intensite"]:
        libelle = (DESCRIPTIFS.get(var) or AUTRES.get(var) or INDICATEURS[var][0]).replace("\n", " ")
        famille = "Volume et sollicitation" if var in DESCRIPTIFS and var != "delai_reponse_j" else (
            "Propriétaire" if var == "delai_reponse_j" else "Sollicitation" if var in AUTRES else INDICATEURS[var][1])
        ligne = {"indicateur": var, "libelle": libelle, "famille": famille}
        for gr, cle in [("touchée", "touchees"), ("témoin", "temoins")]:
            x = d[d["groupe"] == gr]
            ok = x[var].notna()
            if var in ("volume_semaine", "intensite", "delai_reponse_j"):
                # Médiane pondérée : ces grandeurs ont des valeurs extrêmes.
                v, w = x.loc[ok, var].to_numpy(), x.loc[ok, "poids"].to_numpy()
                o = np.argsort(v)
                ligne[cle] = float(v[o][np.searchsorted(np.cumsum(w[o]), w.sum() / 2)]) if len(v) else np.nan
                ligne["statistique"] = "médiane"
            else:
                ligne[cle] = float(np.average(x.loc[ok, var], weights=x.loc[ok, "poids"])) if ok.any() else np.nan
                ligne["statistique"] = ("part des fiches" if var in AUTRES or INDICATEURS[var][2] == "oui / non"
                                        else "nombre moyen" if var == "jours_pic" else "moyenne des fiches")
            ligne[f"fiches_{cle}"] = int(ok.sum())
        lignes.append(ligne)
    return pd.DataFrame(lignes)


def modele(etudiees: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    d = etudiees[(etudiees["groupe"] != "six enseignes") & (etudiees["n_hist"] >= MIN_HISTORIQUE)].copy()
    variables = list(INDICATEURS)
    d = d.dropna(subset=variables)
    print(f"\nmodèle : {len(d)} fiches (au moins {MIN_HISTORIQUE} avis l'année précédente), "
          f"{int(d['publies'].sum())} avis, {int(d['supprimes'].sum())} supprimés")
    X = d[variables].astype(float).copy()
    for v, (_, _, unite) in INDICATEURS.items():
        if unite == "+10 points":
            X[v] = X[v] * 10  # un point de X = 10 points de part
    controles = [pd.get_dummies(d["region"], dtype=float).drop(columns="Europe").rename(columns={"US": "region_US"}),
                 pd.get_dummies(d["industry"], prefix="industry", dtype=float).drop(columns="industry_automotive"),
                 pd.get_dummies(d["bucket"], prefix="bucket", dtype=float).drop(columns="bucket_mono"),
                 d[["log2_volume"]]]
    X = sm.add_constant(pd.concat([X] + controles, axis=1), has_constant="add")
    X = X.loc[:, X.std() > 0].assign(const=1.0)
    y = np.column_stack([d["supprimes"], d["publies"] - d["supprimes"]])
    # Marges robustes (sandwich) : l'échelle de Pearson est sous 1, la diviser rétrécirait les marges.
    res = sm.GLM(y, X, family=sm.families.Binomial()).fit(cov_type="HC0")
    print(f"  échelle de Pearson : {res.pearson_chi2 / res.df_resid:.2f} (non utilisée)")
    ic = res.conf_int()
    rr = pd.DataFrame({"parametre": res.params.index,
                       "rapport_de_cotes": np.exp(res.params.values),
                       "borne_basse": np.exp(ic[0].values), "borne_haute": np.exp(ic[1].values),
                       "p_value": res.pvalues.values})
    rr["role"] = np.where(rr["parametre"].isin(variables), "indicateur",
                          np.where(rr["parametre"] == "const", "constante", "contrôle"))
    rr["lecture"] = rr["parametre"].map(lambda v: INDICATEURS.get(v, ("", "", ""))[2])
    rr["fiches"], rr["avis"], rr["supprimes"] = len(d), int(d["publies"].sum()), int(d["supprimes"].sum())
    return rr, d


def virgule(x: float, nd: int = 2) -> str:
    return f"{x:.{nd}f}".replace(".", ",")


def figure_comparaison(comp: pd.DataFrame, n_t: int, n_c: int, chemin: Path) -> None:
    """Pour chaque part, deux points sur la même échelle (0 à 100 %) : touchées et témoins."""
    c = comp[comp["statistique"].isin(["moyenne des fiches", "part des fiches"])].copy()
    c.loc[c["statistique"] == "part des fiches", "libelle"] += " (part des fiches)"
    c = c.iloc[::-1].reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(9, 0.5 * len(c) + 1.9), dpi=150)
    fig.patch.set_facecolor(FOND)
    ax.set_facecolor(FOND)
    familles_vues = []
    for i, r in c.iterrows():
        t, w = 100 * r["touchees"], 100 * r["temoins"]
        ax.plot([min(t, w), max(t, w)], [i, i], color=GRILLE, lw=2, zorder=1, solid_capstyle="round")
        ax.plot(w, i, "o", ms=8, color=ORANGE, mec=FOND, mew=2, zorder=3)
        ax.plot(t, i, "o", ms=8, color=BLEU, mec=FOND, mew=2, zorder=3)
        gauche, droite = (t, w) if t < w else (w, t)
        ax.annotate(f"{virgule(gauche, 0)} %", (gauche, i), xytext=(-8, 0), textcoords="offset points",
                    ha="right", va="center", fontsize=7.5, color=ENCRE_2)
        ax.annotate(f"{virgule(droite, 0)} %", (droite, i), xytext=(8, 0), textcoords="offset points",
                    ha="left", va="center", fontsize=7.5, color=ENCRE_2)
        familles_vues.append(r["famille"])
    ax.set_yticks(range(len(c)))
    ax.set_yticklabels([textwrap.fill(r["libelle"], 38) for _, r in c.iterrows()], fontsize=8.5, color=ENCRE)
    ax.set_xlim(-8, 108)
    ax.xaxis.set_major_locator(FixedLocator([0, 25, 50, 75, 100]))
    ax.set_xticklabels(["0 %", "25 %", "50 %", "75 %", "100 %"])
    ax.grid(axis="x", color=GRILLE, lw=0.8, zorder=0)
    ax.tick_params(colors=ENCRE_2, labelsize=8, length=0)
    for cote in ["top", "right", "left"]:
        ax.spines[cote].set_visible(False)
    ax.spines["bottom"].set_color(GRILLE)
    ax.set_ylim(-0.6, len(c) - 0.4)
    h = 0.5 * len(c) + 1.9
    fig.text(0.01, 1 - 0.12 / h, "Fiches qui perdent beaucoup de nouveaux avis, face à des fiches semblables qui n'en perdent aucun",
             va="top", fontsize=11, color=ENCRE)
    legende = [Line2D([0], [0], marker="o", color="none", mfc=BLEU, mec=BLEU, ms=8,
                      label=f"fiches touchées ({n_t})"),
               Line2D([0], [0], marker="o", color="none", mfc=ORANGE, mec=ORANGE, ms=8,
                      label=f"fiches témoins ({n_c}), pondérées")]
    fig.legend(handles=legende, loc="upper left", bbox_to_anchor=(0.005, 1 - 0.38 / h),
               frameon=False, fontsize=8, labelcolor=ENCRE, ncol=2, handlelength=1.2)
    fig.text(0.01, 0.08 / h,
             f"Données : corpus 03C (03C_7_17_aout_prenom.parquet), avis 4-5 étoiles publiés du 11 au 17 août 2026, suivis 7 jours.\n"
             f"Fiches avec au moins {MIN_PUBLIES} avis publiés, {PERIMETRE}. "
             f"Touchées : au moins {MIN_SUPPRIMES} avis et {int(100 * MIN_TAUX)} % des avis supprimés.\n"
             "Témoins : aucun avis supprimé, même région, même secteur et même quart de volume habituel "
             "(pondérés pour avoir la même répartition que les touchées).\n"
             "Chaque point : moyenne des parts de chaque fiche, ou part des fiches concernées. "
             "Propriétaire : année précédant le 11 août.",
             fontsize=6.8, color=ENCRE_2, va="bottom")
    fig.subplots_adjust(left=0.33, right=0.97, top=1 - 0.75 / h, bottom=1.0 / h)
    fig.savefig(chemin, facecolor=FOND)
    plt.close(fig)


def figure_modele(rr: pd.DataFrame, chemin: Path) -> None:
    t = rr[rr["role"] == "indicateur"].set_index("parametre")
    pos, entetes, y = {}, [], 0.0
    familles = []
    for v, (lib, fam, unite) in INDICATEURS.items():
        if fam not in familles:
            familles.append(fam)
            entetes.append((y, fam))
            y += 0.85
        pos[v] = (y, f"{lib}  ({unite})")
        y += 1
        if v in ("part_jour_max", "auteur_ailleurs", "texte_double"):
            y += 0.35
    hauteur = y
    h = 0.36 * hauteur + 1.9
    x_min, x_max = 0.125, 32
    fig, ax = plt.subplots(figsize=(8.5, h), dpi=150)
    fig.patch.set_facecolor(FOND)
    ax.set_facecolor(FOND)
    ax.axvline(1, color=ENCRE_2, lw=1, zorder=1)
    for v, (yi, _) in pos.items():
        r = t.loc[v]
        net = r["p_value"] < 0.05
        bas, haut = max(r["borne_basse"], x_min), min(r["borne_haute"], x_max)
        ax.plot([bas, haut], [yi, yi], color=BLEU, lw=2, solid_capstyle="round", zorder=2)
        for borne, limite, sens in [(r["borne_basse"], x_min, "<"), (r["borne_haute"], x_max, ">")]:
            if (sens == "<" and borne < limite) or (sens == ">" and borne > limite):
                ax.plot(limite, yi, marker=sens, color=BLEU, ms=6, zorder=2)
        ax.plot(r["rapport_de_cotes"], yi, "o", ms=7, mew=2, zorder=3, mec=BLEU, mfc=BLEU if net else FOND)
        ax.annotate(virgule(r["rapport_de_cotes"]), (r["rapport_de_cotes"], yi), xytext=(0, 6),
                    textcoords="offset points", ha="center", fontsize=7.5, color=ENCRE,
                    fontweight="bold" if net else "normal")
    for ye, _ in entetes[1:]:
        ax.axhline(ye - 0.3, color=GRILLE, lw=0.8, zorder=0)
    ax.set_xscale("log")
    ax.set_xlim(x_min, x_max)
    grad = [0.125, 0.25, 0.5, 1, 2, 4, 8, 16, 32]
    ax.xaxis.set_major_locator(FixedLocator(grad))
    ax.xaxis.set_minor_locator(NullLocator())
    ax.set_xticklabels([f"{g:g}".replace(".", ",") for g in grad])
    ax.grid(axis="x", color=GRILLE, lw=0.8, zorder=0)
    ax.tick_params(colors=ENCRE_2, labelsize=7.5, length=0)
    for cote in ["top", "right", "left"]:
        ax.spines[cote].set_visible(False)
    ax.spines["bottom"].set_color(GRILLE)
    ax.set_ylim(hauteur - 0.2, -0.5)
    ax.set_yticks([yi for yi, _ in pos.values()])
    ax.set_yticklabels([n for _, n in pos.values()], fontsize=8, color=ENCRE)
    from matplotlib.transforms import blended_transform_factory
    bord = blended_transform_factory(fig.transFigure, ax.transData)
    for ye, fam in entetes:
        ax.text(0.01, ye, fam, transform=bord, ha="left", va="center", fontsize=8.5,
                color=ENCRE_2, fontweight="bold")
    ax.set_xlabel("risque qu'un nouvel avis de la fiche soit supprimé (1 = pas d'effet)", color=ENCRE_2, fontsize=8)
    n_f, n_a, n_s = int(rr["fiches"].iloc[0]), int(rr["avis"].iloc[0]), int(rr["supprimes"].iloc[0])
    fig.text(0.01, 1 - 0.12 / h, "Ce qui distingue les fiches qui perdent leurs nouveaux avis : tous les indicateurs ensemble",
             va="top", fontsize=11, color=ENCRE)
    fig.text(0.01, 1 - 0.42 / h, f"{n_f} fiches, " + f"{n_a:,}".replace(",", " ") + f" avis, {n_s} supprimés",
             va="top", fontsize=8, color=ENCRE_2)
    legende = [Line2D([0], [0], marker="o", color=BLEU, mfc=BLEU, ms=7, lw=2, label="significatif (p < 0,05)"),
               Line2D([0], [0], marker="o", color=BLEU, mfc=FOND, ms=7, mew=2, lw=2, label="non significatif")]
    fig.legend(handles=legende, loc="upper left", bbox_to_anchor=(0.005, 1 - 0.6 / h),
               frameon=False, fontsize=8, labelcolor=ENCRE, ncol=2, handlelength=2)
    fig.text(0.01, 0.08 / h,
             "Données : corpus 03C (03C_7_17_aout_prenom.parquet), avis 4-5 étoiles publiés du 11 au 17 août 2026, suivis 7 jours. "
             f"Fiches avec au moins {MIN_PUBLIES} avis publiés\net au moins {MIN_HISTORIQUE} "
             f"avis l'année précédente, {PERIMETRE}. Un seul modèle (avis supprimés sur avis publiés, par fiche), "
             "à région, secteur, taille\net volume habituel égaux ; marges d'incertitude robustes. "
             "Entre parenthèses : l'écart auquel se lit chaque rapport.",
             fontsize=6.8, color=ENCRE_2, va="bottom")
    fig.subplots_adjust(left=0.42, right=0.97, top=1 - 1.0 / h, bottom=1.05 / h)
    fig.savefig(chemin, facecolor=FOND)
    plt.close(fig)


def main() -> None:
    con = connexion("4GB")
    avis, fiches = charger(con)
    f = indicateurs(avis, fiches)
    etudiees, sel = selection(f)
    print("\n== Sélection ==\n" + sel.to_string(index=False))

    SORTIE.mkdir(parents=True, exist_ok=True)
    colonnes = (["cid", "name", "region", "industry", "bucket", "enseigne", "groupe", "publies", "supprimes",
                 "taux_suppression", "volume_semaine", "intensite", "n_hist", "delai_reponse_j"]
                + [v for v in INDICATEURS if v != "log2_intensite"] + ["part_auteur_ailleurs", "part_texte_double", "au_moins_un_pic"])
    etudiees[colonnes].sort_values(["groupe", "taux_suppression"], ascending=[True, False]).to_csv(
        SORTIE / "fiches_indicateurs.csv", index=False)
    sel.to_csv(SORTIE / "selection_fiches.csv", index=False)

    touchees = etudiees[etudiees["groupe"] == "touchée"]
    print(f"\nfiches touchées des chaînes antiparasitaires : {int(touchees['enseigne'].sum())} sur {len(touchees)}")
    print("\nfiches touchées par région :\n" + touchees["region"].value_counts().to_string())
    print("\nfiches touchées par secteur :\n" + touchees["industry"].value_counts().to_string())

    comp = comparaison(etudiees[etudiees["groupe"] != "six enseignes"])
    comp.to_csv(SORTIE / "comparaison_touchees_temoins.csv", index=False)
    print("\n== Comparaison (témoins pondérés) ==\n"
          + comp[["libelle", "statistique", "touchees", "temoins", "fiches_touchees", "fiches_temoins"]]
          .round(3).to_string(index=False))
    figure_comparaison(comp, int(comp["fiches_touchees"].max()), int(comp["fiches_temoins"].max()),
                       SORTIE / "comparaison_touchees_temoins.png")

    rr, _ = modele(etudiees)
    rr.to_csv(SORTIE / "modele_fiche.csv", index=False)
    fmt = {c: "{:.2f}".format for c in ["rapport_de_cotes", "borne_basse", "borne_haute"]}
    fmt["p_value"] = "{:.3f}".format
    print("\n== Modèle ==\n" + rr[["parametre", "role", "lecture", "rapport_de_cotes", "borne_basse",
                                    "borne_haute", "p_value"]].to_string(index=False, formatters=fmt))
    figure_modele(rr, SORTIE / "modele_fiche.png")

    ens = etudiees[etudiees["groupe"] == "six enseignes"]
    print(f"\nsix enseignes : {len(ens)} fiches, {int(ens['publies'].sum())} avis, "
          f"{int(ens['supprimes'].sum())} supprimés")
    print(f"\nécrit dans {SORTIE}")


if __name__ == "__main__":
    main()
