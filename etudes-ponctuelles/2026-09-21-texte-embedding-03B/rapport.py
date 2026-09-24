#!/usr/bin/env python3
"""Assemble le document Word de l'etude texte, depuis les CSV de sorties/.

    .venv/Scripts/python.exe etudes-ponctuelles/2026-09-21-texte-embedding-03B/rapport.py

Aucun chiffre n'est calcule ici. Tout vient des CSV produits par
`00_effectifs.py`. Le document est destine a etre enrichi : la section des
resultats est vide tant que les routes A et B n'ont pas tourne.

Jamais de texte d'avis, de nom d'auteur ni de lien d'avis dans ce document :
il est versionne.
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
CIBLE = SORTIES / "2026-09-21-texte-embedding-03B.docx"
DATE = "2026-09-21"

ENCRE_DOUCE = RGBColor(0x52, 0x51, 0x4E)


def csv(nom: str) -> pd.DataFrame:
    return pd.read_csv(SORTIES / f"{DATE}-{nom}.csv")


def espace(valeur) -> str:
    return f"{float(valeur):,.0f}".replace(",", " ")


def virgule(valeur, decimales: int = 1) -> str:
    return ("{:." + str(decimales) + "f}").format(float(valeur)).replace(".", ",")


def chapeau(doc, texte: str) -> None:
    p = doc.add_paragraph()
    r = p.add_run(texte)
    r.italic = True
    r.font.size = Pt(10.5)
    r.font.color.rgb = ENCRE_DOUCE


def note_basse(doc, texte: str) -> None:
    p = doc.add_paragraph()
    r = p.add_run(texte)
    r.font.size = Pt(9)
    r.font.color.rgb = ENCRE_DOUCE


def tableau(doc, entetes, lignes, a_droite=None) -> None:
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


def a_completer(doc, texte: str) -> None:
    p = doc.add_paragraph()
    r = p.add_run("[À COMPLÉTER] " + texte)
    r.italic = True
    r.font.color.rgb = ENCRE_DOUCE


def construire() -> None:
    a1 = csv("A1-effectifs-textes")
    a2 = csv("A2-par-note")
    a3 = csv("A3-par-langue")
    a4 = csv("A4-longueurs")
    a5 = csv("A5-enseignes")
    a6 = csv("A6-cases-note-langue")

    c = a1[a1["perimetre"] == "complet"].set_index("supprime")
    s = a1[a1["perimetre"] == "sans_enseignes"].set_index("supprime")
    n_textes = int(c["n_avec_texte"].sum())
    n_avis = int(c["n_avis"].sum())
    n_textes_hors = int(s["n_avec_texte"].sum())

    l4 = a4[a4["perimetre"] == "sans_enseignes"].set_index("supprime")
    a6s = a6[a6["perimetre"] == "sans_enseignes"]

    langues = a3[a3["perimetre"] == "complet"].sort_values("n_avec_texte", ascending=False)
    part_non_anglais = 100 * (1 - int(langues.iloc[0]["n_avec_texte"]) / n_textes)

    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)
    style.paragraph_format.space_after = Pt(8)
    for marge in doc.sections:
        marge.left_margin = Inches(1.0)
        marge.right_margin = Inches(1.0)

    doc.add_heading("Le texte des avis supprimés", level=0)
    chapeau(doc, "ReviewFlowz — 21 septembre 2026 — panel 03B, 35 751 avis publiés "
                 "du 4 au 17 août 2026, suivis jusqu'au 24 août")
    note_basse(doc, "Document en cours. Les sections « Ce que montrent les groupes de textes » "
                    "et « L'écart entre les deux populations » seront remplies quand les calculs "
                    "auront tourné. Tout le reste est établi.")

    # ------------------------------------------------------------------
    doc.add_heading("La question", level=1)
    doc.add_paragraph(
        "Les avis que Google retire ressemblent-ils, par leur texte, à ceux qui restent en "
        "ligne ? La note, l'âge et le profil de l'auteur ont déjà été mesurés. Le texte lui-même "
        "ne l'a été que par sa forme : sa longueur, ses majuscules, ses points d'exclamation.")
    doc.add_paragraph(
        "L'objet de cette étude est de comparer les textes eux-mêmes. Chaque avis est transformé "
        "en une suite de 768 nombres qui résume ce qu'il raconte, de telle sorte que deux avis "
        "qui disent la même chose, même dans deux langues différentes, obtiennent deux suites "
        "voisines. On peut alors regrouper les avis par ce qu'ils racontent et regarder, dans "
        "chaque groupe, la part de ce qui a disparu.")

    # ------------------------------------------------------------------
    doc.add_heading("Ce qui a déjà été tenté sur le texte", level=1)
    doc.add_paragraph(
        "Le 16 septembre, un modèle a été nourri des caractéristiques de forme du texte, d'un "
        "repérage de désaccord entre la note et le vocabulaire employé, et des 50 termes les plus "
        "fréquents du corpus. Sa capacité à classer les avis est passée de 0,860 à 0,864.")
    doc.add_paragraph(
        "Le texte n'a donc presque rien apporté à la capacité de deviner qui sera supprimé. "
        "Cette étude poursuit un autre but : décrire ce qui distingue les deux populations, et "
        "nommer les familles d'avis qui disparaissent.")

    # ------------------------------------------------------------------
    doc.add_heading("La population étudiée", level=1)
    doc.add_paragraph(
        "Un avis sans texte ne peut pas être encodé. La population de cette étude est celle des "
        "avis du panel qui portent un texte non vide.")
    tableau(doc,
            ["", "avis du panel", "dont avec texte", "part"],
            [["restés en ligne", espace(c.loc[False, "n_avis"]),
              espace(c.loc[False, "n_avec_texte"]), virgule(c.loc[False, "part_avec_texte_pct"]) + " %"],
             ["supprimés", espace(c.loc[True, "n_avis"]),
              espace(c.loc[True, "n_avec_texte"]), virgule(c.loc[True, "part_avec_texte_pct"]) + " %"],
             ["ensemble", espace(n_avis), espace(n_textes),
              virgule(100 * n_textes / n_avis) + " %"]],
            a_droite={1, 2, 3})
    doc.add_paragraph(
        "Ces {} avis se répartissent sur 4 971 fiches et 26 058 auteurs. Un auteur ne dépose "
        "donc presque jamais plus d'un avis dans ce panel.".format(espace(n_textes)))

    doc.add_heading("Les avis supprimés ne sont pas plus souvent sans texte", level=2)
    doc.add_paragraph(
        "Sur ce panel, {} % des avis supprimés n'ont pas de texte, contre {} % des avis restés "
        "en ligne. Une fois les enseignes signalées retirées, l'écart se creuse dans le même "
        "sens : {} % contre {} %.".format(
            virgule(100 * c.loc[True, "n_sans_texte"] / c.loc[True, "n_avis"]),
            virgule(100 * c.loc[False, "n_sans_texte"] / c.loc[False, "n_avis"]),
            virgule(100 * s.loc[True, "n_sans_texte"] / s.loc[True, "n_avis"]),
            virgule(100 * s.loc[False, "n_sans_texte"] / s.loc[False, "n_avis"])))
    doc.add_paragraph(
        "La ligne L5 du backlog, « pourquoi 30 % des avis supprimés n'ont aucun texte », porte "
        "sur le panel des 225 757 avis publiés dans les 90 jours avant le 11 août. Elle ne se "
        "transpose pas au panel 03B. Un avis supprimé y porte un texte un peu plus souvent que "
        "la moyenne.")

    # ------------------------------------------------------------------
    doc.add_heading("Ce que l'étape préparatoire montre déjà", level=1)

    doc.add_heading("1. Les chaînes antiparasitaires portent une suppression sur trois", level=2)
    lignes = []
    etiquettes = {"reste_du_panel": "reste du panel",
                  "chaines_antiparasitaires_us": "chaînes antiparasitaires américaines",
                  "salles_de_sport_attaquees": "salles de sport attaquées",
                  "salles_attaquees": "salles de sport attaquées"}
    for _, r in a5.iterrows():
        lignes.append([etiquettes.get(r["groupe"], r["groupe"]),
                       espace(r["n_fiches"]), espace(r["n_avis"]),
                       espace(r["n_avec_texte"]), espace(r["n_supprimes"]),
                       virgule(r["part_supprimee_pct"]) + " %"])
    tableau(doc,
            ["groupe", "fiches", "avis", "avec texte", "supprimés",
             "part supprimée sur les textes"],
            lignes, a_droite={1, 2, 3, 4, 5})
    chaines = a5[a5["groupe"] == "chaines_antiparasitaires_us"].iloc[0]
    doc.add_paragraph(
        "Ces quatre enseignes portent {} des {} suppressions du panel pour {} % des avis qui ont "
        "un texte. Elles domineront tout regroupement. Chaque résultat de cette étude sort donc "
        "en deux versions, avec et sans elles.".format(
            espace(chaines["n_supprimes"]), espace(int(a5["n_supprimes"].sum())),
            virgule(100 * chaines["n_avec_texte"] / n_textes)))
    doc.add_paragraph(
        "Les deux salles de sport espagnoles attaquées ne comptent pas ici : elles portent "
        "24 avis, dont 7 avec texte. Les garder ou les retirer ne change aucun chiffre de cette "
        "étude.")

    doc.add_heading("2. Les textes supprimés sont plus longs", level=2)
    tableau(doc,
            ["", "restés en ligne", "supprimés"],
            [["moyenne", "{} caractères, {} mots".format(espace(l4.loc[False, "moyenne_caracteres"]),
                                                         espace(l4.loc[False, "moyenne_mots"])),
              "{} caractères, {} mots".format(espace(l4.loc[True, "moyenne_caracteres"]),
                                              espace(l4.loc[True, "moyenne_mots"]))],
             ["moitié des avis sous",
              "{} caractères, {} mots".format(espace(l4.loc[False, "mediane_caracteres"]),
                                              espace(l4.loc[False, "mediane_mots"])),
              "{} caractères, {} mots".format(espace(l4.loc[True, "mediane_caracteres"]),
                                              espace(l4.loc[True, "mediane_mots"]))],
             ["9 avis sur 10 sous",
              "{} caractères, {} mots".format(espace(l4.loc[False, "neuf_sur_dix_sous_caracteres"]),
                                              espace(l4.loc[False, "neuf_sur_dix_sous_mots"])),
              "{} caractères, {} mots".format(espace(l4.loc[True, "neuf_sur_dix_sous_caracteres"]),
                                              espace(l4.loc[True, "neuf_sur_dix_sous_mots"]))],
             ["le plus long",
              "{} caractères, {} mots".format(espace(l4.loc[False, "max_caracteres"]),
                                              espace(l4.loc[False, "max_mots"])),
              "{} caractères, {} mots".format(espace(l4.loc[True, "max_caracteres"]),
                                              espace(l4.loc[True, "max_mots"]))]])
    note_basse(doc, "Hors enseignes signalées. Fichier A4-longueurs.csv.")
    doc.add_paragraph(
        "L'écart est visible sur les quatre mesures et n'a besoin d'aucun encodage pour être "
        "constaté. Il devient une réserve pour la suite : un modèle de texte sépare un texte long "
        "d'un texte court, donc une partie de ce qu'il trouvera sera cette différence de "
        "longueur. La longueur figurera dans la lecture de chaque groupe.")

    doc.add_heading("3. Plus d'un tiers des textes ne sont pas en anglais", level=2)
    lignes = [[r["langue"], espace(r["n_avec_texte"]), espace(r["n_fiches"])]
              for _, r in langues.head(7).iterrows()]
    lignes.append(["les 31 autres langues",
                   espace(langues.iloc[7:]["n_avec_texte"].sum()), ""])
    tableau(doc, ["langue", "avis avec texte", "fiches"], lignes, a_droite={1, 2})
    doc.add_paragraph(
        "{} % des textes ne sont pas en anglais. Un modèle anglophone est exclu : il rangerait "
        "les avis par langue.".format(virgule(part_non_anglais)))

    # ------------------------------------------------------------------
    doc.add_heading("Les comparaisons possibles", level=1)
    doc.add_paragraph(
        "La note commande le vocabulaire d'un avis. Comparer les textes supprimés à l'ensemble "
        "des autres reviendrait à comparer un corpus de 1 étoile à un corpus de 5 étoiles, et à "
        "mesurer la note. Chaque comparaison se fait donc à note égale, et à langue égale.")
    doc.add_paragraph(
        "Ce découpage réduit fortement les effectifs disponibles. Voici ce que portent les cases, "
        "hors enseignes signalées.")
    cases = a6s.sort_values("n_supprimes", ascending=False).head(7)
    tableau(doc,
            ["note", "langue", "supprimés avec texte", "restés avec texte"],
            [[int(r["note"]), r["langue"], espace(r["n_supprimes"]), espace(r["n_restes"])]
             for _, r in cases.iterrows()],
            a_droite={0, 2, 3})
    doc.add_paragraph(
        "Deux cases seulement portent assez d'avis supprimés pour une comparaison solide : "
        "5 étoiles en anglais et 1 étoile en anglais. Une troisième tient en rassemblant les "
        "avis 5 étoiles qui ne sont pas en anglais, à condition de vérifier que la composition "
        "par langue est la même des deux côtés. Les notes 2 et 3 sortent du champ : {} et {} "
        "avis supprimés en tout.".format(
            espace(a6s[a6s["note"] == 2]["n_supprimes"].sum()),
            espace(a6s[a6s["note"] == 3]["n_supprimes"].sum())))

    # ------------------------------------------------------------------
    doc.add_heading("Comment les textes sont encodés", level=1)
    doc.add_paragraph(
        "Tout se passe sur la machine de travail. Aucun texte ne sort, aucun service extérieur "
        "n'est appelé. Les textes contiennent le nom de leur auteur et le fichier de licence de "
        "l'export en interdit la rediffusion.")
    tableau(doc,
            ["réglage", "valeur", "pourquoi"],
            [["modèle", "intfloat/multilingual-e5-base",
              "multilingue, 768 nombres par avis ; plus de 100 langues rangées dans le même "
              "espace, ce qui permet de comparer un avis espagnol à un avis anglais"],
             ["longueur maximale", "512 fragments",
              "la valeur du modèle. Couper à 256 tronquerait environ 3 textes sur 100, et plus "
              "souvent du côté des supprimés, qui sont plus longs"],
             ["préfixe", "« query: »",
              "demandé par ce modèle des deux côtés d'une comparaison"],
             ["vecteurs ramenés à la même échelle", "oui",
              "la proximité entre deux avis se lit alors directement"],
             ["taille des lots", "32 textes",
              "tient dans la mémoire disponible"],
             ["fils d'exécution", "8 sur 14",
              "laisse la machine utilisable pendant le calcul"]],
            a_droite=set())
    doc.add_paragraph(
        "Les textes sont triés par longueur avant l'encodage, puis remis dans leur ordre "
        "d'origine. Un lot ne contient alors que des textes de taille voisine, ce qui évite de "
        "traiter un avis de vingt mots comme un avis de cinq cents.")
    doc.add_paragraph(
        "Le résultat est stocké hors du dépôt, dans data/embeddings/, avec l'identifiant de "
        "l'avis, sa note, sa langue, sa longueur et son sort. Aucun texte, aucun nom d'auteur, "
        "aucun lien d'avis.")

    doc.add_heading("Une précision sur le repérage des chaînes", level=2)
    doc.add_paragraph(
        "Le repérage des quatre chaînes antiparasitaires utilisé par le reste du projet compare "
        "le nom de la fiche à quatre libellés exacts. Il attrape 85 fiches et laisse passer "
        "10 succursales nommées « EcoShield Pest Solutions Houston », « Bulwark Exterminating "
        "Corporate » et ainsi de suite, qui portent 342 avis et 9 suppressions. Pour cette étude, "
        "le repérage se fait sur le début du nom, ce qui attrape les 95 fiches. Le drapeau du "
        "projet n'est pas modifié.")

    # ------------------------------------------------------------------
    doc.add_heading("Ce que montrent les groupes de textes", level=1)
    a_completer(doc, "Regroupement des avis par ce qu'ils racontent, puis part supprimée dans "
                     "chaque groupe. Chaque groupe sera décrit par son effectif, sa part "
                     "supprimée, sa langue dominante, sa répartition des notes, sa longueur "
                     "moyenne et son nombre de fiches. Les deux dernières colonnes sont les "
                     "garde-fous : un groupe très supprimé porté par trois fiches est une "
                     "enseigne, et un groupe dont toutes les notes valent 1 est une note.")

    doc.add_heading("L'écart entre les deux populations, à note égale", level=1)
    a_completer(doc, "Pour chaque case retenue, distance entre le centre des textes supprimés et "
                     "le centre des textes restés en ligne, comparée à la distance obtenue en "
                     "tirant au hasard deux groupes de mêmes tailles dans la même case. Si la "
                     "distance observée tombe dans l'intervalle du tirage, les textes supprimés "
                     "ne se distinguent pas des autres, et c'est une réponse.")

    # ------------------------------------------------------------------
    doc.add_heading("Pour aller plus loin", level=1)
    doc.add_paragraph(
        "Deux prolongements sont identifiés et laissés de côté pour l'instant.")

    doc.add_heading("Mesurer combien le texte pèse, à lui seul", level=2)
    doc.add_paragraph(
        "Un modèle nourri des seuls 768 nombres, sans la note ni l'âge ni le profil de l'auteur, "
        "dirait combien le texte permet de séparer les deux populations. Il repose sur {} avis "
        "supprimés hors enseignes, avec une mise de côté par fiche et par auteur : le jeu d'essai "
        "porterait environ 140 avis supprimés. La marge d'incertitude serait large. Cette route "
        "attend un panel plus fourni ou une fenêtre de suivi plus longue.".format(
            espace(s.loc[True, "n_avec_texte"])))

    doc.add_heading("Repérer les textes écrits sur un même gabarit", level=2)
    doc.add_paragraph(
        "Deux avis très proches l'un de l'autre sur une même fiche, ou sur deux succursales d'une "
        "même enseigne, signalent un texte fabriqué à partir d'un modèle. Cette piste vise "
        "directement les chaînes antiparasitaires, qui portent une suppression sur trois du panel "
        "et dont les textes nomment très souvent un technicien.")
    doc.add_paragraph(
        "La recherche de textes identiques figure dans la liste des constructions écartées du "
        "backlog. La rouvrir demande un accord préalable de Romain. L'élément nouveau à lui "
        "soumettre est le poids de ces quatre enseignes dans les suppressions du panel.")

    # ------------------------------------------------------------------
    doc.add_heading("Où sont les chiffres", level=1)
    tableau(doc,
            ["contenu", "fichier"],
            [["effectifs de la population texte", "sorties/2026-09-21-A1-effectifs-textes.csv"],
             ["par note", "sorties/2026-09-21-A2-par-note.csv"],
             ["par langue", "sorties/2026-09-21-A3-par-langue.csv"],
             ["longueurs", "sorties/2026-09-21-A4-longueurs.csv"],
             ["poids des enseignes", "sorties/2026-09-21-A5-enseignes.csv"],
             ["cases note et langue", "sorties/2026-09-21-A6-cases-note-langue.csv"],
             ["comptage", "etudes-ponctuelles/2026-09-21-texte-embedding-03B/00_effectifs.py"],
             ["encodage", "etudes-ponctuelles/2026-09-21-texte-embedding-03B/01_embedding.py"],
             ["ce document", "etudes-ponctuelles/2026-09-21-texte-embedding-03B/rapport.py"]])

    CIBLE.parent.mkdir(parents=True, exist_ok=True)
    doc.save(CIBLE)
    print(f"écrit : {CIBLE}")


if __name__ == "__main__":
    construire()
