"""
Etape 0 de l'etude texte sur le panel 03B.

Question : combien d'avis du panel portent un texte, comment ils se
repartissent entre supprimes et restes en ligne, par note et par langue, et
quelle longueur font ces textes.

Aucun embedding ici. Ce script ne fait que compter, pour dimensionner l'etape
suivante et fixer la longueur maximale du modele.

Source : copie locale du panel,
`data/bigquery/03B_reviews_panel_filtered_08_04_to_08_26.parquet`, exportee de
`client-divers.reviewflowz.03B_reviews_panel_filtered_08_04_to_08_26`. Le panel
n'est pas reconstruit ici : le fichier est lu tel quel.

Perimetres produits pour chaque tableau :
  complet          tout le panel
  sans_enseignes   sans les deux salles de sport attaquees (reperees sur le
                   cid, decision de Romain du 2026-09-14) et sans les quatre
                   chaines antiparasitaires americaines (reperees sur le debut
                   du nom, cf. la note sur RACINES_CHAINES_US ci-dessous)

Aucun texte, aucun nom d'auteur, aucun lien d'avis ne sort dans les fichiers.
"""

from pathlib import Path

import duckdb
import pandas as pd

RACINE = Path(__file__).resolve().parents[2]
PANEL = RACINE / "data" / "bigquery" / "03B_reviews_panel_filtered_08_04_to_08_26.parquet"
BUSINESSES = RACINE / "data" / "bigquery" / "businesses.parquet"
SORTIES = Path(__file__).resolve().parent / "sorties"
DATE = "2026-09-21"

# Les deux salles de sport attaquees, reperees sur le cid.
CID_SALLES_ATTAQUEES = ("3163466139043001754", "10346942689164695031")

# Racines de nom des quatre chaines antiparasitaires americaines.
#
# L'egalite exacte de nom utilisee par sql/03B_adding_features.bqsql attrape
# 85 fiches et laisse passer 10 succursales nommees « EcoShield Pest Solutions
# Houston », « Bulwark Exterminating Corporate » et ainsi de suite, qui portent
# 342 avis et 9 suppressions. C'est la reserve du 2026-09-18. Le repere sur le
# debut du nom attrape les 95 fiches, et c'est celui retenu pour cette etude.
# Le drapeau du projet n'est pas modifie.
RACINES_CHAINES_US = (
    "ecoshield pest solutions",
    "insight pest",
    "pointe pest control",
    "bulwark exterminating",
)


def base(con: duckdb.DuckDBPyConnection) -> None:
    """Table de travail : un avis par ligne, avec ses drapeaux."""
    clauses = " OR ".join(f"lower(b.name) LIKE '{r}%'" for r in RACINES_CHAINES_US)
    con.execute(f"""
    CREATE OR REPLACE TEMP TABLE avis AS
    SELECT
      p.review_id,
      p.cid,
      p.review_link,
      p.star,
      p."language"                                        AS langue,
      p.deleted_detected_at IS NOT NULL                   AS supprime,
      (p.text IS NOT NULL AND LENGTH(TRIM(p.text)) > 0)   AS a_du_texte,
      COALESCE(LENGTH(TRIM(p.text)), 0)                   AS n_caracteres,
      CASE
        WHEN p.text IS NULL OR LENGTH(TRIM(p.text)) = 0 THEN 0
        ELSE LENGTH(TRIM(p.text))
             - LENGTH(REPLACE(REGEXP_REPLACE(TRIM(p.text), '\\s+', ' ', 'g'), ' ', ''))
             + 1
      END                                                 AS n_mots,
      (p.cid IN {CID_SALLES_ATTAQUEES})                   AS salle_attaquee,
      ({clauses})                                         AS chaine_us
    FROM read_parquet('{PANEL.as_posix()}') p
    LEFT JOIN read_parquet('{BUSINESSES.as_posix()}') b USING (cid)
    """)
    con.execute("""
    CREATE OR REPLACE TEMP TABLE avis2 AS
    SELECT *, (salle_attaquee OR chaine_us) AS enseigne_signalee FROM avis
    """)


