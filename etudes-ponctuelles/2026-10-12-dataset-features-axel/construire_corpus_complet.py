#!/usr/bin/env python3
"""Les features des régressions, sur toute la base : data/local/features_regression_reviews_doublons_cleaned_all.parquet

    PYTHONPATH=".venv/Lib/site-packages;outils" <python uv> etudes-ponctuelles/2026-10-12-dataset-features-axel/construire_corpus_complet.py

Demande de Matthieu du 2026-10-12 : le pendant de features_03C_7_17_aout.parquet (voir
construire.py) sur reviews_doublons_cleaned_all, pour qu'Axel puisse lancer les régressions
sur tout le corpus. Vérifié le 2026-10-12 : 03C est exactement le sous-ensemble de
reviews_doublons_cleaned_all publié du 7 au 17 août (27 828 avis, mêmes dates, mêmes notes,
mêmes disparitions).

Une ligne par avis de reviews_doublons_cleaned_all (4 876 933), toutes notes. D'abord ses
25 colonnes, dans le même ordre, les horodatages passés en DATE (UTC). Puis le prénom
(annotation d'Axel, même règle que 03C_ajout_prenom.py) et les features, calculées comme
dans le 07F et 2026-10-09-regression-texte-local-guide.

LA VARIABLE EXPLIQUÉE. Le robot relève du 11 au 24 août. « Supprimé au plus tard au 7e
jour » ne s'observe que pour un avis publié pendant le relevé : un avis de 2025 supprimé à
son 3e jour n'est pas dans la base. D'où deux colonnes :
  supprime   disparu au plus tard au 7e jour, comme le 07F. Rempli seulement pour les avis
             publiés du 7 au 17 août (03C), vide ailleurs.
  disparu    deleted_detected_at renseigné : disparu pendant le relevé (4 590 avis). C'est
             la variable possible sur toute la base, avec l'âge à la première observation
             et la durée de suivi en contrôle.

Pour retrouver exactement les avis des régressions livrées : supprime non vide, star >= 4,
prenom non vide, fiche_plus_relevee faux.

  prenom, prenom_source          prénom cité (annotation d'Axel) ; vide pour 1-3 étoiles
                                 (hors_annotation) et pour les avis introuvables chez Axel ;
                                 FALSE sans texte
  region                         US ou Europe
  industry, bucket               secteur et taille de la fiche (table `businesses`)
  enseigne                       une des 6 enseignes signalées
  fin_suivi, fiche_plus_relevee  dernier jour où la fiche a été relevée ; avant le 24 août
  j_premiere_vue, j_reponse,     jours entre la publication et first_seen_at, reply_date,
  j_suppression                  deleted_detected_at
  jours_de_suivi                 jours entre first_seen_at et fin_suivi
  n_jour                         avis 4-5 étoiles publiés sur la fiche le même jour
  par_jour                       moyenne journalière des avis 4-5 étoiles de la fiche sur les
                                 365 jours avant le 11 août
  pic                            n_jour >= 3 ET n_jour >= 4 x par_jour ; propriété du jour de
                                 la fiche, remplie pour toutes les notes
  photo                          au moins une photo jointe
  reponse_j7, sans_reponse_j7    réponse au plus tard au 7e jour, et son contraire
  longueur_texte, tranche_texte  caractères sans espaces de bord ; sans, 1_40, 41_80, 81_130,
                                 131_240, 241_plus
  tranche_guide                  local_guide_level en 1_3, 4_6, 7_10 ; vide si pas de niveau

Le script vérifie que, sur les avis de 03C, chaque feature est identique à celle de
features_03C_7_17_aout.parquet.
"""
import importlib
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "logistic-regression-study" / "python"))
m = importlib.import_module("07F_regression_03C_prenom")

AXEL = RACINE / "data" / "local" / "axel_file" / "reviews_name_enriched.parquet"
FEATURES_03C = RACINE / "data" / "local" / "features_03C_7_17_aout.parquet"
SORTIE = RACINE / "data" / "local" / "features_regression_reviews_doublons_cleaned_all.parquet"
DEBUT_03C, FIN_03C = "2026-08-07", "2026-08-17"

