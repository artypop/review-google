#!/usr/bin/env python3
"""Répondre tôt protège-t-il un avis ? Jalon au 2e jour sur 03C, sans les enseignes.

    PYTHONPATH=".venv/Lib/site-packages;outils" <python uv> etudes-ponctuelles/2026-10-06-reponse-jalon-03C/calcul.py

Vérification du 2026-10-06 pour la fiche « répondre vite » des faits saignants. 07F ne
donne le jalon au 2e jour qu'avec les enseignes (×0,93). Même montage que son contrôle 3,
importé tel quel : avis 4-5 étoiles de 03C vus et en ligne à la fin de leur 2e jour,
réponse au plus tard au 2e jour, suppression du 3e au 7e jour. N'écrit aucun fichier.
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "logistic-regression-study" / "python"))
import importlib  # noqa: E402

m = importlib.import_module("07F_regression_03C_prenom")
df = m.charger()
rep = m.variable_reponse(df)
variables = ["prenom", "photo", rep, "pic"]
J = m.JALON_J
d = df[(df["j_premiere_vue"] <= J) & ~(df["j_suppression"] <= J).fillna(False)].copy()
d["reponse_j2"] = (d["j_reponse"] <= J).fillna(False).astype(int)
d["supprime_j3_j7"] = d["j_suppression"].between(J + 1, m.HORIZON_J).fillna(False).astype(int)
v = [x for x in variables if x != rep] + ["reponse_j2"]

for nom, s in [("tous", d), ("sans enseignes", d[~d["enseigne"]]),
               ("sans enseignes, US", d[~d["enseigne"] & (d["region"] == "US")]),
               ("Europe", d[d["region"] == "Europe"])]:
    g = s.groupby("reponse_j2")["supprime_j3_j7"].agg(["size", "sum", "mean"])
    print(f"\n== {nom} : {len(s)} avis, {int(s['supprime_j3_j7'].sum())} supprimés du 3e au 7e jour")
    print("  réponse au 2e jour : " + " ; ".join(
        f"{'oui' if k else 'non'} {int(r['size'])} avis, {int(r['sum'])} supprimés, {1000 * r['mean']:.1f} pour 1 000"
        for k, r in g.iterrows()))
    for st in (False, True):
        t = m.tableau(m.ajuster(s, v, "supprime_j3_j7", secteur_taille=st), nom, v)
        r = t[t.variable == "reponse_j2"].iloc[0]
        print(f"  réponse au 2e jour{' (secteur, taille égaux)' if st else ''} : ×{r.rapport_de_cotes:.2f} "
              f"[{r.borne_basse:.2f} ; {r.borne_haute:.2f}]")
