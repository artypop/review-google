#!/usr/bin/env python3
"""Le traitement antiparasitaire est-il sur-représenté dans les home services US ?

    python etudes-ponctuelles/2026-09-18-antiparasitaire-home-services/antiparasitaire.py

Produit les CSV de `sorties/`. La figure et le document sont assemblés ensuite
par `graphiques.py` et `note.py`.

------------------------------------------------------------------------------
COMMENT LE TRAITEMENT ANTIPARASITAIRE EST REPÉRÉ
------------------------------------------------------------------------------
`businesses` ne porte pas de sous-catégorie : `industry` s'arrête aux sept
secteurs du panel. Le repérage se fait donc sur `businesses.name`, avec le
motif ci-dessous.

Une enseigne est ajoutée à la main, décision de Matthieu du 2026-09-21 :
« ABC Home & Commercial Services », entreprise de traitement antiparasitaire
diversifiée, dont le nom ne porte aucun des mots du motif. Ses six variantes
d'écriture sont couvertes par `MOTIF_INCLUSION_MANUELLE`.

Le compte reste un plancher : « Alternative Earthcare » n'est attrapée que sur
celle de ses fiches qui porte le suffixe « Tick and Mosquito Spraying ». Et
aucune vérification enseigne par enseigne n'a été faite sur les 317 fiches
classées en « autres services à domicile ».

------------------------------------------------------------------------------
POURQUOI LE GROUPE « VARIANTE DE NOM » EXISTE
------------------------------------------------------------------------------
Le drapeau `chaine_antiparasitaire_us` de `sql/02_adding_features.sql` marque
sur une égalité exacte de nom, sur quatre valeurs. Les fiches nommées
« EcoShield Pest Solutions Seattle » ou « Bulwark Exterminating Corporate » ne
sont donc pas marquées, alors qu'elles appartiennent à ces mêmes chaînes. Elles
sont isolées ici pour que le compte des « autres » ne les contienne pas.

------------------------------------------------------------------------------
PÉRIMÈTRE
------------------------------------------------------------------------------
Corpus complet, 4,88 millions d'avis, sans filtre de date. Ce n'est pas le
panel de la régression, qui retient 225 757 avis publiés du 13 mai au 16 août.

Définition d'une suppression : `etude-exploratoire/scripts/
suppressions_corrigees.py`, importée telle quelle. Le dossier est gelé ; le
module est lu, rien n'y est écrit ni relancé.
"""
from __future__ import annotations

import sys
from pathlib import Path

DOSSIER = Path(__file__).resolve().parent
RACINE = DOSSIER.parent.parent
SORTIES = DOSSIER / "sorties"
sys.path.insert(0, str(RACINE / "outils"))
sys.path.insert(0, str(RACINE / "etude-exploratoire" / "scripts"))

from local import connexion  # noqa: E402
from suppressions_corrigees import creer_vue_avis  # noqa: E402

# Le motif qui désigne une activité de traitement antiparasitaire.
MOTIF_ACTIVITE = r"(?i)(pest|exterminat|termite|spidexx|mosquito|rodent|wildlife)"

# Ajout manuel du 2026-09-21. Les six écritures du nom présentes dans le panel :
# « ABC Home & Commercial Services », « ABC Home and Commercial Services »,
# « ABC Home&Commercial Services », et trois suffixes — Orlando, Landscaping
# Department, Plumbing Services Department.
MOTIF_INCLUSION_MANUELLE = r"(?i)abc home ?(&|and) ?commercial"

# Les marques des quatre chaînes signalées, pour rattraper leurs fiches dont le
# nom porte un suffixe de ville ou de statut.
MOTIF_MARQUES = r"(?i)(ecoshield|bulwark|pointe pest|insight pest)"

# Les quatre valeurs exactes que marque `sql/02_adding_features.sql`.
NOMS_SIGNALES = (
    "'EcoShield Pest Solutions'", "'Insight Pest Solutions'",
    "'Pointe Pest Control'", "'Bulwark Exterminating'",
)
LISTE_SIGNALES = "(" + ", ".join(NOMS_SIGNALES) + ")"

# Le test unique d'appartenance au métier : le motif d'activité, ou l'ajout
# manuel. Écrit une seule fois, utilisé par `ACTIVITE` et par `GROUPE`.
EST_ANTIPARASITAIRE = (f"(regexp_matches(b.name, '{MOTIF_ACTIVITE}')"
                       f" OR regexp_matches(b.name, '{MOTIF_INCLUSION_MANUELLE}'))")

GROUPE = f"""
  CASE
    WHEN b.name IN {LISTE_SIGNALES}                  THEN 'a. les 4 chaines signalees'
    WHEN regexp_matches(b.name, '{MOTIF_MARQUES}')   THEN 'b. variante de nom de ces 4 chaines'
    WHEN {EST_ANTIPARASITAIRE}                       THEN 'c. autre enseigne antiparasitaire'
    ELSE                                                  'd. autres services a domicile'
  END
"""

ACTIVITE = f"""
  IF({EST_ANTIPARASITAIRE}, 'antiparasitaire', 'autres services')
"""


def ecrire(df, nom):
    SORTIES.mkdir(parents=True, exist_ok=True)
    df.to_csv(SORTIES / nom, index=False)
    print(f"  {nom:46s} {len(df):>5} lignes")
    return df


