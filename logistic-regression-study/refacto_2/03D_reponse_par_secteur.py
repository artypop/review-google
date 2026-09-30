"""Effet de la réponse du propriétaire, par secteur et par note, panel 03D.

    uv run python logistic-regression-study/refacto_2/03D_reponse_par_secteur.py

LA QUESTION
  Dans chaque secteur, quel est le rapport entre le taux de suppression des
  avis avec réponse et celui des avis sans réponse, toutes les autres
  caractéristiques égales ?

LE MONTAGE
  Le modèle de `03D_regression_logistique.py`, passage « ensemble » (États-Unis
  et Europe), avec les mêmes colonnes et les mêmes références. Seule la réponse
  change : une colonne « a répondu » par secteur. Chacune compare l'avis
  répondu à l'avis sans réponse du même secteur.

  La barre « tous secteurs » vient du modèle à une seule colonne de réponse,
  celui de `03D_regression_logistique.py`.

LECTURE
  « 0,46 » : dans ce secteur, le taux de suppression des avis avec réponse vaut
  0,46 fois celui des avis sans réponse. 1 : pas d'effet. Au-dessus de 1 :
  l'avis répondu disparaît plus. La fourchette tient compte de ce que les avis
  d'une même fiche se ressemblent.

  Le CSV donne aussi le rapport direct des deux taux, sans rien tenir égal.

Produit, dans `sorties/` à côté de ce fichier :
  03D_reponse_par_secteur.csv   effets et effectifs, toutes les fiches et sans les chaînes
  figures/03D_reponse_par_secteur.png          autres caractéristiques égales, toutes les fiches
  figures/03D_reponse_par_secteur_direct.png   rapport direct, toutes les fiches
  03D_reponse_par_note.csv      rapport direct par note, toutes les fiches et sans les chaînes
  figures/03D_reponse_par_note_direct.png      rapport direct, toutes les fiches
  figures/03D_reponse_par_note_direct_sans_services_a_domicile.png   rapport direct, sans ce secteur
"""
import os
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # pas d'écran sous WSL
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from matplotlib.ticker import FuncFormatter

PROJET = "client-divers"
TABLE = "client-divers.reviewflowz.reviews_panel_features_03D"
SORTIES = Path(__file__).resolve().parent / "sorties"
DOSSIER_CLES = Path.home() / ".gcp"

# Découpages de `03D_regression_logistique.py`.
PIC_MIN_AVIS = 2
PIC_MIN_RATIO = 3
TEXTE = [(1, 50, "1 à 50 caractères"), (51, 200, "51 à 200 caractères"),
         (201, None, "plus de 200 caractères")]
PHOTOS_AUTEUR = [(1, 20, "1 à 20 photos"), (21, None, "plus de 20 photos")]
AVIS_AUTEUR = [(2, 20, "2 à 20 avis"), (21, None, "plus de 20 avis")]
SECTEURS = {"automotive": "automobile", "home_services": "services à domicile",
            "healthcare": "santé", "wellness_fitness": "sport et bien-être",
            "food_beverage": "restauration", "travel": "voyage", "hospitality": "hôtellerie"}
PERIMETRES = {"tous": "toutes les fiches",
              "sans_enseignes": "sans les 4 chaînes antiparasitaires américaines"}
# Par note seulement : un périmètre de plus, sans tout le secteur des services
# à domicile (demande de Romain du 2026-09-30).
PERIMETRES_NOTES = {**PERIMETRES, "sans_services_a_domicile": "sans le secteur des services à domicile"}


def perimetre_de(perimetre):
    """Les avis d'un périmètre."""
    if perimetre == "sans_enseignes":
        return d0[~d0["enseigne_signalee"]]
    if perimetre == "sans_services_a_domicile":
        return d0[d0["secteur"] != "home_services"]
    return d0


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
# Lecture et découpages, comme dans `03D_regression_logistique.py`
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
d0["secteur_fr"] = d0["secteur"].map(SECTEURS).fillna(d0["secteur"])
d0["taille"] = d0["bucket"]
MEDIANE_TAUX = float(d0["taux_reponse_fiche"].median())
d0["taux_reponse_10pts"] = 10 * (d0["taux_reponse_fiche"] - MEDIANE_TAUX)

