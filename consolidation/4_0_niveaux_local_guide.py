"""4.0. Suppressions par niveau Local Guide, pour fixer les paliers des régressions 4.

    uv run python consolidation/4_0_niveaux_local_guide.py

Produit :
  sorties/4_0_niveaux_local_guide.csv
  sorties/figures/4_0_niveaux_local_guide.png
"""
import numpy as np

from commun import COULEURS, ecrire_csv, enregistrer, figure, requete

df = requete("4_0_niveaux_local_guide")
ecrire_csv(df.drop(columns="ordre"), "4_0_niveaux_local_guide")

fig, axes = figure(1, 2, largeur=12, hauteur=4.5)
for ax, perimetre in zip(axes[0], ["tous", "sans_enseignes"]):
    d = df[df["perimetre"] == perimetre]
    x = np.arange(len(d))
    ax.bar(x - 0.2, d["us_pour_10000"], width=0.38, color=COULEURS["US"], label="US")
    ax.bar(x + 0.2, d["europe_pour_10000"], width=0.38, color=COULEURS["Europe"], label="Europe")
    ax.set_xticks(x, d["niveau"])
    ax.set_title(f"Suppressions pour 10 000 avis, par niveau Local Guide — {perimetre}")
    ax.legend()
enregistrer(fig, "4_0_niveaux_local_guide")
