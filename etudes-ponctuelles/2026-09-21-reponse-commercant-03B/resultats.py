#!/usr/bin/env python3
"""Rassemble les sorties du 08B en tableaux prêts pour la note.

    python etudes-ponctuelles/2026-09-21-reponse-commercant-03B/resultats.py

Aucun modèle n'est ajusté ici. Le script lit les CSV et les summaries écrits par
`logistic-regression-study/python/08B_effet_reponse_commercant.py` et les remet
en forme. Le document Word est assemblé ensuite par `note.py`, qui ne calcule
rien.

Une seule mesure est faite ici et nulle part ailleurs : le recouvrement entre la
population du 08 et celle du 08B, tableau E. Elle demande les deux tables, donc
une requête BigQuery. C'est elle qui décide comment se lit tout le reste : si
les deux passages portent sur les mêmes avis, leur accord ne confirme rien.

------------------------------------------------------------------------------
SOURCE
------------------------------------------------------------------------------
`logistic-regression-study/output-study/2026-09-21-sorties-08B/`, quinze
passages lancés le 2026-09-21 sur `reviews_panel_features_03B`, et
`.../2026-09-17-sorties-08/` pour la comparaison avec l'ancien panel.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

import pandas as pd

DOSSIER = Path(__file__).resolve().parent
RACINE = DOSSIER.parent.parent
SORTIES = DOSSIER / "sorties"
ETUDE = RACINE / "logistic-regression-study" / "output-study"
NOUVEAU = ETUDE / "2026-09-21-sorties-08B"
ANCIEN = ETUDE / "2026-09-17-sorties-08"

PROJET = "client-divers"
DATASET = "reviewflowz"

# L'escalier jalon / fenêtre. Leur somme vaut toujours 8 : c'est le 8e jour de
# vie de l'avis, dernier jour observé pour un avis publié le 16 août.
ESCALIER = [(1, 7), (2, 6), (3, 5), (4, 4), (5, 3), (6, 2)]

# Le passage de référence, celui que la note cite en premier.
JALON, FENETRE = 2, 6

HABITUDES = {
    "habitude_plus_de_75": "Fiches qui répondent à plus de 75 %",
    "habitude_25_75": "Fiches qui répondent à 25 à 75 %",
    "habitude_moins_de_25": "Fiches qui répondent à moins de 25 %",
    "habitude_historique_insuffisant": "Fiches sans historique suffisant",
}


def ecrire(df, nom):
    SORTIES.mkdir(parents=True, exist_ok=True)
    df.to_csv(SORTIES / nom, index=False)
    print(f"  {nom:34s} {len(df):>4} lignes")
    return df


def suffixe(jalon, fenetre, sans_enseignes=False, variante=""):
    return (f"jalon{jalon}_fenetre{fenetre}"
            + ("_sans_enseignes" if sans_enseignes else "") + variante)


def coefficient(dossier, prefixe, suff, variable):
    """Une ligne de coefficient, ou None si la colonne a été écartée."""
    chemin = dossier / f"{prefixe}_coefficients_{suff}.csv"
    if not chemin.exists():
        return None
    d = pd.read_csv(chemin).set_index("variable")
    return d.loc[variable] if variable in d.index else None


def lire_summary(dossier, prefixe, suff):
    """Les effectifs et l'effet minimal détectable, tels que le script les écrit."""
    texte = (dossier / f"{prefixe}_summary_{suff}.txt").read_text(encoding="utf-8")

    def nombre(motif):
        t = re.search(motif, texte)
        return int(t.group(1).replace(" ", "")) if t else None

    mde = re.search(r"détectable par ce montage : ×([0-9.]+) en protection,\s*"
                    r"×([0-9.]+)", texte)
    traites_pct = re.search(r"\(([0-9.]+)%\)", texte)
    return {
        "avis_au_jalon": nombre(r"Dénominateur : ([\d ]+) avis"),
        "suppressions": nombre(r"Cible : ([\d ]+) suppressions"),
        "avec_reponse": nombre(r"Traités : ([\d ]+) avis"),
        "avec_reponse_pct": float(traites_pct.group(1)) if traites_pct else None,
        "mde_protection": float(mde.group(1)) if mde else None,
        "mde_aggravation": float(mde.group(2)) if mde else None,
    }


