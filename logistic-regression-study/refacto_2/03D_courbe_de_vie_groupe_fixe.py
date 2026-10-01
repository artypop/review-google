"""Courbe de vie d'un groupe d'avis fixe, et une courbe par date de publication.

    uv run python logistic-regression-study/refacto_2/03D_courbe_de_vie_groupe_fixe.py

Avis de `reviews_doublons_cleaned_all` publiés du 10 au 17 août 2026. Le
calcul est expliqué en tête de `sql/03D_courbe_de_vie_groupe_fixe.sql`. Il
lève deux réserves de `03D_courbe_de_vie.py` : les jours y sont mesurés sur
des avis différents, et le 1er jour repose sur peu d'avis. Le CSV garde aussi
le périmètre sans les enseignes signalées. Les graphiques ne montrent que
toutes les fiches.

Produit, dans `sorties/` à côté de ce fichier :
  03D_courbe_de_vie_groupe_fixe.csv
  figures/03D_courbe_de_vie_groupe_fixe.png   le groupe entier, jours 2 à 7
  figures/03D_courbe_de_vie_groupe_fixe_A.png les avis du 10 août, jours 2 à 14
  03D_courbe_de_vie_groupe_fixe_B.csv
  figures/03D_courbe_de_vie_groupe_fixe_B.png chaque jour, les avis suivis jusque-là, jours 2 à 14
  figures/03D_courbe_de_vie_par_date.png      une courbe par date de publication
"""
import os
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # pas d'écran sous WSL
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FuncFormatter

PROJET = "client-divers"
DOSSIER = Path(__file__).resolve().parent
SORTIES = DOSSIER / "sorties"
DOSSIER_CLES = Path.home() / ".gcp"
GROUPE = "10 au 17 août"

# Couleurs des régions de consolidation/commun.py.
COULEURS = {"US": "#2a78d6", "Europe": "#eb6834"}
NOMS = {"US": "États-Unis", "Europe": "Europe"}
GRIS, ENCRE, FOND = "#8a8984", "#0b0b0b", "#fcfcfb"


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


def pct(v):
    return f"{v:.1f} %".replace(".", ",")


def jour_libelle(j):
    return "48 h" if j == 2 else f"{j}e jour"


d = client().query((DOSSIER / "sql" / "03D_courbe_de_vie_groupe_fixe.sql")
                   .read_text(encoding="utf-8")).to_dataframe()
SORTIES.mkdir(parents=True, exist_ok=True)
(SORTIES / "figures").mkdir(exist_ok=True)
# Point-virgule et virgule décimale : Sheets en français les lit tels quels.
d.to_csv(SORTIES / "03D_courbe_de_vie_groupe_fixe.csv", sep=";", decimal=",", index=False)
print(f"  {SORTIES / '03D_courbe_de_vie_groupe_fixe.csv'}")
t = d[d["perimetre"] == "tous"]

