"""
Le cas des deux salles de sport espagnoles : une attaque par avis négatifs, nettoyée par Google.

Produit tous les chiffres du cas, **fiche par fiche**. Les deux fiches sont traitées séparément
parce que les additionner puis rapporter le résultat à l'une des deux produit des parts fausses
— l'erreur exacte des premières versions de cette note.

Chaque part est calculée sur le dénominateur de sa propre fiche.

Définition d'une suppression : `suppressions_corrigees.py`. Les chiffres d'avant le 2026-09-08
(399 suppressions, 264 sur 816) datent d'avant cette correction et ne valent plus.

Usage :  nice -n 19 .venv/bin/python etude-exploratoire/scripts/cas_attaque_salles_de_sport.py
"""

import pathlib
import sys

import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from suppressions_corrigees import connect, fr  # noqa: E402

OUT_MD = pathlib.Path("etude-exploratoire/documentations/2026-09-08-cas-attaque-salles-de-sport.md")

# Les deux seules fiches du panel à dépasser 100 suppressions. Identifiants d'établissement
# Google (pas de donnée personnelle). Étiquetées A et B dans la note.
CIDS = ("3163466139043001754", "10346942689164695031")
ETIQUETTES = {"3163466139043001754": "A", "10346942689164695031": "B"}
VAGUE_1 = "2026-08-11 05:01:58"


def vues(c) -> None:
    c.sql(f"""
        CREATE OR REPLACE VIEW g AS
        SELECT a.review_id, a.cid, a.created_at, a.death_at, r.star,
               r.txt IS NULL OR length(r.txt) = 0 AS sans_texte,
               coalesce(r.local_guide_level, 0) = 0 AS auteur_sans_niveau,
               r.auteur
        FROM avis a
        JOIN (SELECT review_id, any_value(star) AS star, any_value(text) AS txt,
                     any_value(local_guide_level) AS local_guide_level,
                     any_value(reviewer_name) AS auteur
              FROM reviews_brut WHERE NOT is_update GROUP BY review_id) r USING (review_id)
        WHERE a.cid IN {CIDS}
    """)


def note_affichee(c) -> pd.DataFrame:
    """La note que Google affiche sur la fiche, au premier et au dernier passage.

    Calculée depuis `histograms.parquet`, la répartition d'étoiles que Google publie lui-même.
    À ne pas confondre avec la moyenne des avis que notre robot a captés : l'histogramme est le
    chiffre que voit un client, et il bouge quand Google nettoie.
    """
    return c.sql(f"""
        SELECT h.cid,
               max(CASE WHEN h.wave = 1  THEN round((h.one + 2*h.two + 3*h.three + 4*h.four
                                                     + 5*h.five)::DOUBLE / h.total, 2) END) AS note_vague_1,
               max(CASE WHEN h.wave = 1  THEN h.total END)  AS total_vague_1,
               max(CASE WHEN h.wave = 14 THEN round((h.one + 2*h.two + 3*h.three + 4*h.four
                                                     + 5*h.five)::DOUBLE / h.total, 2) END) AS note_vague_14,
               max(CASE WHEN h.wave = 14 THEN h.total END)  AS total_vague_14
        FROM '{pathlib.Path("data/exports/exports/histograms.parquet").as_posix()}' h
        WHERE h.cid IN {CIDS} GROUP BY 1
    """).df()


def profil(c) -> pd.DataFrame:
    """Une ligne par fiche : sa taille, ce qu'elle a perdu, et le contraste supprimés / restants."""
    return c.sql(f"""
        SELECT cid,
               count(*)                                          AS avis_du_listing,
               count(death_at)                                   AS supprimes,
               round(100.0 * count(death_at) / count(*), 1)       AS pct_du_listing,
               round(avg(CASE WHEN death_at IS NOT NULL THEN star END), 2) AS note_moy_supprimes,
               round(avg(CASE WHEN death_at IS NULL     THEN star END), 2) AS note_moy_restants,
               round(100.0 * count(*) FILTER (death_at IS NOT NULL AND star = 1)
                     / nullif(count(death_at), 0), 0)             AS pct_1etoile_supprimes,
               round(100.0 * count(*) FILTER (death_at IS NULL AND star = 5)
                     / nullif(count(*) - count(death_at), 0), 0)  AS pct_5etoiles_restants,
               round(100.0 * count(*) FILTER (death_at IS NOT NULL AND sans_texte)
                     / nullif(count(death_at), 0), 0)             AS pct_sans_texte_supprimes,
               round(100.0 * count(*) FILTER (death_at IS NULL AND sans_texte)
                     / nullif(count(*) - count(death_at), 0), 0)  AS pct_sans_texte_restants,
               round(100.0 * count(*) FILTER (death_at IS NOT NULL AND auteur_sans_niveau)
                     / nullif(count(death_at), 0), 0)             AS pct_auteur_sans_niveau_supprimes,
               median(CASE WHEN death_at IS NOT NULL
                      THEN date_diff('day', created_at, TIMESTAMP '{VAGUE_1}') END) AS age_median_supprimes_j,
               round(median(CASE WHEN death_at IS NULL
                      THEN date_diff('day', created_at, TIMESTAMP '{VAGUE_1}') END) / 365.0, 1) AS age_median_restants_ans
        FROM g GROUP BY 1 ORDER BY supprimes DESC
    """).df()