DATES = ["created_at", "updated_at", "reply_date", "first_seen_at", "last_seen_at",
         "deleted_detected_at"]
FEATURES = ["region", "industry", "bucket", "enseigne", "fin_suivi", "fiche_plus_relevee",
            "j_premiere_vue", "j_reponse", "j_suppression", "jours_de_suivi", "n_jour",
            "par_jour", "supprime", "disparu", "photo", "reponse_j7", "sans_reponse_j7",
            "pic", "longueur_texte", "tranche_texte", "tranche_guide"]

SQL = """
WITH
r AS (
  SELECT * REPLACE ({dates}) FROM reviews_doublons_cleaned_all
),
axel AS (
  SELECT r.review_id,
         bool_or(a.has_name) FILTER (a.text = r.text) AS prenom_meme_texte,
         bool_or(a.has_name)                          AS prenom_tout_texte
  FROM r JOIN read_parquet('{axel}') a USING (review_id)
  GROUP BY r.review_id
),
fin AS (
  SELECT cid, max(last_seen_at) AS fin_suivi FROM r GROUP BY cid
),
avis_45 AS (
  SELECT cid, created_at AS jour FROM r WHERE star >= 4
),
rythme AS (
  SELECT cid, count(*) / 365.0 AS par_jour
  FROM avis_45
  WHERE jour BETWEEN DATE '{premiere}' - INTERVAL 365 DAY AND DATE '{premiere}' - INTERVAL 1 DAY
  GROUP BY cid
),
fiche_jour AS (
  SELECT cid, jour, count(*) AS n_jour FROM avis_45 GROUP BY cid, jour
),
base AS (
  SELECT r.*,
    CASE WHEN r.star <= 3                            THEN NULL
         WHEN length(trim(coalesce(r.text, ''))) = 0 THEN FALSE
         ELSE coalesce(x.prenom_meme_texte, x.prenom_tout_texte) END AS prenom,
    CASE WHEN r.star <= 3                            THEN 'hors_annotation'
         WHEN length(trim(coalesce(r.text, ''))) = 0 THEN 'sans_texte'
         WHEN x.prenom_meme_texte IS NOT NULL        THEN 'axel'
         WHEN x.prenom_tout_texte IS NOT NULL        THEN 'axel_texte_modifie'
         ELSE 'introuvable' END                                      AS prenom_source,
    if(b.country = 'US', 'US', 'Europe')                             AS region,
    b.industry, b.bucket,
    COALESCE({chaines}, FALSE) OR r.cid IN ({salles})                AS enseigne,
    f.fin_suivi,
    f.fin_suivi < DATE '{derniere}'                                  AS fiche_plus_relevee,
    date_diff('day', r.created_at, r.first_seen_at)                  AS j_premiere_vue,
    date_diff('day', r.created_at, r.reply_date)                     AS j_reponse,
    date_diff('day', r.created_at, r.deleted_detected_at)            AS j_suppression,
    date_diff('day', r.first_seen_at, f.fin_suivi)                   AS jours_de_suivi,
    coalesce(fj.n_jour, 0)                                           AS n_jour,
    coalesce(ry.par_jour, 0)                                         AS par_jour,
    COALESCE(length(trim(r.text)), 0)                                AS longueur_texte
  FROM r
  LEFT JOIN axel x        ON x.review_id = r.review_id
  LEFT JOIN businesses b  ON b.cid = r.cid
  LEFT JOIN fin f         ON f.cid = r.cid
  LEFT JOIN rythme ry     ON ry.cid = r.cid
  LEFT JOIN fiche_jour fj ON fj.cid = r.cid AND fj.jour = r.created_at
)
SELECT * EXCLUDE ({ordre}), {ordre}
FROM (
  SELECT *,
    CASE WHEN created_at BETWEEN DATE '{debut}' AND DATE '{fin_03c}'
         THEN coalesce(j_suppression <= {horizon}, FALSE)::INT END   AS supprime,
    (deleted_detected_at IS NOT NULL)::INT                           AS disparu,
    (n_jour >= {pic_min} AND n_jour >= {pic_mult} * par_jour)::INT   AS pic,
    (coalesce(n_photos, 0) > 0)::INT                                 AS photo,
    coalesce(j_reponse <= {horizon}, FALSE)::INT                     AS reponse_j7,
    1 - coalesce(j_reponse <= {horizon}, FALSE)::INT                 AS sans_reponse_j7,
    CASE WHEN longueur_texte = 0   THEN 'sans'
         WHEN longueur_texte <= 40  THEN '1_40'
         WHEN longueur_texte <= 80  THEN '41_80'
         WHEN longueur_texte <= 130 THEN '81_130'
         WHEN longueur_texte <= 240 THEN '131_240'
         ELSE '241_plus' END                                         AS tranche_texte,
    CASE WHEN local_guide_level BETWEEN 1 AND 3  THEN '1_3'
         WHEN local_guide_level BETWEEN 4 AND 6  THEN '4_6'
         WHEN local_guide_level BETWEEN 7 AND 10 THEN '7_10' END    AS tranche_guide
  FROM base
)
"""


