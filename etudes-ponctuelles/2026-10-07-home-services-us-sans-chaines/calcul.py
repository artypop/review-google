#!/usr/bin/env python3
"""Les services à domicile américains restent-ils le secteur le plus touché sans
les chaînes antiparasitaires ?

    PYTHONPATH=".venv/Lib/site-packages;outils" <python uv> etudes-ponctuelles/2026-10-07-home-services-us-sans-chaines/calcul.py

Demande de Matthieu du 2026-10-07, d'après la note de `livrables/restitution/A
faire.txt` : vérifier « les services à domicile aux États-Unis sont le secteur
le plus touché du corpus » une fois retirées les chaînes antiparasitaires.

  corpus       data/bigquery/reviews_doublons_cleaned_all.parquet, comme la
               piste 4 (`2026-10-02-flux-4-5-etoiles`). Les 3 fiches qui ne sont
               plus relevées avant le 24 août sont écartées.
  suppression  `deleted_detected_at` renseigné.
  cases        secteur × région : États-Unis, ou Europe pour tout autre pays.
  chaînes      les quatre chaînes du projet, repérées sur le début du nom.
               La note parle de trois : la quatrième (Bulwark) porte 156 des
               1 199 suppressions 4-5 étoiles des chaînes, elle est retirée aussi.

Trois mesures par case :
  flux_45      avis 4-5 étoiles publiés du 11 au 17 août, part disparue au plus
               tard 7 jours après la publication (la mesure de la piste 4).
  pertes_45    avis 4-5 étoiles disparus du 11 au 24 août, quel que soit leur
               âge, rapportés aux avis 4-5 étoiles publiés du 11 au 24 août.
  flux_toutes  comme flux_45, toutes notes.

Trois jeux : toutes les fiches ; sans les 4 chaînes ; sans les 6 enseignes (les
4 chaînes et les 2 salles espagnoles, qui sont en sport, Europe).

En plus, les services à domicile américains sans les chaînes sont coupés en
deux : les autres entreprises antiparasitaires, repérées sur le nom avec le
motif de `2026-09-18-antiparasitaire-home-services`, et le reste du secteur.

Sortie : `sorties/secteur_region_sans_chaines.csv`. Aucun texte, nom d'auteur
ni lien.
"""
from __future__ import annotations

import sys
from pathlib import Path

DOSSIER = Path(__file__).resolve().parent
RACINE = DOSSIER.parents[1]
sys.path.insert(0, str(RACINE / "outils"))
from local import connexion  # noqa: E402

SORTIES = DOSSIER / "sorties"
FLUX_DEBUT, FLUX_FIN, JOURS = "2026-08-11", "2026-08-17", 7
RELEVE_DEBUT, RELEVE_FIN = "2026-08-11", "2026-08-24"

CHAINES_ANTIPARASITAIRES = ("ecoshield pest solutions", "insight pest solutions",
                            "pointe pest control", "bulwark exterminating")
CID_SALLES_ESPAGNOLES = ("3163466139043001754", "10346942689164695031")
# Motif et ajout manuel de `2026-09-18-antiparasitaire-home-services/antiparasitaire.py`.
MOTIF_ACTIVITE = r"(?i)(pest|exterminat|termite|spidexx|mosquito|rodent|wildlife)"
MOTIF_INCLUSION_MANUELLE = r"(?i)abc home ?(&|and) ?commercial"

SECTEURS = {"automotive": "Automobile", "food_beverage": "Restauration",
            "healthcare": "Santé", "home_services": "Services à domicile",
            "hospitality": "Hôtellerie", "travel": "Voyage",
            "wellness_fitness": "Sport et bien-être"}
REGIONS = {"US": "États-Unis", "Europe": "Europe"}

SQL_AVIS = """
CREATE TEMP TABLE avis AS
WITH fin_suivi AS (
  SELECT cid, max(CAST(last_seen_at AS DATE)) AS fin_suivi
  FROM reviews_doublons_cleaned_all GROUP BY cid
)
SELECT r.review_id, r.cid, r.star, b.industry,
       IF(b.country = 'US', 'US', 'Europe')  AS region,
       CAST(r.created_at AS DATE)            AS publie,
       CAST(r.deleted_detected_at AS DATE)   AS disparu,
       COALESCE({chaines}, FALSE)            AS chaine,
       r.cid IN ({salles})                   AS salle,
       regexp_matches(b.name, '{motif}')
         OR regexp_matches(b.name, '{manuel}') AS antiparasitaire
FROM reviews_doublons_cleaned_all r
JOIN fin_suivi f USING (cid)
LEFT JOIN businesses b ON b.cid = r.cid
WHERE f.fin_suivi = DATE '{fin}'
"""

MESURES = f"""
  COUNT(*) FILTER (star >= 4 AND publie BETWEEN DATE '{FLUX_DEBUT}' AND DATE '{FLUX_FIN}') AS flux45_avis,
  COUNT(*) FILTER (star >= 4 AND publie BETWEEN DATE '{FLUX_DEBUT}' AND DATE '{FLUX_FIN}'
                   AND date_diff('day', publie, disparu) <= {JOURS})                    AS flux45_supp,
  COUNT(*) FILTER (star >= 4 AND publie BETWEEN DATE '{RELEVE_DEBUT}' AND DATE '{RELEVE_FIN}') AS periode45_avis,
  COUNT(*) FILTER (star >= 4 AND disparu BETWEEN DATE '{RELEVE_DEBUT}' AND DATE '{RELEVE_FIN}') AS periode45_pertes,
  COUNT(*) FILTER (publie BETWEEN DATE '{FLUX_DEBUT}' AND DATE '{FLUX_FIN}')               AS flux_avis,
  COUNT(*) FILTER (publie BETWEEN DATE '{FLUX_DEBUT}' AND DATE '{FLUX_FIN}'
                   AND date_diff('day', publie, disparu) <= {JOURS})                    AS flux_supp
"""

