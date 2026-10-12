#!/usr/bin/env python3
"""
==============================================================================
Script : 03C_features_corpus.py
Sortie : data/local/features_<nom du corpus>.parquet (non versionné)

Construit les caractéristiques du 07E sur un corpus d'avis quelconque. Écrit le
2026-09-30 à la demande de Matthieu. Le 03B et sa transposition locale ne sont
pas modifiés.

Normalement appelé par `07E_regression_corpus.py`, qui porte le nom du corpus.
Utilisable seul :

    PYTHONPATH=.venv/Lib/site-packages <python uv> logistic-regression-study/python/03C_features_corpus.py data/local/reviews_doublons_cleaned_180.parquet

------------------------------------------------------------------------------
LE CORPUS
------------------------------------------------------------------------------
Un parquet au schéma de `reviews_doublons_cleaned` : une ligne par avis. Les
dates peuvent être des dates ou des horodatages : elles sont passées en DATE
en UTC (`connexion()`), règle de Matthieu du 2026-09-30.

------------------------------------------------------------------------------
LA SUPPRESSION : ABSENT DEUX JOURS DE SUITE OU PLUS
------------------------------------------------------------------------------
Règle de Matthieu du 2026-09-30. Un avis est supprimé si le robot ne l'a pas vu
deux jours de suite ou plus, alors que sa fiche était relevée. La date de
suppression est le premier jour de la première absence de ce type.

Elle se lit sur l'historique complet de `reviews`, une ligne par période où
l'avis a été vu (`first_seen_at` → `last_seen_at`). Un avis qui revient ouvre
une nouvelle ligne. Un jour = une vague : vérifié le 2026-09-30, chaque date de
`first_seen_at`, `last_seen_at` et `deleted_detected_at` tombe dans une seule
vague, la vague 2 (12 août, finie le 13 à 05:00 UTC) comprise.

Deux sortes d'absence :
  entre deux périodes vues   jours manquants entre la fin d'une période et le
                             début de la suivante, toutes lignes confondues ;
  à la fin                   l'avis n'est plus vu jusqu'au dernier relevé de sa
                             fiche. Comptée seulement si le robot a noté la
                             disparition (`deleted_detected_at`).

Trois cas que la règle traite, mesurés sur `reviews` le 2026-09-30 :
  - 3 fiches ne sont plus relevées à partir du 17, 18 ou 22 août. Leurs 547
    avis s'arrêtent sans `deleted_detected_at` : fin de suivi, pas suppression.
    Leur dernier jour de relevé sert de fin de suivi.
  - 495 avis ont une ligne marquée disparue alors qu'une autre ligne du même
    avis est vue jusqu'au 24 août (version modifiée). L'avis est resté en
    ligne : les jours vus sont pris toutes lignes confondues.
  - Un avis disparu au dernier relevé de sa fiche n'a qu'un jour d'absence : il
    n'est pas compté, la règle ne permet pas de conclure.

Écarts avec la définition du rapport (`creer_vue_avis`) : le rapport compte
une disparition au dernier relevé, et ne compte jamais un avis revenu avec un
texte réécrit. Les effectifs de chaque cas sont imprimés à chaque passage.

------------------------------------------------------------------------------
L'EXPOSITION
------------------------------------------------------------------------------
  age_a_la_premiere_observation_j  jours entre la publication et le premier jour
                                   où l'avis a été vu.
  fenetre_observation_j            nombre de jours où une suppression pouvait
                                   commencer ET être confirmée : du lendemain du
                                   premier jour vu à la veille du dernier relevé
                                   de la fiche. 12 jours pour un avis vu le
                                   11 août sur une fiche suivie jusqu'au 24.
                                   Nulle ou négative : l'avis ne peut pas être
                                   supprimé au sens de la règle, le 07E l'écarte.

------------------------------------------------------------------------------
LES AUTRES COLONNES
------------------------------------------------------------------------------
Mêmes règles que le 03B, sauf le palier Local Guide :
  palier_local_guide   sans_niveau (niveau vide) / 1_4 / 5_et_plus. Décision
                       de Matthieu du 2026-09-30. Dans les données, les
                       non-guides ont un niveau de 1 à 3 et les guides 4 ou plus.
  pic d'avis           avis de la fiche ce jour-là ÷ moyenne journalière des
                       365 jours avant le 11 août, sur toute la base `reviews`
                       dédoublonnée. Pour un avis publié avant le 11 août, son
                       propre jour entre dans cette moyenne.
  enseignes            les 4 chaînes antiparasitaires sur le DÉBUT du nom, ce
                       qui attrape les succursales (« EcoShield Pest Solutions
                       Houston ») : 102 fiches au 2026-09-30, contre 93 sur le
                       nom exact du 03B. Les 2 salles espagnoles sur leur `cid`.

La table produite ne contient ni texte, ni nom, ni lien d'avis. `author_key`
est un hachage du lien d'auteur, qui sert à grouper.
==============================================================================
"""
from __future__ import annotations

