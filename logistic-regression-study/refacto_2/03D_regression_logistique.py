"""Régression logistique sur le panel 03D, une ligne par avis.

    uv run python logistic-regression-study/refacto_2/03D_regression_logistique.py

LA QUESTION
  À caractéristiques égales, quelles caractéristiques d'un avis publié du 6 au
  17 août 2026 font varier son risque d'être supprimé avant le 24 août ?

LES DONNÉES
  Table `reviews_panel_features_03D`, construite par `03D_adding_features.bqsql`.
  30 628 avis, 1 191 supprimés.

LES RÉFÉRENCES (décidées par Romain le 2026-09-30)
  note                        3 étoiles
  pic sur la fiche ce jour    pas de pic
  niveau Local Guide          sans niveau
  photo dans l'avis           sans photo
  texte                       sans texte
  photos publiées par l'auteur 0
  avis publiés par l'auteur   1 avis ou moins (proposé, pas encore validé)
  réponse du propriétaire     n'a pas répondu
  secteur                     automobile
  taille                      mono
  taux de réponse de la fiche le taux médian des avis du panel

LECTURE
  « ×2,00 » : à autres caractéristiques égales, l'avis de cette case disparaît
  2 fois plus que l'avis de la case de référence. Pour le taux de réponse de
  la fiche, l'effet se lit pour 10 points de plus. La fourchette tient compte
  de ce que les avis d'une même fiche se ressemblent.

Produit, dans `sorties/` à côté de ce fichier :
  03D_effectifs.csv   avis, suppressions et fiches touchées par case, par passage
  03D_effets.csv      risque relatif et fourchette, par passage
  figures/03D_effets.png, 03D_effets_US.png, 03D_effets_EU.png
"""
import os
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

PROJET = "client-divers"
TABLE = "client-divers.reviewflowz.reviews_panel_features_03D"
SORTIES = Path(__file__).resolve().parent / "sorties"
DOSSIER_CLES = Path.home() / ".gcp"

# ---------------------------------------------------------------------------
# Découpages. Les seuils marqués « proposé » restent à valider par Romain.
# ---------------------------------------------------------------------------
# Pic : proposé. L'avis tombe un jour où la fiche reçoit au moins 2 avis, et
# plus de 3 fois son rythme habituel de l'année d'avant.
PIC_MIN_AVIS = 2
PIC_MIN_RATIO = 3
# Longueur du texte, en caractères : tranches du point 2.3.
TEXTE = [(1, 50, "1 à 50 caractères"), (51, 200, "51 à 200 caractères"),
         (201, None, "plus de 200 caractères")]
# Photos publiées par l'auteur : tranches du plan du point 6.
PHOTOS_AUTEUR = [(1, 20, "1 à 20 photos"), (21, None, "plus de 20 photos")]
# Avis publiés par l'auteur : tranches du plan du point 6. La référence
# « 1 avis ou moins » comprend les profils affichés à 0.
AVIS_AUTEUR = [(2, 20, "2 à 20 avis"), (21, None, "plus de 20 avis")]
# Une case qui compte moins de suppressions que ce seuil sort du passage,
# avec ses avis : son effet ne se mesure pas. Même garde-fou qu'au point 5.
MIN_SUPPRESSIONS = 5

SECTEURS = {"automotive": "automobile", "home_services": "services à domicile",
            "healthcare": "santé", "wellness_fitness": "sport et bien-être",
            "food_beverage": "restauration", "travel": "voyage", "hospitality": "hôtellerie"}

# (région, périmètre). L'Europe n'a aucune enseigne signalée dans ce panel :
# son passage « sans enseignes » serait identique, il n'est pas refait.
PASSAGES = [("US", "tous"), ("US", "sans_enseignes"), ("EU", "tous"),
            ("ensemble", "tous"), ("ensemble", "sans_enseignes")]


def client():
    """Le client BigQuery, avec la clé de service de `~/.gcp/`, comme `consolidation/commun.py`."""
    if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") and DOSSIER_CLES.is_dir():
        cles = sorted(DOSSIER_CLES.glob("*.json"))
        if len(cles) > 1:
            raise SystemExit(f"{len(cles)} clés dans {DOSSIER_CLES}, en garder une.")
        if cles:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(cles[0])
    from google.cloud import bigquery
    return bigquery.Client(project=PROJET, location="EU")


def tranche(valeurs, tranches, defaut):
    """Range chaque valeur dans sa tranche (bornes comprises) ; `defaut` hors tranches."""
    conditions = [(valeurs >= bas) & (valeurs <= haut if haut is not None else True)
                  for bas, haut, _ in tranches]
    return np.select(conditions, [nom for _, _, nom in tranches], defaut)


