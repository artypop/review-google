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

    # Barres verticales US et Europe, modalités en abscisse, un panneau par périmètre.
    n = large["modalite"].nunique()
    fig, axes = figure(1, 2, largeur=max(12, 1.6 * n), hauteur=5)
    longs = large["modalite"].astype(str).str.len().max() > 12
    # Même échelle sur les deux panneaux, pour comparer avec et sans enseignes.
    haut = 1.1 * large[["us_pour_10000", "europe_pour_10000"]].max().max()
    for ax, perimetre in zip(axes[0], ["tous", "sans_enseignes"]):
        p = large[large["perimetre"] == perimetre]
        # Abscisse croissante : 1 à 5 étoiles, secteurs par ordre alphabétique.
        # Les autres caractéristiques sont déjà rangées dans l'ordre croissant.
        if car == "note":
            p = p.iloc[::-1]
        elif car == "secteur":
            p = p.sort_values("modalite")
        x = np.arange(len(p))
        for decalage, region, nom in [(-0.2, "us", "US"), (0.2, "europe", "Europe")]:
            barres = ax.bar(x + decalage, p[f"{region}_pour_10000"], width=0.38,
                            color=COULEURS[nom], label=nom)
            # La valeur au-dessus de chaque barre, en suppressions pour 10 000 avis.
            ax.bar_label(barres, labels=[f"{v:,}".replace(",", " ") for v in p[f"{region}_pour_10000"]],
                         padding=2, fontsize=7.5)
        ax.set_xticks(x, p["modalite"], rotation=30 if longs else 0, ha="right" if longs else "center")
        ax.set_ylabel("suppressions pour 10 000 avis")
        ax.set_ylim(0, haut)
        ax.grid(axis="x", visible=False)
        ax.set_title(f"{car} — {perimetre}")
        ax.legend()
    enregistrer(fig, f"2_3_{car}")
