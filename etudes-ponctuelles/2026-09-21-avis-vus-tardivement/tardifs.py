#!/usr/bin/env python3
"""Les avis du panel 03B vus pour la première fois bien après leur publication.

    python etudes-ponctuelles/2026-09-21-avis-vus-tardivement/tardifs.py

Produit les CSV de `sorties/`. Le document Word est assemblé ensuite par
`note.py`, qui ne calcule rien.

------------------------------------------------------------------------------
LA POPULATION
------------------------------------------------------------------------------
Sur les 35 751 avis de `03B_reviews_panel_filtered_08_04_to_08_26`, 412 ont été
vus par le robot huit jours ou plus après leur publication. Ces 412 se
décomposent en trois groupes, et un seul est examiné ici.

  80   avis modifiés. Leur `first_seen_at` est la date de détection de la
       modification, non celle de la première apparition. Écartés.
  49   avis sur deux fiches, The Boxer Club en Espagne et Lake Travis Zipline
       Adventures aux États-Unis. Écartés : ce sont deux afflux groupés, et
       la première est l'attaque déjà documentée.
  283  avis isolés, sur 230 fiches qui n'en portent qu'un seul. C'est cette
       population-ci.

Le seuil de concentration retenu pour écarter une fiche est de 5 avis tardifs
ou plus. Les deux fiches écartées en portent 21 et 28 ; la suivante en porte 4.

------------------------------------------------------------------------------
PÉRIMÈTRE
------------------------------------------------------------------------------
Copie locale de `03B_reviews_panel_filtered_08_04_to_08_26`, 35 751 avis
publiés du 4 au 17 août 2026, observés du 11 au 24 août.
"""
from __future__ import annotations

import sys
from pathlib import Path

DOSSIER = Path(__file__).resolve().parent
RACINE = DOSSIER.parent.parent
SORTIES = DOSSIER / "sorties"
sys.path.insert(0, str(RACINE / "outils"))

from local import connexion  # noqa: E402

PANEL = '"03B_reviews_panel_filtered_08_04_to_08_26"'
SEUIL_CONCENTRATION = 5
SEUIL_TARDIF = 8


def ecrire(df, nom):
    SORTIES.mkdir(parents=True, exist_ok=True)
    df.to_csv(SORTIES / nom, index=False)
    print(f"  {nom:40s} {len(df):>5} lignes")
    return df


def main() -> int:
    con = connexion("4GB")
    con.execute("SET enable_progress_bar=false")

    con.execute(f"""
        CREATE TEMP TABLE base AS
        SELECT p.review_id, p.cid, b.name AS enseigne, b.country AS pays,
               p.star, p.text, p.is_update,
               p.created_at, p.first_seen_at,
               (p.deleted_detected_at IS NOT NULL) AS supprime,
               DATE_DIFF('day', CAST(p.created_at AS DATE),
                                CAST(p.first_seen_at AS DATE)) AS ecart_j
        FROM {PANEL} p LEFT JOIN businesses b USING (cid)
    """)

    con.execute(f"""
        CREATE TEMP TABLE fiches_concentrees AS
        SELECT cid FROM base
        WHERE ecart_j >= {SEUIL_TARDIF} AND NOT is_update
        GROUP BY cid HAVING COUNT(*) >= {SEUIL_CONCENTRATION}
    """)

    con.execute(f"""
        CREATE TEMP TABLE filet AS
        SELECT * FROM base
        WHERE ecart_j >= {SEUIL_TARDIF} AND NOT is_update
          AND cid NOT IN (SELECT cid FROM fiches_concentrees)
    """)

    print("\nA. Deux exemples")
    ecrire(con.execute("""
        SELECT review_id, CAST(cid AS VARCHAR) AS cid, enseigne, pays, star,
               COALESCE(LENGTH(text), 0) AS caracteres,
               strftime(created_at,   '%d/%m %H:%M') AS publie,
               strftime(first_seen_at,'%d/%m %H:%M') AS vu_le,
               ecart_j
        FROM filet
        WHERE enseigne IN ('Empire Today', 'Insight Pest Solutions')
        ORDER BY ecart_j DESC
    """).df(), "A1-exemples.csv")

    print("\nB. Longueur du texte")
    ecrire(con.execute(f"""
        SELECT CASE WHEN ecart_j >= {SEUIL_TARDIF}
                     AND cid NOT IN (SELECT cid FROM fiches_concentrees)
                    THEN 'filet tardif' ELSE 'vus dans les 7 jours' END AS groupe,
               COUNT(*) AS avis,
               ROUND(AVG(COALESCE(LENGTH(text), 0)), 0)    AS caracteres_moyen,
               ROUND(MEDIAN(COALESCE(LENGTH(text), 0)), 0) AS caracteres_median,
               ROUND(100.0 * COUNT(*) FILTER (WHERE COALESCE(LENGTH(text), 0) = 0)
                     / COUNT(*), 1) AS sans_texte_pct,
               ROUND(100.0 * COUNT(*) FILTER (WHERE COALESCE(LENGTH(text), 0) > 200)
                     / COUNT(*), 1) AS plus_200_car_pct
        FROM base WHERE NOT is_update GROUP BY 1 ORDER BY 1
    """).df(), "B1-longueur-texte.csv")

    print("\nC. Les pays")
    ecrire(con.execute("""
        SELECT pays, COUNT(*) AS avis FROM filet
        GROUP BY 1 ORDER BY avis DESC, pays
    """).df(), "C1-pays.csv")

    print("\nD. Les bornes de publication du filet")
    ecrire(con.execute("""
        SELECT MIN(CAST(created_at AS DATE))    AS publie_min,
               MAX(CAST(created_at AS DATE))    AS publie_max,
               MIN(ecart_j)                     AS ecart_min,
               MAX(ecart_j)                     AS ecart_max,
               COUNT(*)                         AS avis,
               COUNT(DISTINCT cid)              AS fiches,
               COUNT(DISTINCT pays)             AS pays,
               COUNT(*) FILTER (WHERE star = 4) AS avis_4_etoiles
        FROM filet
    """).df(), "D1-bornes.csv")

    con.close()
    print(f"\nCSV dans {SORTIES}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