def recouvrement() -> pd.DataFrame:
    """Combien d'avis du 08B étaient déjà dans la population du 08.

    C'est la mesure qui empêche de lire l'accord des deux passages comme une
    confirmation. La requête ne lit que les identifiants.
    """
    from google.cloud import bigquery

    client = bigquery.Client(project=PROJET)
    sql = f"""
    WITH ancien AS (
      SELECT review_id FROM `{PROJET}.{DATASET}.reviews_panel_features_03`
      WHERE age_a_la_vague1_j <= 1),
    nouveau AS (
      SELECT review_id FROM `{PROJET}.{DATASET}.reviews_panel_features_03B`
      WHERE age_a_la_premiere_observation_j <= 1
        AND fenetre_observation_j + age_a_la_premiere_observation_j
            >= {JALON + FENETRE})
    SELECT (SELECT COUNT(*) FROM ancien)  AS population_08,
           (SELECT COUNT(*) FROM nouveau) AS population_08B,
           (SELECT COUNT(*) FROM ancien JOIN nouveau USING (review_id)) AS communs
    """
    d = client.query(sql).to_dataframe()
    d["part_deja_vue_pct"] = (d["communs"] / d["population_08B"] * 100).round(1)
    d["avis_nouveaux"] = d["population_08B"] - d["communs"]
    d["avis_disparus"] = d["population_08"] - d["communs"]
    return d


def avis_ecartes() -> pd.DataFrame:
    """Ce que sont les avis que le 08 gardait et que le 08B écarte.

    Mesuré parce que la première version de la note les disait retirés en amont
    comme clignotements. C'est faux : ils sont tous dans `03B`. Ce sont des avis
    que le robot n'avait pas encore vus au moment où l'ancien critère les
    déclarait observables.

    `age_a_la_vague1_j` mesurait l'âge de l'avis au 11 août, date d'arrivée du
    robot. `age_a_la_premiere_observation_j` mesure son âge le jour où le robot
    l'a vraiment vu. Un avis publié le 10 août mais découvert le 18 vaut 1 pour
    la première et 8 pour la seconde.
    """
    from google.cloud import bigquery

    client = bigquery.Client(project=PROJET)
    sql = f"""
    WITH ancien AS (
      SELECT review_id FROM `{PROJET}.{DATASET}.reviews_panel_features_03`
      WHERE age_a_la_vague1_j <= 1),
    nouveau AS (
      SELECT review_id FROM `{PROJET}.{DATASET}.reviews_panel_features_03B`
      WHERE age_a_la_premiere_observation_j <= 1
        AND fenetre_observation_j + age_a_la_premiere_observation_j
            >= {JALON + FENETRE})
    SELECT
      CASE WHEN b.age_a_la_premiere_observation_j >= 8
           THEN "vus au 8e jour ou apres" ELSE "vus du 2e au 7e jour" END AS groupe,
      COUNT(*)                                       AS avis,
      MIN(b.age_a_la_premiere_observation_j)         AS age_min,
      MAX(b.age_a_la_premiere_observation_j)         AS age_max,
      COUNTIF(b.review_id IS NOT NULL)               AS presents_dans_03B,
      COUNTIF(b.supprime)                            AS suppressions
    FROM ancien a
    JOIN `{PROJET}.{DATASET}.reviews_panel_features_03B` b USING (review_id)
    WHERE a.review_id NOT IN (SELECT review_id FROM nouveau)
    GROUP BY 1 ORDER BY 2 DESC
    """
    return client.query(sql).to_dataframe()


