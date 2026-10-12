#!/usr/bin/env python3
"""Jour de pic, entre avis d'une même fiche, sur la base du graphique (n° 7 des faits saignants).

    PYTHONPATH=".venv/Lib/site-packages;outils" <python uv> etudes-ponctuelles/2026-10-06-pic-03C/calcul_meme_fiche.py

Base de `graphique.py` : avis 4-5 étoiles de 03C publiés du 7 au 17 août, sans les six
enseignes, supprimés au plus tard au 7e jour (corpus et définitions de 07F). Montage
« même fiche » de 07G : un indicateur par fiche à la place du secteur, de la taille et de
la région, sur les fiches qui ont au moins une suppression. N'écrit aucun fichier.
"""
import importlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

sys.stdout.reconfigure(encoding="utf-8")
RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "logistic-regression-study" / "python"))
m = importlib.import_module("07F_regression_03C_prenom")

df = m.charger()
rep = m.variable_reponse(df)
variables = ["prenom", "photo", rep, "pic"]
d0 = df[~df["enseigne"]]

for nom, s in [("Ensemble", d0), ("États-Unis", d0[d0["region"] == "US"]),
               ("Europe", d0[d0["region"] == "Europe"])]:
    s = s[s["cid"].isin(s.loc[s["supprime"] == 1, "cid"].unique())]
    X = pd.concat([s[variables].astype(float),
                   pd.get_dummies(s["cid"], prefix="f", drop_first=True, dtype=float)], axis=1)
    X = sm.add_constant(X.loc[:, X.std() > 0], has_constant="add")
    res = sm.GLM(s["supprime"].astype(float), X, family=sm.families.Binomial()).fit(
        cov_type="cluster", cov_kwds={"groups": s["cid"].factorize()[0]})
    ic = res.conf_int().loc["pic"]
    print(f"{nom} : {s['cid'].nunique()} fiches, {len(s)} avis, {int(s['supprime'].sum())} supprimés, "
          f"dont {int(s['pic'].sum())} avis publiés un jour de pic -> même fiche ×{np.exp(res.params['pic']):.2f} "
          f"[{np.exp(ic[0]):.2f} ; {np.exp(ic[1]):.2f}]")
