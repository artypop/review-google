#!/usr/bin/env python3
"""Les phénomènes bizarres en un graphique : avis 4-5 étoiles supprimés chaque jour
du relevé, selon la fiche (chaînes antiparasitaires, autres fiches).

    PYTHONPATH=".venv/Lib/site-packages;outils" <python uv> etudes-ponctuelles/2026-10-05-phenomenes-par-jour/calcul.py

Demande de Matthieu du 2026-10-05, pour alléger la partie 6 de la consolidation :
un graphique qui montre d'un coup le poids des chaînes et le pic des 16 et 17 août.

  corpus      data/bigquery/reviews_doublons_cleaned_all.parquet, avis 4 et 5
              étoiles (demande de Matthieu du 2026-10-05 ; la première version
              comptait toutes les notes). Un avis disparu est un avis supprimé
              (doublons et clignotements déjà retirés) : 3 521 suppressions,
              comme la partie 4. Tous les avis, quelle que soit leur date de
              publication.
  jour        passage du robot qui constate la disparition
              (`deleted_detected_at`), du 12 au 24 août.
  fiches      chaînes : début du nom, comme
              `2026-09-28-secteurs-et-concentration/calcul.py`. The Boxer Club
              n'a que 2 suppressions 4-5 étoiles (ses retraits sont des avis à
              une étoile) : il reste dans « autres fiches ».

Mesuré le 2026-10-05 : 442 le 16 août (chaînes 191), 683 le 17 (chaînes 357),
210 un jour ordinaire (médiane des 11 autres jours).

Sorties : livrables/restitution_finale/graphiques/phenomenes_disparitions_par_jour.png
et livrables/restitution_finale/donnees/phenomenes_disparitions_par_jour.csv.

--toutes-notes (demande de Matthieu du 2026-10-05) : même graphique sans le filtre
4-5 étoiles, 4 590 suppressions. The Boxer Club reste dans « autres fiches »
(151 des 657 du 16 août). Sorties suffixées `_toutes_notes`. Le chiffre « un jour
ordinaire » est la médiane des 11 autres jours, arrondie à la dizaine.

--corpus-03c (demande de Matthieu du 2026-10-05) : même graphique sur la table
`03C_7_17_aout`, avis publiés du 7 au 17 août. Mesuré le 2026-10-05 : 905
suppressions 4-5 étoiles (le 07G en compte 903 : il écarte 55 avis au prénom
inconnu et 2 avis d'une fiche plus relevée). Pas de « jour ordinaire » : les
premiers jours ont peu d'avis assez vieux pour être supprimés ; le titre donne
le total et le jour le plus chargé. Sorties suffixées `_03C`.

--par-publies, avec --corpus-03c (demande de Matthieu du 2026-10-05) : chaque
jour, les suppressions pour 1 000 avis du corpus publiés jusqu'à la veille
(`created_at` antérieur au jour). Les deux segments sont rapportés au même
total, leur somme est le taux de l'ensemble ; le CSV donne aussi le taux propre
des chaînes et des autres fiches. Sorties suffixées `_03C_par_publies`.
"""
from __future__ import annotations

import argparse
import statistics
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "outils"))
from local import connexion  # noqa: E402

FINALE = RACINE / "livrables" / "restitution_finale"
DONNEES = FINALE / "donnees" / "phenomenes_disparitions_par_jour.csv"
GRAPHIQUE = FINALE / "graphiques" / "phenomenes_disparitions_par_jour.png"
RACINES_CHAINES_US = ("ecoshield pest solutions", "insight pest",
                      "pointe pest control", "bulwark exterminating")
# Palette de référence du skill dataviz : créneau 1, gris pour le reste.
BLEU, GRIS, ENCRE, ENCRE_2, GRILLE, FOND = ("#2a78d6", "#c3c2b7", "#0b0b0b", "#52514e",
                                            "#e4e3df", "#fcfcfb")
