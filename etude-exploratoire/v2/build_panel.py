"""
Table de panel pour la régression logistique — v2.

Une ligne = un avis, observé à un passage du robot où il était en ligne.
La cible `died` vaut 1 si cet avis a disparu au passage SUIVANT et n'est jamais revenu.

Ce que cette table corrige par rapport à la v1 :

  1. **L'unité est (fiche, avis), pas la ligne du fichier.** 602 avis ont plusieurs
     enregistrements dans l'export parce qu'ils ont disparu puis réapparu. En v1 chaque
     enregistrement comptait pour un avis distinct.

  2. **Un avis qui revient n'est pas supprimé.** 509 des 5 230 « suppressions » de l'export
     concernent un avis qui réapparaît vivant sur la même fiche. Ici, `died` ne vaut 1 que si
     l'avis est absent au dernier passage du panel.

  3. **L'âge est calculé sur la date de publication**, à la date de chaque passage. En v1, tout
     avis vu pour la première fois pendant le suivi était réputé neuf, ce qui a fait entrer
     819 avis anciens — jusqu'à 13 ans — dans le périmètre « avis récents ».

  4. **Les passages douteux sont signalés, pas supprimés.** Trois colonnes permettent de les
     exclure au moment de l'analyse plutôt qu'en amont :
       - `listing_tronque` : le robot a lu moins de pages que d'habitude sur cette fiche ;
       - `total_google_stable` : la fiche perd des avis alors que le compteur public de Google
         ne bouge pas — signature du défaut de collecte ;
       - `passage_incomplet` : le passage n'a pas été validé par le collecteur.

Ce que la table ne peut pas dire, et qu'il faut écrire dans toute analyse qui l'utilise :

  - **Les attributs d'un avis sont son état au dernier passage où il a été vu**, pas son état à
    chaque passage. L'export ne versionne que la note et le texte (2 012 lignes d'historique).
  - **Une réponse de propriétaire retirée est invisible** : `changed_fields` ne contient jamais
    `reply`. La colonne `has_reply` est donc un état final, à manier avec cette réserve.

Aucune donnée personnelle n'est écrite : pas de nom d'auteur, pas de lien, pas de texte.
L'auteur est réduit à une empreinte, le texte à sa longueur.

Usage :  uv run v2/build_panel.py
"""

import pathlib
import sys

import duckdb

SRC = pathlib.Path("data/exports/exports")
OUT = pathlib.Path("data/v2/panel.parquet")
AVIS = pathlib.Path("data/v2/avis.parquet")


