#!/usr/bin/env python3
"""Part des nouveaux avis 4-5 étoiles supprimés en 7 jours selon la longueur du texte.

    PYTHONPATH=".venv/Lib/site-packages;outils" <python uv> etudes-ponctuelles/2026-10-06-longueur-texte-03C/calcul.py

Vérification du 2026-10-06, après la remarque de Matthieu (« les avis longs sont plus
supprimés ») sur l'idée « Écrire un roman ne sert à rien » des faits saignants.

  corpus       data/local/03C_7_17_aout_prenom.parquet, avis 4-5 étoiles, mêmes
               filtres que 07F (prénom connu, fiche relevée jusqu'au 24 août) :
               24 191 avis, 631 supprimés au plus tard au 7e jour.
  longueur     caractères du texte sans les espaces de début et de fin, mêmes
               bornes que 2026-10-02-longueur-texte-quintiles.
  contrôles    secteur, taille, région ; avis d'une même fiche regroupés pour les
               marges d'incertitude.
"""
import sys

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, "outils")
from local import connexion  # noqa: E402

CHAINES = ("ecoshield pest solutions", "insight pest solutions",
           "pointe pest control", "bulwark exterminating")
SALLES = ("3163466139043001754", "10346942689164695031")
BORNES = [-1, 0, 40, 80, 130, 240, 10**9]
GROUPES = ["sans texte", "1-40", "41-80", "81-130", "131-240", "241+"]

con = connexion("4GB")
cond = " OR ".join(f"lower(b.name) LIKE '{n}%'" for n in CHAINES)
df = con.execute(f"""
WITH fin AS (SELECT cid, max(CAST(last_seen_at AS DATE)) fs
             FROM reviews_doublons_cleaned_all GROUP BY cid)
SELECT c.cid, COALESCE(length(trim(c.text)), 0) AS lg,
       if(b.country = 'US', 'US', 'Europe') AS region, b.industry, b.bucket,
       COALESCE({cond}, FALSE) OR c.cid IN {SALLES} AS enseigne,
       coalesce(date_diff('day', c.created_at, c.deleted_detected_at) <= 7, false)::int AS sup
FROM 'data/local/03C_7_17_aout_prenom.parquet' c
LEFT JOIN businesses b ON b.cid = c.cid
LEFT JOIN fin f ON f.cid = c.cid
WHERE c.star >= 4 AND c.prenom IS NOT NULL AND f.fs >= DATE '2026-08-24'
""").df()
df["g"] = pd.cut(df.lg, BORNES, labels=GROUPES)
print(f"{len(df)} avis, {df.sup.sum()} supprimés au plus tard au 7e jour")

populations = {"tous": df, "sans enseignes": df[~df.enseigne]}
populations.update({f"sans enseignes, {r}": df[~df.enseigne & (df.region == r)]
                    for r in ("US", "Europe")})
for nom, d in populations.items():
    t = d.groupby("g", observed=True).agg(avis=("sup", "size"), supprimes=("sup", "sum"))
    t["pour_1000"] = (1000 * t.supprimes / t.avis).round(1)
    print(f"\n== {nom}\n{t.to_string()}")

for nom in ("tous", "sans enseignes"):
    d = populations[nom]
    m = smf.logit("sup ~ C(g, Treatment('sans texte')) + C(industry) + C(bucket) + C(region)",
                  d).fit(disp=0, cov_type="cluster",
                         cov_kwds={"groups": pd.factorize(d.cid)[0]})
    r = np.exp(pd.concat([m.params, m.conf_int()], axis=1)).filter(like="C(g", axis=0)
    r.columns = ["risque", "bas", "haut"]
    print(f"\n## à secteur, taille et région égaux, {nom} (comparé à sans texte)\n{r.round(2).to_string()}")