def main() -> int:
    if not NOUVEAU.is_dir():
        raise SystemExit(f"Sorties introuvables : {NOUVEAU}\n"
                         f"Lancer d'abord 08B_effet_reponse_commercant.py.")

    print("\nA. Les effectifs du passage de référence")
    reference = suffixe(JALON, FENETRE)
    lignes = []
    for nom, suff in [("Corpus entier", reference),
                      ("Sans les enseignes signalées",
                       suffixe(JALON, FENETRE, True))]:
        e = lire_summary(NOUVEAU, "08B", suff)
        c = coefficient(NOUVEAU, "08B", suff, "reponse_au_jalon")
        lignes.append({"passage": nom, **e,
                       "risque_relatif": c["risque_relatif"],
                       "borne_basse": c["borne_basse"],
                       "borne_haute": c["borne_haute"],
                       "p_value": c["p_value"]})
    ecrire(pd.DataFrame(lignes), "A1-effectifs.csv")

    print("\nB. L'escalier jalon / fenêtre, sans les enseignes signalées")
    lignes = []
    for jalon, fenetre in ESCALIER:
        suff = suffixe(jalon, fenetre, True)
        c = coefficient(NOUVEAU, "08B", suff, "reponse_au_jalon")
        ancien = coefficient(ANCIEN, "08", suff, "reponse_au_jalon")
        lignes.append({
            "jalon": jalon, "fenetre": fenetre,
            "risque_relatif": c["risque_relatif"],
            "borne_basse": c["borne_basse"], "borne_haute": c["borne_haute"],
            "p_value": c["p_value"],
            # Le même chiffre sur l'ancien panel, pour la colonne de contrôle.
            "risque_relatif_08": ancien["risque_relatif"] if ancien is not None
                                 else float("nan"),
        })
    ecrire(pd.DataFrame(lignes), "B1-escalier.csv")

    print("\nC. L'effet de la réponse, séparément par habitude de la fiche")
    suff = suffixe(JALON, FENETRE, True, "_reponse_par_habitude")
    lignes = []
    for cle, libelle in HABITUDES.items():
        if cle == "habitude_historique_insuffisant":
            continue                      # rangée avec « moins de 25 % »
        variable = cle.replace("habitude_", "reponse_si_habitude_")
        c = coefficient(NOUVEAU, "08B", suff, variable)
        ancien = coefficient(ANCIEN, "08", suff, variable)
        lignes.append({
            "habitude": libelle, "variable": variable,
            "ecartee": c is None,
            "risque_relatif": c["risque_relatif"] if c is not None else float("nan"),
            "borne_basse": c["borne_basse"] if c is not None else float("nan"),
            "borne_haute": c["borne_haute"] if c is not None else float("nan"),
            "risque_relatif_08": ancien["risque_relatif"] if ancien is not None
                                 else float("nan"),
        })
    ecrire(pd.DataFrame(lignes), "C1-par-habitude.csv")

    print("\nD. Les taux bruts, avant tout modèle, avec et sans les enseignes")
    lignes = []
    for nom, sans in [("corpus entier", False), ("sans enseignes", True)]:
        d = pd.read_csv(NOUVEAU / f"08B_reponse_x_habitude_"
                                  f"{suffixe(JALON, FENETRE, sans)}.csv")
        for _, r in d.iterrows():
            lignes.append({
                "corpus": nom,
                "habitude": HABITUDES.get(r["habitude_reponse_fiche"],
                                          r["habitude_reponse_fiche"]),
                "reponse_au_jalon": int(r["reponse_au_jalon"]),
                "avis_au_jalon": int(r["avis_au_jalon"]),
                "suppressions": int(r["supprimes_dans_la_fenetre"]),
                "taux_pour_10000_avis": r["taux_pour_10000_avis"],
            })
    bruts = ecrire(pd.DataFrame(lignes), "D1-taux-bruts.csv")

    print("\nD bis. Ce que le retrait des enseignes signalées enlève")
    # La différence entre les deux corpus, cellule par cellule. Calculée ici et
    # non dans la note : un document ne fait pas de soustraction.
    pivot = bruts.pivot_table(index=["habitude", "reponse_au_jalon"],
                              columns="corpus",
                              values=["avis_au_jalon", "suppressions"])
    retire = pd.DataFrame({
        "avis_retires": (pivot[("avis_au_jalon", "corpus entier")]
                         - pivot[("avis_au_jalon", "sans enseignes")]),
        "suppressions_retirees": (pivot[("suppressions", "corpus entier")]
                                  - pivot[("suppressions", "sans enseignes")]),
    }).reset_index()
    ecrire(retire, "D2-effet-enseignes.csv")

    print("\nE. Recouvrement avec la population du 08")
    ecrire(recouvrement(), "E1-recouvrement.csv")

    print("\nF. Ce que le 08B écarte et que le 08 gardait")
    ecrire(avis_ecartes(), "F1-avis-ecartes.csv")

    print(f"\nCSV dans {SORTIES}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
