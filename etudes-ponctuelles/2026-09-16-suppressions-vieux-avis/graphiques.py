#!/usr/bin/env python3
"""Les quatre figures du rapport, depuis les CSV de sorties/.

Couleurs : slots 1 et 2 de la palette de référence du projet — bleu #2a78d6
pour la série, orange #eb6834 pour la valeur mise en avant. Une seule série par
figure, donc pas de légende ; la figure 4 en porte une parce qu'elle compare
deux groupes.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

SORTIES = Path(__file__).resolve().parent / "sorties"
FIGURES = SORTIES / "figures"

BLEU, ORANGE = "#2a78d6", "#eb6834"
ENCRE, ENCRE_DOUCE = "#0b0b0b", "#52514e"
FOND = "#ffffff"

plt.rcParams.update({
    "figure.facecolor": FOND, "axes.facecolor": FOND,
    "font.size": 10.5, "font.family": "DejaVu Sans",
    "axes.edgecolor": "#d8d7d2", "axes.labelcolor": ENCRE_DOUCE,
    "xtick.color": ENCRE_DOUCE, "ytick.color": ENCRE_DOUCE,
    "axes.titlecolor": ENCRE, "axes.titlesize": 12, "axes.titleweight": "bold",
})


def habiller(ax, titre, sous_titre=None):
    ax.set_title(titre, loc="left", pad=30 if sous_titre else 10)
    if sous_titre:
        ax.text(0, 1.025, sous_titre, transform=ax.transAxes,
                fontsize=9.5, color=ENCRE_DOUCE, va="bottom")
    for cote in ("top", "right"):
        ax.spines[cote].set_visible(False)
    ax.grid(axis="y", color="#eceae5", linewidth=0.8)
    ax.set_axisbelow(True)


def figure1() -> Path:
    df = pd.read_csv(SORTIES / "E1-age-a-la-suppression.csv")
    df["libelle"] = df["age_a_la_suppression"].str.slice(3)
    fig, ax = plt.subplots(figsize=(9.2, 4.6))
    couleurs = [ORANGE if v == df["supprimes_pour_10000_avis"].max() else BLEU
                for v in df["supprimes_pour_10000_avis"]]
    barres = ax.bar(df["libelle"], df["supprimes_pour_10000_avis"],
                    color=couleurs, width=0.62)
    for barre, valeur in zip(barres, df["supprimes_pour_10000_avis"]):
        ax.text(barre.get_x() + barre.get_width() / 2, valeur + 3, f"{valeur:,.0f}".replace(",", " "),
                ha="center", fontsize=9.5, color=ENCRE)
    habiller(ax, "Un avis de quatre à sept jours est celui qui disparaît le plus",
             "Sur 10 000 avis ayant cet âge pendant le suivi, combien ont disparu")
    ax.set_ylim(0, df["supprimes_pour_10000_avis"].max() * 1.16)
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)
    plt.xticks(rotation=18, ha="right")
    fig.tight_layout()
    chemin = FIGURES / "figure1-age.png"
    fig.savefig(chemin, dpi=170)
    plt.close(fig)
    return chemin


def figure2() -> Path:
    df = pd.read_csv(SORTIES / "E2-quinze-premiers-jours.csv")
    fig, ax = plt.subplots(figsize=(9.2, 4.4))
    couleurs = [ORANGE if a in (6, 7) else BLEU for a in df["age_en_jours"]]
    ax.bar(df["age_en_jours"], df["pour_10000_exposes"], color=couleurs, width=0.64)
    for a, v in zip(df["age_en_jours"], df["pour_10000_exposes"]):
        if a in (6, 7, 2, 14):
            ax.text(a, v + 3.5, f"{v:,.0f}".replace(",", " "), ha="center",
                    fontsize=9.5, color=ENCRE)
    habiller(ax, "Le septième jour de vie concentre les suppressions",
             "Avis disparus pour 10 000 avis en ligne à cet âge, sur les quinze premiers jours")
    ax.set_xlabel("âge de l'avis, en jours")
    ax.set_xticks(range(0, 16))
    ax.set_ylim(0, df["pour_10000_exposes"].max() * 1.16)
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)
    fig.tight_layout()
    chemin = FIGURES / "figure2-quinze-jours.png"
    fig.savefig(chemin, dpi=170)
    plt.close(fig)
    return chemin


def figure3() -> Path:
    df = pd.read_csv(SORTIES / "C1-vieux-par-jour.csv")
    df["jour"] = pd.to_datetime(df["supprime_le"]).dt.strftime("%d/%m")
    fig, ax = plt.subplots(figsize=(9.2, 4.4))
    couleurs = [ORANGE if v == df["suppressions"].max() else BLEU for v in df["suppressions"]]
    barres = ax.bar(df["jour"], df["suppressions"], color=couleurs, width=0.62)
    for barre, v in zip(barres, df["suppressions"]):
        ax.text(barre.get_x() + barre.get_width() / 2, v + 7, f"{v:.0f}",
                ha="center", fontsize=9.5, color=ENCRE)
    habiller(ax, "Les vieux avis tombent surtout le 17 août",
             "Avis de plus d'un an disparus, jour par jour du suivi")
    ax.set_ylim(0, df["suppressions"].max() * 1.16)
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)
    fig.tight_layout()
    chemin = FIGURES / "figure3-vieux-par-jour.png"
    fig.savefig(chemin, dpi=170)
    plt.close(fig)
    return chemin


def figure4() -> Path:
    df = pd.read_csv(SORTIES / "G4-note.csv")
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 4.2))
    titres = {"recents": "Avis de 30 jours ou moins", "vieux": "Avis de plus de 30 jours"}
    for ax, groupe in zip(axes, ["recents", "vieux"]):
        d = df[df["groupe"] == groupe].sort_values("note")
        couleurs = [ORANGE if n == 5 else BLEU for n in d["note"]]
        ax.bar(d["note"], d["pour_10000_avis"], color=couleurs, width=0.62)
        # Une décimale quand les valeurs sont petites : sans elle, 5,2 et 5,1
        # s'affichent tous deux « 5 » sur des barres de hauteurs différentes.
        gabarit = "{:,.1f}" if d["pour_10000_avis"].max() < 20 else "{:,.0f}"
        for n, v in zip(d["note"], d["pour_10000_avis"]):
            ax.text(n, v + d["pour_10000_avis"].max() * 0.035,
                    gabarit.format(v).replace(",", " ").replace(".", ","),
                    ha="center", fontsize=9, color=ENCRE)
        ax.set_title(titres[groupe], loc="left", fontsize=11)
        for cote in ("top", "right", "left"):
            ax.spines[cote].set_visible(False)
        ax.grid(axis="y", color="#eceae5", linewidth=0.8)
        ax.set_axisbelow(True)
        ax.set_yticks([])
        ax.set_xticks([1, 2, 3, 4, 5])
        ax.set_xlabel("note de l'avis")
        ax.set_ylim(0, d["pour_10000_avis"].max() * 1.2)
    fig.suptitle("La courbe descend jusqu'à 3 ou 4 étoiles, puis remonte en 5",
                 x=0.012, ha="left", fontsize=12, fontweight="bold", color=ENCRE)
    fig.text(0.012, 0.905, "Sur 10 000 avis de cette note et de cet âge, combien ont disparu pendant le suivi. "
             "Les deux échelles diffèrent.",
             fontsize=9.5, color=ENCRE_DOUCE)
    fig.tight_layout(rect=[0, 0, 1, 0.88])
    chemin = FIGURES / "figure4-note.png"
    fig.savefig(chemin, dpi=170)
    plt.close(fig)
    return chemin


def main() -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    for fabrique in (figure1, figure2, figure3, figure4):
        print("écrit :", fabrique().name)


if __name__ == "__main__":
    main()