def deux_perimetres(con: duckdb.DuckDBPyConnection, corps: str) -> pd.DataFrame:
    """Execute la meme requete sur le panel complet puis sans les enseignes."""
    morceaux = []
    for nom, filtre in (("complet", "TRUE"), ("sans_enseignes", "NOT enseigne_signalee")):
        df = con.execute(corps.format(filtre=filtre)).df()
        df.insert(0, "perimetre", nom)
        morceaux.append(df)
    return pd.concat(morceaux, ignore_index=True)


def a1_effectifs(con):
    return deux_perimetres(con, """
    SELECT
      supprime,
      COUNT(*)                                        AS n_avis,
      COUNT(*) FILTER (a_du_texte)                    AS n_avec_texte,
      COUNT(*) FILTER (NOT a_du_texte)                AS n_sans_texte,
      ROUND(100.0 * COUNT(*) FILTER (a_du_texte) / COUNT(*), 2) AS part_avec_texte_pct,
      COUNT(DISTINCT cid)                             AS n_fiches,
      COUNT(DISTINCT cid) FILTER (a_du_texte)         AS n_fiches_avec_texte,
      COUNT(DISTINCT review_link)                     AS n_auteurs,
      COUNT(DISTINCT review_link) FILTER (a_du_texte) AS n_auteurs_avec_texte
    FROM avis2 WHERE {filtre}
    GROUP BY supprime ORDER BY supprime
    """)


def a2_par_note(con):
    return deux_perimetres(con, """
    SELECT
      star                                          AS note,
      COUNT(*)                                      AS n_avis,
      COUNT(*) FILTER (a_du_texte)                  AS n_avec_texte,
      COUNT(*) FILTER (supprime)                    AS n_supprimes,
      COUNT(*) FILTER (supprime AND a_du_texte)     AS n_supprimes_avec_texte,
      COUNT(*) FILTER (NOT supprime AND a_du_texte) AS n_restes_avec_texte,
      ROUND(100.0 * COUNT(*) FILTER (supprime) / COUNT(*), 2) AS part_supprimee_pct,
      ROUND(100.0 * COUNT(*) FILTER (supprime AND a_du_texte)
            / NULLIF(COUNT(*) FILTER (a_du_texte), 0), 2)     AS part_supprimee_avec_texte_pct,
      ROUND(100.0 * COUNT(*) FILTER (supprime AND NOT a_du_texte)
            / NULLIF(COUNT(*) FILTER (supprime), 0), 2)       AS part_des_supprimes_sans_texte_pct
    FROM avis2 WHERE {filtre}
    GROUP BY star ORDER BY star
    """)


def a3_par_langue(con):
    return deux_perimetres(con, """
    SELECT
      COALESCE(langue, 'inconnue')                  AS langue,
      COUNT(*) FILTER (a_du_texte)                  AS n_avec_texte,
      COUNT(*) FILTER (supprime AND a_du_texte)     AS n_supprimes_avec_texte,
      ROUND(100.0 * COUNT(*) FILTER (supprime AND a_du_texte)
            / NULLIF(COUNT(*) FILTER (a_du_texte), 0), 2) AS part_supprimee_pct,
      COUNT(DISTINCT cid) FILTER (a_du_texte)       AS n_fiches
    FROM avis2 WHERE {filtre}
    GROUP BY 1 HAVING COUNT(*) FILTER (a_du_texte) > 0
    ORDER BY n_avec_texte DESC
    """)