# ---------------------------------------------------------------------------
# Lecture et découpages
# ---------------------------------------------------------------------------
d0 = client().query(f"""
    SELECT review_id, cid, supprime, star, has_photo, text_chars, palier_local_guide,
           reviewer_photo_count, reviewer_review_count, a_repondu, taux_reponse_fiche,
           secteur, bucket, region, enseigne_signalee, n_avis_meme_jour_fiche, ratio_pic_fiche
    FROM `{TABLE}`
""").to_dataframe()
print(f"  {len(d0)} avis, {int(d0['supprime'].sum())} suppressions")

d0["y"] = d0["supprime"].astype(int)
d0["note"] = d0["star"].astype(int).astype(str) + " étoile(s)"
d0["pic"] = np.where((d0["n_avis_meme_jour_fiche"] >= PIC_MIN_AVIS)
                     & (d0["ratio_pic_fiche"] > PIC_MIN_RATIO), "pic", "pas de pic")
d0["local_guide"] = d0["palier_local_guide"].map(
    {"sans_niveau": "sans niveau", "1_4": "niveau 1 à 4", "5_et_plus": "niveau 5 et plus"})
d0["photo_avis"] = np.where(d0["has_photo"], "avec photo", "sans photo")
d0["texte"] = tranche(d0["text_chars"], TEXTE, "sans texte")
d0["photos_auteur"] = tranche(d0["reviewer_photo_count"], PHOTOS_AUTEUR, "0 photo")
d0["avis_auteur"] = tranche(d0["reviewer_review_count"], AVIS_AUTEUR, "1 avis ou moins")
# Réponse sans son délai, décision de Romain du 2026-09-30.
d0["reponse"] = np.where(d0["a_repondu"], "a répondu", "n'a pas répondu")
d0["secteur_fr"] = d0["secteur"].map(SECTEURS).fillna(d0["secteur"])
d0["taille"] = d0["bucket"]

# Taux de réponse de la fiche : écart au taux médian, en dizaines de points.
# Médiane prise sur les avis du panel entier, la même pour tous les passages.
MEDIANE_TAUX = float(d0["taux_reponse_fiche"].median())
d0["taux_reponse_10pts"] = 10 * (d0["taux_reponse_fiche"] - MEDIANE_TAUX)
print(f"  taux de réponse médian des fiches, sur les avis du panel : {100 * MEDIANE_TAUX:.0f} %")

# Chaque caractéristique découpée, avec sa case de référence en premier.
CARACTERISTIQUES = {
    "note": ["3 étoile(s)", "1 étoile(s)", "2 étoile(s)", "4 étoile(s)", "5 étoile(s)"],
    "pic": ["pas de pic", "pic"],
    "local_guide": ["sans niveau", "niveau 1 à 4", "niveau 5 et plus"],
    "photo_avis": ["sans photo", "avec photo"],
    "texte": ["sans texte"] + [nom for _, _, nom in TEXTE],
    "photos_auteur": ["0 photo"] + [nom for _, _, nom in PHOTOS_AUTEUR],
    "avis_auteur": ["1 avis ou moins"] + [nom for _, _, nom in AVIS_AUTEUR],
    "reponse": ["n'a pas répondu", "a répondu"],
    "secteur_fr": ["automobile"] + [s for s in SECTEURS.values() if s != "automobile"],
    "taille": ["mono", "small", "large"],
}


def selection(region, perimetre):
    d = d0 if region == "ensemble" else d0[d0["region"] == region]
    return d if perimetre == "tous" else d[~d["enseigne_signalee"]]


def effectifs(d):
    touchees = d[d["y"] == 1]
    return {"avis": len(d), "suppressions": len(touchees), "fiches_touchees": touchees["cid"].nunique()}


