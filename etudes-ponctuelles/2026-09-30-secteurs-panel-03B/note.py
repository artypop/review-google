#!/usr/bin/env python3
"""Assemble le document Word à partir des CSV de `calcul.py`.

    PYTHONPATH=.venv/Lib/site-packages <python uv> etudes-ponctuelles/2026-09-30-secteurs-panel-03B/note.py

Aucun chiffre n'est calculé ici. Sortie :
`livrables/2026-09-30-secteurs-panel-03B.docx`. Mise en page et tableaux repris
de `2026-09-28-secteurs-et-concentration/note.py` (tableaux 1 et 2 de
`livrables/analyses-complémentaires.docx`), recopiés sans pandas.
"""
from __future__ import annotations

import csv
from pathlib import Path

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

DOSSIER = Path(__file__).resolve().parent
RACINE = DOSSIER.parent.parent
SORTIES = DOSSIER / "sorties"
LIVRABLE = RACINE / "livrables" / "2026-09-30-secteurs-panel-03B.docx"

ORDRE_SECTEURS = ["Automobile", "Services à domicile", "Santé", "Sport et bien-être",
                  "Restauration", "Voyage", "Hôtellerie"]

NAVY = RGBColor(0x32, 0x29, 0x54); ENC = RGBColor(0x1F, 0x1F, 0x1F); GR = RGBColor(0x6B, 0x6A, 0x66)
POLICE = "Calibri"


def lire(nom):
    with open(SORTIES / nom, encoding="utf-8") as f:
        return {r["secteur_fr"]: r for r in csv.DictReader(f)}


def virgule(x, d=1):
    return f"{float(x):.{d}f}".replace(".", ",")


def espace(n):
    return f"{int(n):,}".replace(",", " ")


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
            ("Heading 1", 16, 18, 8, NAVY, True), ("Title", 24, 0, 4, NAVY, True)):
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
    tt = st.add_style("TitreTableau", 1)
    tt.base_style = n; tt.font.size = Pt(9.5); tt.font.bold = True; tt.font.color.rgb = NAVY
    tt.paragraph_format.space_before = Pt(10); tt.paragraph_format.keep_with_next = True
    nt = st.add_style("NoteTableau", 1)
    nt.base_style = n; nt.font.size = Pt(9); nt.font.color.rgb = GR
    nt.paragraph_format.space_after = Pt(10)


def fond(cell, couleur):
    sh = OxmlElement("w:shd")
    sh.set(qn("w:val"), "clear"); sh.set(qn("w:color"), "auto"); sh.set(qn("w:fill"), couleur)
    cell._tc.get_or_add_tcPr().append(sh)


def tableau(doc, titre, entetes, lignes, largeurs, gras_derniere=True):
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


def lignes_secteurs(d):
    out = []
    for s in ORDRE_SECTEURS:
        r = d[s]
        out.append([s, espace(r["avis"]), f"{virgule(r['part_corpus_pct'])} %",
                    espace(r["suppressions"]), f"{virgule(r['part_supprimee_pct'], 2)} %"])
    tot_a = sum(int(r["avis"]) for r in d.values())
    tot_s = sum(int(r["suppressions"]) for r in d.values())
    out.append(["Total", espace(tot_a), "100 %", espace(tot_s),
                f"{virgule(100 * tot_s / tot_a, 2)} %"])
    return out, tot_a, tot_s


ENTETES = ["Secteur", "Avis du secteur", "% du corpus", "Nombre de suppressions",
           "% de suppression"]
LARGEURS = [4.0, 3.0, 2.6, 3.4, 3.0]


