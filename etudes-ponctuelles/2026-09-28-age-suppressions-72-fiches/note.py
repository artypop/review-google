#!/usr/bin/env python3
"""Assemble les figures et le document Word à partir des CSV de `calcul.py`.

    python etudes-ponctuelles/2026-09-28-age-suppressions-72-fiches/note.py

Aucun chiffre n'est calculé ici. Sorties : `sorties/figures/*.png` et
`livrables/2026-09-28-analyses-complementaires.docx`. Mise en page reprise du
rapport `livrables/reviewflowz-resultats-propre.docx`.
"""
from __future__ import annotations

import re
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
RACINE = DOSSIER.parent.parent
SORTIES = DOSSIER / "sorties"
FIGURES = SORTIES / "figures"
LIVRABLE = RACINE / "livrables" / "2026-09-28-analyses-complementaires.docx"

G72, GAUTRES = "72 fiches les plus touchées", "Autres fiches"


def csv(nom):
    return pd.read_csv(SORTIES / nom)


def virgule(x, d=1):
    return f"{x:.{d}f}".replace(".", ",")


def espace(n):
    return f"{int(n):,}".replace(",", " ")


# ---------------------------------------------------------------------------
# Figure
# ---------------------------------------------------------------------------
SURFACE = "#fcfcfb"; ENCRE = "#0b0b0b"; ENCRE_DOUCE = "#52514e"; GRILLE = "#e4e3df"
BLEU = "#2a78d6"; GRIS = "#9b9a96"


def figure(suffixe, titre, nom, nom72=G72, court72="72 fiches"):
    t = csv(f"B1-tranches{suffixe}.csv")
    r = csv(f"B2-resume{suffixe}.csv").set_index("groupe")
    tranches = sorted(t["tranche_age"].unique())
    libelles = [x.split(". ", 1)[1] for x in tranches]
    x = np.arange(len(tranches))
    larg = 0.38

    fig, ax = plt.subplots(figsize=(6.6, 3.9), dpi=150)
    fig.patch.set_facecolor(SURFACE); ax.set_facecolor(SURFACE)
    fig.subplots_adjust(left=0.08, right=0.98, top=0.78, bottom=0.12)
    for c in ("top", "right", "left"):
        ax.spines[c].set_visible(False)
    ax.spines["bottom"].set_color(GRILLE)
    ax.tick_params(colors=ENCRE_DOUCE, labelsize=8.5, length=0)
    ax.grid(True, axis="y", color=GRILLE, linewidth=1, zorder=0)
    ax.set_axisbelow(True)

    for decal, groupe, couleur in ((-larg / 2, G72, BLEU), (larg / 2, GAUTRES, GRIS)):
        g = t[t["groupe"] == groupe].set_index("tranche_age").reindex(tranches)
        n = int(r.loc[groupe, "suppressions"])
        barres = ax.bar(x + decal, g["part_du_groupe_pct"], width=larg, color=couleur,
                        zorder=3,
                        label=f"{nom72 if groupe == G72 else groupe} ({espace(n)} suppressions)")
        for b, v in zip(barres, g["part_du_groupe_pct"]):
            ax.text(b.get_x() + b.get_width() / 2, v + 0.8, f"{virgule(v, 0)} %",
                    ha="center", fontsize=7.5, color=ENCRE)
    ax.set_xticks(x, libelles)
    haut = t["part_du_groupe_pct"].max()
    ax.set_ylim(0, haut * 1.15)
    graduations = [v for v in (0, 10, 20, 30, 40, 50) if v <= haut * 1.15]
    ax.set_yticks(graduations, [f"{v} %" for v in graduations])
    leg = ax.legend(frameon=False, fontsize=8, loc="upper right")
    for tx in leg.get_texts():
        tx.set_color(ENCRE_DOUCE)
    fig.text(0.012, 0.975, titre, fontsize=11, color=ENCRE, va="top")
    fig.text(0.012, 0.91,
             "Part des suppressions de chaque groupe, par âge de l'avis au jour de sa "
             "suppression.\nÂge médian : {} jours sur les {}, {} jours sur les "
             "autres fiches.".format(int(r.loc[G72, "age_median_j"]), court72,
                                     int(r.loc[GAUTRES, "age_median_j"])),
             fontsize=8.5, color=ENCRE_DOUCE, va="top", linespacing=1.5)
    FIGURES.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURES / nom, dpi=150, facecolor=SURFACE)
    plt.close(fig)
    return FIGURES / nom