def a4_longueurs(con):
    """Longueur des textes. Sert a fixer max_seq_length du modele."""
    return deux_perimetres(con, """
    SELECT
      supprime,
      COUNT(*)                                       AS n_avec_texte,
      ROUND(AVG(n_caracteres))                       AS moyenne_caracteres,
      CAST(MEDIAN(n_caracteres) AS INT)              AS mediane_caracteres,
      CAST(QUANTILE_CONT(n_caracteres, 0.90) AS INT) AS neuf_sur_dix_sous_caracteres,
      CAST(QUANTILE_CONT(n_caracteres, 0.99) AS INT) AS cent_moins_un_sur_cent_sous_caracteres,
      MAX(n_caracteres)                              AS max_caracteres,
      ROUND(AVG(n_mots))                             AS moyenne_mots,
      CAST(MEDIAN(n_mots) AS INT)                    AS mediane_mots,
      CAST(QUANTILE_CONT(n_mots, 0.90) AS INT)       AS neuf_sur_dix_sous_mots,
      CAST(QUANTILE_CONT(n_mots, 0.99) AS INT)       AS cent_moins_un_sur_cent_sous_mots,
      MAX(n_mots)                                    AS max_mots
    FROM avis2 WHERE {filtre} AND a_du_texte
    GROUP BY supprime ORDER BY supprime
    """)


def a5_enseignes(con):
    """Poids des six enseignes dans la population qui porte du texte."""
    return con.execute("""
    SELECT
      CASE WHEN salle_attaquee THEN 'salles_attaquees'
           WHEN chaine_us      THEN 'chaines_antiparasitaires_us'
           ELSE 'reste_du_panel' END                AS groupe,
      COUNT(DISTINCT cid)                           AS n_fiches,
      COUNT(*)                                      AS n_avis,
      COUNT(*) FILTER (a_du_texte)                  AS n_avec_texte,
      COUNT(*) FILTER (supprime)                    AS n_supprimes,
      COUNT(*) FILTER (supprime AND a_du_texte)     AS n_supprimes_avec_texte,
      ROUND(100.0 * COUNT(*) FILTER (supprime AND a_du_texte)
            / NULLIF(COUNT(*) FILTER (a_du_texte), 0), 2) AS part_supprimee_pct
    FROM avis2
    GROUP BY 1 ORDER BY n_avis DESC
    """).df()


def a6_cases(con):
    """Cases note x langue de la population qui porte du texte.

    Chaque case est une comparaison possible pour la route B. Une case ou les
    supprimes se comptent sur les doigts d'une main ne portera aucun resultat,
    et il vaut mieux le savoir avant de lancer le modele.
    """
    return deux_perimetres(con, """
    WITH grandes AS (
      SELECT langue FROM avis2
      WHERE {filtre} AND a_du_texte AND langue IS NOT NULL
      GROUP BY langue HAVING COUNT(*) >= 500
    )
    SELECT
      a.star                                        AS note,
      CASE WHEN a.langue IN (SELECT langue FROM grandes) THEN a.langue
           ELSE 'autres_langues' END                AS langue,
      COUNT(*)                                      AS n_avec_texte,
      COUNT(*) FILTER (a.supprime)                  AS n_supprimes,
      COUNT(*) FILTER (NOT a.supprime)              AS n_restes,
      ROUND(100.0 * COUNT(*) FILTER (a.supprime) / COUNT(*), 2) AS part_supprimee_pct,
      COUNT(DISTINCT a.cid)                         AS n_fiches,
      COUNT(DISTINCT a.cid) FILTER (a.supprime)     AS n_fiches_avec_suppression
    FROM avis2 a WHERE {filtre} AND a.a_du_texte
    GROUP BY 1, 2 ORDER BY 1, n_avec_texte DESC
    """)


def main() -> None:
    SORTIES.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(config={"memory_limit": "2GB", "threads": 4})
    base(con)

    tableaux = {
        "A1-effectifs-textes": a1_effectifs(con),
        "A2-par-note": a2_par_note(con),
        "A3-par-langue": a3_par_langue(con),
        "A4-longueurs": a4_longueurs(con),
        "A5-enseignes": a5_enseignes(con),
        "A6-cases-note-langue": a6_cases(con),
    }
    for nom, df in tableaux.items():
        chemin = SORTIES / f"{DATE}-{nom}.csv"
        df.to_csv(chemin, index=False)
        print(f"\n===== {nom} -> {chemin.name} =====")
        print(df.to_string(index=False))
    con.close()


if __name__ == "__main__":
    main()
