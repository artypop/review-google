"""Avis du jour face à la moyenne des 7 jours précédents, panel 03D.

    uv run python logistic-regression-study/refacto_2/03D_moyenne_mobile.py

LA QUESTION (Axel, 2026-10-08)
  Un avis publié un jour où la fiche reçoit plus d'avis que sa moyenne des
  7 jours précédents disparaît-il plus souvent ?

LE CALCUL
  Tranches et données : `sql/03D_moyenne_mobile.sql`. Deux mesures :
  - suppressions pour 1 000 avis par tranche, comptées directement ;
  - l'effet à autres caractéristiques égales : le modèle de
    `03D_regression_logistique.py`, mêmes références, où la tranche remplace
    le pic. Référence : « au plus la moyenne ».
  Passages : ensemble, ensemble sans les chaînes, États-Unis, Europe.

Produit, dans `sorties/` à côté de ce fichier :
  03D_moyenne_mobile_taux.csv    avis, suppressions, fiches touchées, pour 1 000
  03D_moyenne_mobile_effets.csv  effet de chaque tranche et fourchette à 95 %
  figures/03D_moyenne_mobile.png
"""
import os
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # pas d'écran sous WSL
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm

PROJET = "client-divers"
DOSSIER = Path(__file__).resolve().parent
SORTIES = DOSSIER / "sorties"
DOSSIER_CLES = Path.home() / ".gcp"
BLEU, VERT, GRIS, ENCRE, FOND = "#2a78d6", "#1baf7a", "#8a8984", "#0b0b0b", "#fcfcfb"

TRANCHES = ["au plus la moyenne", "1 à 2 fois la moyenne", "2 à 3 fois la moyenne",
            "plus de 3 fois la moyenne", "aucun avis les 7 jours avant"]
# Mêmes découpages et références que 03D_regression_logistique.py.
TEXTE = [(1, 50, "1 à 50"), (51, 200, "51 à 200"), (201, None, "plus de 200")]
PHOTOS_AUTEUR = [(1, 20, "1 à 20"), (21, None, "plus de 20")]
AVIS_AUTEUR = [(2, 20, "2 à 20"), (21, None, "plus de 20")]
SECTEURS = ["automotive", "home_services", "healthcare", "wellness_fitness", "food_beverage",
            "travel", "hospitality"]
PASSAGES = {"ensemble, tous": lambda d: d,
            "ensemble, sans_enseignes": lambda d: d[~d["enseigne_signalee"]],
            "US, tous": lambda d: d[d["region"] == "US"],
            "EU, tous": lambda d: d[d["region"] == "EU"]}


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


def milliers(n):
    return f"{int(n):,}".replace(",", " ")


def tranche(valeurs, tranches, defaut):
    conditions = [(valeurs >= bas) & (valeurs <= haut if haut is not None else True)
                  for bas, haut, _ in tranches]
    return np.select(conditions, [nom for _, _, nom in tranches], defaut)


d0 = client().query((DOSSIER / "sql" / "03D_moyenne_mobile.sql").read_text(encoding="utf-8")).to_dataframe()
d0["y"] = d0["supprime"].astype(int)
print(f"  {len(d0)} avis, {d0['y'].sum()} suppressions")

# ---------------------------------------------------------------------------
# 1. Taux comptés directement.
# ---------------------------------------------------------------------------
lignes = []
for passage, choisir in PASSAGES.items():
    d = choisir(d0)
    for t in TRANCHES:
        c = d[d["tranche_7j"] == t]
        lignes.append({"passage": passage, "tranche": t, "avis": len(c), "suppressions": int(c["y"].sum()),
                       "fiches_touchees": c.loc[c["y"] == 1, "cid"].nunique(),
                       "pour_1000": round(1000 * c["y"].mean(), 1)})
taux = pd.DataFrame(lignes)
SORTIES.mkdir(parents=True, exist_ok=True)
taux.to_csv(SORTIES / "03D_moyenne_mobile_taux.csv", sep=";", decimal=",", index=False)
print(f"  {SORTIES / '03D_moyenne_mobile_taux.csv'}")

