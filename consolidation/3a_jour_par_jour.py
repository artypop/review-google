"""3a. Réponse du propriétaire : suppressions jour par jour, du 3e au 8e jour.

    uv run python consolidation/3a_jour_par_jour.py

Produit :
  sorties/3_population.csv       la population, étape par étape
  sorties/3a_jour_par_jour.csv   par habitude, réponse au 2e jour, taille, périmètre
  sorties/figures/3a_jour_par_jour.png
"""
from commun import COULEURS, ecrire_csv, enregistrer, figure, requete

ecrire_csv(requete("3_population"), "3_population")
df = requete("3a_jour_par_jour")
ecrire_csv(df, "3a_jour_par_jour")

# Contrôle : une ligne par taille, une colonne par habitude ; périmètre sans enseignes.
d0 = df[df["perimetre"] == "sans_enseignes"]
fig, axes = figure(2, 2, largeur=11, hauteur=7)
for i, taille in enumerate(["mono + small", "large"]):
    for j, habitude in enumerate(["plus de 75 %", "75 % ou moins"]):
        ax = axes[i][j]
        for reponse, couleur in [("oui", COULEURS["ensemble"]), ("non", COULEURS["Europe"])]:
            d = d0[(d0["taille"] == taille) & (d0["habitude"] == habitude)
                   & (d0["reponse_au_2e_jour"] == reponse)]
            # Tous les avis sont en ligne au 2e jour : la courbe part de 10 000.
            ax.plot([2] + d["jour_apres_publication"].tolist(),
                    [10000] + d["encore_en_ligne_sur_10000"].tolist(), color=couleur,
                    linewidth=2, marker="o", markersize=3,
                    label=f"réponse au 2e jour : {reponse}")
        ax.set_title(f"{taille}, fiche qui répond à {habitude}")
        ax.set_xlabel("jour après publication")
        ax.legend()
fig.suptitle("Avis encore en ligne sur 10 000 en ligne au 2e jour — sans enseignes")
enregistrer(fig, "3a_jour_par_jour")
