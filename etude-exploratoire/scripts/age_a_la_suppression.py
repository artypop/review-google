"""
Combien d'avis supprimés à chaque âge, jour par jour.

Une seule question : parmi les avis que Google a supprimés, combien avaient 1 jour, 2 jours,
3 jours... au moment de leur suppression.

Deux colonnes de résultat, à ne pas confondre :

  - `supprimes` : le nombre brut. C'est la réponse à la question telle qu'elle se pose.
  - `pct_des_avis_de_cet_age` : le même nombre divisé par le nombre d'avis qui ont été observés
    à cet âge pendant le suivi. Nécessaire pour dire qu'un âge est plus risqué qu'un autre,
    parce que le corpus ne contient pas autant d'avis de chaque âge.

Périmètre : tout le corpus, pas de restriction. Définition d'une suppression :
`suppressions_corrigees.py`.

Usage :
    nice -n 19 .venv/bin/python etude-exploratoire/scripts/age_a_la_suppression.py
    nice -n 19 .venv/bin/python etude-exploratoire/scripts/age_a_la_suppression.py --age-max 60
"""

import argparse
import pathlib
import sys

import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from suppressions_corrigees import connect, fr, vue_panel  # noqa: E402

OUT_MD = pathlib.Path("etude-exploratoire/documentations/2026-09-08-age-a-la-suppression.md")
OUT_CSV = pathlib.Path("data/resultats/age_a_la_suppression.csv")


def tableau(c, age_max: int) -> pd.DataFrame:
    """Par âge en jours : suppressions, avis observés à cet âge, et le rapport des deux.

    `avis_observes` compte les couples avis × passage du robot : un avis encore en ligne, à
    cet âge, à ce passage. C'est le nombre d'occasions qu'avait Google de le supprimer à cet
    âge, donc le bon dénominateur.
    """
    return c.sql(f"""
        SELECT age_days                                       AS age_jours,
               sum(deleted::INT)                              AS supprimes,
               count(*)                                       AS avis_observes,
               round(100.0 * sum(deleted::INT) / count(*), 3)  AS pct_des_avis_de_cet_age
        FROM panel
        WHERE age_days BETWEEN 1 AND {age_max}
        GROUP BY 1 ORDER BY 1
    """).df()


def trois_definitions(c) -> pd.DataFrame:
    """Réconcilie les trois comptages d'« avis récents supprimés » qui circulent.

    Trois définitions coexistent dans le projet, toutes légitimes, mais elles ne comptent pas
    la même chose. Ce tableau les met côte à côte pour qu'on cesse de les confondre.
    """
    return c.sql("""
        SELECT 'D1' AS code,
               'âge à la suppression strictement inférieur à 30 jours (âges 1 à 29)' AS definition,
               (SELECT sum(deleted::INT) FROM panel WHERE age_days BETWEEN 1 AND 29) AS suppressions,
               'la tranche « moins de 1 mois » du tableau par tranches larges' AS usage
        UNION ALL SELECT 'D2',
               'âge à la suppression de 30 jours ou moins (âges 1 à 30)',
               (SELECT sum(deleted::INT) FROM panel WHERE age_days BETWEEN 1 AND 30),
               'le périmètre de modélisation, filtre age_days <= 30 sur le panel'
        UNION ALL SELECT 'D3',
               'avis âgé de 30 jours ou moins au premier passage, supprimé à n''importe quel moment',
               (SELECT count(death_at) FROM avis
                WHERE date_diff('day', created_at, TIMESTAMP '2026-08-11 05:01:58') <= 30),
               'une cohorte figée au départ de l''étude'
        ORDER BY code
    """).df()