# ---------------------------------------------------------------------------
# 2. À autres caractéristiques égales : le modèle 03D, la tranche remplaçant le pic.
# ---------------------------------------------------------------------------
d0["note"] = d0["star"].astype(int)
d0["texte"] = tranche(d0["text_chars"], TEXTE, "sans texte")
d0["photos_auteur"] = tranche(d0["reviewer_photo_count"], PHOTOS_AUTEUR, "0")
d0["avis_auteur"] = tranche(d0["reviewer_review_count"], AVIS_AUTEUR, "1 ou moins")
d0["taux_reponse_10pts"] = 10 * (d0["taux_reponse_fiche"] - d0["taux_reponse_fiche"].median())
CARACTERISTIQUES = {
    "tranche_7j": TRANCHES,
    "note": [3, 1, 2, 4, 5],
    "palier_local_guide": ["sans_niveau", "1_4", "5_et_plus"],
    "has_photo": [False, True],
    "texte": ["sans texte"] + [n for _, _, n in TEXTE],
    "photos_auteur": ["0"] + [n for _, _, n in PHOTOS_AUTEUR],
    "avis_auteur": ["1 ou moins"] + [n for _, _, n in AVIS_AUTEUR],
    "a_repondu": [False, True],
    "secteur": SECTEURS,
    "bucket": ["mono", "small", "large"],
}

effets = []
for passage, choisir in PASSAGES.items():
    d = choisir(d0)
    X = pd.DataFrame(index=d.index)
    for carac, cases in CARACTERISTIQUES.items():
        for case in cases[1:]:
            # Même garde-fou que 03D : une case de moins de 5 suppressions sort.
            if (d.loc[d[carac] == case, "y"].sum()) >= 5:
                X[f"{carac} : {case}"] = (d[carac] == case).astype(float)
    X["taux_reponse_fiche : +10 points"] = d["taux_reponse_10pts"]
    if passage.startswith("ensemble"):
        X["region : US"] = (d["region"] == "US").astype(float)
    # Les avis des cases retirées sortent du modèle avec elles.
    garde = pd.Series(True, index=d.index)
    for carac, cases in CARACTERISTIQUES.items():
        for case in cases[1:]:
            if f"{carac} : {case}" not in X and (d[carac] == case).any():
                garde &= d[carac] != case
    d, X = d[garde], sm.add_constant(X[garde])
    m = sm.GLM(d["y"], X, family=sm.families.Binomial()).fit(
        cov_type="cluster", cov_kwds={"groups": pd.factorize(d["cid"])[0]})
    marges = m.conf_int()
    print(f"  {passage} : {len(d)} avis, {d['y'].sum()} suppressions, converge : {m.converged}")
    for t in TRANCHES[1:]:
        col = f"tranche_7j : {t}"
        ligne = {"passage": passage, "tranche": t, "avis_dans_le_modele": len(d)}
        if col in X:
            ligne.update(risque_relatif=round(float(np.exp(m.params[col])), 2),
                         fourchette_basse=round(float(np.exp(marges.loc[col, 0])), 2),
                         fourchette_haute=round(float(np.exp(marges.loc[col, 1])), 2))
        effets.append(ligne)
effets = pd.DataFrame(effets)
effets.to_csv(SORTIES / "03D_moyenne_mobile_effets.csv", sep=";", decimal=",", index=False)
print(f"  {SORTIES / '03D_moyenne_mobile_effets.csv'}")
print(taux.to_string(index=False))
print(effets.to_string(index=False))

