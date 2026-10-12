#!/usr/bin/env python3
"""Le dataset des régressions finales : data/local/features_03C_7_17_aout.parquet

    PYTHONPATH=".venv/Lib/site-packages;outils" <python uv> etudes-ponctuelles/2026-10-12-dataset-features-axel/construire.py

Demande de Matthieu du 2026-10-12, pour qu'Axel puisse reprendre le travail. Consigne de
Romain : sortir en parquet reviews_doublons_cleaned_all et 03C_7_17_aout, plus la requête SQL
ou, à défaut, le dataset avec les features. La requête du 07F ne tourne pas seule (DuckDB sur
les copies locales, `businesses`, prénom d'Axel, puis calculs en Python) : on sort le dataset.

Une ligne par avis entrant dans les régressions de livrables/restitution_finale_v2/ : avis
4-5 étoiles de 03C publiés du 7 au 17 août, sans les avis sans annotation de prénom ni ceux
des fiches plus relevées avant le 24 août (`charger()` du 07F). La régression texte + Local
Guide écarte en plus les avis sans niveau Local Guide (`local_guide_level` vide) ; ils restent
ici.

Rien n'est recalculé autrement : `charger()` et `variable_reponse()` du 07F, longueur du
texte et tranches de 2026-10-09-regression-texte-local-guide. Les dates sont des DATE (UTC),
comme dans 03C.

D'abord toutes les colonnes de data/local/03C_7_17_aout_prenom.parquet, dans le même ordre
(texte, auteur, lien, réponse, photos, dates, `prenom` et `prenom_source` d'Axel…). Le texte
et les noms d'auteurs restent hors de tout fichier versionné. Puis les features :

  region                         US ou Europe
  industry, bucket               secteur et taille de la fiche (table `businesses`)
  enseigne                       une des 6 enseignes signalées (4 chaînes antiparasitaires,
                                 2 salles espagnoles)
  j_premiere_vue, j_reponse,     jours entre la publication et first_seen_at, reply_date,
  j_suppression                  deleted_detected_at
  n_jour                         avis 4-5 étoiles publiés sur la fiche le même jour, celui-ci
                                 compris
  par_jour                       moyenne journalière des avis 4-5 étoiles de la fiche sur les
                                 365 jours avant le 11 août (reviews_doublons_cleaned_all)
  supprime                       variable expliquée : disparu au plus tard au 7e jour
  photo                          au moins une photo jointe
  reponse_j7, sans_reponse_j7    réponse au plus tard au 7e jour, et son contraire (la
                                 référence des régressions est « réponse »)
  pic                            n_jour >= 3 ET n_jour >= 4 x par_jour
  longueur_texte, tranche_texte  caractères sans espaces de bord ; sans, 1_40, 41_80, 81_130,
                                 131_240, 241_plus
  tranche_guide                  local_guide_level en 1_3, 4_6, 7_10 ; vide si pas de niveau

Le script vérifie que le dataset seul redonne les rapports de cotes livrés dans
regression_logistique/ et regression_logistique_2/.
"""
import importlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

sys.stdout.reconfigure(encoding="utf-8")
RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "logistic-regression-study" / "python"))
sys.path.insert(0, str(RACINE / "etudes-ponctuelles" / "2026-10-09-regression-texte-local-guide"))
m = importlib.import_module("07F_regression_03C_prenom")
tl = importlib.import_module("calcul")

SORTIE = RACINE / "data" / "local" / "features_03C_7_17_aout.parquet"
LIVRES = RACINE / "livrables" / "restitution_finale_v2"

FEATURES = ["region", "industry", "bucket", "enseigne", "j_premiere_vue", "j_reponse",
            "j_suppression", "n_jour", "par_jour", "supprime", "photo", "reponse_j7",
            "sans_reponse_j7", "pic", "longueur_texte", "tranche_texte", "tranche_guide"]


