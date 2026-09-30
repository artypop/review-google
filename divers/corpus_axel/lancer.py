"""Relance les calculs de `consolidation/` sur le corpus d'Axel.

    uv run python divers/corpus_axel/lancer.py 0_controle_corpus   # ce que contient la table
    uv run python divers/corpus_axel/lancer.py 1_features_axel     # écrit la table de caractéristiques
    uv run python divers/corpus_axel/lancer.py 2_3_taux            # un script de la consolidation
    uv run python divers/corpus_axel/lancer.py                     # les sept, l'un après l'autre

LE CORPUS D'AXEL
  Les avis de 03B (publiés du 4 au 17 août 2026), plus tous les avis supprimés
  pendant le suivi, quelle que soit leur date de publication : la table
  `corpus_axel`. Ses caractéristiques sont dans `reviews_panel_features_axel`,
  construite par `sql/1_features_axel.bqsql`.

MÊME CODE, AUTRE TABLE
  Les scripts et les requêtes de `consolidation/` sont exécutés tels quels.
  Deux choses changent, ici et nulle part ailleurs :
    - dans chaque requête, `reviews_panel_features_03B` devient
      `reviews_panel_features_axel` ;
    - les CSV et les figures vont dans `divers/corpus_axel/sorties/`.

  Les scripts qui lisent la base entière (1a à 1d, 2.1, 2.2) ne sont pas relancés.
"""
import runpy
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
CONSOLIDATION = ICI.parents[1] / "consolidation"
sys.path.insert(0, str(CONSOLIDATION))

import commun  # noqa: E402  (après l'ajout de `consolidation/` au chemin)

TABLE_03B = "reviews_panel_features_03B"
TABLE_AXEL = "reviews_panel_features_axel"

# Les scripts de la consolidation qui lisent le panel.
SCRIPTS = ["2_3_taux", "3a_jour_par_jour", "3b_regression_reponse", "4_0_niveaux_local_guide",
           "4a_quelle_fiche", "4b_quel_avis", "5_reponse_jour_par_jour"]

commun.SORTIES = ICI / "sorties"
commun.FIGURES = commun.SORTIES / "figures"


def requete(nom: str):
    """La requête `consolidation/sql/<nom>.sql`, lue sur la table d'Axel."""
    texte = (commun.SQL / f"{nom}.sql").read_text(encoding="utf-8")
    if TABLE_03B not in texte:
        raise SystemExit(f"sql/{nom}.sql ne lit pas {TABLE_03B} : rien à remplacer.")
    df = commun.client().query(texte.replace(TABLE_03B, TABLE_AXEL)).to_dataframe()
    print(f"  consolidation/sql/{nom}.sql sur {TABLE_AXEL} -> {len(df)} lignes")
    return df


def controle_corpus() -> None:
    """Ce que contient `corpus_axel`, comparé à 03B, et le profil des avis ajoutés."""
    for nom in ["0_controle_corpus", "0b_avis_ajoutes"]:
        texte = (ICI / "sql" / f"{nom}.sql").read_text(encoding="utf-8")
        df = commun.client().query(texte).to_dataframe()
        print(df.to_string(index=False))
        commun.ecrire_csv(df, nom)


def features_axel() -> None:
    """Écrit `reviews_panel_features_axel` dans BigQuery. Seule écriture de ce dossier."""
    texte = (ICI / "sql" / "1_features_axel.bqsql").read_text(encoding="utf-8")
    commun.client().query(texte).result()
    table = commun.client().get_table(f"{commun.PROJET}.reviewflowz.{TABLE_AXEL}")
    print(f"  {TABLE_AXEL} : {table.num_rows} lignes, {len(table.schema)} colonnes")


def taille_4b() -> None:
    """La taille du calcul 4b sur chaque table, comptée dans BigQuery sans lancer le modèle."""
    import pandas as pd
    jours = (commun.SQL / "4b_jours.sql").read_text(encoding="utf-8")
    lignes = []
    for corpus, table in [("03B", TABLE_03B), ("corpus d'Axel", TABLE_AXEL)]:
        texte = f"""
        WITH j AS ({jours.replace(TABLE_03B, table)}),
        s AS (SELECT strate, COUNT(*) AS n, SUM(y) AS k FROM j GROUP BY strate)
        SELECT COUNT(*) AS journees_de_fiche, SUM(n) AS avis_jours, SUM(k) AS suppressions,
               MAX(n) AS avis_dans_la_plus_grosse_journee,
               MAX(k) AS suppressions_max_dans_une_journee
        FROM s"""
        lignes.append({"corpus": corpus, **commun.client().query(texte).to_dataframe().iloc[0]})
    df = pd.DataFrame(lignes)
    print(df.to_string(index=False))
    commun.ecrire_csv(df, "0c_taille_4b")


commun.requete = requete
A_PART = {"0_controle_corpus": controle_corpus, "0c_taille_4b": taille_4b,
          "1_features_axel": features_axel}

for nom in sys.argv[1:] or SCRIPTS:
    print(f"--- {nom}")
    if nom in A_PART:
        A_PART[nom]()
    elif nom in SCRIPTS:
        runpy.run_path(str(CONSOLIDATION / f"{nom}.py"), run_name="__main__")
    else:
        raise SystemExit(f"Script inconnu : {nom}. Connus : {', '.join(list(A_PART) + SCRIPTS)}")