# ---------------------------------------------------------------------------
# Graphique : à gauche les taux directs, à droite l'effet à caractéristiques
# égales. Toutes les fiches en bleu, sans les chaînes en vert.
# ---------------------------------------------------------------------------
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6.2), facecolor=FOND)
x = np.arange(len(TRANCHES))
libelles = [t.replace(" la moyenne", "\nla moyenne").replace(" les 7", "\nles 7") for t in TRANCHES]
for i, (passage, couleur, nom) in enumerate([("ensemble, tous", BLEU, "toutes les fiches"),
                                             ("ensemble, sans_enseignes", VERT, "sans les chaînes")]):
    t = taux[taux["passage"] == passage].set_index("tranche").loc[TRANCHES]
    barres = ax1.bar(x + (i - 0.5) * 0.38, t["pour_1000"], width=0.36, color=couleur, label=nom)
    ax1.bar_label(barres, labels=[f"{v:.1f}".replace(".", ",") for v in t["pour_1000"]], padding=2,
                  fontsize=8)
    e = effets[effets["passage"] == passage].set_index("tranche")
    rr = [1.0] + [e.loc[t_, "risque_relatif"] for t_ in TRANCHES[1:]]
    bas = [1.0] + [e.loc[t_, "fourchette_basse"] for t_ in TRANCHES[1:]]
    haut = [1.0] + [e.loc[t_, "fourchette_haute"] for t_ in TRANCHES[1:]]
    xx = x + (i - 0.5) * 0.3
    ax2.errorbar(xx[1:], rr[1:], yerr=[np.subtract(rr, bas)[1:], np.subtract(haut, rr)[1:]], fmt="o",
                 color=couleur, ecolor=couleur, capsize=4, label=nom)
    for xi, v in zip(xx[1:], rr[1:]):
        ax2.text(xi + 0.06, v, f"×{v:.2f}".replace(".", ","), va="center", fontsize=8, color=ENCRE)
ax2.scatter([0], [1], s=40, facecolor=FOND, edgecolor=GRIS, zorder=3)
ax2.axhline(1, color=ENCRE, linestyle="--", linewidth=1)
ax2.text(0.1, 1.02, "référence", fontsize=8, color=GRIS, va="bottom")
for ax, titre in [(ax1, "Suppressions pour 1 000 avis, comptées directement"),
                  (ax2, "Risque face à « au plus la moyenne », autres caractéristiques égales")]:
    ax.set_facecolor(FOND)
    ax.set_xticks(x, libelles, fontsize=8.5)
    ax.set_title(titre, loc="left", fontsize=10.5, color=ENCRE)
    ax.grid(axis="y", color="#e4e3df", linewidth=0.6)
    for cote in ["top", "right"]:
        ax.spines[cote].set_visible(False)
    ax.legend(frameon=False, fontsize=8.5, loc="upper right")
ax2.set_yscale("log")
ax2.set_yticks([0.25, 0.5, 1, 2])
ax2.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"×{v:g}".replace(".", ",")))
ax2.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())

n = taux[taux["passage"] == "ensemble, tous"]
fig.suptitle("Avis publiés un jour où la fiche reçoit plus que sa moyenne des 7 jours précédents",
             x=0.02, ha="left", fontsize=12.5, color=ENCRE)
fig.text(0.02, 0.905,
         f"{milliers(n['avis'].sum())} avis publiés du 6 au 17 août 2026, suivis jusqu'au 24 août, dont "
         f"{milliers(n['suppressions'].sum())} supprimés. Chaque tranche : avis de la fiche le jour de "
         "publication rapportés à sa moyenne quotidienne des 7 jours précédents.\n"
         + "Droite : note, Local Guide, texte, photos, profil de l'auteur, réponse, secteur, taille et "
           "région tenus égaux ; trait : fourchette à 95 %.",
         ha="left", va="top", fontsize=8.5, color=GRIS)
fig.tight_layout(rect=(0, 0, 1, 0.85))
(SORTIES / "figures").mkdir(exist_ok=True)
fig.savefig(SORTIES / "figures" / "03D_moyenne_mobile.png", dpi=130, facecolor=FOND)
plt.close(fig)
print(f"  {SORTIES / 'figures' / '03D_moyenne_mobile.png'}")