SQL_CASES = f"""
WITH jeux AS (
  SELECT 'toutes les fiches' AS jeu, * FROM avis
  UNION ALL
  SELECT 'sans les 4 chaînes', * FROM avis WHERE NOT chaine
  UNION ALL
  SELECT 'sans les 6 enseignes', * FROM avis WHERE NOT (chaine OR salle)
)
SELECT jeu, industry, region, {MESURES}
FROM jeux GROUP BY jeu, industry, region
"""

SQL_DETAIL_HS_US = f"""
SELECT IF(antiparasitaire, 'antiparasitaire hors chaînes', 'autres services à domicile') AS groupe,
       COUNT(DISTINCT cid) AS fiches, {MESURES}
FROM avis WHERE industry = 'home_services' AND region = 'US' AND NOT chaine
GROUP BY 1 ORDER BY 1
"""


def pct(s: int, d: int) -> str:
    return f"{100 * s / d:.2f}" if d else ""


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    SORTIES.mkdir(exist_ok=True)
    con = connexion("4GB")
    con.execute("SET threads=4")
    chaines = " OR ".join(f"lower(b.name) LIKE '{n}%'" for n in CHAINES_ANTIPARASITAIRES)
    con.execute(SQL_AVIS.format(chaines=chaines, fin=RELEVE_FIN, motif=MOTIF_ACTIVITE,
                                manuel=MOTIF_INCLUSION_MANUELLE,
                                salles=", ".join(f"'{c}'" for c in CID_SALLES_ESPAGNOLES)))

    n, distincts, sans_secteur, hors_hs_us = con.execute(
        "SELECT COUNT(*), COUNT(DISTINCT review_id), COUNT(*) FILTER (industry IS NULL), "
        "COUNT(*) FILTER (chaine AND NOT (industry = 'home_services' AND region = 'US')) "
        "FROM avis").fetchone()
    if n != distincts:
        raise SystemExit("La jointure a dupliqué des avis.")
    if sans_secteur:
        raise SystemExit(f"{sans_secteur} avis sans fiche dans businesses.")
    if hors_hs_us:
        raise SystemExit(f"{hors_hs_us} avis des chaînes hors services à domicile US.")

    # Contrôle : sans découpage par région, on doit retomber sur la piste 4.
    attendu = {"toutes les fiches": (292, 2967), "sans les 6 enseignes": (86, 1736)}
    for jeu, (s_att, a_att) in attendu.items():
        s, a = con.execute(
            f"SELECT SUM(flux45_supp), SUM(flux45_avis) FROM ({SQL_CASES}) "
            f"WHERE jeu = '{jeu}' AND industry = 'home_services'").fetchone()
        if (s, a) != (s_att, a_att):
            raise SystemExit(f"{jeu} : {s}/{a}, la piste 4 donne {s_att}/{a_att}.")

    lignes = con.execute(SQL_CASES).fetchall()
    with (SORTIES / "secteur_region_sans_chaines.csv").open("w", encoding="utf-8") as sortie:
        sortie.write("jeu,secteur,region,flux45_avis,flux45_supprimes_7j,flux45_pour_100,"
                     "periode45_avis,periode45_pertes,pertes45_pour_100,"
                     "flux_toutes_avis,flux_toutes_supprimes_7j,flux_toutes_pour_100\n")
        for jeu in ("toutes les fiches", "sans les 4 chaînes", "sans les 6 enseignes"):
            print(f"\n--- {jeu} (trié sur flux 4-5 étoiles) ---")
            cases = sorted((l for l in lignes if l[0] == jeu),
                           key=lambda l: -(l[4] / l[3] if l[3] else 0))
            for _, ind, reg, fa, fs, pa, pp, ta, ts in cases:
                nom = f"{SECTEURS[ind]},{REGIONS[reg]}"
                sortie.write(f"{jeu},{nom},{fa},{fs},{pct(fs, fa)},{pa},{pp},{pct(pp, pa)},"
                             f"{ta},{ts},{pct(ts, ta)}\n")
                print(f"{SECTEURS[ind]:20s} {REGIONS[reg]:11s} flux45 {fs:4d}/{fa:5d} = "
                      f"{pct(fs, fa):>5s} % | pertes45 {pp:4d}/{pa:5d} = {pct(pp, pa):>6s} % | "
                      f"flux toutes {ts:4d}/{ta:5d} = {pct(ts, ta):>5s} %")

        print("\n--- services à domicile US sans les 4 chaînes, coupés en deux ---")
        for groupe, fiches, fa, fs, pa, pp, ta, ts in con.execute(SQL_DETAIL_HS_US).fetchall():
            sortie.write(f"sans les 4 chaînes,Services à domicile : {groupe},États-Unis,"
                         f"{fa},{fs},{pct(fs, fa)},{pa},{pp},{pct(pp, pa)},"
                         f"{ta},{ts},{pct(ts, ta)}\n")
            print(f"{groupe:30s} {fiches:4d} fiches | flux45 {fs:4d}/{fa:5d} = "
                  f"{pct(fs, fa):>5s} % | pertes45 {pp:4d}/{pa:5d} = {pct(pp, pa):>6s} % | "
                  f"flux toutes {ts:4d}/{ta:5d} = {pct(ts, ta):>5s} %")
    print(f"\nécrit : {SORTIES / 'secteur_region_sans_chaines.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
