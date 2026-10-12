#!/usr/bin/env python3
"""Écrit `livrables/regroupement-textes-us.docx`, version courte.

    .venv/Scripts/python.exe etudes-ponctuelles/2026-09-29-hdbscan-residus-us/note.py

Lit `sorties/A1-regroupements.csv` et `sorties/A2-groupes.csv`. Aucun chiffre
n'est calculé ici. Styles repris de `livrables/analyses-complémentaires.docx`,
dont le contenu est retiré de la copie.

Étiquettes des groupes : établies le 2026-09-29 par lecture de 6 à 8 textes
tirés au hasard dans chaque groupe et de ses mots les plus caractéristiques
(`lecture.py`, écran seulement). Elles valent pour les numéros de groupe
produits par `calcul.py` avec ses graines : le script s'arrête si les effectifs
ne correspondent plus.
"""
from __future__ import annotations

# Remplacé le 2026-09-29 par etudes-ponctuelles/2026-09-29-synthese-textes/note.py,
# qui écrit livrables/regroupement-textes-us.docx en entier. Relancer ce script
# réécrirait l'ancienne structure du document.
raise SystemExit("remplacé par etudes-ponctuelles/2026-09-29-synthese-textes/note.py")


from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from docx import Document  # noqa: E402
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT  # noqa: E402
from docx.enum.text import WD_ALIGN_PARAGRAPH  # noqa: E402
from docx.oxml import OxmlElement  # noqa: E402
from docx.oxml.ns import qn  # noqa: E402
from docx.shared import Cm, Pt, RGBColor  # noqa: E402

DOSSIER = Path(__file__).resolve().parent
RACINE = DOSSIER.parents[1]
SORTIES = DOSSIER / "sorties"
FIGURE = SORTIES / "figure-groupes.png"
MODELE = RACINE / "livrables" / "analyses-complémentaires.docx"
LIVRABLE = RACINE / "livrables" / "regroupement-textes-us.docx"
POP = "sans_enseignes"

# groupe -> (étiquette, nombre d'avis attendu dans A2, lecture), sans les six enseignes
GROUPES = {
    14: ("Jugements d'un à trois mots (« Good job », « Nice »)", 106, "réparti sur 6 fiches"),
    66: ("1 étoile : frais, facturation, location de voiture", 90, "réparti sur 10 fiches"),
    33: ("Soins esthétiques, praticienne citée par son prénom", 182, "réparti sur 8 fiches"),
    3: ("Station de lavage, employé cité par son prénom", 53, "7 sur 8 sur une fiche"),
    8: ("Lavage auto, employé cité, avis courts", 48, "une seule fiche"),
    0: ("Revêtements de sol, vendeur cité par son nom", 163, "contre-exemple"),
}


def virgule(x, d=1):
    return f"{x:.{d}f}".replace(".", ",")


def espace(n):
    return f"{int(n):,}".replace(",", " ")


# ---------------------------------------------------------------------------
# Figure : suppressions observées et attendues, groupes du tableau 1
# ---------------------------------------------------------------------------
SURFACE = "#fcfcfb"; ENCRE = "#0b0b0b"; ENCRE_DOUCE = "#52514e"; GRILLE = "#e4e3df"
BLEU = "#2a78d6"; GRIS = "#bdbcb8"


def figure(lignes):
    lignes = lignes[::-1]
    y = np.arange(len(lignes))
    fig, ax = plt.subplots(figsize=(7.2, 3.3), dpi=150)
    fig.patch.set_facecolor(SURFACE); ax.set_facecolor(SURFACE)
    fig.subplots_adjust(left=0.45, right=0.96, top=0.74, bottom=0.12)
    h = 0.36
    obs = [r["n_supprimes"] for _, r in lignes]
    att = [r["attendu_par_case"] for _, r in lignes]
    ax.barh(y + h / 2, obs, h, color=BLEU, label="supprimés")
    ax.barh(y - h / 2, att, h, color=GRIS, label="attendus d'après le secteur et la note")
    for yi, o in zip(y, obs):
        ax.text(o + 0.2, yi + h / 2, str(int(o)), va="center", fontsize=7, color=ENCRE)
    ax.set_yticks(y, [GROUPES[g][0].split(" (")[0] for g, _ in lignes], fontsize=7.5)
    for c in ("top", "right", "left"):
        ax.spines[c].set_visible(False)
    ax.spines["bottom"].set_color(GRILLE)
    ax.tick_params(colors=ENCRE_DOUCE, labelsize=7.5, length=0)
    ax.set_xlabel("avis supprimés", fontsize=7.5, color=ENCRE_DOUCE)
    ax.legend(frameon=False, fontsize=7.5, loc="lower left", bbox_to_anchor=(0, 1.0), ncol=2)
    fig.text(0.012, 0.97, "Suppressions observées et attendues par groupe de textes",
             fontsize=10.5, color=ENCRE, va="top")
    fig.text(0.012, 0.90, "Avis US en anglais, sans les six enseignes", fontsize=8,
             color=ENCRE_DOUCE, va="top")
    fig.savefig(FIGURE, dpi=150, facecolor=SURFACE)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Document