# Colonnes tenues égales, avec leur référence en premier. La réponse et le
# secteur sont traités à part.
CONTROLES = {
    "note": ["3 étoile(s)", "1 étoile(s)", "2 étoile(s)", "4 étoile(s)", "5 étoile(s)"],
    "pic": ["pas de pic", "pic"],
    "local_guide": ["sans niveau", "niveau 1 à 4", "niveau 5 et plus"],
    "photo_avis": ["sans photo", "avec photo"],
    "texte": ["sans texte"] + [nom for _, _, nom in TEXTE],
    "photos_auteur": ["0 photo"] + [nom for _, _, nom in PHOTOS_AUTEUR],
    "avis_auteur": ["1 avis ou moins"] + [nom for _, _, nom in AVIS_AUTEUR],
    "taille": ["mono", "small", "large"],
}
LISTE_SECTEURS = list(SECTEURS.values())


def colonnes(d, reponse_par_secteur):
    """Les colonnes du modèle. La réponse : une par secteur, ou une seule."""
    X = pd.DataFrame(index=d.index)
    for carac, cases in CONTROLES.items():
        for case in cases[1:]:
            if (d[carac] == case).any():
                X[f"{carac} : {case}"] = (d[carac] == case).astype(float)
    for s in LISTE_SECTEURS[1:]:
        X[f"secteur : {s}"] = (d["secteur_fr"] == s).astype(float)
    if reponse_par_secteur:
        for s in LISTE_SECTEURS:
            X[f"a répondu : {s}"] = ((d["secteur_fr"] == s) & d["a_repondu"]).astype(float)
    else:
        X["a répondu : tous secteurs"] = d["a_repondu"].astype(float)
    X["taux_reponse_fiche : +10 points"] = d["taux_reponse_10pts"]
    X["region : US"] = (d["region"] == "US").astype(float)
    return sm.add_constant(X)


def ajuster(d, X):
    return sm.GLM(d["y"], X, family=sm.families.Binomial()).fit(
        cov_type="cluster", cov_kwds={"groups": pd.factorize(d["cid"])[0]})


def effectifs(d):
    touchees = d[d["y"] == 1]
    return len(d), len(touchees), touchees["cid"].nunique()


def rapport_direct(d, colonne=None, groupes=(), total="tous secteurs"):
    """Rapport direct des taux avec et sans réponse, et sa fourchette.

    Le modèle ne contient que le groupe (secteur ou note) et la réponse : son
    multiplicateur redonne exactement le rapport des deux taux comptés à la
    main. Il sert à calculer la fourchette, en tenant compte de ce que les avis
    d'une même fiche se ressemblent. Sans `colonne`, une seule réponse pour
    tous les avis, nommée `total`.
    """
    X = pd.DataFrame(index=d.index)
    if colonne:
        for g in groupes[1:]:
            X[f"{colonne} : {g}"] = (d[colonne] == g).astype(float)
        for g in groupes:
            X[f"a répondu : {g}"] = ((d[colonne] == g) & d["a_repondu"]).astype(float)
    else:
        X[f"a répondu : {total}"] = d["a_repondu"].astype(float)
    return sm.GLM(d["y"], sm.add_constant(X), family=sm.families.Poisson()).fit(
        cov_type="cluster", cov_kwds={"groups": pd.factorize(d["cid"])[0]})


