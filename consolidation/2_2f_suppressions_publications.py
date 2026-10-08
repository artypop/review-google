"""2.2f. Avis supprimés rapportés aux avis publiés, par jour de publication.

    uv run python consolidation/2_2f_suppressions_publications.py

Fiches des deux phénomènes (4 chaînes antiparasitaires US, 2 salles espagnoles),
avis publiés du 1er juillet au 23 août 2026. Le calcul est en tête de
`sql/2_2f_publications_par_jour.sql`.

Produit :
  sorties/2_2f_publications_par_jour.csv
      par groupe et jour de publication : avis publiés, moyenne mobile sur 7 jours,
      avis supprimés, part supprimée
  sorties/figures/2_2f_suppressions_publications.png
"""
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

from commun import ENCRE, ENCRE_SECONDAIRE, FIGURES, ecrire_csv, figure, requete

GROUPES = {"chaines_antiparasitaires": "4 chaînes antiparasitaires américaines",
           "salles_espagnoles": "2 salles de sport espagnoles"}
NOTES = {"1 étoile": "#eb6834", "2 à 4 étoiles": "#8a8984", "5 étoiles": "#2a78d6"}
PUBLIES = "#dcdad5"
# Un avis publié après le 17 août est suivi moins de 7 jours : ses suppressions
# sont incomplètes. Zone grisée sur le graphique.
SUIVI_COMPLET = pd.Timestamp("2026-08-17")
PREMIER_PASSAGE = pd.Timestamp("2026-08-11")

d = requete("2_2f_publications_par_jour")
d["jour_publication"] = pd.to_datetime(d["jour_publication"])
jours = pd.date_range("2026-07-01", "2026-08-23")

# Une ligne par groupe et par jour, jours sans avis compris (moyenne mobile juste).
lignes = []
for groupe in GROUPES:
    g = (d[d["groupe"] == groupe].groupby("jour_publication")[["avis_publies", "avis_supprimes"]].sum()
         .reindex(jours, fill_value=0))
    g["moyenne_mobile_7j"] = g["avis_publies"].rolling(7, min_periods=7).mean().round(1)
    g["part_supprimee_pct"] = (100 * g["avis_supprimes"] / g["avis_publies"].where(g["avis_publies"] > 0)).round(1)
    lignes.append(g.rename_axis("jour_publication").reset_index().assign(groupe=groupe))
t = pd.concat(lignes)[["groupe", "jour_publication", "avis_publies", "moyenne_mobile_7j",
                       "avis_supprimes", "part_supprimee_pct"]]
sortie = t.copy()
sortie["jour_publication"] = sortie["jour_publication"].dt.date
ecrire_csv(sortie, "2_2f_publications_par_jour")


def constat(groupe):
    """Titre-constat de chaque panneau, calculé sur les données."""
    g = t[t["groupe"] == groupe].set_index("jour_publication")
    if groupe == "chaines_antiparasitaires":
        # Avis vus dès leur premier jour et suivis au moins 7 jours.
        p = g.loc["2026-08-11":"2026-08-17"]
        pub, sup = int(p["avis_publies"].sum()), int(p["avis_supprimes"].sum())
        return (f"{GROUPES[groupe]} : {100 * sup / pub:.0f} % des avis publiés du 11 au 17 août "
                f"supprimés ({sup} sur {pub}),\nsoit un avis sur {pub / sup:.0f}")
    p = g.loc["2026-08-01":"2026-08-02"]
    pub, sup = int(p["avis_publies"].sum()), int(p["avis_supprimes"].sum())
    normal = g.loc["2026-07-01":"2026-07-31", "avis_publies"].sum()
    return (f"{GROUPES[groupe]} : {pub} avis publiés les 1er et 2 août, {sup} supprimés,\n"
            f"pour {int(normal)} avis publiés sur tout le mois de juillet")


