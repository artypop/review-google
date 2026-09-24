#!/usr/bin/env python3
"""Rassemble les sorties du 07B en tableaux prêts pour la note.

    python etudes-ponctuelles/2026-09-21-regression-03B/resultats.py

Aucun modèle n'est ajusté ici et aucun chiffre n'est recalculé. Le script lit
les CSV et les summaries écrits par
`logistic-regression-study/python/07B_regression_panel.py` et les remet en
forme. Les figures sont dessinées ensuite par `graphiques.py`, le document Word
assemblé par `note.py`.

------------------------------------------------------------------------------
SOURCE
------------------------------------------------------------------------------
`logistic-regression-study/output-study/2026-09-21-sorties-07B/`, six passages
lancés le 2026-09-21 sur `reviews_panel_features_03B`.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd

DOSSIER = Path(__file__).resolve().parent
RACINE = DOSSIER.parent.parent
SORTIES = DOSSIER / "sorties"
PASSAGES = (RACINE / "logistic-regression-study" / "output-study"
            / "2026-09-21-sorties-07B")

# Les six passages, dans l'ordre où la note les présente.
PASSAGES_ATTENDUS = [
    ("tous", "Panel entier"),
    ("tous_sans_enseignes", "Sans les enseignes signalées"),
    ("US", "États-Unis"),
    ("Europe", "Europe"),
    ("tous_sans_tardifs", "Sans les avis vus tardivement"),
    ("tous_sans_modifies", "Sans les avis réécrits"),
]

# Les variables que la note commente, avec leur libellé en clair. L'ordre est
# celui de la figure : du risque le plus fort au plus faible.
LIBELLES = {
    "log_burst": "Avis publiés le même jour par l'auteur",
    "secteur_home_services": "Secteur home services",
    "etoiles_1": "Avis 1 étoile",
    "etoiles_2": "Avis 2 étoiles",
    "vu_tardivement": "Première observation au 8e jour ou plus tard",
    "secteur_travel": "Secteur travel",
    "secteur_wellness_fitness": "Secteur wellness et fitness",
    "region_US": "Établissement aux États-Unis",
    "guide_sans_niveau": "Auteur sans niveau Local Guide",
    "guide_4_et_plus": "Auteur Local Guide niveau 4 ou plus",
    "log_ratio_pic_journalier_fiche": "Pic d'avis sur la fiche ce jour-là",
    "taille_small": "Établissement small",
    "taille_large": "Établissement large",
    "secteur_healthcare": "Secteur healthcare",
    "langue_minoritaire_sur_la_fiche": "Langue inhabituelle sur la fiche",
    "texte_texte_1_50": "Texte de 1 à 50 caractères",
    "texte_texte_201p": "Texte de plus de 200 caractères",
    "has_photo": "L'avis porte une photo",
    "texte_texte_51_200": "Texte de 51 à 200 caractères",
    "log_rc": "Nombre d'avis publiés par l'auteur",
    "secteur_hospitality": "Secteur hospitality",
    "etoiles_4": "Avis 4 étoiles",
    "secteur_food_beverage": "Secteur food et beverage",
    "etoiles_3": "Avis 3 étoiles",
    "log_photos_auteur": "Photos publiées par l'auteur",
}

# Les trois contrôles d'exposition. Ils sont dans le modèle mais leurs
# coefficients ne se citent pas : ils servent à ce que les autres se lisent à
# âge et à durée de suivi comparables.
CONTROLES = {"age_a_la_premiere_observation_j", "fenetre_observation_j", "const"}


def ecrire(df, nom):
    SORTIES.mkdir(parents=True, exist_ok=True)
    df.to_csv(SORTIES / nom, index=False)
    print(f"  {nom:34s} {len(df):>4} lignes")
    return df


def lire_auc(suffixe: str) -> float:
    """L'AUC telle que `ecrire_summary` l'a écrite dans l'en-tête du summary."""
    texte = (PASSAGES / f"07B_summary_{suffixe}.txt").read_text(encoding="utf-8")
    trouve = re.search(r"AUC sur des établissements jamais vus : ([0-9.]+)", texte)
    return float(trouve.group(1)) if trouve else float("nan")


