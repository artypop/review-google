#!/usr/bin/env python3
"""La réponse du commerçant protège-t-elle un avis, selon le jour où elle arrive ?

    PYTHONPATH=.venv/Lib/site-packages <python uv> etudes-ponctuelles/2026-09-30-secteurs-panel-03B/reponse_delai.py

Demande de Matthieu du 2026-09-30, à la suite du tableau 14 du rapport
(×0,37 sur les fiches qui répondent à plus de 75 %). Sorties dans `sorties/`,
reprises par `note.py`.

------------------------------------------------------------------------------
ÉTAPE 1. REJOUER LE ×0,37 EN LOCAL
------------------------------------------------------------------------------
Le ×0,37 vient du 08B lancé sur BigQuery le 2026-09-21. Trois colonnes du 08B
n'existent pas dans la copie locale du panel et sont refaites ici :
  age_a_la_suppression_j, delai_reponse_j   depuis le panel brut
                                            `03B_reviews_panel_filtered_...`,
                                            mêmes formules que `sql/03B`
  taux_reponse_fiche_avant_vague1           depuis `reviews`, dédoublonné
                                            comme dans `03B_features_local.py`,
                                            mêmes bornes que `sql/03B`
Les enseignes : `biz_surveillance` n'est pas copiée en local. Les chaînes sont
repérées par la colonne `chaine_antiparasitaire_us` du panel (nom exact), les
salles par leur `cid`. Mesuré le 2026-09-30 : ce repérage redonne les 16 212
avis du 08B. Celui du tableau 2 (chaînes par début de nom) retire en plus
8 succursales, 151 avis au jalon, aucune suppression parmi eux, et donne ×0,368.
Le même repérage sert à l'étape 2, pour que ses chiffres et le ×0,37 portent
sur la même population. Le passage est rejoué
avec les fonctions du 08B, importées telles quelles. S'il ne retombe pas sur
16 212 avis au jalon, 380 suppressions et ×0,37, le script s'arrête.

------------------------------------------------------------------------------
ÉTAPE 2. LE JOUR DE LA RÉPONSE
------------------------------------------------------------------------------
Avis publiés du 9 au 16 août (J = 11 août, premier relevé ; de J-2 à J+5).
Les avis du 17 (J+6) n'ont que 7 jours de suivi avant le dernier relevé du
24 août : ils sont écartés. Sans les enseignes signalées.

Pour chaque jour k de 0 à 6 (0 = réponse le jour de l'avis) :
  avis retenus   vus par le robot au plus tard à l'âge k, encore en ligne à
                 l'âge k, sans réponse avant le jour k
  groupe répondu réponse datée exactement du jour k
  comparaison    toujours sans réponse au jour k (réponse plus tard ou jamais)
  suppression    détectée entre le jour k+1 et le jour 8. Un avis encore en
                 ligne au jour 8 compte comme conservé, même s'il disparaît
                 ensuite (règle de Matthieu du 2026-09-30).
Le premier critère écarte, pour le jour k, un avis que le robot n'a vu qu'après
l'âge k : on ne sait pas s'il aurait pu disparaître avant d'être vu. Les avis
du 9 août, vus à l'âge 2, n'entrent donc qu'à partir de k = 2.

Même modèle que le 08B : mêmes variables, mêmes références, marges groupées
par fiche. Un passage sur toutes les fiches, un passage où l'effet est mesuré
dans chaque tranche d'habitude de la fiche.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd

DOSSIER = Path(__file__).resolve().parent
RACINE = DOSSIER.parent.parent
SORTIES = DOSSIER / "sorties"
sys.path.insert(0, str(RACINE / "outils"))
from local import connexion  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "m08B", RACINE / "logistic-regression-study" / "python" / "08B_effet_reponse_commercant.py")
m08B = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(m08B)

PANEL_BRUT = "03B_reviews_panel_filtered_08_04_to_08_26"
PANEL_FEATURES = RACINE / "data" / "local" / "reviews_panel_features_03B.parquet"
DERNIER_RELEVE = pd.Timestamp("2026-08-24")
PREMIER_RELEVE = pd.Timestamp("2026-08-11")
SUIVI_J = 8

CID_SALLES_ATTAQUEES = ("3163466139043001754", "10346942689164695031")

ATTENDU_037 = {"avis": 16_212, "suppressions": 380, "risque": 0.374}
JOURS = range(0, 7)
MIN_SUPPRESSIONS = m08B.MIN_SUPPRESSIONS_PAR_COLONNE


def charger() -> pd.DataFrame:
    con = connexion("2GB")
    con.execute("SET threads=2")
    con.execute("SET enable_progress_bar=false")
    df = con.execute(f"""
        WITH p AS (
          SELECT review_id, cid,
                 CAST(created_at AS DATE)          AS created_at_day,
                 CAST(first_seen_at AS DATE)       AS first_seen_day,
                 CAST(deleted_detected_at AS DATE) AS deleted_day,
                 CAST(reply_date AS DATE)          AS reply_day
          FROM "{PANEL_BRUT}"
        ),
        corpus AS (
          SELECT review_id, arg_max(cid, id) AS cid,
                 CAST(arg_max(created_at, id) AS DATE) AS jour,
                 arg_max(reply_date, id) AS reply_date
          FROM reviews
          WHERE cid IN (SELECT cid FROM p)
          GROUP BY review_id
        ),
        hr AS (
          SELECT cid, COUNT(*) AS n_avis,
                 COUNT(*) FILTER (reply_date IS NOT NULL
                                  AND CAST(reply_date AS DATE) < DATE '2026-08-11')
                   / COUNT(*) AS taux
          FROM corpus
          WHERE jour BETWEEN DATE '2025-08-11' AND DATE '2026-08-03'
          GROUP BY cid
        )
        SELECT f.*,
               p.created_at_day, p.first_seen_day,
               date_diff('day', p.created_at_day, p.deleted_day) AS age_a_la_suppression_j,
               date_diff('day', p.created_at_day, p.reply_day)   AS delai_reponse_j,
               IF(COALESCE(hr.n_avis, 0) >= 10, hr.taux, NULL)   AS taux_reponse_fiche_avant_vague1,
               (p.cid IN {CID_SALLES_ATTAQUEES} OR f.chaine_antiparasitaire_us)
                                                                 AS enseigne_signalee
        FROM p
        JOIN read_parquet('{PANEL_FEATURES.as_posix()}') f USING (review_id)
        LEFT JOIN hr ON hr.cid = p.cid
    """).df()
    con.close()
    df["created_at_day"] = pd.to_datetime(df["created_at_day"])
    df["jours_observables"] = (DERNIER_RELEVE - df["created_at_day"]).dt.days
    return df


def rejouer_037(df: pd.DataFrame) -> dict:
    d = df[(df["age_a_la_premiere_observation_j"] <= 1)
           & (df["jours_observables"] >= 8) & ~df["enseigne_signalee"]]
    d = m08B.ajouter_variables(m08B.appliquer_jalon(d, 2, 6))
    _, t = m08B.ajuster(d, "rejeu_037", d["region"].nunique() > 1, True, True)
    r = t.loc["reponse_si_habitude_plus_de_75"]
    obs = {"avis": len(d), "suppressions": int(d["supprime_fenetre"].sum()),
           "risque": round(float(r["risque_relatif"]), 3)}
    print(f"[rejeu ×0,37] {obs}  attendu {ATTENDU_037}")
    if obs != ATTENDU_037:
        raise SystemExit("ARRÊT : le rejeu local ne retombe pas sur le 08B.")
    return [{"habitude": tranche, "avis_au_jalon": obs["avis"],
             "suppressions": obs["suppressions"],
             **ligne_modele(t, f"reponse_si_habitude_{tranche}")}
            for tranche in ("plus_de_75", "25_75")]


def cohorte_jour(base: pd.DataFrame, k: int) -> pd.DataFrame:
    # Âge à la suppression vide = jamais supprimé ; délai vide = jamais répondu.
    age_supp = base["age_a_la_suppression_j"].astype("float64")
    delai = base["delai_reponse_j"].astype("float64")
    garde = ((base["age_a_la_premiere_observation_j"] <= k)
             & (age_supp.isna() | (age_supp > k))
             & ~(delai < k))
    d = base[garde].copy()
    d["reponse_au_jalon"] = (delai[garde] == k).astype("int8")
    d["supprime_fenetre"] = age_supp[garde].between(k + 1, SUIVI_J).astype("int8")
    return m08B.ajouter_variables(d)


def taux(d: pd.DataFrame) -> dict:
    out = {}
    for v, nom in ((1, "repondu"), (0, "sans_reponse")):
        g = d[d["reponse_au_jalon"] == v]
        out[f"avis_{nom}"] = len(g)
        out[f"suppr_{nom}"] = int(g["supprime_fenetre"].sum())
    return out


def ligne_modele(t: pd.DataFrame, var: str) -> dict:
    if var not in t.index:
        return {"risque_relatif": np.nan, "borne_basse": np.nan, "borne_haute": np.nan}
    r = t.loc[var]
    return {"risque_relatif": r["risque_relatif"], "borne_basse": r["borne_basse"],
            "borne_haute": r["borne_haute"]}


def main() -> int:
    SORTIES.mkdir(parents=True, exist_ok=True)
    df = charger()
    print(f"[lecture] {len(df):,} avis".replace(",", " "))

    pd.DataFrame(rejouer_037(df)).to_csv(SORTIES / "R0-rejeu-037.csv", index=False)

    base = df[df["created_at_day"].between("2026-08-09", "2026-08-16")
              & ~df["enseigne_signalee"]].copy()
    print(f"[population] {len(base):,} avis publiés du 9 au 16 août, sans enseignes"
          .replace(",", " "))

    toutes, par_habitude = [], []
    for k in JOURS:
        d = cohorte_jour(base, k)
        n = taux(d)
        ligne = {"jour_reponse": k, "avis": len(d), **n}
        if n["suppr_repondu"] >= MIN_SUPPRESSIONS and n["avis_repondu"] >= m08B.MIN_CAS_PAR_COLONNE:
            _, t = m08B.ajuster(d, f"jour{k}", d["region"].nunique() > 1, True, False)
            ligne |= ligne_modele(t, "reponse_au_jalon")
        toutes.append(ligne)
        print(f"  jour {k}: {ligne}")

        _, t = m08B.ajuster(d, f"jour{k}_habitude", d["region"].nunique() > 1, True, True)
        for tranche in ("plus_de_75", "25_75"):
            dd = d[d["habitude_reponse_fiche"] == f"habitude_{tranche}"]
            par_habitude.append({"jour_reponse": k, "habitude": tranche, "avis": len(dd),
                                 **taux(dd), **ligne_modele(t, f"reponse_si_habitude_{tranche}")})

    pd.DataFrame(toutes).to_csv(SORTIES / "R1-jour-reponse.csv", index=False)
    pd.DataFrame(par_habitude).to_csv(SORTIES / "R2-jour-reponse-par-habitude.csv", index=False)
    print(pd.DataFrame(par_habitude).to_string())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