# ---------------------------------------------------------------------------
# Graphiques en barres, US et Europe côte à côte, axe vertical depuis 0.
# ---------------------------------------------------------------------------
def barres(g, fichier, titre, sous_titre, avis_sous_les_barres=False):
    """`g` : une ligne par région et par jour, colonnes jour, avis, encore_en_ligne_pct."""
    jours = sorted(g["jour"].unique())
    long = len(jours) > 7
    fig, ax = plt.subplots(figsize=(13 if long else 10, 5.4), facecolor=FOND)
    ax.set_facecolor(FOND)
    largeur = 0.4
    for i, region in enumerate(["US", "Europe"]):
        r = g[g["region"] == region].sort_values("jour")
        x = r["jour"] + (i - 0.5) * largeur
        ax.bar(x, r["encore_en_ligne_pct"], width=largeur - 0.04, color=COULEURS[region],
               label=NOMS[region], zorder=2)
        for xi, v in zip(x, r["encore_en_ligne_pct"]):
            ax.text(xi, v + 1, pct(v), ha="center", va="bottom", fontsize=7 if long else 8,
                    rotation=90 if long else 0, color=ENCRE)

    ax.set_ylim(0, 112 if long else 108)
    ax.set_yticks(range(0, 101, 20))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0f} %"))
    ax.set_xticks(jours)
    libelles = ["48 h" if j == 2 else (f"{j}e" if long else jour_libelle(j)) for j in jours]
    if avis_sous_les_barres:
        n = g.set_index(["region", "jour"])["avis"]
        libelles = [f"{l}\n{milliers(n['US', j])}\n{milliers(n['Europe', j])}"
                    for l, j in zip(libelles, jours)]
        ax.text(-0.01, -0.075, "avis US\navis Europe", transform=ax.transAxes, ha="right",
                va="top", fontsize=8, color=GRIS)
    ax.set_xticklabels(libelles)
    ax.set_xlabel("âge de l'avis, en jours", color=ENCRE)
    ax.grid(axis="y", color="#e4e3df", linewidth=0.6, zorder=0)
    for cote in ["top", "right", "left"]:
        ax.spines[cote].set_visible(False)
    ax.tick_params(colors=GRIS, labelsize=8 if avis_sous_les_barres else 9)
    ax.legend(loc="lower right", bbox_to_anchor=(1, 1.01), ncol=2, frameon=False, fontsize=9)

    fig.suptitle(titre, x=0.02, ha="left", fontsize=12, color=ENCRE)
    fig.text(0.02, 0.905, sous_titre, ha="left", va="top", fontsize=8.5, color=GRIS)
    fig.tight_layout(rect=(0, 0, 1, 0.86))
    fig.savefig(SORTIES / "figures" / fichier, dpi=130, facecolor=FOND, bbox_inches="tight")
    plt.close(fig)
    print(f"  {SORTIES / 'figures' / fichier}")


QUARANTE_HUIT = ("« 48 h » regroupe les 2 premiers jours : le robot passe une fois par jour et voit "
                 "la plupart des avis pour la première fois à 1 jour d'âge.")

# Le groupe entier, jours 2 à 7.
g = t[t["publication"] == GROUPE]
n = {region: g[(g["region"] == region) & (g["jour"] == 2)].iloc[0] for region in ["US", "Europe"]}
barres(g, "03D_courbe_de_vie_groupe_fixe.png",
       "Part des avis encore en ligne, sur un même groupe d'avis suivi jour par jour",
       f"Avis publiés du 10 au 17 août 2026 : {milliers(n['US']['avis'])} aux États-Unis, "
       f"{milliers(n['Europe']['avis'])} en Europe, toutes les fiches. Les mêmes avis à chaque jour.\n"
       + QUARANTE_HUIT)

# A : les seuls avis du 10 août, suivis jusqu'à 14 jours.
a = t[t["publication"] == "2026-08-10"]
n = {region: a[(a["region"] == region) & (a["jour"] == 2)].iloc[0] for region in ["US", "Europe"]}
barres(a, "03D_courbe_de_vie_groupe_fixe_A.png",
       "Part des avis encore en ligne sur 14 jours, avis publiés le 10 août",
       f"Avis publiés le 10 août 2026 : {milliers(n['US']['avis'])} aux États-Unis, "
       f"{milliers(n['Europe']['avis'])} en Europe, toutes les fiches. Les mêmes avis à chaque jour, "
       "seule date suivie 14 jours.\n" + QUARANTE_HUIT)

# B : chaque jour, les avis du 10 au 17 août suivis jusqu'à ce jour-là.
# Le groupe rétrécit : 8 dates de publication jusqu'au 7e jour, la seule du
# 10 août au 14e. Les fiches touchées ne s'additionnent pas d'une date à
# l'autre, elles restent dans le CSV par date.
b = (d[d["publication"] != GROUPE]
     .groupby(["perimetre", "region", "jour"], as_index=False)
     .agg(dates_suivies=("publication", "nunique"), avis=("avis", "sum"),
          disparus=("disparus", "sum")))
