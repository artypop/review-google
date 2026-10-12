#!/usr/bin/env python3
"""Le pic au 7e jour : nombre d'avis 4-5 étoiles supprimés selon leur âge, du 1er
au 13e jour.

    PYTHONPATH=".venv/Lib/site-packages;outils" <python uv> etudes-ponctuelles/2026-10-05-pic-7e-jour/calcul.py

Demande de Matthieu du 2026-10-05, pour la partie 5 de la consolidation (remplace
la courbe de survie). 13 jours : le nombre d'intervalles entre les 14 passages.

  corpus      data/bigquery/reviews_doublons_cleaned_all.parquet, avis 4 et 5
              étoiles. Un avis disparu est un avis supprimé (doublons et
              clignotements déjà retirés).
  âge         jours entre la publication et le passage qui constate la
              disparition (`deleted_detected_at`).
  fiches      les 3 fiches qui ne sont plus relevées avant le 24 août sont
              écartées, comme dans les autres calculs de taux.

Pourquoi des nombres bruts se comparent d'un âge à l'autre : pendant les 13 jours
de suivi, le robot observe à chaque âge à peu près le même nombre d'avis en ligne
(environ 28 000 du 2e au 13e jour), parce que chaque âge est vu pour 13 à 14
jours de publication différents. Le script l'imprime (`avis_observes`). Seul le
1er jour en voit beaucoup moins : un avis n'est vu le jour même de sa
publication que s'il est publié avant le passage du robot.

Sorties : livrables/restitution_finale/graphiques/pic_suppressions_par_jour.png
et livrables/restitution_finale/donnees/pic_suppressions_par_jour.csv.

LA VERSION EN TAUX (pic_taux_suppression_par_jour.png et .csv)
Corpus demandé par Matthieu le 2026-10-05 : les seuls avis publiés pendant les
vagues (à partir du 11 août), du 1er au 12e jour. Avec ce corpus, le nombre
d'avis observés baisse avec l'âge (un avis publié le 20 août n'atteint pas son
8e jour avant le 24) : seul le taux se compare d'un âge à l'autre.
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "outils"))
from local import DERNIERE_VAGUE, connexion  # noqa: E402

FINALE = RACINE / "livrables" / "restitution_finale"
DONNEES = FINALE / "donnees" / "pic_suppressions_par_jour.csv"
GRAPHIQUE = FINALE / "graphiques" / "pic_suppressions_par_jour.png"
# En taux : supprimés pour 1 000 avis observés en ligne à cet âge, avis publiés
# pendant les vagues, 12 jours (demande de Matthieu du 2026-10-05).
GRAPHIQUE_TAUX = FINALE / "graphiques" / "pic_taux_suppression_par_jour.png"
DONNEES_TAUX = FINALE / "donnees" / "pic_taux_suppression_par_jour.csv"
JOURS = 13
JOURS_TAUX = 12
DEBUT_TAUX = "2026-08-11"
# Palette de référence du skill dataviz, comme les autres graphiques de la restitution.
BLEU_PIC, BLEU, ENCRE, ENCRE_2, GRILLE, FOND = ("#2a78d6", "#9ec5f4", "#0b0b0b", "#52514e",
                                                "#e4e3df", "#fcfcfb")

SQL = """
WITH fin_suivi AS (
  SELECT cid, max(CAST(last_seen_at AS DATE)) AS fin_suivi
  FROM reviews_doublons_cleaned_all GROUP BY cid
),
avis AS (
  SELECT CAST(r.created_at AS DATE)          AS publie,
         CAST(r.first_seen_at AS DATE)       AS vu,
         CAST(r.deleted_detected_at AS DATE) AS disparu
  FROM reviews_doublons_cleaned_all r JOIN fin_suivi f USING (cid)
  WHERE r.star >= 4 AND f.fin_suivi = DATE '{derniere}'
    AND CAST(r.created_at AS DATE) >= DATE '{debut}'
),
ages AS (SELECT range::INTEGER AS age FROM range(1, {jours} + 1))
SELECT a.age,
       count(*) FILTER (publie + a.age > vu
                        AND publie + a.age <= coalesce(disparu, DATE '{derniere}'))
                                                            AS avis_observes,
       count(*) FILTER (date_diff('day', publie, disparu) = a.age) AS supprimes
