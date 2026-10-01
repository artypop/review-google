"""Courbe de vie d'un avis sur ses 21 premiers jours, États-Unis et Europe.

    uv run python logistic-regression-study/refacto_2/03D_courbe_de_vie.py

Avis de `reviews_doublons_cleaned_all` publiés de J-7 à J+14 (J = 11 août 2026,
premier passage du robot).
Le calcul est expliqué en tête de `sql/03D_courbe_de_vie.sql`. Le CSV garde
aussi le périmètre sans les enseignes signalées, pour le commentaire. Le
graphique ne montre que toutes les fiches.

Produit, dans `sorties/` à côté de ce fichier :
  03D_courbe_de_vie.csv   figures/03D_courbe_de_vie.png
"""
import os
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # pas d'écran sous WSL
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

PROJET = "client-divers"
DOSSIER = Path(__file__).resolve().parent
SORTIES = DOSSIER / "sorties"
DOSSIER_CLES = Path.home() / ".gcp"

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


d = client().query((DOSSIER / "sql" / "03D_courbe_de_vie.sql").read_text(encoding="utf-8")).to_dataframe()
SORTIES.mkdir(parents=True, exist_ok=True)
# Point-virgule et virgule décimale : Sheets en français les lit tels quels.
d.to_csv(SORTIES / "03D_courbe_de_vie.csv", sep=";", decimal=",", index=False)
print(f"  {SORTIES / '03D_courbe_de_vie.csv'}")

# ---------------------------------------------------------------------------
# Graphique : barres US et Europe côte à côte, jour par jour, toutes les fiches.
# ---------------------------------------------------------------------------
t = d[d["perimetre"] == "tous"]
fig, ax = plt.subplots(figsize=(13, 5.2), facecolor=FOND)
ax.set_facecolor(FOND)
largeur = 0.4
for i, region in enumerate(["US", "Europe"]):
    r = t[t["region"] == region].sort_values("jour")
    ax.bar(r["jour"] + (i - 0.5) * largeur, r["encore_en_ligne_pct"], width=largeur - 0.04,
           color=COULEURS[region], label=NOMS[region], zorder=2)

ax.set_ylim(0, 100)
ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0f} %"))
ax.set_xticks(range(1, 22))
ax.set_xlim(0.4, 21.6)
ax.set_xlabel("jour d'existence de l'avis", color=ENCRE)
ax.grid(axis="y", color="#e4e3df", linewidth=0.6, zorder=0)
for cote in ["top", "right", "left"]:
    ax.spines[cote].set_visible(False)
ax.tick_params(colors=GRIS, labelsize=9)
ax.legend(loc="lower right", bbox_to_anchor=(1, 1.01), ncol=2, frameon=False, fontsize=9)

# Avis observés au 1er et au 20e jour, par région, pour le sous-titre.
def observes(region, jour):
    n = int(t[(t["region"] == region) & (t["jour"] == jour)]["en_ligne_la_veille"].iloc[0])
    return f"{n:,}".replace(",", " ")


fig.suptitle("Part des avis encore en ligne, jour par jour, sur leurs 21 premiers jours",
             x=0.02, ha="left", fontsize=12, color=ENCRE)
fig.text(0.02, 0.905,
         "Avis publiés du 4 au 24 août 2026 (J-7 à J+13, J = 11 août), suivis du 11 au 24 août, toutes les fiches. "
         "Un avis ne compte qu'à partir du jour où le robot l'a vu en ligne.\n"
         f"Avis observés au 1er jour : {observes('US', 1)} aux États-Unis, {observes('Europe', 1)} en Europe. "
         f"Au 20e jour : {observes('US', 20)} et {observes('Europe', 20)}. "
         "Le 21e jour est vide : le suivi s'arrête avant.",
         ha="left", va="top", fontsize=8.5, color=GRIS)
fig.tight_layout(rect=(0, 0, 1, 0.86))
(SORTIES / "figures").mkdir(exist_ok=True)
fig.savefig(SORTIES / "figures" / "03D_courbe_de_vie.png", dpi=130, facecolor=FOND, bbox_inches="tight")
print(f"  {SORTIES / 'figures' / '03D_courbe_de_vie.png'}")
