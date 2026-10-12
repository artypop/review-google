#!/usr/bin/env python3
"""Le tableau des avis 4 et 5 étoiles perdus du 2026-10-02, séparé entre États-Unis et
Europe : une matrice par région.

    PYTHONPATH=".venv/Lib/site-packages;outils" <python uv> etudes-ponctuelles/2026-10-08-pertes-secteur-taille-region/calcul.py

Demande de Matthieu du 2026-10-08. Définitions et matrice reprises telles quelles de
`2026-10-02-pertes-secteur-taille/calcul.py` :

  numérateur    avis 4 et 5 étoiles dont la disparition est notée du 11 au 24 août
                (`deleted_detected_at`), quelle que soit leur date de publication.
  dénominateur  avis 4 et 5 étoiles publiés du 11 au 24 août (`created_at`).
  fiches        les 3 fiches qui ne sont plus relevées avant le 24 août sont écartées.
  région        États-Unis si `businesses.country` vaut 'US', Europe sinon (07F).
  enseignes     deux versions : enseignes comprises, comme dans le tableau d'origine, et
                sans les six enseignes (repérées comme dans le 07F).

Les quatre matrices partagent la même échelle de couleur : une case de même teinte a le
même taux dans toutes. Le script vérifie qu'États-Unis + Europe, enseignes comprises,
redonne case par case le CSV du 2026-10-02.

Sorties :
  livrables/restitution_finale/graphiques/pertes_secteur_taille_us.png
  livrables/restitution_finale/graphiques/pertes_secteur_taille_europe.png
  livrables/restitution_finale/graphiques/pertes_secteur_taille_us_sans_enseignes.png
  livrables/restitution_finale/graphiques/pertes_secteur_taille_europe_sans_enseignes.png
  livrables/restitution_finale/donnees/pertes_secteur_taille_region.csv
"""
from __future__ import annotations

import csv
import importlib
import importlib.util
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location(
    "p02", RACINE / "etudes-ponctuelles" / "2026-10-02-pertes-secteur-taille" / "calcul.py")
p02 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(p02)
sys.path.insert(0, str(RACINE / "logistic-regression-study" / "python"))
f07 = importlib.import_module("07F_regression_03C_prenom")
from local import connexion  # noqa: E402  (chemin posé par le script du 2026-10-02)

FINALE = p02.FINALE
DONNEES = FINALE / "donnees" / "pertes_secteur_taille_region.csv"
REGIONS = {"US": ("États-Unis", "us"), "Europe": ("Europe", "europe")}
# (suffixe du fichier, mention du titre, phrase du sous-titre)
VERSIONS = {"avec": ("", "", "Six enseignes comprises."),
            "sans": ("_sans_enseignes", ", sans les six enseignes",
                     "Sans les six enseignes (4 chaînes antiparasitaires américaines, "
                     "2 salles de sport espagnoles).")}
DEBUT, FIN = p02.DEBUT, p02.FIN
SOUS_TITRE = ("Dans chaque case : avis perdus pour 100 avis publiés (avis perdus / avis "
              "publiés) ; un avis perdu peut avoir été publié avant la période.\n"
              "Plus la case est foncée, plus le taux est élevé, sur la même échelle pour "
              "les quatre tableaux.\n{}")

PERIODE = f"BETWEEN DATE '{DEBUT}' AND DATE '{FIN}'"
SQL = f"""
WITH fin_suivi AS (
  SELECT cid, max(CAST(last_seen_at AS DATE)) AS fin_suivi
  FROM reviews_doublons_cleaned_all GROUP BY cid
),
avis AS (
  SELECT if(b.country = 'US', 'US', 'Europe')          AS region,
         b.industry, b.bucket,
         COALESCE({{chaines}}, FALSE) OR r.cid IN ({{salles}}) AS enseigne,
         CAST(r.created_at AS DATE)          AS publie,
         CAST(r.deleted_detected_at AS DATE) AS disparu
  FROM reviews_doublons_cleaned_all r
  JOIN fin_suivi f USING (cid)
  JOIN businesses b ON b.cid = r.cid
  WHERE r.star >= 4 AND f.fin_suivi = DATE '{FIN}'
)
SELECT region, industry, bucket,
       COUNT(*) FILTER (disparu {PERIODE})                  AS perdus,
       COUNT(*) FILTER (publie  {PERIODE})                  AS nouveaux,
       COUNT(*) FILTER (NOT enseigne AND disparu {PERIODE}) AS perdus_sans,
       COUNT(*) FILTER (NOT enseigne AND publie  {PERIODE}) AS nouveaux_sans
FROM avis
GROUP BY GROUPING SETS ((region, industry, bucket), (region, industry),
                        (region, bucket), (region))
"""