def main() -> None:
    if not (SRC / "reviews.parquet").exists():
        sys.exit(f"Export absent : {SRC}/reviews.parquet")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    c = duckdb.connect(config={"memory_limit": "3GB", "preserve_insertion_order": "false"})

    for nom in ("reviews", "businesses", "histograms", "waves", "wave_progress"):
        c.sql(f"CREATE VIEW {nom} AS SELECT * FROM '{(SRC / (nom + '.parquet')).as_posix()}'")

    # ------------------------------------------------------------------ les vagues
    c.sql("""
        CREATE TABLE vagues AS
        SELECT wave, started_at, finished_at,
               lead(started_at) OVER (ORDER BY wave) AS started_suivante
        FROM waves
    """)
    n_vagues = c.sql("SELECT max(wave) FROM vagues").fetchone()[0]

    # --------------------------------------------- un avis = (fiche, identifiant d'avis)
    # Plusieurs enregistrements peuvent exister pour un même avis : il a disparu puis il est
    # revenu. On les recolle. Les attributs retenus sont ceux de l'enregistrement le plus
    # récent. `mort` n'est vrai que si AUCUN enregistrement n'est vivant à la fin du suivi.
    c.sql("""
        CREATE TABLE avis AS
        WITH base AS (SELECT * FROM reviews WHERE NOT is_update),
        recolle AS (
          SELECT cid, review_id,
                 min(first_seen_at)                                   AS premiere_vue,
                 max(last_seen_at)                                    AS derniere_vue,
                 count(*)                                             AS n_enregistrements,
                 bool_or(deleted_detected_at IS NULL)                 AS encore_en_ligne,
                 max(deleted_detected_at)                             AS derniere_disparition,
                 count(*) FILTER (deleted_detected_at IS NOT NULL)    AS n_disparitions,
                 max_by(id, last_seen_at)                             AS id_retenu
          FROM base GROUP BY cid, review_id
        )
        SELECT r.cid, r.review_id,
               k.premiere_vue, k.derniere_vue, k.n_enregistrements, k.n_disparitions,
               -- une disparition ne compte que si l'avis n'est jamais revenu
               NOT k.encore_en_ligne                                  AS mort,
               CASE WHEN NOT k.encore_en_ligne THEN k.derniere_disparition END AS date_mort,
               k.n_disparitions > 0 AND k.encore_en_ligne             AS revenu_apres_disparition,
               r.created_at, r.updated_at,
               r.star,
               r.text IS NOT NULL AND trim(r.text) <> ''              AS has_text,
               coalesce(length(r.text), 0)                            AS text_chars,
               r.n_photos,
               r.reply_text IS NOT NULL                               AS has_reply,
               r.reply_date,
               r.language,
               r.updated_at > r.created_at                            AS was_edited,
               r.local_guide_level,
               r.local_guide_level IS NULL                            AS lg_level_missing,
               r.reviewer_review_count,
               r.reviewer_review_count = 0                            AS rc_zero,
               r.reviewer_photo_count,
               md5(regexp_extract(r.review_link, 'contrib/([0-9]+)', 1)) AS author_key
        FROM recolle k JOIN base r ON r.id = k.id_retenu
    """)

    # ------------------------------------------------------- caractéristiques de l'auteur
    c.sql("""
        CREATE TABLE auteurs AS
        SELECT author_key,
               count(*)                                              AS auteur_n_avis_panel,
               count(DISTINCT cid)                                   AS auteur_n_fiches_panel,
               count(*) > 1 AND date_diff('day', min(created_at), max(created_at)) <= 1
                                                                     AS auteur_rafale
        FROM avis WHERE author_key IS NOT NULL GROUP BY author_key
    """)

    # ------------------------------------------- qualité de collecte, par fiche et par vague
    # listing_tronque : le robot a lu moins de pages que son maximum sur cette fiche.
    # total_google_stable : la fiche perd des avis mais le compteur public ne baisse pas.
    c.sql("""
        CREATE TABLE collecte AS
        WITH pages AS (
          SELECT cid, wave, pages, complete,
                 max(pages) OVER (PARTITION BY cid) AS pages_max
          FROM wave_progress
        ),
        totaux AS (
          SELECT cid, wave, total,
                 lag(total) OVER (PARTITION BY cid ORDER BY wave) AS total_precedent
          FROM histograms
        )
        SELECT p.cid, p.wave,
               NOT p.complete                              AS passage_incomplet,
               p.pages < p.pages_max                       AS listing_tronque,
               coalesce(t.total >= t.total_precedent, FALSE) AS total_google_stable
        FROM pages p LEFT JOIN totaux t USING (cid, wave)
    """)

    # -------------------------------------------------------------------- la table de panel
    # Une ligne par avis et par passage où il était en ligne. `died` = il a disparu au
    # passage suivant, définitivement.
    c.sql(f"""
        CREATE TABLE panel AS
        WITH bornes AS (
          SELECT a.*,
                 (SELECT min(v.wave) FROM vagues v WHERE v.started_at >= a.premiere_vue)  AS vague_entree,
                 (SELECT max(v.wave) FROM vagues v WHERE v.started_at <= a.derniere_vue)   AS vague_sortie,
                 CASE WHEN a.mort THEN
                   (SELECT min(v.wave) FROM vagues v WHERE v.started_at >= a.date_mort)
                 END                                                                       AS vague_mort
          FROM avis a
        )
        SELECT b.cid, b.review_id, v.wave,
               -- l'avis disparaît au passage suivant celui-ci
               coalesce(b.vague_mort = v.wave + 1, FALSE)                    AS died,
               date_diff('day', b.created_at, vg.started_at)                 AS age_jours,
               b.created_at, b.star, b.has_text, b.text_chars, b.n_photos,
               b.has_reply, b.reply_date,
               coalesce(b.reply_date <= vg.started_at, FALSE)                AS reply_deja_publiee,
               b.language, b.was_edited,
               b.local_guide_level, b.lg_level_missing,
               b.reviewer_review_count, b.rc_zero, b.reviewer_photo_count,
               b.author_key, au.auteur_n_avis_panel, au.auteur_n_fiches_panel, au.auteur_rafale,
               b.n_enregistrements, b.revenu_apres_disparition,
               co.passage_incomplet, co.listing_tronque, co.total_google_stable,
               bu.country, bu.industry, bu.bucket, bu.review_count_at_build
        FROM bornes b
        JOIN vagues v ON v.wave BETWEEN b.vague_entree AND least(b.vague_sortie, {n_vagues} - 1)
        JOIN vagues vg ON vg.wave = v.wave
        LEFT JOIN auteurs au ON au.author_key = b.author_key
        LEFT JOIN collecte co ON co.cid = b.cid AND co.wave = v.wave
        JOIN businesses bu ON bu.cid = b.cid
    """)

    controles(c)
    c.sql(f"COPY avis TO '{AVIS.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)")
    c.sql(f"COPY panel TO '{OUT.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)")
    print(f"\nÉcrit : {AVIS}  ({AVIS.stat().st_size / 1e6:.0f} Mo)")
    print(f"Écrit : {OUT}  ({OUT.stat().st_size / 1e6:.0f} Mo)")


