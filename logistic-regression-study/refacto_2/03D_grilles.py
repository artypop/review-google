"""Suppressions pour 1 000 avis, en grilles croisées, panel 03D.

    uv run python logistic-regression-study/refacto_2/03D_grilles.py

Avis publiés du 6 au 17 août 2026, suivis jusqu'au 24 août, toutes les fiches.
Taux bruts : rien n'est tenu égal, contrairement à la régression. Le comptage
se fait dans BigQuery, une requête par grille dans `sql/`.

Trois grilles, lignes × colonnes :
  secteur × note                    sql/03D_grille_secteur_note.sql
  réponse du propriétaire × note    sql/03D_grille_reponse_note.sql
  secteur × réponse du propriétaire sql/03D_grille_reponse_secteur.sql

Les CSV gardent aussi le périmètre sans les 4 chaînes antiparasitaires
américaines, pour le commentaire. Les graphiques ne montrent que toutes les
fiches.

Produit, dans `sorties/` à côté de ce fichier :
  03D_grille_secteur_note.csv   figures/03D_grille_secteur_note.png
  03D_grille_reponse_note.csv   figures/03D_grille_reponse_note.png
  03D_grille_reponse_secteur.csv figures/03D_grille_reponse_secteur.png
                                 figures/03D_grille_reponse_secteur_sans_enseignes.png
"""
import os
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # pas d'écran sous WSL
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.patches import Patch, Rectangle

PROJET = "client-divers"
DOSSIER = Path(__file__).resolve().parent
SORTIES = DOSSIER / "sorties"
DOSSIER_CLES = Path.home() / ".gcp"

# Libellés de chaque dimension. La case « total » de la dernière ligne ou
# colonne reçoit son nom grille par grille.
NOTES = {"1": "1 étoile", "2": "2 étoiles", "3": "3 étoiles", "4": "4 étoiles", "5": "5 étoiles"}
SECTEURS = {"automotive": "Automobile", "home_services": "Services à domicile",
            "healthcare": "Santé", "wellness_fitness": "Sport et bien-être",
            "food_beverage": "Restauration", "travel": "Voyage", "hospitality": "Hôtellerie"}
REPONSES = {"n'a pas répondu": "N'a pas répondu", "a répondu": "A répondu"}

# Couleur par tranche de suppressions pour 1 000 avis : un seul bleu, du
# clair (peu de suppressions) au foncé (beaucoup).
TRANCHES = [0, 5, 10, 25, 50, 100, 1000]
NOMS_TRANCHES = ["moins de 5", "5 à 10", "10 à 25", "25 à 50", "50 à 100", "100 et plus"]
BLEUS = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#104281"]
# Une case de moins de 100 avis est hachurée, sans chiffre : une ou deux
# suppressions de plus y changent beaucoup le taux.
MIN_AVIS = 100
HACHURE = "#b0afa9"
ENCRE, GRIS, FOND = "#0b0b0b", "#52514e", "#fcfcfb"


def client():
    """Le client BigQuery, avec la clé de service de `~/.gcp/`, comme `consolidation/commun.py`."""
    if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") and DOSSIER_CLES.is_dir():
        cles = sorted(DOSSIER_CLES.glob("*.json"))
        if len(cles) > 1:
            raise SystemExit(f"{len(cles)} clés dans {DOSSIER_CLES}, en garder une.")
        if cles:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(cles[0])
    from google.cloud import bigquery
    return bigquery.Client(project=PROJET, location="EU")


def milliers(n):
    return f"{int(n):,}".replace(",", " ")


PERIMETRES = {"tous": "toutes les fiches",
              "sans_enseignes": "sans les 4 chaînes antiparasitaires américaines"}


def grille(nom, lignes_de, colonnes_de, titre, perimetres=("tous",)):
    """Lit `sql/<nom>.sql`, écrit `sorties/<nom>.csv` et un graphique par périmètre.

    `lignes_de` et `colonnes_de` : (colonne du CSV, libellés, nom du total).
    La ligne de total totalise chaque colonne, la colonne de total chaque ligne.
    Graphique : `sorties/figures/<nom>.png` pour toutes les fiches,
    `<nom>_sans_enseignes.png` sans les chaînes.
    """
    colonne_ligne, libelles_lignes, total_lignes = lignes_de
    colonne_colonne, libelles_colonnes, total_colonnes = colonnes_de
    libelles_lignes = {**libelles_lignes, "total": total_lignes}
    libelles_colonnes = {**libelles_colonnes, "total": total_colonnes}
    d = client().query((DOSSIER / "sql" / f"{nom}.sql").read_text(encoding="utf-8")).to_dataframe()
    d["pour_1000"] = (1000 * d["suppressions"] / d["avis"]).round(1)
    SORTIES.mkdir(parents=True, exist_ok=True)
    d.to_csv(SORTIES / f"{nom}.csv", sep=";", decimal=",", index=False)
    print(f"  {SORTIES / f'{nom}.csv'}")

    for perimetre in perimetres:
        g = d[d["perimetre"] == perimetre].set_index([colonne_ligne, colonne_colonne])
        figure = nom if perimetre == "tous" else f"{nom}_{perimetre}"
        dessiner(g, figure, nom, libelles_lignes, libelles_colonnes, titre, PERIMETRES[perimetre])