import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "outils"))
from local import COPIES, PREMIERE_VAGUE, connexion  # noqa: E402

DERNIERE_VAGUE = "2026-08-24"

CHAINES_ANTIPARASITAIRES = ("ecoshield pest solutions", "insight pest solutions",
                            "pointe pest control", "bulwark exterminating")
CID_SALLES_ESPAGNOLES = ("3163466139043001754", "10346942689164695031")


def chemin_features(corpus: Path) -> Path:
    return RACINE / "data" / "local" / f"features_{corpus.stem}.parquet"


def sources(corpus: Path) -> list[Path]:
    """Les fichiers dont dépend la table : si l'un est plus récent qu'elle, elle
    est à reconstruire."""
    return [corpus, Path(__file__), COPIES / "reviews.parquet",
            COPIES / "businesses.parquet"]


SQL_CORPUS = """
CREATE TEMP TABLE corpus AS
SELECT review_id, cid, review_link, star, text, n_photos, reviewer_photo_count,
       local_guide_level, CAST(created_at AS DATE) AS created_at_day,
       deleted_detected_at IS NOT NULL AS disparu_brut
FROM read_parquet('{corpus}')
"""

# Historique complet des avis du corpus, et dernier relevé de chaque fiche.
SQL_HISTORIQUE = """
CREATE TEMP TABLE lignes AS
SELECT r.review_id, r.id,
       CAST(r.first_seen_at AS DATE)       AS vu_du,
       CAST(r.last_seen_at AS DATE)        AS vu_au,
       CAST(r.deleted_detected_at AS DATE) AS disparu_le
FROM reviews r
WHERE r.review_id IN (SELECT review_id FROM corpus);

CREATE TEMP TABLE fin_suivi_fiche AS
SELECT cid, max(CAST(last_seen_at AS DATE)) AS fin_suivi
FROM reviews
WHERE cid IN (SELECT cid FROM corpus)
GROUP BY cid;

CREATE TEMP TABLE suppression AS
WITH
ordonnees AS (
  SELECT *, max(vu_au) OVER (PARTITION BY review_id ORDER BY vu_du, id
                             ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING)
            AS vu_jusqu_au
  FROM lignes
),
absences_internes AS (
  SELECT review_id, vu_jusqu_au + 1 AS debut,
         date_diff('day', vu_jusqu_au, vu_du) - 1 AS jours
  FROM ordonnees
  WHERE vu_jusqu_au IS NOT NULL AND date_diff('day', vu_jusqu_au, vu_du) - 1 >= 1
),
periode AS (
  SELECT review_id, min(vu_du) AS premier_jour_vu, max(vu_au) AS dernier_jour_vu
  FROM lignes GROUP BY review_id
),
fin AS (
  SELECT p.review_id, p.premier_jour_vu, p.dernier_jour_vu, f.fin_suivi,
         bool_or(l.disparu_le IS NOT NULL) AS disparition_notee
  FROM periode p
  JOIN corpus c USING (review_id)
  JOIN fin_suivi_fiche f ON f.cid = c.cid
  JOIN lignes l ON l.review_id = p.review_id AND l.vu_au = p.dernier_jour_vu
  GROUP BY ALL
),
candidats AS (
  SELECT review_id, debut FROM absences_internes WHERE jours >= 2
  UNION ALL
  SELECT review_id, dernier_jour_vu + 1 FROM fin
  WHERE disparition_notee AND date_diff('day', dernier_jour_vu, fin_suivi) >= 2
),
premiere_suppression AS (
  SELECT review_id, min(debut) AS date_suppression FROM candidats GROUP BY review_id
),
absences_d_un_jour AS (
  SELECT review_id, count(*) AS n FROM absences_internes WHERE jours = 1
  GROUP BY review_id
)
SELECT f.review_id, f.premier_jour_vu, f.fin_suivi, ps.date_suppression,
       -- pour le bilan de la règle
       (f.disparition_notee AND date_diff('day', f.dernier_jour_vu, f.fin_suivi) = 1)
                                            AS disparu_au_dernier_releve,
       COALESCE(u.n, 0)                     AS absences_d_un_jour,
       (NOT f.disparition_notee AND f.dernier_jour_vu < DATE '{derniere}')
                                            AS fiche_plus_relevee
FROM fin f
LEFT JOIN premiere_suppression ps USING (review_id)
LEFT JOIN absences_d_un_jour   u  USING (review_id)
"""