def paquet(c) -> pd.DataFrame:
    """Le paquet d'avis négatifs, jour de publication par jour de publication, fiche par fiche."""
    return c.sql("""
        SELECT cid, created_at::DATE AS jour, strftime(created_at, '%d/%m') AS publie_le,
               count(*)                                     AS avis_publies,
               count(death_at)                              AS dont_supprimes,
               round(avg(star), 2)                          AS note_moyenne,
               count(DISTINCT auteur)                       AS auteurs_distincts,
               round(100.0 * count(*) FILTER (sans_texte) / count(*), 0) AS pct_sans_texte
        FROM g
        WHERE created_at::DATE BETWEEN DATE '2026-07-28' AND DATE '2026-08-05'
        GROUP BY 1, 2, 3 ORDER BY jour, cid
    """).df()


def part_du_paquet(c) -> pd.DataFrame:
    """La part du listing que représente le paquet des 1er-2 août, avec le bon dénominateur."""
    return c.sql("""
        SELECT cid, count(*) AS avis_du_listing,
               count(*) FILTER (created_at::DATE BETWEEN DATE '2026-08-01' AND DATE '2026-08-02')
                                                            AS publies_les_1_et_2_aout,
               round(100.0 * count(*) FILTER (created_at::DATE BETWEEN DATE '2026-08-01' AND DATE '2026-08-02')
                     / count(*), 1)                         AS pct_du_listing
        FROM g GROUP BY 1 ORDER BY 3 DESC
    """).df()


def delai(c) -> pd.DataFrame:
    """Délai entre publication et suppression, pour les avis du paquet."""
    return c.sql("""
        SELECT cid, date_diff('day', created_at, death_at) AS jours, count(*) AS avis
        FROM g
        WHERE death_at IS NOT NULL AND created_at >= TIMESTAMP '2026-07-28'
        GROUP BY 1, 2 ORDER BY 1, 2
    """).df()