# ---------------------------------------------------------------------------
NAVY = RGBColor(0x32, 0x29, 0x54)


def P(doc, texte, style=None):
    p = doc.add_paragraph(style=style)
    for i, m in enumerate(texte.split("**")):
        if m:
            p.add_run(m).bold = i % 2 == 1
    return p


def puces(doc, textes):
    for t in textes:
        P(doc, t, "List Bullet")


def fond(cell, couleur):
    sh = OxmlElement("w:shd")
    sh.set(qn("w:val"), "clear"); sh.set(qn("w:color"), "auto"); sh.set(qn("w:fill"), couleur)
    cell._tc.get_or_add_tcPr().append(sh)


def tableau(doc, titre, entetes, lignes, largeurs, note=None):
    doc.add_paragraph(titre, style="TitreTableau")
    t = doc.add_table(rows=1 + len(lignes), cols=len(entetes))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    bords = OxmlElement("w:tblBorders")
    for cote in ("top", "left", "bottom", "right", "insideH", "insideV"):
        e = OxmlElement(f"w:{cote}")
        if cote in ("left", "right", "insideV"):
            e.set(qn("w:val"), "nil")
        else:
            e.set(qn("w:val"), "single"); e.set(qn("w:sz"), "4"); e.set(qn("w:color"), "D9D8DE")
        bords.append(e)
    t._tbl.tblPr.append(bords)
    for i, rangee in enumerate([entetes] + lignes):
        for j, val in enumerate(rangee):
            c = t.rows[i].cells[j]
            c.width = Cm(largeurs[j])
            c.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            p = c.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT if j == 0 else WD_ALIGN_PARAGRAPH.RIGHT
            texte, gras = val if isinstance(val, tuple) else (val, False)
            r = p.add_run(str(texte)); r.font.size = Pt(9); r.bold = gras
            if i == 0:
                r.bold = True; r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF); fond(c, "322954")
            elif i % 2 == 0:
                fond(c, "F4F4F7")
    for j, gc in enumerate(t._tbl.tblGrid.findall(qn("w:gridCol"))):
        gc.set(qn("w:w"), str(int(largeurs[j] * 567)))
    if note:
        doc.add_paragraph(note, style="NoteTableau")


def document_vide():
    doc = Document(MODELE)
    corps = doc.element.body
    for e in list(corps):
        if e.tag != qn("w:sectPr"):
            corps.remove(e)
    for s in doc.sections:
        for zone in (s.header, s.footer, s.first_page_header, s.first_page_footer):
            for p in zone.paragraphs:
                for r in p.runs:
                    r.text = ""
    return doc


