"""
Construction des tables d'analyse — étude suppressions d'avis Google.

Produit trois parquet dans data/build/ :

  reviews_features.parquet  1 ligne / avis de base (4,88 M). Table maîtresse, corpus entier.
                            Le stock ancien y est conservé : il sert au Test 2, aux features
                            d'établissement et aux comparaisons frais / ancien.
  business_features.parquet 1 ligne / établissement (9 048). Support de l'analyse A.
  fresh_hazard.parquet      1 ligne / (avis frais x vague où il est vivant). Support de
                            l'analyse B, en temps discret : cible = meurt-il à cette vague.

Aucune colonne identifiante n'est écrite (ni nom, ni lien, ni texte) : l'auteur est réduit
à un hash. Voir CLAUDE.md, section données personnelles.

Usage :  .venv/bin/python scripts/build_tables.py
"""

import pathlib
import sys

import duckdb

SRC = pathlib.Path("data/exports/exports")
OUT = pathlib.Path("data/build")
WAVE1 = "TIMESTAMP '2026-08-11 07:00:00'"  # fin de la vague 1 : sépare stock et flux
FRESH_DAYS = 30


def main() -> None:
    if not SRC.exists():
        sys.exit(f"Données introuvables : {SRC}")
    OUT.mkdir(parents=True, exist_ok=True)

    c = duckdb.connect()
    c.sql(f"SET file_search_path='{SRC.resolve()}'")

    # ------------------------------------------------------------------ socle
    c.sql("""
        CREATE VIEW waves AS
        SELECT wave, started_at, finished_at FROM 'waves.parquet'
    """)
    c.sql("""
        CREATE VIEW biz AS
        SELECT cid, place_id, name, country, industry, bucket, review_count_at_build,
               CASE WHEN country = 'US' THEN 'US' ELSE 'EU' END AS region
        FROM 'businesses.parquet'
    """)
    # Lignes de base uniquement. review_id n'est pas unique : voir README de l'export.
    c.sql(f"""
        CREATE VIEW base AS
        SELECT
            r.id                AS row_id,
            r.cid,
            r.review_id,
            md5(regexp_extract(r.review_link, 'contrib/([0-9]+)', 1)) AS author_key,
            r.star,
            r.text,
            r.language,
            r.created_at, r.updated_at,
            r.reviewer_review_count, r.reviewer_photo_count,
            r.local_guide_level,
            r.n_photos,
            r.reply_text, r.reply_date,
            r.first_seen_at, r.last_seen_at, r.deleted_detected_at,
            r.deleted_detected_at IS NOT NULL AS deleted,
            r.first_seen_at >= {WAVE1} AS born_during_panel
        FROM 'reviews.parquet' r
        WHERE NOT r.is_update
    """)

    # ------------------------------------------------- agrégats auteur & fiche
    # Multi-présence de l'auteur dans le panel + rafale (plusieurs avis le même jour).
    c.sql("""
        CREATE TABLE author_agg AS
        SELECT author_key,
               count(*)                                   AS author_n_panel_reviews,
               count(DISTINCT cid)                        AS author_n_panel_biz,
               date_diff('day', min(created_at), max(created_at)) AS author_span_days,
               count(*) > 1
                 AND date_diff('day', min(created_at), max(created_at)) <= 1
                                                          AS author_same_day_burst
        FROM base GROUP BY author_key
    """)

    # Langue dominante de la fiche : évite une table de correspondance pays -> langue.
    c.sql("""
        CREATE TABLE biz_lang AS
        SELECT cid, language AS modal_language FROM (
            SELECT cid, language,
                   row_number() OVER (PARTITION BY cid ORDER BY count(*) DESC, language) AS rn
            FROM base WHERE language IS NOT NULL GROUP BY cid, language
        ) WHERE rn = 1
    """)

    # Vélocité : part du stock reçue dans les 30 j précédant la vague 1.
    c.sql(f"""
        CREATE TABLE biz_agg AS
        SELECT cid,
               count(*)                                            AS n_reviews_panel,
               count(*) FILTER (deleted)                            AS n_deleted,
               count(*) FILTER (NOT born_during_panel
                    AND date_diff('day', created_at, {WAVE1}) <= 30) AS n_new_30d,
               count(*) FILTER (born_during_panel)                  AS n_born_during_panel,
               avg(star)                                            AS mean_star_panel
        FROM base GROUP BY cid
    """)

    # Trajectoire de note sur les 14 vagues, reconstruite depuis histograms.
    c.sql("""
        CREATE TABLE biz_hist AS
        WITH per_wave AS (
            SELECT cid, wave, total,
                   (one + 2*two + 3*three + 4*four + 5*five) / nullif(total, 0) AS mean_star
            FROM 'histograms.parquet'
        )
        SELECT cid,
               max(mean_star) FILTER (wave = 1)                    AS mean_star_w1,
               max(mean_star) FILTER (wave = 14)                   AS mean_star_w14,
               max(mean_star) FILTER (wave = 14)
                 - max(mean_star) FILTER (wave = 1)                AS mean_star_delta,
               max(total)     FILTER (wave = 1)                    AS google_total_w1,
               max(total)     FILTER (wave = 14)                   AS google_total_w14
        FROM per_wave GROUP BY cid
    """)

    # ------------------------------------------------------- table 1 : avis
    # reviewer_review_count = 0 et local_guide_level NULL sont deux états transitoires de
    # compte neuf (vérifié manuellement le 2026-09-06) : jamais un zéro numérique.
    c.sql(f"""
        CREATE TABLE reviews_features AS
        SELECT
            b.row_id, b.cid, b.review_id, b.author_key,

            -- cible et fenêtre d'observation
            b.deleted,
            b.deleted_detected_at,
            b.first_seen_at, b.last_seen_at, b.created_at,
            b.born_during_panel,
            date_diff('day', b.created_at, {WAVE1})             AS age_days_w1,
            date_diff('day', b.created_at, {WAVE1}) BETWEEN 0 AND {FRESH_DAYS} - 1
              OR b.born_during_panel                            AS is_fresh,

            -- contenu
            b.star,
            b.text IS NOT NULL AND length(trim(b.text)) > 0      AS has_text,
            coalesce(length(b.text), 0)                          AS text_chars,
            CASE WHEN b.text IS NULL THEN 0
                 ELSE length(b.text) - length(replace(trim(b.text), ' ', '')) + 1
            END                                                  AS text_words,
            b.n_photos,
            b.n_photos > 0                                       AS has_photo,
            b.reply_text IS NOT NULL                             AS has_reply,
            b.reply_date,
            b.language,
            b.language IS NOT NULL AND l.modal_language IS NOT NULL
              AND b.language <> l.modal_language                 AS lang_off_modal,
            b.updated_at > b.created_at                          AS was_edited,

            -- auteur : niveau et compteurs, avec les manquants explicites
            b.local_guide_level,
            b.local_guide_level IS NULL                          AS lg_level_missing,
            b.reviewer_review_count,
            b.reviewer_review_count = 0                          AS rc_zero,
            CASE WHEN b.reviewer_review_count > 0
                 THEN ln(b.reviewer_review_count) END            AS log_rc,
            b.reviewer_photo_count,
            CASE WHEN b.reviewer_photo_count > 0
                 THEN ln(b.reviewer_photo_count) END             AS log_pc,
            -- signature « premier avis » : niveau absent ET compteur à 0
            b.local_guide_level IS NULL
              AND b.reviewer_review_count = 0                    AS new_account,

            a.author_n_panel_reviews, a.author_n_panel_biz,
            a.author_span_days, a.author_same_day_burst,

            -- établissement
            z.region, z.country, z.industry, z.bucket, z.review_count_at_build
        FROM base b
        LEFT JOIN biz_lang   l USING (cid)
        LEFT JOIN author_agg a USING (author_key)
        LEFT JOIN biz        z USING (cid)
    """)
    c.sql(f"COPY reviews_features TO '{OUT}/reviews_features.parquet' (FORMAT parquet, COMPRESSION zstd)")

    # -------------------------------------------- table 2 : établissements
    c.sql(f"""
        CREATE TABLE business_features AS
        SELECT
            z.cid, z.region, z.country, z.industry, z.bucket,
            z.review_count_at_build,
            g.n_reviews_panel, g.n_born_during_panel, g.mean_star_panel,
            g.n_deleted,
            g.n_deleted > 0                                        AS touched,
            g.n_deleted::DOUBLE / nullif(g.n_reviews_panel, 0)     AS purge_share,
            -- Purge caractérisée : plus de 5 % des avis ET au moins 10 suppressions.
            -- Le seuil en volume est indispensable : sans lui, une fiche de 2 avis dont 1 saute
            -- compte comme « purgée à 50 % ». 7 des 37 fiches étaient dans ce cas.
            g.n_deleted::DOUBLE / nullif(g.n_reviews_panel, 0) > 0.05
              AND g.n_deleted >= 10                                AS heavy_purge,
            g.n_new_30d,
            g.n_new_30d::DOUBLE / nullif(g.n_reviews_panel, 0)     AS velocity_30d,
            h.mean_star_w1, h.mean_star_w14, h.mean_star_delta,
            h.google_total_w1, h.google_total_w14,
            f.n_fresh, f.n_fresh_deleted
        FROM biz z
        LEFT JOIN biz_agg  g USING (cid)
        LEFT JOIN biz_hist h USING (cid)
        LEFT JOIN (
            SELECT cid, count(*) AS n_fresh, count(*) FILTER (deleted) AS n_fresh_deleted
            FROM reviews_features WHERE is_fresh GROUP BY cid
        ) f USING (cid)
    """)
    c.sql(f"COPY business_features TO '{OUT}/business_features.parquet' (FORMAT parquet, COMPRESSION zstd)")

    # ------------------------------- table 3 : risque en temps discret (frais)
    # Un avis est exposé à la vague w s'il a été vu avant w et n'est pas déjà supprimé.
    # Il meurt à la vague w si sa suppression a été détectée dans la fenêtre de cette vague.
    c.sql("""
        CREATE TABLE fresh_hazard AS
        WITH w AS (SELECT wave, started_at, finished_at FROM waves WHERE wave >= 2),
        died AS (
            SELECT f.row_id,
                   (SELECT max(w2.wave) FROM w w2 WHERE w2.started_at <= f.deleted_detected_at)
                     AS death_wave
            FROM reviews_features f WHERE f.is_fresh AND f.deleted
        )
        SELECT
            f.row_id, f.cid, f.author_key,
            w.wave,
            date_diff('day', f.created_at, w.started_at)   AS age_days,
            coalesce(d.death_wave = w.wave, FALSE)         AS died,
            f.star, f.has_text, f.text_chars, f.text_words, f.n_photos, f.has_photo,
            f.has_reply, f.lang_off_modal, f.was_edited,
            f.local_guide_level, f.lg_level_missing, f.reviewer_review_count, f.rc_zero,
            f.log_rc, f.log_pc, f.new_account,
            f.author_n_panel_reviews, f.author_n_panel_biz, f.author_same_day_burst,
            f.region, f.country, f.industry, f.bucket, f.born_during_panel
        FROM reviews_features f
        JOIN w ON f.first_seen_at < w.started_at
              AND (f.deleted_detected_at IS NULL OR f.deleted_detected_at >= w.started_at)
        LEFT JOIN died d USING (row_id)
        WHERE f.is_fresh
    """)
    c.sql(f"COPY fresh_hazard TO '{OUT}/fresh_hazard.parquet' (FORMAT parquet, COMPRESSION zstd)")

    # ------------------------------------------------------------- contrôles
    checks(c)


