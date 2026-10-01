"""Google supprime peu une fois l'avis publié : deux graphiques, tous pays confondus.

    uv run python logistic-regression-study/refacto_2/03D_google_supprime_peu.py

Base `reviews_doublons_cleaned_all`, suppressions constatées du 11 au 24 août
2026. Les avis sont rangés selon leur date de publication (created_at) :
  jusqu'au 31 décembre 2025                    sql/03D_supprime_peu_anciens.sql
  de janvier à juillet 2026, par mois          sql/03D_supprime_peu_2026.sql
  du 11 au 23 août                             sql/03D_supprime_peu_recents.sql

Les CSV gardent aussi le périmètre sans les enseignes signalées, pour le
commentaire. Les graphiques ne montrent que toutes les fiches.

Produit, dans `sorties/` à côté de ce fichier :
  03D_supprime_peu_anciens.csv   figures/03D_supprime_peu_anciens.png
  03D_supprime_peu_2026.csv      figures/03D_supprime_peu_2026.png
  03D_supprime_peu_recents.csv   figures/03D_supprime_peu_recents.png
"""
import os
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # pas d'écran sous WSL
import matplotlib.pyplot as plt

PROJET = "client-divers"
DOSSIER = Path(__file__).resolve().parent
SORTIES = DOSSIER / "sorties"
DOSSIER_CLES = Path.home() / ".gcp"
BLEU, GRIS, ENCRE, FOND = "#2a78d6", "#8a8984", "#0b0b0b", "#fcfcfb"
# Même mesure et même échelle sur les trois graphiques : suppressions d'une
# journée pour 10 000 avis en ligne, de 0 à 200.
Y_MAX = 200


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


def virgule(v, decimales=1):
    return f"{v:.{decimales}f}".replace(".", ",")


def lire(nom):
    d = client().query((DOSSIER / "sql" / f"{nom}.sql").read_text(encoding="utf-8")).to_dataframe()
    # Point-virgule et virgule décimale : Sheets en français les lit tels quels.
    d.to_csv(SORTIES / f"{nom}.csv", sep=";", decimal=",", index=False)
    print(f"  {SORTIES / f'{nom}.csv'}")
    return d


def barres(x_libelles, valeurs, fichier, titre, sous_titre, ylabel, xlabel, decimales=1):
    fig, ax = plt.subplots(figsize=(12, 5.4), facecolor=FOND)
    ax.set_facecolor(FOND)
    x = range(len(valeurs))
    ax.bar(x, valeurs, width=0.7, color=BLEU, zorder=2)
    for xi, v in zip(x, valeurs):
        ax.text(xi, v + Y_MAX * 0.01, virgule(v, decimales), ha="center", va="bottom", fontsize=8,
                color=ENCRE)
    ax.set_ylim(0, Y_MAX)
    ax.set_xticks(list(x))
    ax.set_xticklabels(x_libelles)
    ax.set_ylabel(ylabel, color=ENCRE)
    ax.set_xlabel(xlabel, color=ENCRE)
    ax.grid(axis="y", color="#e4e3df", linewidth=0.6, zorder=0)
    for cote in ["top", "right", "left"]:
        ax.spines[cote].set_visible(False)
    ax.tick_params(colors=GRIS, labelsize=8)
    fig.suptitle(titre, x=0.02, ha="left", fontsize=12, color=ENCRE)
    fig.text(0.02, 0.905, sous_titre, ha="left", va="top", fontsize=8.5, color=GRIS)
    fig.tight_layout(rect=(0, 0, 1, 0.86))
    fig.savefig(SORTIES / "figures" / fichier, dpi=130, facecolor=FOND, bbox_inches="tight")
    plt.close(fig)
    print(f"  {SORTIES / 'figures' / fichier}")


SORTIES.mkdir(parents=True, exist_ok=True)
(SORTIES / "figures").mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Graphique 1 : avis publiés jusqu'en 2025, par année de publication.
# ---------------------------------------------------------------------------
anciens = lire("03D_supprime_peu_anciens")
a = anciens[anciens["perimetre"] == "tous"].set_index("publication")
total = a.loc["total"]
a = a.drop("total")
barres(list(a.index), list(a["pour_10000_par_jour"]),
       "03D_supprime_peu_anciens.png",
       "Avis publiés de 2004 à 2025 : suppressions par jour pendant le suivi",
       f"{milliers(total['suppressions'])} suppressions sur {milliers(total['avis'])} avis publiés "
       f"jusqu'au 31 décembre 2025, soit {virgule(total['pour_10000_par_jour'], 2)} par jour pour 10 000. "
       "Toutes les fiches, tous pays.\n"
       "Chaque barre : suppressions d'une journée pour 10 000 avis, soit le total des 13 jours de suivi "
       "(12 au 24 août 2026) divisé par 13.\nUn avis supprimé avant le 11 août n'est pas dans la base.",
       "suppressions du jour pour 10 000 avis", "année de publication", decimales=2)

# ---------------------------------------------------------------------------
# Graphique 1 bis : avis publiés de janvier à juillet 2026, par mois.
# ---------------------------------------------------------------------------
MOIS = {"01": "janvier", "02": "février", "03": "mars", "04": "avril", "05": "mai",
        "06": "juin", "07": "juillet"}
mois = lire("03D_supprime_peu_2026")
m = mois[mois["perimetre"] == "tous"].set_index("publication")
total = m.loc["total"]
m = m.drop("total").sort_index()
barres([MOIS[k] for k in m.index], list(m["pour_10000_par_jour"]),
       "03D_supprime_peu_2026.png",
       "Avis publiés de janvier à juillet 2026 : suppressions par jour pendant le suivi",
       f"{milliers(total['suppressions'])} suppressions sur {milliers(total['avis'])} avis publiés "
       f"du 1er janvier au 31 juillet 2026, soit {virgule(total['pour_10000_par_jour'], 2)} par jour pour 10 000. "
       "Toutes les fiches, tous pays.\n"
       "Chaque barre : suppressions d'une journée pour 10 000 avis, soit le total des 13 jours de suivi "
       "(12 au 24 août 2026) divisé par 13.\nUn avis supprimé avant le 11 août n'est pas dans la base.",
       "suppressions du jour pour 10 000 avis", "mois de publication", decimales=2)

# ---------------------------------------------------------------------------
# Graphique 2 : avis publiés du 11 au 23 août, par jour d'âge.
# ---------------------------------------------------------------------------
recents = lire("03D_supprime_peu_recents")
r = recents[recents["perimetre"] == "tous"].set_index("jour")
total = r.loc[0]
r = r.drop(0).sort_index()
barres([f"{'48 h' if j == 2 else f'{j}e'}\n{milliers(n)}" for j, n in r["en_ligne_la_veille"].items()],
       list(r["pour_10000"]),
       "03D_supprime_peu_recents.png",
       "Avis publiés pendant le suivi : suppressions selon l'âge de l'avis",
       f"{milliers(total['suppressions'])} suppressions sur {milliers(total['en_ligne_la_veille'])} avis "
       f"publiés du 11 au 23 août 2026, soit {virgule(100 * total['suppressions'] / total['en_ligne_la_veille'])} %. "
       "Toutes les fiches, tous pays.\n"
       "Chaque barre : avis disparus ce jour-là pour 10 000 avis en ligne la veille. Sous chaque barre : "
       "avis en ligne la veille.\n"
       "« 48 h » regroupe les 2 premiers jours. Un avis du 11 août est suivi 13 jours, un avis du "
       "20 août 4 jours.",
       "suppressions du jour pour 10 000 avis", "âge de l'avis, en jours")
