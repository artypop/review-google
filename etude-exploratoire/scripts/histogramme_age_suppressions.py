"""
Histogramme de l'âge des avis supprimés — estimation large pour le mail à Axel.

Question posée : sur les avis que Google supprime, quel âge avaient-ils ? Et quel est le
risque, pour un avis d'un âge donné, de se faire supprimer ?

Ce sont deux questions différentes et le script répond aux deux séparément, parce que les
réponses vont dans des directions opposées :

  - la RÉPARTITION (tableau 1) compte les suppressions par tranche d'âge. Elle est tirée par
    le stock : il y a beaucoup plus d'avis vieux que d'avis neufs dans le corpus, donc même
    avec un risque faible les vieux avis pèsent lourd dans le total.

  - le RISQUE (tableau 2) divise les suppressions par le nombre d'avis exposés dans la même
    tranche. C'est la probabilité qu'un avis de cet âge disparaisse, indépendamment du nombre
    d'avis de cet âge.

Unité d'exposition : un avis × un passage du robot où il est encore en ligne. On part de la
vague 2, la vague 1 étant le recensement initial (rien à comparer avant elle). L'âge est
recalculé à chaque passage, depuis `created_at` — la vraie date de publication donnée par
Google, pas la date où notre robot a vu l'avis.

Définition d'une suppression : dans `suppressions_corrigees.py`, qui réimplémente en DuckDB la
logique de logistic-regression-study/sql/01_build_avis_deleted_panel.sql. 5 230 disparitions
brutes -> 4 747 suppressions retenues.

Extrapolation annuelle : le suivi dure 14 jours, soit 13 intervalles d'un jour. Le risque
quotidien est projeté sur 365 jours en risque composé, 1-(1-p)^365. C'est une projection à
hypothèse forte (risque constant dans le temps, pas de vague de purge exceptionnelle dans la
fenêtre observée) : elle donne un ordre de grandeur, pas une mesure. Elle n'est valable par
tranche que pour « plus d'un an », la seule tranche dont un avis ne sort jamais en vieillissant.

Usage :  .venv/bin/python etude-exploratoire/scripts/histogramme_age_suppressions.py
"""

import pathlib
import sys

import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from suppressions_corrigees import bloc_ascii, connect, fr, vue_panel  # noqa: E402

OUT_MD = pathlib.Path("etude-exploratoire/documentations/2026-09-08-histogramme-age-des-suppressions.md")
OUT_CSV = pathlib.Path("data/resultats/histogramme_age_suppressions.csv")

N_INTERVALLES = 13   # vagues 2 à 14 : 13 passages comparables
JOURS_AN = 365

# Tranches d'âge demandées. Ordre alphabétique = ordre chronologique, pour que GROUP BY trie seul.
TRANCHES = """CASE
    WHEN age_days <  30 THEN 'a. moins de 1 mois'
    WHEN age_days <  91 THEN 'b. 1 à 3 mois'
    WHEN age_days < 183 THEN 'c. 3 à 6 mois'
    WHEN age_days < 366 THEN 'd. 6 à 12 mois'
    ELSE                     'e. plus de 1 an'
  END"""

# Bandes fines pour la courbe de survie du premier mois (tableau 4).
BANDES_FINES = """CASE
    WHEN age_days <   7 THEN 'a. 0-6 j'
    WHEN age_days <  14 THEN 'b. 7-13 j'
    WHEN age_days <  30 THEN 'c. 14-29 j'
    WHEN age_days <  91 THEN 'd. 1-3 mois'
    WHEN age_days < 183 THEN 'e. 3-6 mois'
    WHEN age_days < 366 THEN 'f. 6-12 mois'
    WHEN age_days < 1096 THEN 'g. 1-3 ans'
    ELSE                      'h. plus de 3 ans'
  END"""


def tableau_repartition(c) -> pd.DataFrame:
    """Tableau 1 — où tombent les suppressions, par âge de l'avis au moment de sa suppression."""
    return c.sql(f"""
        SELECT {TRANCHES} AS tranche,
               count(*)                                        AS suppressions,
               round(100.0 * count(*) / sum(count(*)) OVER (), 1) AS pct,
               round(count(*) * {JOURS_AN} / {N_INTERVALLES})   AS proj_annuelle
        FROM panel WHERE deleted GROUP BY 1 ORDER BY 1
    """).df()