def construire() -> pa.Table:
    df = m.charger()
    if m.variable_reponse(df) != "sans_reponse_j7":
        raise SystemExit("La référence de la réponse a changé : revoir le dataset.")
    con = m.connexion("4GB")
    corpus = m.CORPUS.as_posix()
    extra = con.execute(f"""
        SELECT review_id, COALESCE(length(trim(text)), 0) AS longueur_texte, local_guide_level
        FROM '{corpus}' WHERE star >= 4""").df()
    n0 = len(df)
    df = df.merge(extra, on="review_id", how="left", validate="one_to_one")
    if len(df) != n0 or df["longueur_texte"].isna().any():
        raise SystemExit("Jointure de la longueur incomplète.")
    df["tranche_texte"] = pd.cut(df["longueur_texte"], tl.BORNES_TEXTE,
                                 labels=tl.TEXTE).astype(str)
    df["tranche_guide"] = None
    for nom, (a, b) in tl.GUIDE.items():
        df.loc[df["local_guide_level"].between(a, b), "tranche_guide"] = nom
    if df["local_guide_level"].notna().sum() != df["tranche_guide"].notna().sum():
        raise SystemExit("Niveau Local Guide hors de 1 à 10.")
    for c in ["j_premiere_vue", "j_reponse", "j_suppression"]:
        df[c] = df[c].astype("Int64")

    # Les colonnes de 03C sont relues dans le parquet pour garder leurs types (DATE, entiers).
    calc = df[["review_id"] + FEATURES]
    con.register("calc", calc)
    table = con.execute(f"""
        SELECT c.*, {", ".join(f"k.{x}" for x in FEATURES)}
        FROM '{corpus}' c JOIN calc k USING (review_id)""").fetch_arrow_table()
    if table.num_rows != n0:
        raise SystemExit("Jointure avec 03C incomplète.")
    return table


def verifier(df: pd.DataFrame) -> None:
    """Refait les deux régressions livrées à partir du dataset seul."""
    d = df.copy()
    base = ["prenom", "photo", "sans_reponse_j7", "pic"]
    d["prenom"] = d["prenom"].astype(int)
    ecarts = []

    livre = pd.read_csv(LIVRES / "regression_logistique_2" / "regression_secteur_taille.csv")
    for passage in ["US", "Europe", "tous"]:
        x = d if passage == "tous" else d[d["region"] == passage]
        res = m.ajuster(x, base, secteur_taille=True)
        attendu = livre[livre["passage"] == passage].set_index("parametre")["rapport_de_cotes"]
        ecarts.append(np.abs(np.exp(res.params) - attendu.loc[res.params.index]).max())

    d = d[d["tranche_guide"].notna()].copy()
    for t in tl.TEXTE[1:]:
        d[f"texte_{t}"] = (d["tranche_texte"] == t).astype(int)
    for g in list(tl.GUIDE)[1:]:
        d[f"guide_{g}"] = (d["tranche_guide"] == g).astype(int)
    variables = (base + [f"texte_{t}" for t in tl.TEXTE[1:]]
                 + [f"guide_{g}" for g in list(tl.GUIDE)[1:]])
    for passage, suffixe in [("US", "us"), ("Europe", "europe")]:
        x = d[d["region"] == passage]
        res = m.ajuster(x, variables, secteur_taille=True)
        livre = pd.read_csv(LIVRES / "regression_logistique"
                            / f"regression_texte_local_guide_{suffixe}.csv")
        attendu = livre.set_index("parametre")["rapport_de_cotes"]
        ecarts.append(np.abs(np.exp(res.params) - attendu.loc[res.params.index]).max())

    print(f"  écart maximal aux rapports de cotes livrés : {max(ecarts):.2e}")
    if max(ecarts) > 1e-6:
        raise SystemExit("Le dataset ne redonne pas les régressions livrées.")


def main() -> None:
    table = construire()
    df = table.to_pandas()
    verifier(df)
    pq.write_table(table, SORTIE)
    print(f"{len(df)} avis, {df['cid'].nunique()} fiches, {int(df['supprime'].sum())} "
          f"suppressions au plus tard au 7e jour, {df['tranche_guide'].isna().sum()} sans "
          f"niveau Local Guide, {table.num_columns} colonnes\nécrit dans {SORTIE}")


if __name__ == "__main__":
    main()
