#!/usr/bin/env python3
"""Ajoute la section 5 à `livrables/analyses-complémentaires.docx`.

    .venv/Scripts/python.exe etudes-ponctuelles/2026-09-28-kmeans-us-1-5-etoiles/note.py

Lit `sorties/A1-groupes.csv` et `sorties/B1-ecart-centres.csv`. Aucun chiffre
n'est calculé ici. La section « 5. » est retirée si elle existe, puis réécrite
à la fin du document ; le reste n'est pas touché.

Étiquettes des groupes : établies le 2026-09-28 à partir des mots les plus
caractéristiques de chaque groupe, de sa longueur médiane et de ses secteurs
dominants, sans lecture de textes. Elles décrivent le groupe, pas chaque avis.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from docx import Document  # noqa: E402
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT  # noqa: E402
from docx.enum.text import WD_ALIGN_PARAGRAPH  # noqa: E402
from docx.oxml import OxmlElement  # noqa: E402
from docx.oxml.ns import qn  # noqa: E402
from docx.shared import Cm, Pt, RGBColor  # noqa: E402

DOSSIER = Path(__file__).resolve().parent
RACINE = DOSSIER.parents[1]
SORTIES = DOSSIER / "sorties"
FIGURE = SORTIES / "figure-groupes-k4.png"
LIVRABLE = RACINE / "livrables" / "analyses-complémentaires.docx"
TITRE = "5. Textes des avis américains supprimés, à note égale"
NUM_TABLEAUX, NUM_FIGURE = (7, 8, 9), 6

CONTRATS = "Contrats et frais : concession, location, assurance"
ETIQUETTES = {
    ("1_etoile_toutes_fiches", 3): {0: CONTRATS + ", antiparasitaire",
                                    1: "Plaintes courtes et génériques",
                                    2: "Restaurant et hôtel : service, chambre"},
    ("1_etoile_toutes_fiches", 4): {0: "Soins vétérinaires et médicaux",
                                    1: CONTRATS + ", antiparasitaire",
                                    2: "Restaurant et hôtel : service, chambre",
                                    3: "Plaintes courtes et génériques"},
    ("1_etoile_sans_enseignes", 3): {0: CONTRATS + ", vétérinaire",
                                     1: "Plaintes courtes et génériques",
                                     2: "Restaurant et hôtel : service, chambre"},
    ("1_etoile_sans_enseignes", 4): {0: "Restaurant et hôtel : service, chambre",
                                     1: "Soins vétérinaires et médicaux",
                                     2: "Voiture : concession, location, péages, garantie",
                                     3: "Plaintes courtes et génériques"},
    ("5_etoiles_toutes_fiches", 3): {0: "Avis détaillés : intervention, soin, séjour",
                                     1: "Éloges très courts (« awesome », « excellent »)",
                                     2: "Éloges courts du service : rapide, serviable"},
    ("5_etoiles_toutes_fiches", 4): {0: "Éloges très courts (« awesome », « excellent »)",
                                     1: "Récits détaillés d'une prestation : réparation, soin, nuisibles",
                                     2: "Éloges courts du service : rapide, serviable",
                                     3: "Loisirs, restaurants, séjours : bateau, excursion, hôtel"},
    ("5_etoiles_sans_enseignes", 3): {0: "Éloges courts du service : rapide, serviable",
                                      1: "Avis détaillés : intervention, soin, séjour",
                                      2: "Éloges très courts (« awesome », « excellent »)"},
    ("5_etoiles_sans_enseignes", 4): {0: "Récits détaillés d'une prestation : location, réparation, soin",
                                      1: "Éloges très courts (« awesome », « excellent »)",
                                      2: "Éloges courts du service : rapide, serviable",
                                      3: "Loisirs, restaurants, séjours : bateau, excursion, hôtel"},
}
NOMS_POP = {"1_etoile_toutes_fiches": "1 étoile, toutes les fiches",
            "1_etoile_sans_enseignes": "1 étoile, sans les six enseignes",
            "5_etoiles_toutes_fiches": "5 étoiles, toutes les fiches",
            "5_etoiles_sans_enseignes": "5 étoiles, sans les six enseignes"}


def virgule(x, d=1):
    return f"{x:.{d}f}".replace(".", ",")


def espace(n):
    return f"{int(n):,}".replace(",", " ")


# ---------------------------------------------------------------------------
# Figure : K = 4, part supprimée par groupe et fourchette du hasard
# ---------------------------------------------------------------------------
SURFACE = "#fcfcfb"; ENCRE = "#0b0b0b"; ENCRE_DOUCE = "#52514e"; GRILLE = "#e4e3df"
BLEU = "#2a78d6"; ORANGE = "#eb6834"; GRIS = "#9b9a96"


def figure(g):
    fig, axes = plt.subplots(2, 2, figsize=(7.2, 6.4), dpi=150)
    fig.patch.set_facecolor(SURFACE)
    fig.subplots_adjust(left=0.30, right=0.97, top=0.82, bottom=0.07, hspace=0.6, wspace=0.95)
    for ax, pop in zip(axes.ravel(), NOMS_POP):
        d = g[(g["population"] == pop) & (g["k"] == 4)].sort_values("part_supprimee_pct")
        moyenne = 100 * d["n_supprimes"].sum() / d["n_avis"].sum()
        y = np.arange(len(d))
        couleurs = [BLEU if h == "plus" else (ORANGE if h == "moins" else GRIS)
                    for h in d["hors_du_hasard"].fillna("")]
        ax.set_facecolor(SURFACE)
        bas = 100 * d["hasard_borne_basse"] / d["n_avis"]
        haut = 100 * d["hasard_borne_haute"] / d["n_avis"]
        ax.hlines(y, bas, haut, color=GRILLE, lw=6, zorder=1)
        ax.scatter(d["part_supprimee_pct"], y, color=couleurs, s=36, zorder=3)
        ax.axvline(moyenne, color=ENCRE_DOUCE, lw=1, ls="--", zorder=2)
        ax.set_yticks(y, [ETIQUETTES[(pop, 4)][int(k)].split(" :")[0].split(" (")[0].replace("Récits détaillés d'une", "Récits d'une")
                          for k in d["groupe"]], fontsize=7.5)
        ax.set_title(NOMS_POP[pop].replace(", ", "\n", 1), fontsize=8.5, color=ENCRE, loc="left")
        for c in ("top", "right", "left"):
            ax.spines[c].set_visible(False)
        ax.spines["bottom"].set_color(GRILLE)
        ax.tick_params(colors=ENCRE_DOUCE, labelsize=7.5, length=0)
        ax.set_xlim(0, max(haut.max(), d["part_supprimee_pct"].max()) * 1.15)
        ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{virgule(v, 0)} %"))
    fig.text(0.012, 0.975, "Part des avis supprimés par groupe de textes (K = 4)",
             fontsize=11, color=ENCRE, va="top")
    fig.text(0.012, 0.935, "Point bleu : plus de suppressions que le hasard ; orange : moins ; "
             "gris : dans la fourchette du hasard (bande).\nTiret : part supprimée de la population.",
             fontsize=8, color=ENCRE_DOUCE, va="top", linespacing=1.4)
    fig.savefig(FIGURE, dpi=150, facecolor=SURFACE)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Document
# ---------------------------------------------------------------------------
NAVY = RGBColor(0x32, 0x29, 0x54); GR = RGBColor(0x6B, 0x6A, 0x66)


def P(doc, texte, style=None):
    p = doc.add_paragraph(style=style)
    for i, m in enumerate(texte.split("**")):
        if m:
            p.add_run(m).bold = i % 2 == 1
    return p


def fond(cell, couleur):
    sh = OxmlElement("w:shd")
    sh.set(qn("w:val"), "clear"); sh.set(qn("w:color"), "auto"); sh.set(qn("w:fill"), couleur)
    cell._tc.get_or_add_tcPr().append(sh)


def tableau(doc, titre, entetes, lignes, largeurs, note=None, nouvelle_page=False):
    """`lignes` : listes de valeurs, ou chaîne seule pour une ligne de sous-titre.
    Une valeur (texte, True) est écrite en gras."""
    tp = doc.add_paragraph(titre, style="TitreTableau")
    tp.paragraph_format.page_break_before = nouvelle_page
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
    zebre = 0
    for i, rangee in enumerate([entetes] + lignes):
        ligne = t.rows[i]
        if isinstance(rangee, str):
            c = ligne.cells[0].merge(ligne.cells[-1])
            c.width = Cm(sum(largeurs))
            p = c.paragraphs[0]; p.paragraph_format.space_after = Pt(0)
            r = p.add_run(rangee); r.font.size = Pt(9); r.bold = True; r.font.color.rgb = NAVY
            fond(c, "E6E5EC"); zebre = 0
            continue
        zebre += 1
        for j, val in enumerate(rangee):
            c = ligne.cells[j]
            c.width = Cm(largeurs[j])
            c.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            p = c.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT if j == 0 else WD_ALIGN_PARAGRAPH.RIGHT
            texte, gras = val if isinstance(val, tuple) else (val, False)
            r = p.add_run(str(texte)); r.font.size = Pt(9); r.bold = gras
            if i == 0:
                r.bold = True; r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF); fond(c, "322954")
            elif zebre % 2 == 0:
                fond(c, "F4F4F7")
    for j, gc in enumerate(t._tbl.tblGrid.findall(qn("w:gridCol"))):
        gc.set(qn("w:w"), str(int(largeurs[j] * 567)))
    if note:
        doc.add_paragraph(note, style="NoteTableau")


def lignes_note(g, note):
    out = []
    for pop in [p for p in NOMS_POP if p.startswith(f"{note}_")]:
        for k in (4,):             # K = 3 reste dans A1-groupes.csv, hors du document
            d = g[(g["population"] == pop) & (g["k"] == k)].sort_values(
                "part_supprimee_pct", ascending=False)
            moyenne = 100 * d["n_supprimes"].sum() / d["n_avis"].sum()
            out.append(f"K = {k}, {NOMS_POP[pop].split(', ', 1)[1]} "
                       f"(part supprimée moyenne : {virgule(moyenne, 1)} %)")
            for r in d.itertuples():
                sens = {"plus": " ▲", "moins": " ▼"}.get(r.hors_du_hasard if isinstance(
                    r.hors_du_hasard, str) else "", "")
                net = bool(sens)
                out.append([ETIQUETTES[(pop, k)][int(r.groupe)], espace(r.n_avis),
                            espace(r.n_supprimes),
                            (f"{virgule(r.part_supprimee_pct, 1)} %{sens}", net),
                            f"{r.hasard_borne_basse} à {r.hasard_borne_haute}",
                            virgule(r.attendu_par_secteur, 0),
                            f"{virgule(r.part_supp_fiche_la_plus_touchee_pct, 0)} %",
                            espace(r.longueur_mediane)])
    return out


def retirer_section(doc):
    corps = doc.element.body
    debut = next((p._p for p in doc.paragraphs if p.text.strip() == TITRE), None)
    if debut is None:
        return
    courant = debut
    while courant is not None and courant.tag != qn("w:sectPr"):
        suivant = courant.getnext()
        corps.remove(courant)
        courant = suivant


def main() -> int:
    g = pd.read_csv(SORTIES / "A1-groupes.csv")
    b = pd.read_csv(SORTIES / "B1-ecart-centres.csv").set_index("population")
    figure(g)

    def part(pop, k, grp):
        r = g[(g["population"] == pop) & (g["k"] == k) & (g["groupe"] == grp)].iloc[0]
        return f"{virgule(r['part_supprimee_pct'], 1)} %"

    def ligne(pop, grp):
        return g[(g["population"] == pop) & (g["k"] == 4) & (g["groupe"] == grp)].iloc[0]

    def supp(pop, grp):
        return espace(ligne(pop, grp)["n_supprimes"])

    def att(pop, grp):
        return virgule(ligne(pop, grp)["attendu_par_secteur"], 0)

    ecart_max = g.loc[g["k"] == 4, "ecart_au_secteur_en_ecarts_types"].abs().max()
    if ecart_max >= 2:
        raise SystemExit("Un groupe s'écarte de son secteur : « À retenir » est à réécrire.")

    def moyenne(pop):
        d = g[(g["population"] == pop) & (g["k"] == 4)]
        return f"{virgule(100 * d['n_supprimes'].sum() / d['n_avis'].sum(), 1)} %"

    doc = Document(LIVRABLE)
    retirer_section(doc)
    h = doc.add_heading(TITRE, level=1)
    h.paragraph_format.page_break_before = True
    P(doc, "Avis américains en anglais du panel 03B, avec texte : 97,9 % des avis américains "
           "avec texte. Même vectorisation que la figure 9 du rapport ; les avis de chaque note "
           "sont ensuite répartis en 4 groupes de textes proches (KMeans). Chaque "
           "groupe est comparé à 2 000 groupes de même taille tirés au hasard dans la même "
           "population.")

    tableau(doc, f"Tableau {NUM_TABLEAUX[0]}. Les textes supprimés s'écartent-ils des textes "
                 "restés en ligne ?",
            ["Population", "Avis", "Supprimés", "Écart observé", "Écart au hasard", "Rapport"],
            [[NOMS_POP[p], espace(r["n_supprimes"] + r["n_restes"]), espace(r["n_supprimes"]),
              virgule(r["ecart_observe"], 4), virgule(r["hasard_moyen"], 4),
              (f"×{virgule(r['rapport_observe_sur_hasard'], 1)}", bool(r["au_dessus_du_hasard"]))]
             for p, r in b.iterrows()],
            [5.2, 1.8, 2.0, 2.4, 2.4, 1.8],
            note="Écart : distance entre le texte moyen des avis supprimés et celui des avis "
                 "restés en ligne. Écart au hasard : moyenne de 2 000 partages au hasard de "
                 "mêmes tailles. En gras : écart au-dessus de 97,5 % des tirages.")

    entetes = ["Groupe de textes", "Avis", "Supprimés", "Part supprimée",
               "Hasard : supprimés", "Attendus (secteur)", "Fiche la plus touchée",
               "Longueur"]
    largeurs = [4.7, 1.3, 1.8, 1.8, 1.9, 1.7, 1.6, 1.8]
    note_groupes = ("▲ / ▼ : plus / moins de suppressions que 97,5 % des groupes tirés au hasard. "
                    "Hasard : fourchette du nombre de suppressions attendu (2,5 % à 97,5 %). "
                    "Attendus (secteur) : suppressions qu'aurait le groupe si chaque avis "
                    "avait le taux de suppression de son secteur. "
                    "Fiche la plus touchée : part des suppressions du groupe portée par une seule "
                    "fiche. Longueur : médiane, en caractères. Étiquettes tirées des mots les plus "
                    "caractéristiques de chaque groupe.")
    tableau(doc, f"Tableau {NUM_TABLEAUX[1]}. Avis 1 étoile : suppressions par groupe de textes",
            entetes, lignes_note(g, 1), largeurs, note_groupes)
    tableau(doc, f"Tableau {NUM_TABLEAUX[2]}. Avis 5 étoiles : suppressions par groupe de textes",
            entetes, lignes_note(g, 5), largeurs, note_groupes, nouvelle_page=True)

    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.page_break_before = True
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(str(FIGURE), width=Cm(13.5))
    doc.add_paragraph(f"Figure {NUM_FIGURE}. Part des avis supprimés par groupe de textes, K = 4.",
                      style="Legende")

    doc.add_paragraph("À retenir", style="TitreTableau")
    b1, b1s = b.loc["1_etoile_toutes_fiches"], b.loc["1_etoile_sans_enseignes"]
    b5, b5s = b.loc["5_etoiles_toutes_fiches"], b.loc["5_etoiles_sans_enseignes"]
    for texte in (
            "**Les textes supprimés se distinguent des autres dans les quatre populations** : "
            f"écart ×{virgule(b1['rapport_observe_sur_hasard'])} et "
            f"×{virgule(b1s['rapport_observe_sur_hasard'])} le hasard en 1 étoile, "
            f"×{virgule(b5['rapport_observe_sur_hasard'])} et "
            f"×{virgule(b5s['rapport_observe_sur_hasard'])} en 5 étoiles (toutes les fiches, "
            "puis sans les six enseignes).",
            "**Les écarts entre groupes viennent des secteurs** : chaque groupe compte à peu près "
            "les suppressions qu'on attend de ses secteurs. Aucun des 16 groupes ne s'en écarte "
            f"de plus de {virgule(ecart_max, 1)} écart-type. Le groupe voiture en 1 étoile "
            f"({supp('1_etoile_sans_enseignes', 2)} suppressions, {att('1_etoile_sans_enseignes', 2)} "
            "attendues) est surtout automobile ; le groupe loisirs en 5 étoiles "
            f"({supp('5_etoiles_sans_enseignes', 3)}, {att('5_etoiles_sans_enseignes', 3)} attendues) "
            "surtout restauration, voyage et hôtellerie.",
            "**À note égale, le style du texte ne distingue pas les avis supprimés** : ni la "
            "longueur, ni le thème une fois le secteur connu. L'écart du tableau 7 peut venir du "
            "même effet : un texte trahit son secteur et sa fiche.",
            "À la lecture, les avis 5 étoiles supprimés citent souvent un employé par son prénom, "
            "et quelques avis 1 étoile supprimés sont republiés à l'identique. Observé sur un "
            "échantillon de lecture, non mesuré ici."):
        P(doc, texte, "List Bullet")

    doc.add_heading("Réserves", level=1)
    for texte in (
            "Contrôle par secteur : l'écart-type suppose des avis indépendants. Les suppressions "
            "étant groupées par fiche, le vrai écart-type est plus large : le contrôle est "
            "plutôt favorable aux groupes, et aucun ne le franchit.",
            "Avec 4 groupes, les groupes restent larges : ils décrivent un thème dominant, "
            "pas chaque avis.",
            "En 1 étoile, la plupart des groupes ne comptent que 13 à 19 suppressions, dont "
            "jusqu'à 39 % sur une seule fiche."):
        P(doc, texte, "List Bullet")
    P(doc, "Sources : etudes-ponctuelles/2026-09-28-kmeans-us-1-5-etoiles/ (calcul.py, note.py, "
           "sorties/A1-groupes.csv, B1-ecart-centres.csv, A2-appartenance-avis.csv). Vecteurs : "
           "data/embeddings/03B_e5base.parquet.", "NoteTableau")

    doc.save(LIVRABLE)
    print(f"écrit : {LIVRABLE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
