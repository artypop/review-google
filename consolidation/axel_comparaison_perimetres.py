"""Pour Axel : le taux de suppression calculé sur notre panel et sur « sa » table.

    uv run python consolidation/axel_comparaison_perimetres.py

Produit :
  sorties/axel_comparaison_perimetres.csv   une ligne par caractéristique et modalité,
                                            les deux tables côte à côte
  sorties/figures/axel_comparaison_perimetres.png
L'explication est dans `explication_pour_axel.md`.
"""
import numpy as np

from commun import COULEURS, ecrire_csv, enregistrer, figure, requete

df = requete("axel_comparaison_perimetres")

# Les deux tables côte à côte, pour une lecture directe.
large = df.pivot_table(index=["caracteristique", "ordre", "modalite"], columns="table_utilisee",
                       values=["avis", "suppressions", "pour_10000"]).astype("Int64")
large.columns = [f"{'panel' if t.startswith('1') else 'axel'}_{m}" for m, t in large.columns]
colonnes = [f"{t}_{m}" for t in ["panel", "axel"] for m in ["avis", "suppressions", "pour_10000"]]
large = large[colonnes].reset_index().sort_values(["caracteristique", "ordre"]).drop(columns="ordre")
ecrire_csv(large, "axel_comparaison_perimetres")

fig, axes = figure(1, 3, largeur=14, hauteur=4.5)
for ax, car in zip(axes[0], ["1. note", "2. photos publiées par l'auteur", "3. niveau Local Guide"]):
    d = large[large["caracteristique"] == car]
    x = np.arange(len(d))
    ax.bar(x - 0.2, d["panel_pour_10000"], width=0.38, color=COULEURS["ensemble"], label="notre panel (03B)")
    ax.bar(x + 0.2, d["axel_pour_10000"], width=0.38, color=COULEURS["Europe"], label="table d'Axel")
    ax.set_xticks(x, d["modalite"], rotation=20)
    ax.set_title(car.split(". ", 1)[1])
    ax.set_ylabel("suppressions pour 10 000 avis")
    ax.legend()
fig.suptitle("Le même calcul sur deux tables")
enregistrer(fig, "axel_comparaison_perimetres")