# Socle des comptes par fiche et par auteur : `reviews` dédoublonnée sur
# `review_id` en gardant la dernière ligne, comme `03B_features_local.py`.
SQL_SOCLE = """
CREATE TEMP TABLE corpus_unique AS
SELECT review_id,
       arg_max(cid, id)                      AS cid,
       arg_max(review_link, id)              AS review_link,
       CAST(arg_max(created_at, id) AS DATE) AS jour
FROM reviews
WHERE cid IN (SELECT cid FROM corpus)
   OR review_link IN (SELECT review_link FROM corpus)
GROUP BY review_id
"""

SQL_FEATURES = """
WITH
fiche_jour AS (
  SELECT cid, jour, COUNT(*) AS n_avis_ce_jour FROM corpus_unique GROUP BY cid, jour
),
rythme_fiche AS (
  SELECT cid, COUNT(*) / 365.0 AS avis_par_jour_avant_vague1
  FROM corpus_unique
  WHERE jour BETWEEN DATE '{vague1}' - INTERVAL 365 DAY AND DATE '{vague1}' - INTERVAL 1 DAY
  GROUP BY cid
)
SELECT
  c.review_id,
  c.cid,
  CAST(hash(c.review_link) AS VARCHAR)                          AS author_key,

  s.date_suppression IS NOT NULL                                AS supprime,
  s.date_suppression,
  c.disparu_brut,
  s.disparu_au_dernier_releve,
  s.absences_d_un_jour,
  s.fiche_plus_relevee,

  c.created_at_day,
  s.premier_jour_vu,
  greatest(date_diff('day', c.created_at_day, s.premier_jour_vu), 0)
                                                                AS age_a_la_premiere_observation_j,
  date_diff('day', s.premier_jour_vu, s.fin_suivi) - 1          AS fenetre_observation_j,

  c.star,
  COALESCE(length(c.text), 0)                                   AS text_chars,
  COALESCE(c.n_photos > 0, FALSE)                               AS has_photo,
  COALESCE(c.reviewer_photo_count, 0)                           AS reviewer_photo_count,
  CASE WHEN c.local_guide_level IS NULL THEN 'sans_niveau'
       WHEN c.local_guide_level <= 4    THEN '1_4'
       ELSE '5_et_plus' END                                     AS palier_local_guide,

  b.industry,
  b.country,
  b.bucket,
  IF(b.country = 'US', 'US', 'Europe')                          AS region,
  COALESCE({condition_chaines}, FALSE)                          AS chaine_antiparasitaire,
  c.cid IN ({cid_salles})                                       AS salle_espagnole,

  fj.n_avis_ce_jour                                             AS n_avis_meme_jour_fiche,
  (rf.avis_par_jour_avant_vague1 IS NULL)                       AS rythme_fiche_inconnu,
  ln(fj.n_avis_ce_jour / rf.avis_par_jour_avant_vague1 + 1)     AS log_ratio_pic_journalier_fiche

FROM corpus c
LEFT JOIN suppression   s  USING (review_id)
LEFT JOIN businesses    b  ON b.cid = c.cid
LEFT JOIN rythme_fiche  rf ON rf.cid = c.cid
LEFT JOIN fiche_jour    fj ON fj.cid = c.cid AND fj.jour = c.created_at_day
"""