# ---------------------------------------------------------------------------
# Document
# ---------------------------------------------------------------------------
NAVY = RGBColor(0x32, 0x29, 0x54); ENC = RGBColor(0x1F, 0x1F, 0x1F); GR = RGBColor(0x6B, 0x6A, 0x66)
POLICE = "Calibri"
MARQUE = re.compile(r"(\*\*.+?\*\*)")


def styler(doc):
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21), Cm(29.7)
    sec.left_margin = sec.right_margin = Cm(2.2)
    sec.top_margin, sec.bottom_margin = Cm(2.2), Cm(2.0)
    st = doc.styles
    n = st["Normal"]
    n.font.name = POLICE; n.font.size = Pt(10.5); n.font.color.rgb = ENC
    n.element.rPr.rFonts.set(qn("w:eastAsia"), POLICE)
    n.paragraph_format.space_after = Pt(6)
    for nom, taille, avant, apres, couleur, gras in (
            ("Heading 1", 16, 18, 8, NAVY, True), ("Title", 24, 0, 4, NAVY, True),
            ("Subtitle", 12, 0, 16, GR, False)):
        s = st[nom]
        s.font.name = POLICE; s.font.size = Pt(taille); s.font.bold = gras
        s.font.italic = False; s.font.color.rgb = couleur
        rpr = s.element.get_or_add_rPr()
        rf = rpr.find(qn("w:rFonts"))
        if rf is None:
            rf = OxmlElement("w:rFonts"); rpr.append(rf)
        for a in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
            rf.set(qn(a), POLICE)
        for a in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
            if rf.get(qn(a)) is not None:
                del rf.attrib[qn(a)]
        s.paragraph_format.space_before = Pt(avant); s.paragraph_format.space_after = Pt(apres)
        s.paragraph_format.keep_with_next = True
        ppr = s.element.get_or_add_pPr()
        for b in ppr.findall(qn("w:pBdr")):
            ppr.remove(b)
    leg = st.add_style("Legende", 1)
    leg.base_style = n; leg.font.size = Pt(9); leg.font.italic = True; leg.font.color.rgb = GR
    leg.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    leg.paragraph_format.space_after = Pt(12)
    tt = st.add_style("TitreTableau", 1)
    tt.base_style = n; tt.font.size = Pt(9.5); tt.font.bold = True; tt.font.color.rgb = NAVY
    tt.paragraph_format.space_before = Pt(10); tt.paragraph_format.keep_with_next = True
    nt = st.add_style("NoteTableau", 1)
    nt.base_style = n; nt.font.size = Pt(9); nt.font.color.rgb = GR
    nt.paragraph_format.space_after = Pt(10)
    st["List Bullet"].font.size = Pt(10.5)


def P(doc, texte, style=None):
    p = doc.add_paragraph(style=style)
    for m in MARQUE.split(texte):
        if m.startswith("**"):
            p.add_run(m[2:-2]).bold = True
        elif m:
            p.add_run(m)
    return p


def fond(cell, couleur):
    sh = OxmlElement("w:shd")
    sh.set(qn("w:val"), "clear"); sh.set(qn("w:color"), "auto"); sh.set(qn("w:fill"), couleur)
    cell._tc.get_or_add_tcPr().append(sh)


def tableau(doc, titre, entetes, lignes, largeurs, gras_derniere=False):
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
            r = p.add_run(str(val)); r.font.size = Pt(9)
            if i == 0:
                r.bold = True; r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF); fond(c, "322954")
            elif gras_derniere and i == len(lignes):
                r.bold = True
            elif i % 2 == 0:
                fond(c, "F4F4F7")
    for j, gc in enumerate(t._tbl.tblGrid.findall(qn("w:gridCol"))):
        gc.set(qn("w:w"), str(int(largeurs[j] * 567)))


def lignes_tranches(suffixe):
    t = csv(f"B1-tranches{suffixe}.csv")
    a = t[t["groupe"] == G72].set_index("tranche_age")
    b = t[t["groupe"] == GAUTRES].set_index("tranche_age")
    out = []
    for tr in sorted(t["tranche_age"].unique()):
        out.append([tr.split(". ", 1)[1],
                    espace(a.loc[tr, "suppressions"]), f"{virgule(a.loc[tr, 'part_du_groupe_pct'])} %",
                    espace(b.loc[tr, "suppressions"]), f"{virgule(b.loc[tr, 'part_du_groupe_pct'])} %"])
    out.append(["Total", espace(a["suppressions"].sum()), "100 %",
                espace(b["suppressions"].sum()), "100 %"])
    return out