def main() -> int:
    a = pd.read_csv(SORTIES / "A1-regroupements.csv").set_index(["population", "vecteurs"])
    g = pd.read_csv(SORTIES / "A2-groupes.csv")
    g = g[(g["population"] == POP) & (g["vecteurs"] == "corriges")].set_index("groupe")
    for grp, (_, n, _) in GROUPES.items():
        if int(g.at[grp, "n_avis"]) != n:
            raise SystemExit(f"groupe {grp} : effectif changé, étiquettes à refaire")
    lignes = [(grp, g.loc[grp]) for grp in GROUPES]
    figure(lignes)

    rs, rb = a.loc[(POP, "corriges")], a.loc[(POP, "bruts")]
    groupes = g[g.index >= 0]
    hors = (groupes["hors_du_hasard"].fillna("") != "").sum()
    bruit = g.loc[-1]
    n_trois = int(sum(g.at[k, "n_supprimes"] for k in (14, 66, 33)))

    doc = document_vide()
    doc.add_paragraph("Groupes de textes après retrait du secteur et de la note", style="Title")
    P(doc, "Avis américains en anglais, panel 03B, sans les six enseignes : "
           f"{espace(rs['n_avis'])} avis, {espace(rs['n_supprimes'])} supprimés. 2026-09-29.")

    # 1. Résultats ------------------------------------------------------------
    doc.add_heading("1. Résultats", level=1)
    puces(doc, [
        "**Les groupes décrivent désormais la forme des avis** : avis très courts, employé cité, "
        "plainte sur des frais. Le secteur pèse moins (tableau 2).",
        f"**{hors} groupes sur {len(groupes)} s'écartent du hasard.** Le hasard seul en "
        f"produirait environ {virgule(0.05 * len(groupes), 0)}.",
        "**Trois motifs répartis sur plusieurs fiches sont supprimés 1,7 à 2,6 fois plus "
        "qu'attendu** : jugements d'un à trois mots, praticienne citée en soins esthétiques, "
        "plaintes sur des frais.",
        f"**Ils ne pèsent que {n_trois} des {espace(rs['n_supprimes'])} suppressions.** Le texte "
        "explique donc une petite part des suppressions.",
        "**Citer un employé ne suffit pas** : les avis de revêtements de sol qui nomment le "
        f"vendeur comptent {int(g.at[0, 'n_supprimes'])} suppression pour "
        f"{virgule(g.at[0, 'attendu_par_case'], 0)} attendues.",
    ])

    tableau(doc, "Tableau 1. Les groupes à retenir",
            ["Groupe de textes", "Avis", "Supprimés", "Attendus", "Lecture"],
            [[GROUPES[k][0], espace(r["n_avis"]), (espace(r["n_supprimes"]), True),
              virgule(r["attendu_par_case"]), GROUPES[k][2]] for k, r in lignes],
            [7.6, 1.4, 1.8, 1.8, 3.6],
            "Attendus : suppressions qu'aurait le groupe si chacun de ses avis était supprimé "
            "au taux moyen de son secteur et de sa note.")

    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(str(FIGURE), width=Cm(15.5))
    doc.add_paragraph("Figure 1. Suppressions observées et attendues, groupes du tableau 1.",
                      style="Legende")

    tableau(doc, "Tableau 2. Ce que change le retrait du secteur et de la note",
            ["", "Vecteurs bruts", "Secteur et note retirés", "Groupes au hasard"],
            [["Part des avis d'un groupe venant de son secteur principal",
              f"{virgule(rb['part_secteur_principal_pct'], 0)} %",
              (f"{virgule(rs['part_secteur_principal_pct'], 0)} %", True),
              f"{virgule(rs['part_secteur_principal_hasard_pct'], 0)} %"],
             ["Nombre de groupes", espace(rb["n_groupes"]), espace(rs["n_groupes"]), ""],
             ["Avis hors de tout groupe", f"{virgule(rb['part_sans_groupe_pct'], 0)} %",
              f"{virgule(rs['part_sans_groupe_pct'], 0)} %", ""]],
            [7.0, 2.8, 3.6, 2.8])

    # 2. Méthode ----------------------------------------------------------------
    doc.add_heading("2. Méthode", level=1)
    puces(doc, [
        "**Embedding** : chaque avis est traduit en une liste de 768 nombres par le modèle "
        "e5-base. Deux textes au sens proche ont des listes proches.",
        "**Retrait du secteur et de la note** : on soustrait à chaque avis la moyenne des avis "
        "de même secteur et de même note. Il reste ce qui le distingue de ses voisins : "
        "tournure, longueur, prénom, plainte précise.",
        "**Pourquoi pas par fiche** : un prénom répété sur une fiche disparaîtrait avec la "
        "moyenne de la fiche.",
        "**ACP** : résume les 768 nombres en 50, en gardant l'essentiel des différences.",
        "**t-SNE** : place les avis sur une carte à deux dimensions où les avis proches restent "
        "voisins. Remplace UMAP, bloqué par Windows sur ce poste.",
        "**HDBSCAN** : forme des groupes là où les avis sont serrés sur la carte. Le nombre de "
        "groupes n'est pas fixé à l'avance, et les avis isolés restent hors groupe. KMeans, "
        "utilisé le 28/09, range chaque avis dans l'un de 3 ou 4 grands groupes.",
        "**Hasard** : 2 000 groupes tirés au hasard, de même taille et même mélange secteur × "
        "note. Un groupe s'en écarte s'il compte plus ou moins de suppressions que 97,5 % des tirages.",
        "**Stabilité** : calcul relancé trois fois ; un groupe est retenu s'il réapparaît à "
        "chaque fois avec au moins la moitié de ses avis.",
        "**Noms des groupes** : lecture de 6 à 8 avis par groupe.",
    ])

    # 3. Limites ------------------------------------------------------------------
    doc.add_heading("3. Limites", level=1)
    puces(doc, [
        "10 à 15 suppressions par groupe retenu : quelques avis de plus ou de moins changent "
        "la lecture.",
        f"{int(rs['n_groupes_stables'])} groupes sur {int(rs['n_groupes'])} seulement réapparaissent "
        "à chaque relance.",
        "Europe non couverte.",
    ])

    doc.add_heading("4. Suite proposée", level=1)
    puces(doc, [
        "Mesurer directement « texte d'un à trois mots » et « prénom d'employé cité » dans la "
        "régression, à note et secteur égaux.",
    ])

    P(doc, "Sources : etudes-ponctuelles/2026-09-29-hdbscan-residus-us/ (calcul.py, note.py, "
           "sorties/A1-regroupements.csv, A2-groupes.csv). Version avec les six enseignes dans "
           "les mêmes fichiers. Vecteurs : data/embeddings/03B_e5base.parquet.", "NoteTableau")

    doc.save(LIVRABLE)
    print(f"écrit : {LIVRABLE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
