#!/usr/bin/env python3
"""Avis 4 et 5 étoiles perdus sur deux semaines, rapportés aux avis 4 et 5 étoiles
gagnés sur les mêmes deux semaines, par secteur et par taille d'entreprise.

    PYTHONPATH=".venv/Lib/site-packages;outils" <python uv> etudes-ponctuelles/2026-10-02-pertes-secteur-taille/calcul.py

Demande de Matthieu du 2026-10-02 (« ce mois-ci j'ai collecté X avis et j'en ai
perdu Y », Axel).

  corpus        data/bigquery/reviews_doublons_cleaned_all.parquet, avis 4 et
                5 étoiles.
  deux semaines du 11 août (premier relevé) au 24 août (dernier relevé) 2026.
  numérateur    avis 4 et 5 étoiles dont la disparition est notée pendant les
                deux semaines (`deleted_detected_at`), quelle que soit leur date
                de publication.
  dénominateur  avis 4 et 5 étoiles publiés pendant les deux semaines
                (`created_at` du 11 au 24 août).
  fiches        les 3 fiches qui ne sont plus relevées avant le 24 août sont
                écartées, comme dans `2026-10-02-flux-4-5-etoiles`.
  taille        `businesses.bucket` : mono (un établissement), small (groupe de
                4 à 10), large (groupe de 20 à 50).

Toutes les fiches, enseignes comprises.

Sorties : livrables/restitution_finale/graphiques/pertes_secteur_taille.png (la
matrice imprimée) et livrables/restitution_finale/donnees/pertes_secteur_taille.csv, une
ligne par case, total par ligne et par colonne compris.
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "outils"))
from local import connexion  # noqa: E402

FINALE = RACINE / "livrables" / "restitution_finale"
DONNEES = FINALE / "donnees" / "pertes_secteur_taille.csv"
MATRICE = FINALE / "graphiques" / "pertes_secteur_taille.png"
ENCRE, ENCRE_2, GRILLE, FOND, GRIS_TOTAL = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb", "#ecebe7"
DEBUT, FIN = "2026-08-11", "2026-08-24"

SECTEURS = {"automotive": "Automobile", "food_beverage": "Restauration",
            "healthcare": "Santé", "home_services": "Services à domicile",
            "hospitality": "Hôtellerie", "travel": "Voyage",
            "wellness_fitness": "Sport et bien-être"}
TAILLES = {"mono": "Mono", "small": "Small", "large": "Large"}

SQL = f"""
WITH fin_suivi AS (
  SELECT cid, max(CAST(last_seen_at AS DATE)) AS fin_suivi
  FROM reviews_doublons_cleaned_all GROUP BY cid
),
avis AS (
  SELECT b.industry, b.bucket,
         CAST(r.created_at AS DATE)          AS publie,
         CAST(r.deleted_detected_at AS DATE) AS disparu
  FROM reviews_doublons_cleaned_all r
  JOIN fin_suivi f USING (cid)
  JOIN businesses b ON b.cid = r.cid
  WHERE r.star >= 4 AND f.fin_suivi = DATE '{FIN}'
)
SELECT industry, bucket,
       COUNT(*) FILTER (disparu BETWEEN DATE '{DEBUT}' AND DATE '{FIN}') AS perdus,
       COUNT(*) FILTER (publie  BETWEEN DATE '{DEBUT}' AND DATE '{FIN}') AS nouveaux