def checks(c: duckdb.DuckDBPyConnection) -> None:
    """Contrôles de cohérence. Toute ligne FAIL doit être traitée avant d'analyser."""
    print("\n=== Contrôles de cohérence ===")
    tests = [
        ("avis de base = 4 878 151",
         "SELECT count(*) = 4878151 FROM reviews_features"),
        ("suppressions = 5 230",
         "SELECT count(*) FILTER (deleted) = 5230 FROM reviews_features"),
        ("établissements = 9 048",
         "SELECT count(*) = 9048 FROM business_features"),
        ("aucun row_id dupliqué",
         "SELECT count(*) = count(DISTINCT row_id) FROM reviews_features"),
        ("aucune colonne identifiante (nom / lien / texte brut)",
         """SELECT count(*) = 0 FROM (SELECT column_name FROM information_schema.columns
            WHERE table_name = 'reviews_features'
              AND column_name IN ('text','reviewer_name','review_link','reviewer_avatar'))"""),
        ("log_rc NULL exactement quand le compteur est à 0",
         "SELECT count(*) = 0 FROM reviews_features WHERE (log_rc IS NULL) <> rc_zero"),
        ("chaque suppression fraîche tombe sur exactement une vague",
         """SELECT count(*) = (SELECT count(*) FROM reviews_features WHERE is_fresh AND deleted)
            FROM (SELECT row_id FROM fresh_hazard WHERE died GROUP BY row_id)"""),
        ("aucune ligne d'exposition après la mort",
         """SELECT count(*) = 0 FROM (
              SELECT row_id, max(CASE WHEN died THEN wave END) dw, max(wave) mw
              FROM fresh_hazard GROUP BY row_id) WHERE dw IS NOT NULL AND mw > dw"""),
        ("died n'est jamais NULL",
         "SELECT count(*) = 0 FROM fresh_hazard WHERE died IS NULL"),
        ("purge_share dans [0, 1]",
         "SELECT count(*) = 0 FROM business_features WHERE purge_share < 0 OR purge_share > 1"),
    ]
    ok = True
    for label, sql in tests:
        passed = bool(c.sql(sql).fetchone()[0])
        ok &= passed
        print(f"  [{'OK  ' if passed else 'FAIL'}] {label}")

    print("\n=== Volumétrie ===")
    print(c.sql("""
        SELECT 'reviews_features' AS table, count(*) AS lignes,
               count(*) FILTER (deleted) AS suppressions,
               round(100.0 * count(*) FILTER (deleted) / count(*), 3) AS taux_pct
        FROM reviews_features
        UNION ALL SELECT 'dont frais', count(*), count(*) FILTER (deleted),
               round(100.0 * count(*) FILTER (deleted) / count(*), 3)
        FROM reviews_features WHERE is_fresh
        UNION ALL SELECT 'fresh_hazard (avis x vague)', count(*), count(*) FILTER (died),
               round(100.0 * count(*) FILTER (died) / count(*), 3)
        FROM fresh_hazard
        UNION ALL SELECT 'business_features', count(*), count(*) FILTER (touched), NULL
        FROM business_features
    """).df().to_string(index=False))

    if not ok:
        sys.exit("\nAu moins un contrôle a échoué.")
    print("\nTous les contrôles passent.")


if __name__ == "__main__":
    main()
