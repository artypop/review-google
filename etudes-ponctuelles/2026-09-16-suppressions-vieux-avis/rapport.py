#!/usr/bin/env python3
"""Assemble le document Word depuis les CSV et les figures de sorties/.

    python etudes-ponctuelles/2026-09-16-suppressions-vieux-avis/rapport.py

Aucun chiffre n'est calculé ici. Tout vient des CSV produits par `lancer.py`,
`vieux_avis.py`, `controle_collecte.py`, `age_a_la_suppression.py` et
`donnees_rapport.py`, dans cet ordre.
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
CIBLE = SORTIES / "2026-09-16-suppressions-avis-google.docx"

ENCRE_DOUCE = RGBColor(0x52, 0x51, 0x4E)


def csv(nom):
    return pd.read_csv(SORTIES / nom)


def espace(valeur):
    """12345.0 -> '12 345', avec une espace insécable."""
    return f"{float(valeur):,.0f}".replace(",", " ")


def virgule(valeur, decimales=1):
    """1.05 -> '1,05'. Le document est en français."""
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


def part_groupee(df):
    """Part des suppressions tombant sur une fiche qui en perd au moins quatre."""
    gros = df[df["perte_par_fiche"].str.startswith(("c.", "d."))]
    return gros["part_pct"].sum()


def construire():
    e1 = csv("E1-age-a-la-suppression.csv")
    e2 = csv("E2-quinze-premiers-jours.csv")
    e3 = csv("E3-recents-contre-anciens.csv")
    bnouv = csv("B-nouveaux-contre-anciens.csv")
    bage = csv("B-age-a-la-suppression.csv")
    c1 = csv("C1-vieux-par-jour.csv")
    c2 = csv("C2-taille-des-paquets.csv")
    c4 = csv("C4-concentration.csv")
    c5 = csv("C5-note-des-vieux.csv")
    c6 = csv("C6-dates-de-publication.csv")
    d1 = csv("D1-suppressions-definitives.csv")
    d3 = csv("D3-groupement-17-aout.csv")
    d3b = csv("D3bis-groupement-20-aout.csv")
    g5 = csv("G5-exemples-fiches.csv")
    g6 = csv("G6-exemple-10-aout.csv")

    pic = e1.iloc[1]["supprimes_pour_10000_avis"]
    plancher = e1.iloc[7]["supprimes_pour_10000_avis"]
    pic_jour = e1.iloc[1]["supprimes_par_million_de_jours"]
    plancher_jour = e1.iloc[7]["supprimes_par_million_de_jours"]
    j7 = e2[e2["age_en_jours"] == 7].iloc[0]["pour_10000_exposes"]
    recents = e3[e3["categorie"].str.startswith("récent")].iloc[0]
    conc = c4.iloc[0]
    ligne17 = c1[c1["supprime_le"] == "2026-08-17"].iloc[0]
    j17 = d1[d1["supprime_le"] == "2026-08-17"].iloc[0]
    vieux_total = c5["supprimes"].sum()

    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)
    style.paragraph_format.space_after = Pt(8)

    doc.add_heading("Quels avis Google disparaissent, et quand", level=0)
    chapeau(doc, "ReviewFlowz — 16 septembre 2026 — 4,88 millions d'avis suivis du 11 au 24 août 2026")

    doc.add_heading("Ce qu'il faut retenir", level=1)
    puces = [
        "Sur 10 000 avis âgés de quatre à sept jours, {} ont disparu pendant les quatorze jours "
        "de suivi. Sur 10 000 avis de plus de trois ans, {}.".format(espace(pic), espace(plancher)),
        "Le septième jour de vie concentre à lui seul {} disparitions pour 10 000 avis en ligne "
        "à cet âge, contre 5 au premier jour.".format(espace(j7)),
        "La moitié des suppressions frappe un avis de trente jours ou moins : {} sur {}, "
        "soit {} %.".format(espace(recents["suppressions"]), espace(e3["suppressions"].sum()),
                            virgule(recents["part_pct"])),
        "L'autre moitié touche des avis anciens, et le motif y est différent : {} fiches sur {} "
        "portent la moitié de ces suppressions.".format(espace(conc["fiches_pour_la_moitie"]),
                                                       espace(conc["fiches_touchees"])),
        "Dans les deux populations, l'avis 5 étoiles disparaît plus souvent que l'avis 3 ou "
        "4 étoiles.",
    ]
    for puce in puces:
        doc.add_paragraph(puce, style="List Bullet")

    doc.add_heading("Ce qu'on a regardé", level=1)
    doc.add_paragraph(
        "Un robot a relevé chaque jour la totalité des avis de 9 048 fiches Google Maps, du 11 au "
        "24 août 2026. Quatorze passages, donc treize occasions de constater qu'un avis a disparu. "
        "Les avis observés vont de 2004 à août 2026.")
    doc.add_paragraph(
        "Un avis absent deux jours ou plus est compté comme supprimé, à la date de sa première "
        "disparition. Une absence d'un seul jour est un raté du robot : parmi les avis qui "
        "disparaissent puis reviennent, 71 % ne manquent qu'une journée. Cette règle retient "
        "4 747 suppressions.")
    doc.add_paragraph(
        "L'âge dont il est question ici est celui de l'avis au moment où il disparaît, sans tenir "
        "compte de la date du premier passage du robot. Un avis publié le 10 août et supprimé le "
        "13 a trois jours : il compte comme un avis récent.")

    doc.add_heading("1. Les avis récents partent en premier", level=1)
    doc.add_paragraph(
        "Le nombre brut de suppressions ne suffit pas à comparer les âges : le parc contient "
        "2,87 millions d'avis de plus de trois ans contre 40 000 avis âgés de quatre à sept "
        "jours. Chaque tranche est donc rapportée au nombre d'avis qui ont eu cet âge pendant "
        "le suivi.")
    figure(doc, "figure1-age.png",
           "Figure 1 — Sur 10 000 avis ayant cet âge pendant le suivi, combien ont disparu.")
    doc.add_paragraph(
        "Le risque culmine entre quatre et sept jours, à {} disparitions pour 10 000 avis, puis "
        "s'effondre : {} entre un et trois mois, {} au-delà de trois ans.".format(
            espace(pic), espace(e1.iloc[4]["supprimes_pour_10000_avis"]), espace(plancher)))
    tableau(doc,
            ["Âge", "Suppressions", "Avis concernés", "Sur 10 000 avis",
             "Jours observés par avis"],
            [[r["age_a_la_suppression"][3:], espace(r["suppressions"]),
              espace(r["avis_concernes"]), virgule(r["supprimes_pour_10000_avis"]),
              virgule(r["jours_observes_par_avis"])] for _, r in e1.iterrows()],
            a_droite={1, 2, 3, 4})
    doc.add_paragraph(
        "La dernière colonne signale une limite de cette lecture. Un avis de plus de trois ans "
        "reste dans sa tranche d'âge pendant les {} jours du suivi, alors qu'un avis de quatre à "
        "sept jours n'y reste que {} jours avant d'en sortir. À risque identique, la tranche large "
        "ramasse donc davantage de suppressions.".format(
            virgule(e1.iloc[7]["jours_observes_par_avis"]),
            virgule(e1.iloc[1]["jours_observes_par_avis"])))
    doc.add_paragraph(
        "Corrigé de cet écart, en comptant le risque par journée passée en ligne, l'avis de "
        "quatre à sept jours disparaît {} fois plus souvent que l'avis de plus de trois ans, au "
        "lieu des {} fois que donne la lecture directe. Les deux chiffres sont justes et "
        "répondent à deux questions différentes : ce que perd un stock d'avis en quatorze jours, "
        "et ce que risque un avis un jour donné.".format(
            espace(pic_jour / plancher_jour), espace(pic / plancher)))

    doc.add_heading("Le septième jour", level=2)
    figure(doc, "figure2-quinze-jours.png",
           "Figure 2 — Avis disparus pour 10 000 avis en ligne à cet âge, sur les quinze premiers jours de vie.")
    doc.add_paragraph(
        "Au premier jour, 5 avis sur 10 000 disparaissent. Au septième, 138. Le risque retombe "
        "ensuite sans jamais revenir à ce niveau.")
    doc.add_paragraph(
        "Un délai aussi régulier oriente vers un traitement automatique déclenché à date fixe "
        "après la publication. Les données ne permettent pas de le confirmer.")

    doc.add_heading("Un exemple : les avis publiés le 10 août", level=2)
    doc.add_paragraph(
        "Chaque ligne réunit les avis publiés le 10 août, supprimés le même jour, avec la même "
        "note.")
    tableau(doc,
            ["Publié le", "Supprimé le", "Âge", "Note", "Avis dans ce cas"],
            [[r["publie_le"], r["supprime_le"], "{} j".format(r["age_j"]),
              "{} étoiles".format(r["note"]), espace(r["combien_d_avis_dans_ce_cas"])]
             for _, r in g6.head(6).iterrows()],
            a_droite={2, 4})
    doc.add_paragraph(
        "Les deux cas les plus fournis tombent à six et sept jours. Les dix avis supprimés le "
        "13 août, trois jours après leur publication, comptent eux aussi comme des avis récents.")

    doc.add_heading("2. Quelle part des suppressions touche des avis récents", level=1)
    tableau(doc, ["Âge au moment de la suppression", "Suppressions", "Part", "Fiches touchées"],
            [[r["age_a_la_suppression"][3:], espace(r["suppressions"]),
              "{} %".format(virgule(r["part_pct"])), espace(r["fiches"])] for _, r in bage.iterrows()],
            a_droite={1, 2, 3})
    doc.add_paragraph(
        "La moitié des suppressions frappe un avis de moins d'un mois. Un avis supprimé sur trois "
        "avait plus d'un an : {} avis, sur 788 fiches.".format(
            espace(bage.iloc[4]["suppressions"] + bage.iloc[5]["suppressions"])))
    doc.add_paragraph(
        "Une autre découpe, celle qui sépare les avis écrits pendant le suivi de ceux qui "
        "existaient avant, donne une lecture complémentaire :")
    tableau(doc, ["Population", "Avis en ligne", "Suppressions", "Part", "Taux"],
            [[r["population"], espace(r["avis_en_ligne"]), espace(r["suppressions"]),
              "{} %".format(virgule(r["part_des_suppressions_pct"])),
              "{} %".format(virgule(r["taux_de_suppression_pct"], 3))] for _, r in bnouv.iterrows()],
            a_droite={1, 2, 3, 4})
    doc.add_paragraph(
        "Quatre suppressions sur cinq frappent un avis qui existait déjà avant le premier passage "
        "du robot, parce que ces avis sont cent fois plus nombreux. Rapporté au nombre d'avis, un "
        "avis écrit pendant le suivi est trente-deux fois plus exposé.")

    doc.add_heading("3. Les vieux avis suivent un autre motif", level=1)
    doc.add_paragraph(
        "Chez les avis récents, la date de publication commande : un avis tombe six ou sept jours "
        "après avoir été déposé. Chez les avis de plus d'un an, la date de publication n'explique "
        "rien.")
    doc.add_paragraph(
        "La date de publication la plus touchée perd {} avis, répartis sur {} fiches et {} jours "
        "de suppression différents. Les quatorze suivantes en perdent quatre à six, toujours "
        "dispersées. Une fiche qui perd 32 vieux avis les a reçus à 32 dates différentes, étalées "
        "sur trois ans.".format(espace(c6.iloc[0]["suppressions"]), espace(c6.iloc[0]["fiches"]),
                                espace(c6.iloc[0]["jours_de_suppression"])))

    doc.add_heading("Le pic tombe sur la date de suppression", level=2)
    figure(doc, "figure3-vieux-par-jour.png",
           "Figure 3 — Avis de plus d'un an disparus, jour par jour du suivi.")
    doc.add_paragraph(
        "Le 17 août porte {} des {} suppressions de vieux avis, soit un quart en une journée sur "
        "treize. C'est aussi le seul jour où une fiche touchée en perd {} en moyenne, contre 1,1 "
        "à 1,5 les autres jours.".format(espace(ligne17["suppressions"]),
                                         espace(c1["suppressions"].sum()), virgule(ligne17["par_fiche"])))

    doc.add_heading("Quand une fiche perd de vieux avis, elle en perd un paquet", level=2)
    tableau(doc, ["Vieux avis perdus par une fiche en un jour", "Cas", "Suppressions", "Part"],
            [[r["taille_du_paquet"][3:], espace(r["paquets"]), espace(r["suppressions"]),
              "{} %".format(virgule(r["part_pct"]))] for _, r in c2.iterrows()],
            a_droite={1, 2, 3})
    doc.add_paragraph(
        "La concentration est forte : {} fiches portent un quart des suppressions de vieux avis, "
        "{} en portent la moitié, sur {} fiches touchées et 9 048 suivies.".format(
            espace(conc["fiches_pour_un_quart"]), espace(conc["fiches_pour_la_moitie"]),
            espace(conc["fiches_touchees"])))

    doc.add_heading("Qui sont ces fiches", level=2)
    doc.add_paragraph(
        "Les dix fiches qui perdent le plus de vieux avis. Leurs identifiants sont dans "
        "G5-exemples-fiches.csv.")
    noms = ["Fiche A", "Fiche B", "Fiche C", "Fiche D", "Fiche E",
            "Fiche F", "Fiche G", "Fiche H", "Fiche I", "Fiche J"]
    tableau(doc,
            ["", "Pays", "Secteur", "Vieux avis perdus", "Dates de publication", "Note moyenne"],
            [[noms[i], r["country"], r["industry"], espace(r["vieux_supprimes"]),
              espace(r["dates_de_publication"]), virgule(r["note_moyenne"], 2)]
             for i, (_, r) in enumerate(g5.iterrows())],
            a_droite={3, 4, 5})
    doc.add_paragraph(
        "Huit de ces dix fiches sont des prestataires de services à domicile américains "
        "appartenant à des groupes de vingt à cinquante établissements, et les avis qu'elles "
        "perdent sont notés en moyenne entre 4,79 et 5,00. Sept d'entre elles font partie des "
        "quatre chaînes de traitement antiparasitaire déjà signalées dans l'étude, dont les "
        "suppressions restent inexpliquées. Ces chaînes portent 360 des 1 438 suppressions de "
        "vieux avis, soit 25 %.")
    doc.add_paragraph(
        "La fiche A fait exception. C'est un autocariste allemand qui perd 39 vieux avis notés "
        "1,05 en moyenne, publiés entre 2018 et 2025. Le profil est inverse et l'hypothèse la "
        "plus simple est un retrait obtenu sur demande auprès de Google.")

    doc.add_heading("4. La note de l'avis supprimé", level=1)
    figure(doc, "figure4-note.png",
           "Figure 4 — Suppressions pour un million de journées en ligne, par note. Les deux échelles diffèrent.")
    doc.add_paragraph(
        "Dans les deux populations, le taux descend de 1 à 3 ou 4 étoiles, puis remonte en 5. "
        "L'avis 5 étoiles disparaît deux fois plus souvent que l'avis 4 étoiles chez les avis "
        "récents, trois fois et demie plus chez les avis anciens.")
    tableau(doc, ["Note", "Vieux avis en ligne", "Supprimés", "Pour 10 000 en ligne"],
            [["{} étoile{}".format(r["note"], "s" if r["note"] > 1 else ""),
              espace(r["en_ligne"]), espace(r["supprimes"]),
              virgule(r["supprimes_pour_10000_en_ligne"])] for _, r in c5.iterrows()],
            a_droite={1, 2, 3})
    doc.add_paragraph(
        "En volume, {} des {} vieux avis supprimés portaient 5 étoiles, soit 75,7 %. Les "
        "suppressions ne visent donc pas principalement les avis négatifs.".format(
            espace(c5[c5["note"] == 5].iloc[0]["supprimes"]), espace(vieux_total)))

    doc.add_heading("5. Les contrôles passés", level=1)
    doc.add_paragraph(
        "Le pic du 17 août pourrait venir du robot plutôt que de Google. Trois vérifications "
        "écartent cette explication.")
    tableau(doc, ["Contrôle", "Résultat", "Verdict"],
            [["Les suppressions du 17 août sont-elles définitives ?",
              "{} avis revus sur {}, soit {} %".format(espace(j17["revenues_ensuite"]),
                                                       espace(j17["suppressions"]),
                                                       virgule(j17["part_revenues_pct"])),
              "passé"],
             ["La collecte du 17 août est-elle normale ?",
              "2 246 avis vus pour la première fois, plage habituelle 2 099 à 2 981", "passé"],
             ["Les pertes sont-elles groupées par fiche ?",
              "{} % sur des fiches perdant au moins 4 avis, contre {} % un jour "
              "ordinaire".format(virgule(part_groupee(d3)), virgule(part_groupee(d3b))), "passé"]])
    doc.add_paragraph(
        "Un défaut de pagination du robot frapperait des avis isolés dispersés sur beaucoup de "
        "fiches. Ce qu'on observe le 17 août est l'inverse : des fiches qui perdent plusieurs avis "
        "d'un coup. Les journées réellement douteuses sont le 13 août, dont 15,3 % des "
        "disparitions sont suivies d'un retour, et le 14 août à 13,1 %.")

    doc.add_heading("6. Ce que ces chiffres ne disent pas", level=1)
    reserves = [
        "Les vieux avis encore en ligne sont là parce qu'ils ont survécu. Un avis ancien et "
        "fragile a été retiré avant le 11 août et n'existe pas pour nous. Le risque des avis "
        "anciens est donc sous-estimé.",
        "Un avis publié le 24 août n'a pas pu être observé assez longtemps pour qu'on le voie "
        "disparaître. Les taux des tout premiers jours de vie sont des planchers.",
        "Un retour ne s'observe que s'il reste de la fenêtre. L'absence de retours constatés du "
        "20 au 24 août ne prouve rien.",
        "La modération avant publication reste invisible. Aucun avis contenant un lien n'a été "
        "supprimé pendant le suivi, alors qu'il en existe dans le parc : ceux-là sont bloqués "
        "avant d'être mis en ligne.",
        "Rien dans les données ne dit pourquoi un avis part. Traitement automatique, signalement "
        "par le commerçant, contestation par un tiers : la cause n'est pas observable.",
        "Un avis publié et supprimé dans la même journée n'est jamais vu, le robot passant une "
        "fois par jour.",
        "Le panel couvre 41 pays dont un seul hors d'Europe, sans le Royaume-Uni.",
    ]
    for puce in reserves:
        doc.add_paragraph(puce, style="List Bullet")

    doc.add_heading("7. Refaire les calculs", level=1)
    doc.add_paragraph(
        "Tous les chiffres de ce document viennent des fichiers CSV du dossier sorties/, "
        "eux-mêmes produits par six scripts qui lisent la copie locale des données. Dans l'ordre :")
    for commande in ["lancer.py", "vieux_avis.py", "controle_collecte.py",
                     "age_a_la_suppression.py", "donnees_rapport.py", "graphiques.py",
                     "rapport.py"]:
        p = doc.add_paragraph(
            "python etudes-ponctuelles/2026-09-16-suppressions-vieux-avis/" + commande)
        p.paragraph_format.space_after = Pt(2)
        p.runs[0].font.name = "Consolas"
        p.runs[0].font.size = Pt(9.5)
    doc.add_paragraph()
    doc.add_paragraph(
        "La définition d'une suppression est celle de suppressions_corrigees.py, importée telle "
        "quelle. Aucune table n'est créée et rien n'est écrit dans BigQuery.")

    doc.save(CIBLE)
    return CIBLE


if __name__ == "__main__":
    print("écrit :", construire())
