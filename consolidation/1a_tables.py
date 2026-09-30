"""1a. Ce que contiennent les tables `reviews`, `reviews_doublons_cleaned_all` et `businesses`.

    uv run python consolidation/1a_tables.py

Produit :
  sorties/1a_tables.csv            lignes, avis, fiches, dates, suppressions par table
  sorties/1a_fiches_par_case.csv   fiches par région, secteur et taille
  sorties/figures/1a_fiches_par_case.png
"""
from commun import COULEURS, ecrire_csv, enregistrer, figure, requete

ecrire_csv(requete("1a_tables"), "1a_tables")

cases = requete("1a_fiches_par_case")
ecrire_csv(cases, "1a_fiches_par_case")

# Contrôle : les fiches par secteur, US et Europe côte à côte.
fig, axes = figure(largeur=9, hauteur=4.5)
ax = axes[0][0]
pivot = cases.pivot(index="secteur", columns="region", values="fiches")
pivot[["US", "Europe"]].plot.barh(ax=ax, color=[COULEURS["US"], COULEURS["Europe"]], width=0.8)
ax.set_title("Fiches du panel par secteur")
ax.set_xlabel("fiches")
ax.set_ylabel("")
enregistrer(fig, "1a_fiches_par_case")
