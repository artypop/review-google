#!/usr/bin/env python3
"""Quel âge avaient les avis supprimés sur les fiches qui portent la moitié des
suppressions ?

    python etudes-ponctuelles/2026-09-28-age-suppressions-72-fiches/calcul.py

Produit les CSV de `sorties/`. La figure et le document Word sont assemblés
par `note.py`, qui ne calcule rien.

------------------------------------------------------------------------------
LES FICHES
------------------------------------------------------------------------------
Même périmètre et même classement que la figure 4 du rapport
(`2026-09-18-concentration-suppressions/concentration.py`) : toute la base,
fiches rangées par suppressions décroissantes, puis avis décroissants, puis
`cid`. Les fiches retenues sont les premières dont le cumul atteint la moitié
des suppressions. Le script vérifie qu'il en trouve 72, comme la figure 4.

Point de comparaison : les suppressions de toutes les autres fiches.

------------------------------------------------------------------------------
L'ÂGE À LA SUPPRESSION
------------------------------------------------------------------------------
Jour du relevé où l'avis a disparu (`death_at` de `creer_vue_avis()`) moins
son jour de publication (`created_at`), en jours, lus en UTC. Le robot passe
une fois par jour : l'âge est connu au jour près. Seules les suppressions
constatées du 11 au 24 août sont visibles.

Enseignes signalées : les deux salles de sport attaquées sur leur `cid`, les
quatre chaînes antiparasitaires américaines sur le début du nom, comme dans
`2026-09-28-secteurs-et-concentration/calcul.py`.
"""
from __future__ import annotations

import sys
from pathlib import Path

DOSSIER = Path(__file__).resolve().parent
RACINE = DOSSIER.parent.parent
SORTIES = DOSSIER / "sorties"
sys.path.insert(0, str(RACINE / "outils"))
sys.path.insert(0, str(RACINE / "etude-exploratoire" / "scripts"))

from local import connexion  # noqa: E402
from suppressions_corrigees import creer_vue_avis  # noqa: E402

FICHES_ATTENDUES = 72   # figure 4 du rapport, B2-seuils.csv de l'étude concentration

CID_SALLES_ATTAQUEES = ("3163466139043001754", "10346942689164695031")
RACINES_CHAINES_US = ("ecoshield pest solutions", "insight pest",
                      "pointe pest control", "bulwark exterminating")

TRANCHES = """
    CASE WHEN age_j <= 7    THEN 'a. 0 à 7 jours'
         WHEN age_j <= 30   THEN 'b. 8 à 30 jours'
         WHEN age_j <= 90   THEN 'c. 1 à 3 mois'
         WHEN age_j <= 365  THEN 'd. 3 à 12 mois'
         WHEN age_j <= 1095 THEN 'e. 1 à 3 ans'
         ELSE                    'f. plus de 3 ans' END
"""


def ecrire(df, nom):
    SORTIES.mkdir(parents=True, exist_ok=True)
    df.to_csv(SORTIES / nom, index=False)
    print(f"  {nom:36s} {len(df):>5} lignes")
    return df


def main() -> int:
    con = connexion("1500MB")
    con.execute("SET threads=2")
    con.execute("SET enable_progress_bar=false")
    creer_vue_avis(con, source="reviews")

    chaines = " OR ".join(f"lower(b.name) LIKE '{r}%'" for r in RACINES_CHAINES_US)
    con.execute(f"""
        CREATE TEMP TABLE fiches AS
        SELECT a.cid, any_value(b.name) AS enseigne, any_value(b.industry) AS secteur,
               any_value(b.country) AS pays,
               bool_or(a.cid IN {CID_SALLES_ATTAQUEES} OR {chaines}) AS enseigne_signalee,
               COUNT(*) AS avis, COUNT(a.death_at) AS suppressions
        FROM avis a LEFT JOIN businesses b USING (cid)
        GROUP BY a.cid
    """)
    con.execute("""
        CREATE TEMP TABLE rangs AS
        SELECT *, ROW_NUMBER() OVER (ORDER BY suppressions DESC, avis DESC, cid) AS rang,
               100.0 * SUM(suppressions) OVER (ORDER BY suppressions DESC, avis DESC, cid
                                              ROWS UNBOUNDED PRECEDING)
                     / SUM(suppressions) OVER () AS part_cumulee
        FROM fiches
    """)
    n = con.execute("SELECT MIN(rang) FROM rangs WHERE part_cumulee >= 50").fetchone()[0]
    if n != FICHES_ATTENDUES:
        print(f"ARRÊT : {n} fiches portent la moitié des suppressions, "
              f"{FICHES_ATTENDUES} attendues (figure 4).")
        return 1
    print(f"{n} fiches portent la moitié des suppressions, comme la figure 4")

    con.execute(f"""
        CREATE TEMP TABLE supp AS
        SELECT a.review_id, a.cid, a.star,
               date_diff('day', CAST(a.created_at AS DATE), CAST(a.death_at AS DATE)) AS age_j,
               CASE WHEN r.rang <= {n} THEN '72 fiches les plus touchées'
                    ELSE 'Autres fiches' END AS groupe,
               r.enseigne_signalee
        FROM avis a JOIN rangs r USING (cid)
        WHERE a.death_at IS NOT NULL
    """)

    ecrire(con.execute(f"""
        SELECT rang, cid, enseigne, secteur, pays, enseigne_signalee, avis, suppressions,
               ROUND(part_cumulee, 1) AS part_cumulee_des_suppressions_pct,
               (SELECT MEDIAN(age_j) FROM supp s WHERE s.cid = r.cid) AS age_median_j
        FROM rangs r WHERE rang <= {n} ORDER BY rang
    """).df(), "A1-les-72-fiches.csv")

    for suffixe, filtre in (("", "TRUE"), ("-sans-enseignes", "NOT enseigne_signalee")):
        ecrire(con.execute(f"""
            SELECT groupe, {TRANCHES} AS tranche_age, COUNT(*) AS suppressions,
                   ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY groupe), 1)
                       AS part_du_groupe_pct
            FROM supp WHERE {filtre}
            GROUP BY 1, 2 ORDER BY 1, 2
        """).df(), f"B1-tranches{suffixe}.csv")

        ecrire(con.execute(f"""
            SELECT groupe, COUNT(*) AS suppressions,
                   COUNT(DISTINCT cid) AS fiches,
                   MEDIAN(age_j) AS age_median_j,
                   QUANTILE_CONT(age_j, 0.25) AS age_premier_quart_j,
                   QUANTILE_CONT(age_j, 0.75) AS age_dernier_quart_j,
                   MIN(age_j) AS age_min_j, MAX(age_j) AS age_max_j
            FROM supp WHERE {filtre}
            GROUP BY 1 ORDER BY 1
        """).df(), f"B2-resume{suffixe}.csv")

    con.close()
    print(f"\nCSV dans {SORTIES}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