JOURS_PIC = (16, 17)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--toutes-notes", action="store_true", help="sans le filtre 4-5 étoiles")
    ap.add_argument("--corpus-03c", action="store_true",
                    help="avis publiés du 7 au 17 août (table 03C_7_17_aout)")
    ap.add_argument("--par-publies", action="store_true",
                    help="avec --corpus-03c : pour 1 000 avis publiés jusqu'à la veille")
    args = ap.parse_args()
    toutes, c03 = args.toutes_notes, args.corpus_03c
    if args.par_publies and not c03:
        ap.error("--par-publies ne vaut que pour --corpus-03c")
    table = '"03C_7_17_aout"' if c03 else "reviews_doublons_cleaned_all"
    suffixe = (("_03C" if c03 else "") + ("_toutes_notes" if toutes else "")
               + ("_par_publies" if args.par_publies else ""))
    donnees = DONNEES.with_name(f"{DONNEES.stem}{suffixe}.csv")
    sortie = GRAPHIQUE.with_name(f"{GRAPHIQUE.stem}{suffixe}.png")
    con = connexion("6GB")
    chaines = " OR ".join(f"lower(b.name) LIKE '{r}%'" for r in RACINES_CHAINES_US)
    lignes = con.execute(f"""
        SELECT CAST(r.deleted_detected_at AS DATE)                   AS jour,
               count(*) FILTER (coalesce({chaines}, FALSE))          AS chaines,
               count(*) FILTER (NOT coalesce({chaines}, FALSE))      AS autres
        FROM {table} r LEFT JOIN businesses b USING (cid)
        WHERE r.deleted_detected_at IS NOT NULL {"" if toutes else "AND r.star >= 4"}
        GROUP BY 1 ORDER BY 1
    """).fetchall()
    if args.par_publies:
        par_publies(con, table, chaines, toutes, lignes, donnees, sortie)
        return 0
    donnees.parent.mkdir(parents=True, exist_ok=True)
    with donnees.open("w", encoding="utf-8") as fh:
        fh.write("jour,chaines,autres,total\n")
        for jour, c, a in lignes:
            fh.write(f"{jour},{c},{a},{c + a}\n")
            print(f"{jour} : {c + a:>4} (chaînes {c:>3}, autres {a:>3})")
    print(f"total {sum(c + a for _, c, a in lignes)}")
    graphique(lignes, sortie, toutes, c03)
    print(f"\nécrit : {donnees}\nécrit : {sortie}")
    return 0


def par_publies(con, table: str, chaines: str, toutes: bool, lignes: list, donnees: Path,
                sortie: Path) -> None:
    """Suppressions du jour pour 1 000 avis du corpus publiés jusqu'à la veille.

    Les deux segments sont rapportés au même total d'avis publiés : leur somme est
    le taux de l'ensemble. Le CSV donne aussi le taux propre à chaque groupe.
    """
    publies = con.execute(f"""
        SELECT CAST(r.created_at AS DATE) AS jour,
               count(*) FILTER (coalesce({chaines}, FALSE))      AS chaines,
               count(*) FILTER (NOT coalesce({chaines}, FALSE))  AS autres
        FROM {table} r LEFT JOIN businesses b USING (cid)
        {"" if toutes else "WHERE r.star >= 4"}
        GROUP BY 1
    """).fetchall()
    taux = []
    donnees.parent.mkdir(parents=True, exist_ok=True)
    with donnees.open("w", encoding="utf-8") as fh:
        fh.write("jour,supprimes_chaines,supprimes_autres,publies_chaines_veille,"
                 "publies_autres_veille,pour_1000_publies,part_chaines_pour_1000,"
                 "part_autres_pour_1000,taux_propre_chaines_pour_1000,"
                 "taux_propre_autres_pour_1000\n")
        for jour, c, a in lignes:
            pc = sum(n for j, n, _ in publies if j < jour)
            pa = sum(n for j, _, n in publies if j < jour)
            tc, ta = 1000 * c / (pc + pa), 1000 * a / (pc + pa)
            taux.append((jour, tc, ta))
            fh.write(f"{jour},{c},{a},{pc},{pa},{tc + ta:.2f},{tc:.2f},{ta:.2f},"
                     f"{1000 * c / pc:.2f},{1000 * a / pa:.2f}\n")
            print(f"{jour} : {tc + ta:5.2f} ‰ de {pc + pa:>6} publiés (chaînes {1000 * c / pc:6.2f} ‰"
                  f" de {pc:>5}, autres {1000 * a / pa:5.2f} ‰ de {pa:>6})")
    graphique(taux, sortie, toutes, c03=True, par_publies=True)
    print(f"\nécrit : {donnees}\nécrit : {sortie}")


