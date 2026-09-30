"""2.2. Les deux phénomènes : les 4 chaînes antiparasitaires US et les 2 salles espagnoles.

    uv run python consolidation/2_2_deux_phenomenes.py

Base complète (`reviews_doublons_cleaned_all`). Produit :
  sorties/2_2_resume.csv        par enseigne : avis, suppressions, notes, délais
  sorties/2_2a_calendrier.csv   date de publication × date de suppression des avis supprimés
  sorties/2_2b_delai.csv        jours entre publication et suppression, par note
  sorties/2_2c_auteurs.csv      profil des auteurs, avis supprimés et conservés
  sorties/2_2_par_jour.csv      avis supprimés par jour de publication et par jour de suppression
  sorties/figures/2_2a_calendrier.png
  sorties/figures/2_2b_delai.png
"""
import pandas as pd

from commun import COULEURS, ecrire_csv, enregistrer, figure, requete

GROUPES = {"chaines_antiparasitaires": "4 chaînes antiparasitaires US",
           "salles_espagnoles": "2 salles de sport espagnoles"}

ecrire_csv(requete("2_2_resume"), "2_2_resume")
cal = requete("2_2a_calendrier")
ecrire_csv(cal, "2_2a_calendrier")
delai = requete("2_2b_delai")
ecrire_csv(delai, "2_2b_delai")
ecrire_csv(requete("2_2c_auteurs"), "2_2c_auteurs")
ecrire_csv(requete("2_2_par_jour"), "2_2_par_jour")

# Contrôle : chaque point est un couple (publication, suppression), sa taille le
# nombre d'avis. Seuls les avis publiés depuis le 1er juillet 2026 sont tracés.
fig, axes = figure(1, 2, largeur=12, hauteur=5)
for ax, (groupe, titre) in zip(axes[0], GROUPES.items()):
    d = cal[(cal["groupe"] == groupe)
            & (pd.to_datetime(cal["jour_publication"]) >= "2026-07-01")]
    d = d.groupby(["jour_publication", "jour_suppression", "note"], as_index=False)["avis_supprimes"].sum()
    for note, couleur in [(5, COULEURS["US"]), (1, COULEURS["Europe"])]:
        n = d[d["note"] == note]
        ax.scatter(pd.to_datetime(n["jour_publication"]), pd.to_datetime(n["jour_suppression"]),
                   s=12 * n["avis_supprimes"], color=couleur, alpha=0.7, label=f"{note} étoile(s)")
    autres = d[~d["note"].isin([1, 5])]
    ax.scatter(pd.to_datetime(autres["jour_publication"]), pd.to_datetime(autres["jour_suppression"]),
               s=12 * autres["avis_supprimes"], color="#999999", alpha=0.7, label="2 à 4 étoiles")
    ax.set_title(f"{titre} : publication et suppression")
    ax.set_xlabel("jour de publication")
    ax.set_ylabel("jour de suppression")
    ax.tick_params(axis="x", rotation=45)
    ax.legend()
enregistrer(fig, "2_2a_calendrier")

fig, axes = figure(1, 2, largeur=12, hauteur=4.5)
for ax, (groupe, titre) in zip(axes[0], GROUPES.items()):
    d = delai[(delai["groupe"] == groupe) & delai["delai_j"].notna()]
    ax.bar(d["delai_j"], d["supprimes_5_etoiles"], color=COULEURS["US"], label="5 étoiles")
    ax.bar(d["delai_j"], d["supprimes_1_etoile"], bottom=d["supprimes_5_etoiles"],
           color=COULEURS["Europe"], label="1 étoile")
    reste = d["supprimes"] - d["supprimes_5_etoiles"] - d["supprimes_1_etoile"]
    ax.bar(d["delai_j"], reste, bottom=d["supprimes_5_etoiles"] + d["supprimes_1_etoile"],
           color="#999999", label="2 à 4 étoiles")
    ax.set_title(f"{titre} : jours entre publication et suppression (30 au plus)")
    ax.set_xlabel("jours")
    ax.legend()
enregistrer(fig, "2_2b_delai")
