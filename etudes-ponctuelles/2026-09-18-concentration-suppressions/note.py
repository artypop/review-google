#!/usr/bin/env python3
"""Assemble le document Word sur la concentration des suppressions.

    python etudes-ponctuelles/2026-09-18-concentration-suppressions/note.py

Aucun chiffre n'est calculé ici. Tout vient des CSV de `sorties/`, produits par
`concentration.py`, et de la figure de `matthieu/figures/`, produite par
`graphiques.py`. Lancer les trois dans cet ordre.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor

DOSSIER = Path(__file__).resolve().parent
RACINE = DOSSIER.parent.parent
SORTIES = DOSSIER / "sorties"
MATTHIEU = RACINE / "matthieu"
FIGURES = MATTHIEU / "figures"
CIBLE = MATTHIEU / "2026-09-18-concentration-des-suppressions.docx"

ENCRE_DOUCE = RGBColor(0x52, 0x51, 0x4E)

SECTEURS_FR = {
    "home_services": "Services à domicile", "healthcare": "Santé",
    "automotive": "Automobile", "wellness_fitness": "Sport et bien-être",
    "travel": "Voyage", "food_beverage": "Restauration", "hospitality": "Hôtellerie",
}


def csv(nom):
    return pd.read_csv(SORTIES / nom)


def espace(valeur):
    return f"{float(valeur):,.0f}".replace(",", " ")


def virgule(valeur, decimales=1):
    return ("{:." + str(decimales) + "f}").format(float(valeur)).replace(".", ",")


def chapeau(doc, texte):
    p = doc.add_paragraph()
    r = p.add_run(texte)
    r.italic = True
    r.font.size = Pt(10.5)
    r.font.color.rgb = ENCRE_DOUCE


def figure(doc, fichier, legende):
    doc.add_picture(str(FIGURES / fichier), width=Inches(6.3))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(legende)
    r.font.size = Pt(9)
    r.font.color.rgb = ENCRE_DOUCE


def tableau(doc, entetes, lignes, a_droite=None):
    a_droite = a_droite or set()
    t = doc.add_table(rows=1, cols=len(entetes))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, titre in enumerate(entetes):
        cellule = t.rows[0].cells[i]
        cellule.text = ""
        r = cellule.paragraphs[0].add_run(titre)
        r.bold = True
        r.font.size = Pt(9.5)
    for ligne in lignes:
        cells = t.add_row().cells
        for i, valeur in enumerate(ligne):
            cells[i].text = ""
            p = cells[i].paragraphs[0]
            if i in a_droite:
                p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            r = p.add_run(str(valeur))
            r.font.size = Pt(9.5)
    doc.add_paragraph()


def construire():
    cadre = csv("A1-cadre.csv").set_index("mesure")["valeur"]
    conc = csv("B1-concentration.csv")
    seuils = csv("B2-seuils.csv").set_index("mesure")["valeur"]
    fiches = csv("C1-fiches.csv")
    paquets = csv("D1-paquets.csv")

    n_fiches = int(cadre["fiches suivies"])
    n_touchees = int(cadre["fiches ayant perdu au moins un avis"])
    n_suppr = int(cadre["suppressions"])
    moitie = int(seuils["fiches portant la moitié des suppressions"])
    quart = int(seuils["fiches portant le quart des suppressions"])
    trois_quarts = int(seuils["fiches portant les trois quarts des suppressions"])
    l20 = conc[conc["fiches_les_plus_touchees"] == 20].iloc[0]
    l905 = conc[conc["fiches_les_plus_touchees"] == 905].iloc[0]
    gros = paquets[paquets["paquet"].str.startswith(("d.", "e."))]

    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)
    style.paragraph_format.space_after = Pt(8)

    doc.add_heading("Les suppressions se concentrent-elles sur quelques fiches ?", level=0)
    chapeau(doc, "ReviewFlowz — suppressions d'avis Google — 18 septembre 2026 — "
                 "{} suppressions sur {} fiches, du 11 au 24 août 2026"
                 .format(espace(n_suppr), espace(n_fiches)))

    # -----------------------------------------------------------------------
    doc.add_heading("La réponse en une phrase", level=1)
    doc.add_paragraph(
        "{} fiches sur {} portent la moitié des {} suppressions. Si les suppressions "
        "tombaient au hasard, proportionnellement au nombre d'avis de chaque fiche, il en "
        "faudrait environ {} pour atteindre la même moitié.".format(
            moitie, espace(n_fiches), espace(n_suppr),
            espace(int(l905["fiches_les_plus_touchees"]))))
    doc.add_paragraph(
        "Autrement dit, la moitié des suppressions se joue sur douze fois moins de fiches que "
        "ce que la taille des fiches laisserait attendre. La concentration est donc réelle, et "
        "elle ne vient pas de ce que certaines fiches ont beaucoup plus d'avis que d'autres.")

    figure(doc, "figure4-concentration-suppressions.png",
           "Figure — Part cumulée des suppressions, des fiches les plus touchées aux moins "
           "touchées.")

    # -----------------------------------------------------------------------
    doc.add_heading("Le détail chiffré", level=1)
    tableau(doc,
            ["Les N fiches les plus touchées", "Part observée des suppressions",
             "Part si les suppressions suivaient la taille des fiches"],
            [[espace(r["fiches_les_plus_touchees"]),
              "{} %".format(virgule(r["part_observee_pct"])),
              "{} %".format(virgule(r["part_attendue_pct"]))]
             for _, r in conc.iterrows()
             if r["fiches_les_plus_touchees"] in (1, 5, 10, 20, 50, 100, 200, 500)],
            a_droite={0, 1, 2})
    doc.add_paragraph(
        "Deux lectures utiles. Les {} fiches les plus touchées portent {} % des suppressions "
        "quand leur taille leur en donnerait {} %. Et {} fiches suffisent à porter le quart du "
        "total, {} à en porter les trois quarts.".format(
            espace(l20["fiches_les_plus_touchees"]), virgule(l20["part_observee_pct"]),
            virgule(l20["part_attendue_pct"]), quart, trois_quarts))

    doc.add_paragraph(
        "L'autre bout de la distribution compte autant : {} fiches sur {} n'ont perdu aucun "
        "avis, soit {} %. La suppression est un événement rare et groupé.".format(
            espace(n_fiches - n_touchees), espace(n_fiches),
            virgule(100.0 * (n_fiches - n_touchees) / n_fiches)))

    # -----------------------------------------------------------------------
    doc.add_heading("Combien de suppressions par fiche touchée", level=1)
    tableau(doc,
            ["Suppressions sur la fiche", "Fiches", "Suppressions", "Part du total"],
            [[r["paquet"][3:], espace(r["fiches"]), espace(r["suppressions"]),
              "{} %".format(virgule(r["part_du_total_pct"]))]
             for _, r in paquets.iterrows()],
            a_droite={1, 2, 3})
    doc.add_paragraph(
        "Les {} fiches qui perdent dix avis ou plus portent {} % des suppressions. À l'opposé, "
        "{} fiches n'en perdent qu'une seule et portent ensemble {} % du total.".format(
            espace(gros["fiches"].sum()), virgule(gros["part_du_total_pct"].sum()),
            espace(paquets.iloc[0]["fiches"]), virgule(paquets.iloc[0]["part_du_total_pct"])))

    # -----------------------------------------------------------------------
    doc.add_heading("Quelles fiches", level=1)
    tableau(doc,
            ["Enseigne", "Secteur", "Pays", "Avis", "Suppressions", "Part de son stock",
             "Part du total"],
            [[r["enseigne"], SECTEURS_FR.get(r["secteur"], r["secteur"]), r["pays"],
              espace(r["avis"]), espace(r["suppressions"]),
              "{} %".format(virgule(r["part_du_stock_pct"])),
              "{} %".format(virgule(r["part_du_total_pct"], 2))]
             for _, r in fiches.head(10).iterrows()],
            a_droite={3, 4, 5, 6})
    doc.add_paragraph(
        "Les deux premières sont les salles de sport espagnoles attaquées, déjà documentées : "
        "{} suppressions à elles deux, soit {} % du total. Les suivantes sont les chaînes "
        "américaines de traitement antiparasitaire, également déjà repérées. Ces deux groupes "
        "sont connus ; le reste de la liste ne l'est pas, et c'est là que se trouve le travail "
        "qui reste.".format(
            espace(fiches.head(2)["suppressions"].sum()),
            virgule(fiches.head(2)["part_du_total_pct"].sum())))

    # -----------------------------------------------------------------------
    doc.add_heading("Ce que ces chiffres ne disent pas", level=1)
    for puce in [
        "Une fiche très touchée n'est pas forcément une fiche attaquée. L'attaque par faux "
        "avis, le retrait obtenu sur demande du commerçant et le tri automatique produisent le "
        "même motif dans les données.",
        "La comparaison au tirage proportionnel suppose qu'à taille égale toutes les fiches "
        "courent le même risque. Le secteur, le pays et l'âge des avis ne sont pas tenus "
        "constants ici ; une partie de l'écart vient donc de là.",
        "Les {} fiches suivies sont celles qui portent au moins un avis. Le panel en compte "
        "{}, dont {} sans aucun avis dans la table.".format(
            espace(n_fiches), "9 048", espace(9048 - n_fiches)),
        "On ne voit que quatorze jours. Une fiche épargnée pendant le suivi a pu être purgée "
        "avant le 11 août.",
    ]:
        doc.add_paragraph(puce, style="List Bullet")

    chapeau(doc, "Définition d'une suppression : etude-exploratoire/scripts/"
                 "suppressions_corrigees.py, importée telle quelle — absence de deux jours ou "
                 "plus, bugs d'enregistrement retirés. Régénérer avec "
                 "etudes-ponctuelles/2026-09-18-concentration-suppressions/concentration.py")

    MATTHIEU.mkdir(parents=True, exist_ok=True)
    doc.save(CIBLE)
    print(f"écrit : {CIBLE}")


if __name__ == "__main__":
    construire()
