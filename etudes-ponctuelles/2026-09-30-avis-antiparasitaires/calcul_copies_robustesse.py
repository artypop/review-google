#!/usr/bin/env python3
"""L'excès de suppressions des copies tient-il sans la fiche la plus touchée ?

    PYTHONPATH=.venv/Lib/site-packages <python uv> etudes-ponctuelles/2026-09-30-avis-antiparasitaires/calcul_copies_robustesse.py

À lancer après `calcul_copies.py`, dont il relit `sorties/copies/C6-avis-copies.csv`
(les avis d'au moins 80 caractères qui ont un jumeau). Le 2026-09-30, 13 des 32
copies supprimées viennent d'une seule fiche, toutes publiées en août 2026.
Mêmes attendus et mêmes tirages que `calcul_copies.py`, sur quatre populations :
  toutes les fiches
  sans la fiche la plus touchée   celle qui a le plus de copies supprimées,
                                  retirée entièrement (avis et suppressions)
  avis publiés avant août 2026
  avis publiés en août 2026

Sortie : `sorties/copies/C7-robustesse.csv`.
"""
from __future__ import annotations

import csv
import sys

import numpy as np

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
import calcul_copies as cc  # noqa: E402


def main() -> int:
    rng = np.random.default_rng(cc.GRAINE + 1)
    cc.journal("lecture")
    d, _, _ = cc.charger()
    with (cc.SORTIES / "C6-avis-copies.csv").open(encoding="utf-8") as f:
        copies = {r["review_id"]: r for r in csv.DictReader(f)}
    copie = np.array([r in copies for r in d["review_id"]])
    supp_copies = [r["cid"] for r in copies.values() if r["supprime"] == "True"]
    fiche, n_fiche = max(((c, supp_copies.count(c)) for c in set(supp_copies)), key=lambda x: x[1])
    cc.journal(f"fiche la plus touchée : {n_fiche} copies supprimées")
    base = d["longueur"] >= 80
    lignes = []
    for nom, pop in (("toutes les fiches", base),
                     ("sans la fiche la plus touchée", base & (d["cid"] != fiche)),
                     ("avis publiés avant août 2026", base & (d["periode"] > 0)),
                     ("avis publiés en août 2026", base & (d["periode"] == 0))):
        supp = d["supprime"][pop]
        strate = cc.codes(d["periode"][pop], d["note"][pop])
        taux = (np.bincount(strate, weights=supp.astype(float)) / np.bincount(strate))[strate]
        t_per = cc.tirages(supp, strate, rng)
        t_fic = cc.tirages(supp, cc.codes(d["cid"][pop], d["periode"][pop], d["note"][pop]), rng)
        r = cc.mesurer(copie[pop], supp, taux, t_per, t_fic)
        lignes.append({"population": nom, "avis_population": int(pop.sum()),
                       "supprimes_population": int(supp.sum()), "copies": r.pop("avis"), **r,
                       "fiches_avec_copie_supprimee": len(np.unique(d["cid"][pop][copie[pop] & supp]))})
        cc.journal(f"{nom} : {lignes[-1]}")
    cc.ecrire(cc.SORTIES / "C7-robustesse.csv", lignes)
    cc.journal("terminé")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