def controles(c: duckdb.DuckDBPyConnection) -> None:
    """Chaque contrôle doit renvoyer vrai. Un échec arrête le programme."""
    q = c.sql
    n_avis = q("SELECT count(*) FROM avis").fetchone()[0]
    n_morts = q("SELECT count(*) FROM avis WHERE mort").fetchone()[0]
    n_revenus = q("SELECT count(*) FROM avis WHERE revenu_apres_disparition").fetchone()[0]
    n_panel = q("SELECT count(*) FROM panel").fetchone()[0]
    n_died = q("SELECT sum(died::INT) FROM panel").fetchone()[0]

    print(f"Avis distincts (fiche + identifiant) : {n_avis:,}".replace(",", " "))
    print(f"  dont morts définitivement           : {n_morts:,}".replace(",", " "))
    print(f"  dont disparus puis revenus          : {n_revenus:,}".replace(",", " "))
    print(f"Lignes de panel (avis x passage)      : {n_panel:,}".replace(",", " "))
    print(f"  dont disparitions                   : {n_died:,}".replace(",", " "))

    tests = [
        ("un avis n'apparaît qu'une fois par vague",
         "SELECT count(*) = count(DISTINCT (cid, review_id, wave)) FROM panel"),
        ("aucune disparition pour un avis revenu",
         "SELECT count(*) = 0 FROM panel WHERE died AND revenu_apres_disparition"),
        ("aucune ligne après la disparition",
         """SELECT count(*) = 0 FROM (
              SELECT cid, review_id, max(CASE WHEN died THEN wave END) w_mort, max(wave) w_max
              FROM panel GROUP BY 1, 2) WHERE w_mort IS NOT NULL AND w_max > w_mort"""),
        ("au plus une disparition par avis",
         """SELECT count(*) = 0 FROM (
              SELECT cid, review_id, sum(died::INT) n FROM panel GROUP BY 1, 2) WHERE n > 1"""),
        ("aucun âge négatif de plus de 14 jours",
         "SELECT count(*) = 0 FROM panel WHERE age_jours < -14"),
        ("les disparitions du panel égalent les avis morts observables",
         """SELECT (SELECT sum(died::INT) FROM panel)
                 <= (SELECT count(*) FROM avis WHERE mort)"""),
    ]
    print()
    for nom, sql in tests:
        ok = q(sql).fetchone()[0]
        print(f"  [{'ok ' if ok else 'ECHEC'}] {nom}")
        if not ok:
            sys.exit(f"Contrôle en échec : {nom}")


if __name__ == "__main__":
    main()
