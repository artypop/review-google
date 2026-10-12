#!/usr/bin/env python3
"""Taux de suppression des avis 4 et 5 étoiles selon le niveau Local Guide de l'auteur.

    PYTHONPATH=".venv/Lib/site-packages;outils" <python uv> etudes-ponctuelles/2026-10-02-local-guide-niveaux/calcul.py

Demande d'Axel, cadrée avec Matthieu le 2026-10-02 : un bâton par niveau, avec
le pourcentage supprimé, sans autre ambition que dire si le niveau joue.

  corpus       data/bigquery/reviews_doublons_cleaned_all.parquet, avis 4 et
               5 étoiles, toutes dates de publication (le stock).
  suppression  `deleted_detected_at` renseigné, soit une disparition du 11 au
               24 août (décision de Matthieu du 2026-10-02).
  fiches       les 3 fiches qui ne sont plus relevées avant le 24 août sont
               écartées, comme dans `2026-10-02-flux-4-5-etoiles`.
  niveaux      1 à 3 : comptes qui ne sont pas Local Guide (`local_guide` faux
               sur toutes ces lignes), 4 et plus : Local Guides. Les niveaux du
               haut sont regroupés tant que le groupe a moins de 30
               suppressions : 8, 9 et 10 en ont 17 à eux trois, d'où « 7 à 10 ».
  sans niveau  niveau vide : 2 % de suppressions, vingt fois les autres
               groupes. Il est dans le CSV et hors du graphique, où sa barre
               écraserait toutes les autres.

Le niveau est celui du dernier relevé, pas celui de l'auteur à l'écriture.

Sorties, séparées :
  livrables/restitution_finale/graphiques/local_guide_niveaux.png
  livrables/restitution_finale/donnees/local_guide_niveaux.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "outils"))
from local import connexion  # noqa: E402

FINALE = RACINE / "livrables" / "restitution_finale"
GRAPHIQUE = FINALE / "graphiques" / "local_guide_niveaux.png"
DONNEES = FINALE / "donnees" / "local_guide_niveaux.csv"
RELEVE_FIN = "2026-08-24"
MIN_SUPPRESSIONS = 30

# Dégradé du bleu, du niveau le plus bas (clair) au plus haut (foncé) : rampe
# séquentielle du skill dataviz, du pas 250 (le plus clair admis pour des barres
# ordonnées sur fond clair) au pas 700.
RAMPE = ["#86b6ef", "#6da7ec", "#5598e7", "#3987e5", "#2a78d6",
         "#256abf", "#1c5cab", "#184f95", "#104281", "#0d366b"]
ENCRE, ENCRE_2, GRILLE, FOND = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"

SQL = f"""
WITH fin_suivi AS (
  SELECT cid, max(CAST(last_seen_at AS DATE)) AS fin_suivi
  FROM reviews_doublons_cleaned_all GROUP BY cid
)
SELECT local_guide_level, bool_or(local_guide), bool_and(local_guide),
       COUNT(*), COUNT(deleted_detected_at)
