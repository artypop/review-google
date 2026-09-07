"""
Charger les tables pour les explorer dans Data Wrangler (VS Code).

Mode d'emploi
-------------
1. Ouvrir ce fichier dans VS Code.
2. Exécuter les cellules une par une : `Shift+Entrée` sur chaque bloc `# %%`.
   (VS Code demandera d'installer l'extension Jupyter la première fois.)
3. Dans le panneau Variables, cliquer sur l'icône Data Wrangler à côté d'un DataFrame.
   Sinon : palette de commandes -> « Data Wrangler: Open in Data Wrangler ».

Attention à la taille. `avis` fait 4,88 millions de lignes : Data Wrangler rame au-delà de
quelques centaines de milliers. Les cellules ci-dessous chargent donc des extraits ciblés.
La cellule « tout le corpus » est là si besoin, mais elle prend de la mémoire.

Pour une question précise, `scripts/query.py` est plus rapide que l'exploration visuelle.
"""

# %% Chargement
import duckdb
import pandas as pd

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 200)

db = duckdb.connect()
db.sql("CREATE VIEW avis           AS SELECT * FROM 'data/build/reviews_features.parquet'")
db.sql("CREATE VIEW etablissements AS SELECT * FROM 'data/build/business_features.parquet'")
db.sql("CREATE VIEW suivi          AS SELECT * FROM 'data/build/fresh_hazard.parquet'")

q = lambda sql: db.sql(sql).df()  # noqa: E731 — raccourci d'exploration

print(q("""
    SELECT 'avis' AS table, count(*) AS lignes FROM avis
    UNION ALL SELECT 'etablissements', count(*) FROM etablissements
    UNION ALL SELECT 'suivi', count(*) FROM suivi
"""))


# %% Les établissements — 9 048 lignes, se charge entièrement
etablissements = q("SELECT * FROM etablissements")
etablissements


# %% Les avis récents — 106 761 lignes, c'est le périmètre de l'étude
avis_frais = q("SELECT * FROM avis WHERE is_fresh")
avis_frais


# %% Le suivi jour par jour des avis récents — 1,1 M de lignes, un peu lourd
# Une ligne = un avis vérifié à un passage du robot. `died` = il a disparu à ce passage.
suivi = q("SELECT * FROM suivi")
suivi


# %% Les 24 fiches massivement purgées
fiches_purgees = q("""
    SELECT region, country, industry, bucket,
           n_reviews_panel, n_fresh, n_deleted, n_fresh_deleted,
           round(100 * purge_share, 1) AS pct_fiche,
           round(100 * velocity_30d, 1) AS pct_avis_recents,
           mean_star_w1, mean_star_delta
    FROM etablissements WHERE heavy_purge ORDER BY n_deleted DESC
""")
fiches_purgees


# %% Les avis supprimés, avec le contexte de leur fiche
supprimes = q("""
    SELECT a.*, e.industry, e.bucket, e.region AS region_fiche, e.purge_share
    FROM avis a JOIN etablissements e USING (cid)
    WHERE a.is_fresh AND a.deleted
""")
supprimes


# %% Un échantillon du corpus entier — pour regarder le stock ancien
# 200 000 lignes tirées au hasard. Le corpus complet fait 4,88 M : trop pour Data Wrangler.
echantillon = q("SELECT * FROM avis USING SAMPLE 200000 ROWS")
echantillon


# %% Sa propre question
# Remplacer par la requête voulue, puis Data Wrangler sur `resultat`.
resultat = q("""
    SELECT star, count(*) AS avis, count(*) FILTER (deleted) AS supprimes
    FROM avis WHERE is_fresh GROUP BY 1 ORDER BY 1
""")
resultat


# %% Tout le corpus — 4,88 M de lignes, plusieurs Go en mémoire
# À décommenter seulement si nécessaire.
# corpus = q("SELECT * FROM avis")
# corpus
