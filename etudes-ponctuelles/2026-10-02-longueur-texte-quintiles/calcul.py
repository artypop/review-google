#!/usr/bin/env python3
"""Taux de suppression des avis 4 et 5 étoiles selon la longueur du texte.

    PYTHONPATH=".venv/Lib/site-packages;outils" <python uv> etudes-ponctuelles/2026-10-02-longueur-texte-quintiles/calcul.py

Demande d'Axel (réunion du 2026-10-02), cadrée avec Matthieu le même jour : une
distribution de la longueur en quintiles plutôt qu'une règle dans la
régression, sur les 4 et 5 étoiles, avec « sans texte » à part.

  corpus       data/bigquery/reviews_doublons_cleaned_all.parquet, avis 4 et
               5 étoiles, toutes dates de publication (le stock).
  suppression  `deleted_detected_at` renseigné, soit une disparition du 11 au
               24 août (décision de Matthieu du 2026-10-02).
  fiches       les 3 fiches qui ne sont plus relevées avant le 24 août sont
               écartées, comme dans `2026-10-02-flux-4-5-etoiles`.
  longueur     caractères du texte sans les espaces de début et de fin. Texte
               vide : groupe « sans texte ». Les avis avec texte sont répartis
               en 5 groupes sur les quintiles de leur longueur, bornes
               arrondies à la dizaine ; les groupes s'écartent donc un peu de
               20 %. Vérifié le 2026-10-02 : 1 seul texte porte une
               traduction automatique de Google, rien n'est retiré.

Sorties, séparées :
  livrables/restitution_finale/graphiques/longueur_texte_quintiles.png
  livrables/restitution_finale/donnees/longueur_texte_quintiles.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "outils"))
from local import connexion  # noqa: E402

FINALE = RACINE / "livrables" / "restitution_finale"
GRAPHIQUE = FINALE / "graphiques" / "longueur_texte_quintiles.png"
DONNEES = FINALE / "donnees" / "longueur_texte_quintiles.csv"
RELEVE_FIN = "2026-08-24"

# Palette des figures du 07E (skill dataviz, emplacement 1), et sa teinte claire
# pour le groupe « sans texte ».
BLEU, BLEU_CLAIR = "#2a78d6", "#9cc0ec"
ENCRE, ENCRE_2, GRILLE, FOND = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"

SQL_AVIS = f"""
CREATE TEMP TABLE avis AS
WITH fin_suivi AS (
  SELECT cid, max(CAST(last_seen_at AS DATE)) AS fin_suivi
  FROM reviews_doublons_cleaned_all GROUP BY cid
)
SELECT COALESCE(length(trim(r.text)), 0)   AS longueur,
       r.deleted_detected_at IS NOT NULL    AS supprime
