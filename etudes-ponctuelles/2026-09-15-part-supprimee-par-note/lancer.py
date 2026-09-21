#!/usr/bin/env python3
"""
==============================================================================
Étude ponctuelle — part des avis supprimés par note, à durée d'observation égale

Question : parmi les avis publiés du 11 au 16 août 2026, quelle part a disparu
dans les 8 jours qui ont suivi leur publication, note par note, aux États-Unis,
en Europe, et sur les deux ensemble.

Pourquoi ce périmètre. Le tableau par note de `docs/00-brief-equipe.md` porte
sur les avis publiés du 13 mai au 16 août. Leurs âges vont de 0 à 90 jours, et
le risque de suppression est divisé par 21 entre un avis du jour et un avis de
trois mois. Une proportion calculée dessus mélange la note et l'âge.

------------------------------------------------------------------------------
DEUX PASSAGES, ET LE PREMIER S'ARRÊTE
------------------------------------------------------------------------------
  --passage 1   les effectifs seuls, sans aucun taux. Il dit si les cases 2, 3
                et 4 étoiles sont assez garnies pour être citées. Puis arrêt.
  --passage 2   la mesure, sur les cases que le passage 1 a retenues.

Le passage 2 n'existe pas encore : il s'écrit une fois le passage 1 lu.
C'est l'enseignement 6 de `docs/04-enseignements.md` — sortir la colonne des
effectifs et la regarder avant de construire.

------------------------------------------------------------------------------
LE REPÉRAGE DES FICHES ATTAQUÉES SE FAIT SUR LE `cid`
------------------------------------------------------------------------------
Le flag `salle_de_sport_attaquee` de `sql/02_adding_features.bqsql` marque sur le
nom de l'enseigne : 13 fiches marquées pour 2 attaquées. Il n'est pas utilisé
ici. `CID_GYM_ATTAQUEE` porte la liste validée ; tant qu'elle est vide, le
script la déduit de `controle_cid_fiches_attaquees.sql` en gardant les fiches
marquées qui portent au moins une suppression, et le signale à l'écran.

Aucune modification de `sql/02_adding_features.bqsql`, aucune table créée.
==============================================================================
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import pandas as pd

PROJET = "client-divers"
DATASET = "reviewflowz"
TABLE = "reviews_panel_features"

# Dossier des clés de service, pas un fichier précis : son nom change à chaque
# rotation. Repris de `logistic-regression-study/python/07_regression_panel.py`.
DOSSIER_CLES = Path("/home/romain/.gcp")

# Chemins absolus : un `cd` entre deux appels a déjà fait échouer un script de
# ce projet sur un FileNotFoundError après qu'il eut écrit des fichiers
# (`docs/04-enseignements.md` § 13).
ICI = Path(__file__).resolve().parent
SORTIES = ICI / "sorties"

# Fiches de salle de sport réellement attaquées, par `cid`.
#
# Validées par Romain le 2026-09-15, sur la sortie de
# `controle_cid_fiches_attaquees.sql` :
#
#   3163466139043001754    206 avis, 192 suppressions, 99,5 % en 1 étoile
#   10346942689164695031   151 avis, 135 suppressions, 93,3 % en 1 étoile
#
# Leurs 327 suppressions redonnent le chiffre de `docs/02-donnees.md` § 1 pour le
# panel de régression. Les 11 autres fiches que le flag de nom retenait portent
# 296 avis et aucune suppression.
CID_GYM_ATTAQUEE: list[str] = [
    "3163466139043001754",
    "10346942689164695031",
]


# ---------------------------------------------------------------------------
# Connexion
# ---------------------------------------------------------------------------

def trouver_cle() -> str | None:
    """La clé de service, quel que soit son nom de fichier.

    `GOOGLE_APPLICATION_CREDENTIALS` l'emporte s'il est posé. Sinon on prend le
    seul `.json` de DOSSIER_CLES. S'il y en a plusieurs, on s'arrête : deux clés
    veut dire qu'une rotation est en cours, et prendre la mauvaise donne une
    erreur de droits incompréhensible.
    """
    if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        return None
    if not DOSSIER_CLES.is_dir():
        return None
    cles = sorted(DOSSIER_CLES.glob("*.json"))
    if len(cles) > 1:
        raise SystemExit(
            f"{len(cles)} clés dans {DOSSIER_CLES} : "
            f"{', '.join(c.name for c in cles)}.\n"
            f"Garder celle qui est active, ou poser "
            f"GOOGLE_APPLICATION_CREDENTIALS sur le bon fichier.")
    return str(cles[0]) if cles else None


def client_bigquery():
    cle = trouver_cle()
    if cle:
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = cle
        print(f"[auth] clé : {Path(cle).name}")
    from google.cloud import bigquery

    return bigquery.Client(project=PROJET)


def interroger(client, fichier_sql: str, parametres=None) -> pd.DataFrame:
    """Exécute une requête en lecture et annonce ce qu'elle lit."""
    from google.cloud import bigquery

    sql = (ICI / fichier_sql).read_text(encoding="utf-8")
    config = bigquery.QueryJobConfig(query_parameters=parametres or [])

    estime = client.query(
        sql,
        job_config=bigquery.QueryJobConfig(query_parameters=parametres or [],
                                           dry_run=True),
    ).total_bytes_processed / 1024**2
    print(f"[lecture] {fichier_sql} : {estime:.0f} Mo")

    return client.query(sql, job_config=config).to_dataframe()


# ---------------------------------------------------------------------------
# Programme
# ---------------------------------------------------------------------------