def lire_effectifs(suffixe: str) -> tuple[int, int]:
    texte = (PASSAGES / f"07B_summary_{suffixe}.txt").read_text(encoding="utf-8")
    trouve = re.search(r"Panel : ([\d ]+) avis, ([\d ]+) suppressions", texte)
    return (int(trouve.group(1).replace(" ", "")),
            int(trouve.group(2).replace(" ", "")))


def main() -> int:
    if not PASSAGES.is_dir():
        raise SystemExit(f"Sorties introuvables : {PASSAGES}\n"
                         f"Lancer d'abord 07B_regression_panel.py.")

    print("\nA. Les six passages et leur capacité à classer")
    lignes = []
    for suffixe, libelle in PASSAGES_ATTENDUS:
        avis, suppressions = lire_effectifs(suffixe)
        lignes.append({
            "passage": libelle, "suffixe": suffixe,
            "avis": avis, "suppressions": suppressions,
            "taux_pct": round(suppressions / avis * 100, 2),
            "auc": lire_auc(suffixe),
        })
    ecrire(pd.DataFrame(lignes), "A1-passages.csv")

    print("\nB. Les risques relatifs du passage principal")
    coef = pd.read_csv(PASSAGES / "07B_coefficients_tous.csv")
    coef = coef[~coef["variable"].isin(CONTROLES)].copy()
    coef = coef[coef["variable"] != "etoiles_5"]
    coef["libelle"] = coef["variable"].map(LIBELLES)
    manquants = coef[coef["libelle"].isna()]["variable"].tolist()
    if manquants:
        raise SystemExit(f"Variables sans libellé, à ajouter dans LIBELLES : "
                         f"{', '.join(manquants)}")
    # « Tranché » : la fourchette ne contient pas 1. C'est la seule lecture que
    # la note fait de la p_value, et elle est dite en clair, pas en jargon.
    coef["tranche"] = (coef["borne_basse"] > 1) | (coef["borne_haute"] < 1)
    coef = coef.sort_values("risque_relatif", ascending=False)
    ecrire(coef[["variable", "libelle", "risque_relatif", "borne_basse",
                 "borne_haute", "tranche"]], "B1-risques-relatifs.csv")

    print("\nC. Les deux contrôles d'exposition, lus à part")
    brut = pd.read_csv(PASSAGES / "07B_coefficients_tous.csv")
    ctrl = brut[brut["variable"].isin(
        ["age_a_la_premiere_observation_j", "fenetre_observation_j"])].copy()
    ctrl["libelle"] = ctrl["variable"].map({
        "age_a_la_premiere_observation_j":
            "Un jour de plus entre la publication et la première observation",
        "fenetre_observation_j":
            "Un jour de plus de surveillance après la première observation"})
    ecrire(ctrl[["variable", "libelle", "risque_relatif", "borne_basse",
                 "borne_haute"]], "C1-controles.csv")

    print("\nD. Le taux observé par note, sans aucun modèle")
    croise = pd.read_csv(PASSAGES / "07B_croisements_tous.csv")
    notes = croise[croise["caracteristique"] == "star"].copy()
    notes["taux_pct"] = (notes["suppressions"] / notes["avis"] * 100).round(2)
    ecrire(notes[["valeur", "avis", "suppressions", "taux_pct"]], "D1-notes.csv")

    print("\nD bis. La concentration des suppressions sur les fiches")
    ecrire(pd.read_csv(PASSAGES / "07B_concentration_tous.csv"),
           "D2-concentration.csv")

    print("\nE. La courbe de ciblage du passage principal")
    ecrire(pd.read_csv(PASSAGES / "07B_courbe_ciblage_tous.csv"), "E1-ciblage.csv")
    # Les repères exacts, écrits à part par le 07B. La courbe est enregistrée
    # en 200 points et les relire dessus décalait le repère à 10 % d'un point.
    ecrire(pd.read_csv(PASSAGES / "07B_reperes_ciblage_tous.csv"),
           "E2-reperes-ciblage.csv")

    print(f"\nCSV dans {SORTIES}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