# ---------------------------------------------------------------------------
# Un modèle par périmètre, puis le modèle à une seule colonne de réponse
# ---------------------------------------------------------------------------
lignes = []
for perimetre in PERIMETRES:
    d = d0 if perimetre == "tous" else d0[~d0["enseigne_signalee"]]
    for par_secteur in (True, False):
        modele = ajuster(d, colonnes(d, par_secteur))
        marges = modele.conf_int()
        direct = rapport_direct(d, "secteur_fr", LISTE_SECTEURS) if par_secteur else rapport_direct(d)
        marges_direct = direct.conf_int()
        for s in (LISTE_SECTEURS if par_secteur else ["tous secteurs"]):
            col = f"a répondu : {s}"
            ds = d if s == "tous secteurs" else d[d["secteur_fr"] == s]
            av_r, sup_r, fi_r = effectifs(ds[ds["a_repondu"]])
            av_n, sup_n, fi_n = effectifs(ds[~ds["a_repondu"]])
            rr = float(np.exp(modele.params[col]))
            bas, haut = (float(np.exp(marges.loc[col, k])) for k in (0, 1))
            rd = (sup_r / av_r) / (sup_n / av_n)
            # Contrôle : le modèle réduit redonne le rapport compté à la main.
            assert abs(float(np.exp(direct.params[col])) - rd) < 1e-6, (perimetre, s)
            bas_d, haut_d = (float(np.exp(marges_direct.loc[col, k])) for k in (0, 1))
            lignes.append({
                "perimetre": perimetre, "secteur": s,
                "risque_relatif": round(rr, 2), "fourchette_basse": round(bas, 2),
                "fourchette_haute": round(haut, 2),
                # Rapport direct des deux taux, sans rien tenir égal.
                "taux_repondus_pour_1000": round(1000 * sup_r / av_r, 1),
                "taux_sans_reponse_pour_1000": round(1000 * sup_n / av_n, 1),
                "rapport_direct": round(rd, 2), "rapport_direct_bas": round(bas_d, 2),
                "rapport_direct_haut": round(haut_d, 2),
                "avis_repondus": av_r, "suppressions_repondus": sup_r, "fiches_repondus": fi_r,
                "avis_sans_reponse": av_n, "suppressions_sans_reponse": sup_n, "fiches_sans_reponse": fi_n,
                "converge": bool(modele.converged)})
        print(f"  {perimetre}, {'par secteur' if par_secteur else 'tous secteurs'} : "
              f"{len(d)} avis, {int(d['y'].sum())} suppressions, converge : {modele.converged}")

r = pd.DataFrame(lignes)
SORTIES.mkdir(parents=True, exist_ok=True)
r.to_csv(SORTIES / "03D_reponse_par_secteur.csv", sep=";", decimal=",", index=False)
print(f"  {SORTIES / '03D_reponse_par_secteur.csv'}")

# ---------------------------------------------------------------------------
# Par note : le rapport direct seulement
# ---------------------------------------------------------------------------
LISTE_NOTES = [f"{n} étoile(s)" for n in range(1, 6)]
lignes_notes = []
for perimetre in PERIMETRES_NOTES:
    d = perimetre_de(perimetre)
    for par_note in (True, False):
        direct = rapport_direct(d, "note", LISTE_NOTES) if par_note else rapport_direct(d, total="toutes notes")
        marges_direct = direct.conf_int()
        for n in (LISTE_NOTES if par_note else ["toutes notes"]):
            col = f"a répondu : {n}"
            dn = d if n == "toutes notes" else d[d["note"] == n]
            av_r, sup_r, fi_r = effectifs(dn[dn["a_repondu"]])
            av_n, sup_n, fi_n = effectifs(dn[~dn["a_repondu"]])
            rd = (sup_r / av_r) / (sup_n / av_n)
            assert abs(float(np.exp(direct.params[col])) - rd) < 1e-6, (perimetre, n)
            bas_d, haut_d = (float(np.exp(marges_direct.loc[col, k])) for k in (0, 1))
            lignes_notes.append({
                "perimetre": perimetre, "note": n.replace("1 étoile(s)", "1 étoile").replace("étoile(s)", "étoiles"),
                "taux_repondus_pour_1000": round(1000 * sup_r / av_r, 1),
                "taux_sans_reponse_pour_1000": round(1000 * sup_n / av_n, 1),
                "rapport_direct": round(rd, 2), "rapport_direct_bas": round(bas_d, 2),
                "rapport_direct_haut": round(haut_d, 2),
                "avis_repondus": av_r, "suppressions_repondus": sup_r, "fiches_repondus": fi_r,
                "avis_sans_reponse": av_n, "suppressions_sans_reponse": sup_n, "fiches_sans_reponse": fi_n})