def controle_cid(client) -> list[str]:
    """Les fiches marquées par le flag de nom, avec leurs compteurs."""
    tab = interroger(client, "controle_cid_fiches_attaquees.sql")
    SORTIES.mkdir(parents=True, exist_ok=True)
    tab.to_csv(SORTIES / "2026-09-15-controle-cid-fiches-attaquees.csv",
               index=False)

    print(f"\n--- fiches portant le flag `salle_de_sport_attaquee` : "
          f"{len(tab)} ---")
    print(tab.to_string(index=False))

    if CID_GYM_ATTAQUEE:
        print(f"\n  liste validée : {len(CID_GYM_ATTAQUEE)} cid")
        return CID_GYM_ATTAQUEE

    retenus = tab.loc[tab["suppressions"] > 0, "cid"].astype(str).tolist()
    print(f"\n  PROVISOIRE : {len(retenus)} fiche(s) retenue(s), celles qui "
          f"portent au moins une suppression.")
    print(f"  À valider par Romain, puis à écrire dans CID_GYM_ATTAQUEE.")
    return retenus


def effectifs(client, cid_gym: list[str]) -> pd.DataFrame:
    from google.cloud import bigquery

    tab = interroger(
        client, "01_effectifs.sql",
        [bigquery.ArrayQueryParameter("cid_gym", "STRING", cid_gym)])

    SORTIES.mkdir(parents=True, exist_ok=True)
    tab.to_csv(SORTIES / "2026-09-15-effectifs.csv", index=False)

    print("\n--- effectifs, avis publiés du 11 au 16 août 2026 ---")
    print("    (la ligne sans note est le total de la zone)\n")
    for perimetre in tab["perimetre"].unique():
        bloc = tab[tab["perimetre"] == perimetre].copy()
        bloc["star"] = bloc["star"].astype("Int64").astype(str).replace(
            "<NA>", "total")
        print(f"  périmètre {perimetre}")
        print(bloc[["zone", "star", "avis", "supprimes_8j"]]
              .to_string(index=False))
        print()
    print(f"  écrit : sorties/2026-09-15-effectifs.csv")
    return tab


def parts(client, cid_gym: list[str]) -> pd.DataFrame:
    from google.cloud import bigquery

    tab = interroger(
        client, "02_parts.sql",
        [bigquery.ArrayQueryParameter("cid_gym", "STRING", cid_gym)])

    SORTIES.mkdir(parents=True, exist_ok=True)
    tab.to_csv(SORTIES / "2026-09-15-part-supprimee-par-note.csv", index=False)

    print("\n--- part supprimée, avis publiés du 11 au 16 août 2026 ---")
    print("    dénominateur : les avis de la case. La ligne « total » est la")
    print("    zone entière, toutes notes confondues.\n")
    for perimetre in tab["perimetre"].unique():
        bloc = tab[tab["perimetre"] == perimetre].copy()
        # Une case sous les seuils garde ses valeurs dans le CSV et disparaît de
        # l'affichage : c'est ici que se lisent les chiffres qu'on recopie.
        bloc = bloc[bloc["citable"] | bloc["star"].isna()]
        bloc["star"] = bloc["star"].astype("Int64").astype(str).replace(
            "<NA>", "total")
        print(f"  périmètre {perimetre}")
        print(bloc[["zone", "star", "avis", "supprimes_8j",
                    "part_supprimee_pct", "rr_vs_5_etoiles"]]
              .to_string(index=False))
        print()

    non_citables = tab[~tab["citable"] & tab["star"].notna()]
    print(f"  {len(non_citables)} case(s) sous les seuils, retirées de "
          f"l'affichage et gardées dans le CSV :")
    for _, ligne in non_citables.iterrows():
        print(f"    {ligne['perimetre']:<15} {ligne['zone']:<9} "
              f"{int(ligne['star'])} étoile(s) : {int(ligne['avis'])} avis, "
              f"{int(ligne['supprimes_8j'])} suppressions")

    print(f"\n  écrit : sorties/2026-09-15-part-supprimee-par-note.csv")
    return tab


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Part des avis supprimés par note, sur les avis publiés "
                    "du 11 au 16 août 2026 et observés 8 jours.")
    ap.add_argument("--passage", type=int, default=2, choices=[1, 2],
                    help="1 : les effectifs seuls. 2 : la mesure, "
                         "effectifs compris.")
    args = ap.parse_args()

    client = client_bigquery()
    cid_gym = controle_cid(client)
    effectifs(client, cid_gym)

    if args.passage == 1:
        print("=" * 78)
        print("  PASSAGE 1 TERMINÉ — aucun taux n'est calculé ici.")
        print("  Regarder la colonne des effectifs avant d'écrire le passage 2 :")
        print("  une case sous 300 avis ou sous 10 suppressions n'est pas citable.")
        print("=" * 78)
        return 0

    parts(client, cid_gym)

    print("=" * 78)
    print("  À SAVOIR EN LISANT CES CHIFFRES")
    print("=" * 78)
    print("  - Ils portent sur les avis publiés du 11 au 16 août 2026, observés")
    print("    chacun sur ses 8 premiers jours. Toute phrase qui les cite doit")
    print("    porter ces dates.")
    print("  - Une suppression survenue au 10e jour de vie de l'avis est comptée")
    print("    ici comme une absence de suppression.")
    print("  - La ligne « les_deux » réunit deux marchés dont les taux")
    print("    d'ensemble diffèrent : elle ne décrit aucun des deux.")
    print("  - Un avis publié et supprimé dans la même journée n'est pas vu.")
    print("  - La modération avant publication reste invisible.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as erreur:
        print(f"\nARRÊT : {erreur}", file=sys.stderr)
        sys.exit(1)