FROM avis
GROUP BY CUBE (industry, bucket)
"""


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    con = connexion("4GB")
    con.execute("SET threads=4")
    cases = {(i, b): (p, n) for i, b, p, n in con.execute(SQL).fetchall()}
    inconnus = {k for k in cases if (k[0] is not None and k[0] not in SECTEURS)
                or (k[1] is not None and k[1] not in TAILLES)}
    if inconnus:
        raise SystemExit(f"secteur ou taille inattendus : {inconnus}")

    lignes = list(SECTEURS) + [None]
    colonnes = list(TAILLES) + [None]
    DONNEES.parent.mkdir(parents=True, exist_ok=True)
    with DONNEES.open("w", encoding="utf-8") as f:
        f.write("secteur,taille,avis_4_5_perdus,avis_4_5_nouveaux,perdus_pour_100_nouveaux\n")
        for i in lignes:
            for b in colonnes:
                p, n = cases.get((i, b), (0, 0))
                taux = f"{100 * p / n:.1f}" if n else ""
                f.write(f"{SECTEURS.get(i, 'Total')},{TAILLES.get(b, 'Total')},{p},{n},{taux}\n")
    for i in lignes:
        cellules = []
        for b in colonnes:
            p, n = cases.get((i, b), (0, 0))
            cellules.append(f"{p:>5} / {n:>5} = {100 * p / n:5.1f} %" if n else "—")
        print(f"{SECTEURS.get(i, 'Total'):20s} | " + " | ".join(cellules))
    matrice(cases, lignes, colonnes)
    print(f"\nécrit : {DONNEES}\nécrit : {MATRICE}")
    return 0


def nombre(n: int) -> str:
    return f"{n:,}".replace(",", " ")


def teinte(t: float, t_max: float) -> tuple:
    """Fond de case : du presque blanc au bleu moyen de la rampe dataviz (pas 350),
    assez clair pour garder le texte en encre."""
    a = np.array(matplotlib.colors.to_rgb("#f2f7fd"))
    b = np.array(matplotlib.colors.to_rgb("#5598e7"))
    return tuple(a + (b - a) * min(t / t_max, 1))


TITRE = "Avis 4 et 5 étoiles perdus, rapportés aux avis 4 et 5 étoiles publiés, du 11 au 24 août 2026"
SOUS_TITRE = ("Dans chaque case : part (avis perdus / avis publiés). Plus la case est "
              "foncée, plus la part est élevée.")


def matrice(cases: dict, lignes: list, colonnes: list, chemin: Path = MATRICE,
            titre: str = TITRE, sous_titre: str = SOUS_TITRE,
            t_max: float | None = None) -> None:
    """La matrice imprimée : part en gros, (perdus / nouveaux) dessous. `t_max` fixe la
    case la plus foncée, pour que plusieurs matrices partagent la même échelle."""
    entetes = ["Mono\nun établissement", "Small\ngroupe de 4 à 10",
               "Large\ngroupe de 20 à 50", "Total"]
    if t_max is None:
        t_max = max(100 * p / n for (i, b), (p, n) in cases.items()
                    if n and i is not None and b is not None)
    larg_sect, larg_case, haut_ent, haut = 2.1, 1.75, 0.62, 0.56
    largeur = larg_sect + larg_case * len(colonnes)
    hauteur = haut_ent + haut * len(lignes)
    fig = plt.figure(figsize=(largeur + 0.3, hauteur + 1.2), dpi=150)
    fig.patch.set_facecolor(FOND)
    ax = fig.add_axes((0.15 / (largeur + 0.3), 0.15 / (hauteur + 1.2),
                       largeur / (largeur + 0.3), hauteur / (hauteur + 1.2)))
    ax.set_xlim(0, largeur)
    ax.set_ylim(hauteur, 0)
    ax.axis("off")

    for k, texte in enumerate(entetes):
        x = larg_sect + larg_case * (k + 0.5)
        entete, *detail = texte.split("\n")
        ax.text(x, haut_ent * 0.38, entete, ha="center", va="center", fontsize=9,
                color=ENCRE, fontweight="bold")
        if detail:
            ax.text(x, haut_ent * 0.75, detail[0], ha="center", va="center",
                    fontsize=7, color=ENCRE_2)
    for r, i in enumerate(lignes):
        y = haut_ent + haut * r
        total_ligne = i is None
        ax.text(0.08, y + haut / 2, SECTEURS.get(i, "Total"), ha="left", va="center",
                fontsize=8.5, color=ENCRE, fontweight="bold" if total_ligne else "normal")
        for k, b in enumerate(colonnes):
            x = larg_sect + larg_case * k
            p, n = cases.get((i, b), (0, 0))
            total = total_ligne or b is None
            fond = GRIS_TOTAL if total else (teinte(100 * p / n, t_max) if n else FOND)
            ax.add_patch(Rectangle((x + 0.03, y + 0.03), larg_case - 0.06, haut - 0.06,
                                   facecolor=fond, edgecolor="none"))
            if not n:
                ax.text(x + larg_case / 2, y + haut / 2, "—", ha="center", va="center",
                        fontsize=9, color=ENCRE_2)
                continue
            ax.text(x + larg_case / 2, y + haut * 0.38,
                    f"{100 * p / n:.1f}".replace(".", ",") + " %", ha="center",
                    va="center", fontsize=9.5, color=ENCRE,
                    fontweight="bold" if total else "normal")
            ax.text(x + larg_case / 2, y + haut * 0.72, f"({nombre(p)} / {nombre(n)})",
                    ha="center", va="center", fontsize=7, color=ENCRE_2)
        ax.plot([0, largeur], [y, y], color=GRILLE, lw=0.6)

    fig.text(0.15 / (largeur + 0.3), 1 - 0.12 / (hauteur + 1.2),
             titre, va="top", fontsize=11, color=ENCRE)
    fig.text(0.15 / (largeur + 0.3), 1 - 0.5 / (hauteur + 1.2),
             sous_titre, va="top", fontsize=8, color=ENCRE_2)
    chemin.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(chemin, facecolor=FOND)
    plt.close(fig)


if __name__ == "__main__":
    raise SystemExit(main())
