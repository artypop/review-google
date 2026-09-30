"""Fabrique la présentation `livrables/presentation-suppressions-avis-google.pptx`.

    uv run --with python-pptx python consolidation/presentation.py

Aucune requête, aucun calcul. Trois sources, nommées au pied de chaque diapositive :
  - les schémas à points lisent les CSV d'effets de `sorties/` (4a, 4b, 5, 8) ;
  - les autres chiffres sont recopiés des synthèses `.md` de `consolidation/` ;
  - les diapositives « rapport » reprennent les trois docx de `livrables/`.
Si un CSV change, les schémas suivent ; les chiffres recopiés se corrigent ici.

Le client ne lit pas « ×2 » : dans le texte, écrire « 2 fois plus ». Les graduations
des schémas gardent « ×2 ».
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

import commun

from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION, XL_LEGEND_POSITION
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

SORTIE = Path(__file__).resolve().parent.parent / "livrables" / "presentation-suppressions-avis-google.pptx"

# Les couleurs de `commun.py` : une par région, la même partout.
BLEU = RGBColor(0x2A, 0x78, 0xD6)       # US
ORANGE = RGBColor(0xEB, 0x68, 0x34)     # Europe
VERT = RGBColor(0x1B, 0xAF, 0x7A)       # ensemble
GRIS_SERIE = RGBColor(0xB9, 0xB8, 0xB3)  # « tous », à côté de « sans enseignes »
ENCRE = RGBColor(0x0B, 0x0B, 0x0B)
ENCRE_2 = RGBColor(0x52, 0x51, 0x4E)
FOND = RGBColor(0xFC, 0xFC, 0xFB)
FOND_CARTE = RGBColor(0xF1, 0xF0, 0xEC)
TRAIT = RGBColor(0xDD, 0xDC, 0xD7)
BLANC = RGBColor(0xFF, 0xFF, 0xFF)
POLICE = "Calibri"

LARGEUR, HAUTEUR = 13.333, 7.5
MARGE = 0.6

RAPPORT = "livrables/1. reviewflowz-resultats-propre.docx"
COMPLEMENTS = "livrables/2. analyses-complémentaires.docx"
JUMEAUX = "livrables/3. embeddings_further.docx"

prs = Presentation()
prs.slide_width, prs.slide_height = Inches(LARGEUR), Inches(HAUTEUR)
numero = 0


# ---------------------------------------------------------------- briques

def texte(diapo, x, y, l, h, lignes, taille=14, couleur=ENCRE, gras=False, puces=False,
          alignement=PP_ALIGN.LEFT, ancre=MSO_ANCHOR.TOP, espace=6):
    """Une zone de texte. `lignes` : une chaîne ou une liste ; un tuple (texte, True) met en gras."""
    zone = diapo.shapes.add_textbox(Inches(x), Inches(y), Inches(l), Inches(h))
    cadre = zone.text_frame
    cadre.word_wrap = True
    cadre.vertical_anchor = ancre
    cadre.margin_left = cadre.margin_right = cadre.margin_top = cadre.margin_bottom = 0
    if isinstance(lignes, str):
        lignes = [lignes]
    for i, ligne in enumerate(lignes):
        contenu, en_gras = ligne if isinstance(ligne, tuple) else (ligne, gras)
        p = cadre.paragraphs[0] if i == 0 else cadre.add_paragraph()
        p.alignment = alignement
        p.space_after = Pt(espace)
        r = p.add_run()
        r.text = ("•  " if puces else "") + contenu
        r.font.size, r.font.bold, r.font.name = Pt(taille), en_gras, POLICE
        r.font.color.rgb = couleur
    return zone


def rectangle(diapo, x, y, l, h, fond=FOND_CARTE, bord=None):
    forme = diapo.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(l), Inches(h))
    forme.fill.solid()
    forme.fill.fore_color.rgb = fond
    if bord is None:
        forme.line.fill.background()
    else:
        forme.line.color.rgb = bord
    forme.shadow.inherit = False
    return forme


def diapositive(titre, sous_titre=None, source=None):
    """Une diapositive vide avec son titre, son sous-titre et la source en pied."""
    global numero
    numero += 1
    diapo = prs.slides.add_slide(prs.slide_layouts[6])
    diapo.background.fill.solid()
    diapo.background.fill.fore_color.rgb = FOND
    rectangle(diapo, MARGE, 0.45, 0.09, 0.62, fond=VERT)
    texte(diapo, MARGE + 0.25, 0.4, LARGEUR - 2 * MARGE - 0.25, 0.75, titre, taille=24, gras=True,
          ancre=MSO_ANCHOR.MIDDLE)
    if sous_titre:
        texte(diapo, MARGE + 0.25, 1.2, LARGEUR - 2 * MARGE - 0.25, 0.55, sous_titre, taille=13,
              couleur=ENCRE_2)
    rectangle(diapo, MARGE, 6.88, LARGEUR - 2 * MARGE, 0.01, fond=TRAIT)
    if source:
        texte(diapo, MARGE, 6.97, LARGEUR - 2 * MARGE - 0.8, 0.35, "Source : " + source, taille=9,
              couleur=ENCRE_2)
    texte(diapo, LARGEUR - MARGE - 0.6, 6.97, 0.6, 0.35, str(numero), taille=9, couleur=ENCRE_2,
          alignement=PP_ALIGN.RIGHT)
    return diapo


def carte(diapo, x, y, l, h, gros, libelle, detail=None, couleur=ENCRE):
    """Un chiffre en grand, ce qu'il compte dessous, sa fourchette ou sa variante en petit."""
    rectangle(diapo, x, y, l, h)
    texte(diapo, x + 0.2, y + 0.15, l - 0.4, 0.7, gros, taille=30, gras=True, couleur=couleur)
    texte(diapo, x + 0.2, y + 0.9, l - 0.4, 0.75, libelle, taille=12)
    if detail:
        texte(diapo, x + 0.2, y + h - 0.5, l - 0.4, 0.4, detail, taille=10, couleur=ENCRE_2)


def barres(diapo, x, y, l, h, categories, series, titre=None, horizontal=False, decimales=0):
    """Des barres groupées. `series` : liste de (nom, valeurs, couleur)."""
    donnees = CategoryChartData()
    donnees.categories = categories
    for nom, valeurs, _ in series:
        donnees.add_series(nom, valeurs)
    type_graphique = XL_CHART_TYPE.BAR_CLUSTERED if horizontal else XL_CHART_TYPE.COLUMN_CLUSTERED
    graphique = diapo.shapes.add_chart(type_graphique, Inches(x), Inches(y), Inches(l), Inches(h),
                                       donnees).chart
    graphique.font.size, graphique.font.name = Pt(11), POLICE
    graphique.font.color.rgb = ENCRE_2
    graphique.has_title = titre is not None
    if titre:
        graphique.chart_title.text_frame.text = titre
        r = graphique.chart_title.text_frame.paragraphs[0].runs[0]
        r.font.size, r.font.bold = Pt(12), True
        r.font.color.rgb = ENCRE
    graphique.has_legend = len(series) > 1
    if graphique.has_legend:
        graphique.legend.position = XL_LEGEND_POSITION.BOTTOM
        graphique.legend.include_in_layout = False
    graphique.value_axis.visible = False
    graphique.value_axis.has_major_gridlines = False
    graphique.value_axis.minimum_scale = 0
    graphique.category_axis.format.line.color.rgb = TRAIT
    graphique.category_axis.has_major_gridlines = False
    if horizontal:
        graphique.category_axis.reverse_order = True  # la première catégorie en haut
    trace = graphique.plots[0]
    trace.gap_width, trace.overlap = 60, -10
    trace.has_data_labels = True
    trace.data_labels.number_format = "0." + "0" * decimales if decimales else "0"
    trace.data_labels.number_format_is_linked = False
    trace.data_labels.position = XL_LABEL_POSITION.OUTSIDE_END
    trace.data_labels.font.size = Pt(10)
    trace.data_labels.font.color.rgb = ENCRE
    for serie, (_, _, couleur) in zip(trace.series, series):
        serie.format.fill.solid()
        serie.format.fill.fore_color.rgb = couleur
    return graphique