FROM avis, ages a
GROUP BY a.age ORDER BY a.age
"""


def nombre(n: int) -> str:
    return f"{n:,}".replace(",", " ")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    con = connexion("6GB")
    lignes = con.execute(SQL.format(derniere=DERNIERE_VAGUE, debut="2026-07-01",
                                    jours=JOURS)).fetchall()
    DONNEES.parent.mkdir(parents=True, exist_ok=True)
    with DONNEES.open("w", encoding="utf-8") as fh:
        fh.write("age_jours,avis_observes,supprimes,risque_pour_1000\n")
        for age, n, s in lignes:
            fh.write(f"{age},{n},{s},{1000 * s / n:.2f}\n")
            print(f"jour {age:>2} : {nombre(s):>5} supprimés sur {nombre(n):>7} avis observés "
                  f"({1000 * s / n:5.2f} ‰)")
    total = sum(s for _, _, s in lignes)
    pic = sum(s for a, _, s in lignes if a in (6, 7))
    print(f"total {total}, dont 6e et 7e jours : {pic} ({100 * pic / total:.0f} %)")
    graphique(lignes, pic, total)

    print(f"\n== Taux : avis publiés à partir du {DEBUT_TAUX}, {JOURS_TAUX} jours ==")
    lignes_taux = con.execute(SQL.format(derniere=DERNIERE_VAGUE, debut=DEBUT_TAUX,
                                         jours=JOURS_TAUX)).fetchall()
    with DONNEES_TAUX.open("w", encoding="utf-8") as fh:
        fh.write("age_jours,avis_observes,supprimes,taux_pour_1000\n")
        for age, n, s in lignes_taux:
            fh.write(f"{age},{n},{s},{1000 * s / n:.2f}\n")
            print(f"jour {age:>2} : {nombre(s):>5} supprimés sur {nombre(n):>7} avis observés "
                  f"({1000 * s / n:5.2f} ‰)")
    graphique_taux(lignes_taux)
    print(f"\nécrit : {DONNEES}\nécrit : {GRAPHIQUE}\nécrit : {DONNEES_TAUX}\nécrit : {GRAPHIQUE_TAUX}")
    return 0


def graphique(lignes: list, pic: int, total: int) -> None:
    ages = [a for a, _, _ in lignes]
    supprimes = [s for _, _, s in lignes]
    fig, ax = plt.subplots(figsize=(8.5, 4.2), dpi=150)
    fig.patch.set_facecolor(FOND)
    ax.set_facecolor(FOND)
    couleurs = [BLEU_PIC if a in (6, 7) else BLEU for a in ages]
    ax.bar(ages, supprimes, width=0.72, color=couleurs, edgecolor=FOND, linewidth=1, zorder=3)
    for a, s in zip(ages, supprimes):
        ax.text(a, s + max(supprimes) * 0.015, nombre(s), ha="center", va="bottom",
                fontsize=8, color=ENCRE, fontweight="bold" if a in (6, 7) else "normal", zorder=4)
    ax.set_xticks(ages)
    ax.set_xticklabels([f"{a}e" if a > 1 else "1er" for a in ages])
    ax.set_xlim(0.4, len(ages) + 0.6)
    ax.set_ylim(0, max(supprimes) * 1.12)
    ax.tick_params(colors=ENCRE_2, labelsize=8.5, length=0)
    ax.grid(axis="y", color=GRILLE, lw=0.8, zorder=0)
    for cote in ["top", "right", "left"]:
        ax.spines[cote].set_visible(False)
    ax.spines["bottom"].set_color(GRILLE)
    ax.set_xlabel("âge de l'avis le jour de sa suppression", color=ENCRE_2, fontsize=8.5)
    ax.set_ylabel("avis 4 et 5 étoiles supprimés", color=ENCRE_2, fontsize=8.5)
    fig.text(0.012, 0.97, f"{100 * pic / total:.0f} % des suppressions des 13 premiers jours "
             "tombent au 6e ou au 7e jour", va="top", fontsize=11.5, color=ENCRE)
    fig.subplots_adjust(left=0.09, right=0.985, top=0.86, bottom=0.14)
    GRAPHIQUE.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(GRAPHIQUE, facecolor=FOND)
    plt.close(fig)


def graphique_taux(lignes: list) -> None:
    """Même graphique, en avis supprimés pour 1 000 avis observés en ligne à cet âge."""
    ages = [a for a, _, _ in lignes]
    taux = [1000 * s / n for _, n, s in lignes]
    hors_pic = max(t for a, t in zip(ages, taux) if a not in (6, 7))
    virgule = lambda x: f"{x:.1f}".replace(".", ",")
    fig, ax = plt.subplots(figsize=(8.5, 4.2), dpi=150)
    fig.patch.set_facecolor(FOND)
    ax.set_facecolor(FOND)
    couleurs = [BLEU_PIC if a in (6, 7) else BLEU for a in ages]
    ax.bar(ages, taux, width=0.72, color=couleurs, edgecolor=FOND, linewidth=1, zorder=3)
    for a, t in zip(ages, taux):
        ax.text(a, t + max(taux) * 0.015, virgule(t), ha="center", va="bottom", fontsize=8,
                color=ENCRE, fontweight="bold" if a in (6, 7) else "normal", zorder=4)
    ax.set_xticks(ages)
    ax.set_xticklabels([f"{a}e" if a > 1 else "1er" for a in ages])
    ax.set_xlim(0.4, len(ages) + 0.6)
    ax.set_ylim(0, max(taux) * 1.12)
    ax.tick_params(colors=ENCRE_2, labelsize=8.5, length=0)
    ax.grid(axis="y", color=GRILLE, lw=0.8, zorder=0)
    for cote in ["top", "right", "left"]:
        ax.spines[cote].set_visible(False)
    ax.spines["bottom"].set_color(GRILLE)
    ax.set_xlabel("âge de l'avis", color=ENCRE_2, fontsize=8.5)
    ax.set_ylabel("supprimés pour 1 000 avis en ligne (‰)", color=ENCRE_2, fontsize=8.5)
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(
        lambda v, _: f"{v:g}".replace(".", ",")))
    t7 = taux[ages.index(7)]
    fig.text(0.012, 0.97, f"Au 7e jour, {virgule(t7)} ‰ des avis 4-5 étoiles en ligne sont "
             f"supprimés, au plus {virgule(hors_pic)} ‰ hors du pic",
             va="top", fontsize=11.5, color=ENCRE)
    fig.subplots_adjust(left=0.09, right=0.985, top=0.86, bottom=0.14)
    GRAPHIQUE_TAUX.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(GRAPHIQUE_TAUX, facecolor=FOND)
    plt.close(fig)


if __name__ == "__main__":
    raise SystemExit(main())
