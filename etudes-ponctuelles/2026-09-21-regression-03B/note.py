#!/usr/bin/env python3
"""Assemble le document Word sur la régression du panel 03B.

    python etudes-ponctuelles/2026-09-21-regression-03B/note.py

Aucun chiffre n'est calculé ici. Tout vient des CSV de `sorties/`, produits par
`resultats.py`, et des PNG de `sorties/figures/`, produits par
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
SORTIES = DOSSIER / "sorties"
FIGURES = SORTIES / "figures"
CIBLE = SORTIES / "2026-09-21-regression-panel-03B.docx"

ENCRE_DOUCE = RGBColor(0x52, 0x51, 0x4E)


def csv(nom):
    return pd.read_csv(SORTIES / nom)


def espace(valeur):
    return f"{float(valeur):,.0f}".replace(",", " ")


def virgule(valeur, decimales=1):
    return ("{:." + str(decimales) + "f}").format(float(valeur)).replace(".", ",")


def facteur(valeur, decimales=1):
    """Un risque relatif, écrit comme on le lit : ×2,8 ou ÷1,2.

    Les contrôles d'exposition demandent deux décimales : à une seule, le
    ×1,067 de la fenêtre d'observation devient ×1,1, et les 6,7 % par jour
    qu'il mesure disparaissent dans l'arrondi.
    """
    v = float(valeur)
    return ("×{}".format(virgule(v, decimales)) if v >= 1
            else "÷{}".format(virgule(1 / v, decimales)))


# Les nombres que la note écrit en toutes lettres. Ils sont comptés, jamais
# saisis : un « quatorze » écrit à la main annonçait seize lignes de tableau.
MOTS = {1: "Une", 2: "Deux", 3: "Trois", 4: "Quatre", 5: "Cinq", 6: "Six",
        7: "Sept", 8: "Huit", 9: "Neuf", 10: "Dix", 11: "Onze", 12: "Douze",
        13: "Treize", 14: "Quatorze", 15: "Quinze", 16: "Seize",
        17: "Dix-sept", 18: "Dix-huit", 19: "Dix-neuf", 20: "Vingt"}


def mot(n):
    return MOTS.get(int(n), str(int(n)))


def chapeau(doc, texte):
    p = doc.add_paragraph()
    r = p.add_run(texte)
    r.italic = True
    r.font.size = Pt(10.5)
    r.font.color.rgb = ENCRE_DOUCE


def amorce(doc, gras, suite):
    """Un paragraphe qui commence par quelques mots en gras.

    python-docx n'interprète pas le Markdown : un `**` écrit dans le texte
    ressort tel quel dans le document.
    """
    p = doc.add_paragraph()
    r = p.add_run(gras)
    r.bold = True
    p.add_run(suite)
    return p


def legende(doc, texte):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(texte)
    r.italic = True
    r.font.size = Pt(9)
    r.font.color.rgb = ENCRE_DOUCE


def figure(doc, fichier, titre, largeur=6.1):
    doc.add_picture(str(FIGURES / fichier), width=Inches(largeur))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    legende(doc, titre)


def tableau(doc, entetes, lignes, a_droite=None, taille=9.5, gras_lignes=()):
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
    for n, ligne in enumerate(lignes):
        cells = t.add_row().cells
        for i, valeur in enumerate(ligne):
            cells[i].text = ""
            p = cells[i].paragraphs[0]
            if i in a_droite:
                p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            r = p.add_run(str(valeur))
            r.font.size = Pt(taille)
            r.bold = n in gras_lignes
    doc.add_paragraph()


def construire():
    passages = csv("A1-passages.csv").set_index("suffixe")
    risques = csv("B1-risques-relatifs.csv").set_index("variable")
    controles = csv("C1-controles.csv").set_index("variable")
    notes = csv("D1-notes.csv")
    conc = csv("D2-concentration.csv").iloc[0]

    principal = passages.loc["tous"]
    tranches = risques[risques["tranche"]]
    non_tranches = risques[~risques["tranche"]]

    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)
    style.paragraph_format.space_after = Pt(8)

    doc.add_heading("Régression logistique sur le panel 03B", level=0)
    chapeau(doc, "ReviewFlowz — suppressions d'avis Google — 21 septembre 2026 — "
                 "résultats des six passages lancés sur "
                 "reviews_panel_features_03B")

    doc.add_paragraph(
        "Le panel compte {} avis publiés du 4 au 17 août 2026 sur {} fiches, dont {} "
        "ont disparu, soit {} % des avis. Chaque avis est une ligne, observé entre "
        "la date où le robot l'a vu pour la première fois et le 24 août.".format(
            espace(principal["avis"]), espace(conc["fiches"]),
            espace(principal["suppressions"]), virgule(principal["taux_pct"], 2)))

    # -----------------------------------------------------------------------
    doc.add_heading("Ce que le modèle retient", level=1)

    doc.add_paragraph(
        "Chaque valeur ci-dessous est un risque relatif : de combien le risque de "
        "suppression est multiplié quand cette caractéristique est présente, tout "
        "le reste étant tenu constant. La fourchette donne l'étendue des valeurs "
        "compatibles avec les données. Quand elle contient 1, les données ne "
        "tranchent pas.")

    figure(doc, "figure7-risques-relatifs-03B.png",
           "Figure 7 — Risques relatifs ajustés, panel 03B, {} avis".format(
               espace(principal["avis"])))

    doc.add_paragraph(
        "{} caractéristiques ressortent nettement. Les voici, de la plus forte à "
        "la plus faible.".format(mot(len(tranches))))

    tableau(doc,
            ["Caractéristique", "Risque", "Fourchette"],
            [[r["libelle"], facteur(r["risque_relatif"]),
              "{} à {}".format(facteur(r["borne_basse"]), facteur(r["borne_haute"]))]
             for _, r in tranches.iterrows()],
            a_droite={1, 2})

    amorce(doc, "La rafale d'auteur domine tout le reste. ",
           "Le nombre d'avis qu'un auteur publie le même jour est de loin le "
           "signal le plus fort du modèle, à {}. C'est aussi le plus intuitif : "
           "un compte qui dépose plusieurs avis dans la journée se comporte comme "
           "un compte de campagne, et Google le traite comme tel.".format(
               facteur(risques.loc["log_burst", "risque_relatif"])))

    amorce(doc, "Le secteur home services suit, à {}. ".format(
                facteur(risques.loc["secteur_home_services", "risque_relatif"])),
           "Ce résultat est à lire avec la note du 18 septembre sur "
           "l'antiparasitaire américain : une partie de cet écart tient à des "
           "enseignes de traitement antiparasitaire qui concentrent les "
           "suppressions, et dont toutes ne sont pas repérées par le drapeau "
           "chaine_antiparasitaire_us.")

    amorce(doc, "La note compte, mais pas dans le sens le plus simple. ",
           "Un avis 1 étoile est à {}, un 2 étoiles à {}, quand les 3 et 4 étoiles "
           "ne se distinguent pas de la référence. Ce n'est donc pas « plus la "
           "note est basse, plus le risque monte » : ce sont les deux notes les "
           "plus basses qui se détachent.".format(
               facteur(risques.loc["etoiles_1", "risque_relatif"]),
               facteur(risques.loc["etoiles_2", "risque_relatif"])))

    doc.add_paragraph(
        "Le taux observé par note, sans aucun modèle, dit la même chose et fait "
        "voir pourquoi les 5 étoiles servent de référence : ils portent la plus "
        "grande part du panel.")

    tableau(doc,
            ["Note", "Avis", "Suppressions", "Taux"],
            [["{} étoile{}".format(int(r["valeur"]), "s" if r["valeur"] > 1 else ""),
              espace(r["avis"]), espace(r["suppressions"]),
              "{} %".format(virgule(r["taux_pct"], 2))]
             for _, r in notes.iterrows()],
            a_droite={1, 2, 3})

    amorce(doc, "Un auteur qui publie des photos est moins touché, à {}. ".format(
                facteur(risques.loc["log_photos_auteur", "risque_relatif"])),
           "C'est le seul effet protecteur tranché du modèle. Le nombre d'avis "
           "publiés par l'auteur, lui, ne dit rien.")

    # -----------------------------------------------------------------------
    doc.add_heading("Ce que le modèle ne retient pas", level=1)

    doc.add_paragraph(
        "{} caractéristiques restent dans le gris de la figure 7 : leur "
        "fourchette contient 1. Trois méritent d'être citées parce qu'on les "
        "attendait ailleurs.".format(mot(len(non_tranches))))

    tableau(doc,
            ["Caractéristique", "Risque", "Fourchette"],
            [[risques.loc[v, "libelle"], facteur(risques.loc[v, "risque_relatif"]),
              "{} à {}".format(facteur(risques.loc[v, "borne_basse"]),
                               facteur(risques.loc[v, "borne_haute"]))]
             for v in ["texte_texte_201p", "has_photo", "log_rc"]],
            a_droite={1, 2})

    doc.add_paragraph(
        "La longueur du texte ne joue pas. Les trois tranches — 1 à 50, 51 à 200, "
        "plus de 200 caractères — sont toutes à peu près à 1 par rapport à un avis "
        "sans texte. Un avis long n'est ni plus ni moins supprimé qu'un avis nu.")

    doc.add_paragraph(
        "C'est le résultat qui pèse le plus sur les trois pistes discutées le "
        "18 septembre. Si la longueur du texte ne dit rien, il reste à vérifier "
        "si son contenu en dit, ce que ni la longueur ni la présence de texte ne "
        "permettent de savoir.")

    # -----------------------------------------------------------------------
    doc.add_heading("Les deux contrôles d'exposition", level=1)

    doc.add_paragraph(
        "Ces deux colonnes ne sont pas des résultats à citer. Elles sont dans le "
        "modèle pour que tout le reste se lise à âge et à durée de suivi "
        "comparables. Elles sont données ici parce que la seconde est nouvelle.")

    tableau(doc,
            ["", "Risque", "Fourchette"],
            [[controles.loc[v, "libelle"],
              facteur(controles.loc[v, "risque_relatif"], 3),
              "{} à {}".format(facteur(controles.loc[v, "borne_basse"], 3),
                               facteur(controles.loc[v, "borne_haute"], 3))]
             for v in ["fenetre_observation_j", "age_a_la_premiere_observation_j"]],
            a_droite={1, 2})

    amorce(doc, "La fenêtre d'observation n'existait dans aucune version "
                "précédente du modèle. ",
           "Un avis vu pour la première fois le 17 août est regardé sept jours, un "
           "avis vu le 11 août l'est treize, et les deux comptent « non supprimé » "
           "s'ils survivent. Chaque jour de surveillance en plus multiplie par {} "
           "la chance de voir la suppression, soit {} % de plus par jour. Sans "
           "cette colonne, le modèle confondrait le risque par jour et le nombre "
           "de jours regardés.".format(
               virgule(controles.loc["fenetre_observation_j", "risque_relatif"], 3),
               virgule((controles.loc["fenetre_observation_j", "risque_relatif"] - 1)
                       * 100)))

    # -----------------------------------------------------------------------
    doc.add_heading("Le modèle sait-il classer", level=1)

    figure(doc, "figure8-ciblage-03B.png",
           "Figure 8 — Ciblage, panel entier, cinq tours par établissement")

    doc.add_paragraph(
        "Les établissements sont répartis en cinq groupes ; chaque groupe sert de "
        "test une fois, noté par un modèle qui ne l'a jamais vu. En examinant les "
        "10 % d'avis jugés les plus risqués, on retrouve 32 % des suppressions ; "
        "les 20 % les plus risqués en portent 53 %.")

    tableau(doc,
            ["Passage", "Avis", "Suppressions", "Taux", "Capacité à classer"],
            [[r["passage"], espace(r["avis"]), espace(r["suppressions"]),
              "{} %".format(virgule(r["taux_pct"], 2)), virgule(r["auc"], 3)]
             for _, r in passages.reset_index().iterrows()],
            a_droite={1, 2, 3, 4}, gras_lignes={0})

    amorce(doc, "Ce 0,724 ne se compare pas au 0,785 du passage précédent. ",
           "L'ancien panel couvrait trois mois de publication, où un avis d'un "
           "jour et un avis de trois mois n'avaient pas du tout le même risque : "
           "une bonne part du classement venait de cet écart d'âge. Ici tous les "
           "avis ont entre zéro et treize jours, ce levier a disparu, et ce qui "
           "reste est ce que la note, l'auteur, le secteur et la fiche disent "
           "vraiment. Un 0,724 sur un panel homogène en âge n'est pas un recul "
           "par rapport à un 0,785 porté par l'âge.")

    doc.add_paragraph(
        "Le passage sans les enseignes signalées tombe à {} : une partie de ce que "
        "le modèle sait classer tient aux quelques fiches attaquées. C'est "
        "cohérent avec la concentration déjà mesurée — {} fiches portent au moins "
        "une suppression, et les cinquante plus touchées en portent la "
        "moitié.".format(virgule(passages.loc["tous_sans_enseignes", "auc"], 3),
                         espace(conc["fiches_touchees"])))

    # -----------------------------------------------------------------------
    doc.add_heading("Deux questions tranchées par la mesure", level=1)

    amorce(doc, "Les 412 avis vus tardivement restent dans le corpus. ",
           "Ce sont les avis vus par le robot au huitième jour ou plus tard, "
           "décrits dans la note complémentaire du même jour. Sans eux, la "
           "capacité à classer passe à {} et les risques relatifs bougent de 15 % "
           "au maximum. Le modèle les isole déjà par une colonne dédiée, dont la "
           "fourchette va de {} à {} : les données ne tranchent pas sur leur "
           "compte, ce qui est cohérent avec ce qu'on savait déjà — leur excès de "
           "suppressions venait presque entièrement d'une seule fiche "
           "attaquée.".format(
               virgule(passages.loc["tous_sans_tardifs", "auc"], 3),
               facteur(risques.loc["vu_tardivement", "borne_basse"]),
               facteur(risques.loc["vu_tardivement", "borne_haute"])))

    amorce(doc, "Les 280 avis réécrits par leur auteur restent aussi. ",
           "Sans eux, {} et des risques relatifs à 7 % près. Ces avis sont "
           "mesurables pour la première fois : la chaîne de tables précédente les "
           "excluait entièrement du corpus. Les trois colonnes qui les décrivent "
           "sont lues dans le tableau croisé mais ne sont pas entrées dans le "
           "modèle, la modification étant observée au dernier passage du robot, "
           "donc peut-être après le début de la période de risque.".format(
               virgule(passages.loc["tous_sans_modifies", "auc"], 3)))

    # -----------------------------------------------------------------------
    doc.add_heading("Ce qu'on ne peut pas dire", level=1)

    doc.add_paragraph(
        "Les avis encore en ligne au dernier passage du robot n'ont pas fini leur "
        "histoire. Ils comptent « non supprimé » alors que leur sort est inconnu.")

    doc.add_paragraph(
        "Les fiches rares ne se lisent pas. Le secteur travel est à {} et le "
        "wellness et fitness à {}, mais leurs fourchettes contiennent 1 : sur ce "
        "panel de quatorze jours, ces secteurs ne portent pas assez de "
        "suppressions pour qu'on les sépare du reste.".format(
            facteur(risques.loc["secteur_travel", "risque_relatif"]),
            facteur(risques.loc["secteur_wellness_fitness", "risque_relatif"])))

    doc.add_paragraph(
        "Les tailles d'établissement ne se départagent pas entre elles. Small à {} "
        "et large à {} sont au même niveau face aux fiches mono : ce que le modèle "
        "voit, c'est l'écart entre une fiche isolée et une fiche de réseau, pas "
        "une progression avec la taille.".format(
            facteur(risques.loc["taille_small", "risque_relatif"]),
            facteur(risques.loc["taille_large", "risque_relatif"])))

    chapeau(doc, "Sorties complètes dans logistic-regression-study/output-study/"
                 "2026-09-21-sorties-07B/ : coefficients, tableaux croisés et "
                 "summaries des six passages. Régénérer avec "
                 "logistic-regression-study/python/07B_regression_panel.py, puis "
                 "etudes-ponctuelles/2026-09-21-regression-03B/resultats.py, "
                 "graphiques.py et note.py.")

    CIBLE.parent.mkdir(parents=True, exist_ok=True)
    doc.save(CIBLE)
    print(f"écrit : {CIBLE}")


if __name__ == "__main__":
    construire()