def tableau(diapo, x, y, l, lignes, largeurs, hauteur_ligne=0.42, taille=12):
    """Un tableau sobre : en-tête sombre, lignes blanches. `largeurs` en parts de `l`."""
    forme = diapo.shapes.add_table(len(lignes), len(lignes[0]), Inches(x), Inches(y), Inches(l),
                                   Inches(hauteur_ligne * len(lignes)))
    table = forme.table
    total = sum(largeurs)
    for j, part in enumerate(largeurs):
        table.columns[j].width = Inches(l * part / total)
    for i, ligne in enumerate(lignes):
        table.rows[i].height = Inches(hauteur_ligne)
        for j, valeur in enumerate(ligne):
            cellule = table.cell(i, j)
            cellule.fill.solid()
            cellule.fill.fore_color.rgb = ENCRE if i == 0 else (BLANC if i % 2 else FOND_CARTE)
            cellule.vertical_anchor = MSO_ANCHOR.MIDDLE
            cellule.margin_left = cellule.margin_right = Inches(0.1)
            cellule.margin_top = cellule.margin_bottom = Inches(0.03)
            p = cellule.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.LEFT if j == 0 else PP_ALIGN.RIGHT
            r = p.add_run()
            r.text = valeur
            r.font.size, r.font.name, r.font.bold = Pt(taille), POLICE, i == 0
            r.font.color.rgb = BLANC if i == 0 else ENCRE
    return table



# ---------------------------------------------------------------- schémas à points

GRIS_POINT = "#b0afaa"
_effets = {}


def effet(csv, passage, colonne):
    """La ligne d'un CSV d'effets : (écart, bas, haut, citable), ou None si elle manque."""
    if csv not in _effets:
        _effets[csv] = pd.read_csv(commun.SORTIES / f"{csv}.csv", sep=";", decimal=",")
    df = _effets[csv]
    ligne = df[(df["passage"] == passage) & (df["colonne"] == colonne)]
    if ligne.empty or pd.isna(ligne.iloc[0]["risque_relatif"]):
        return None
    l = ligne.iloc[0]
    return l["risque_relatif"], l["fourchette_basse"], l["fourchette_haute"], l["citable"] == "oui"


def schema(nom, panneaux, lignes, largeur, hauteur, bornes=(0.1, 10), marge_gauche=0.4):
    """Un point et sa fourchette par ligne, un panneau par périmètre. Rend le chemin du PNG.

    `panneaux` : liste de titres. `lignes` : ("Titre de groupe", None) ou
    (libellé, [(csv, passage, colonne) ou None pour chaque panneau]).
    Vert : l'écart passe la règle de citation. Gris : il ne la passe pas.
    """
    fig, axes = plt.subplots(1, len(panneaux), sharey=True, figsize=(largeur, hauteur), squeeze=False)
    fig.patch.set_facecolor(commun.FOND)
    n = len(lignes)
    for ax, titre, k in zip(axes[0], panneaux, range(len(panneaux))):
        ax.set_facecolor(commun.FOND)
        ax.set_xscale("log")
        ax.set_xlim(*bornes)
        ax.axvline(1, color=commun.ENCRE, linewidth=1.1, zorder=1)
        for i, (_, sources) in enumerate(lignes):
            y = n - 1 - i
            if sources is None or sources[k] is None:
                continue
            e = effet(*sources[k])
            if e is None:
                ax.text(1, y, "trop peu de suppressions", ha="center", va="center", fontsize=7.5,
                        color=commun.ENCRE_SECONDAIRE, style="italic",
                        bbox=dict(facecolor=commun.FOND, edgecolor="none", pad=1.5))
                continue
            valeur, bas, haut, citable = e
            couleur = commun.COULEURS["ensemble"] if citable else GRIS_POINT
            ax.plot([max(bas, bornes[0]), min(haut, bornes[1])], [y, y], color="#8c8b87",
                    linewidth=1.6, zorder=2, solid_capstyle="round")
            ax.plot(valeur, y, "o", color=couleur, markersize=8, zorder=3)
        graduations = [g for g in (0.05, 0.1, 0.2, 0.5, 1, 2, 5, 10, 20) if bornes[0] < g < bornes[1]]
        ax.set_xticks(graduations)
        ax.set_xticklabels([f"×{g:g}".replace(".", ",") for g in graduations], fontsize=9)
        ax.minorticks_off()
        ax.grid(axis="x", color="#e4e3df", linewidth=0.8, zorder=0)
        ax.set_ylim(-0.7, n - 0.3)
        ax.set_title(titre, fontsize=10.5, color=commun.ENCRE, pad=6)
        ax.set_xlabel("◄ moins            plus ►", fontsize=8.5, color=commun.ENCRE_SECONDAIRE)
        ax.tick_params(axis="both", length=0, colors=commun.ENCRE_SECONDAIRE)
        for cote in ("top", "right", "left"):
            ax.spines[cote].set_visible(False)
        ax.spines["bottom"].set_color("#c9c8c3")
    gauche = axes[0][0]
    gauche.set_yticks([n - 1 - i for i in range(n)])
    etiquettes = gauche.set_yticklabels([libelle for libelle, _ in lignes], fontsize=9.5)
    for etiquette, (_, sources) in zip(etiquettes, lignes):
        if sources is None:
            etiquette.set_fontweight("bold")
            etiquette.set_fontsize(9)
            etiquette.set_color(commun.ENCRE)
    fig.subplots_adjust(left=marge_gauche, right=0.985, top=1 - 0.32 / hauteur,
                        bottom=0.62 / hauteur, wspace=0.1)
    chemin = commun.FIGURES / f"presentation_{nom}.png"
    fig.savefig(chemin, dpi=220, facecolor=commun.FOND)
    plt.close(fig)
    return chemin


def image(diapo, chemin, x, y, largeur):
    return diapo.shapes.add_picture(str(chemin), Inches(x), Inches(y), width=Inches(largeur))


LEGENDE = ("Point : l'écart mesuré. Trait : les valeurs compatibles avec les données. "
           "Vert : l'écart repose sur assez de suppressions et de fiches pour être cité. Gris : non.")

SANS, TOUS = "Sans les six enseignes", "Tous les avis"
PLUS_75, MOINS_75 = "fiche qui répond à plus de 75 %", "fiche qui répond à 75 % ou moins"


def deux(csv, colonne, base="ensemble"):
    """La même colonne dans les deux périmètres d'un CSV d'effets."""
    return [(csv, f"{base}, sans_enseignes", colonne), (csv, f"{base}, tous", colonne)]