def main() -> int:
    con = connexion("4GB")
    con.execute("SET enable_progress_bar=false")
    creer_vue_avis(con, source="reviews")

    con.execute(f"""
        CREATE TEMP TABLE hs AS
        SELECT b.cid,
               b.name      AS enseigne,
               b.bucket,
               {ACTIVITE}  AS activite,
               {GROUPE}    AS groupe,
               COUNT(a.review_id)                                      AS avis,
               SUM(CASE WHEN a.death_at IS NOT NULL THEN 1 ELSE 0 END) AS suppressions
        FROM businesses b
        LEFT JOIN avis a USING (cid)
        WHERE b.industry = 'home_services' AND b.country = 'US'
        GROUP BY 1, 2, 3, 4, 5
    """)

    print("\nA. Le cadre : les trois tailles")
    ecrire(con.execute("""
        SELECT bucket, COUNT(*) AS fiches, SUM(avis) AS avis,
               SUM(suppressions) AS suppressions,
               ROUND(100.0 * SUM(suppressions) / NULLIF(SUM(avis), 0), 2) AS taux_pct
        FROM hs GROUP BY 1 ORDER BY SUM(avis) DESC
    """).df(), "A1-cadre-par-taille.csv")

    print("\nB. L'antiparasitaire dans chaque taille")
    ecrire(con.execute("""
        SELECT bucket, activite, COUNT(*) AS fiches, SUM(avis) AS avis,
               SUM(suppressions) AS suppressions,
               ROUND(100.0 * COUNT(*)
                     / SUM(COUNT(*)) OVER (PARTITION BY bucket), 1) AS part_fiches_pct,
               ROUND(100.0 * SUM(avis)
                     / SUM(SUM(avis)) OVER (PARTITION BY bucket), 1) AS part_avis_pct,
               ROUND(100.0 * SUM(suppressions)
                     / SUM(SUM(suppressions)) OVER (PARTITION BY bucket), 1) AS part_suppr_pct,
               ROUND(100.0 * SUM(suppressions) / NULLIF(SUM(avis), 0), 2) AS taux_pct
        FROM hs GROUP BY 1, 2 ORDER BY 1, 2
    """).df(), "B1-par-taille.csv")

    print("\nC. Small et large réunis — le tableau du document")
    ecrire(con.execute("""
        SELECT activite, COUNT(*) AS fiches, SUM(avis) AS avis,
               SUM(suppressions) AS suppressions,
               ROUND(100.0 * COUNT(*)   / SUM(COUNT(*))   OVER (), 1) AS part_fiches_pct,
               ROUND(100.0 * SUM(avis)  / SUM(SUM(avis))  OVER (), 1) AS part_avis_pct,
               ROUND(100.0 * SUM(suppressions)
                     / SUM(SUM(suppressions)) OVER (), 1) AS part_suppr_pct,
               ROUND(100.0 * SUM(suppressions) / NULLIF(SUM(avis), 0), 2) AS taux_pct
        FROM hs WHERE bucket IN ('small', 'large') GROUP BY 1 ORDER BY 1
    """).df(), "C1-small-large.csv")

    print("\nD. Ce que le drapeau actuel laisse passer")
    ecrire(con.execute("""
        SELECT groupe, COUNT(*) AS fiches, SUM(avis) AS avis,
               SUM(suppressions) AS suppressions,
               ROUND(100.0 * SUM(suppressions) / NULLIF(SUM(avis), 0), 2) AS taux_pct,
               ROUND(100.0 * SUM(avis)  / SUM(SUM(avis))  OVER (), 1) AS part_avis_pct,
               ROUND(100.0 * SUM(suppressions)
                     / SUM(SUM(suppressions)) OVER (), 1) AS part_suppr_pct
        FROM hs WHERE bucket IN ('small', 'large') GROUP BY 1 ORDER BY 1
    """).df(), "D1-quatre-groupes.csv")

    print("\nE. Les enseignes antiparasitaires que le drapeau ne marque pas")
    ecrire(con.execute("""
        SELECT enseigne, bucket, groupe, COUNT(*) AS fiches, SUM(avis) AS avis,
               SUM(suppressions) AS suppressions
        FROM hs
        WHERE bucket IN ('small', 'large')
          AND groupe IN ('b. variante de nom de ces 4 chaines',
                         'c. autre enseigne antiparasitaire')
        GROUP BY 1, 2, 3
        ORDER BY groupe, avis DESC, enseigne
    """).df(), "E1-enseignes-non-marquees.csv")

    print("\nE bis. Ce que pèse l'ajout manuel d'ABC")
    ecrire(con.execute(f"""
        SELECT enseigne, bucket, COUNT(*) AS fiches, SUM(avis) AS avis,
               SUM(suppressions) AS suppressions
        FROM hs
        WHERE bucket IN ('small', 'large')
          AND regexp_matches(enseigne, '{MOTIF_INCLUSION_MANUELLE}')
        GROUP BY 1, 2 ORDER BY avis DESC
    """).df(), "E2-ajout-manuel-abc.csv")

    print("\nF. Ce qui resterait après le retrait des six enseignes signalées")
    ecrire(con.execute("""
        SELECT activite, COUNT(*) AS fiches, SUM(avis) AS avis,
               SUM(suppressions) AS suppressions,
               ROUND(100.0 * SUM(avis)  / SUM(SUM(avis))  OVER (), 1) AS part_avis_pct,
               ROUND(100.0 * SUM(suppressions)
                     / SUM(SUM(suppressions)) OVER (), 1) AS part_suppr_pct
        FROM hs
        WHERE bucket IN ('small', 'large')
          AND groupe <> 'a. les 4 chaines signalees'
        GROUP BY 1 ORDER BY 1
    """).df(), "F1-apres-retrait-des-quatre.csv")

    con.close()
    print(f"\nCSV dans {SORTIES}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
