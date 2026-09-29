"""1b. De l'export brut au panel 03B, étape par étape.

    uv run python consolidation/1b_entonnoir.py

Produit :
  sorties/1b_entonnoir.csv   une ligne par étape, puis quatre lignes de contrôle (attendu : 0)
  sorties/1b_retires_365_jours_par_fiche.csv   fiches qui perdent des avis supprimés à l'étape 4
  sorties/1b_retires_365_jours_profil.csv      les mêmes suppressions, comptées par dimension
  sorties/figures/1b_entonnoir.png
"""
from commun import COULEURS, ecrire_csv, enregistrer, figure, requete

df = requete("1b_entonnoir")
ecrire_csv(df, "1b_entonnoir")

retires = requete("1b_retires_365_jours_par_fiche")
ecrire_csv(retires, "1b_retires_365_jours_par_fiche")
print(retires.groupby("enseigne_signalee")[["suppressions_retirees", "dont_5_etoiles"]].sum())
ecrire_csv(requete("1b_retires_365_jours_profil"), "1b_retires_365_jours_profil")

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