# ---------------------------------------------------------------- titre

numero += 1
d = prs.slides.add_slide(prs.slide_layouts[6])
d.background.fill.solid()
d.background.fill.fore_color.rgb = FOND
rectangle(d, MARGE, 2.3, 0.12, 1.9, fond=VERT)
texte(d, MARGE + 0.4, 2.2, 11.5, 1.0, "Suppressions d'avis Google", taille=44, gras=True)
texte(d, MARGE + 0.4, 3.2, 11.5, 1.1,
      "Quelles caractéristiques d'un avis vont avec sa suppression : la note, l'auteur, "
      "le secteur, l'âge de l'avis, le texte, la réponse du propriétaire", taille=20, couleur=ENCRE_2)
texte(d, MARGE + 0.4, 5.6, 11.5, 0.8,
      ["ReviewFlowz — étude pour Axel", "Chiffres des 29 et 30 septembre 2026"],
      taille=14, couleur=ENCRE_2)

# ---------------------------------------------------------------- l'essentiel

d = diapositive("Les résultats en huit points",
                "Chaque chiffre est donné sans les six enseignes signalées ; la version avec "
                "enseignes figure dans les diapositives de détail.",
                "synthèses de consolidation/, points 1 à 8 ; rapports de livrables/")
points = [
    ("Volume", "Sur 10 000 avis en ligne, 6,6 disparaissent pendant les 14 jours de suivi."),
    ("Concentration", "20 fiches portent 29 % des suppressions d'avis publiés du 4 au 24 août "
                      "et détiennent 2,3 % de ces avis."),
    ("Âge", "Sur 10 000 avis publiés en 2026, 42,9 disparaissent ; sur 10 000 avis de 2025, 5,1. "
            "Le 7e jour de l'avis est le plus risqué."),
    ("Note", "Dans une même fiche, un avis 1 étoile disparaît 5 fois plus qu'un avis 5 étoiles."),
    ("Auteur", "Un compte sans niveau Local Guide perd 1,6 fois plus d'avis. Un auteur à plus de "
               "20 photos en perd 2,4 fois moins."),
    ("Secteur", "Une fiche de services à domicile a 2 fois plus de chances de perdre un avis "
                "qu'une fiche automobile."),
    ("Texte", "Un avis recopié d'un autre est supprimé une fois sur deux. La longueur du texte "
              "et la photo jointe ne changent rien dans une même fiche."),
    ("Réponse", "Sur les fiches qui répondent à presque tout, l'avis répondu disparaît 3 à 5 fois "
                "moins. Les données ne disent pas si la réponse protège l'avis."),
]
for i, (mot, phrase) in enumerate(points):
    x = MARGE + (i % 2) * 6.15
    y = 1.85 + (i // 2) * 1.24
    rectangle(d, x, y, 5.95, 1.12)
    texte(d, x + 0.2, y + 0.1, 5.5, 0.3, mot, taille=12, gras=True, couleur=VERT)
    texte(d, x + 0.2, y + 0.42, 5.55, 0.68, phrase, taille=13)

# ---------------------------------------------------------------- le corpus

d = diapositive("Le corpus : 4,88 millions d'avis relevés chaque jour pendant 14 jours",
                "Un robot a relevé tous les avis de chaque fiche une fois par jour, du 11 au 24 août 2026.",
                "1a_tables.csv, 1b_entonnoir.csv — uv run python consolidation/1a_tables.py, 1b_entonnoir.py")
for i, (gros, libelle, detail) in enumerate([
    ("9 048", "fiches Google Maps", "41 pays, 7 secteurs, 3 tailles d'entreprise"),
    ("4 876 933", "avis dans la base complète", "2 627 609 aux États-Unis, 2 249 324 en Europe"),
    ("4 590", "avis disparus pendant le suivi", "constatés du 12 au 24 août"),
    ("35 751", "avis publiés du 4 au 17 août", "le panel : 1 355 disparus"),
]):
    carte(d, MARGE + i * 3.08, 1.85, 2.9, 1.95, gros, libelle, detail)
tableau(d, MARGE, 4.05, 7.3, [
    ["De l'export à la base", "Avis", "Avis supprimés"],
    ["Export brut, une ligne par avis", "4 877 534", "4 697"],
    ["Sans les avis disparus puis revenus : la base complète", "4 876 933", "4 590"],
    ["Publiés du 4 au 17 août : le panel", "35 751", "1 355"],
], [5, 1.6, 1.8], hauteur_ligne=0.4, taille=11)
texte(d, 8.3, 4.05, 4.4, 2.6, [
    ("Deux populations", True),
    "La base complète décrit les avis supprimés, quelle que soit leur date de publication.",
    "Le panel compare des avis supprimés à des avis conservés publiés la même période.",
    "Une suppression : le robot ne retrouve plus l'avis à un passage.",
], taille=12)

# ---------------------------------------------------------------- peu de suppressions

d = diapositive("Sur 10 000 avis en ligne, 9,4 disparaissent en 14 jours",
                "Base complète. Suppressions pour 10 000 avis, par année de publication de l'avis.",
                "2_1a_par_annee.csv, 1c_suppressions_secteur_region.csv — "
                "uv run python consolidation/2_1_peu_de_suppressions.py")
barres(d, MARGE, 1.8, 6.9, 4.9, ["2026", "2025", "2024", "2023"], [
    ("Tous les avis", [63.0, 7.2, 5.8, 3.7], GRIS_SERIE),
    ("Sans les six enseignes", [42.9, 5.1, 3.8, 3.0], VERT),
], decimales=1)
texte(d, 7.9, 1.9, 4.8, 4.7, [
    "4 590 avis disparus sur 4 876 933 : 9,4 pour 10 000.",
    "Sans les six enseignes : 3 067 sur 4 627 581, soit 6,6 pour 10 000.",
    "États-Unis : 12,4 pour 10 000 (8,6 sans enseignes). Europe : 5,9 (4,5 sans enseignes).",
    "3 067 des 4 590 suppressions portent sur des avis publiés en 2026, soit 67 % "
    "(1 968 sur 3 067 sans enseignes).",
    "Avis publiés de 2016 à 2022 : de 1,2 à 2,5 suppressions pour 10 000.",
    "Avis publiés avant 2014 : aucune suppression.",
], taille=14, puces=True, espace=10)

# ---------------------------------------------------------------- l'âge de l'avis

d = diapositive("Après le 8e jour, le rythme des suppressions est divisé par 3",
                "Avis publiés du 12 juillet au 24 août 2026 : 107 644 avis, 2 467 supprimés. "
                "Suppressions par jour pour 10 000 avis en ligne, selon l'âge de l'avis.",
                "2_1b_resume.csv, 2_1b_par_age.csv — uv run python consolidation/2_1_peu_de_suppressions.py")
barres(d, MARGE, 1.9, 6.9, 4.8, ["1 à 8 jours", "le 7e jour seul", "9 jours et plus", "le 30e jour seul"], [
    ("Tous les avis", [48.5, 136.6, 14.5, 3.7], GRIS_SERIE),
    ("Sans les six enseignes", [35.1, 84.3, 8.3, 3.9], VERT),
], decimales=1)
texte(d, 7.9, 1.95, 4.8, 2.3, [
    "Le rythme quotidien est divisé par 3,3 après le 8e jour (par 4,2 sans enseignes).",
    "Le 7e jour de l'avis compte le plus de disparitions.",
    "Sans enseignes, sur 10 000 avis, 285 disparaissent pendant les 8 premiers jours, "
    "puis 210 du 9e au 30e jour.",
], taille=14, puces=True, espace=10)
tableau(d, 7.9, 4.55, 4.8, [
    ["Encore en ligne sur 10 000", "Tous", "Sans enseignes"],
    ["au 8e jour", "9 623", "9 715"],
    ["au 15e jour", "9 395", "9 605"],
    ["au 30e jour", "9 250", "9 505"],
    ["au 43e jour", "9 213", "9 470"],
], [2.6, 1, 1.5], hauteur_ligne=0.38, taille=11)

# ---------------------------------------------------------------- concentration (rapports)

d = diapositive("Les suppressions se concentrent sur quelques fiches",
                "Avis publiés du 4 au 24 août 2026, sans les six enseignes. Les N fiches les plus "
                "touchées : leur part des suppressions, et leur part des avis, en %.",
                f"{COMPLEMENTS}, chapitre 2 ; {RAPPORT}, chapitre 2")
barres(d, MARGE, 1.9, 7.3, 4.8, ["1 fiche", "5", "10", "20", "50", "100", "200"], [
    ("Part des suppressions", [3.7, 11.4, 18.8, 29.1, 50.6, 69.8, 82.9], VERT),
    ("Part des avis de ces fiches", [0.2, 0.9, 1.5, 2.3, 4.5, 8.4, 17.2], GRIS_SERIE),
], decimales=1)
texte(d, 8.3, 1.95, 4.4, 4.7, [
    "50 923 avis publiés du 4 au 24 août sur 6 176 fiches ; 1 485 suppressions sur 422 fiches.",
    "Sans enseignes, 16 fiches portent le quart des suppressions, 49 la moitié, 126 les trois "
    "quarts. Avec les enseignes : 17, 54 et 122.",
    "Les 20 fiches les plus touchées portent 29,1 % des suppressions et détiennent 2,3 % des "
    "avis. Avec les enseignes : 28,1 % et 3,3 %.",
    "Sur toute la base, le rapport compte 7 682 fiches sur 8 997 sans aucune suppression, "
    "soit 85,4 %.",
], taille=13, puces=True, espace=10)

# ---------------------------------------------------------------- les six enseignes

d = diapositive("Six enseignes portent 26 % et 7 % des suppressions de la base",
                "Base complète, suppressions constatées du 12 au 24 août 2026.",
                "2_2_resume.csv, 2_2_par_jour.csv, 2_2b_delai.csv — "
                "uv run python consolidation/2_2_deux_phenomenes.py")
for x, couleur, titre, lignes in [
    (MARGE, BLEU, "4 chaînes antiparasitaires américaines", [
        "93 fiches, 247 938 avis, 1 194 supprimés.",
        "5,1 % des avis de la base, 26 % de ses suppressions.",
        "1 143 des 1 194 avis supprimés portent 5 étoiles (96 %).",
        "290 sont supprimés 6 ou 7 jours après leur publication.",
        "405 avis publiés avant le 4 août sont supprimés en deux jours, les 12 et 17 août.",
        "EcoShield, Insight, Pointe, Bulwark.",
    ]),
    (MARGE + 6.15, ORANGE, "2 salles de sport espagnoles", [
        "2 fiches, 1 414 avis, 329 supprimés : 23 % de leurs avis.",
        "0,03 % des avis de la base, 7 % de ses suppressions.",
        "317 des 329 avis supprimés portent 1 étoile.",
        "295 ont été publiés en deux jours, les 1er et 2 août.",
        "Suppressions en trois vagues : 12 août, 16 août, 22 et 23 août.",
        "Aucune suppression avant le 9e jour de l'avis.",
    ]),
]:
    rectangle(d, x, 1.85, 5.95, 4.1)
    rectangle(d, x, 1.85, 5.95, 0.08, fond=couleur)
    texte(d, x + 0.25, 2.1, 5.5, 0.45, titre, taille=17, gras=True)
    texte(d, x + 0.25, 2.7, 5.5, 3.2, lignes, taille=13, puces=True, espace=7)
texte(d, MARGE, 6.15, LARGEUR - 2 * MARGE, 0.6,
      "Ces 95 fiches sont retirées dans la version « sans enseignes » de chaque résultat. "
      "Les données ne disent pas qui a demandé ces suppressions.", taille=13, couleur=ENCRE_2)

# ---------------------------------------------------------------- avis revenus (rapport)

d = diapositive("Des avis disparaissent puis reviennent, surtout dès le lendemain",
                "Avis disparus à un passage du robot puis revus ensuite. Avis revenus pour un million "
                "d'avis du secteur.",
                f"{RAPPORT}, chapitre 1 ; 1b_entonnoir.csv")
barres(d, MARGE, 1.9, 6.9, 4.8,
       ["Automobile", "Services à domicile", "Santé", "Sport et bien-être", "Restauration", "Voyage",
        "Hôtellerie"], [("Avis revenus pour un million d'avis", [199, 166, 159, 141, 77, 64, 46], VERT)],
       horizontal=True)
tableau(d, 7.9, 1.95, 4.8, [
    ["Secteur", "Avis revenus", "dont dès le lendemain"],
    ["Automobile", "130", "101"],
    ["Services à domicile", "126", "89"],
    ["Restauration", "91", "63"],
    ["Santé", "89", "62"],
    ["Sport et bien-être", "72", "54"],
    ["Hôtellerie", "46", "29"],
    ["Voyage", "14", "7"],
], [2.2, 1.2, 1.7], hauteur_ligne=0.38, taille=11)
texte(d, 7.9, 5.2, 4.8, 1.5, [
    "Un avis revenu ne compte pas comme une suppression : la base écarte les 601 avis qui ont "
    "disparu puis sont revenus.",
    "Le rapport ne donne pas ce décompte sans les six enseignes.",
], taille=12, puces=True, espace=8)

# ---------------------------------------------------------------- le secteur

d = diapositive("Les services à domicile américains sont le secteur le plus touché",
                "Base complète, sans les six enseignes. Suppressions pour 10 000 avis en 14 jours.",
                "1c_suppressions_secteur_region.csv — uv run python consolidation/1c_secteurs.py")
barres(d, MARGE, 1.8, 7.2, 4.95,
       ["Services à domicile", "Sport et bien-être", "Santé", "Voyage", "Automobile", "Restauration",
        "Hôtellerie"], [
           ("États-Unis", [24.7, 10.4, 11.7, 9.4, 6.8, 3.3, 3.2], BLEU),
           ("Europe", [4.0, 6.5, 5.0, 10.7, 4.2, 3.4, 3.6], ORANGE),
       ], horizontal=True, decimales=1)
texte(d, 8.2, 1.95, 4.5, 4.7, [
    "Services à domicile aux États-Unis : 24,7 suppressions pour 10 000 avis, 35,3 avec les "
    "4 chaînes antiparasitaires.",
    "Sport et bien-être en Europe : 6,5, et 16,8 avec les 2 salles espagnoles.",
    "Hôtellerie et restauration : environ 3 pour 10 000 des deux côtés.",
    "Ces taux directs comptent aussi la taille des fiches et leur pays. La diapositive "
    "suivante compare des fiches égales par ailleurs.",
], taille=13, puces=True, espace=10)

# ---------------------------------------------------------------- quelle fiche (4a)

d = diapositive("Quelle fiche perd au moins un avis",
                "Panel : 1 890 fiches avec au moins 5 avis publiés du 4 au 17 août, dont 262 perdent un "
                "avis (1 813 et 214 sans enseignes). Chaque ligne compare des fiches égales par ailleurs.",
                "4a_effets.csv — uv run python consolidation/4a_quelle_fiche.py")
fiche = lambda c: deux("4a_effets", c)
chemin = schema("4a", [SANS, TOUS], [
    ("Secteur, face à l'automobile", None),
    ("services à domicile", fiche("secteur : Services à domicile")),
    ("sport et bien-être", fiche("secteur : Sport et bien-être")),
    ("santé", fiche("secteur : Santé")),
    ("hôtellerie", fiche("secteur : Hôtellerie")),
    ("restauration", fiche("secteur : Restauration")),
    ("voyage", fiche("secteur : Voyage")),
    ("Taille, face à 1 établissement", None),
    ("4 à 10 établissements", fiche("taille : small")),
    ("20 à 50 établissements", fiche("taille : large")),
    ("Région, face à l'Europe", None),
    ("États-Unis", fiche("region : US")),
    ("Habitude, face à 75 % d'avis répondus ou moins", None),
    ("répond à plus de 75 % de ses avis", fiche("habitude : plus de 75 %")),
    ("Avis reçus en 14 jours, face au rythme habituel", None),
    ("1 à 2 fois le rythme habituel", fiche("afflux : 1 à 2 fois l'habitude")),
    ("plus de 2 fois le rythme habituel", fiche("afflux : plus de 2 fois l'habitude")),
], 8.1, 4.6, bornes=(0.2, 6), marge_gauche=0.44)
image(d, chemin, MARGE, 1.78, 8.1)
texte(d, MARGE, 6.43, 8.1, 0.4, LEGENDE, taille=9, couleur=ENCRE_2)
texte(d, 9.0, 1.9, 3.7, 4.8, [
    "Une fiche de services à domicile a 2 fois plus de chances de perdre un avis qu'une fiche "
    "automobile. Avec les enseignes : 3 fois plus.",
    "Une fiche qui reçoit 1 à 2 fois son rythme habituel d'avis a 1,9 fois plus de chances "
    "d'en perdre un (sans enseignes).",
    "États-Unis : 1,4 fois plus avec les enseignes. Sans elles, le trait traverse ×1.",
    "Taille, habitude de réponse, santé, hôtellerie, sport : les traits traversent ×1, les "
    "données ne tranchent pas.",
    "Restauration et voyage, en gris : une seule fiche porte le quart ou plus de leurs suppressions.",
], taille=12, puces=True, espace=8)

# ---------------------------------------------------------------- la note

d = diapositive("L'avis 1 étoile est le plus supprimé, aux États-Unis comme en Europe",
                "Panel : avis publiés du 4 au 17 août 2026. Suppressions pour 10 000 avis, par note.",
                "2_3_note.csv, 4b_effets.csv — uv run python consolidation/2_3_taux.py, 4b_quel_avis.py")
notes = ["1 étoile", "2 étoiles", "3 étoiles", "4 étoiles", "5 étoiles"]
barres(d, MARGE, 1.8, 4.1, 4.9, notes, [
    ("Tous", [842, 444, 164, 288, 529], GRIS_SERIE),
    ("Sans enseignes", [807, 421, 142, 166, 320], BLEU),
], titre="États-Unis")
barres(d, MARGE + 4.15, 1.8, 4.1, 4.9, notes, [
    ("Tous", [631, 324, 72, 88, 163], GRIS_SERIE),
    ("Sans enseignes", [514, 207, 72, 88, 163], ORANGE),
], titre="Europe")
texte(d, 9.2, 1.9, 3.5, 4.8, [
    ("Dans la même fiche, le même jour, face à un avis 5 étoiles", True),
    "L'avis 1 étoile disparaît 5 fois plus (3,5 fois plus avec les enseignes).",
    "L'avis 2 étoiles disparaît 2,8 fois plus (2,1 fois plus avec les enseignes).",
    "L'avis 4 étoiles disparaît 1,8 fois moins, avec et sans les enseignes.",
    ("États-Unis", True),
    "L'avis 5 étoiles disparaît plus que l'avis 3 ou 4 étoiles, avec ou sans les chaînes.",
], taille=13, espace=9)

# ---------------------------------------------------------------- quel avis (4b)

d = diapositive("Quel avis tombe, dans une même fiche, le même jour",
                "Panel : 6 350 avis de 314 fiches, 1 314 suppressions (4 888 avis et 841 suppressions sans "
                "enseignes). Les avis comparés partagent la fiche, son secteur et son pays.",
                "4b_effets.csv — nice -n 19 uv run python consolidation/4b_quel_avis.py")
avis = lambda c: deux("4b_effets", c)
chemin = schema("4b", [SANS, TOUS], [
    ("Note, face à 5 étoiles", None),
    ("1 étoile", avis("note : 1 étoile(s)")),
    ("2 étoiles", avis("note : 2 étoile(s)")),
    ("3 étoiles", avis("note : 3 étoile(s)")),
    ("4 étoiles", avis("note : 4 étoile(s)")),
    ("Auteur, face au niveau Local Guide 1 à 4", None),
    ("sans niveau Local Guide", avis("local_guide : sans niveau")),
    ("niveau 5 et plus", avis("local_guide : niveau 5 et plus")),
    ("Auteur, face à aucune photo sur son profil", None),
    ("1 à 20 photos", avis("photos_auteur : 1 à 20 photos")),
    ("plus de 20 photos", avis("photos_auteur : plus de 20 photos")),
    ("Auteur, face à 1 avis déclaré", None),
    ("2 à 20 avis", avis("avis_auteur : 2 à 20 avis")),
    ("plus de 20 avis", avis("avis_auteur : plus de 20 avis")),
    ("Réponse déjà là, face à pas de réponse", None),
    ("fiche qui répond à plus de 75 %", avis(f"reponse : réponse déjà là, {PLUS_75}")),
    ("fiche qui répond à 75 % ou moins", avis(f"reponse : réponse déjà là, {MOINS_75}")),
], 8.1, 4.6, bornes=(0.1, 10), marge_gauche=0.4)
image(d, chemin, MARGE, 1.78, 8.1)
texte(d, MARGE, 6.43, 8.1, 0.4, LEGENDE, taille=9, couleur=ENCRE_2)
texte(d, 9.0, 1.9, 3.7, 4.8, [
    "L'avis 1 étoile tombe 5 fois plus que l'avis 5 étoiles ; l'avis 4 étoiles, 1,8 fois moins.",
    "L'avis d'un compte sans niveau Local Guide tombe 1,6 fois plus.",
    "L'avis d'un auteur à plus de 20 photos tombe 2,4 fois moins.",
    "Sur une fiche qui répond à plus de 75 % de ses avis, l'avis déjà répondu tombe 5 fois "
    "moins, avec et sans les enseignes.",
    "3 étoiles sans enseignes, en gris : 9 suppressions.",
    "Fiche qui répond à 75 % ou moins, sans enseignes, en gris : une fiche porte 35 % des "
    "suppressions.",
], taille=12, puces=True, espace=8)

# ---------------------------------------------------------------- l'auteur

d = diapositive("Auteur sans niveau Local Guide ou sans photo : l'avis disparaît plus",
                "Panel, sans les six enseignes. Suppressions pour 10 000 avis, selon le profil de l'auteur.",
                "2_3_local_guide.csv, 2_3_photos_auteur.csv, 4b_effets.csv — "
                "uv run python consolidation/2_3_taux.py, 4b_quel_avis.py")
barres(d, MARGE, 1.8, 3.9, 4.9, ["sans niveau", "niveau 1 à 4", "niveau 5 et plus"], [
    ("États-Unis", [634, 350, 139], BLEU),
    ("Europe", [551, 177, 93], ORANGE),
], titre="Niveau Local Guide de l'auteur")
barres(d, MARGE + 3.95, 1.8, 4.6, 4.9, ["0", "1 à 5", "6 à 20", "21 à 100", "plus de 100"], [
    ("États-Unis", [397, 304, 272, 68, 72], BLEU),
    ("Europe", [211, 212, 125, 83, 69], ORANGE),
], titre="Photos publiées par l'auteur sur son profil")
texte(d, 9.4, 1.9, 3.3, 4.8, [
    ("Avec les enseignes, pour 10 000 avis", True),
    "Sans niveau : 777 aux États-Unis, 601 en Europe. Niveau 5 et plus : 198 et 97.",
    "Aucune photo : 611 et 233. Plus de 100 photos : 98 et 69.",
    ("Dans la même fiche, le même jour", True),
    "Sans niveau Local Guide : 1,6 fois plus qu'au niveau 1 à 4 (1,5 avec les enseignes).",
    "Plus de 20 photos : 2,4 fois moins qu'un auteur sans photo, avec et sans les enseignes.",
    "2 à 20 avis déclarés : 1,3 fois moins qu'un auteur à 1 avis, sans enseignes.",
], taille=12, espace=8)

# ---------------------------------------------------------------- photo jointe, longueur du texte

d = diapositive("Photo jointe et longueur du texte : aucun écart dans une même fiche",
                "À gauche, panel du 4 au 17 août : suppressions pour 10 000 avis, tous / sans enseignes. "
                "À droite, les avis d'une même fiche comparés le même jour.",
                "2_3_photo_jointe.csv, 2_3_texte.csv, 2_3_longueur_texte.csv, 4b_effets.csv, 8_effets.csv")
tableau(d, MARGE, 1.9, 5.6, [
    ["Pour 10 000 avis (tous / sans enseignes)", "États-Unis", "Europe"],
    ["avec photo jointe", "280 / 265", "186 / 186"],
    ["sans photo jointe", "547 / 346", "194 / 178"],
    ["avec texte", "514 / 348", "216 / 211"],
    ["sans texte", "568 / 311", "140 / 106"],
    ["texte de 1 à 50 caractères", "517 / 329", "185 / 175"],
    ["texte de 51 à 200 caractères", "502 / 317", "204 / 197"],
    ["texte de plus de 200 caractères", "531 / 403", "240 / 238"],
], [3.2, 1.2, 1.2], hauteur_ligne=0.4, taille=11)
texte(d, MARGE, 5.3, 5.6, 1.5, [
    "Dans une même fiche, tous les traits traversent ×1.",
    "Sur les avis publiés avant le 4 août, sans enseignes, un avis avec texte disparaît "
    "1,3 à 1,4 fois plus qu'un avis sans texte. Avec les enseignes, les données ne "
    "tranchent pas.",
], taille=11, puces=True, espace=6)
egal = lambda c: deux("4b_effets", c)
chemin = schema("photo_texte", [SANS, TOUS], [
    ("Face à l'avis sans photo", None),
    ("avec photo jointe", egal("photo_jointe : avec photo")),
    ("Face à l'avis sans texte", None),
    ("texte de 1 à 50 caractères", egal("texte : 1 à 50 caractères")),
    ("texte de 51 à 200 caractères", egal("texte : 51 à 200 caractères")),
    ("texte de plus de 200 caractères", egal("texte : plus de 200 caractères")),
], 6.2, 3.6, bornes=(0.4, 2.5), marge_gauche=0.42)
image(d, chemin, 6.5, 1.85, 6.2)
texte(d, 6.5, 5.6, 6.2, 0.6, LEGENDE, taille=9, couleur=ENCRE_2)

# ---------------------------------------------------------------- le sujet du texte (rapports)

d = diapositive("Le sujet du texte suit le secteur de la fiche",
                "Avis américains en anglais du panel, sans les six enseignes, rangés en groupes de textes "
                "proches. Suppressions constatées, et suppressions attendues d'après le secteur de chaque avis.",
                f"{COMPLEMENTS}, chapitre 5")
barres(d, MARGE, 1.95, 7.6, 4.8, [
    "1 étoile : voiture, location, garantie", "1 étoile : restaurant et hôtel",
    "1 étoile : plaintes courtes", "1 étoile : soins vétérinaires et médicaux",
    "5 étoiles : récit détaillé d'une prestation", "5 étoiles : éloge court du service",
    "5 étoiles : éloge très court", "5 étoiles : loisirs, restaurants, séjours"], [
    ("Suppressions constatées", [41, 16, 13, 13, 139, 105, 58, 47], VERT),
    ("Attendues d'après le secteur", [37, 19, 13, 14, 144, 99, 48, 58], GRIS_SERIE),
], horizontal=True)
texte(d, 8.6, 2.0, 4.1, 4.7, [
    "950 avis 1 étoile, dont 83 supprimés ; 11 019 avis 5 étoiles, dont 349 supprimés.",
    "Chaque groupe compte à peu près les suppressions attendues d'après ses secteurs.",
    "Part supprimée en 1 étoile : de 5,9 % (restaurant et hôtel) à 11,2 % (voiture). "
    "En 5 étoiles : de 1,9 % (loisirs, séjours) à 3,8 % (récit détaillé).",
    "Avec les enseignes, le groupe « récit détaillé » en 5 étoiles compte 281 suppressions "
    "pour 298 attendues.",
    "En 1 étoile, trois groupes sur quatre reposent sur 13 à 16 suppressions, dont jusqu'à "
    "38 % sur une seule fiche.",
], taille=12, puces=True, espace=8)

# ---------------------------------------------------------------- les copies (rapports)

d = diapositive("Un avis recopié d'un autre est supprimé une fois sur deux",
                "Panel : 26 168 avis avec texte. Chaque texte d'au moins 80 caractères est comparé au texte "
                "le plus proche parmi les autres. Part des avis supprimés, en %.",
                f"{JUMEAUX}, chapitre 1")
barres(d, MARGE, 1.95, 6.6, 4.8, ["Copie", "Quasi-copie", "Même sujet", "Aucun texte proche"], [
    ("Tous les avis", [61.9, 20.9, 4.2, 3.6], GRIS_SERIE),
    ("Sans les six enseignes", [50.0, 19.5, 3.6, 2.7], VERT),
], decimales=1)
texte(d, 7.6, 2.0, 5.1, 4.7, [
    "Sans enseignes : 21 copies supprimées sur 42, 16 quasi-copies sur 82, et 403 avis sur "
    "14 927 sans texte proche.",
    "Comparée aux autres avis de sa fiche, une copie est supprimée 6 fois plus et une "
    "quasi-copie 3,4 fois plus. Sans enseignes : 13 fois et 3,2 fois, sur 17 et 15 suppressions.",
    "Deux avis différents sur le même sujet : aucun écart avec le reste de la fiche.",
    "Sur 68 paires de textes jumeaux sans enseignes, 12 perdent les deux avis, 11 le second "
    "publié seul, 5 le premier seul.",
    "Volume : 149 copies et quasi-copies sur 26 168 avis, pour 57 suppressions.",
], taille=12, puces=True, espace=8)

# ---------------------------------------------------------------- le prénom (rapport)

d = diapositive("Citer un prénom dans un avis 5 étoiles va avec plus de suppressions",
                "Panel. Suppressions pour 10 000 avis, selon que le texte cite ou non un prénom, à note égale.",
                f"{RAPPORT}, chapitre 8")
barres(d, MARGE, 1.9, 6.9, 4.8, ["5 étoiles, sans enseignes", "1 étoile, sans enseignes",
                                 "5 étoiles, tous les avis"], [
    ("Sans prénom", [272, 807, 422], GRIS_SERIE),
    ("Avec prénom", [387, 766, 611], VERT),
])
texte(d, 7.9, 1.95, 4.8, 4.7, [
    "5 étoiles, sans enseignes : 154 avis supprimés sur 3 976 avec prénom, 219 sur 8 066 sans "
    "prénom. L'avis avec prénom disparaît 1,4 fois plus.",
    "1 étoile, sans enseignes : 16 sur 209 avec prénom, 73 sur 905 sans. Aucun écart.",
    "5 étoiles, avec les enseignes : 287 sur 4 694 avec prénom, 381 sur 9 024 sans. "
    "1,4 fois plus.",
    "Ce sont des taux directs à note égale. Le secteur et la fiche ne sont pas tenus égaux, "
    "et aucune fourchette n'est calculée.",
], taille=13, puces=True, espace=10)

# ---------------------------------------------------------------- la réponse, fiches > 75 %

d = diapositive("Fiches qui répondent à presque tout : l'avis répondu disparaît moins",
                "Fiches dont plus de 75 % des avis de l'année précédente ont une réponse. "
                "Avis répondu comparé à l'avis sans réponse du même âge.",
                "5_effets.csv, 4b_effets.csv, 8_effets.csv — uv run python consolidation/"
                "5_reponse_jour_par_jour.py, 4b_quel_avis.py, 8_regression_reponse_base.py")
jour = lambda base, quand, h: deux("5_effets", f"réponse {quand}, {h}", base)
age = lambda tranche, h: deux("8_effets", f"réponse : avis {tranche}, {h}")
chemin = schema("reponse_plus_75", [SANS, TOUS], [
    ("Avis du 4 au 17 août, 1 à 10 établissements", None),
    ("réponse le jour même", jour("mono + small", "jour même", PLUS_75)),
    ("réponse le lendemain", jour("mono + small", "1 jour", PLUS_75)),
    ("réponse à 2 jours", jour("mono + small", "2 jours", PLUS_75)),
    ("Avis du 4 au 17 août, 20 à 50 établissements", None),
    ("réponse le jour même", jour("large", "jour même", PLUS_75)),
    ("réponse le lendemain", jour("large", "1 jour", PLUS_75)),
    ("réponse à 2 jours", jour("large", "2 jours", PLUS_75)),
    ("Même fiche, même jour", None),
    ("réponse déjà là", deux("4b_effets", f"reponse : réponse déjà là, {PLUS_75}")),
    ("Avis publiés avant le 4 août", None),
    ("avis de 8 à 30 jours", age("de 8 à 30 jours", PLUS_75)),
    ("avis de 31 à 90 jours", age("de 31 à 90 jours", PLUS_75)),
    ("avis de 91 jours à un an", age("de 91 à 365 jours", PLUS_75)),
    ("avis de plus d'un an", age("de plus d'un an", PLUS_75)),
], 8.1, 4.6, bornes=(0.07, 3), marge_gauche=0.43)
image(d, chemin, MARGE, 1.78, 8.1)
texte(d, MARGE, 6.43, 8.1, 0.4, LEGENDE, taille=9, couleur=ENCRE_2)
texte(d, 9.0, 1.9, 3.7, 4.8, [
    "Avis répondu le jour même ou le lendemain : il disparaît 3 fois moins sur les entreprises "
    "de 1 à 10 établissements, 4 fois moins sur celles de 20 à 50 (sans enseignes).",
    "Dans la même fiche, le même jour : 5 fois moins, avec et sans les enseignes.",
    "Avis de 91 jours à un an : 4 fois moins (3,6 fois moins avec les enseignes).",
    "Avis de 8 à 30 jours et de plus d'un an : le trait traverse ×1. Avec les enseignes, "
    "l'avis répondu de plus d'un an disparaît 1,4 fois plus.",
    "Avec les enseignes, réponse le jour même sur 20 à 50 établissements : le trait traverse ×1. "
    "Les 4 chaînes répondent le jour même et perdent beaucoup d'avis.",
    "31 à 90 jours, en gris : une fiche porte 6 des 18 suppressions d'avis sans réponse "
    "(cid 13197914448513377771).",
], taille=11, puces=True, espace=7)

# ---------------------------------------------------------------- la réponse, fiches <= 75 %

d = diapositive("Fiches qui répondent moins : aucune protection visible",
                "Fiches dont 75 % ou moins des avis de l'année précédente ont une réponse. "
                "Avis répondu comparé à l'avis sans réponse du même âge.",
                "8_effets.csv, 5_effets.csv, 5_fiches_par_case.csv, 4b_effets.csv — uv run python "
                "consolidation/8_regression_reponse_base.py, 5_reponse_jour_par_jour.py")
chemin = schema("reponse_moins_75", [SANS, TOUS], [
    ("Avis du 4 au 17 août, 1 à 10 établissements", None),
    ("réponse le jour même", jour("mono + small", "jour même", MOINS_75)),
    ("réponse le lendemain", jour("mono + small", "1 jour", MOINS_75)),
    ("Avis du 4 au 17 août, 20 à 50 établissements", None),
    ("réponse le jour même", jour("large", "jour même", MOINS_75)),
    ("réponse le lendemain", jour("large", "1 jour", MOINS_75)),
    ("Même fiche, même jour", None),
    ("réponse déjà là", deux("4b_effets", f"reponse : réponse déjà là, {MOINS_75}")),
    ("Avis publiés avant le 4 août", None),
    ("avis de 8 à 30 jours", age("de 8 à 30 jours", MOINS_75)),
    ("avis de 31 à 90 jours", age("de 31 à 90 jours", MOINS_75)),
    ("avis de 91 jours à un an", age("de 91 à 365 jours", MOINS_75)),
    ("avis de plus d'un an", age("de plus d'un an", MOINS_75)),
], 8.1, 4.6, bornes=(0.1, 10), marge_gauche=0.43)
image(d, chemin, MARGE, 1.78, 8.1)
texte(d, MARGE, 6.43, 8.1, 0.4, LEGENDE, taille=9, couleur=ENCRE_2)
texte(d, 9.0, 1.9, 3.7, 1.9, [
    "Sans enseignes, tous les points verts ont un trait qui traverse ×1.",
    "Dans la même fiche, avec les enseignes, l'avis répondu tombe 2,4 fois moins. Sans elles, "
    "le point est gris : une fiche porte 35 % des suppressions.",
], taille=11, puces=True, espace=7)
rectangle(d, 9.0, 3.75, 3.7, 2.95)
texte(d, 9.15, 3.85, 3.4, 0.5, "« Répondre sur une fiche qui répond peu augmente le risque » : "
      "non établi", taille=12, gras=True)
texte(d, 9.15, 4.45, 3.4, 2.2, [
    "Première ligne du schéma : le point est à droite de ×1, en gris.",
    "Il repose sur 24 suppressions portées par 6 fiches.",
    "18 des 24 viennent de Cedar Park Overhead Doors, services à domicile, États-Unis "
    "(cid 10505273405281271038), supprimées du 13 au 22 août.",
], taille=11, puces=True, espace=6)

# ---------------------------------------------------------------- ce qu'on ne peut pas dire

d = diapositive("Ce que les données ne permettent pas de dire",
                source="réserves de 1_corpus.md, 2_2_deux_phenomenes.md, 4_quelle_fiche_quel_avis.md, "
                       "8_regression_reponse_base.md")
reserves = [
    ("Qui demande la suppression", "Les signalements sont invisibles. Pour la réponse, deux lectures "
     "restent possibles : la réponse protège l'avis, ou le propriétaire s'abstient de répondre "
     "aux avis qu'il signale."),
    ("Avant le 11 août", "Le suivi dure 14 jours. Un avis supprimé avant le premier passage du "
     "robot est absent de la base."),
    ("Réponses retirées", "Une réponse retirée par le propriétaire ne laisse aucune trace : "
     "l'avis compte « sans réponse »."),
    ("Avis réécrits", "La base contient 125 253 avis modifiés plus d'un an après leur publication, "
     "dont 555 supprimés. Leur âge se compte depuis la publication : ils sont rangés avec "
     "les avis de plus d'un an."),
    ("Europe, par fiche", "Aucun écart de secteur, de taille ou d'afflux entre fiches ne se cite : "
     "les cases de comparaison ne passent pas la règle de citation."),
    ("Texte, copies, prénom, avis revenus", "Ces quatre résultats viennent des rapports, calculés "
     "avant la consolidation. Leurs décomptes peuvent différer de ceux des autres diapositives."),
]
for i, (mot, phrase) in enumerate(reserves):
    x = MARGE + (i % 2) * 6.15
    y = 1.4 + (i // 2) * 1.78
    rectangle(d, x, y, 5.95, 1.62)
    texte(d, x + 0.2, y + 0.14, 5.5, 0.35, mot, taille=13, gras=True, couleur=ORANGE)
    texte(d, x + 0.2, y + 0.5, 5.55, 1.1, phrase, taille=13)

# ---------------------------------------------------------------- comment lire les schémas

d = diapositive("Comment lire les schémas à points",
                source="4b_effets.csv, 8_effets.csv, 5_effets.csv, commun.py (règle de citation), 2_3_note.csv")
chemin = schema("lecture", ["Trois exemples tirés de l'étude"], [
    ("avis 1 étoile, face à un avis 5 étoiles\nde la même fiche", [("4b_effets", "ensemble, sans_enseignes", "note : 1 étoile(s)")]),
    ("avis répondu de 8 à 30 jours, face à\nl'avis sans réponse", [("8_effets", "ensemble, sans_enseignes", f"réponse : avis de 8 à 30 jours, {PLUS_75}")]),
    ("avis répondu le jour même sur une fiche\nqui répond peu", [("5_effets", "mono + small, tous", f"réponse jour même, {MOINS_75}")]),
], 6.0, 2.9, bornes=(0.2, 10), marge_gauche=0.47)
image(d, chemin, MARGE, 1.5, 6.0)
texte(d, MARGE, 4.6, 6.0, 2.1, [
    "Ligne 1 : le point est à ×5, le trait entier est à droite de ×1. L'avis 1 étoile disparaît "
    "5 fois plus.",
    "Ligne 2 : le trait traverse ×1. Les données ne disent pas si l'écart existe.",
    "Ligne 3 : point gris. 18 des 24 suppressions viennent d'une seule fiche.",
], taille=12, puces=True, espace=7)
for i, (titre, lignes) in enumerate([
    ("Le trait vertical à ×1", [
        "Sur ce trait, aucun écart. À droite, l'avis disparaît plus ; à gauche, moins.",
        "×2 : deux fois plus. ×0,5 : deux fois moins.",
    ]),
    ("Le trait horizontal", [
        "Les valeurs compatibles avec les données. Plus il est court, plus la mesure est précise.",
    ]),
    ("Vert ou gris", [
        "Vert : au moins 10 suppressions, sur au moins 5 fiches, sans qu'une fiche en porte plus "
        "du quart. Gris : l'une de ces conditions manque.",
    ]),
    ("Égal par ailleurs", [
        "Aux États-Unis, 529 avis 5 étoiles sur 10 000 disparaissent ; 320 sans les 4 chaînes. "
        "Les schémas comparent des avis qui ne diffèrent que par une caractéristique.",
    ]),
]):
    y = 1.4 + i * 1.34
    rectangle(d, 7.1, y, 5.6, 1.22)
    texte(d, 7.3, y + 0.1, 5.2, 0.3, titre, taille=13, gras=True, couleur=VERT)
    texte(d, 7.3, y + 0.45, 5.2, 0.75, lignes, taille=11, espace=3)

# ---------------------------------------------------------------- reste à faire

d = diapositive("Reste à faire", source="6_plan_regression_panel.md, 8_regression_reponse_base.md, README.md")
texte(d, MARGE, 1.5, 7.4, 4.9, [
    ("Toutes les caractéristiques ensemble, sur le panel", True),
    "Un seul calcul qui tient égales la note, l'auteur, le secteur, l'âge et la réponse. "
    "Le plan et ses 9 questions sont écrits ; la première à trancher : sur quels avis.",
    ("Le texte : copies, sujet, prénom", True),
    "Ces résultats viennent des rapports. Ils restent à refaire sur la base consolidée, avec "
    "la règle de citation.",
    ("L'âge tenu plus finement de 8 à 30 jours", True),
    "Dans cette tranche, le risque passe de 25 à 4 suppressions pour 10 000 avis entre le 8e "
    "et le 30e jour. L'écart lié à la réponse peut en compter une partie.",
], taille=14, espace=9)
rectangle(d, 8.4, 1.5, 4.3, 4.9)
texte(d, 8.65, 1.7, 3.8, 4.5, [
    ("Régénérer les chiffres", True),
    "Un script par point dans consolidation/, moins d'une minute chacun.",
    "Chaque script écrit ses CSV dans consolidation/sorties/. Les schémas à points de cette "
    "présentation lisent ces CSV.",
    "La liste des commandes et des CSV : consolidation/README.md.",
    "Cette présentation : uv run --with python-pptx python consolidation/presentation.py",
], taille=12, espace=9)

SORTIE.parent.mkdir(parents=True, exist_ok=True)
prs.save(SORTIE)
print(f"{SORTIE} : {numero} diapositives")
