#!/usr/bin/env python3
"""Prénom de l'avis, entre avis d'une même fiche, sur les avis neufs de 03C.

    PYTHONPATH=".venv/Lib/site-packages;outils" <python uv> etudes-ponctuelles/2026-10-07-prenom-dans-les-fiches/meme_fiche_03C.py

Vérification du 2026-10-07 pour la réponse à Axel. Même montage que
`2026-10-06-pic-03C/calcul_meme_fiche.py` : avis 4-5 étoiles de 03C publiés du 7 au 17
août (corpus et définitions de 07F), supprimés au plus tard au 7e jour ; un indicateur
par fiche à la place du secteur, de la taille et de la région, sur les fiches qui ont au
moins une suppression ; prénom, photo, réponse et jour de pic dans le modèle. Avec et
sans les six enseignes. N'écrit aucun fichier.
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
for nom, d0 in [("avec enseignes", df), ("sans enseignes", df[~df["enseigne"]])]:
    s = d0[d0["cid"].isin(d0.loc[d0["supprime"] == 1, "cid"].unique())]
    X = pd.concat([s[variables].astype(float),
                   pd.get_dummies(s["cid"], prefix="f", drop_first=True, dtype=float)], axis=1)
    X = sm.add_constant(X.loc[:, X.std() > 0], has_constant="add")
    res = sm.GLM(s["supprime"].astype(float), X, family=sm.families.Binomial()).fit(
        cov_type="cluster", cov_kwds={"groups": s["cid"].factorize()[0]})
    ic = res.conf_int().loc["prenom"]
    print(f"{nom} : {s['cid'].nunique()} fiches, {len(s)} avis, {int(s['supprime'].sum())} supprimés "
          f"-> prénom, même fiche ×{np.exp(res.params['prenom']):.2f} "
          f"[{np.exp(ic[0]):.2f} ; {np.exp(ic[1]):.2f}]")