def construire(corpus: Path) -> Path:
    """Écrit la table de caractéristiques du corpus et renvoie son chemin."""
    corpus = Path(corpus).resolve()
    sortie = chemin_features(corpus)
    con = connexion("4GB")
    con.execute("SET threads=4")
    con.execute("SET preserve_insertion_order=false")
    con.execute("SET enable_progress_bar=false")
    sortie.parent.mkdir(parents=True, exist_ok=True)
    con.execute(f"SET temp_directory='{(sortie.parent / 'tmp_duckdb').as_posix()}'")

    con.execute(SQL_CORPUS.format(corpus=corpus.as_posix()))
    n, distincts = con.execute(
        "SELECT COUNT(*), COUNT(DISTINCT review_id) FROM corpus").fetchone()
    if n != distincts:
        raise SystemExit(f"{corpus.name} : {n - distincts} avis en double, "
                         f"une ligne par avis attendue.")
    print(f"[03C] corpus {corpus.name} : {n:,} avis".replace(",", " "))

    con.execute(SQL_HISTORIQUE.format(derniere=DERNIERE_VAGUE))
    con.execute(SQL_SOCLE)
    condition_chaines = " OR ".join(f"lower(b.name) LIKE '{nom}%'"
                                    for nom in CHAINES_ANTIPARASITAIRES)
    sql = SQL_FEATURES.format(
        vague1=PREMIERE_VAGUE, condition_chaines=condition_chaines,
        cid_salles=", ".join(f"'{c}'" for c in CID_SALLES_ESPAGNOLES))
    con.execute(f"COPY ({sql}) TO '{sortie.as_posix()}' (FORMAT parquet, COMPRESSION zstd)")

    b = con.execute(f"""
        SELECT COUNT(*), COUNT(DISTINCT review_id), COUNT(DISTINCT cid),
               COUNT(*) FILTER (supprime), COUNT(*) FILTER (disparu_brut),
               COUNT(*) FILTER (disparu_au_dernier_releve AND NOT supprime),
               COUNT(*) FILTER (absences_d_un_jour > 0 AND NOT supprime),
               COUNT(*) FILTER (fiche_plus_relevee),
               COUNT(*) FILTER (premier_jour_vu IS NULL),
               COUNT(*) FILTER (fenetre_observation_j <= 0),
               COUNT(DISTINCT cid) FILTER (chaine_antiparasitaire),
               COUNT(DISTINCT cid) FILTER (salle_espagnole),
               COUNT(*) FILTER (industry IS NULL)
        FROM '{sortie.as_posix()}'""").fetchone()
    n = lambda x: f"{x:,}".replace(",", " ")
    print(f"[03C] écrit : {sortie}\n"
          f"  {n(b[0])} avis, {n(b[2])} fiches\n"
          f"  supprimés (absents 2 jours de suite ou plus) : {n(b[3])}\n"
          f"  deleted_detected_at renseigné dans le corpus : {n(b[4])}\n"
          f"    dont non comptés, disparus au dernier relevé : {n(b[5])}\n"
          f"    avis revenus après un seul jour d'absence    : {n(b[6])}\n"
          f"  avis de fiches plus relevées avant le 24 août  : {n(b[7])}\n"
          f"  avis sans historique dans reviews               : {n(b[8])}\n"
          f"  avis qui ne peuvent pas être supprimés (fenêtre nulle) : {n(b[9])}\n"
          f"  fiches des chaînes antiparasitaires : {b[10]}, salles espagnoles : {b[11]}\n"
          f"  avis sans fiche dans businesses : {n(b[12])}")
    if b[0] != b[1]:
        raise SystemExit("La jointure a dupliqué des avis.")
    if b[8]:
        raise SystemExit("Des avis du corpus n'ont aucun historique dans reviews.")
    return sortie


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage : 03C_features_corpus.py <corpus.parquet>")
    construire(Path(sys.argv[1]))