def lignes_csv(nom):
    with open(SORTIES / nom, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def pour_10000(s, n):
    return espace(round(10000 * int(s) / int(n))) if int(n) else "-"


def risque(r):
    if not r["risque_relatif"]:
        return "Trop peu de suppressions", ""
    return (f"×{virgule(r['risque_relatif'], 2)}",
            f"{virgule(r['borne_basse'], 2)} à {virgule(r['borne_haute'], 2)}")


def lignes_jours(rangees):
    out = []
    for r in rangees:
        rr, fourchette = risque(r)
        out.append([f"Jour {r['jour_reponse']}", espace(r["avis"]), espace(r["avis_repondu"]),
                    f"{r['suppr_repondu']} ({pour_10000(r['suppr_repondu'], r['avis_repondu'])})",
                    pour_10000(r["suppr_sans_reponse"], r["avis_sans_reponse"]),
                    rr, fourchette])
    return out


ENTETES_JOURS = ["Jour de la réponse", "Avis retenus", "Répondus ce jour-là",
                 "Suppressions des répondus (pour 10 000)", "Pour 10 000 non répondus",
                 "Risque", "Fourchette"]
LARGEURS_JOURS = [2.4, 2.0, 2.2, 3.0, 2.4, 2.4, 2.2]


def puce(doc, texte):
    doc.add_paragraph(texte, style="List Bullet")


def section_reponse(doc):
    doc.add_heading("2. Réponse du commerçant : le jour où elle arrive", level=1)

    r0s = {r["habitude"]: r for r in lignes_csv("R0-rejeu-037.csv")}
    r0, r1 = r0s["plus_de_75"], r0s["25_75"]
    doc.add_paragraph(
        "Rappel du tableau 14 du rapport. Réponses datées du jour de l'avis ou des deux jours "
        "calendaires suivants (délai de 0, 1 ou 2 jours, soit moins de 72 heures), relevées au "
        "2ᵉ jour. Suppressions comptées du 3ᵉ au 8ᵉ jour. Avis publiés du 10 au 16 août, vus par "
        "le robot le jour même ou le lendemain, sans les enseignes signalées : "
        f"{espace(r0['avis_au_jalon'])} avis en ligne au 2ᵉ jour, {r0['suppressions']} suppressions.")
    tableau(doc, "Tableau 3. Effet d'une réponse arrivée dans les 2 jours, selon l'habitude de la fiche",
            ["Habitude de la fiche", "Effet de la réponse", "Fourchette"],
            [["Fiches qui répondent à plus de 75 %",
              f"×{virgule(r0['risque_relatif'], 2)}",
              f"{virgule(r0['borne_basse'], 2)} à {virgule(r0['borne_haute'], 2)}"],
             ["Fiches qui répondent à 25 à 75 %", f"×{virgule(r1['risque_relatif'], 2)}",
              f"{virgule(r1['borne_basse'], 2)} à {virgule(r1['borne_haute'], 2)}"],
             ["Fiches qui répondent à moins de 25 %", "Écartée, trop peu de suppressions", ""]],
            [6.0, 5.0, 3.0], gras_derniere=False)
    doc.add_paragraph(
        "Sur les fiches qui répondent à plus de 75 %, un avis répondu dans les 2 jours est "
        "supprimé 2,7 fois moins souvent qu'un avis de la même tranche resté sans réponse. "
        "Recalculé en local le 2026-09-30 : mêmes effectifs, même ×0,37.", style="NoteTableau")

    doc.add_paragraph("Dispositif", style="TitreTableau")
    puce(doc, "Avis publiés du 9 au 16 août, de J-2 à J+5, J étant le premier relevé du 11 août. "
              "Les avis du 17 août (J+6) sont écartés : le dernier relevé, le 24 août, ne les "
              "suit que 7 jours.")
    puce(doc, "Pour chaque jour k, de 0 (le jour de l'avis) à 6 : on garde les avis encore en "
              "ligne au jour k et sans réponse avant ce jour. On compare ceux qui reçoivent leur "
              "réponse exactement le jour k à ceux qui n'en ont toujours pas.")
    puce(doc, "Suppressions comptées du jour k+1 au jour 8. Un avis encore en ligne au jour 8 "
              "compte comme conservé.")
    puce(doc, "Un avis n'entre au jour k que si le robot l'a vu au plus tard à cet âge. Les avis "
              "du 9 août, vus pour la première fois le 11, entrent à partir du jour 2. Au jour 0, "
              "seuls restent les avis vus le jour de leur publication.")
    puce(doc, "Même modèle et mêmes variables que le tableau 3, sans les enseignes signalées.")

    tableau(doc, "Tableau 4. Effet d'une réponse selon le jour où elle arrive, toutes les fiches",
            ENTETES_JOURS, lignes_jours(lignes_csv("R1-jour-reponse.csv")), LARGEURS_JOURS,
            gras_derniere=False)
    doc.add_paragraph(
        "Risque : suppressions d'un avis répondu ce jour-là, rapportées à celles d'un avis encore "
        "sans réponse, à note, auteur, secteur, taille de fiche et habitude de réponse comparables. "
        "Les taux baissent d'une ligne à l'autre parce que la période de suivi raccourcit : ils se "
        "comparent au sein d'une même ligne.", style="NoteTableau")

    par_hab = lignes_csv("R2-jour-reponse-par-habitude.csv")
    tableau(doc, "Tableau 5. Même mesure, fiches qui répondent à plus de 75 %",
            ENTETES_JOURS, lignes_jours([r for r in par_hab if r["habitude"] == "plus_de_75"]),
            LARGEURS_JOURS, gras_derniere=False)
    tableau(doc, "Tableau 6. Même mesure, fiches qui répondent à 25 à 75 %",
            ENTETES_JOURS, lignes_jours([r for r in par_hab if r["habitude"] == "25_75"]),
            LARGEURS_JOURS, gras_derniere=False)
    doc.add_paragraph("Fiches qui répondent à moins de 25 % : trop peu d'avis répondus pour "
                      "une ligne.", style="NoteTableau")

    doc.add_paragraph("À retenir", style="TitreTableau")
    puce(doc, "Réponse le lendemain de l'avis (jour 1) : risque divisé par 1,8 sur toutes les "
              "fiches (×0,57, de 0,35 à 0,91) et par 2,3 sur les fiches qui répondent à plus de "
              "75 % (×0,43, de 0,27 à 0,67).")
    puce(doc, "Réponse au jour 2 : ×0,53 sur toutes les fiches, fourchette de 0,26 à 1,06 qui "
              "contient 1. Sur les fiches à plus de 75 % : ×0,39, de 0,18 à 0,83.")
    puce(doc, "Réponse le jour même (jour 0) : ×0,45, de 0,15 à 1,37. 10 suppressions parmi les "
              "503 avis répondus, trop peu pour trancher.")
    puce(doc, "Réponse au jour 3 : aucune suppression parmi les 706 avis répondus. Au taux des "
              "avis sans réponse, on en attendrait environ 17. Le modèle ne chiffre pas un effet "
              "calculé sur zéro suppression.")
    puce(doc, "Jours 4 à 6 : 7, 3 et 0 suppressions parmi les avis répondus. Seul le jour 4 se "
              "chiffre (×0,63, de 0,28 à 1,38).")
    puce(doc, "Sur les fiches qui répondent de 25 à 75 %, la réponse du jour 1 va dans l'autre "
              "sens (×2,11, de 0,93 à 4,79), comme dans le tableau 3.")
    puce(doc, "Jusqu'au 2ᵉ jour, l'effet mesuré sur les fiches à plus de 75 % reste proche du "
              "×0,37. Au-delà, le nombre de suppressions ne permet pas de dire si l'effet "
              "diminue avec le délai.")

    doc.add_paragraph("Réserves", style="TitreTableau")
    puce(doc, "Une réponse publiée après le dernier passage où l'avis était visible n'est jamais "
              "vue. Un avis répondu le jour k et disparu avant le relevé suivant compte donc "
              "comme non répondu et supprimé. Ce cas grossit l'effet protecteur ; son poids n'est "
              "pas mesuré.")
    puce(doc, "Une réponse retirée est invisible : changed_fields ne suit pas la réponse.")
    puce(doc, "Le sens de la relation n'est pas établi : le commerçant qui répond est souvent "
              "celui qui signale.")
    puce(doc, "Délai compté en jours calendaires UTC : une réponse du jour 1 arrive entre "
              "quelques minutes et 48 heures après l'avis.")
    doc.add_paragraph("Régénérer : reponse_delai.py puis note.py, dossier "
                      "etudes-ponctuelles/2026-09-30-secteurs-panel-03B.", style="NoteTableau")


def main() -> int:
    tous, tot_a, tot_s = lignes_secteurs(lire("A1-secteurs.csv"))
    sans, sans_a, sans_s = lignes_secteurs(lire("A1-secteurs-sans-enseignes.csv"))

    doc = Document()
    styler(doc)
    doc.add_paragraph("Panel 03B, analyses complémentaires", style="Title")
    doc.add_heading("1. Suppressions par secteur", level=1)
    doc.add_paragraph(
        "Panel 03B : avis publiés du 4 au 17 août 2026, suivis jusqu'au relevé du 24 août. "
        f"{espace(tot_a)} avis sur 5 566 fiches, {espace(tot_s)} suppressions.")
    tableau(doc, "Tableau 1. Avis et suppressions par secteur", ENTETES, tous, LARGEURS)
    doc.add_paragraph("% de suppression : suppressions du secteur divisées par ses avis. "
                      "Corpus : les avis du panel 03B.", style="NoteTableau")
    tableau(doc, "Tableau 2. Même tableau, sans les six enseignes signalées",
            ENTETES, sans, LARGEURS)
    doc.add_paragraph(
        "Enseignes signalées : les 4 chaînes antiparasitaires américaines (services à "
        "domicile), succursales comprises, et les 2 salles de sport espagnoles attaquées "
        f"(sport et bien-être). Retirés : {espace(tot_a - sans_a)} avis et "
        f"{espace(tot_s - sans_s)} suppressions.", style="NoteTableau")
    doc.add_paragraph(
        "Régénérer : calcul.py puis note.py, dossier "
        "etudes-ponctuelles/2026-09-30-secteurs-panel-03B.", style="NoteTableau")

    section_reponse(doc)

    LIVRABLE.parent.mkdir(parents=True, exist_ok=True)
    doc.save(LIVRABLE)
    print(f"Écrit : {LIVRABLE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
