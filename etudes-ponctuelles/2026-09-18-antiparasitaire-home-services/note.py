#!/usr/bin/env python3
"""Assemble le document Word sur l'antiparasitaire dans les home services US.

    python etudes-ponctuelles/2026-09-18-antiparasitaire-home-services/note.py

Aucun chiffre n'est calculé ici. Tout vient des CSV de `sorties/`, produits par
`antiparasitaire.py`, et des figures de `sorties/figures/`, produites par
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
CIBLE = SORTIES / "2026-09-18-antiparasitaire-home-services-us.docx"

ENCRE_DOUCE = RGBColor(0x52, 0x51, 0x4E)

GROUPES_FR = {
    "a. les 4 chaines signalees": "Les 4 chaînes signalées",
    "b. variante de nom de ces 4 chaines": "Variantes de nom de ces 4 chaînes",
    "c. autre enseigne antiparasitaire": "Autres enseignes antiparasitaires",
    "d. autres services a domicile": "Autres services à domicile",
}
TAILLES_FR = {"large": "large — groupes de 20 à 50",
              "small": "small — groupes de 4 à 10",
              "mono": "mono — établissement unique"}


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


def amorce(doc, gras, suite):
    """Un paragraphe dont les premiers mots sont en gras.

    Word n'interprète pas les astérisques du Markdown : le gras passe par un
    `run` distinct.
    """
    p = doc.add_paragraph()
    r = p.add_run(gras)
    r.bold = True
    p.add_run(" " + suite)
    return p


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
    cadre = csv("A1-cadre-par-taille.csv")
    par_taille = csv("B1-par-taille.csv")
    sl = csv("C1-small-large.csv").set_index("activite")
    groupes = csv("D1-quatre-groupes.csv")
    enseignes = csv("E1-enseignes-non-marquees.csv")
    abc = csv("E2-ajout-manuel-abc.csv")
    apres = csv("F1-apres-retrait-des-quatre.csv").set_index("activite")

    p = sl.loc["antiparasitaire"]
    a = sl.loc["autres services"]
    g = groupes.set_index("groupe")
    quatre = g.loc["a. les 4 chaines signalees"]
    variantes = g.loc["b. variante de nom de ces 4 chaines"]
    autres_ap = g.loc["c. autre enseigne antiparasitaire"]
    autres_hs = g.loc["d. autres services a domicile"]
    ap_apres = apres.loc["antiparasitaire"]
    mono = cadre[cadre["bucket"] == "mono"].iloc[0]
    large = par_taille[(par_taille["bucket"] == "large")
                       & (par_taille["activite"] == "antiparasitaire")].iloc[0]

    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)
    style.paragraph_format.space_after = Pt(8)

    doc.add_heading("Le traitement antiparasitaire dans les home services américains",
                    level=0)
    chapeau(doc, "ReviewFlowz — suppressions d'avis Google — 18 septembre 2026 — "
                 "corpus complet, fiches de taille « small » et « large »")

    # -----------------------------------------------------------------------
    doc.add_heading("Ce qu'il faut retenir", level=1)
    for puce in [
        "Le traitement antiparasitaire occupe {} % des fiches de home services américaines, "
        "mais {} % de leurs avis et {} % de leurs suppressions.".format(
            virgule(p["part_fiches_pct"], 0), virgule(p["part_avis_pct"], 0),
            virgule(p["part_suppr_pct"], 0)),

        "Le déséquilibre vient des grands groupes. Dans la taille « large », {} fiches sur {} "
        "font du traitement antiparasitaire, soit {} %.".format(
            espace(large["fiches"]),
            espace(par_taille[par_taille["bucket"] == "large"]["fiches"].sum()),
            virgule(large["part_fiches_pct"], 0)),

        "Le drapeau qui sert à relancer les modèles sans les enseignes signalées ne marque que "
        "quatre noms. {} fiches de traitement antiparasitaire restent donc dans le corpus dit "
        "« sans enseignes signalées », où elles pèsent {} % des avis et {} % des "
        "suppressions.".format(
            espace(ap_apres["fiches"]), virgule(ap_apres["part_avis_pct"], 0),
            virgule(ap_apres["part_suppr_pct"], 0)),

        "Les enseignes antiparasitaires qui ne sont pas parmi les quatre signalées perdent "
        "{} % de leurs avis, soit davantage que les quatre chaînes elles-mêmes à {} %, et plus "
        "du double des autres services à domicile à {} %. Le phénomène suit l'activité.".format(
            virgule(autres_ap["taux_pct"], 2), virgule(quatre["taux_pct"], 2),
            virgule(autres_hs["taux_pct"], 2)),
    ]:
        doc.add_paragraph(puce, style="List Bullet")

    # -----------------------------------------------------------------------
    doc.add_heading("1. La sur-représentation", level=1)
    figure(doc, "figure5-part-antiparasitaire.png",
           "Figure 1 — Part du traitement antiparasitaire dans les fiches, les avis et les "
           "suppressions des home services américains.")

    tableau(doc,
            ["Taille", "Activité", "Fiches", "Avis", "Suppressions",
             "Part des fiches", "Part des avis", "Part des suppressions"],
            [[TAILLES_FR.get(r["bucket"], r["bucket"]), r["activite"],
              espace(r["fiches"]), espace(r["avis"]), espace(r["suppressions"]),
              "{} %".format(virgule(r["part_fiches_pct"])),
              "{} %".format(virgule(r["part_avis_pct"])),
              "{} %".format(virgule(r["part_suppr_pct"]))]
             for _, r in par_taille[par_taille["bucket"] != "mono"].iterrows()],
            a_droite={2, 3, 4, 5, 6, 7})

    doc.add_paragraph(
        "Dans la taille « large », {} fiches sur {} font du traitement antiparasitaire et "
        "portent {} % des avis. Une explication tient au critère de sélection lui-même : "
        "cette taille retient les groupes de 20 à 50 établissements, et la franchise "
        "antiparasitaire est une des formes d'entreprise qui atteint ce nombre de succursales "
        "aux États-Unis. C'est une hypothèse ; rien dans les données ne la démontre.".format(
            espace(large["fiches"]),
            espace(par_taille[par_taille["bucket"] == "large"]["fiches"].sum()),
            virgule(large["part_avis_pct"], 0)))

    amorce(doc, "Une enseigne est classée à la main.",
           "« ABC Home & Commercial Services » est une entreprise de traitement "
           "antiparasitaire diversifiée, dont aucun des noms de fiche ne porte les mots du "
           "motif. Ses {} fiches et {} avis ont été rattachés au métier sur décision du "
           "2026-09-21. Le reste de la classification repose sur le seul nom de l'enseigne et "
           "n'a pas été vérifié cas par cas : d'autres entreprises du même métier peuvent "
           "rester du côté des autres services, et les chiffres de ce document sont à lire "
           "comme un plancher.".format(espace(abc["fiches"].sum()),
                                       espace(abc["avis"].sum())))

    doc.add_paragraph(
        "La taille « mono » est laissée de côté dans tout ce document. Elle porte {} fiches "
        "mais seulement {} avis et {} suppressions, contre {} suppressions pour « small » et "
        "« large » réunies.".format(
            espace(mono["fiches"]), espace(mono["avis"]), espace(mono["suppressions"]),
            espace(sl["suppressions"].sum())))

    # -----------------------------------------------------------------------
    doc.add_heading("2. Ce que le drapeau actuel laisse passer", level=1)
    doc.add_paragraph(
        "Le drapeau `chaine_antiparasitaire_us` de sql/02_adding_features.sql marque une "
        "égalité exacte de nom, sur quatre valeurs : EcoShield Pest Solutions, Insight Pest "
        "Solutions, Pointe Pest Control, Bulwark Exterminating. Deux catégories lui échappent.")

    tableau(doc,
            ["Groupe", "Fiches", "Avis", "Suppressions", "Part des avis supprimés",
             "Part des avis", "Part des suppressions"],
            [[GROUPES_FR.get(r["groupe"], r["groupe"]), espace(r["fiches"]),
              espace(r["avis"]), espace(r["suppressions"]),
              "{} %".format(virgule(r["taux_pct"], 2)),
              "{} %".format(virgule(r["part_avis_pct"])),
              "{} %".format(virgule(r["part_suppr_pct"]))]
             for _, r in groupes.iterrows()],
            a_droite={1, 2, 3, 4, 5, 6})

    amorce(doc, "Les variantes de nom.",
           "{} fiches portent le nom d'une des quatre chaînes suivi d'une ville ou d'une "
           "mention de statut — « EcoShield Pest Solutions Seattle », « Bulwark Exterminating "
           "Corporate », « Insight Pest Control ». L'égalité exacte ne les attrape pas. Elles "
           "totalisent {} avis.".format(
               espace(variantes["fiches"]), espace(variantes["avis"])))

    amorce(doc, "Les autres enseignes du même métier.",
           "{} fiches, {} avis, {} suppressions. Ce sont des entreprises sans lien avec les "
           "quatre chaînes.".format(
               espace(autres_ap["fiches"]), espace(autres_ap["avis"]),
               espace(autres_ap["suppressions"])))

    doc.add_paragraph(
        "Conséquence directe : une fois les quatre chaînes retirées, il reste {} fiches de "
        "traitement antiparasitaire dans les home services américains, qui portent {} % des "
        "avis restants et {} % des suppressions restantes. Le corpus « sans enseignes "
        "signalées » n'est donc pas un corpus sans traitement antiparasitaire.".format(
            espace(ap_apres["fiches"]), virgule(ap_apres["part_avis_pct"]),
            virgule(ap_apres["part_suppr_pct"])))

    # -----------------------------------------------------------------------
    doc.add_heading("3. Le phénomène suit l'activité", level=1)
    figure(doc, "figure6-taux-par-groupe.png",
           "Figure 2 — Part des avis supprimés dans chaque groupe.")

    doc.add_paragraph(
        "Les enseignes antiparasitaires qui ne sont pas parmi les quatre signalées perdent "
        "{} % de leurs avis. C'est au-dessus des quatre chaînes elles-mêmes, à {} %, et plus "
        "du double des autres services à domicile, à {} %. Si le phénomène tenait à quatre "
        "entreprises particulières, ce palier n'existerait pas.".format(
            virgule(autres_ap["taux_pct"], 2), virgule(quatre["taux_pct"], 2),
            virgule(autres_hs["taux_pct"], 2)))

    doc.add_paragraph(
        "Une exception à signaler : les variantes de nom des quatre chaînes tombent à {} %, "
        "le plus bas des quatre groupes. Ces {} fiches sont de grosses succursales, {} avis "
        "pour {} suppressions. Rien dans les données n'explique cet écart avec les fiches de "
        "la même chaîne au nom exact.".format(
            virgule(variantes["taux_pct"], 2), espace(variantes["fiches"]),
            espace(variantes["avis"]), espace(variantes["suppressions"])))

    # -----------------------------------------------------------------------
    doc.add_heading("4. Les enseignes antiparasitaires non marquées", level=1)
    doc.add_paragraph(
        "La liste complète est dans sorties/E1-enseignes-non-marquees.csv. Les dix premières "
        "par nombre d'avis :")
    tableau(doc,
            ["Enseigne", "Taille", "Groupe", "Fiches", "Avis", "Suppressions"],
            [[r["enseigne"], r["bucket"],
              "variante" if r["groupe"].startswith("b.") else "autre enseigne",
              espace(r["fiches"]), espace(r["avis"]), espace(r["suppressions"])]
             for _, r in enseignes.sort_values("avis", ascending=False).head(10).iterrows()],
            a_droite={3, 4, 5})

    # -----------------------------------------------------------------------
    doc.add_heading("5. Ce que ces chiffres ne disent pas", level=1)
    for puce in [
        "Le repérage se fait sur le nom de l'enseigne, faute de sous-catégorie dans la table "
        "des commerces : la colonne industry s'arrête aux sept secteurs du panel. Le motif "
        "retenu est pest, exterminat, termite, spidexx, mosquito, rodent, wildlife.",
        "Une seule enseigne a été ajoutée à la main, « ABC Home & Commercial Services ». "
        "Aucune revue enseigne par enseigne n'a été faite sur les {} fiches restées du côté "
        "des autres services à domicile. La part de l'antiparasitaire est donc un "
        "plancher.".format(espace(a["fiches"])),
        "Deux des fiches d'ABC portent le nom d'un département sans rapport avec le métier — "
        "« Plumbing Services Department » et « Landscaping Department », {} avis et {} "
        "suppressions à elles deux. Elles sont comptées avec le reste de l'enseigne.".format(
            espace(abc[abc["enseigne"].str.contains("Department")]["avis"].sum()),
            espace(abc[abc["enseigne"].str.contains("Department")]["suppressions"].sum())),
        "« Alternative Earthcare » n'est attrapée que sur celle de ses fiches qui porte le "
        "suffixe « Tick and Mosquito Spraying ».",
        "Ces chiffres portent sur le corpus complet, 4,88 millions d'avis sans filtre de "
        "date. Ils ne se comparent pas ligne à ligne avec ceux du panel de la régression, qui "
        "retient 225 757 avis publiés du 13 mai au 16 août.",
        "Le taux de suppression n'est pas corrigé de l'âge des avis. Une activité dont les "
        "fiches ont des avis plus récents affichera un taux plus élevé pour cette seule "
        "raison. La comparaison entre groupes est donc indicative.",
        "Savoir pourquoi ces avis disparaissent reste ouvert. C'est le premier point du "
        "backlog depuis le 14 septembre.",
    ]:
        doc.add_paragraph(puce, style="List Bullet")

    # -----------------------------------------------------------------------
    doc.add_heading("6. Ce que ça implique pour l'étude", level=1)
    for puce in [
        "L'effet « secteur des services à domicile » mesuré par la régression est en partie un "
        "effet du traitement antiparasitaire. Les deux ne sont pas séparés aujourd'hui.",
        "Le contrôle « sans les six enseignes signalées » ne retire pas le traitement "
        "antiparasitaire du corpus. Les résultats ainsi produits en portent encore {} % des "
        "suppressions de home services américains.".format(
            virgule(ap_apres["part_suppr_pct"], 0)),
        "Deux corrections possibles, à trancher : étendre le drapeau aux variantes de nom, ou "
        "ajouter une caractéristique « activité antiparasitaire » au modèle pour la lire à "
        "part du secteur. La première demande de reconstruire la table et de relancer les "
        "modèles ; la seconde aussi.",
    ]:
        doc.add_paragraph(puce, style="List Bullet")

    chapeau(doc, "Régénérer : python etudes-ponctuelles/2026-09-18-antiparasitaire-home-"
                 "services/antiparasitaire.py, puis graphiques.py, puis note.py. Définition "
                 "d'une suppression : etude-exploratoire/scripts/suppressions_corrigees.py, "
                 "importée telle quelle.")

    CIBLE.parent.mkdir(parents=True, exist_ok=True)
    doc.save(CIBLE)
    print(f"écrit : {CIBLE}")


if __name__ == "__main__":
    construire()
