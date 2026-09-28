#!/usr/bin/env python3
"""
==============================================================================
Script : 03B_features_local_controle.py

Contrôle de la transposition locale du 03B (`03B_features_local.py`) et du
moteur numpy (`glm_numpy.py`), écrit le 2026-09-28.

Rejoue sur la table locale ce que le 07B a produit le 2026-09-21 depuis
BigQuery, avec les fonctions du 07B elles-mêmes :

  1. le tableau croisé, valeur par valeur (`07B_croisements_tous.csv`) ;
  2. le modèle complet sur tout le panel (`07B_coefficients_tous.csv`).

Si statsmodels ne se charge pas, le 07B tourne sur `glm_numpy`. Le contrôle
porte alors sur les deux substitutions à la fois.

Mesuré le 2026-09-28 (glm_numpy) : 75 lignes du tableau croisé sur 78
identiques, les 3 autres sur `n_avis_meme_jour_auteur` (6 avis) ; écart
maximal de coefficient 0,012 (`log_burst`), de 0,003 sur
`log_ratio_pic_journalier_fiche`, sous 0,002 ailleurs hors `vu_tardivement`
(0,004) et `secteur_wellness_fitness` (0,006). Ces écarts viennent du socle
local, qui compte 1 560 avis de plus que `01_reviews_avis_update_et_unique`.

    .venv/Scripts/python.exe logistic-regression-study/python/03B_features_local_controle.py
==============================================================================
"""
from __future__ import annotations

import importlib.util
import sys
from datetime import date
from pathlib import Path

import pandas as pd

PY = Path(__file__).resolve().parent
sys.path.insert(0, str(PY))
import glm_numpy  # noqa: E402

try:
    import statsmodels.api  # noqa: F401
    MOTEUR = "statsmodels"
except ImportError:
    glm_numpy.installer()
    MOTEUR = "glm_numpy"

REFERENCE = PY.parent / "output-study" / "2026-09-21-sorties-07B"
TABLE_LOCALE = PY.parents[1] / "data" / "local" / "reviews_panel_features_03B.parquet"
SORTIES = PY.parent / "output-study" / f"{date.today():%Y-%m-%d}-sorties-07C"


def main() -> int:
    spec = importlib.util.spec_from_file_location("m07B", PY / "07B_regression_panel.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)

    df = m.ajouter_variables(m.compacter(pd.read_parquet(TABLE_LOCALE)))
    SORTIES.mkdir(parents=True, exist_ok=True)

    ici, ref = m.tableau_croise(df), pd.read_csv(REFERENCE / "07B_croisements_tous.csv")
    for t in (ici, ref):
        t["valeur"] = t["valeur"].astype(str).str.replace(r"\.0$", "", regex=True).str.lower()
    croise = ref.merge(ici, on=["caracteristique", "valeur"], how="outer",
                       suffixes=("_bigquery", "_local"))
    croise["identique"] = ((croise["avis_bigquery"] == croise["avis_local"])
                           & (croise["suppressions_bigquery"] == croise["suppressions_local"]))
    croise.to_csv(SORTIES / "07C_controle_croisements.csv", index=False)

    _, tab, _, _ = m.ajuster(df, "tous", True)
    rc = pd.read_csv(REFERENCE / "07B_coefficients_tous.csv", index_col=0)
    coef = pd.DataFrame({
        "coefficient_bigquery": rc["coefficient"], "coefficient_local": tab["coefficient"],
        "std_err_bigquery": rc["std_err"], "std_err_local": tab["std_err"],
        "risque_relatif_bigquery": rc["risque_relatif"],
        "risque_relatif_local": tab["risque_relatif"],
    })
    coef["ecart_coefficient"] = (coef["coefficient_local"] - coef["coefficient_bigquery"]).abs()
    coef.index.name = "variable"
    coef.to_csv(SORTIES / "07C_controle_coefficients_07B.csv")

    print(f"moteur : {MOTEUR}")
    print(f"tableau croisé : {int(croise['identique'].sum())} lignes identiques "
          f"sur {len(croise)}")
    print(croise.loc[~croise["identique"]].to_string(index=False))
    print(f"coefficients : écart maximal {coef['ecart_coefficient'].max():.4f}")
    print(coef.sort_values("ecart_coefficient", ascending=False).head(6).round(4).to_string())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
