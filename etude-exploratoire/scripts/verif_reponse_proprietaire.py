"""
La réponse du patron protège-t-elle vraiment, ou est-ce l'inverse ?

L'analyse B donne « avis avec réponse du propriétaire : 3,7 fois moins supprimé ». C'est
l'effet protecteur le plus fort de l'étude, et le seul levier que le client puisse actionner.
Avant d'en faire une recommandation, il faut écarter une explication concurrente.

Le problème. Dans les tables, `has_reply` vaut l'état final de l'avis au dernier passage du
robot, et cette valeur est recopiée sur tous les passages précédents. Un avis supprimé au
troisième jour n'a pas eu le temps de recevoir une réponse ; un avis qui survit trois semaines
en reçoit une. Dans ce cas « avoir une réponse » serait une conséquence de la survie, pas une
cause. L'effet serait un artefact.

Ce script tranche en trois mesures :

  1. Le délai entre la publication de l'avis et la réponse du patron.
  2. Combien d'avis supprimés avaient reçu leur réponse AVANT leur suppression.
  3. Le même effet, recalculé en ne comptant la réponse comme présente qu'à partir du passage
     qui suit sa date réelle. Si l'effet tient, la protection est réelle.

Usage :  uv run scripts/verif_reponse_proprietaire.py
"""

import pathlib
import sys

import duckdb
import numpy as np
import pandas as pd

AVIS = pathlib.Path("data/build/reviews_features.parquet")
HAZ = pathlib.Path("data/build/fresh_hazard.parquet")
WAVES = pathlib.Path("data/exports/exports/waves.parquet")
OUT = pathlib.Path("documentations/2026-09-06-verif-reponse-proprietaire.md")
CSV = pathlib.Path("data/resultats/verif_reponse_proprietaire.csv")
BEGIN = "<!-- genere:reponse — regenere par scripts/verif_reponse_proprietaire.py, ne pas editer a la main -->"
END = "<!-- /genere:reponse -->"

AGE_BAND = """CASE WHEN age_days < 3 THEN '0-2j' WHEN age_days < 7 THEN '3-6j'
   WHEN age_days < 14 THEN '7-13j' WHEN age_days < 21 THEN '14-20j'
   WHEN age_days < 30 THEN '21-29j' ELSE '30j+' END"""


def standardise(g: pd.DataFrame, cle: str) -> pd.DataFrame:
    """Risque par passage, recalculé à âge comparable."""
    poids = g.groupby("age_band")["expo"].sum()
    poids = poids / poids.sum()
    rows = []
    for val, sub in g.groupby(cle):
        s = sub.set_index("age_band")
        taux = (s["morts"] / s["expo"]).reindex(poids.index).fillna(0)
        rows.append({cle: val, "expositions": int(s["expo"].sum()),
                     "morts": int(s["morts"].sum()),
                     "risque_pour_10k": 1e4 * float((taux * poids).sum())})
    return pd.DataFrame(rows)


def main() -> None:
    for p in (AVIS, HAZ, WAVES):
        if not p.exists():
            sys.exit(f"Fichier absent : {p}. Lancer d'abord : uv run scripts/build_tables.py")
    c = duckdb.connect(config={"memory_limit": "2GB"})
    c.sql(f"CREATE VIEW a AS SELECT * FROM '{AVIS.as_posix()}'")
    c.sql(f"CREATE VIEW h AS SELECT * FROM '{HAZ.as_posix()}'")
    c.sql(f"CREATE VIEW w AS SELECT wave, started_at FROM '{WAVES.as_posix()}'")

    # 1. Délai entre publication de l'avis et réponse du patron, sur les avis récents
    delai = c.sql("""
        SELECT count(*) AS avis_avec_reponse,
               median(date_diff('day', created_at, reply_date)) AS delai_median_j,
               quantile_cont(date_diff('day', created_at, reply_date), 0.25) AS q25,
               quantile_cont(date_diff('day', created_at, reply_date), 0.75) AS q75,
               100.0 * count(*) FILTER (date_diff('day', created_at, reply_date) <= 2)
                     / count(*) AS pct_sous_2j,
               100.0 * count(*) FILTER (date_diff('day', created_at, reply_date) <= 7)
                     / count(*) AS pct_sous_7j
        FROM a WHERE is_fresh AND has_reply AND reply_date IS NOT NULL
    """).df().iloc[0]

    # 2. Chez les avis supprimés qui ont une réponse : arrivée avant ou après la suppression ?
    ordre = c.sql("""
        SELECT count(*) AS supprimes_avec_reponse,
               -- Comparaison à `death_at`, la date de suppression corrigée. Sur la date
               -- brute, un raté de collecte d'un jour ferait basculer une réponse du
               -- côté « après la suppression » alors que l'avis n'a jamais été supprimé.
               count(*) FILTER (reply_date < death_at)  AS reponse_avant,
               count(*) FILTER (reply_date >= death_at) AS reponse_apres
        FROM a WHERE is_fresh AND deleted AND has_reply AND reply_date IS NOT NULL
    """).df().iloc[0]

    # 3. L'effet recalculé avec la réponse datée : présente seulement à partir du passage
    #    qui suit sa date réelle.
    g_fige = c.sql(f"""
        SELECT has_reply AS reponse, {AGE_BAND} AS age_band,
               count(*) AS expo, sum(died::INT) AS morts
        FROM h GROUP BY 1, 2
    """).df()
    g_date = c.sql(f"""
        SELECT coalesce(a.reply_date <= w.started_at, FALSE) AS reponse,
               {AGE_BAND.replace('age_days', 'h.age_days')} AS age_band,
               count(*) AS expo, sum(h.died::INT) AS morts
        FROM h JOIN a USING (row_id) JOIN w USING (wave)
        GROUP BY 1, 2
    """).df()

    res = {}
    for nom, g in [("réponse figée à l'état final (méthode actuelle)", g_fige),
                   ("réponse datée, comptée seulement une fois publiée", g_date)]:
        d = standardise(g, "reponse")
        avec = d[d["reponse"]].iloc[0]
        sans = d[~d["reponse"]].iloc[0]
        res[nom] = {
            "expo_avec": int(avec["expositions"]), "morts_avec": int(avec["morts"]),
            "risque_avec": avec["risque_pour_10k"],
            "expo_sans": int(sans["expositions"]), "morts_sans": int(sans["morts"]),
            "risque_sans": sans["risque_pour_10k"],
            "rapport": avec["risque_pour_10k"] / sans["risque_pour_10k"],
        }

    out = pd.DataFrame(res).T.reset_index(names="methode")
    CSV.parent.mkdir(parents=True, exist_ok=True)
    out.round(3).to_csv(CSV, index=False, sep=";", decimal=",", encoding="utf-8-sig")
    print(out.to_string(index=False))
    print(f"\nÉcrit : {CSV}")
    write_note(delai, ordre, res)
    print(f"Écrit : {OUT}")


