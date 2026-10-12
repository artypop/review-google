#!/usr/bin/env python3
"""Même question que `calcul.py`, sur le corpus 03C : les services à domicile
américains restent-ils les plus touchés sans les chaînes antiparasitaires ?

    PYTHONPATH=".venv/Lib/site-packages;outils" <python uv> etudes-ponctuelles/2026-10-07-home-services-us-sans-chaines/calcul_03C.py

Demande de Matthieu du 2026-10-07 : refaire la mesure de la première semaine
sur 03C, avis publiés du 7 au 17 août.

  corpus       avis 4-5 étoiles de 03C, chargés par `charger()` de
               `07F_regression_03C_prenom`, comme les pistes 2, 5 et 6 :
               55 avis sans annotation de prénom et fiches plus relevées avant
               le 24 août écartés.
  suppression  disparition notée au plus tard 7 jours après la publication.
  enseignes    les quatre chaînes et les deux salles espagnoles ; les salles
               n'ont aucun avis dans 03C.
  antiparasitaire  hors chaînes, repéré sur le nom avec le motif de
               `2026-09-18-antiparasitaire-home-services`.

Sortie : `sorties/secteur_region_03C.csv`. Aucun texte, nom d'auteur ni lien.
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

DOSSIER = Path(__file__).resolve().parent
RACINE = DOSSIER.parents[1]
sys.path.insert(0, str(RACINE / "outils"))
sys.path.insert(0, str(RACINE / "logistic-regression-study" / "python"))
from local import connexion  # noqa: E402

m = importlib.import_module("07F_regression_03C_prenom")

SORTIES = DOSSIER / "sorties"
MOTIF_ACTIVITE = r"(?i)(pest|exterminat|termite|spidexx|mosquito|rodent|wildlife)"
MOTIF_INCLUSION_MANUELLE = r"(?i)abc home ?(&|and) ?commercial"
SECTEURS = {"automotive": "Automobile", "food_beverage": "Restauration",
            "healthcare": "Santé", "home_services": "Services à domicile",
            "hospitality": "Hôtellerie", "travel": "Voyage",
            "wellness_fitness": "Sport et bien-être"}
REGIONS = {"US": "États-Unis", "Europe": "Europe"}


def pct(s: int, d: int) -> str:
    return f"{100 * s / d:.2f}" if d else ""


def concentration(g) -> tuple[int, int]:
    """Fiches ayant au moins une suppression, et suppressions de la fiche qui en a le plus."""
    par_fiche = g.groupby("cid")["supprime"].sum()
    return int((par_fiche > 0).sum()), int(par_fiche.max()) if len(par_fiche) else 0


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    SORTIES.mkdir(exist_ok=True)
    df = m.charger()

    con = connexion("2GB")
    antip = con.execute(
        f"SELECT cid FROM businesses WHERE regexp_matches(name, '{MOTIF_ACTIVITE}') "
        f"OR regexp_matches(name, '{MOTIF_INCLUSION_MANUELLE}')").df()["cid"]
    df["antiparasitaire"] = df["cid"].isin(set(antip)) & ~df["enseigne"]
    if (df["enseigne"] & ~((df["industry"] == "home_services") & (df["region"] == "US"))).any():
        raise SystemExit("Des avis des enseignes hors services à domicile US.")

    lignes = []
    for jeu, s in [("toutes les fiches", df), ("sans les 6 enseignes", df[~df["enseigne"]])]:
        for (ind, reg), g in s.groupby(["industry", "region"]):
            fiches, maxi = concentration(g)
            lignes.append((jeu, f"{SECTEURS[ind]}", REGIONS[reg], len(g), int(g["supprime"].sum()),
                           g["cid"].nunique(), fiches, maxi))
    hs_us = df[(df["industry"] == "home_services") & (df["region"] == "US") & ~df["enseigne"]]
    for nom, g in [("Services à domicile : antiparasitaire hors chaînes", hs_us[hs_us["antiparasitaire"]]),
                   ("Services à domicile : autres", hs_us[~hs_us["antiparasitaire"]])]:
        fiches, maxi = concentration(g)
        lignes.append(("sans les 6 enseignes", nom, "États-Unis", len(g), int(g["supprime"].sum()),
                       g["cid"].nunique(), fiches, maxi))

    with (SORTIES / "secteur_region_03C.csv").open("w", encoding="utf-8") as sortie:
        sortie.write("jeu,secteur,region,avis,supprimes_7j,pour_100,fiches,"
                     "fiches_avec_suppression,max_suppressions_une_fiche\n")
        for jeu in ("toutes les fiches", "sans les 6 enseignes"):
            print(f"\n--- {jeu} (trié sur la part supprimée) ---")
            for l in sorted((l for l in lignes if l[0] == jeu), key=lambda l: -l[4] / l[3]):
                _, sect, reg, n, s, nf, fs, mx = l
                sortie.write(f"{jeu},{sect},{reg},{n},{s},{pct(s, n)},{nf},{fs},{mx}\n")
                print(f"{sect:52s} {reg:11s} {s:4d}/{n:5d} = {pct(s, n):>5s} % | "
                      f"{fs:3d} fiches touchées sur {nf:4d}, au plus {mx} sur une fiche")
    print(f"\nécrit : {SORTIES / 'secteur_region_03C.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
