#!/usr/bin/env python3
"""Assemble les figures et le document Word à partir des CSV de `calcul.py`.

    python etudes-ponctuelles/2026-09-28-secteurs-et-concentration/note.py

Aucun chiffre n'est calculé ici. Sorties : `sorties/figures/*.png` et
`livrables/2026-09-28-secteurs-et-concentration.docx`. Mise en page reprise du
rapport `livrables/reviewflowz-resultats-propre.docx`.

    python etudes-ponctuelles/2026-09-28-secteurs-et-concentration/note.py --doublons-cleaned

Lit `sorties/doublons-cleaned/` et réécrit les parties 1 et 2 de
`livrables/analyses-complémentaires.docx`, le document où Matthieu a réuni les
notes du 2026-09-28. Tout ce qui va du titre « 1. Suppressions par secteur » au
titre « 3. » est remplacé ; le reste du document n'est pas touché.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
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
LIVRABLE = RACINE / "livrables" / "2026-09-28-secteurs-et-concentration.docx"

# Ordre des lignes du tableau 1 du rapport.
ORDRE_SECTEURS = ["Automobile", "Services à domicile", "Santé", "Sport et bien-être",
                  "Restauration", "Voyage", "Hôtellerie"]


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
BLEU = "#2a78d6"; ORANGE = "#eb6834"; GRIS = "#9b9a96"


def figure(suffixe, titre, nom):
    d = csv(f"B4-courbe{suffixe}.csv")
    cadre = csv(f"B1-cadre{suffixe}.csv").set_index("mesure")["valeur"]
    touchees = int(cadre["fiches ayant perdu au moins un avis"])
    seuils = csv(f"B3-seuils{suffixe}.csv").set_index("mesure")["valeur"]
    moitie = int(seuils["fiches portant la moitié des suppressions"])
    # Les courbes s'arrêtent à la dernière fiche touchée : au-delà, le classement
    # passe aux fiches sans suppression, rangées par taille.
    d = d[d["rang"] <= touchees]
    borne = int(round(touchees * 1.05 / 10) * 10)

    fig, ax = plt.subplots(figsize=(6.6, 4.0), dpi=150)
    fig.patch.set_facecolor(SURFACE); ax.set_facecolor(SURFACE)
    fig.subplots_adjust(left=0.09, right=0.97, top=0.80, bottom=0.14)
    for c in ("top", "right"):
        ax.spines[c].set_visible(False)
    for c in ("left", "bottom"):
        ax.spines[c].set_color(GRILLE)
    ax.tick_params(colors=ENCRE_DOUCE, labelsize=8.5, length=0)
    ax.grid(True, color=GRILLE, linewidth=1, zorder=0)
    ax.set_axisbelow(True)

    ax.plot(d["rang"], d["part_observee"], color=BLEU, linewidth=2, zorder=4,
            label="Part des suppressions des fiches les plus touchées")
    ax.plot(d["rang"], d["part_avis_touchees"], color=GRIS, linewidth=2, zorder=3,
            label="Part des avis de ces mêmes fiches")
    ax.plot(d["rang"], d["part_avis_plus_grosses"], color=ORANGE, linewidth=2,
            linestyle="--", zorder=3, label="Part des avis des plus grosses fiches")
    ax.plot([moitie], [50], marker="o", markersize=7, color=BLEU,
            markeredgecolor=SURFACE, markeredgewidth=2, zorder=5)
    ax.annotate(f"{moitie} fiches portent\nla moitié des suppressions", xy=(moitie, 50),
                xytext=(moitie + borne * 0.08, 36), fontsize=8.5, color=ENCRE,
                arrowprops=dict(arrowstyle="-", color=ENCRE_DOUCE, linewidth=1))
    ax.set_xlim(0, borne)
    ax.set_ylim(0, 102)
    ax.set_yticks([0, 25, 50, 75, 100], ["0 %", "25 %", "50 %", "75 %", "100 %"])
    ax.set_xlabel("Nombre de fiches, rangées de la plus touchée à la moins touchée",
                  fontsize=8.5, color=ENCRE_DOUCE, labelpad=6)
    leg = ax.legend(frameon=False, fontsize=8, loc="center right", handlelength=2,
                    bbox_to_anchor=(1.0, 0.6))
    for t in leg.get_texts():
        t.set_color(ENCRE_DOUCE)
    fig.text(0.012, 0.975, titre, fontsize=11, color=ENCRE, va="top")
    fig.text(0.012, 0.915,
             f"{espace(cadre['suppressions'])} suppressions sur {espace(cadre['avis'])} avis "
             f"publiés du 4 au 24 août 2026.\n{touchees} fiches touchées sur "
             f"{espace(cadre['fiches ayant au moins un avis publié dans la période'])}.",
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
        rf = s.element.get_or_add_rPr().find(qn("w:rFonts"))
        if rf is None:
            rf = OxmlElement("w:rFonts"); s.element.get_or_add_rPr().append(rf)
        for a in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
            rf.set(qn(a), POLICE)
        for a in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
            if rf.get(qn(a)) is not None:
                del rf.attrib[qn(a)]
        s.paragraph_format.space_before = Pt(avant); s.paragraph_format.space_after = Pt(apres)
        s.paragraph_format.keep_with_next = True
        for b in s.element.get_or_add_pPr().findall(qn("w:pBdr")):
            s.element.get_or_add_pPr().remove(b)
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
    return t


def lignes_secteurs(d):
    d = d.set_index("secteur_fr").loc[ORDRE_SECTEURS].reset_index()
    out = [[r.secteur_fr, espace(r.avis), f"{virgule(r.part_corpus_pct)} %",
            espace(r.suppressions), f"{virgule(r.part_supprimee_pct, 2)} %"]
           for r in d.itertuples()]
    tot_a, tot_s = d["avis"].sum(), d["suppressions"].sum()
    out.append(["Total", espace(tot_a), "100 %", espace(tot_s),
                f"{virgule(100 * tot_s / tot_a, 2)} %"])
    return out


def lignes_concentration(d):
    dernier = d["fiches_les_plus_touchees"].max()
    nom = lambda n: f"{n} (toutes les fiches touchées)" if n == dernier else str(n)
    return [[nom(r.fiches_les_plus_touchees), f"{virgule(r.part_suppressions_pct)} %",
             f"{virgule(r.part_avis_de_ces_fiches_pct)} %",
             f"{virgule(r.part_avis_plus_grosses_fiches_pct)} %"] for r in d.itertuples()]


def parties_1_2(doc, fig_tous, fig_sans, base: str, note_tableau_1: str,
                definition: str) -> None:
    """Écrit les parties 1 et 2 à la fin de `doc`."""
    # 1. Secteurs --------------------------------------------------------------
    doc.add_heading("1. Suppressions par secteur", level=1)
    sect = csv("A1-secteurs.csv")
    P(doc, f"{base} : {espace(sect['avis'].sum())} avis, toutes dates de publication, "
           f"{espace(sect['suppressions'].sum())} suppressions.")
    tableau(doc, "Tableau 1. Avis et suppressions par secteur",
            ["Secteur", "Avis du secteur", "% du corpus", "Nombre de suppressions",
             "% de suppression"], lignes_secteurs(sect), [4.0, 3.0, 2.6, 3.4, 3.0],
            gras_derniere=True)
    P(doc, note_tableau_1, "NoteTableau")
    tableau(doc, "Tableau 2. Même tableau, sans les six enseignes signalées",
            ["Secteur", "Avis du secteur", "% du corpus", "Nombre de suppressions",
             "% de suppression"], lignes_secteurs(csv("A1-secteurs-sans-enseignes.csv")),
            [4.0, 3.0, 2.6, 3.4, 3.0], gras_derniere=True)
    P(doc, "Enseignes signalées : les 4 chaînes antiparasitaires américaines (services à domicile) "
           "et les 2 salles de sport espagnoles attaquées (sport et bien-être).", "NoteTableau")

    # 2. Concentration -----------------------------------------------------------
    h = doc.add_heading("2. Concentration des suppressions, avis publiés du 4 au 24 août", level=1)
    h.paragraph_format.page_break_before = True
    cadre = csv("B1-cadre.csv").set_index("mesure")["valeur"]
    seuils = csv("B3-seuils.csv").set_index("mesure")["valeur"]
    P(doc, "Avis publiés du 4 août, 7 jours avant le premier relevé, au 24 août, dernier relevé : "
           f"{espace(cadre['avis'])} avis sur "
           f"{espace(cadre['fiches ayant au moins un avis publié dans la période'])} fiches, "
           f"{espace(cadre['suppressions'])} suppressions sur "
           f"{espace(cadre['fiches ayant perdu au moins un avis'])} fiches.")
    for chemin, leg in ((fig_tous, "Figure 1. Part des suppressions portée par les fiches les plus touchées."),):
        p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.keep_with_next = True
        p.add_run().add_picture(str(chemin), width=Cm(15.5))
        doc.add_paragraph(leg, style="Legende")
    for texte in (
            f"**{int(seuils['fiches portant le quart des suppressions'])} fiches** portent le quart "
            "des suppressions.",
            f"**{int(seuils['fiches portant la moitié des suppressions'])} fiches** en portent la "
            "moitié.",
            f"**{int(seuils['fiches portant les trois quarts des suppressions'])} fiches** en "
            "portent les trois quarts."):
        P(doc, texte, "List Bullet")
    tableau(doc, "Tableau 3. Part des suppressions et des avis des N fiches les plus touchées",
            ["N fiches les plus touchées", "Part des suppressions", "Part des avis de ces fiches",
             "Part des avis des N plus grosses fiches"],
            lignes_concentration(csv("B2-concentration.csv")), [5.0, 3.2, 3.4, 4.4])
    P(doc, "La courbe orange et la dernière colonne donnent la part des avis détenue par les N "
           "fiches qui ont le plus d'avis. Ce ne sont pas les fiches les plus touchées : leur "
           "propre part d'avis est la courbe grise.", "NoteTableau")

    seuils_s = csv("B3-seuils-sans-enseignes.csv").set_index("mesure")["valeur"]
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.page_break_before = True
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(str(fig_sans), width=Cm(15.5))
    doc.add_paragraph("Figure 2. Même mesure, sans les six enseignes signalées.", style="Legende")
    P(doc, f"Sans les enseignes, {int(seuils_s['fiches portant le quart des suppressions'])}, "
           f"{int(seuils_s['fiches portant la moitié des suppressions'])} et "
           f"{int(seuils_s['fiches portant les trois quarts des suppressions'])} fiches portent le "
           "quart, la moitié et les trois quarts des suppressions.")
    tableau(doc, "Tableau 4. Même tableau, sans les six enseignes signalées",
            ["N fiches les plus touchées", "Part des suppressions", "Part des avis de ces fiches",
             "Part des avis des N plus grosses fiches"],
            lignes_concentration(csv("B2-concentration-sans-enseignes.csv")), [5.0, 3.2, 3.4, 4.4])

    doc.add_heading("Réserves", level=1)
    for texte in (
            "Un avis publié en fin de période est suivi quelques jours seulement : il a moins de "
            "temps pour être supprimé.",
            "Une chaîne compte autant de fiches que de succursales : les EcoShield occupent "
            "plusieurs rangs du classement.",
            definition):
        P(doc, texte, "List Bullet")
    dossier = "sorties/doublons-cleaned/*.csv" if SORTIES.name == "doublons-cleaned" else "sorties/*.csv"
    P(doc, "Sources : etudes-ponctuelles/2026-09-28-secteurs-et-concentration/ (calcul.py, "
           f"note.py, {dossier}).", "NoteTableau")


def remplacer_dans(chemin: Path, fig_tous, fig_sans, **textes) -> None:
    """Remplace les parties 1 et 2 d'un document existant, du titre « 1. » au titre « 3. »."""
    doc = Document(chemin)
    corps = doc.element.body
    paras = doc.paragraphs
    debut = next(p._p for p in paras if p.text.startswith("1. Suppressions par secteur"))
    fin = next(p._p for p in paras if p.text.startswith("3. "))
    courant = debut
    while courant is not fin:
        suivant = courant.getnext()
        corps.remove(courant)
        courant = suivant
    avant = len(corps)
    parties_1_2(doc, fig_tous, fig_sans, **textes)
    # Les éléments ajoutés à la fin (avant sectPr) remontent devant le titre « 3. ».
    nouveaux = [e for e in list(corps)[avant - 1:] if e.tag != qn("w:sectPr")]
    for e in nouveaux:
        fin.addprevious(e)
    doc.save(chemin)
    print(f"ecrit : {chemin}")


