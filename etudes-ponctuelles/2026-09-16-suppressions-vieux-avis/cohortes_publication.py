#!/usr/bin/env python3
"""Le taux de suppression selon la date de publication de l'avis.

    python etudes-ponctuelles/2026-09-16-suppressions-vieux-avis/cohortes_publication.py

Question posée par Matthieu le 2026-09-16 : les avis publiés à certaines dates
se font-ils supprimer davantage pendant les quatorze jours de suivi ?

Une cohorte de publication réunit les avis parus le même jour ou le même mois.
Son taux est la part d'entre eux qui a disparu pendant le suivi. Le dénominateur
ne contient que les avis encore en ligne au 11 août : ceux qui avaient déjà été
retirés avant le premier passage du robot sont invisibles, ce qui sous-estime
les cohortes anciennes.

Définition d'une suppression : `suppressions_corrigees.py`, importée telle
quelle — absence de deux jours ou plus, bugs d'édition retirés.

Sorties : trois figures dans sorties/figures/ et trois CSV dans sorties/.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.dates as mdates  # noqa: E402

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "outils"))
sys.path.insert(0, str(RACINE / "etude-exploratoire" / "scripts"))

from local import connexion  # noqa: E402
from suppressions_corrigees import creer_vue_avis  # noqa: E402

SORTIES = Path(__file__).resolve().parent / "sorties"
FIGURES = SORTIES / "figures"

BLEU, ORANGE = "#2a78d6", "#eb6834"
ENCRE, ENCRE_DOUCE = "#0b0b0b", "#52514e"

plt.rcParams.update({
    "figure.facecolor": "#ffffff", "axes.facecolor": "#ffffff",
    "font.size": 10.5, "font.family": "DejaVu Sans",
    "axes.edgecolor": "#d8d7d2", "axes.labelcolor": ENCRE_DOUCE,
    "xtick.color": ENCRE_DOUCE, "ytick.color": ENCRE_DOUCE,
    "axes.titlecolor": ENCRE, "axes.titlesize": 12, "axes.titleweight": "bold",
})

# Un mois compte quand il porte assez d'avis pour qu'un taux veuille dire
# quelque chose. Sous ce seuil, une seule suppression déplace la courbe de
# plusieurs points.
SEUIL_MOIS = 2000
PREMIERE_ANNEE = 2016


def habiller(ax, titre, sous_titre):
    ax.set_title(titre, loc="left", pad=34)
    ax.text(0, 1.025, sous_titre, transform=ax.transAxes, fontsize=9.5,
            color=ENCRE_DOUCE, va="bottom")
    for cote in ("top", "right"):
        ax.spines[cote].set_visible(False)
    ax.grid(axis="y", color="#eceae5", linewidth=0.8)
    ax.set_axisbelow(True)


def preparer(con):
    creer_vue_avis(con, source="reviews")

    # Les six enseignes signalées, repérées par leur cid dans le panel puis
    # appliquées à tout le corpus.
    con.execute("""
    CREATE OR REPLACE VIEW enseignes AS
    SELECT DISTINCT cid FROM reviews_panel_features
    WHERE chaine_antiparasitaire_us OR salle_de_sport_attaquee
    """)
    con.execute("""
    CREATE OR REPLACE VIEW cohortes AS
    SELECT CAST(a.created_at AS DATE) AS publie_le,
           date_trunc('month', CAST(a.created_at AS DATE)) AS mois,
           YEAR(CAST(a.created_at AS DATE)) AS annee,
           a.death_at IS NOT NULL AS supprime,
           a.cid,
           e.cid IS NOT NULL AS enseigne_signalee
    FROM avis a LEFT JOIN enseignes e USING (cid)
    WHERE CAST(a.created_at AS DATE) < DATE '2026-08-11'
    """)


def figure_a(con):
    """Le gradient, mois par mois, sur une échelle qui tient trois ordres de grandeur."""
    # Au trimestre : au mois, les cohortes de 2016 à 2020 tombent souvent à
    # zéro suppression, ce qu'une échelle logarithmique ne peut pas tracer.
    df = con.execute(f"""
    SELECT date_trunc('quarter', publie_le) AS trimestre,
           COUNT(*) AS avis,
           SUM(supprime::INT) AS supprimes,
           ROUND(10000.0 * AVG(supprime::INT), 2) AS pour_10000,
           ROUND(10000.0 * AVG(CASE WHEN enseigne_signalee THEN NULL
                                    ELSE supprime::INT END), 2) AS pour_10000_sans_enseignes
    FROM cohortes WHERE annee >= {PREMIERE_ANNEE}
    GROUP BY 1 HAVING SUM(supprime::INT) > 0 ORDER BY 1
    """).df()
    df.to_csv(SORTIES / "H1-taux-par-trimestre-de-publication.csv", index=False)

    fig, ax = plt.subplots(figsize=(9.6, 4.8))
    ax.plot(df["trimestre"], df["pour_10000"], color=BLEU, linewidth=2, label="tous les avis")
    ax.plot(df["trimestre"], df["pour_10000_sans_enseignes"], color=ORANGE, linewidth=2,
            linestyle=(0, (5, 2)), label="sans les six enseignes signalées")
    ax.set_yscale("log")
    ax.set_yticks([1, 2, 5, 10, 20, 50, 100, 200, 500])
    ax.set_yticklabels(["1", "2", "5", "10", "20", "50", "100", "200", "500"])
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    habiller(ax, "Plus un avis est ancien, moins il disparaît",
             "Avis disparus pendant le suivi pour 10 000 avis publiés ce trimestre-là. "
             "Échelle multipliée par 10 à chaque graduation.")
    ax.legend(frameon=False, loc="upper left", fontsize=9.5)
    ax.set_xlabel("trimestre de publication de l'avis")
    fig.tight_layout()
    fig.savefig(FIGURES / "figure5-cohortes-par-trimestre.png", dpi=170)
    plt.close(fig)
    return df


def figure_b(con):
    """Le même gradient par année, sur une échelle droite."""
    df = con.execute(f"""
    SELECT annee, COUNT(*) AS avis, SUM(supprime::INT) AS supprimes,
           ROUND(10000.0 * AVG(supprime::INT), 1) AS pour_10000
    FROM cohortes WHERE annee BETWEEN {PREMIERE_ANNEE} AND 2025 GROUP BY 1 ORDER BY 1
    """).df()
    df.to_csv(SORTIES / "H2-taux-par-annee-de-publication.csv", index=False)

    fig, ax = plt.subplots(figsize=(9.6, 4.6))
    couleurs = [ORANGE if a == 2025 else BLEU for a in df["annee"]]
    barres = ax.bar(df["annee"].astype(str), df["pour_10000"], color=couleurs, width=0.62)
    for barre, valeur in zip(barres, df["pour_10000"]):
        ax.text(barre.get_x() + barre.get_width() / 2, valeur + 1.2,
                str(valeur).replace(".", ","), ha="center", fontsize=9.5, color=ENCRE)
    habiller(ax, "Le risque continue de baisser bien au-delà d'un an",
             "Avis disparus pendant le suivi pour 10 000 avis publiés cette année-là. "
             "2026 est retirée : à 50,7, elle écraserait l'échelle.")
    ax.set_ylim(0, df["pour_10000"].max() * 1.30)
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)
    ax.set_xlabel("année de publication de l'avis")
    ax.text(0, df["pour_10000"].max() * 0.84,
            "Un avis publié en 2025 disparaît {} fois plus souvent\n"
            "qu'un avis publié en 2016.".format(
                ("%.1f" % (df["pour_10000"].iloc[-1] / df["pour_10000"].iloc[0])).replace(".", ",")),
            fontsize=9.5, color=ENCRE_DOUCE)
    fig.tight_layout()
    fig.savefig(FIGURES / "figure6-cohortes-par-annee.png", dpi=170)
    plt.close(fig)
    return df


def figure_c(con):
    """Les cohortes anciennes seules : y a-t-il un mois qui sort du lot ?"""
    df = con.execute(f"""
    SELECT mois, COUNT(*) AS avis, SUM(supprime::INT) AS supprimes,
           ROUND(10000.0 * AVG(supprime::INT), 2) AS pour_10000,
           COUNT(DISTINCT cid) FILTER (supprime) AS fiches_touchees
    FROM cohortes WHERE annee BETWEEN {PREMIERE_ANNEE} AND 2024
    GROUP BY 1 HAVING COUNT(*) >= {SEUIL_MOIS} ORDER BY 1
    """).df()
    df.to_csv(SORTIES / "H3-cohortes-anciennes.csv", index=False)

    moyenne = 10000.0 * df["supprimes"].sum() / df["avis"].sum()
    fig, ax = plt.subplots(figsize=(9.6, 4.6))
    ax.bar(df["mois"], df["pour_10000"], color=BLEU, width=22)
    ax.axhline(moyenne, color=ORANGE, linewidth=2, linestyle=(0, (5, 2)))
    ax.set_ylim(0, df["pour_10000"].max() * 1.22)
    ax.text(df["mois"].iloc[0], df["pour_10000"].max() * 1.12,
            "ligne orange : moyenne de la période, {} pour 10 000".format(
                ("%.1f" % moyenne).replace(".", ",")),
            fontsize=9.5, color=ORANGE)
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    habiller(ax, "La montée est régulière, aucun mois ne sort du lot",
             "Avis publiés de 2016 à 2024, disparus pendant le suivi, pour 10 000 avis du mois. "
             "La pente de droite est l'effet de l'âge.")
    ax.set_xlabel("mois de publication de l'avis")
    ax.set_ylabel("pour 10 000 avis")
    fig.tight_layout()
    fig.savefig(FIGURES / "figure7-cohortes-anciennes.png", dpi=170)
    plt.close(fig)
    return df, moyenne


def figure_d(con):
    """Les mêmes cohortes anciennes, en nombre d'avis perdus.

    La figure C rapporte les suppressions au volume du mois. Celle-ci compte
    les avis, sans dénominateur : elle dit combien de suppressions chaque
    génération d'avis a réellement fournies. Le périmètre est le même, et sur
    2016-2024 les 108 mois passent tous le seuil de volume.
    """
    df = con.execute(f"""
    SELECT mois, COUNT(*) AS avis, SUM(supprime::INT) AS supprimes,
           COUNT(DISTINCT cid) FILTER (supprime) AS fiches_touchees
    FROM cohortes WHERE annee BETWEEN {PREMIERE_ANNEE} AND 2024
    GROUP BY 1 HAVING COUNT(*) >= {SEUIL_MOIS} ORDER BY 1
    """).df()
    df.to_csv(SORTIES / "H4-cohortes-anciennes-en-volume.csv", index=False)

    moyenne = df["supprimes"].mean()
    fig, ax = plt.subplots(figsize=(9.6, 4.6))
    couleurs = [ORANGE if v == df["supprimes"].max() else BLEU for v in df["supprimes"]]
    ax.bar(df["mois"], df["supprimes"], color=couleurs, width=22)
    ax.axhline(moyenne, color="#8a8a86", linewidth=1.6, linestyle=(0, (5, 2)))
    ax.set_ylim(0, df["supprimes"].max() * 1.24)
    ax.text(df["mois"].iloc[0], df["supprimes"].max() * 1.13,
            "ligne grise : moyenne de la période, {} suppressions par mois de publication".format(
                ("%.1f" % moyenne).replace(".", ",")),
            fontsize=9.5, color="#6f6f6b")
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    habiller(ax, "En nombre d'avis, les générations récentes pèsent bien plus",
             "Avis publiés de 2016 à 2024 et disparus pendant le suivi, comptés par mois "
             "de publication. Aucun dénominateur.")
    ax.set_xlabel("mois de publication de l'avis")
    ax.set_ylabel("avis disparus")
    fig.tight_layout()
    fig.savefig(FIGURES / "figure8-cohortes-anciennes-volume.png", dpi=170)
    plt.close(fig)
    return df


def main() -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    con = connexion(memoire="8GB")
    preparer(con)

    a = figure_a(con)
    b = figure_b(con)
    c, moyenne = figure_c(con)
    d = figure_d(con)

    print("figure5-cohortes-par-trimestre.png :", len(a), "trimestres")
    print("figure6-cohortes-par-annee.png   :", len(b), "années")
    print("figure7-cohortes-anciennes.png   :", len(c), "mois de 2016 à 2024")
    print("\nCohortes anciennes : moyenne {:.1f} pour 10 000, "
          "du plus calme au plus touché {:.1f} à {:.1f}".format(
              moyenne, c["pour_10000"].min(), c["pour_10000"].max()))
    print("figure8-cohortes-anciennes-volume.png :", len(d), "mois, en nombre d'avis")

    print("\nLes cinq mois anciens les plus touchés, en part :")
    print(c.nlargest(5, "pour_10000").to_string(index=False))
    print("\nLes cinq mois anciens les plus touchés, en nombre d'avis :")
    print(d.nlargest(5, "supprimes").to_string(index=False))
    print("\nTotal des suppressions sur les cohortes 2016-2024 : {} avis, "
          "soit {:.0f} par mois en moyenne.".format(d["supprimes"].sum(), d["supprimes"].mean()))


if __name__ == "__main__":
    main()
