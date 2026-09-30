"""1b. De l'export brut au panel 03B, étape par étape.

    uv run python consolidation/1b_entonnoir.py

Produit :
  sorties/1b_entonnoir.csv   une ligne par étape, puis cinq lignes de contrôle (attendu : 0)
  sorties/figures/1b_entonnoir.png
"""
from commun import COULEURS, ecrire_csv, enregistrer, figure, requete

df = requete("1b_entonnoir")
ecrire_csv(df, "1b_entonnoir")

controles = df[df["etape"].str.startswith("contrôle")]
if (controles["avis"] != 0).any():
    print("ATTENTION : un contrôle n'est pas à 0, voir sorties/1b_entonnoir.csv")

# Contrôle : les suppressions restantes à chaque étape.
etapes = df[~df["etape"].str.startswith("contrôle")]
fig, axes = figure(largeur=9, hauteur=3.5)
ax = axes[0][0]
ax.barh(etapes["etape"].str.slice(0, 45), etapes["avis_supprimes"], color=COULEURS["ensemble"])
ax.invert_yaxis()
ax.set_title("Avis supprimés restant à chaque étape")
enregistrer(fig, "1b_entonnoir")
