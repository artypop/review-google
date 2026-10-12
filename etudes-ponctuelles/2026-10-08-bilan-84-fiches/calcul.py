#!/usr/bin/env python3
"""Les 84 fiches les plus touchées ont-elles perdu plus d'avis qu'elles n'en ont gagné du
11 au 24 août 2026 ?

    PYTHONPATH=".venv/Lib/site-packages;outils" <python uv> etudes-ponctuelles/2026-10-08-bilan-84-fiches/calcul.py

Demande de Matthieu du 2026-10-08.

  les 84 fiches  celles de `2026-10-06-velocite-prenom` (1 % des fiches, 1 043
                 suppressions d'avis 4-5 étoiles avec texte), retrouvées par le même tri.
  perdus         avis dont la disparition est notée du 11 au 24 août
                 (`deleted_detected_at`), quelle que soit leur date de publication.
  gagnés         avis publiés du 11 au 24 août (`created_at`).
  en ligne       avis publiés avant le 11 août et pas encore disparus au 11 août.
  Définitions du tableau `pertes_secteur_taille` (2026-10-02), en 4-5 étoiles et en
  toutes notes. Un avis publié puis disparu pendant les deux semaines compte des deux côtés.
  comparaison    toutes les autres fiches relevées jusqu'au 24 août, sans les six enseignes.

Sorties : etudes-ponctuelles/2026-10-08-bilan-84-fiches/sorties/
  bilan_84_fiches.csv (une ligne par fiche), bilan_groupes.csv
"""
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location(
    "v06", RACINE / "etudes-ponctuelles" / "2026-10-06-velocite-prenom" / "calcul.py")
v06 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(v06)
from local import connexion  # noqa: E402  (chemin posé par le script du 2026-10-06)

sys.stdout.reconfigure(encoding="utf-8")
pd.set_option("display.width", 200)
SORTIES = Path(__file__).resolve().parent / "sorties"
ATTENDU = (84, 1043)
DEBUT, FIN = "2026-08-11", "2026-08-24"
PERIODE = f"BETWEEN DATE '{DEBUT}' AND DATE '{FIN}'"

SQL = f"""
WITH fin_suivi AS (
  SELECT cid, max(CAST(last_seen_at AS DATE)) AS fin_suivi
  FROM reviews_doublons_cleaned_all GROUP BY cid
),
av AS (
  SELECT r.cid, r.star >= 4 AS quatre_cinq,
         CAST(r.created_at AS DATE)          AS publie,
         CAST(r.deleted_detected_at AS DATE) AS disparu
  FROM reviews_doublons_cleaned_all r JOIN fin_suivi f USING (cid)
  WHERE f.fin_suivi = DATE '{FIN}'
)
SELECT av.cid, b.industry, if(b.country = 'US', 'US', 'Europe') AS region,
       COALESCE({{chaines}}, FALSE) OR av.cid IN ({{salles}}) AS enseigne,
       count(*) FILTER (quatre_cinq AND disparu {PERIODE}) AS perdus_45,
       count(*) FILTER (quatre_cinq AND publie  {PERIODE}) AS gagnes_45,
       count(*) FILTER (quatre_cinq AND publie < DATE '{DEBUT}'
                        AND (disparu IS NULL OR disparu >= DATE '{DEBUT}')) AS en_ligne_45,
       count(*) FILTER (disparu {PERIODE}) AS perdus_tout,
       count(*) FILTER (publie  {PERIODE}) AS gagnes_tout,
       count(*) FILTER (publie < DATE '{DEBUT}'
                        AND (disparu IS NULL OR disparu >= DATE '{DEBUT}')) AS en_ligne_tout
FROM av JOIN businesses b ON b.cid = av.cid
GROUP BY ALL
"""


def top_84(con) -> pd.Index:
    fi = v06.fiches(con)
    a = v06.avis_tous_ages(con).merge(fi, on="cid", how="left")
    a = a[a["classe_prenom"].isin(v06.CLASSES_PRENOM)]
    par_fiche = a.groupby("cid")["supprime"].sum().sort_values(ascending=False)
    top = par_fiche.head(int(np.ceil(0.01 * len(par_fiche)))).index
    if (len(top), int(par_fiche.loc[top].sum())) != ATTENDU:
        raise SystemExit(f"fiches les plus touchées : {len(top)}, attendu {ATTENDU}")
    return top


def bilan(d: pd.DataFrame, s: str) -> dict:
    p, g, e = d[f"perdus_{s}"], d[f"gagnes_{s}"], d[f"en_ligne_{s}"]
    return {"fiches": len(d), "perdus": int(p.sum()), "gagnes": int(g.sum()),
            "solde": int(g.sum() - p.sum()),
            "perdus_pour_100_gagnes": round(100 * p.sum() / g.sum(), 1),
            "perdus_pour_100_en_ligne": round(100 * p.sum() / e.sum(), 2),
            "fiches_en_perte": int((p > g).sum()), "fiches_a_egalite": int((p == g).sum()),
            "fiches_en_gain": int((p < g).sum())}


def main():
    con = connexion("6GB")
    top = top_84(con)
    chaines = " OR ".join(f"lower(b.name) LIKE '{nom}%'"
                          for nom in v06.f07.CHAINES_ANTIPARASITAIRES)
    salles = ", ".join(f"'{c}'" for c in v06.f07.CID_SALLES_ESPAGNOLES)
    d = con.execute(SQL.format(chaines=chaines, salles=salles)).df()
    d["top_84"] = d["cid"].isin(top)
    if d["top_84"].sum() != len(top) or d.loc[d["top_84"], "enseigne"].any():
        raise SystemExit("les 84 fiches ne se retrouvent pas toutes, ou une enseigne s'y trouve")

    groupes = []
    for nom, g in [("84 fiches les plus touchées", d[d["top_84"]]),
                   ("autres fiches, sans les enseignes", d[~d["top_84"] & ~d["enseigne"]])]:
        for s, notes in [("45", "4-5 étoiles"), ("tout", "toutes notes")]:
            groupes.append({"groupe": nom, "notes": notes, **bilan(g, s)})
    groupes = pd.DataFrame(groupes)
    print(groupes.to_string(index=False))

    t = d[d["top_84"]].drop(columns=["top_84", "enseigne"]).copy()
    t["solde_45"] = t["gagnes_45"] - t["perdus_45"]
    t = t.sort_values("perdus_45", ascending=False)
    print("\n84 fiches, 4-5 étoiles, perdus pour 100 gagnés (quartiles) :\n"
          + (100 * t["perdus_45"] / t["gagnes_45"].replace(0, np.nan)).describe().round(0).to_string())
    print("\nfiches sans aucun avis 4-5 étoiles gagné :", int((t["gagnes_45"] == 0).sum()))
    print("\nselon la région, 4-5 étoiles :\n" + t.groupby("region")[["perdus_45", "gagnes_45"]]
          .agg(["sum", "count"]).to_string())
    print("\nselon le secteur, 4-5 étoiles :\n" + t.groupby("industry")[["perdus_45", "gagnes_45"]]
          .sum().assign(fiches=t.groupby("industry").size()).to_string())

    SORTIES.mkdir(parents=True, exist_ok=True)
    t.to_csv(SORTIES / "bilan_84_fiches.csv", index=False)
    groupes.to_csv(SORTIES / "bilan_groupes.csv", index=False)
    print("\nécrit :", SORTIES / "bilan_84_fiches.csv")
    print("écrit :", SORTIES / "bilan_groupes.csv")


if __name__ == "__main__":
    main()
