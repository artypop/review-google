#!/usr/bin/env python3
"""Assemble la note d'arbitrage sur les trois pistes proposées le 2026-09-18.

    python etudes-ponctuelles/2026-09-18-pistes-analyse/note.py

Aucun calcul n'est lancé et aucun chiffre n'est produit ici. Tout ce qui est
chiffré dans la note vient de la documentation du projet, citée à côté :

    docs/03-resultats.md                                   § 2, § 4, § 5, § 6
    docs/01-etude.md                                       § 5
    docs/02-donnees.md                                     § 2
    docs/BACKLOG.md                                        points 1 et L5
    logistic-regression-study/output-study/
        2026-09-16-interpretation-controle-xgboost.md      § 1.A
"""
from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt, RGBColor

DOSSIER = Path(__file__).resolve().parent
SORTIES = DOSSIER / "sorties"
CIBLE = SORTIES / "2026-09-18-trois-pistes.docx"

ENCRE_DOUCE = RGBColor(0x52, 0x51, 0x4E)


def chapeau(doc, texte):
    p = doc.add_paragraph()
    r = p.add_run(texte)
    r.italic = True
    r.font.size = Pt(10.5)
    r.font.color.rgb = ENCRE_DOUCE


def verdict(doc, texte):
    p = doc.add_paragraph()
    r = p.add_run(texte)
    r.bold = True


def sous_titre(doc, texte):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(2)
    r = p.add_run(texte)
    r.bold = True
    r.font.size = Pt(10.5)