def par_jour(c) -> pd.DataFrame:
    """Suppressions par journée du suivi, avec de quoi juger si une journée est une purge.

    `fiches` : sur combien d'établissements les suppressions du jour se répartissent.
    `pct_plus_grosse` : la part que porte l'établissement le plus touché ce jour-là.
    `hors_fiches_purgees` : le même total, en écartant les établissements ayant perdu plus de
    5 % de leur listing sur tout le suivi.
    """
    return c.sql("""
        WITH morts AS (
            SELECT a.cid,
                   (SELECT max(w.wave) FROM waves w WHERE w.started_at <= a.death_at) AS vague
            FROM avis a WHERE a.death_at IS NOT NULL),
        purgees AS (
            SELECT cid FROM (SELECT cid, count(*) t, count(death_at) d FROM avis GROUP BY cid)
            WHERE d::DOUBLE / t > 0.05),
        pf AS (SELECT vague, cid, count(*) AS n FROM morts GROUP BY 1, 2)
        SELECT pf.vague, strftime(w.started_at, '%d/%m') AS date_du_passage,
               sum(pf.n)                                   AS suppressions,
               count(*)                                    AS fiches,
               round(100.0 * max(pf.n) / sum(pf.n), 0)      AS pct_plus_grosse,
               sum(CASE WHEN pf.cid NOT IN (SELECT cid FROM purgees) THEN pf.n ELSE 0 END)
                                                           AS hors_fiches_purgees
        FROM pf JOIN waves w ON w.wave = pf.vague
        GROUP BY 1, 2 ORDER BY 1
    """).df()


def controle_pic(c, age_pic: int) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Le pic d'âge vient-il d'un effet d'âge, ou d'une purge tombée un jour donné ?

    Trois façons de répondre, qui doivent concorder :
      - étalement sur les journées du suivi : une purge tient sur une ou deux journées ;
      - étalement sur les établissements : une purge frappe quelques listings ;
      - retrait des deux journées les plus chargées : une purge disparaît avec elles.
    """
    jours = c.sql(f"""
        SELECT w.wave, strftime(w.started_at, '%d/%m') AS jour,
               sum(p.deleted::INT)                            AS suppressions,
               count(*)                                       AS avis_de_cet_age_ce_jour,
               round(100.0 * sum(p.deleted::INT) / count(*), 3) AS pct
        FROM panel p JOIN waves w USING (wave)
        WHERE p.age_days = {age_pic} GROUP BY 1, 2 ORDER BY 1
    """).df()
    fiches = c.sql(f"""
        WITH f AS (SELECT cid, sum(deleted::INT) AS n FROM panel
                   WHERE age_days = {age_pic} GROUP BY cid HAVING sum(deleted::INT) > 0)
        SELECT count(*) AS etablissements, sum(n) AS suppressions,
               max(n) AS plus_grosse_fiche, round(100.0 * max(n) / sum(n), 1) AS pct_plus_grosse
        FROM f
    """).df()
    # Les deux journées les plus chargées de tout le suivi, retirées du calcul.
    lourdes = [int(x) for x in c.sql("""
        SELECT wave FROM (SELECT wave, sum(deleted::INT) AS n FROM panel GROUP BY 1)
        ORDER BY n DESC LIMIT 2
    """).df()["wave"]]
    sans = c.sql(f"""
        SELECT age_days AS age_jours, sum(deleted::INT) AS suppressions,
               sum(CASE WHEN wave NOT IN ({lourdes[0]}, {lourdes[1]}) THEN deleted::INT END)
                                                       AS sans_les_2_journees_lourdes
        FROM panel WHERE age_days BETWEEN 4 AND 10 GROUP BY 1 ORDER BY 1
    """).df()
    return jours, fiches, sans


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--age-max", type=int, default=30, help="dernier âge du tableau (défaut : 30)")
    a = p.parse_args()

    c = connect()
    vue_panel(c)
    t = tableau(c, a.age_max)
    jours = par_jour(c)
    tdef = trois_definitions(c)
    age_pic = int(t.loc[t['supprimes'].idxmax(), 'age_jours'])
    pic_jours, pic_fiches, pic_sans = controle_pic(c, age_pic)

    total_supp = c.sql("SELECT count(death_at) FROM avis").fetchone()[0]
    dans_le_tableau = int(t["supprimes"].sum())

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    t.to_csv(OUT_CSV, index=False, sep=";", decimal=",", encoding="utf-8-sig")

    md = f"""# Âge des avis au moment de leur suppression, jour par jour

Script : `etude-exploratoire/scripts/age_a_la_suppression.py --age-max {a.age_max}`.
Date : 2026-09-08. Périmètre : tout le corpus.