def main() -> int:
    global SORTIES, FIGURES
    ap = argparse.ArgumentParser()
    ap.add_argument("--doublons-cleaned", action="store_true")
    args = ap.parse_args()
    if args.doublons_cleaned:
        SORTIES = SORTIES / "doublons-cleaned"
        FIGURES = SORTIES / "figures"

    fig_tous = figure("", "Part des suppressions portée par les fiches les plus touchées",
                      "figure1-concentration.png")
    fig_sans = figure("-sans-enseignes",
                      "Même mesure, sans les six enseignes signalées",
                      "figure2-concentration-sans-enseignes.png")

    if args.doublons_cleaned:
        remplacer_dans(
            RACINE / "livrables" / "analyses-complémentaires.docx", fig_tous, fig_sans,
            base="Toute la base, avis de reviews_doublons_cleaned",
            note_tableau_1="% de suppression : suppressions du secteur divisées par ses avis. "
                           "Corpus : les avis présents dans reviews_doublons_cleaned.",
            definition="Suppression : même définition que la figure 4 du rapport (absence de "
                       "deux jours ou plus pour un avis revenu, bugs de réécriture retirés), "
                       "appliquée aux avis de reviews_doublons_cleaned.")
        return 0

    doc = Document()
    styler(doc)
    pied = doc.sections[0].footer.paragraphs[0]
    r = pied.add_run("ReviewFlowz · Suppressions par secteur et concentration · Septembre 2026")
    r.font.size = Pt(8.5); r.font.color.rgb = GR

    doc.add_paragraph("Suppressions par secteur et concentration", style="Title")
    doc.add_paragraph("ReviewFlowz · 28 septembre 2026", style="Subtitle")
    parties_1_2(doc, fig_tous, fig_sans, base="Toute la base",
                note_tableau_1="% de suppression : suppressions du secteur divisées par ses "
                               "avis. Chaque avis est compté une fois, d'où un écart de 14 à 145 "
                               "avis par secteur avec le tableau 1 du rapport.",
                definition="Suppression : même définition que la figure 4 du rapport (absence "
                           "de deux jours ou plus pour un avis revenu, bugs de réécriture retirés).")

    doc.core_properties.title = "Suppressions par secteur et concentration"
    doc.core_properties.author = "Cartelis"
    doc.save(LIVRABLE)
    print(f"ecrit : {LIVRABLE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