def dessiner(g, figure, nom, libelles_lignes, libelles_colonnes, titre, perimetre):
    """Trace la grille `g` et l'écrit dans `sorties/figures/<figure>.png`."""
    couleurs = ListedColormap(BLEUS)
    norme = BoundaryNorm(TRANCHES, couleurs.N)
    lignes, colonnes = list(libelles_lignes), list(libelles_colonnes)

    fig, ax = plt.subplots(figsize=(10, 1.9 + 0.75 * len(lignes)), facecolor=FOND)
    ax.set_facecolor(FOND)
    for i, ligne in enumerate(lignes):
        for j, colonne in enumerate(colonnes):
            c = g.loc[(ligne, colonne)]
            taux = float(c["pour_1000"])
            if c["avis"] < MIN_AVIS:
                ax.add_patch(Rectangle((j, i), 1, 1, facecolor=FOND, edgecolor=HACHURE, hatch="///",
                                       linewidth=0))
                ax.add_patch(Rectangle((j, i), 1, 1, facecolor="none", edgecolor=FOND, linewidth=2))
                continue
            ax.add_patch(Rectangle((j, i), 1, 1, facecolor=couleurs(norme(taux)), edgecolor=FOND,
                                   linewidth=2))
            # Texte blanc sur les trois bleus les plus foncés.
            encre = "white" if norme(taux) >= 3 else ENCRE
            gras = "bold" if "total" in (ligne, colonne) else "normal"
            ax.text(j + 0.5, i + 0.5, f"{taux:.1f}".replace(".", ","), ha="center", va="center",
                    fontsize=13, fontweight=gras, color=encre)
    # Traits épais avant la ligne et la colonne de total.
    ax.axhline(len(lignes) - 1, color=FOND, linewidth=6)
    ax.axvline(len(colonnes) - 1, color=FOND, linewidth=6)
    ax.set_xlim(0, len(colonnes))
    ax.set_ylim(len(lignes), 0)
    ax.set_xticks(np.arange(len(colonnes)) + 0.5, [libelles_colonnes[n] for n in colonnes], fontsize=9.5)
    ax.set_yticks(np.arange(len(lignes)) + 0.5, [libelles_lignes[s] for s in lignes], fontsize=9.5)
    ax.xaxis.tick_top()
    ax.tick_params(length=0, colors=ENCRE)
    for cote in ax.spines.values():
        cote.set_visible(False)

    legende = [Patch(facecolor=b, edgecolor=b, label=n) for b, n in zip(BLEUS, NOMS_TRANCHES)]
    legende.append(Patch(facecolor=FOND, edgecolor=HACHURE, hatch="///", linewidth=0.5,
                         label=f"moins de {MIN_AVIS} avis"))
    fig.legend(handles=legende, loc="lower center", ncol=len(legende), frameon=False, fontsize=9,
               title="Suppressions pour 1 000 avis", title_fontsize=9)
    total = g.loc[("total", "total")]
    haut = fig.get_figheight()
    fig.suptitle(titre, x=0.02, ha="left", fontsize=13, color=ENCRE)
    fig.text(0.02, 1 - 0.7 / haut,
             f"{milliers(total['avis'])} avis publiés du 6 au 17 août 2026, suivis jusqu'au 24 août, "
             f"dont {milliers(total['suppressions'])} supprimés, {perimetre}.\n"
             "Dans chaque case : suppressions pour 1 000 avis. Avis, suppressions et fiches touchées "
             f"de chaque case dans sorties/{nom}.csv.",
             ha="left", va="top", fontsize=8.5, color=GRIS)
    fig.tight_layout(rect=(0, 0.75 / haut, 1, 1 - 1.3 / haut))
    (SORTIES / "figures").mkdir(exist_ok=True)
    fig.savefig(SORTIES / "figures" / f"{figure}.png", dpi=130, facecolor=FOND)
    plt.close(fig)
    print(f"  {SORTIES / 'figures' / f'{figure}.png'}")


grille("03D_grille_secteur_note",
       ("secteur", SECTEURS, "Total étoile"), ("note", NOTES, "Total secteur"),
       "Avis supprimés pour 1 000 avis publiés, par secteur et par note")
grille("03D_grille_reponse_note",
       ("reponse", REPONSES, "Total étoile"), ("note", NOTES, "Total réponse"),
       "Avis supprimés pour 1 000 avis publiés, par réponse du propriétaire et par note")
grille("03D_grille_reponse_secteur",
       ("secteur", SECTEURS, "Total réponse"),
       ("reponse", REPONSES, "Total secteur"),
       "Avis supprimés pour 1 000 avis publiés, par secteur et par réponse du propriétaire",
       perimetres=("tous", "sans_enseignes"))