def graphique(lignes: list, sortie: Path, toutes: bool, c03: bool = False,
              par_publies: bool = False) -> None:
    jours = [j.day for j, _, _ in lignes]
    chaines = [c for _, c, _ in lignes]
    autres = [a for _, _, a in lignes]
    totaux = [c + a for c, a in zip(chaines, autres)]
    notes = "avis" if toutes else "avis 4-5 étoiles"
    virgule = lambda x: f"{x:.1f}".replace(".", ",")
    etiquette = virgule if par_publies else str
    if par_publies:
        jour_max = jours[totaux.index(max(totaux))]
        gras = (jour_max,)
        titre = (f"Corpus 03C : au plus {virgule(max(totaux))} ‰ des {notes} publiés "
                 f"supprimés en un jour, le {jour_max} août")
    elif c03:
        # Avis publiés du 7 au 17 août : les premiers jours ont peu d'avis assez
        # vieux pour être supprimés, il n'y a pas de « jour ordinaire ».
        jour_max = jours[totaux.index(max(totaux))]
        gras = (jour_max,)
        titre = (f"Corpus 03C : {sum(totaux)} {notes} supprimés, dont "
                 f"{100 * sum(chaines) / sum(totaux):.0f} % sur les 4 chaînes ; "
                 f"{max(totaux)} le {jour_max} août")
    else:
        gras = JOURS_PIC
        ordinaire = round(statistics.median(t for j, t in zip(jours, totaux)
                                            if j not in JOURS_PIC), -1)
        pic = [t for j, t in zip(jours, totaux) if j in JOURS_PIC]
        titre = (f"{pic[0]} et {pic[1]} {notes} supprimés les 16 et 17 août, "
                 f"contre {ordinaire:.0f} environ un jour ordinaire")
    fig, ax = plt.subplots(figsize=(8.5, 4.2), dpi=150)
    fig.patch.set_facecolor(FOND)
    ax.set_facecolor(FOND)
    commun = dict(width=0.72, edgecolor=FOND, linewidth=1, zorder=3)
    ax.bar(jours, autres, color=GRIS, label="Autres fiches", **commun)
    ax.bar(jours, chaines, bottom=autres, color=BLEU,
           label="4 chaînes antiparasitaires", **commun)
    for j, t in zip(jours, totaux):
        ax.text(j, t + max(totaux) * 0.015, etiquette(t), ha="center", va="bottom", fontsize=8,
                color=ENCRE, fontweight="bold" if j in gras else "normal", zorder=4)
    ax.set_xticks(jours)
    ax.set_xticklabels([str(j) for j in jours])
    ax.set_xlim(jours[0] - 0.6, jours[-1] + 0.6)
    ax.set_ylim(0, max(totaux) * 1.12)
    ax.tick_params(colors=ENCRE_2, labelsize=8.5, length=0)
    ax.grid(axis="y", color=GRILLE, lw=0.8, zorder=0)
    for cote in ["top", "right", "left"]:
        ax.spines[cote].set_visible(False)
    ax.spines["bottom"].set_color(GRILLE)
    ax.set_xlabel("jour d'août où le robot constate la suppression", color=ENCRE_2,
                  fontsize=8.5)
    if par_publies:
        ax.set_ylabel(f"supprimés pour 1 000 {notes} publiés (‰)", color=ENCRE_2, fontsize=8.5)
        ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(
            lambda v, _: f"{v:g}".replace(".", ",")))
    else:
        ax.set_ylabel("avis supprimés, toutes notes" if toutes else "avis 4 et 5 étoiles supprimés",
                      color=ENCRE_2, fontsize=8.5)
    poignees, etiquettes = ax.get_legend_handles_labels()
    leg = ax.legend(poignees[::-1], etiquettes[::-1], loc="upper left", frameon=False,
                    fontsize=8.5, labelcolor=ENCRE_2)
    leg.set_zorder(5)
    fig.text(0.012, 0.97, titre, va="top", fontsize=11.5, color=ENCRE)
    fig.subplots_adjust(left=0.09, right=0.985, top=0.86, bottom=0.14)
    sortie.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(sortie, facecolor=FOND)
    plt.close(fig)


if __name__ == "__main__":
    raise SystemExit(main())