r_notes = pd.DataFrame(lignes_notes)
r_notes.to_csv(SORTIES / "03D_reponse_par_note.csv", sep=";", decimal=",", index=False)
print(f"  {SORTIES / '03D_reponse_par_note.csv'}")

# ---------------------------------------------------------------------------
# Graphiques : toutes les fiches. Une barre par groupe, puis le total à part.
# Les secteurs vont du plus petit rapport au plus grand, les notes de 1 à 5.
# ---------------------------------------------------------------------------
BLEU, BLEU_TOTAL, GRIS, ENCRE, FOND = "#2a78d6", "#104281", "#8a8984", "#0b0b0b", "#fcfcfb"


def en_pourcentage(rapport):
    """Le rapport en écart de taux : 0,2 donne « −80 % », 1 donne « 0 % »."""
    ecart = round(100 * (rapport - 1))
    return "0 %" if ecart == 0 else f"{ecart:+d} %".replace("-", "−")


def graphique(t, groupe, total, valeur, bas, haut, fichier, titre, lecture, trier=True, en_avis=False,
              perimetre="tous"):
    """Une barre par valeur de `groupe` pour la colonne `valeur`, fourchette `bas`-`haut`.

    L'axe se lit en écart de taux : chaque barre part de 0 % (même taux avec
    ou sans réponse) et descend jusqu'au rapport, ou monte s'il dépasse 1.
    Sous chaque valeur : les suppressions d'avis répondus / sans réponse, ou,
    avec `en_avis`, le nombre d'avis sur lequel l'écart est calculé.
    """
    g = t[t["perimetre"] == perimetre]
    d = perimetre_de(perimetre)
    n_avis = f"{len(d):,}".replace(",", " ")
    n_suppr = f"{int(d['y'].sum()):,}".replace(",", " ")
    groupes = g[g[groupe] != total]
    barres = pd.concat([groupes.sort_values(valeur) if trier else groupes, g[g[groupe] == total]])
    x = np.arange(len(barres), dtype=float)
    x[-1] += 0.6  # un blanc avant la barre « tous secteurs »

    fig, ax = plt.subplots(figsize=(11, 6.5), facecolor=FOND)
    ax.set_facecolor(FOND)
    couleurs = [BLEU] * (len(barres) - 1) + [BLEU_TOTAL]
    ax.bar(x, barres[valeur] - 1, bottom=1, width=0.62, color=couleurs, zorder=2)
    ax.errorbar(x, barres[valeur], yerr=[barres[valeur] - barres[bas], barres[haut] - barres[valeur]],
                fmt="none", ecolor=ENCRE, elinewidth=1.3, capsize=5, zorder=3)
    # Valeur et effectifs au bout de la barre, au-delà de la fourchette : sous
    # une barre qui descend, au-dessus d'une barre qui monte.
    for xi, (_, b) in zip(x, barres.iterrows()):
        if en_avis:
            effectif = f"({b['avis_repondus'] + b['avis_sans_reponse']:,} avis)".replace(",", " ")
        else:
            effectif = f"{b['suppressions_repondus']} / {b['suppressions_sans_reponse']} suppr."
        if b[valeur] < 1:
            ax.text(xi, b[bas] - 0.03, en_pourcentage(b[valeur]),
                    ha="center", va="top", fontsize=10, fontweight="bold", color=ENCRE)
            ax.text(xi, b[bas] - 0.10, effectif, ha="center", va="top", fontsize=7.5, color=GRIS)
        else:
            ax.text(xi, b[haut] + 0.10, en_pourcentage(b[valeur]),
                    ha="center", va="bottom", fontsize=10, fontweight="bold", color=ENCRE)
            ax.text(xi, b[haut] + 0.03, effectif, ha="center", va="bottom", fontsize=7.5, color=GRIS)

    # Pas d'effet : même taux de suppression avec ou sans réponse.
    ax.axhline(1, color=ENCRE, linestyle="--", linewidth=1.2, zorder=1)
    ax.text(x[-1] + 0.45, 1.02, "pas d'effet", ha="left", va="bottom", fontsize=9, color=ENCRE)

    ax.set_xticks(x, [s[0].upper() + s[1:].replace(" et ", "\net ").replace(" à ", "\nà ")
                      for s in barres[groupe]], fontsize=9.5)
    ax.set_yticks(np.arange(0, float(barres[haut].max()) + 0.31, 0.2))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: en_pourcentage(v)))
    ax.set_ylim(min(0.0, float(barres[bas].min()) - 0.22), float(barres[haut].max()) + 0.3)
    ax.set_xlim(-0.6, x[-1] + 1.4)
    ax.set_ylabel("Écart du taux de suppression, avis avec réponse face aux avis sans réponse",
                  fontsize=9.5, color=ENCRE)
    ax.grid(axis="y", color="#e4e3df", linewidth=0.6, zorder=0)
    for cote in ["top", "right"]:
        ax.spines[cote].set_visible(False)
    ax.tick_params(colors=ENCRE)

    fig.suptitle(titre, x=0.02, ha="left", fontsize=13, color=ENCRE)
    fig.text(0.02, 0.915,
             f"{n_avis} avis publiés du 6 au 17 août 2026, suivis jusqu'au 24 août, dont {n_suppr} supprimés, "
             f"{PERIMETRES_NOTES[perimetre]}.\n"
             f"{lecture} Trait : fourchette à 95 %. "
             "−60 % : l'avis répondu disparaît 60 % de moins que l'avis sans réponse.\n"
             "Sous chaque valeur : "
             + ("nombre d'avis sur lequel l'écart est calculé." if en_avis
                else "suppressions d'avis répondus / d'avis sans réponse."),
             ha="left", va="top", fontsize=8.5, color=GRIS)
    fig.tight_layout(rect=(0, 0, 1, 0.84))
    (SORTIES / "figures").mkdir(exist_ok=True)
    fig.savefig(SORTIES / "figures" / f"{fichier}.png", dpi=130, facecolor=FOND)
    plt.close(fig)
    print(f"  {SORTIES / 'figures' / f'{fichier}.png'}")