FROM reviews_doublons_cleaned_all r
JOIN fin_suivi f USING (cid)
WHERE r.star >= 4 AND f.fin_suivi = DATE '{RELEVE_FIN}'
"""


def espace(n: float) -> str:
    return f"{n:,.0f}".replace(",", " ")


def virgule(x: float, d: int = 1) -> str:
    return f"{x:.{d}f}".replace(".", ",")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    con = connexion("4GB")
    con.execute("SET threads=4")
    con.execute(SQL_AVIS)
    quintiles = con.execute("SELECT quantile_disc(longueur, [0.2, 0.4, 0.6, 0.8]) "
                            "FROM avis WHERE longueur > 0").fetchone()[0]
    # Bornes arrondies à la dizaine pour la lecture (demande de Matthieu du
    # 2026-10-02) : 39, 76, 132, 242 deviennent 40, 80, 130, 240.
    coupures = [int(round(c / 10) * 10) for c in quintiles]
    print(f"quintiles {quintiles}, arrondis à {coupures}")
    bornes = [(0, 0)] + [(a + 1, b) for a, b in zip([0] + coupures, coupures)] \
        + [(coupures[-1] + 1, None)]

    lignes = []
    for bas, haut in bornes:
        cond = f"longueur >= {bas}" + (f" AND longueur <= {haut}" if haut is not None else "")
        n, s = con.execute(f"SELECT COUNT(*), COUNT(*) FILTER (supprime) FROM avis "
                           f"WHERE {cond}").fetchone()
        nom = ("sans texte" if haut == 0 else f"{bas} à {haut}" if haut is not None
               else f"{bas} et plus")
        lignes.append({"groupe": nom, "min": bas, "max": haut, "avis": n, "suppr": s})
    total_avis = sum(l["avis"] for l in lignes)
    total_suppr = sum(l["suppr"] for l in lignes)
    verif = con.execute("SELECT COUNT(*), COUNT(*) FILTER (supprime) FROM avis").fetchone()
    if (total_avis, total_suppr) != verif:
        raise SystemExit(f"Groupes incomplets : {total_avis, total_suppr} contre {verif}.")
    moyenne = 100 * total_suppr / total_avis

    DONNEES.parent.mkdir(parents=True, exist_ok=True)
    GRAPHIQUE.parent.mkdir(parents=True, exist_ok=True)
    with DONNEES.open("w", encoding="utf-8") as f:
        f.write("groupe,longueur_min,longueur_max,avis,part_des_avis_pct,suppressions,"
                "part_des_suppressions_pct,part_supprimee_pct\n")
        for l in lignes + [{"groupe": "total", "min": "", "max": "", "avis": total_avis,
                            "suppr": total_suppr}]:
            taux = 100 * l["suppr"] / l["avis"]
            l["taux"] = taux
            f.write(f"{l['groupe']},{l['min']},{'' if l['max'] is None else l['max']},"
                    f"{l['avis']},{100 * l['avis'] / total_avis:.1f},{l['suppr']},"
                    f"{100 * l['suppr'] / total_suppr:.1f},{taux:.4f}\n")
            print(f"{l['groupe']:14s} {l['avis']:>9,} avis ({100 * l['avis'] / total_avis:4.1f} %)"
                  f"  {l['suppr']:>5,} suppr. ({100 * l['suppr'] / total_suppr:4.1f} %)"
                  f"  {taux:.3f} % supprimés")

    # Graphique : une barre par groupe, « sans texte » séparé des quintiles.
    x = [0] + [i + 1.4 for i in range(5)]
    fig, ax = plt.subplots(figsize=(8.5, 4.8), dpi=150)
    fig.patch.set_facecolor(FOND)
    ax.set_facecolor(FOND)
    couleurs = [BLEU_CLAIR] + [BLEU] * 5
    ax.bar(x, [l["taux"] for l in lignes], width=0.7, color=couleurs, zorder=3,
           edgecolor=FOND, linewidth=1)
    for xi, l in zip(x, lignes):
        ax.annotate(virgule(l["taux"], 3) + " %", (xi, l["taux"]), xytext=(0, 4),
                    textcoords="offset points", ha="center", fontsize=8, color=ENCRE,
                    zorder=5, bbox={"boxstyle": "square,pad=0.15", "fc": FOND, "ec": "none"})
    ax.axhline(moyenne, color=ENCRE_2, lw=1, ls=(0, (4, 3)), zorder=4)

    ax.set_xticks(x)
    ax.set_xticklabels([f"{l['groupe']}\n{espace(l['avis'])} avis" for l in lignes])
    ax.tick_params(colors=ENCRE_2, labelsize=8, length=0)
    ax.set_ylim(0, max(l["taux"] for l in lignes) * 1.18)
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.2f}".replace(".", ",") + " %")
    ax.grid(axis="y", color=GRILLE, lw=0.8, zorder=0)
    for cote in ["top", "right", "left"]:
        ax.spines[cote].set_visible(False)
    ax.spines["bottom"].set_color(GRILLE)
    ax.set_xlabel("longueur du texte, en caractères", color=ENCRE_2, fontsize=8)
    ax.set_ylabel("part des avis supprimés du 11 au 24 août 2026",
                  color=ENCRE_2, fontsize=8)

    fig.text(0.01, 0.97, "Taux de suppression des avis 4 et 5 étoiles selon la longueur "
             "du texte", va="top", fontsize=11, color=ENCRE)
    legende = [Patch(color=BLEU_CLAIR, label="sans texte"),
               Patch(color=BLEU, label="avec texte, en 5 groupes de taille proche"),
               Line2D([0], [0], color=ENCRE_2, lw=1, ls=(0, (4, 3)),
                      label=f"moyenne des avis 4 et 5 étoiles ({virgule(moyenne, 3)} %)")]
    fig.legend(handles=legende, loc="upper left", bbox_to_anchor=(0.005, 0.92), ncol=3,
               frameon=False, fontsize=8, labelcolor=ENCRE, handlelength=1.6)
    fig.tight_layout(rect=(0, 0, 1, 0.86))
    fig.savefig(GRAPHIQUE, facecolor=FOND)
    plt.close(fig)
    print(f"\nécrit : {GRAPHIQUE}\nécrit : {DONNEES}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
