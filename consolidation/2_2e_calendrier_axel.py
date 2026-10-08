"""2.2e. Quand les avis des deux phénomènes sont supprimés : deux graphiques pour Axel.

    uv run python consolidation/2_2e_calendrier_axel.py

Aucune requête : lit `sorties/2_2a_calendrier.csv`, produit par `2_2_deux_phenomenes.py`.
Remplace la lecture du nuage de points de `2_2a_calendrier.png`, qui reste en place.

Vague k = passage du robot du (10 + k) août 2026 : 14 passages, un par jour, du
11 au 24 août. Une suppression se constate au passage suivant l'absence : les
suppressions observées vont du 12 au 24 août. Celles d'avant le 12 août sont
inconnues. Les avis publiés avant le 11 août sont gardés : seule leur date de
suppression compte ici.

Produit :
  sorties/figures/2_2e_par_jour.png   recommandé : avis supprimés par jour de suppression
  sorties/figures/2_2e_delai.png      délai entre publication et suppression, avis
                                      publiés pendant l'observation
"""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Patch

from commun import ENCRE, ENCRE_SECONDAIRE, FIGURES, SORTIES, figure

GROUPES = {"chaines_antiparasitaires": "4 chaînes antiparasitaires américaines",
           "salles_espagnoles": "2 salles de sport espagnoles"}
# Trois classes de note : 1 étoile, 2 à 4, 5 étoiles. Couleurs du projet.
NOTES = {"1 étoile": "#eb6834", "2 à 4 étoiles": "#b5b3ad", "5 étoiles": "#2a78d6"}
PREMIER_PASSAGE = pd.Timestamp("2026-08-11")
DPI = 200


def classe(note):
    return "1 étoile" if note == 1 else "5 étoiles" if note == 5 else "2 à 4 étoiles"


def enregistrer(fig, nom):
    """Comme `commun.enregistrer`, sans refaire la mise en page, en haute résolution."""
    FIGURES.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURES / f"{nom}.png", dpi=DPI)
    plt.close(fig)
    print(f"  sorties/figures/{nom}.png")


def pct(n, total):
    return f"{100 * n / total:.0f} %"


def date_courte(d):
    return f"{d.day} août"


d = pd.read_csv(SORTIES / "2_2a_calendrier.csv", sep=";")
d["publication"] = pd.to_datetime(d["jour_publication"])
d["suppression"] = PREMIER_PASSAGE + pd.to_timedelta(d["vague_suppression"] - 1, unit="D")
d["delai"] = (d["suppression"] - d["publication"]).dt.days
d["classe"] = d["note"].map(classe)
assert d["suppression"].min() >= pd.Timestamp("2026-08-12")
assert d["suppression"].max() <= pd.Timestamp("2026-08-24")


def barres_empilees(ax, t, x, cle):
    """Barres empilées par classe de note ; `t` agrégé par `cle` et classe."""
    bas = np.zeros(len(x))
    for nom, couleur in NOTES.items():
        v = t[t["classe"] == nom].set_index(cle)["avis_supprimes"].reindex(x, fill_value=0).to_numpy()
        ax.bar(range(len(x)), v, bottom=bas, width=0.75, color=couleur, edgecolor="#fcfcfb",
               linewidth=0.8, zorder=2)
        bas += v
    for i, total in enumerate(bas):
        if total:
            ax.text(i, total + 4, f"{int(total)}", ha="center", va="bottom", fontsize=8, color=ENCRE)
    return bas


def legende(fig):
    fig.legend(handles=[Patch(color=c, label=n) for n, c in NOTES.items()], title="Note de l'avis",
               loc="upper right", bbox_to_anchor=(0.99, 0.91), ncol=3, fontsize=9, title_fontsize=9,
               frameon=False)


# ---------------------------------------------------------------------------
# 1. Recommandé : avis supprimés par jour de suppression, du 12 au 24 août.
# ---------------------------------------------------------------------------
jours = pd.date_range("2026-08-12", "2026-08-24")
t = d.groupby(["groupe", "suppression", "classe"], as_index=False)["avis_supprimes"].sum()
haut = t.groupby(["groupe", "suppression"])["avis_supprimes"].sum().max() * 1.12