def main() -> int:
    # Nombre des 72 fiches qui restent sans les enseignes signalées : compté, pas saisi.
    n_sans = int(csv("B2-resume-sans-enseignes.csv").set_index("groupe").loc[G72, "fiches"])
    fig_tous = figure("", "Âge des avis au jour de leur suppression", "figure1-age-72-fiches.png")
    fig_sans = figure("-sans-enseignes", "Même mesure, sans les six enseignes signalées",
                      "figure2-age-72-fiches-sans-enseignes.png",
                      nom72=f"{n_sans} fiches restantes des 72", court72=f"{n_sans} fiches")
    r = csv("B2-resume.csv").set_index("groupe")
    rs = csv("B2-resume-sans-enseignes.csv").set_index("groupe")
    fiches = csv("A1-les-72-fiches.csv")
    n_ens = int(fiches["enseigne_signalee"].sum())

    doc = Document()
    styler(doc)
    pied = doc.sections[0].footer.paragraphs[0]
    run = pied.add_run("ReviewFlowz · Analyses complémentaires · Septembre 2026")
    run.font.size = Pt(8.5); run.font.color.rgb = GR

    doc.add_paragraph("Analyses complémentaires", style="Title")
    doc.add_paragraph("ReviewFlowz · 28 septembre 2026", style="Subtitle")

    doc.add_heading("1. Âge des avis supprimés sur les 72 fiches les plus touchées", level=1)
    P(doc, "Les 72 fiches qui portent la moitié des suppressions de toute la base (figure 4 du "
           f"rapport), comparées aux {espace(r.loc[GAUTRES, 'fiches'])} autres fiches touchées. "
           "Âge : jour du relevé où l'avis a disparu moins son jour de publication.")

    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(str(fig_tous), width=Cm(15.5))
    doc.add_paragraph("Figure 1. Âge des avis au jour de leur suppression.", style="Legende")

    for texte in (
            f"**Âge médian : {int(r.loc[G72, 'age_median_j'])} jours** sur les 72 fiches, "
            f"{int(r.loc[GAUTRES, 'age_median_j'])} jours sur les autres.",
            "La moitié des suppressions des 72 fiches porte sur des avis de "
            f"{virgule(r.loc[G72, 'age_premier_quart_j'], 0)} à "
            f"{virgule(r.loc[G72, 'age_dernier_quart_j'], 0)} jours ; sur les autres fiches, de "
            f"{virgule(r.loc[GAUTRES, 'age_premier_quart_j'], 0)} à "
            f"{virgule(r.loc[GAUTRES, 'age_dernier_quart_j'], 0)} jours."):
        P(doc, texte, "List Bullet")

    tableau(doc, "Tableau 1. Suppressions par âge de l'avis",
            ["Âge de l'avis", "72 fiches : avis", "72 fiches : part", "Autres : avis",
             "Autres : part"], lignes_tranches(""), [3.6, 3.1, 3.1, 3.1, 3.1], gras_derniere=True)

    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.page_break_before = True
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(str(fig_sans), width=Cm(15.5))
    doc.add_paragraph("Figure 2. Même mesure, sans les six enseignes signalées.", style="Legende")
    P(doc, f"{n_ens} des 72 fiches appartiennent aux enseignes signalées. Sans elles, il reste "
           f"{int(rs.loc[G72, 'fiches'])} fiches et {espace(rs.loc[G72, 'suppressions'])} "
           f"suppressions ; âge médian {int(rs.loc[G72, 'age_median_j'])} jours, contre "
           f"{int(rs.loc[GAUTRES, 'age_median_j'])} jours sur les autres fiches.")
    tableau(doc, "Tableau 2. Même tableau, sans les six enseignes signalées",
            ["Âge de l'avis", f"{n_sans} fiches : avis", f"{n_sans} fiches : part", "Autres : avis",
             "Autres : part"], lignes_tranches("-sans-enseignes"), [3.6, 3.1, 3.1, 3.1, 3.1],
            gras_derniere=True)

    doc.add_heading("Réserves", level=1)
    for texte in (
            "Seules les suppressions constatées du 11 au 24 août sont visibles. Un avis ancien "
            "n'apparaît que s'il a été supprimé pendant ces 14 jours.",
            "L'âge est connu au jour près : le robot passe une fois par jour.",
            "Suppression : même définition que la figure 4 du rapport."):
        P(doc, texte, "List Bullet")
    P(doc, "Sources : etudes-ponctuelles/2026-09-28-age-suppressions-72-fiches/ (calcul.py, "
           "note.py, sorties/*.csv, dont la liste des 72 fiches A1-les-72-fiches.csv).",
      "NoteTableau")

    doc.core_properties.title = "Analyses complémentaires"
    doc.core_properties.author = "Cartelis"
    doc.save(LIVRABLE)
    print(f"ecrit : {LIVRABLE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