def write_note(delai, ordre, res: dict) -> None:
    f = lambda n: f"{n:,}".replace(",", " ")  # noqa: E731
    fige = res["réponse figée à l'état final (méthode actuelle)"]
    date = res["réponse datée, comptée seulement une fois publiée"]
    ecart = 100 * (date["rapport"] - fige["rapport"]) / fige["rapport"]

    b = [BEGIN, ""]
    b.append("### 1. Quand le patron répond-il ?")
    b.append("")
    b.append(f"- {f(int(delai.avis_avec_reponse))} avis récents ont reçu une réponse.")
    b.append(f"- Délai médian entre l'avis et la réponse : **{delai.delai_median_j:.0f} jours** "
             f"(moitié des cas entre {delai.q25:.0f} et {delai.q75:.0f} jours).")
    b.append(f"- **{delai.pct_sous_2j:.1f} %** des réponses arrivent dans les 2 jours, "
             f"**{delai.pct_sous_7j:.1f} %** dans les 7 jours.")
    b.append("")
    b.append("Plus les réponses sont tardives, plus le risque que « avoir une réponse » "
             "signifie surtout « avoir survécu » est grand.")
    b.append("")
    b.append("### 2. Chez les avis supprimés, la réponse est-elle arrivée avant ?")
    b.append("")
    b.append(f"- {f(int(ordre.supprimes_avec_reponse))} avis récents supprimés avaient une réponse.")
    b.append(f"- **{f(int(ordre.reponse_avant))}** l'avaient reçue **avant** la suppression.")
    b.append(f"- {f(int(ordre.reponse_apres))} l'ont reçue après la date de suppression détectée.")
    b.append("")
    b.append("### 3. L'effet tient-il quand on date la réponse ?")
    b.append("")
    b.append("| Façon de compter la réponse | Avis suivis | Disparitions | Sur 10 000 passages | Effet |")
    b.append("|---|---:|---:|---:|---:|")
    for nom, r in res.items():
        b.append(f"| {nom} — **avec** réponse | {f(r['expo_avec'])} | {f(r['morts_avec'])} | "
                 f"{r['risque_avec']:.2f} | ×{r['rapport']:.2f} |")
        b.append(f"| {nom} — **sans** réponse | {f(r['expo_sans'])} | {f(r['morts_sans'])} | "
                 f"{r['risque_sans']:.2f} | référence |")
    b.append("")
    b.append(f"L'effet passe de ×{fige['rapport']:.2f} à ×{date['rapport']:.2f} quand on ne "
             f"compte la réponse qu'à partir du moment où elle existe réellement, "
             f"soit un déplacement de {ecart:+.0f} %.")
    b.append("")
    b.append(END)
    body = "\n".join(b)

    head = """---
date: 2026-09-06
projet: reviewflowz-analyse-google
titre: "La réponse du patron protège-t-elle vraiment ?"
statut: résultats
---

# La réponse du patron protège-t-elle vraiment ?

Produit par `scripts/verif_reponse_proprietaire.py`.

## Pourquoi cette vérification est indispensable

L'analyse B donne « avis avec réponse du propriétaire : 3,7 fois moins supprimé ». C'est le seul
levier que le client puisse actionner lui-même, donc le résultat le plus directement
exploitable de l'étude. Il faut être sûr avant de le recommander.

L'explication concurrente à écarter : dans les tables, la présence d'une réponse est enregistrée
telle qu'elle est au dernier passage du robot, puis recopiée sur tous les passages précédents.
Un avis supprimé au troisième jour n'a pas eu le temps de recevoir une réponse. Un avis qui
survit trois semaines en reçoit une. Si c'est le mécanisme dominant, « avoir une réponse » est
une conséquence de la survie et non une protection, et la recommandation est fausse.

## Résultats

"""
    if OUT.exists() and BEGIN in (prev := OUT.read_text(encoding="utf-8")) and END in prev:
        OUT.write_text(prev[: prev.index(BEGIN)] + body + prev[prev.index(END) + len(END):],
                       encoding="utf-8")
    else:
        OUT.write_text(head + body + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