# ---------------------------------------------------------------------------
# Un modèle par passage
# ---------------------------------------------------------------------------
lignes_effectifs, lignes_effets = [], []
modele_par_passage = {}  # avis et suppressions entrés dans chaque modèle
for region, perimetre in PASSAGES:
    passage = f"{region}, {perimetre}"
    d = selection(region, perimetre)
    lignes_effectifs.append({"passage": passage, "caracteristique": "total", "case": "",
                             **effectifs(d)})

    # Effectifs de chaque case, puis retrait des cases trop maigres.
    ecartees = []
    for carac, cases in CARACTERISTIQUES.items():
        for case in cases:
            e = effectifs(d[d[carac] == case])
            lignes_effectifs.append({"passage": passage, "caracteristique": carac, "case": case, **e})
            if case != cases[0] and e["avis"] > 0 and e["suppressions"] < MIN_SUPPRESSIONS:
                ecartees.append((carac, case, e))
    for carac, case, _ in ecartees:
        d = d[d[carac] != case]

    X = pd.DataFrame(index=d.index)
    for carac, cases in CARACTERISTIQUES.items():
        for case in cases[1:]:
            if (d[carac] == case).any():
                X[f"{carac} : {case}"] = (d[carac] == case).astype(float)
    X["taux_reponse_fiche : +10 points"] = d["taux_reponse_10pts"]
    if region == "ensemble":
        X["region : US"] = (d["region"] == "US").astype(float)
    X = sm.add_constant(X)

    modele = sm.GLM(d["y"], X, family=sm.families.Binomial()).fit(
        cov_type="cluster", cov_kwds={"groups": pd.factorize(d["cid"])[0]})
    converge = bool(modele.converged)
    modele_par_passage[passage] = (len(d), int(d["y"].sum()))
    marges = modele.conf_int()
    print(f"  {passage} : {len(d)} avis, {int(d['y'].sum())} suppressions, "
          f"{d['cid'].nunique()} fiches, converge : {converge}")

    for col in X.columns.drop("const"):
        lignes_effets.append({
            "passage": passage, "colonne": col,
            "risque_relatif": round(float(np.exp(modele.params[col])), 2),
            "fourchette_basse": round(float(np.exp(marges.loc[col, 0])), 2),
            "fourchette_haute": round(float(np.exp(marges.loc[col, 1])), 2),
            "converge": converge, "remarque": ""})
    for carac, case, e in ecartees:
        lignes_effets.append({"passage": passage, "colonne": f"{carac} : {case}",
                              "converge": converge,
                              "remarque": f"écartée : {e['suppressions']} suppressions sur {e['avis']} avis"})

SORTIES.mkdir(parents=True, exist_ok=True)
# Point-virgule et virgule décimale : Sheets en français les lit tels quels.
pd.DataFrame(lignes_effectifs).to_csv(SORTIES / "03D_effectifs.csv", sep=";", decimal=",", index=False)
effets = pd.DataFrame(lignes_effets)
effets.to_csv(SORTIES / "03D_effets.csv", sep=";", decimal=",", index=False)
print(f"  {SORTIES / '03D_effectifs.csv'}\n  {SORTIES / '03D_effets.csv'}")

# ---------------------------------------------------------------------------
# Graphiques : passages « ensemble », « US » et « EU », toutes les fiches.
# Chaque groupe commence par sa référence, posée sur ×1. La région, simple
# contrôle du passage « ensemble », n'y figure pas.
# ---------------------------------------------------------------------------
import matplotlib

matplotlib.use("Agg")  # pas d'écran sous WSL
import matplotlib.pyplot as plt
import matplotlib.transforms
from matplotlib.ticker import FuncFormatter, NullFormatter

# (passage, fichier, fin du titre, périmètre écrit dans le sous-titre)
GRAPHIQUES = [("ensemble, tous", "03D_effets.png", "", "toutes les fiches"),
              ("US, tous", "03D_effets_US.png", ", États-Unis",
               "fiches des États-Unis, chaînes comprises"),
              ("EU, tous", "03D_effets_EU.png", ", Europe", "fiches d'Europe")]
BLEU, GRIS, ENCRE, FOND = "#2a78d6", "#8a8984", "#0b0b0b", "#fcfcfb"
TITRES = {"note": "Note", "pic": "Pic d'avis sur la fiche le jour du dépôt",
          "local_guide": "Niveau Local Guide", "photo_avis": "Photo dans l'avis",
          "texte": "Longueur du texte", "photos_auteur": "Photos publiées par l'auteur",
          "avis_auteur": "Avis publiés par l'auteur", "reponse": "Réponse du propriétaire",
          "taux": "Taux de réponse de la fiche", "secteur_fr": "Secteur", "taille": "Taille de l'entreprise"}


def libelle(case):
    return case.replace("1 étoile(s)", "1 étoile").replace("étoile(s)", "étoiles")


groupes = [(carac, cases[0], [f"{carac} : {c}" for c in cases[1:]])
           for carac, cases in CARACTERISTIQUES.items()]
groupes.insert(8, ("taux", f"taux médian ({100 * MEDIANE_TAUX:.0f} %)".replace(".", ","),
                   ["taux_reponse_fiche : +10 points"]))


