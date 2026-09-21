#!/usr/bin/env python3
"""Assemble le document Word sur les avis disparus puis réapparus.

    python etudes-ponctuelles/2026-09-18-reapparitions/note.py

Aucun chiffre n'est calculé ici. Tout vient des CSV de `sorties/`, produits par
`reapparitions.py`, et des figures de `matthieu/figures/`, produites par
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
CIBLE = MATTHIEU / "2026-09-18-avis-disparus-puis-revenus.docx"

ENCRE_DOUCE = RGBColor(0x52, 0x51, 0x4E)

SECTEURS_FR = {
    "home_services": "Services à domicile",
    "healthcare": "Santé",
    "automotive": "Automobile",
    "wellness_fitness": "Sport et bien-être",
    "travel": "Voyage",
    "food_beverage": "Restauration",
    "hospitality": "Hôtellerie",
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
    perimetre = csv("A1-perimetre.csv").set_index("mesure")["valeur"]
    duree = csv("B1-duree-absence.csv")
    texte = csv("C1-texte.csv")
    pop = csv("J1-population-retenue.csv").set_index("mesure")["valeur"]
    secteurs = csv("J2-secteurs-vrais-retours.csv")
    regions = csv("J3-regions-vrais-retours.csv")
    note = csv("J4-note-vrais-retours.csv")
    duree_vraie = csv("J6-duree-vrais-retours.csv")
    calendrier = csv("H1-calendrier.csv").dropna(subset=["disparu_le"])
    tous_retours = csv("K1-secteurs-tous-retours.csv")
    fiches = csv("F2-fiches-les-plus-touchees.csv")
    fiches_vrais = csv("J5-fiches-vrais-retours.csv")

    avis_multi = int(perimetre["avis à plusieurs lignes de présence"])
    episodes = int(perimetre["épisodes de réapparition"])
    avis_total = int(perimetre["avis distincts"])
    vrais_avis = int(pop["avis"])
    vrais_fiches = int(pop["fiches"])
    disparus_avis = int(pop["avis ayant disparu au moins une fois"])

    un_jour = duree.iloc[0]
    bug = texte[texte["nature"].str.startswith("texte différent")]
    bug_2j = int(bug[bug["duree"] == "2 jours et plus"]["episodes"].iloc[0])
    j12 = calendrier.iloc[0]
    tete = fiches.iloc[0]
    tete_vrais = fiches_vrais.iloc[0]
    sous_3j = int(duree_vraie[duree_vraie["jours_absent"] <= 3]["episodes"].sum())
    total_vrais_ep = int(duree_vraie["episodes"].sum())

    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)
    style.paragraph_format.space_after = Pt(8)

    doc.add_heading("Les avis disparus puis réapparus", level=0)
    chapeau(doc, "ReviewFlowz — suppressions d'avis Google — 18 septembre 2026 — "
                 "4,88 millions d'avis sur 9 048 fiches, relevés du 11 au 24 août 2026")

    # -----------------------------------------------------------------------
    doc.add_heading("Ce qu'il faut retenir", level=1)
    for puce in [
        "{} avis ont quitté le listing de leur fiche puis y sont revenus pendant les quatorze "
        "jours de suivi, en {} épisodes. Sur les {} avis suivis, cela fait {} %.".format(
            espace(avis_multi), espace(episodes), espace(avis_total),
            virgule(100.0 * avis_multi / avis_total, 3)),

        "Deux retours sur trois suivent une absence d'une seule journée : {} épisodes sur {}. "
        "La règle du projet les compte comme des ratés du robot, et leur forme le confirme — "
        "ils arrivent par paquets sur une même fiche le même jour.".format(
            espace(un_jour["episodes"]), espace(episodes)),

        "{} avis sont revenus après une absence de deux jours ou plus, sur {} fiches. C'est la "
        "population qui compte : un retrait qui a tenu plusieurs jours, puis a été annulé. "
        "Rapporté aux {} avis ayant disparu au moins une fois pendant le suivi, cela fait un "
        "retrait annulé sur trente.".format(
            espace(vrais_avis), espace(vrais_fiches), espace(disparus_avis)),

        "Sur les seuls retraits qui ont tenu deux jours ou plus, et rapporté à la taille du "
        "secteur, les services à domicile et la santé arrivent en tête avec {} et {} avis "
        "revenus pour un million d'avis du secteur ; l'hôtellerie ferme la marche à {}. Tous "
        "retours confondus, y compris ceux du lendemain, l'automobile passe en tête à {}."
        .format(
            virgule(secteurs.iloc[0]["avis_revenus_par_million"], 0),
            virgule(secteurs.iloc[1]["avis_revenus_par_million"], 0),
            virgule(secteurs.iloc[-1]["avis_revenus_par_million"], 0),
            virgule(tous_retours.iloc[0]["avis_revenus_par_million"], 0)),

        "Un avis américain revient {} fois plus souvent qu'un avis européen : {} contre {} pour "
        "un million d'avis de la région.".format(
            virgule(regions.iloc[0]["avis_revenus_par_million"]
                    / regions.iloc[1]["avis_revenus_par_million"]),
            virgule(regions.iloc[0]["avis_revenus_par_million"], 0),
            virgule(regions.iloc[1]["avis_revenus_par_million"], 0)),
    ]:
        doc.add_paragraph(puce, style="List Bullet")

    # -----------------------------------------------------------------------
    doc.add_heading("Ce qu'on a compté", level=1)
    doc.add_paragraph(
        "Le robot crée une ligne par période de présence continue d'un avis. Un avis vu sans "
        "interruption du 11 au 24 août a donc une seule ligne. Un avis que le robot ne "
        "retrouve plus, puis qu'il revoit, en a deux : la première porte une date de "
        "disparition, la seconde une nouvelle date de première observation. Un avis à trois "
        "lignes a disparu deux fois.")
    doc.add_paragraph(
        "Les lignes d'historique, qui enregistrent la modification d'un avis par son auteur, "
        "ne signalent aucune absence et sont écartées. Sur ce périmètre, la table compte "
        "{} lignes de présence pour {} avis, soit {} lignes en trop portées par {} avis. Ces "
        "deux chiffres sont ceux de la documentation du projet.".format(
            espace(perimetre["lignes de présence (is_update faux)"]), espace(avis_total),
            espace(int(perimetre["lignes de présence (is_update faux)"]) - avis_total),
            espace(avis_multi)))
    doc.add_paragraph(
        "Un épisode est un couple : une ligne qui disparaît, la ligne suivante qui revient. "
        "Les {} avis concernés portent {} épisodes. Le document dit à chaque fois lequel des "
        "deux il compte.".format(espace(avis_multi), espace(episodes)))
    chapeau(doc, "Source : data/bigquery/reviews.parquet, copie locale de la table reviews. "
                 "Régénérer avec etudes-ponctuelles/2026-09-18-reapparitions/reapparitions.py")

    # -----------------------------------------------------------------------
    doc.add_heading("1. Le raté du robot et le vrai retour se distinguent", level=1)
    figure(doc, "figure1-duree-absence.png",
           "Figure 1 — Répartition des {} épisodes selon le nombre de jours d'absence."
           .format(espace(episodes)))

    doc.add_paragraph(
        "La règle du projet veut qu'une absence d'un seul jour soit un raté de collecte et "
        "qu'une absence de deux jours ou plus soit une vraie suppression. Les données lui "
        "donnent raison, et pour une raison qui se voit sans modèle : les deux populations "
        "n'ont pas la même forme.")
    tableau(doc,
            ["", "Absence d'un jour", "Absence de 2 jours ou plus"],
            [["Avis concernés", espace(un_jour["avis"]), espace(vrais_avis)],
             ["Fiches concernées", espace(un_jour["fiches"]), espace(vrais_fiches)],
             ["Avis par fiche touchée",
              virgule(float(un_jour["avis"]) / float(un_jour["fiches"]), 1),
              virgule(vrais_avis / vrais_fiches, 1)],
             ["Le plus gros paquet sur une fiche",
              "{} avis".format(espace(tete["avis_revenus"])),
              "{} avis".format(espace(tete_vrais["avis_revenus"]))]],
            a_droite={1, 2})
    doc.add_paragraph(
        "Le raté de collecte emporte plusieurs dizaines d'avis d'une même fiche d'un coup. "
        "{} en est le cas le plus net : cette fiche grecque perd {} de ses {} avis le 12 août "
        "et les retrouve tous le lendemain. Le vrai retour, lui, est dispersé — {} avis sur "
        "{} fiches, soit un peu plus d'un par fiche.".format(
            tete["enseigne"], espace(tete["avis_revenus"]), espace(tete["avis_de_la_fiche"]),
            espace(vrais_avis), espace(vrais_fiches)))
    doc.add_paragraph(
        "Reste un troisième cas, déjà documenté : {} épisodes reviennent après deux jours ou "
        "plus avec un texte entièrement différent. Ce sont les bugs d'enregistrement, écartés "
        "de tous les comptages ci-dessous.".format(bug_2j))

    # -----------------------------------------------------------------------
    doc.add_heading("2. Les secteurs", level=1)
    doc.add_paragraph(
        "Cette partie retient tous les avis revenus, y compris ceux qui réapparaissent dès le "
        "lendemain : {} avis sur les {} fiches touchées. Les bugs d'enregistrement en sont "
        "écartés, le texte de l'avis devant être le même avant et après l'absence.".format(
            espace(tous_retours["avis_revenus"].sum()),
            espace(tous_retours["fiches_touchees"].sum())))

    figure(doc, "figure2a-secteurs-par-million.png",
           "Figure 2a — Avis revenus pour un million d'avis du secteur.")
    figure(doc, "figure2b-secteurs-en-volume.png",
           "Figure 2b — Les mêmes avis, en nombre brut.")

    doc.add_paragraph(
        "Les deux figures ne classent pas les secteurs dans le même ordre, et l'écart se lit "
        "directement. La restauration est troisième en nombre d'avis revenus, avec {}, et "
        "cinquième une fois rapportée à ses {} avis. Le voyage fait le chemin inverse : "
        "dernier en nombre avec {} avis, sixième une fois rapporté à ses {}. L'automobile "
        "arrive en tête des deux.".format(
            espace(tous_retours[tous_retours["secteur"] == "food_beverage"]
                   ["avis_revenus"].iloc[0]),
            espace(tous_retours[tous_retours["secteur"] == "food_beverage"]
                   ["avis_du_secteur"].iloc[0]),
            espace(tous_retours[tous_retours["secteur"] == "travel"]["avis_revenus"].iloc[0]),
            espace(tous_retours[tous_retours["secteur"] == "travel"]["avis_du_secteur"].iloc[0])))

    tableau(doc,
            ["Secteur", "Avis du secteur", "Avis revenus", "dont dès le lendemain",
             "dont après 2 jours ou plus", "Fiches", "Pour un million"],
            [[SECTEURS_FR.get(r["secteur"], r["secteur"]), espace(r["avis_du_secteur"]),
              espace(r["avis_revenus"]), espace(r["avis_revenus_des_le_lendemain"]),
              espace(r["avis_revenus_apres_2j"]), espace(r["fiches_touchees"]),
              virgule(r["avis_revenus_par_million"], 0)]
             for _, r in tous_retours.iterrows()],
            a_droite={1, 2, 3, 4, 5, 6})

    doc.add_paragraph(
        "Les deux colonnes de détail totalisent {} et {} avis, soit {} pour une colonne "
        "« avis revenus » qui en affiche {}. L'écart tient à {} avis qui ont clignoté deux "
        "fois, une fois d'une journée et une fois plus longtemps ; ils comptent dans les deux "
        "colonnes de détail et une seule fois dans le total.".format(
            espace(tous_retours["avis_revenus_des_le_lendemain"].sum()),
            espace(tous_retours["avis_revenus_apres_2j"].sum()),
            espace(tous_retours["avis_revenus_des_le_lendemain"].sum()
                   + tous_retours["avis_revenus_apres_2j"].sum()),
            espace(tous_retours["avis_revenus"].sum()),
            espace(tous_retours["avis_revenus_des_le_lendemain"].sum()
                   + tous_retours["avis_revenus_apres_2j"].sum()
                   - tous_retours["avis_revenus"].sum())))

    doc.add_heading("Les seuls retraits qui ont tenu plus d'un jour", level=2)
    doc.add_paragraph(
        "Le tableau ci-dessous reprend la colonne « après 2 jours ou plus » et lui ajoute la "
        "durée moyenne de l'absence. C'est la population dont on peut dire qu'un retrait a été "
        "annulé.")
    tableau(doc,
            ["Secteur", "Avis du secteur", "Avis revenus", "Fiches", "Pour un million",
             "Absence moyenne"],
            [[SECTEURS_FR.get(r["secteur"], r["secteur"]), espace(r["avis_du_secteur"]),
              espace(r["avis_revenus"]), espace(r["fiches_touchees"]),
              virgule(r["avis_revenus_par_million"], 0),
              "{} j".format(virgule(r["absence_moyenne_j"]))]
             for _, r in secteurs.iterrows()],
            a_droite={1, 2, 3, 4, 5})
    doc.add_paragraph(
        "Les effectifs sont petits : le secteur de tête porte {} avis revenus, le dernier {}. "
        "Quelques avis suffisent à déplacer un rang, et ce classement se lit avec cette "
        "réserve.".format(espace(secteurs.iloc[0]["avis_revenus"]),
                          espace(secteurs.iloc[-1]["avis_revenus"])))

    # -----------------------------------------------------------------------
    doc.add_heading("3. La région et la note", level=1)
    tableau(doc,
            ["Région", "Avis du parc", "Avis revenus", "Fiches", "Pour un million"],
            [[r["region"], espace(r["avis_du_parc"]), espace(r["avis_revenus"]),
              espace(r["fiches_touchees"]), virgule(r["avis_revenus_par_million"], 0)]
             for _, r in regions.iterrows()],
            a_droite={1, 2, 3, 4})
    doc.add_paragraph(
        "Le sens est le même que pour les suppressions elles-mêmes : les États-Unis "
        "concentrent le phénomène.")

    tableau(doc,
            ["Note de l'avis", "Avis du parc", "Avis revenus", "Pour un million"],
            [["{} étoile{}".format(int(r["note"]), "s" if int(r["note"]) > 1 else ""),
              espace(r["avis_du_parc"]), espace(r["avis_revenus"]),
              virgule(r["avis_revenus_par_million"], 0)]
             for _, r in note.iterrows()],
            a_droite={1, 2, 3})
    doc.add_paragraph(
        "L'avis 1 étoile est celui qui revient le plus souvent rapporté à son nombre, et "
        "l'avis 5 étoiles celui qui revient le plus en volume : {} des {} avis concernés. "
        "Aucun avis 2 étoiles n'est revenu.".format(
            espace(note[note["note"] == 5]["avis_revenus"].iloc[0]), espace(vrais_avis)))

    # -----------------------------------------------------------------------
    doc.add_heading("4. Quand les avis disparaissent, et quand ils reviennent", level=1)
    figure(doc, "figure3-calendrier.png",
           "Figure 3 — Épisodes par jour de disparition, selon la durée de l'absence.")
    doc.add_paragraph(
        "Le 12 août porte {} des {} épisodes, dont {} reviennent dès le lendemain. Les trois "
        "premières journées du suivi concentrent les ratés de collecte. Les données ne disent "
        "pas pourquoi ; la mise en route de la collecte est l'hypothèse la plus simple.".format(
            espace(j12["episodes"]), espace(episodes),
            espace(int(j12["episodes"]) - int(j12["ep_2_jours_et_plus"]))))
    doc.add_paragraph(
        "Quand le retrait est réel, l'annulation vient vite : {} des {} épisodes de deux jours "
        "ou plus se règlent en deux ou trois jours. La plus longue absence suivie d'un retour "
        "dure {} jours.".format(sous_3j, total_vrais_ep,
                                int(duree_vraie["jours_absent"].max())))

    # -----------------------------------------------------------------------
    doc.add_heading("5. Ce que ces chiffres ne disent pas", level=1)
    for puce in [
        "On ne sait pas pourquoi un avis revient. Contestation par son auteur, correction par "
        "Google, erreur de modération rattrapée : rien dans les données ne tranche.",
        "Un avis disparu dans les derniers jours du suivi n'a plus le temps de revenir avant "
        "le 24 août. Le compte de {} avis revenus est donc un plancher.".format(
            espace(vrais_avis)),
        "Un avis disparu avant le 11 août et revenu pendant le suivi ressemble à un avis neuf. "
        "Ces retours-là sont invisibles.",
        "Le retour ne se voit que si le robot repasse sur la fiche. Une absence commencée et "
        "terminée entre deux passages ne laisse aucune trace.",
        "Les ratés de collecte sont reconnus à leur forme, non à une information venue du "
        "robot. Un vrai retrait massif suivi d'un rétablissement le lendemain serait compté "
        "comme un raté.",
    ]:
        doc.add_paragraph(puce, style="List Bullet")

    MATTHIEU.mkdir(parents=True, exist_ok=True)
    doc.save(CIBLE)
    print(f"écrit : {CIBLE}")


if __name__ == "__main__":
    construire()