def main() -> None:
    c = connect()
    vues(c)
    pr, pq, dl = profil(c), paquet(c), delai(c)
    pp = part_du_paquet(c).set_index('cid')
    na = note_affichee(c).set_index('cid')
    # Les identifiants, dans l'ordre des étiquettes A puis B : tout accès par cid,
    # jamais par position, sinon A et B s'échangent au moindre changement de tri.
    A, B = CIDS[0], CIDS[1]

    def lib(cid: str) -> str:
        return f"Fiche {ETIQUETTES[cid]}"

    bloc_fiches = ""
    for r in pr.itertuples():
        d = dl[dl.cid == r.cid].sort_values("avis", ascending=False)
        pic = d.head(2).sort_values("jours")
        pp_r = pp.loc[r.cid]
        bloc_fiches += f"""
### {lib(r.cid)}

| | |
|---|---:|
| Avis au listing | {fr(r.avis_du_listing)} |
| Note affichée par Google, au 11/08 | {fr(na.loc[r.cid, 'note_vague_1'], 2)} sur {fr(na.loc[r.cid, 'total_vague_1'])} avis |
| Note affichée par Google, au 24/08 | **{fr(na.loc[r.cid, 'note_vague_14'], 2)}** sur {fr(na.loc[r.cid, 'total_vague_14'])} avis |
| Avis publiés les 1er et 2 août | {fr(pp_r.publies_les_1_et_2_aout)}, soit **{fr(pp_r.pct_du_listing, 1)} % de ses {fr(pp_r.avis_du_listing)} avis** |
| Avis supprimés | {fr(r.supprimes)}, soit **{fr(r.pct_du_listing, 1)} % de ses {fr(r.avis_du_listing)} avis** |
| Note moyenne des supprimés | {fr(r.note_moy_supprimes, 2)} |
| Note moyenne des restants | {fr(r.note_moy_restants, 2)} |
| Part de 1 étoile parmi les supprimés | {fr(r.pct_1etoile_supprimes, 0)} % |
| Part de 5 étoiles parmi les restants | {fr(r.pct_5etoiles_restants, 0)} % |
| Sans aucun texte, supprimés / restants | {fr(r.pct_sans_texte_supprimes, 0)} % / {fr(r.pct_sans_texte_restants, 0)} % |
| Auteur sans niveau Local Guide, parmi les supprimés | {fr(r.pct_auteur_sans_niveau_supprimes, 0)} % |
| Âge médian des supprimés | {fr(r.age_median_supprimes_j, 0)} jours |
| Âge médian des restants | {fr(r.age_median_restants_ans, 1)} ans |
| Délai de suppression le plus fréquent | **{int(pic.jours.iloc[0])} à {int(pic.jours.iloc[-1])} jours** ({fr(pic.avis.sum())} avis) |
"""

    md = f"""# Le cas des deux salles de sport espagnoles

Script : `etude-exploratoire/scripts/cas_attaque_salles_de_sport.py`. Date : 2026-09-08.

Une attaque par avis négatifs, nettoyée par Google. Les deux seules fiches du panel à dépasser
100 suppressions, toutes deux du secteur `wellness_fitness` en Espagne.

**Les deux fiches sont traitées séparément, et chaque part est rapportée au listing de sa propre
fiche.** Les versions précédentes de ce cas additionnaient les deux fiches puis rapportaient le
total à l'une d'elles, ce qui donnait des parts fausses. Correctifs au bas de cette note.

{bloc_fiches}
## Le paquet, jour par jour

| Fiche | Publié le | Avis publiés | Dont supprimés | Note moyenne | Auteurs distincts | Sans texte |
|---|---|---:|---:|---:|---:|---:|
""" + "\n".join(
        f"| {ETIQUETTES[r.cid]} | {r.publie_le} | {fr(r.avis_publies)} | {fr(r.dont_supprimes)} "
        f"| {fr(r.note_moyenne, 2)} | {fr(r.auteurs_distincts)} | {fr(r.pct_sans_texte, 0)} % |"
        for r in pq.itertuples()
    ) + f"""

Un auteur distinct par avis, ou presque. Le signal n'est pas dans le texte — la majorité de ces
avis n'en ont aucun — il est dans le rythme et dans l'écart à la note habituelle de la fiche.

## Délai entre publication et suppression

| Fiche | Jours | Avis |
|---|---:|---:|
""" + "\n".join(
        f"| {ETIQUETTES[r.cid]} | {int(r.jours)} | {fr(r.avis)} |" for r in dl.itertuples()
    ) + f"""

Les deux fiches n'ont pas été nettoyées à la même vitesse, alors que l'attaque est simultanée.

## Ce que ça veut dire

Ce n'est pas un faux positif. Une entreprise s'est fait attaquer, Google a nettoyé. Deux
conséquences pour le livrable :

1. Le dire, sinon l'étude paraît à charge. Google fait son travail quand le signal est massif.
2. Ces {fr(pr.supprimes.sum())} avis faussent tout résultat où ils entrent. Ils expliquent à eux
   seuls pourquoi « 1 étoile » et « secteur sport et bien-être » sortaient si forts avant le
   contrôle de robustesse.

## Correctifs par rapport aux notes du 2026-09-06

| Chiffre publié le 2026-09-06 | Ce qui est vrai | Cause de l'erreur |
|---|---|---|
| 399 avis supprimés | {fr(pr.supprimes.sum())} : {fr(pr.set_index('cid').loc[A, 'supprimes'])} sur A + {fr(pr.set_index('cid').loc[B, 'supprimes'])} sur B | Comptage d'avant la correction des résurrections et des bugs d'édition |
| 264 avis sur 816 | {fr(pr.set_index('cid').loc[A, 'supprimes'])} sur {fr(pr.set_index('cid').loc[A, 'avis_du_listing'])} pour la fiche A | Idem |
| « 361 avis en deux jours » | {fr(pp.publies_les_1_et_2_aout.sum())} : {fr(pp.loc[A, 'publies_les_1_et_2_aout'])} sur A, {fr(pp.loc[B, 'publies_les_1_et_2_aout'])} sur B | Deux fiches, deux paquets, jamais un seul |
| « 24 % de son listing » | {fr(pp.loc[A, 'pct_du_listing'], 1)} % sur A, {fr(pp.loc[B, 'pct_du_listing'], 1)} % sur B | Paquet d'une fiche divisé par le total des deux |
| « sur une fiche notée 4,95 » | Google affichait {fr(na.loc[A, 'note_vague_1'], 2)} sur A et {fr(na.loc[B, 'note_vague_1'], 2)} sur B au 11/08, remontées à {fr(na.loc[A, 'note_vague_14'], 2)} et {fr(na.loc[B, 'note_vague_14'], 2)} au 24/08 | 4,95 était la note moyenne des avis restés en ligne, jamais celle affichée par la fiche |
| « effacés 10 à 14 jours plus tard » | voir le tableau des délais : deux vitesses distinctes | Les deux fiches étaient confondues |

Le compte des contrôles textuels (« 1 seul avis contenait une insulte ») vient de
`scripts/verif_texte.py`, sur le périmètre d'avant la correction. Non recalculé ici.
"""
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text(md, encoding="utf-8")

    with pd.option_context("display.width", 250, "display.max_columns", 30):
        print(pr.to_string(index=False))
        print("\n", pq.to_string(index=False))
        print("\n", pp.to_string(index=False))
    print(f"\nÉcrit : {OUT_MD}")


if __name__ == "__main__":
    main()
