#!/usr/bin/env python3
"""Assemble le document Word sur l'effet de la réponse, panel 03B.

    python etudes-ponctuelles/2026-09-21-reponse-commercant-03B/note.py

Aucun chiffre n'est calculé ici. Tout vient des CSV de `sorties/`, produits par
`resultats.py`. Lancer les deux dans cet ordre.

Pas de figure : le document tient en trois tableaux, et une courbe n'ajouterait
rien à six valeurs alignées.
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
CIBLE = SORTIES / "2026-09-21-effet-reponse-commercant-03B.docx"

ENCRE_DOUCE = RGBColor(0x52, 0x51, 0x4E)


def csv(nom):
    return pd.read_csv(SORTIES / nom)


def espace(valeur):
    return f"{float(valeur):,.0f}".replace(",", " ")


def virgule(valeur, decimales=1):
    return ("{:." + str(decimales) + "f}").format(float(valeur)).replace(".", ",")


def facteur(valeur, decimales=2):
    return "×{}".format(virgule(valeur, decimales))


def fourchette(ligne, decimales=2):
    return "{} à {}".format(virgule(ligne["borne_basse"], decimales),
                            virgule(ligne["borne_haute"], decimales))


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
    effectifs = csv("A1-effectifs.csv").set_index("passage")
    escalier = csv("B1-escalier.csv")
    habitude = csv("C1-par-habitude.csv")
    bruts = csv("D1-taux-bruts.csv")
    retire = csv("D2-effet-enseignes.csv")
    rec = csv("E1-recouvrement.csv").iloc[0]
    ecartes = csv("F1-avis-ecartes.csv")

    entier = effectifs.loc["Corpus entier"]
    sans = effectifs.loc["Sans les enseignes signalées"]

    def brut(corpus, hab, repondu):
        m = ((bruts["corpus"] == corpus) & (bruts["habitude"] == hab)
             & (bruts["reponse_au_jalon"] == repondu))
        return bruts[m].iloc[0]

    reactives = "Fiches qui répondent à plus de 75 %"
    moyennes = "Fiches qui répondent à 25 à 75 %"

    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)
    style.paragraph_format.space_after = Pt(8)

    doc.add_heading("Répondre vite protège-t-il un avis ?", level=0)
    chapeau(doc, "ReviewFlowz — suppressions d'avis Google — 21 septembre 2026 — "
                 "le montage du 08 rejoué sur le panel 03B")

    doc.add_paragraph(
        "Le montage ne change pas : on photographie tous les avis au jalon du "
        "2e jour, on note lesquels portent déjà une réponse à cet instant, puis "
        "on regarde qui disparaît entre le 3e et le 8e jour. Un avis supprimé "
        "avant le jalon sort de l'étude. La réponse est donc connue avant la "
        "période de risque et ne peut pas être une conséquence de la survie.")

    # -----------------------------------------------------------------------
    doc.add_heading("Ce qui a été adapté", level=1)

    doc.add_paragraph("Deux choses seulement.")

    amorce(doc, "La sélection. ",
           "La colonne age_a_la_vague1_j n'existe plus. Le critère devient "
           "age_a_la_premiere_observation_j inférieur ou égal à 1 : le robot a "
           "vu l'avis le jour même ou le lendemain. Cela retient exactement les "
           "avis publiés du 10 au 17 août. Ceux du 4 au 9 ont tous été vus pour "
           "la première fois le 11, jour de l'arrivée du robot, donc à un âge de "
           "2 à 7 jours : ils sortent d'eux-mêmes.")

    amorce(doc, "Les avis du 17 août. ",
           "L'ancien panel s'arrêtait au 16 et tous ses avis atteignaient leur "
           "8e jour avant le dernier passage. Le 03B va jusqu'au 17, et un avis "
           "du 17 n'est suivi que sept jours. Le script mesure désormais, avis "
           "par avis, le nombre de jours entre la publication et le dernier "
           "passage, et écarte ceux qui n'atteignent pas la fenêtre demandée.")

    doc.add_paragraph(
        "Restent {} avis encore en ligne au jalon, dont {} portent déjà une "
        "réponse ({} %), et {} disparaissent dans la fenêtre.".format(
            espace(entier["avis_au_jalon"]), espace(entier["avec_reponse"]),
            virgule(entier["avec_reponse_pct"]), espace(entier["suppressions"])))

    # -----------------------------------------------------------------------
    doc.add_heading("Le résultat", level=1)

    doc.add_paragraph(
        "Sur le corpus entier, répondre dans les deux jours donne {} "
        "[{}]. La fourchette contient 1 : aucune protection mesurable. Le plus "
        "petit effet que ce montage pouvait repérer est {}, donc s'il existe une "
        "protection, elle est plus faible que cela.".format(
            facteur(entier["risque_relatif"]), fourchette(entier),
            facteur(entier["mde_protection"])))

    doc.add_paragraph(
        "Sans les enseignes signalées, {} [{}]. Là, la fourchette exclut 1.".format(
            facteur(sans["risque_relatif"]), fourchette(sans)))

    doc.add_paragraph(
        "Le résultat ne dépend pas de l'endroit où l'on place le jalon. Sans les "
        "enseignes signalées, toutes les fourchettes excluent 1. La dernière "
        "colonne donne la même mesure sur l'ancien panel, le 17 septembre.")

    tableau(doc,
            ["Jalon + fenêtre", "Risque", "Fourchette", "Sur l'ancien panel"],
            [["{} + {} jours".format(int(r["jalon"]), int(r["fenetre"])),
              facteur(r["risque_relatif"]), fourchette(r),
              facteur(r["risque_relatif_08"])]
             for _, r in escalier.iterrows()],
            a_droite={1, 2, 3},
            gras_lignes={int(escalier.index[escalier["jalon"] == 2][0])})

    # -----------------------------------------------------------------------
    doc.add_heading("Où la protection se trouve, et où elle s'inverse", level=1)

    doc.add_paragraph(
        "Découpé selon l'habitude de réponse de la fiche, mesurée sur les douze "
        "mois qui précèdent l'arrivée du robot. Jalon au 2e jour, sans les "
        "enseignes signalées.")

    tableau(doc,
            ["Habitude de la fiche", "Effet de la réponse", "Fourchette"],
            [[r["habitude"],
              "écartée, trop peu de suppressions" if r["ecartee"]
              else facteur(r["risque_relatif"]),
              "" if r["ecartee"] else fourchette(r)]
             for _, r in habitude.iterrows()],
            a_droite={2})

    doc.add_paragraph(
        "Ce n'est pas un artefact du modèle : les taux bruts le disent déjà. Sur "
        "les fiches qui répondent à plus de 75 %, {} suppressions pour 10 000 "
        "avis répondus contre {} pour les non répondus. Sur les fiches à 25 à "
        "75 %, {} contre {}. L'inversion est dans les données, pas dans "
        "l'ajustement.".format(
            virgule(brut("sans enseignes", reactives, 1)["taux_pour_10000_avis"], 0),
            virgule(brut("sans enseignes", reactives, 0)["taux_pour_10000_avis"], 0),
            virgule(brut("sans enseignes", moyennes, 1)["taux_pour_10000_avis"], 0),
            virgule(brut("sans enseignes", moyennes, 0)["taux_pour_10000_avis"], 0)))

    doc.add_paragraph(
        "Une lecture possible, qui n'est pas testée. Sur une fiche qui répond "
        "systématiquement, l'absence de réponse signale que le commerçant a jugé "
        "l'avis illégitime et l'a signalé. Sur une fiche qui répond de temps en "
        "temps, c'est au contraire la réponse qui marque l'avis qu'il a remarqué. "
        "Dans les deux cas, ce que la variable mesure serait l'attention du "
        "commerçant, non l'effet de l'acte de répondre.")

    ligne_retire = retire[(retire["habitude"] == reactives)
                          & (retire["reponse_au_jalon"] == 1)].iloc[0]
    amorce(doc, "Pourquoi les enseignes signalées changent tout. ",
           "Elles ne pèsent que {} avis sur {}, mais elles sont sur des fiches "
           "très réactives. Les retirer enlève {} avis répondus de la tranche "
           "« plus de 75 % » et {} des suppressions de cette tranche. Son taux y "
           "passe de {} à {} pour 10 000.".format(
               espace(entier["avis_au_jalon"] - sans["avis_au_jalon"]),
               espace(entier["avis_au_jalon"]),
               espace(ligne_retire["avis_retires"]),
               espace(ligne_retire["suppressions_retirees"]),
               virgule(brut("corpus entier", reactives, 1)["taux_pour_10000_avis"], 0),
               virgule(brut("sans enseignes", reactives, 1)["taux_pour_10000_avis"], 0)))

    # -----------------------------------------------------------------------
    doc.add_heading("La réserve qui compte le plus", level=1)

    amorce(doc, "Ce n'est pas une confirmation indépendante. ",
           "Les identifiants d'avis ont été croisés : sur les {} avis du nouveau "
           "corpus, {} étaient déjà dans l'ancien. {} avis nouveaux. La sélection "
           "« vu dès sa naissance » impose de partir du 10 août, jour de "
           "l'arrivée du robot, donc les deux corpus sont structurellement les "
           "mêmes pour cette question. Le 03B ne l'élargit pas.".format(
               espace(rec["population_08B"]), espace(rec["communs"]),
               espace(rec["avis_nouveaux"])))

    doc.add_paragraph(
        "Les valeurs le montrent : elles collent à l'ancien passage à un ou deux "
        "centièmes près, sur les six marches de l'escalier comme sur le découpage "
        "par habitude, où les fiches très réactives passent de {} à {}.".format(
            facteur(habitude.iloc[0]["risque_relatif_08"]),
            facteur(habitude.iloc[0]["risque_relatif"])))

    amorce(doc, "Ce que ce passage établit. ",
           "Rien n'a bougé quand le corpus a été reconstruit, et la sélection "
           "s'est assainie au passage.")

    doc.add_paragraph(
        "Les {} avis que le 08 gardait et que le 08B écarte ne sont pas sortis "
        "du corpus : ils sont tous dans la table 03B. Ils sortent parce que le "
        "robot ne les avait pas encore vus. L'ancien critère mesurait l'âge de "
        "l'avis au 11 août, date d'arrivée du robot ; le nouveau mesure son âge "
        "le jour où le robot l'a vraiment vu. Un avis publié le 10 août mais "
        "découvert le 18 vaut 1 pour l'ancien et 8 pour le nouveau.".format(
            espace(rec["avis_disparus"])))

    tableau(doc,
            ["Avis écartés par le 08B", "Nombre", "Âge à la première observation"],
            [[r["groupe"].replace("apres", "après").capitalize(),
              espace(r["avis"]),
              "{} à {} jours".format(int(r["age_min"]), int(r["age_max"]))]
             for _, r in ecartes.iterrows()],
            a_droite={1, 2})

    doc.add_paragraph(
        "Le 08 leur attribuait donc une survie entre le 3e et le 8e jour que "
        "personne n'avait observée. C'est une correction réelle, et elle ne "
        "déplace pas le résultat : les {} avis concernés ne portaient que {} "
        "suppressions.".format(espace(rec["avis_disparus"]),
                               espace(ecartes["suppressions"].sum())))

    amorce(doc, "Ce qu'il n'établit pas. ",
           "Que l'effet se retrouve sur d'autres avis. Il faudrait pour cela une "
           "seconde période de collecte, où le robot serait déjà en place quand "
           "les avis naissent.")

    doc.add_paragraph(
        "Deux limites du montage lui-même restent entières. Une réponse retirée "
        "est invisible : changed_fields ne contient que la note et le texte, "
        "jamais la réponse, donc un avis dont la réponse a été effacée est compté "
        "« sans réponse ». Et le sens de la causalité n'est pas établi : le "
        "commerçant qui répond est souvent celui qui signale.")

    chapeau(doc, "Sorties complètes dans logistic-regression-study/output-study/"
                 "2026-09-21-sorties-08B/, quinze passages. Régénérer avec "
                 "logistic-regression-study/python/08B_effet_reponse_commercant.py, "
                 "puis etudes-ponctuelles/2026-09-21-reponse-commercant-03B/"
                 "resultats.py et note.py.")

    CIBLE.parent.mkdir(parents=True, exist_ok=True)
    doc.save(CIBLE)
    print(f"écrit : {CIBLE}")


if __name__ == "__main__":
    construire()
