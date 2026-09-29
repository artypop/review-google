"""1d. Survie des avis publiés de J-7 à J+7 (4 au 18 août), jour par jour.

    uv run python consolidation/1d_survie.py

Le calcul est expliqué en tête de `sql/1d_survie.sql`. Produit :
  sorties/1d_survie.csv
  sorties/figures/1d_survie.png
"""
from commun import COULEURS, ecrire_csv, enregistrer, figure, requete

df = requete("1d_survie")
ecrire_csv(df, "1d_survie")

fig, axes = figure(1, 2, largeur=12, hauteur=4.5)
for ax, perimetre in zip(axes[0], ["tous", "sans_enseignes"]):
    for region in ["US", "Europe", "ensemble"]:
        d = df[(df["perimetre"] == perimetre) & (df["region"] == region)]
        ax.plot(d["age_j"], d["encore_en_ligne_sur_10000"], color=COULEURS[region],
                linewidth=2, marker="o", markersize=3, label=region)
    ax.set_title(f"Avis encore en ligne sur 10 000 publiés — {perimetre}")
    ax.set_xlabel("âge de l'avis, en jours")
    ax.legend()
enregistrer(fig, "1d_survie")
