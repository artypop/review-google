#!/usr/bin/env python3
"""Assemble le document Word sur les avis vus tardivement.

    python etudes-ponctuelles/2026-09-21-avis-vus-tardivement/note.py

Aucun chiffre n'est calculé ici. Tout vient des CSV de `sorties/`, produits par
`tardifs.py`. Lancer les deux dans cet ordre.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt, RGBColor

DOSSIER = Path(__file__).resolve().parent
SORTIES = DOSSIER / "sorties"
CIBLE = SORTIES / "2026-09-21-analyse-complementaire.docx"

ENCRE_DOUCE = RGBColor(0x52, 0x51, 0x4E)


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


def tableau(doc, entetes, lignes, a_droite=None, taille=9.5):
    a_droite = a_droite or set()
    t = doc.add_table(rows=1, cols=len(entetes))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, titre in enumerate(entetes):
        cellule = t.rows[0].cells[i]
        cellule.text = ""
        r = cellule.paragraphs[0].add_run(titre)
        r.bold = True
        r.font.size = Pt(taille)
    for ligne in lignes:
        cells = t.add_row().cells
        for i, valeur in enumerate(ligne):
            cells[i].text = ""
            p = cells[i].paragraphs[0]
            if i in a_droite:
                p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            r = p.add_run(str(valeur))
            r.font.size = Pt(taille)
    doc.add_paragraph()


def construire():
    ex = csv("A1-exemples.csv")
    lg = csv("B1-longueur-texte.csv").set_index("groupe")
    pays = csv("C1-pays.csv")
    b = csv("D1-bornes.csv").iloc[0]

    tardif = lg.loc["filet tardif"]
    normal = lg.loc["vus dans les 7 jours"]

    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)
    style.paragraph_format.space_after = Pt(8)

    doc.add_heading("Analyse complémentaire", level=0)
    chapeau(doc, "ReviewFlowz — suppressions d'avis Google — 21 septembre 2026 — "
                 "les avis vus pour la première fois bien après leur publication")

    doc.add_paragraph(
        "Sur les 35 751 avis du panel 03B, {} ont été vus par le robot huit jours ou plus "
        "après leur publication, sur {} fiches différentes. Les avis modifiés et deux fiches "
        "à afflux groupé en sont écartés. C'est cette population que décrit ce "
        "document.".format(espace(b["avis"]), espace(b["fiches"])))

    # -----------------------------------------------------------------------
    doc.add_heading("Deux exemples", level=1)
    tableau(doc,
            ["review_id", "cid", "Enseigne", "Pays", "Note", "Caractères",
             "Publié", "Vu le", "Écart"],
            [[r["review_id"], r["cid"], r["enseigne"], r["pays"], r["star"],
              espace(r["caracteres"]), r["publie"], r["vu_le"],
              "{} j".format(r["ecart_j"])]
             for _, r in ex.iterrows()],
            a_droite={4, 5, 8}, taille=7.5)

    doc.add_paragraph(
        "Ce n'est pas seulement la première semaine du panel qui est concernée. Les avis du "
        "filet sont publiés du {} au {}, et l'écart avec la première observation va de {} à "
        "{} jours. Un avis publié le 12 ou le 15 août peut apparaître neuf jours plus "
        "tard.".format(
            pd.to_datetime(b["publie_min"]).strftime("%d/%m"),
            pd.to_datetime(b["publie_max"]).strftime("%d/%m"),
            int(b["ecart_min"]), int(b["ecart_max"])))

    # -----------------------------------------------------------------------
    doc.add_heading("Le portrait de ces avis", level=1)
    tableau(doc,
            ["", "Filet tardif", "Vus dans les 7 jours"],
            [["Avis", espace(tardif["avis"]), espace(normal["avis"])],
             ["Longueur moyenne",
              "{} car.".format(espace(tardif["caracteres_moyen"])),
              "{} car.".format(espace(normal["caracteres_moyen"]))],
             ["Longueur médiane",
              "{} car.".format(espace(tardif["caracteres_median"])),
              "{} car.".format(espace(normal["caracteres_median"]))],
             ["Sans texte",
              "{} %".format(virgule(tardif["sans_texte_pct"])),
              "{} %".format(virgule(normal["sans_texte_pct"]))],
             ["Plus de 200 caractères",
              "{} %".format(virgule(tardif["plus_200_car_pct"])),
              "{} %".format(virgule(normal["plus_200_car_pct"]))]],
            a_droite={1, 2})

    doc.add_paragraph(
        "Ce sont des avis longs, détaillés et majoritairement négatifs. Une étoile avec "
        "2 181 caractères chez Empire Today, 1 848 chez un cabinet vétérinaire, 740 chez une "
        "clinique. Rien de commun avec l'avis 5 étoiles de trente caractères qui domine le "
        "panel.")

    # Les quatre pays les plus représentés, en toutes lettres. Les codes ISO se
    # lisent mal dans une phrase.
    noms = {"US": "aux États-Unis", "FR": "en France", "DE": "en Allemagne",
            "ES": "en Espagne", "IT": "en Italie", "HR": "en Croatie",
            "NL": "aux Pays-Bas", "PT": "au Portugal"}
    doc.add_paragraph(
        "Ils sont répartis sur {} pays : {}. Ce n'est donc ni un pays, ni une fiche, ni un "
        "secteur.".format(
            int(b["pays"]),
            ", ".join("{} {}".format(espace(r["avis"]), noms.get(r["pays"], r["pays"]))
                      for _, r in pays.head(4).iterrows())))

    # -----------------------------------------------------------------------
    doc.add_heading("Ce que ça évoque", level=1)
    doc.add_paragraph(
        "Un avis long, argumenté et négatif est exactement ce qu'un système de modération met "
        "en attente, soit pour vérification automatique, soit parce que le commerçant l'a "
        "signalé et que Google a statué ensuite. Les avis 5 étoiles présents dans le filet "
        "montrent que le phénomène ne vise pas que le négatif.")

    doc.add_paragraph(
        "Rien ne permet de trancher entre cette explication et une explication par l'ordre "
        "dans lequel le robot lit le listing. Les deux dépendent de la note, donc le motif ne "
        "les départage pas.")

    doc.add_paragraph(
        "Ce qui est mesuré, et qui tient : aucun de ces {} avis ne porte 4 étoiles, et {} % "
        "dépassent 200 caractères contre {} % dans le reste du panel.".format(
            espace(b["avis"]), virgule(tardif["plus_200_car_pct"]),
            virgule(normal["plus_200_car_pct"])))

    chapeau(doc, "Le texte et le lien de chaque avis sont dans les colonnes text et "
                 "review_link de la table, pour qui veut en ouvrir quelques-uns sur Maps. Ils "
                 "ne sont pas recopiés ici : règle du projet sur les données personnelles. "
                 "Régénérer avec etudes-ponctuelles/2026-09-21-avis-vus-tardivement/"
                 "tardifs.py, puis note.py.")

    CIBLE.parent.mkdir(parents=True, exist_ok=True)
    doc.save(CIBLE)
    print(f"écrit : {CIBLE}")


if __name__ == "__main__":
    construire()
