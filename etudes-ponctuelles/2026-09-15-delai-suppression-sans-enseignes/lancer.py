#!/usr/bin/env python3
"""
==============================================================================
Étude ponctuelle — au bout de combien de jours un avis récent disparaît-il,
une fois les six enseignes signalées écartées

Question : parmi les avis publiés du 11 au 17 août 2026 sur une fiche qui
n'appartient à aucune des six enseignes, combien disparaissent, et au bout de
combien de jours.

Ce que ça vérifie. `docs/03-resultats.md` § 4 annonce que sept suppressions sur
dix tombent au sixième ou septième jour, sur 17 659 avis publiés et 695
supprimés. Ce chiffre vient d'un export, et les six enseignes y sont dedans.
Si le pic tient sans elles, le délai régulier décrit la modération de Google
et non la correction d'attaques ciblées.

------------------------------------------------------------------------------
LE REPÉRAGE DES SIX ENSEIGNES
------------------------------------------------------------------------------
  quatre chaînes antiparasitaires   par le nom, dans `businesses`, soit 93
                                    fiches. Le panel n'en retient que 88 :
                                    26, 19, 19 et 24 (`docs/02-donnees.md`
                                    § 4). Les 5 autres n'ont pas le volume
                                    d'avis exigé à la sélection du panel, et
                                    cette étude les écarte aussi.
  deux salles de sport espagnoles   par le `cid`, écrit en dur ci-dessous.
                                    Décision de Romain du 2026-09-14.

Aucune modification de `sql/02_adding_features.sql`, aucune table créée.
==============================================================================
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd

PROJET = "client-divers"

DOSSIER_CLES = Path("/home/romain/.gcp")

ICI = Path(__file__).resolve().parent
SORTIES = ICI / "sorties"

# Fiches de salle de sport réellement attaquées, par `cid`.
# Validées par Romain le 2026-09-15 (`docs/02-donnees.md` § 4).
CID_GYM_ATTAQUEE: list[str] = [
    "3163466139043001754",
    "10346942689164695031",
]

# Comptes de fiches attendus pour les quatre chaînes, `docs/02-donnees.md` § 4.
#
# Ces comptes sont ceux du PANEL. `businesses` porte 5 fiches de plus, sorties
# à la sélection parce qu'elles n'ont pas entre 100 et 10 000 avis. L'étude lit
# `reviews`, donc elle écarte toutes les fiches de `businesses` ; le contrôle
# ci-dessous porte sur la colonne du panel, la seule que la documentation
# chiffre.
FICHES_ATTENDUES = sorted([26, 19, 19, 24])


def trouver_cle() -> str | None:
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


def cid_des_enseignes(client) -> list[str]:
    """Les `cid` à écarter : les succursales des quatre chaînes, plus les deux
    fiches de salle de sport attaquées."""
    from google.cloud import bigquery

    tab = interroger(client, "controle_cid_enseignes.sql")
    SORTIES.mkdir(parents=True, exist_ok=True)
    tab.to_csv(SORTIES / "2026-09-15-controle-cid-enseignes.csv", index=False)

    print("\n--- fiches des quatre chaînes antiparasitaires ---")
    print(tab.to_string(index=False))

    trouves = sorted(tab["fiches_dans_le_panel"].tolist())
    if trouves != FICHES_ATTENDUES:
        raise SystemExit(
            f"ARRÊT : comptes de fiches {trouves}, attendus "
            f"{FICHES_ATTENDUES} (`docs/02-donnees.md` § 4). Le repérage par "
            f"nom a bougé, la suite est fausse.")
    print(f"  comptes du panel conformes à docs/02-donnees.md § 4 ; "
          f"{int(tab['fiches_businesses'].sum())} fiches écartées au total")

    sql_cid = """
        SELECT DISTINCT cid
        FROM `client-divers`.reviewflowz.businesses
        WHERE name IN ("EcoShield Pest Solutions", "Insight Pest Solutions",
                       "Pointe Pest Control", "Bulwark Exterminating")
    """
    cid_chaines = [str(c) for c in
                   client.query(sql_cid).to_dataframe()["cid"].tolist()]
    cid = sorted(set(cid_chaines) | set(CID_GYM_ATTAQUEE))
    print(f"  {len(cid_chaines)} fiches de chaîne + {len(CID_GYM_ATTAQUEE)} "
          f"salles de sport = {len(cid)} cid écartés")
    return cid


def croiser(tab: pd.DataFrame, perimetre: str) -> pd.DataFrame:
    """Le tableau croisé : une ligne par jour de publication, une colonne par
    délai de suppression."""
    bloc = tab[tab["perimetre"] == perimetre]
    supprimes = bloc[bloc["delai_j"].notna()]
    croise = supprimes.pivot_table(index="jour_creation", columns="delai_j",
                                   values="avis", aggfunc="sum", fill_value=0)
    croise.columns = [f"J+{int(c)}" for c in croise.columns]
    croise.insert(0, "avis_publies",
                  bloc.groupby("jour_creation")["avis"].sum())
    croise["supprimes"] = supprimes.groupby("jour_creation")["avis"].sum()
    croise["part_supprimee_pct"] = (
        croise["supprimes"] / croise["avis_publies"] * 100).round(2)
    return croise


def lire(croise: pd.DataFrame, perimetre: str) -> None:
    total_publies = int(croise["avis_publies"].sum())
    total_supprimes = int(croise["supprimes"].sum())
    colonnes_j = [c for c in croise.columns if c.startswith("J+")]
    par_delai = croise[colonnes_j].sum()
    pic = par_delai.get("J+6", 0) + par_delai.get("J+7", 0)

    print(f"\n--- périmètre {perimetre} ---")
    print(f"  {total_publies:,} avis publiés, {total_supprimes:,} supprimés, "
          f"{total_supprimes / total_publies * 100:.2f} %".replace(",", " "))
    print(f"  J+6 et J+7 : {int(pic):,} suppressions sur {total_supprimes:,}, "
          f"{pic / total_supprimes * 100:.1f} %".replace(",", " "))
    print()
    print(croise.to_string())


def main() -> int:
    from google.cloud import bigquery

    client = client_bigquery()
    cid = cid_des_enseignes(client)

    tab = interroger(
        client, "01_delai.sql",
        [bigquery.ArrayQueryParameter("cid_exclus", "STRING", cid)])
    tab.to_csv(SORTIES / "2026-09-15-delai-brut.csv", index=False)

    for perimetre in ["complet", "sans_enseignes"]:
        croise = croiser(tab, perimetre)
        croise.to_csv(SORTIES / f"2026-09-15-delai-{perimetre}.csv")
        lire(croise, perimetre)

    print("\n" + "=" * 78)
    print("  À SAVOIR EN LISANT CES CHIFFRES")
    print("=" * 78)
    print("  - Une ligne compte des avis publiés ce jour-là, une colonne compte")
    print("    ceux qui ont disparu ce nombre de jours après leur publication.")
    print("  - Le dernier passage du robot est le 24 août : un avis du 11 août")
    print("    a été observé 13 jours, un avis du 17 août seulement 7. Les")
    print("    colonnes J+8 et au-delà sont incomplètes en bas du tableau.")
    print("  - Un avis publié et supprimé dans la même journée n'est pas vu.")
    print("  - La modération avant publication reste invisible.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as erreur:
        print(f"\nARRÊT : {erreur}", file=sys.stderr)
        sys.exit(1)