b["encore_en_ligne_pct"] = (100 - 100 * b["disparus"] / b["avis"]).round(3)
b.to_csv(SORTIES / "03D_courbe_de_vie_groupe_fixe_B.csv", sep=";", decimal=",", index=False)
print(f"  {SORTIES / '03D_courbe_de_vie_groupe_fixe_B.csv'}")
barres(b[b["perimetre"] == "tous"], "03D_courbe_de_vie_groupe_fixe_B.png",
       "Part des avis encore en ligne sur 14 jours, groupe qui rétrécit",
       "Avis publiés du 10 au 17 août 2026, toutes les fiches. Chaque jour compte les avis suivis "
       "jusque-là : les 8 dates jusqu'au 7e jour, une date de moins chaque jour ensuite, le 10 août "
       "seul au 14e.\n" + QUARANTE_HUIT + " Sous chaque barre : avis comptés ce jour-là.",
       avis_sous_les_barres=True)

# ---------------------------------------------------------------------------
# Graphique 2 : une courbe par date de publication, en avis disparus.
# Les dates se suivent : un seul bleu, du plus clair (10 août) au plus foncé.
# ---------------------------------------------------------------------------
p = t[t["publication"] != GROUPE]
dates = sorted(p["publication"].unique())
bleus = plt.get_cmap("Blues")(np.linspace(0.35, 0.95, len(dates)))
fig, axes = plt.subplots(1, 2, figsize=(13, 5.2), facecolor=FOND, sharey=True)
haut = np.ceil(p["disparus_pct"].max()) + 1
for ax, region in zip(axes, ["US", "Europe"]):
    ax.set_facecolor(FOND)
    for couleur, date in zip(bleus, dates):
        r = p[(p["region"] == region) & (p["publication"] == date)].sort_values("jour")
        jour_mois = f"{int(date[8:])} août"
        ax.plot(r["jour"], r["disparus_pct"], color=couleur, linewidth=2, marker="o", markersize=3,
                label=f"{jour_mois} ({milliers(r['avis'].iloc[0])} avis)")
    ax.set_title(NOMS[region], loc="left", fontsize=11, color=ENCRE)
    ax.set_ylim(0, haut)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0f} %"))
    ax.set_xticks(range(2, 15))
    ax.set_xticklabels(["48 h"] + [str(j) for j in range(3, 15)])
    ax.set_xlabel("âge de l'avis, en jours", color=ENCRE)
    ax.grid(axis="y", color="#e4e3df", linewidth=0.6)
    for cote in ["top", "right"]:
        ax.spines[cote].set_visible(False)
    ax.tick_params(colors=GRIS, labelsize=9)
    ax.legend(title="publiés le", frameon=False, fontsize=8, title_fontsize=8, loc="upper left")

fig.suptitle("Part des avis disparus selon leur âge, une courbe par date de publication",
             x=0.02, ha="left", fontsize=12, color=ENCRE)
fig.text(0.02, 0.905,
         "Avis publiés du 10 au 17 août 2026, toutes les fiches, suivis jusqu'au 24 août. "
         "Chaque courbe suit les mêmes avis, compte direct.\n"
         "Si les courbes se superposent, enchaîner les jours comme dans 03D_courbe_de_vie.png est "
         "justifié.",
         ha="left", va="top", fontsize=8.5, color=GRIS)
fig.tight_layout(rect=(0, 0, 1, 0.86))
fig.savefig(SORTIES / "figures" / "03D_courbe_de_vie_par_date.png", dpi=130, facecolor=FOND,
            bbox_inches="tight")
plt.close(fig)
print(f"  {SORTIES / 'figures' / '03D_courbe_de_vie_par_date.png'}")