haut = t["avis_publies"].max() * 1.3
fig, axes = figure(2, 1, largeur=13, hauteur=9)
for ax, groupe in zip(axes[:, 0], GROUPES):
    g = t[t["groupe"] == groupe]
    x = g["jour_publication"]
    ax.axvspan(SUIVI_COMPLET + pd.Timedelta(hours=12), jours[-1] + pd.Timedelta(hours=12),
               color="#efeeea", zorder=0)
    ax.bar(x, g["avis_publies"], width=0.8, color=PUBLIES, zorder=1)
    # Supprimés par-dessus, empilés par note.
    bas = np.zeros(len(g))
    s = d[d["groupe"] == groupe]
    for nom, couleur in NOTES.items():
        v = (s[s["classe"] == nom].set_index("jour_publication")["avis_supprimes"]
             .reindex(jours, fill_value=0).to_numpy())
        ax.bar(x, v, bottom=bas, width=0.8, color=couleur, zorder=2)
        bas += v
    ax.plot(x, g["moyenne_mobile_7j"], color=ENCRE, linewidth=1.5, zorder=3)
    # Au-dessus de chaque barre : avis supprimés / avis publiés ce jour-là.
    for xi, pub, sup in zip(x, g["avis_publies"], g["avis_supprimes"]):
        if pub:
            ax.text(xi, pub + haut * 0.012, f"{sup} / {pub}", rotation=90, ha="center", va="bottom",
                    fontsize=6.5, color=ENCRE if sup else ENCRE_SECONDAIRE, zorder=4,
                    bbox=dict(facecolor="#fcfcfb", edgecolor="none", pad=0.6))
    ax.axvline(PREMIER_PASSAGE - pd.Timedelta(hours=12), color=ENCRE_SECONDAIRE, linestyle=":",
               linewidth=1, zorder=3)
    ax.text(PREMIER_PASSAGE - pd.Timedelta(hours=10), haut * 0.97, "premier passage\ndu robot, 11 août",
            ha="left", va="top", fontsize=8, color=ENCRE_SECONDAIRE)
    ax.text(SUIVI_COMPLET + pd.Timedelta(hours=18), haut * 0.97, "suivis moins de\n7 jours",
            ha="left", va="top", fontsize=8, color=ENCRE_SECONDAIRE)
    ax.set_ylim(0, haut)
    ax.set_xlim(jours[0] - pd.Timedelta(days=1), jours[-1] + pd.Timedelta(days=1))
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=mdates.MO))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m"))
    ax.grid(axis="x", visible=False)
    ax.set_ylabel("avis par jour de publication")
    ax.set_title(constat(groupe), loc="left", fontsize=11, color=ENCRE)
axes[1][0].set_xlabel("jour de publication de l'avis, 2026")

fig.legend(handles=[Patch(color=PUBLIES, label="avis publiés ce jour-là"),
                    Line2D([0], [0], color=ENCRE, linewidth=1.5, label="moyenne sur les 7 derniers jours"),
                    *[Patch(color=c, label=f"dont supprimés, {n}") for n, c in NOTES.items()]],
           loc="upper left", bbox_to_anchor=(0.02, 0.905), ncol=5, fontsize=8.5, frameon=False)
fig.suptitle("Les chaînes perdent un avis récent sur cinq, les salles presque tous les avis "
             "d'une attaque de deux jours",
             x=0.02, ha="left", fontsize=12.5, color=ENCRE)
fig.text(0.02, 0.955,
         "Chaque barre grise = avis publiés ce jour-là sur ces fiches ; partie colorée = ceux supprimés "
         "pendant le suivi du 11 au 24 août 2026. Au-dessus : supprimés / publiés.\n"
         "Avant le 11 août, les barres colorées sont sous-estimées : un avis supprimé avant le premier "
         "passage du robot n'est pas dans la base. Juillet paraît donc peu touché.",
         ha="left", va="top", fontsize=8.5, color=ENCRE_SECONDAIRE)
fig.tight_layout(rect=(0, 0, 1, 0.88))
FIGURES.mkdir(parents=True, exist_ok=True)
fig.savefig(FIGURES / "2_2f_suppressions_publications.png", dpi=200)
plt.close(fig)
print("  sorties/figures/2_2f_suppressions_publications.png")