FROM reviews_doublons_cleaned_all r
JOIN fin_suivi f USING (cid)
WHERE r.star >= 4 AND f.fin_suivi = DATE '{RELEVE_FIN}'
GROUP BY local_guide_level
ORDER BY local_guide_level NULLS FIRST
"""


def espace(n: float) -> str:
    return f"{n:,.0f}".replace(",", " ")


def pct(s: int, n: int) -> str:
    return f"{100 * s / n:.3f}".replace(".", ",") + " %"


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    con = connexion("4GB")
    con.execute("SET threads=4")
    lignes = con.execute(SQL).fetchall()
    sans = [l for l in lignes if l[0] is None]
    niveaux = [l for l in lignes if l[0] is not None]
    for niv, un_guide, tous_guides, _, _ in niveaux:
        if (niv <= 3 and un_guide) or (niv >= 4 and not tous_guides):
            raise SystemExit(f"niveau {niv} : `local_guide` ne suit pas la règle 1-3 / 4+.")

    # Regroupement des niveaux du haut tant que le groupe a trop peu de suppressions.
    groupes = [[n] for n in niveaux]
    while len(groupes) > 1 and sum(l[4] for l in groupes[-1]) < MIN_SUPPRESSIONS:
        groupes[-2:] = [groupes[-2] + groupes[-1]]
    barres = []
    for g in groupes:
        bas, haut = g[0][0], g[-1][0]
        barres.append({"groupe": str(bas) if bas == haut else f"{bas} à {haut}",
                       "guide": bas >= 4, "avis": sum(l[3] for l in g),
                       "suppr": sum(l[4] for l in g)})
    n_tot = sum(b["avis"] for b in barres)
    s_tot = sum(b["suppr"] for b in barres)

    DONNEES.parent.mkdir(parents=True, exist_ok=True)
    GRAPHIQUE.parent.mkdir(parents=True, exist_ok=True)
    with DONNEES.open("w", encoding="utf-8") as f:
        f.write("groupe,local_guide,avis,suppressions,part_supprimee_pct,dans_le_graphique\n")
        for b in barres:
            f.write(f"niveau {b['groupe']},{'oui' if b['guide'] else 'non'},{b['avis']},"
                    f"{b['suppr']},{100 * b['suppr'] / b['avis']:.4f},oui\n")
        for _, _, _, n, s in sans:
            f.write(f"sans niveau,,{n},{s},{100 * s / n:.4f},non\n")
        f.write(f"total des niveaux,,{n_tot},{s_tot},{100 * s_tot / n_tot:.4f},\n")
        f.write("détail des niveaux regroupés,,,,,\n")
        for g in groupes:
            if len(g) > 1:
                for niv, _, _, n, s in g:
                    f.write(f"niveau {niv},oui,{n},{s},{100 * s / n:.4f},non\n")
    for b in barres:
        print(f"niveau {b['groupe']:7s} {b['suppr']:5d} / {b['avis']:>9,}  {pct(b['suppr'], b['avis'])}")
    for _, _, _, n, s in sans:
        print(f"sans niveau    {s:5d} / {n:>9,}  {pct(s, n)}  (hors graphique)")
    print(f"total niveaux  {s_tot:5d} / {n_tot:>9,}  {pct(s_tot, n_tot)}")

    taux = [100 * b["suppr"] / b["avis"] for b in barres]
    moyenne = 100 * s_tot / n_tot
    x = list(range(len(barres)))
    fig, ax = plt.subplots(figsize=(8.5, 4.8), dpi=150)
    fig.patch.set_facecolor(FOND)
    ax.set_facecolor(FOND)
    pas = [round(i * (len(RAMPE) - 1) / max(len(barres) - 1, 1)) for i in x]
    ax.bar(x, taux, width=0.7, color=[RAMPE[p] for p in pas],
           zorder=3, edgecolor=FOND, linewidth=1)
    ax.axhline(moyenne, color=ENCRE_2, lw=1, ls=(0, (4, 3)), zorder=4)
    for xi, t, b in zip(x, taux, barres):
        ax.annotate(f"{pct(b['suppr'], b['avis'])}\n{espace(b['suppr'])} / {espace(b['avis'])}",
                    (xi, t), xytext=(0, 4), textcoords="offset points", ha="center",
                    va="bottom", fontsize=7.5, color=ENCRE, linespacing=1.3, zorder=5,
                    bbox={"boxstyle": "square,pad=0.15", "fc": FOND, "ec": "none"})

    ax.set_xticks(x)
    ax.set_xticklabels([b["groupe"] for b in barres])
    ax.tick_params(colors=ENCRE_2, labelsize=8, length=0)
    ax.set_ylim(0, max(taux) * 1.3)
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.2f}".replace(".", ",") + " %")
    ax.grid(axis="y", color=GRILLE, lw=0.8, zorder=0)
    for cote in ["top", "right", "left"]:
        ax.spines[cote].set_visible(False)
    ax.spines["bottom"].set_color(GRILLE)
    ax.set_xlabel("niveau Local Guide de l'auteur", color=ENCRE_2, fontsize=8)
    ax.set_ylabel("part des avis supprimés du 11 au 24 août 2026", color=ENCRE_2, fontsize=8)

    fig.text(0.01, 0.97, "Taux de suppression des avis 4 et 5 étoiles selon le niveau "
             "Local Guide de l'auteur", va="top", fontsize=11, color=ENCRE)
    legende = [Line2D([0], [0], color=ENCRE_2, lw=1, ls=(0, (4, 3)),
                      label=f"moyenne ({pct(s_tot, n_tot)})"),
               Patch(color="none", label="sur chaque barre : supprimés / avis du groupe")]
    fig.legend(handles=legende, loc="upper left", bbox_to_anchor=(0.005, 0.92), ncol=2,
               frameon=False, fontsize=8, labelcolor=ENCRE, handlelength=1.6)
    fig.tight_layout(rect=(0, 0, 1, 0.86))
    fig.savefig(GRAPHIQUE, facecolor=FOND)
    plt.close(fig)
    print(f"\nécrit : {GRAPHIQUE}\nécrit : {DONNEES}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