def puces(doc, lignes):
    for ligne in lignes:
        doc.add_paragraph(ligne, style="List Bullet")


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
    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)
    style.paragraph_format.space_after = Pt(8)

    doc.add_heading("Trois pistes pour aller plus loin", level=0)
    chapeau(doc,
            "ReviewFlowz — suppressions d'avis Google — 18 septembre 2026 — "
            "note d'arbitrage, aucun calcul lancé")

    # -----------------------------------------------------------------------
    doc.add_heading("Ce qu'il faut retenir", level=1)
    puces(doc, [
        "La réponse du propriétaire est à traiter en premier. Coût faible, c'est la question "
        "du client d'Axel, et la réserve qui affaiblit le résultat actuel se referme avec les "
        "données en main.",
        "Les textes qui se ressemblent forment la piste la plus prometteuse, à une condition : "
        "comparer les avis à l'intérieur d'une même fiche. Comparés globalement, ils "
        "produiront des marqueurs faux.",
        "L'embedding est un bon outil de recherche au service de la piste précédente. Ajouté "
        "comme colonnes au modèle, le gain attendu est proche de zéro.",
        "Les deux premières pistes reposent sur le même montage, la comparaison entre avis "
        "d'une même fiche. Construit une fois, il sert les deux.",
    ])

    # -----------------------------------------------------------------------
    doc.add_heading("Pourquoi on cherche autre chose", level=1)
    doc.add_paragraph(
        "Présenté avec un avis supprimé et un avis resté en ligne tirés au hasard, le modèle "
        "actuel donne le score le plus élevé au bon dans 86 % des cas. Sans l'âge de l'avis, "
        "qui sert de correction et non de résultat, il tombe à 72 %.")
    doc.add_paragraph(
        "Un modèle d'arbres de décision nourri du texte des avis donne 86,6 % sur le même "
        "corpus, et exactement le même chiffre que la régression une fois les six enseignes "
        "signalées retirées. Le plafond vient donc des colonnes disponibles. Changer "
        "d'algorithme n'apporte plus rien.")
    chapeau(doc, "Sources : docs/03-resultats.md § 6 et "
                 "output-study/2026-09-16-interpretation-controle-xgboost.md § 1.A")

    # -----------------------------------------------------------------------
    doc.add_heading("Piste 1 — Transformer les textes en nombres (embedding)", level=1)
    doc.add_paragraph(
        "Le principe : chaque texte d'avis devient une suite de nombres qui rapproche les "
        "textes de sens voisin, quelle que soit la langue.")
    verdict(doc, "Verdict : bon outil de recherche, mauvais ajout au modèle.")

    sous_titre(doc, "Pourquoi c'est une mauvaise idée comme entrée du modèle")
    puces(doc, [
        "Le test voisin a déjà été passé le 16 septembre. Un modèle d'arbres nourri de 50 mots "
        "tirés du texte classe correctement 86,6 % des paires, contre 86,0 % pour la "
        "régression sans aucun texte. Une fois les six enseignes retirées, les deux donnent "
        "exactement le même chiffre.",
        "30 % des avis supprimés n'ont aucun texte. Une piste qui laisse de côté le tiers de "
        "la cible ne peut pas porter l'étude.",
        "Un embedding encode la langue, le registre et le vocabulaire de métier. Sur un corpus "
        "où le secteur et la région dominent, il réapprendra « services à domicile, en "
        "anglais » et affichera un bon score sans rien expliquer. Le projet a déjà connu cette "
        "erreur avec la variable de langue étrangère, qui mesurait en réalité le tourisme.",
        "S'il fait beaucoup monter le score, c'est le signe qu'il relit le secteur. Le seul "
        "montage où un gain serait interprétable est la comparaison entre avis d'une même "
        "fiche, où le secteur et le pays s'annulent.",
    ])

    sous_titre(doc, "Pourquoi c'est une bonne idée comme outil")
    puces(doc, [
        "Regrouper les avis supprimés par ressemblance et décrire les paquets obtenus, ce qui "
        "donne une typologie lisible.",
        "Retrouver, pour un avis supprimé, les avis restés en ligne qui lui ressemblent le "
        "plus. C'est le cœur de la piste 2.",
        "Repérer les gabarits — même structure, mots différents — que la recherche de doublons "
        "exacts laisse passer.",
    ])

    sous_titre(doc, "Une contrainte pratique")
    doc.add_paragraph(
        "Le fichier de licence de l'export interdit la rediffusion des données, et les textes "
        "d'avis sont des données personnelles. Passer 226 000 textes dans un service extérieur "
        "revient à les transmettre à un tiers. Le calcul doit se faire avec un modèle installé "
        "sur la machine, ce qui demande quelques heures.")

    # -----------------------------------------------------------------------
    doc.add_heading("Piste 2 — Comparer les textes supprimés aux textes restés en ligne", level=1)
    verdict(doc, "Verdict : la plus prometteuse des trois. Tout se joue sur le périmètre de "
                 "comparaison.")

    sous_titre(doc, "Pourquoi c'est une bonne idée")
    puces(doc, [
        "C'est la seule des trois pistes qui puisse expliquer les 27 % de suppressions du "
        "panel portées par les quatre chaînes antiparasitaires américaines, premier point du "
        "backlog depuis le 14 septembre.",
        "Elle peut produire une phrase utilisable par un commerçant : « les avis qui "
        "disparaissent chez vous se ressemblent entre eux, et voici en quoi ».",
    ])

    sous_titre(doc, "Pourquoi elle peut échouer complètement")
    puces(doc, [
        "Le lot des avis supprimés est à 71 % en 5 étoiles, majoritairement américain, "
        "concentré sur les services à domicile, et 39 % de son volume vient de six enseignes. "
        "Comparé globalement au lot des survivants, il livrera des marqueurs de traitement "
        "antiparasitaire américain et de salle de sport espagnole.",
        "La version par mots a déjà été tentée et n'a rien donné : onze marqueurs cherchés "
        "dans les textes supprimés — insultes, spam, charabia —, avec un dictionnaire qui "
        "couvre 7 langues sur 41 pays.",
    ])

    sous_titre(doc, "La condition qui la rend valable")
    doc.add_paragraph(
        "La comparaison se fait à l'intérieur d'une fiche qui a perdu des avis un jour donné, "
        "entre ce qui est parti et ce qui est resté. Le secteur, le pays, la taille du groupe, "
        "la langue habituelle de la fiche et l'attention du commerçant s'annulent alors par "
        "construction. Ce montage a déjà tourné dans l'étude exploratoire sur 514 "
        "établissements et 61 202 observations, et ses 26 effets ont tous tenu au contrôle de "
        "robustesse.")

    sous_titre(doc, "Ce qu'il faut mesurer, et qui n'a jamais été mesuré")
    tableau(doc,
            ["Mesure", "Ce qu'elle teste"],
            [["Quasi-doublons entre avis d'une même fiche", "des avis produits en série"],
             ["Répétition d'un même prénom sur les avis d'une fiche",
              "l'hypothèse du technicien nommé, point 1 du backlog"],
             ["Ressemblance de gabarit, mots différents", "une campagne d'avis sollicités"],
             ["Absence de texte", "les 30 % d'avis supprimés sans texte, point L5"]])
    doc.add_paragraph(
        "La recherche de quasi-doublons se fait par empreintes de suites de caractères, sans "
        "modèle et sans difficulté de langue. L'embedding n'intervient que pour le cas « même "
        "idée, mots différents ».")

    # -----------------------------------------------------------------------
    doc.add_heading("Piste 3 — Pousser l'analyse sur la réponse du propriétaire", level=1)
    verdict(doc, "Verdict : à faire en premier, en poussant sur le sens de la cause.")

    sous_titre(doc, "Pourquoi c'est une bonne idée")
    puces(doc, [
        "C'est la question posée par le client d'Axel, et le seul levier qu'un commerçant peut "
        "actionner lui-même.",
        "Le résultat existe déjà et porte le livrable : hors des quatre chaînes "
        "antiparasitaires, répondre dans les deux jours divise le risque par 1,8.",
        "La réserve qui l'affaiblit est nommée dans la documentation, et elle se referme avec "
        "les données en main.",
    ])

    sous_titre(doc, "Ce qui n'apportera rien")
    doc.add_paragraph(
        "Ajouter des moments d'observation. Quatre ont été testés — la protection vaut 1,7 fois "
        "au premier jour, 1,8 au deuxième, 2,2 au troisième, 2,1 au quatrième. Le cinquième "
        "donnera la même réponse.")

    sous_titre(doc, "Le trou à refermer")
    doc.add_paragraph(
        "Un commerçant qui répond en deux jours est aussi un commerçant qui surveille sa fiche "
        "et signale les avis qu'il juge illégitimes. Tant que cette explication tient, le "
        "conseil « répondez vite » perd son fondement. Trois travaux la réduisent, tous "
        "faisables sur les données existantes.")
    puces(doc, [
        "Mesurer l'habitude de la fiche — sa part d'avis répondus et son délai habituel de "
        "réponse, calculés sur les avis publiés avant le 11 août, donc figés avant la période "
        "de risque — et la mettre dans le modèle. Il compare alors deux avis dont les commerces "
        "ont la même habitude.",
        "Comparer deux avis de la même fiche, l'un répondu vite, l'autre non. Même montage que "
        "pour la piste 2, et il règle le problème sans qu'il faille mesurer l'habitude.",
        "Séparer les avis négatifs des avis élogieux. C'est le test le plus tranchant et le "
        "moins cher. Si la protection joue aussi sur les avis 5 étoiles, le signalement par le "
        "commerçant ne peut pas l'expliquer, puisque personne ne signale un avis élogieux.",
    ])

    sous_titre(doc, "Les limites à surveiller")
    puces(doc, [
        "La population est petite. Au jalon du deuxième jour, le corpus complet compte 15 193 "
        "avis et 505 suppressions ; une fois les quatre chaînes antiparasitaires retirées, il "
        "reste 14 170 avis et 316 suppressions. Chaque découpage la vide un peu plus.",
        "Le découpage par note tiendra du côté 5 étoiles, qui porte le gros du volume. Du côté "
        "1 étoile, les effectifs seront trop minces pour conclure.",
        "Avec 316 suppressions, tester dix découpages en produira un remarquable par accident. "
        "Les découpages se déclarent avant de lancer le calcul.",
        "Tout doit être rejoué deux fois. Les quatre chaînes antiparasitaires portent 189 des "
        "505 suppressions de cette population, soit 37 %.",
        "Deux limites resteront : une réponse retirée par le commerçant est invisible, et une "
        "réponse arrivée après la suppression ne peut pas être observée.",
    ])

    # -----------------------------------------------------------------------
    doc.add_heading("Le classement des trois", level=1)
    tableau(doc,
            ["", "Piste", "Valeur", "Coût", "Risque de se tromper"],
            [["1", "Réponse du propriétaire, les trois travaux",
              "élevée, c'est le livrable", "faible", "faible"],
             ["2", "Textes qui se ressemblent, en comparaison interne à la fiche",
              "élevée, c'est la part inexpliquée", "moyen",
              "élevé si le périmètre est global"],
             ["3", "Embedding",
              "faible en prédiction, réelle en exploration", "moyen",
              "élevé, il relit le secteur"]],
            a_droite={0})
    doc.add_paragraph(
        "Les pistes 2 et 3 sont la même idée à deux niveaux de finesse. L'embedding est "
        "l'outil, la comparaison de textes est la question. Choisir l'embedding avant d'avoir "
        "posé le périmètre de comparaison reviendrait à choisir l'outil avant la question.")

    # -----------------------------------------------------------------------
    doc.add_heading("Deux points à trancher avant tout code", level=1)
    sous_titre(doc, "1. Les documents du projet se contredisent sur la piste 2")
    puces(doc, [
        "docs/01-etude.md § 5, « ce qui est écarté et qu'il ne faut pas proposer » : « la "
        "recherche de textes identiques à l'intérieur d'un même établissement ». Repris tel "
        "quel dans la section « écarté » du backlog.",
        "docs/BACKLOG.md, « à faire, par ordre d'intérêt », point 1 : « leurs textes citent "
        "très souvent un technicien par son prénom. Compter la répétition d'un même prénom sur "
        "les avis d'une fiche ».",
    ])
    doc.add_paragraph(
        "Les deux portent sur la répétition de texte au sein d'une fiche. L'un l'interdit, "
        "l'autre le classe premier. La contradiction se règle avant d'écrire une ligne de code.")

    sous_titre(doc, "2. L'embedding doit tourner sur la machine")
    doc.add_paragraph(
        "Voir la contrainte de licence rappelée dans la piste 1. Le choix du modèle en découle.")

    SORTIES.mkdir(parents=True, exist_ok=True)
    doc.save(CIBLE)
    print(f"écrit : {CIBLE}")


if __name__ == "__main__":
    construire()
