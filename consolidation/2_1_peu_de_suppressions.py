"""2.1. Google supprime peu une fois l'avis publié.

    uv run python consolidation/2_1_peu_de_suppressions.py

Produit :
  sorties/2_1a_par_annee.csv     base complète, par année de publication
  sorties/2_1b_par_age.csv       avis publiés de J-30 à J+13, suppressions par âge
  sorties/2_1b_resume.csv        les 8 premiers jours comparés à la suite
  sorties/figures/2_1a_par_annee.png
  sorties/figures/2_1b_par_age.png
"""
from commun import COULEURS, ecrire_csv, enregistrer, figure, requete

annee = requete("2_1a_par_annee")
ecrire_csv(annee, "2_1a_par_annee")

age = requete("2_1b_par_age")
ecrire_csv(age, "2_1b_par_age")

resume = requete("2_1b_resume")
ecrire_csv(resume, "2_1b_resume")

# Contrôle : la somme des suppressions par âge redonne le total de la fenêtre.
for perimetre in ["tous", "sans_enseignes"]:
    somme = age[(age["perimetre"] == perimetre) & (age["region"] == "ensemble")]["suppressions"].sum()
    total = resume[(resume["perimetre"] == perimetre) & (resume["region"] == "ensemble")
                   & (resume["tranche"] == "total")]["suppressions"].iloc[0]
    print(f"  contrôle {perimetre} : suppressions par âge {somme} / avis supprimés {total}")

fig, axes = figure(1, 2, largeur=12, hauteur=4.5)
for ax, perimetre in zip(axes[0], ["tous", "sans_enseignes"]):
    d = annee[annee["perimetre"] == perimetre]
    ax.bar(d["annee_publication"], d["pour_10000"], color=COULEURS["ensemble"])
    ax.set_title(f"Suppressions pour 10 000 avis, par année de publication — {perimetre}")
    ax.tick_params(axis="x", rotation=90)
enregistrer(fig, "2_1a_par_annee")

fig, axes = figure(1, 2, largeur=12, hauteur=4.5)
for ax, perimetre in zip(axes[0], ["tous", "sans_enseignes"]):
    for region in ["US", "Europe"]:
        d = age[(age["perimetre"] == perimetre) & (age["region"] == region)]
        ax.plot(d["age_j"], d["pour_10000"], color=COULEURS[region], linewidth=2,
                marker="o", markersize=3, label=region)
    ax.axvline(8.5, color="#999999", linewidth=1, linestyle="--")
    ax.set_title(f"Suppressions du jour pour 10 000 avis en ligne — {perimetre}")
    ax.set_xlabel("âge de l'avis, en jours")
    ax.legend()
enregistrer(fig, "2_1b_par_age")