graphique(r, "secteur", "tous secteurs", "risque_relatif", "fourchette_basse", "fourchette_haute",
          "03D_reponse_par_secteur",
          "Écart du taux de suppression quand le propriétaire répond, par secteur",
          "Barre : écart des taux, les autres caractéristiques tenues égales.")
graphique(r, "secteur", "tous secteurs", "rapport_direct", "rapport_direct_bas", "rapport_direct_haut",
          "03D_reponse_par_secteur_direct",
          "Écart direct du taux de suppression quand le propriétaire répond, par secteur",
          "Barre : écart des taux comptés directement, rien n'est tenu égal.", en_avis=True)
graphique(r_notes, "note", "toutes notes", "rapport_direct", "rapport_direct_bas", "rapport_direct_haut",
          "03D_reponse_par_note_direct",
          "Écart direct du taux de suppression quand le propriétaire répond, par note",
          "Barre : écart des taux comptés directement, rien n'est tenu égal.", trier=False, en_avis=True)
graphique(r_notes, "note", "toutes notes", "rapport_direct", "rapport_direct_bas", "rapport_direct_haut",
          "03D_reponse_par_note_direct_sans_services_a_domicile",
          "Écart direct du taux de suppression quand le propriétaire répond, par note, sans les services à domicile",
          "Barre : écart des taux comptés directement, rien n'est tenu égal.", trier=False, en_avis=True,
          perimetre="sans_services_a_domicile")