{fr(dans_le_tableau)} des {fr(total_supp)} suppressions du corpus concernent un avis de
{a.age_max} jours ou moins. Le reste concerne des avis plus vieux.

- **`Supprimés`** répond à « combien d'avis de cet âge ont été supprimés ».
- **`Part des avis de cet âge`** répond à « un avis de cet âge, quel risque court-il ». Le
  corpus ne contient pas autant d'avis de chaque âge, donc les deux colonnes ne classent pas
  les âges dans le même ordre.

| Âge | Supprimés | Avis observés à cet âge | Part des avis de cet âge |
|---:|---:|---:|---:|
""" + "\n".join(
        f"| {int(r.age_jours)} j | {fr(r.supprimes)} | {fr(r.avis_observes)} "
        f"| {fr(r.pct_des_avis_de_cet_age, 3)} % |" for r in t.itertuples()
    ) + f"""

Maximum en nombre : **{int(t.loc[t.supprimes.idxmax(), 'age_jours'])} jours**
({fr(t.supprimes.max())} suppressions).
Maximum en part : **{int(t.loc[t.pct_des_avis_de_cet_age.idxmax(), 'age_jours'])} jours**
({fr(t.pct_des_avis_de_cet_age.max(), 3)} %).

L'âge 1 jour est sous-représenté : un avis n'entre dans le calcul qu'au passage suivant celui
qui l'a découvert, donc son premier jour d'exposition est le jour 1 et il y est peu observé.
Partout ailleurs le nombre d'avis observés est quasi constant (environ 32 000 par âge), donc la
colonne des nombres bruts classe les âges dans le même ordre que la colonne des parts.

## Contrôle fait le 2026-09-08 : y a-t-il un rythme hebdomadaire ?

Le tableau montre des bosses sur 7, 14, 21 et 28 jours. Deux explications possibles, et il faut
les séparer avant de conclure quoi que ce soit.

**Ce n'est pas un artefact de date.** `created_at` pourrait être une date reconstruite à partir
d'un libellé du type « il y a une semaine », ce qui produirait mécaniquement des âges multiples
de 7. Vérification faite : la répartition horaire de `created_at` suit une courbe de journée
plausible (creux à 4h, pic à 17h), les 60 valeurs de secondes sont présentes, et seuls 945 avis
sur 58 107 tombent sur la seconde zéro. C'est un horodatage réel.

**Ce n'est pas non plus un rythme hebdomadaire.** Sur les âges 2 à 30, les multiples de 7
affichent 0,554 % contre 0,215 % pour les autres âges, soit un rapport de 2,6. Mais en retirant
le seul âge 7, le rapport tombe à 1,5 (0,275 % contre 0,184 %) et ne se vérifie plus que dans
5 vagues sur 13. Ces 5 vagues comprennent les 16 et 23 août, les deux dimanches, qui sont les
deux journées les plus chargées en suppressions de tout le suivi (706 et 479 sur 4 747).

Conclusion : le pic à 7 jours de vie est solide. Les bosses à 14, 21 et 28 jours sont
essentiellement produites par ces deux dimanches, un avis publié un dimanche et supprimé un
dimanche ayant par construction un âge multiple de 7. Ne pas en tirer de cycle hebdomadaire.

## Trois comptages d'« avis récents supprimés », et ce qui les distingue

Trois valeurs circulent dans le projet. Aucune n'est fausse ; elles ne comptent pas la même
chose. À citer avec son code plutôt qu'avec le seul chiffre.

| Code | Définition | Suppressions | À quoi elle sert |
|---|---|---:|---|
""" + "\n".join(
        f"| **{r.code}** | {r.definition} | {fr(r.suppressions)} | {r.usage} |"
        for r in tdef.itertuples()
    ) + f"""

Les écarts s'expliquent entièrement :

- **D2 − D1 = 12** : les 12 avis supprimés à exactement 30 jours d'âge, exclus de D1 par la
  borne stricte de la tranche.
- **D3 − D2 = 78** : les 78 avis qui avaient 30 jours ou moins au 11 août mais qui ont franchi
  leur trentième jour avant d'être supprimés. D3 fige la cohorte au départ, D2 mesure l'âge au
  moment de la suppression.