def tableau_risque(c) -> pd.DataFrame:
    """Tableau 2 — risque de suppression par tranche d'âge, et sa projection sur un an."""
    return c.sql(f"""
        SELECT {TRANCHES} AS tranche,
               count(DISTINCT review_id)                     AS avis_exposes,
               count(*)                                      AS observations,
               sum(deleted::INT)                             AS suppressions,
               round(100.0 * sum(deleted::INT) / count(*), 4) AS risque_quotidien_pct,
               round(100.0 * (1 - pow(1 - sum(deleted::INT)::DOUBLE / count(*), {JOURS_AN})), 2)
                                                             AS risque_annuel_projete_pct
        FROM panel GROUP BY 1 ORDER BY 1
    """).df()


def tableau_cohorte_vague1(c) -> pd.DataFrame:
    """Tableau 3 — même découpage sur la seule cohorte présente à la vague 1.

    Les avis apparus pendant le suivi sont observés moins longtemps que les autres (censure à
    droite). Ce tableau les écarte : dénominateur fixe, tous les avis suivis les 14 jours.
    """
    return c.sql(f"""
        WITH cohorte AS (
            SELECT a.review_id,
                   date_diff('day', a.created_at, TIMESTAMP '2026-08-11 05:01:58') AS age_days,
                   a.death_at IS NOT NULL AS supprime
            FROM avis a
            WHERE a.first_seen_at < TIMESTAMP '2026-08-12 05:02:14')
        SELECT {TRANCHES} AS tranche,
               count(*)                                       AS avis,
               sum(supprime::INT)                             AS suppressions,
               round(100.0 * sum(supprime::INT) / count(*), 3) AS pct_supprimes_en_14j
        FROM cohorte GROUP BY 1 ORDER BY 1
    """).df()


def tableau_bandes_fines(c) -> pd.DataFrame:
    """Tableau 4 — la même chose en bandes fines, pour voir où le risque se concentre."""
    return c.sql(f"""
        SELECT {BANDES_FINES} AS bande,
               count(*)                                      AS observations,
               sum(deleted::INT)                             AS suppressions,
               round(100.0 * sum(deleted::INT) / count(*), 4) AS risque_quotidien_pct
        FROM panel GROUP BY 1 ORDER BY 1
    """).df()


def survie_premier_mois(c) -> pd.DataFrame:
    """Risque cumulé sur les 30 premiers jours de vie d'un avis, jour par jour.

    On ne peut pas lire ce chiffre dans le tableau 2 : un avis ne reste pas un mois dans la
    tranche « moins de 1 mois », il en sort. Le risque cumulé s'obtient en enchaînant les
    probabilités de survie de chaque jour d'âge : (1-p0)(1-p1)...(1-p29).
    """
    h = c.sql("""
        SELECT age_days, count(*) AS obs, sum(deleted::INT) AS morts
        FROM panel WHERE age_days BETWEEN 0 AND 29 GROUP BY 1 ORDER BY 1
    """).df()
    h["p"] = h["morts"] / h["obs"]
    h["survie_cumulee"] = (1 - h["p"]).cumprod()
    h["risque_cumule_pct"] = 100 * (1 - h["survie_cumulee"])
    return h


def tableau_hors_fiches_purgees(c) -> tuple[pd.DataFrame, int, int]:
    """Tableau 6 — même répartition, en écartant les fiches massivement purgées.

    Les suppressions sont très concentrées : quelques fiches perdent une grosse part de leur
    listing d'un coup. Si la tranche « plus de 1 an » vient surtout de ces fiches-là, alors ce
    n'est pas un risque diffus qui pèse sur les vieux avis, c'est une poignée d'interventions
    groupées. Le contrôle : refaire le tableau 1 sans les fiches ayant perdu plus de 5 % de
    leurs avis, et regarder si la répartition tient.
    """
    c.sql("""
        CREATE OR REPLACE VIEW fiches AS
        SELECT cid, count(*) AS n_avis, count(death_at) AS n_supp,
               count(death_at)::DOUBLE / count(*) AS part_purgee
        FROM avis GROUP BY cid
    """)
    n_fiches, n_supp = c.sql(
        "SELECT count(*), sum(n_supp) FROM fiches WHERE part_purgee > 0.05").fetchone()
    df = c.sql(f"""
        SELECT {TRANCHES} AS tranche,
               count(*)                                          AS suppressions,
               round(100.0 * count(*) / sum(count(*)) OVER (), 1) AS pct
        FROM panel p
        WHERE p.deleted
          AND p.cid NOT IN (SELECT cid FROM fiches WHERE part_purgee > 0.05)
        GROUP BY 1 ORDER BY 1
    """).df()
    return df, n_fiches, n_supp