fig, axes = figure(1, 2, largeur=13, hauteur=6)
parts = {}
for ax, (groupe, nom) in zip(axes[0], GROUPES.items()):
    g = t[t["groupe"] == groupe]
    par_jour = g.groupby("suppression")["avis_supprimes"].sum().sort_values(ascending=False)
    total, deux = par_jour.sum(), par_jour.iloc[:2]
    jours_pic = sorted(deux.index)
    parts[groupe] = pct(deux.sum(), total)
    barres_empilees(ax, g, jours, "suppression")
    ax.set_xticks(range(len(jours)), [f"{j.day}" for j in jours])
    ax.set_xlabel("jour de suppression constatée, août 2026")
    ax.set_ylim(0, haut)
    ax.grid(axis="x", visible=False)
    ax.set_title(f"{nom} : {pct(deux.sum(), total)} des {total} suppressions\n"
                 f"en 2 jours, le {jours_pic[0].day} et le {date_courte(jours_pic[1])}",
                 loc="left", fontsize=11, color=ENCRE)
axes[0][0].set_ylabel("avis supprimés ce jour-là")
legende(fig)
fig.suptitle(f"Suppressions par vagues : 2 jours portent {parts['chaines_antiparasitaires']} des "
             f"suppressions des chaînes et {parts['salles_espagnoles']} de celles des salles",
             x=0.02, ha="left", fontsize=13, color=ENCRE)
fig.text(0.02, 0.905,
         "Chaque barre = avis supprimés constatés ce jour-là par le robot, toutes dates de publication. "
         "Même échelle sur les deux panneaux.\n"
         "Le robot passe une fois par jour du 11 au 24 août 2026 : une suppression faite avant le "
         "12 août n'est pas visible.",
         ha="left", va="top", fontsize=8.5, color=ENCRE_SECONDAIRE)
fig.tight_layout(rect=(0, 0, 1, 0.86))
enregistrer(fig, "2_2e_par_jour")

# ---------------------------------------------------------------------------
# 2. Délai entre publication et suppression, avis publiés pendant l'observation.
# Un avis publié dès le 11 août est vu dès son premier jour : tous ses délais
# de suppression sont observables, jusqu'au 24 août.
# ---------------------------------------------------------------------------
r = d[d["publication"] >= PREMIER_PASSAGE]
# Plus long délai observable : un avis du 11 août, suivi jusqu'au 24.
delais = list(range(1, 14))
t = r.groupby(["groupe", "delai", "classe"], as_index=False)["avis_supprimes"].sum()
haut = t.groupby(["groupe", "delai"])["avis_supprimes"].sum().max() * 1.12

fig, axes = figure(1, 2, largeur=13, hauteur=6)
for ax, (groupe, nom) in zip(axes[0], GROUPES.items()):
    g = t[t["groupe"] == groupe]
    total = int(g["avis_supprimes"].sum())
    ax.set_xticks(range(len(delais)), [str(j) for j in delais])
    ax.set_xlabel("jours entre la publication et la suppression")
    ax.set_xlim(-0.6, len(delais) - 0.4)
    ax.set_ylim(0, haut)
    ax.grid(axis="x", visible=False)
    if total == 0:
        avant = int(d.loc[d["groupe"] == groupe, "avis_supprimes"].sum())
        ax.text(0.5, 0.5, f"Aucun avis supprimé publié à partir du 11 août.\n"
                          f"Les {avant} suppressions portent sur des avis publiés avant.",
                transform=ax.transAxes, ha="center", va="center", fontsize=9.5,
                color=ENCRE_SECONDAIRE, style="italic")
        ax.set_title(f"{nom} : aucun avis concerné", loc="left", fontsize=11, color=ENCRE)
        continue
    barres_empilees(ax, g, delais, "delai")
    six_sept = int(g[g["delai"].isin([6, 7])]["avis_supprimes"].sum())
    ax.set_title(f"{nom} : {pct(six_sept, total)} des {total} suppressions\n"
                 "6 ou 7 jours après la publication", loc="left", fontsize=11, color=ENCRE)
axes[0][0].set_ylabel("avis supprimés")
legende(fig)
fig.suptitle("Les avis récents des chaînes sont supprimés une semaine après leur publication",
             x=0.02, ha="left", fontsize=13, color=ENCRE)
fig.text(0.02, 0.905,
         "Chaque barre = avis publiés du 11 au 23 août 2026 et supprimés ce nombre de jours après leur "
         "publication. Même échelle sur les deux panneaux.\n"
         "Un avis du 11 août est suivi 13 jours, un avis du 20 août 4 jours : les longs délais reposent "
         "sur moins d'avis.",
         ha="left", va="top", fontsize=8.5, color=ENCRE_SECONDAIRE)
fig.tight_layout(rect=(0, 0, 1, 0.86))
enregistrer(fig, "2_2e_delai")
