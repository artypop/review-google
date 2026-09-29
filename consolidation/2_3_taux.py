"""2.3. Taux de suppression par caractéristique, Europe et US — panel 03B.

    uv run python consolidation/2_3_taux.py

Un calcul direct, sans modèle. Produit un CSV par caractéristique :
  sorties/2_3_<caracteristique>.csv
      une ligne par modalité et par périmètre (tous, sans_enseignes) ;
      pour US, Europe et ensemble : avis, suppressions, fiches touchées, pour 10 000
  sorties/figures/2_3_<caracteristique>.png
"""
import numpy as np

from commun import COULEURS, ecrire_csv, enregistrer, figure, requete

df = requete("2_3_taux")

# Contrôle : pour chaque caractéristique, la somme des modalités redonne le panel.
tous = df[(df["perimetre"] == "tous") & (df["region"] == "ensemble")]
for car, d in tous.groupby("caracteristique"):
    print(f"  contrôle {car:32s} {d['avis'].sum():>6} avis  {d['suppressions'].sum():>5} suppressions")

for car, d in df.groupby("caracteristique"):
    # Régions en colonnes : us_avis, us_suppressions, ..., europe_..., ensemble_...
    large = d.pivot_table(index=["ordre", "modalite", "perimetre"], columns="region",
                          values=["avis", "suppressions", "fiches_touchees", "pour_10000"])
    large.columns = [f"{region.lower()}_{mesure}" for mesure, region in large.columns]
    colonnes = [f"{r}_{m}" for r in ["us", "europe", "ensemble"]
                for m in ["avis", "suppressions", "fiches_touchees", "pour_10000"]]
    large = large[colonnes].astype("Int64")  # la pivot rend des décimaux : 17042,0
    large = (large.reset_index()
             .sort_values(["perimetre", "ordre", "modalite"], ascending=[False, True, True])
             .drop(columns="ordre"))
    if car == "secteur":
        large = large.sort_values(["perimetre", "ensemble_pour_10000"], ascending=[False, False])
    ecrire_csv(large, f"2_3_{car}")

    # Contrôle : barres US et Europe, un panneau par périmètre.
    fig, axes = figure(1, 2, largeur=12, hauteur=0.9 + 0.45 * large["modalite"].nunique() * 2)
    for ax, perimetre in zip(axes[0], ["tous", "sans_enseignes"]):
        p = large[large["perimetre"] == perimetre]
        y = np.arange(len(p))
        ax.barh(y - 0.2, p["us_pour_10000"], height=0.38, color=COULEURS["US"], label="US")
        ax.barh(y + 0.2, p["europe_pour_10000"], height=0.38, color=COULEURS["Europe"], label="Europe")
        ax.set_yticks(y, p["modalite"])
        ax.invert_yaxis()
        ax.set_title(f"{car} — suppressions pour 10 000 avis — {perimetre}")
        ax.legend()
    enregistrer(fig, f"2_3_{car}")