def main() -> None:
    c = connect()
    vue_panel(c)

    total_avis, total_supp = c.sql("SELECT count(*), count(death_at) FROM avis").fetchone()
    brut = c.sql("SELECT count(*) FROM base WHERE deleted_detected_at IS NOT NULL").fetchone()[0]

    t1 = tableau_repartition(c)
    t2 = tableau_risque(c)
    t3 = tableau_cohorte_vague1(c)
    t4 = tableau_bandes_fines(c)
    t6, n_fiches_purgees, n_supp_purgees = tableau_hors_fiches_purgees(c)
    # Concentration, recalculée sur le comptage corrigé (les chiffres de la note du 2026-09-06
    # — 84 % / 39 fiches — datent d'avant la correction et ne sont plus valables).
    pct_fiches_intactes, n_top, pct_top = c.sql("""
        WITH f AS (SELECT cid, count(*) AS n, count(death_at) AS d FROM avis GROUP BY cid),
        top AS (SELECT sum(d) AS s, count(*) AS k FROM (
                    SELECT d FROM f WHERE d::DOUBLE / n > 0.05))
        SELECT round(100.0 * count(*) FILTER (d = 0) / count(*), 1), any_value(top.k),
               round(100.0 * any_value(top.s) / sum(f.d), 1)
        FROM f, top
    """).fetchone()
    surv = survie_premier_mois(c)
    risque_30j = surv["risque_cumule_pct"].iloc[-1]

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    t1.merge(t2, on="tranche").merge(t3, on="tranche").to_csv(
        OUT_CSV, index=False, sep=";", decimal=",", encoding="utf-8-sig")

    md = f"""# Histogramme de l'âge des avis supprimés

Date : 2026-09-08. Script : `etude-exploratoire/scripts/histogramme_age_suppressions.py`.
Objet : estimation large de la répartition par âge des suppressions, pour le mail à Axel.

Suivi : 14 vagues quotidiennes, {N_INTERVALLES} intervalles comparables (vagues 2 à 14).
Corpus : {fr(total_avis)} avis de base, {fr(total_supp)} suppressions retenues sur {fr(brut)}
disparitions brutes (correction des bugs d'édition et des ratés de collecte d'un jour, même
définition que `logistic-regression-study/sql/01_build_avis_deleted_panel.sql`).

L'âge d'un avis est compté depuis `created_at`, la date de publication donnée par Google.

---

## 1. Où tombent les suppressions — répartition par âge

Sur 100 avis supprimés, combien avaient tel âge au moment de leur suppression.

{bloc_ascii(t1, 'tranche', 'suppressions', dec=0, suffixe='')}

| Âge à la suppression | Suppressions (14 j) | Part | Projection sur 12 mois |
|---|---:|---:|---:|
""" + "\n".join(
        f"| {r.tranche[3:]} | {fr(r.suppressions)} | {fr(r.pct, 1)} % | {fr(r.proj_annuelle)} |"
        for r in t1.itertuples()
    ) + f"""

Projection sur 12 mois = observé × 365 / {N_INTERVALLES}, à volume et à comportement constants.
Ordre de grandeur seulement.

## 2. Risque de suppression par tranche d'âge

Même découpage, mais rapporté au nombre d'avis exposés. Une observation = un avis vivant à un
passage du robot.

| Âge de l'avis | Avis exposés | Observations | Suppressions | Risque par jour | Projection sur 12 mois |
|---|---:|---:|---:|---:|---:|
""" + "\n".join(
        f"| {r.tranche[3:]} | {fr(r.avis_exposes)} | {fr(r.observations)} | {fr(r.suppressions)} "
        f"| {fr(r.risque_quotidien_pct, 4)} % | {fr(r.risque_annuel_projete_pct, 2)} % |"
        for r in t2.itertuples()
    ) + f"""

Lecture de la projection : elle suppose que l'avis reste toute l'année dans sa tranche. Vrai
seulement pour « plus de 1 an ». Pour les tranches plus jeunes, l'avis vieillit et change de
tranche en cours de route : le chiffre répond à « et si le risque de cette tranche durait un
an », pas à « que devient un avis de cet âge sur un an ».

## 3. Contrôle de censure — cohorte présente à la vague 1

Les avis apparus pendant le suivi sont observés moins longtemps que les autres. Ce tableau les
écarte : tous les avis comptés ici ont été suivis les 14 jours complets.

| Âge au 11 août | Avis | Suppressions | Part supprimée en 14 j |
|---|---:|---:|---:|
""" + "\n".join(
        f"| {r.tranche[3:]} | {fr(r.avis)} | {fr(r.suppressions)} | {fr(r.pct_supprimes_en_14j, 3)} % |"
        for r in t3.itertuples()
    ) + f"""

## 4. Risque cumulé sur le premier mois de vie d'un avis

Un avis ne passe pas un an dans la tranche « moins de 1 mois » : il en sort en vieillissant. Le
chiffre utile pour un avis neuf est donc le risque cumulé sur ses 30 premiers jours, obtenu en
enchaînant les probabilités de survie de chaque jour d'âge.

**{fr(risque_30j, 2)} % des avis neufs sont supprimés dans leurs 30 premiers jours** (risque
cumulé, jours d'âge 0 à 29).

Le détail jour par jour est dans `2026-09-08-age-a-la-suppression.md`.

Le chiffre de {fr(risque_30j, 2)} % enchaîne des risques quotidiens mesurés sur 13 jours pour
couvrir 30 jours d'âge. Il est sensible au pic de 7-13 jours : si ce pic est un accident de la
fenêtre observée, le cumul baisse d'autant.

Ce pic est isolé jour par jour dans `2026-09-08-age-a-la-suppression.md` : il tombe à 7 jours de
vie exactement, avec 449 suppressions contre 279 à 6 jours et 118 à 8 jours.

## 5. Contrôle — la répartition sans les fiches massivement purgées

{fr(n_fiches_purgees)} fiches ont perdu plus de 5 % de leurs avis pendant le suivi, soit
{fr(n_supp_purgees)} suppressions ({fr(100.0 * n_supp_purgees / total_supp, 1)} % du total).
Tableau 1 recalculé sans elles :

| Âge à la suppression | Suppressions | Part |
|---|---:|---:|
""" + "\n".join(
        f"| {r.tranche[3:]} | {fr(r.suppressions)} | {fr(r.pct, 1)} % |"
        for r in t6.itertuples()
    ) + f"""

## Limites à dire à Axel

- 14 jours d'observation. Toute projection annuelle suppose que ces 14 jours sont représentatifs.
  Rien ne le garantit : une vague de purge tombée dans la fenêtre gonflerait tout, une fenêtre
  calme sous-estimerait tout.
- Les suppressions sont très concentrées : {fr(pct_fiches_intactes, 1)} % des
  établissements n'en ont aucune, et les {fr(n_top)} fiches ayant perdu plus de 5 % de leurs
  avis portent {fr(pct_top, 1)} % du total. Un taux moyen ne décrit aucun établissement en
  particulier.
- Le jour d'âge 0 est absent du cumul du § 4 : un avis n'est comparable qu'à partir du passage
  qui suit celui où le robot l'a découvert, donc son premier jour d'exposition est le jour 1.
  Ce qui se passe dans les vingt-quatre premières heures d'un avis n'est pas mesuré ici.
- L'âge vient de `created_at`, la date de publication annoncée par Google. Un avis réédité garde
  sa date de publication d'origine.
- Les tranches sont des tranches d'âge à la date du passage du robot, pas des cohortes suivies
  dans le temps. Un même avis peut apparaître dans deux tranches si son anniversaire tombe
  pendant les 14 jours ; c'est marginal sauf à la frontière du mois.

## Fichiers produits

- `data/resultats/histogramme_age_suppressions.csv` (gitignoré) — tableaux 1 à 3 fusionnés.
"""
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text(md, encoding="utf-8")

    with pd.option_context("display.width", 200, "display.max_rows", 60):
        print("\n--- 1. Répartition des suppressions par âge\n", t1.to_string(index=False))
        print("\n--- 2. Risque par tranche d'âge\n", t2.to_string(index=False))
        print("\n--- 3. Cohorte vague 1\n", t3.to_string(index=False))
        print("\n--- 4. Bandes fines\n", t4.to_string(index=False))
        print(f"\n--- 5. Risque cumulé 30 premiers jours : {risque_30j:.2f} %")
    print(f"\nÉcrit : {OUT_MD}\nÉcrit : {OUT_CSV}")


if __name__ == "__main__":
    main()
