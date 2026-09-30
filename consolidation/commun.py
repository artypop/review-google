"""Outils partagés par tous les scripts de `consolidation/`.

Quatre choses, rien d'autre :

  requete(nom)        exécute `sql/<nom>.sql` dans BigQuery, rend un tableau pandas
  ecrire_csv(df, nom) écrit `sorties/<nom>.csv`, prêt pour Google Sheets en français
  figure(...)         ouvre un graphique aux couleurs du projet
  enregistrer(fig, n) écrit `sorties/figures/<n>.png`

Tout le comptage se fait dans BigQuery. Python ne reçoit que des tableaux déjà
agrégés, de quelques centaines de lignes au plus. Les régressions font exception :
3b, 4b, 5, et le 8 avec un million de lignes regroupées par fiche.
"""
from __future__ import annotations

import os
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # pas d'écran sous WSL : les graphiques vont dans des fichiers
import matplotlib.pyplot as plt
import pandas as pd

PROJET = "client-divers"
DOSSIER = Path(__file__).resolve().parent
SQL = DOSSIER / "sql"
SORTIES = DOSSIER / "sorties"
FIGURES = SORTIES / "figures"
DOSSIER_CLES = Path.home() / ".gcp"

# Couleurs des graphiques. Une couleur par région, la même partout.
COULEURS = {"US": "#2a78d6", "Europe": "#eb6834", "ensemble": "#1baf7a"}
ENCRE = "#0b0b0b"
ENCRE_SECONDAIRE = "#52514e"
FOND = "#fcfcfb"

_client = None


def client():
    """Le client BigQuery, avec la clé de service de `~/.gcp/`.

    Même logique que `logistic-regression-study/python/08B_effet_reponse_commercant.py` :
    `GOOGLE_APPLICATION_CREDENTIALS` l'emporte s'il est posé, sinon on prend le
    seul `.json` du dossier.
    """
    global _client
    if _client is None:
        if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") and DOSSIER_CLES.is_dir():
            cles = sorted(DOSSIER_CLES.glob("*.json"))
            if len(cles) > 1:
                raise SystemExit(f"{len(cles)} clés dans {DOSSIER_CLES}, en garder une.")
            if cles:
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(cles[0])
        from google.cloud import bigquery
        _client = bigquery.Client(project=PROJET, location="EU")
    return _client


def requete(nom: str) -> pd.DataFrame:
    """Exécute `sql/<nom>.sql` et rend le résultat."""
    texte = (SQL / f"{nom}.sql").read_text(encoding="utf-8")
    df = client().query(texte).to_dataframe()
    print(f"  sql/{nom}.sql -> {len(df)} lignes")
    return df


def ecrire_csv(df: pd.DataFrame, nom: str) -> None:
    """Point-virgule entre colonnes, virgule décimale : Sheets en français les lit tels quels."""
    SORTIES.mkdir(parents=True, exist_ok=True)
    df.to_csv(SORTIES / f"{nom}.csv", sep=";", decimal=",", index=False)
    print(f"  sorties/{nom}.csv")


def pour_10000(suppressions, avis):
    """Suppressions pour 10 000 avis, arrondi à l'unité. Vide si aucun avis."""
    avis = pd.Series(avis, dtype="float")
    return (10000 * pd.Series(suppressions, dtype="float") / avis.where(avis > 0)).round(0)


def figure(lignes: int = 1, colonnes: int = 1, largeur: float = 10, hauteur: float = 5):
    plt.rcParams.update({
        "figure.facecolor": FOND, "axes.facecolor": FOND,
        "axes.edgecolor": ENCRE_SECONDAIRE, "axes.labelcolor": ENCRE,
        "xtick.color": ENCRE_SECONDAIRE, "ytick.color": ENCRE_SECONDAIRE,
        "text.color": ENCRE, "font.size": 9,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.color": "#e4e3df", "grid.linewidth": 0.6,
        "axes.axisbelow": True, "legend.frameon": False,
    })
    return plt.subplots(lignes, colonnes, figsize=(largeur, hauteur), squeeze=False)


def enregistrer(fig, nom: str) -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    # Un titre général prend sa place au-dessus des panneaux, sans les chevaucher.
    fig.tight_layout(rect=(0, 0, 1, 0.97) if fig._suptitle else None)
    fig.savefig(FIGURES / f"{nom}.png", dpi=130)
    plt.close(fig)
    print(f"  sorties/figures/{nom}.png")


# ---------------------------------------------------------------------------
# Règle de citation des points 4, 5, 7 et 8.
# Un effet se cite si sa case ET sa case de référence ont :
#   au moins 10 suppressions ;
#   réparties sur au moins 5 fiches ;
#   et aucune fiche ne porte plus du quart de ces suppressions.
# Seuils du 2026-09-30. Ceux du 2026-09-29 (20 suppressions, 10 fiches), jugés
# trop stricts par Romain, écartaient des cases à 14 suppressions sur 13 fiches.
# ---------------------------------------------------------------------------
MIN_SUPPRESSIONS_CITABLE = 10
MIN_FICHES_CITABLE = 5
PART_MAX_PREMIERE_FICHE = 0.25


def effectifs(d: pd.DataFrame, evenement: str = "y") -> dict:
    """Les effectifs d'une case : lignes, suppressions, fiches et enseignes touchées.

    `d` contient les lignes de la case, avec `cid`, `enseigne` et la colonne
    `evenement` (1 = l'avis disparaît). `citable` applique la règle ci-dessus
    à la case seule ; la comparaison à la référence se fait dans chaque script.
    """
    touchees = d[d[evenement] == 1]
    n = int(len(touchees))
    par_fiche = touchees.groupby("cid").size()
    part = float(par_fiche.max() / n) if n else None
    return {
        "lignes": int(len(d)),
        # Avis distincts : un avis suivi 10 jours fait 10 lignes et compte 1 avis.
        "avis": int(d["review_id"].nunique()) if "review_id" in d else None,
        "suppressions": n,
        "fiches_touchees": int(par_fiche.size),
        "enseignes_touchees": int(touchees["enseigne"].nunique()),
        "part_de_la_premiere_fiche": round(part, 2) if part is not None else None,
        "citable": bool(n >= MIN_SUPPRESSIONS_CITABLE and par_fiche.size >= MIN_FICHES_CITABLE
                        and part is not None and part <= PART_MAX_PREMIERE_FICHE),
    }