def graphique(passage, fichier, fin_titre, perimetre):
    e = effets[effets["passage"] == passage].set_index("colonne")
    # Une ligne par titre de groupe, par référence et par case.
    lignes = []
    for carac, reference, colonnes in groupes:
        lignes.append(("titre", TITRES[carac], None))
        lignes.append(("reference", f"{libelle(reference)} (référence)", None))
        for col in colonnes:
            if col in e.index:
                nom = "10 points de plus" if carac == "taux" else libelle(col.split(" : ", 1)[1])
                lignes.append(("case", nom, e.loc[col]))

    fig, ax = plt.subplots(figsize=(10, 0.28 * len(lignes) + 1.6), facecolor=FOND)
    ax.set_facecolor(FOND)
    X_MIN, X_MAX = 0.1, 10
    # Libellés à gauche du graphique : x en fraction de largeur, y en lignes.
    gauche = matplotlib.transforms.blended_transform_factory(ax.transAxes, ax.transData)
    for y, (sorte, nom, r) in enumerate(lignes):
        if sorte == "titre":
            ax.text(-0.42, y, nom, transform=gauche, fontweight="bold", va="center", ha="left",
                    fontsize=9.5, color=ENCRE)
            continue
        ax.text(-0.01, y, nom, transform=gauche, va="center", ha="right", fontsize=9, color=ENCRE)
        if sorte == "reference":
            ax.scatter(1, y, s=36, facecolor=FOND, edgecolor=GRIS, linewidth=1.5, zorder=3)
        elif pd.notna(r["risque_relatif"]):
            rr, bas, haut = r["risque_relatif"], r["fourchette_basse"], r["fourchette_haute"]
            ax.plot([max(bas, X_MIN), min(haut, X_MAX)], [y, y], color=BLEU, linewidth=2, zorder=2)
            ax.scatter(rr, y, s=36, color=BLEU, zorder=3)
            ax.text(X_MAX * 1.05, y, f"×{rr:.2f}  [{bas:.2f} – {haut:.2f}]".replace(".", ","),
                    va="center", ha="left", fontsize=8, color=GRIS)
        else:
            ax.text(1.08, y, r["remarque"], va="center", ha="left", fontsize=8, color=GRIS, style="italic")

    ax.axvline(1, color=ENCRE, linewidth=1.2, zorder=1)
    ax.set_xscale("log")
    ax.set_xlim(X_MIN, X_MAX)
    ax.set_xticks([0.1, 0.2, 0.5, 1, 2, 5, 10])
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"×{v:g}".replace(".", ",")))
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.set_ylim(len(lignes) - 0.5, -2.2)
    ax.set_yticks([])
    ax.grid(axis="x", color="#e4e3df", linewidth=0.6)
    for cote in ["top", "right", "left"]:
        ax.spines[cote].set_visible(False)
    ax.tick_params(axis="x", colors=GRIS, labelsize=9)

    # Les deux sens de lecture, au-dessus du graphique.
    ax.annotate("", xy=(0.35, -1.6), xytext=(0.93, -1.6), arrowprops=dict(arrowstyle="->", color=GRIS))
    ax.text(0.9, -1.6, "disparaît moins souvent\nque la référence", ha="right", va="bottom",
            fontsize=9, color=ENCRE)
    ax.annotate("", xy=(2.85, -1.6), xytext=(1.07, -1.6), arrowprops=dict(arrowstyle="->", color=GRIS))
    ax.text(1.1, -1.6, "disparaît plus souvent\nque la référence", ha="left", va="bottom",
            fontsize=9, color=ENCRE)

    n_avis, n_suppr = (f"{n:,}".replace(",", " ") for n in modele_par_passage[passage])
    fig.suptitle(f"Risque de suppression d'un avis face à la référence de son groupe{fin_titre}",
                 x=0.02, ha="left", fontsize=12, color=ENCRE)
    fig.text(0.02, 0.965 - 0.3 / fig.get_figheight(),
             f"{n_avis} avis publiés du 6 au 17 août 2026 et entrés dans le modèle, dont {n_suppr} supprimés, {perimetre}. "
             "Point : risque relatif. Trait : fourchette à 95 %.\n"
             f"Les autres caractéristiques{', et la région,' if passage.startswith('ensemble') else ''} sont tenues égales.",
             ha="left", va="top", fontsize=8.5, color=GRIS)
    fig.tight_layout(rect=(0, 0, 0.93, 1 - 0.9 / fig.get_figheight()))
    (SORTIES / "figures").mkdir(exist_ok=True)
    fig.savefig(SORTIES / "figures" / fichier, dpi=130, facecolor=FOND, bbox_inches="tight")
    plt.close(fig)
    print(f"  {SORTIES / 'figures' / fichier}")


for passage, fichier, fin_titre, perimetre in GRAPHIQUES:
    graphique(passage, fichier, fin_titre, perimetre)
