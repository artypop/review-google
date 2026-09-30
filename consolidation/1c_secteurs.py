"""1c. Les secteurs : avis par secteur et par taille, suppressions pour 10 000 avis par région.

    uv run python consolidation/1c_secteurs.py

Base complète (`reviews_doublons_cleaned_all`). Produit :
  sorties/1c_avis_secteur_taille.csv
  sorties/1c_suppressions_secteur_region.csv   le CSV de l'histogramme
  sorties/figures/1c_suppressions_secteur_region.png
"""
import numpy as np

from commun import COULEURS, ecrire_csv, enregistrer, figure, requete

taille = requete("1c_avis_secteur_taille")
ecrire_csv(taille, "1c_avis_secteur_taille")

suppr = requete("1c_suppressions_secteur_region")
ecrire_csv(suppr, "1c_suppressions_secteur_region")

# Contrôle : la somme des secteurs redonne la ligne « Tous secteurs ».
for perimetre, d in suppr.groupby("perimetre"):
    total = d[d["secteur"] == "Tous secteurs"]["ensemble_avis"].iloc[0]
    somme = d[d["secteur"] != "Tous secteurs"]["ensemble_avis"].sum()
    print(f"  contrôle {perimetre} : somme des secteurs {somme} / total {total}")

# Contrôle : l'histogramme, Europe et US côte à côte, un panneau par périmètre.
fig, axes = figure(1, 2, largeur=12, hauteur=4.5)
for ax, perimetre in zip(axes[0], ["tous", "sans_enseignes"]):
    d = suppr[(suppr["perimetre"] == perimetre) & (suppr["secteur"] != "Tous secteurs")]
    y = np.arange(len(d))
    ax.barh(y - 0.2, d["us_pour_10000"], height=0.38, color=COULEURS["US"], label="US")
    ax.barh(y + 0.2, d["europe_pour_10000"], height=0.38, color=COULEURS["Europe"], label="Europe")
    ax.set_yticks(y, d["secteur"])
    ax.invert_yaxis()
    ax.set_title(f"Suppressions pour 10 000 avis — {perimetre}")
    ax.legend()
enregistrer(fig, "1c_suppressions_secteur_region")