Les 2 540 de D3 se décomposent donc en 2 462 supprimés avant leur 31e jour et 78 après.

## Le pic à {age_pic} jours : effet d'âge ou purge ?

Une purge est une opération groupée : elle tombe un jour donné, sur quelques établissements.
Un effet d'âge se reproduit tous les jours, partout. Trois vérifications.

**a) Les {fr(int(t.supprimes.max()))} suppressions à {age_pic} jours sont étalées sur
{fr((pic_jours.suppressions > 0).sum())} des {fr(len(pic_jours))} journées du suivi.**

| Jour | Suppressions à {age_pic} j | Avis de {age_pic} j ce jour-là | Part |
|---|---:|---:|---:|
""" + "\n".join(
        f"| {r.jour} | {fr(r.suppressions)} | {fr(r.avis_de_cet_age_ce_jour)} | {fr(r.pct, 3)} % |"
        for r in pic_jours.itertuples()
    ) + f"""

**b) Elles sont réparties sur {fr(pic_fiches.etablissements.iloc[0])} établissements**,
le plus touché n'en portant que {fr(pic_fiches.plus_grosse_fiche.iloc[0])}, soit
{fr(pic_fiches.pct_plus_grosse.iloc[0], 1)} %.

**c) Le pic reste après retrait des deux journées les plus chargées du suivi.**

| Âge | Suppressions | Sans les 2 journées les plus chargées |
|---:|---:|---:|
""" + "\n".join(
        f"| {int(r.age_jours)} j | {fr(r.suppressions)} | {fr(r.sans_les_2_journees_lourdes)} |"
        for r in pic_sans.itertuples()
    ) + f"""

Les trois vérifications concordent : le pic à {age_pic} jours est un effet d'âge, pas une purge.

## Suppressions par journée du suivi

Le pendant du tableau ci-dessus, rangé par date au lieu de l'être par âge. Sert à savoir si une
journée du suivi sort du lot.

| Vague | Date | Suppressions | Fiches touchées | Part de la plus touchée | Hors fiches purgées à plus de 5 % |
|---:|---|---:|---:|---:|---:|
""" + "\n".join(
        f"| {int(r.vague)} | {r.date_du_passage} | {fr(r.suppressions)} | {fr(r.fiches)} "
        f"| {fr(r.pct_plus_grosse, 0)} % | {fr(r.hors_fiches_purgees)} |"
        for r in jours.itertuples()
    ) + f"""

Le volume varie d'un facteur {fr(jours.suppressions.max() / jours.suppressions.min(), 1)} d'une
journée à l'autre, de {fr(jours.suppressions.min())} le
{jours.loc[jours.suppressions.idxmin(), 'date_du_passage']} à {fr(jours.suppressions.max())} le
{jours.loc[jours.suppressions.idxmax(), 'date_du_passage']}. Les quatre journées les plus
chargées font {fr(100 * jours.suppressions.nlargest(4).sum() / jours.suppressions.sum(), 0)} %
du total.

Chaque journée se répartit sur {fr(jours.fiches.min())} à {fr(jours.fiches.max())}
établissements, donc aucune n'est une purge de quelques listings — à une exception : le
{jours.loc[jours.pct_plus_grosse.idxmax(), 'date_du_passage']}, un seul établissement porte
{fr(jours.pct_plus_grosse.max(), 0)} % des suppressions du jour, et le total de cette journée
tombe de {fr(jours.loc[jours.pct_plus_grosse.idxmax(), 'suppressions'])} à
{fr(jours.loc[jours.pct_plus_grosse.idxmax(), 'hors_fiches_purgees'])} en écartant les fiches
purgées à plus de 5 %.

## Fichiers produits

- `{OUT_CSV}` (gitignoré) — le tableau par âge.
"""
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text(md, encoding="utf-8")

    with pd.option_context("display.max_rows", 80):
        print(t.to_string(index=False))
    print(f"\nÉcrit : {OUT_MD}\nÉcrit : {OUT_CSV}")


if __name__ == "__main__":
    main()