def requete() -> str:
    chaines = " OR ".join(f"lower(b.name) LIKE '{nom}%'" for nom in m.CHAINES_ANTIPARASITAIRES)
    return SQL.format(
        dates=", ".join(f"CAST({c} AS DATE) AS {c}" for c in DATES),
        axel=AXEL.as_posix(), premiere=m.PREMIERE_VAGUE, derniere=m.DERNIERE_VAGUE,
        chaines=chaines, salles=", ".join(f"'{c}'" for c in m.CID_SALLES_ESPAGNOLES),
        debut=DEBUT_03C, fin_03c=FIN_03C, horizon=m.HORIZON_J,
        pic_min=m.PIC_MIN_AVIS, pic_mult=m.PIC_MULTIPLE, ordre=", ".join(FEATURES))


def verifier(con) -> None:
    sortie = SORTIE.as_posix()
    n, distincts, total, disparus, sans_fiche = con.execute(f"""
        SELECT count(*), count(DISTINCT review_id),
               (SELECT count(*) FROM reviews_doublons_cleaned_all),
               sum(disparu), count(*) FILTER (industry IS NULL)
        FROM '{sortie}'""").fetchone()
    print(f"  {n} avis, {disparus} disparus, {sans_fiche} sans fiche dans businesses")
    if not n == distincts == total:
        raise SystemExit("La construction a dupliqué ou perdu des avis.")

    communes = [c for c in con.execute(f"DESCRIBE SELECT * FROM '{FEATURES_03C.as_posix()}'")
                .fetchall()]
    communes = [c[0] for c in communes if c[0] != "review_id"]
    ecarts = " + ".join(
        f"count(*) FILTER (abs(a.{c} - b.{c}) > 1e-9 OR (a.{c} IS NULL) <> (b.{c} IS NULL))"
        if c == "par_jour" else f"count(*) FILTER (a.{c} IS DISTINCT FROM b.{c})"
        for c in communes)
    n_03c, n_ecarts = con.execute(f"""
        SELECT count(*), {ecarts}
        FROM '{FEATURES_03C.as_posix()}' a JOIN '{sortie}' b USING (review_id)""").fetchone()
    garde = con.execute(f"""
        SELECT count(*) FROM '{sortie}'
        WHERE supprime IS NOT NULL AND star >= 4 AND prenom IS NOT NULL
          AND NOT fiche_plus_relevee""").fetchone()[0]
    attendu = con.execute(f"SELECT count(*) FROM '{FEATURES_03C.as_posix()}'").fetchone()[0]
    print(f"  03C : {n_03c} avis retrouvés sur {attendu}, {len(communes)} colonnes comparées, "
          f"{n_ecarts} écarts ; filtre des régressions : {garde} avis")
    if n_03c != attendu or n_ecarts or garde != attendu:
        raise SystemExit("Les features ne recoupent pas celles de 03C.")


def main() -> None:
    con = m.connexion("6GB")
    con.execute(f"COPY ({requete()}) TO '{SORTIE.as_posix()}' "
                "(FORMAT parquet, COMPRESSION zstd)")
    verifier(con)
    print(f"écrit dans {SORTIE}")


if __name__ == "__main__":
    main()