def taux(p: int, n: int) -> str:
    return f"{100 * p / n:.1f}" if n else ""


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    con = connexion("4GB")
    con.execute("SET threads=4")
    sans_pays = con.execute("""
        SELECT count(*) FROM reviews_doublons_cleaned_all r
        JOIN businesses b ON b.cid = r.cid WHERE b.country IS NULL""").fetchone()[0]
    if sans_pays:
        raise SystemExit(f"{sans_pays} avis sur des fiches sans pays.")
    chaines = " OR ".join(f"lower(b.name) LIKE '{nom}%'" for nom in f07.CHAINES_ANTIPARASITAIRES)
    salles = ", ".join(f"'{c}'" for c in f07.CID_SALLES_ESPAGNOLES)
    lus = con.execute(SQL.format(chaines=chaines, salles=salles)).fetchall()
    cases = {(r, i, b): (p, n, ps, ns) for r, i, b, p, n, ps, ns in lus}
    inconnus = {k for k in cases if (k[1] is not None and k[1] not in p02.SECTEURS)
                or (k[2] is not None and k[2] not in p02.TAILLES)}
    if inconnus:
        raise SystemExit(f"secteur ou taille inattendus : {inconnus}")

    lignes = list(p02.SECTEURS) + [None]
    colonnes = list(p02.TAILLES) + [None]

    # États-Unis + Europe = le tableau du 2026-10-02, case par case.
    with p02.DONNEES.open(encoding="utf-8") as f:
        attendu = {(l["secteur"], l["taille"]): (int(l["avis_4_5_perdus"]),
                                                  int(l["avis_4_5_nouveaux"]))
                   for l in csv.DictReader(f)}
    ecarts = []
    for i in lignes:
        for b in colonnes:
            somme = tuple(sum(cases.get((r, i, b), (0, 0, 0, 0))[k] for r in REGIONS)
                          for k in (0, 1))
            cle = (p02.SECTEURS.get(i, "Total"), p02.TAILLES.get(b, "Total"))
            if somme != attendu[cle]:
                ecarts.append((cle, somme, attendu[cle]))
    if ecarts:
        raise SystemExit(f"États-Unis + Europe ne redonne pas le tableau du 2026-10-02 : {ecarts}")
    print("États-Unis + Europe redonne le tableau du 2026-10-02, case par case.")

    DONNEES.parent.mkdir(parents=True, exist_ok=True)
    with DONNEES.open("w", encoding="utf-8") as f:
        f.write("region,secteur,taille,avis_4_5_perdus,avis_4_5_nouveaux,"
                "perdus_pour_100_nouveaux,avis_4_5_perdus_sans_enseignes,"
                "avis_4_5_nouveaux_sans_enseignes,perdus_pour_100_nouveaux_sans_enseignes\n")
        for r, (nom, _) in REGIONS.items():
            for i in lignes:
                for b in colonnes:
                    p, n, ps, ns = cases.get((r, i, b), (0, 0, 0, 0))
                    f.write(f"{nom},{p02.SECTEURS.get(i, 'Total')},{p02.TAILLES.get(b, 'Total')},"
                            f"{p},{n},{taux(p, n)},{ps},{ns},{taux(ps, ns)}\n")

    t_max = max(100 * v[k] / v[k + 1] for (r, i, b), v in cases.items() for k in (0, 2)
                if v[k + 1] and i is not None and b is not None)
    for r, (nom, fichier) in REGIONS.items():
        print(f"\n{nom} (enseignes comprises | sans les six enseignes)")
        for i in lignes:
            cellules = []
            for b in colonnes:
                p, n, ps, ns = cases.get((r, i, b), (0, 0, 0, 0))
                if (p and not n) or (ps and not ns):
                    print(f"  attention : avis perdus sans avis publié, {i} × {b}")
                cellules.append(f"{p:>5} / {n:>5} = {taux(p, n):>5} % | {taux(ps, ns):>5} %"
                                if n else "—")
            print(f"{p02.SECTEURS.get(i, 'Total'):20s} | " + " | ".join(cellules))
        for k, (suffixe, mention, phrase) in enumerate(VERSIONS.values()):
            chemin = FINALE / "graphiques" / f"pertes_secteur_taille_{fichier}{suffixe}.png"
            p02.matrice({(i, b): v[2 * k:2 * k + 2] for (rr, i, b), v in cases.items() if rr == r},
                        lignes, colonnes, chemin=chemin, t_max=t_max,
                        titre=f"{nom}{mention} : avis 4 et 5 étoiles perdus pour 100 publiés, "
                              f"du 11 au 24 août 2026",
                        sous_titre=SOUS_TITRE.format(phrase))
            print(f"écrit : {chemin}")
    print(f"écrit : {DONNEES}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
