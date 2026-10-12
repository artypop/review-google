#!/usr/bin/env python3
"""Écrit `livrables/regroupement-textes-us.docx` en entier.

    PYTHONPATH=.venv/Lib/site-packages <python uv> etudes-ponctuelles/2026-09-29-synthese-textes/note.py

Remplace, pour ce document, les trois scripts qui l'écrivaient par morceaux
(`2026-09-29-hdbscan-residus-us/note.py`, `2026-09-29-home-services-us/note.py`,
`logistic-regression-study/python/07D_note.py`), à la demande de Matthieu du
2026-09-29 : ce qu'on a fait, puis les résultats, puis une courte conclusion.

Aucun chiffre calculé ici : tout est lu dans les sorties des études.
  A  etudes-ponctuelles/2026-09-29-hdbscan-residus-us/sorties/     A1, A2
  B  etudes-ponctuelles/2026-09-30-avis-antiparasitaires/sorties/regroupement/  A1, A2, A4, B1
  C  logistic-regression-study/output-study/2026-09-29-sorties-07D(-min30)/
  D  etudes-ponctuelles/2026-09-29-quasi-copies/sorties/(min30/)   A1
  E  etudes-ponctuelles/2026-09-28-embeddings-further/sorties/     A2, A3
Le script s'arrête si un chiffre ne correspond plus au texte qui le commente.

Étiquettes des groupes : lecture de 6 à 8 textes par groupe à l'écran
(2026-09-29), jamais enregistrés. Sans pandas (bloqué sur le poste).
"""
from __future__ import annotations

import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from docx import Document  # noqa: E402
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT  # noqa: E402
from docx.enum.text import WD_ALIGN_PARAGRAPH  # noqa: E402
from docx.oxml import OxmlElement  # noqa: E402
from docx.oxml.ns import qn  # noqa: E402
from docx.shared import Cm, Pt, RGBColor  # noqa: E402

DOSSIER = Path(__file__).resolve().parent
RACINE = DOSSIER.parents[1]
EP = RACINE / "etudes-ponctuelles"
A = EP / "2026-09-29-hdbscan-residus-us" / "sorties"
B = EP / "2026-09-30-avis-antiparasitaires" / "sorties" / "regroupement"
C80 = RACINE / "logistic-regression-study" / "output-study" / "2026-09-29-sorties-07D"
C30 = RACINE / "logistic-regression-study" / "output-study" / "2026-09-29-sorties-07D-min30"
D = EP / "2026-09-29-quasi-copies" / "sorties"
E = EP / "2026-09-28-embeddings-further" / "sorties"
FIGURES = DOSSIER / "sorties"
MODELE = RACINE / "livrables" / "analyses-complémentaires.docx"
LIVRABLE = RACINE / "livrables" / "regroupement-textes-us.docx"
SEUIL = 97.5

# Partie A : groupe -> (étiquette, avis attendus, lecture), sans les quatre chaînes antiparasitaires
GROUPES_A = {
    14: ("Jugements d'un à trois mots (« Good job », « Nice »)", 106, "6 fiches"),
    66: ("1 étoile : frais, facturation, location de voiture", 90, "10 fiches"),
    33: ("Soins esthétiques, praticienne citée par son prénom", 182, "8 fiches"),
    3: ("Station de lavage, employé cité par son prénom", 53, "7 sur 8 sur une fiche"),
    8: ("Lavage auto, employé cité, avis courts", 48, "une seule fiche"),
    0: ("Revêtements de sol, vendeur cité par son nom", 163, "contre-exemple"),
}
# Partie B : avis des fiches antiparasitaires américaines, embeddings Colab
POP_TOUS, POP_RECENTS = "cinq_etoiles", "cinq_etoiles_recents"
# Partie C : types de lien entre une copie et son jumeau
TYPES = ["un auteur, plusieurs fiches", "doublon", "gabarit sur une fiche",
         "gabarit sur une enseigne", "rencontre"]
NOMS_TYPES = {"un auteur, plusieurs fiches": "Même auteur, plusieurs fiches",
              "doublon": "Même auteur, même fiche",
              "gabarit sur une fiche": "Auteurs différents, même fiche",
              "gabarit sur une enseigne": "Auteurs différents, même enseigne",
              "rencontre": "Auteurs et enseignes différents", "tous": "Total"}
PASSAGES = [("tous", "Tous"), ("US", "US"), ("Europe", "Europe")]


def lire(chemin):
    with chemin.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def virgule(x, d=1):
    return f"{float(x):.{d}f}".replace(".", ",")


def espace(n):
    return f"{round(float(n)):,}".replace(",", " ")


def pct(x, d=0):
    return f"{virgule(x, d)} %"


def verifier(condition, message):
    if not condition:
        raise SystemExit(f"arrêt : {message} ; texte à réécrire")


# ---------------------------------------------------------------------------
# Figures
# ---------------------------------------------------------------------------
SURFACE = "#fcfcfb"; ENCRE = "#0b0b0b"; ENCRE_DOUCE = "#52514e"; GRILLE = "#e4e3df"
BLEU = "#2a78d6"; GRIS = "#bdbcb8"


def axes_propres(ax):
    for c in ("top", "right", "left"):
        ax.spines[c].set_visible(False)
    ax.spines["bottom"].set_color(GRILLE)
    ax.tick_params(colors=ENCRE_DOUCE, labelsize=7.5, length=0)


def barres_paires(chemin, titre, sous_titre, noms, obs, att, seuils=(), gauche=0.45):
    """Barres « supprimés » et « attendus » par groupe, du haut vers le bas.
    `seuils` : liste de (valeurs par groupe, légende, couleur)."""
    noms, obs, att = noms[::-1], obs[::-1], att[::-1]
    y = np.arange(len(noms))
    fig, ax = plt.subplots(figsize=(7.2, 0.42 * len(noms) + 1.2), dpi=150)
    fig.patch.set_facecolor(SURFACE); ax.set_facecolor(SURFACE)
    haut = 1 - 0.95 / (0.42 * len(noms) + 1.2)
    fig.subplots_adjust(left=gauche, right=0.96, top=haut, bottom=0.45 / (0.42 * len(noms) + 1.2))
    h = 0.36
    ax.barh(y + h / 2, obs, h, color=BLEU, label="supprimés")
    ax.barh(y - h / 2, att, h, color=GRIS, label="attendus")
    for valeurs, legende, couleur in seuils:
        ax.scatter(valeurs[::-1], y + h / 2, marker="|", s=160, linewidths=2, color=couleur,
                   zorder=3, label=legende)
    for yi, o in zip(y, obs):
        if seuils:   # chiffre dans la barre, pour laisser la place aux seuils
            ax.text(o - max(obs) * 0.01, yi + h / 2, str(int(o)), va="center", ha="right",
                    fontsize=7, color="white", fontweight="bold")
        else:
            ax.text(o + max(obs) * 0.012, yi + h / 2, str(int(o)), va="center", fontsize=7,
                    color=ENCRE)
    ax.set_yticks(y, noms, fontsize=7.5)
    axes_propres(ax)
    ax.set_xlabel("avis supprimés", fontsize=7.5, color=ENCRE_DOUCE)
    ax.legend(frameon=False, fontsize=7, loc="lower left", bbox_to_anchor=(-0.02, 1.0), ncol=3)
    fig.text(0.012, 0.985, titre, fontsize=10.5, color=ENCRE, va="top")
    fig.text(0.012, 0.985 - 0.32 / (0.42 * len(noms) + 1.2), sous_titre, fontsize=8,
             color=ENCRE_DOUCE, va="top")
    fig.savefig(chemin, dpi=150, facecolor=SURFACE)
    plt.close(fig)


def barres_parts(chemin, panneaux):
    """Part supprimée par groupe (du plus court au plus long), un panneau par population,
    avec la part moyenne en tirets."""
    fig, axes = plt.subplots(1, len(panneaux), figsize=(7.2, 2.9), dpi=150)
    fig.patch.set_facecolor(SURFACE)
    fig.subplots_adjust(left=0.08, right=0.98, top=0.72, bottom=0.2, wspace=0.35)
    for ax, (titre, groupes, moyenne) in zip(axes, panneaux):
        ax.set_facecolor(SURFACE)
        x = np.arange(len(groupes))
        parts = [float(r["part_supprimee_pct"]) for r in groupes]
        ax.bar(x, parts, 0.6, color=BLEU)
        ax.axhline(moyenne, color=ENCRE_DOUCE, lw=1, ls="--")
        for xi, p_, r in zip(x, parts, groupes):
            ax.text(xi, p_ * 1.02, f"{virgule(p_, 2)} %", ha="center", va="bottom", fontsize=7,
                    color=ENCRE)
        ax.set_xticks(x, [f"{r['longueur_mediane']} car.\n{espace(r['avis'])} avis"
                          for r in groupes], fontsize=6.5)
        for c in ("top", "right"):
            ax.spines[c].set_visible(False)
        ax.spines["left"].set_color(GRILLE); ax.spines["bottom"].set_color(GRILLE)
        ax.tick_params(colors=ENCRE_DOUCE, labelsize=6.5, length=0)
        ax.set_ylim(0, max(parts) * 1.3)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{virgule(v, 1)} %"))
        ax.set_title(titre, fontsize=8.5, color=ENCRE, loc="left")
    fig.text(0.012, 0.97, "Part des avis supprimés par groupe de textes (KMeans, K = 4)",
             fontsize=10.5, color=ENCRE, va="top")
    fig.text(0.012, 0.9, "Fiches antiparasitaires américaines ; groupes rangés par longueur "
             "médiane ; tirets : part moyenne", fontsize=8, color=ENCRE_DOUCE, va="top")
    fig.savefig(chemin, dpi=150, facecolor=SURFACE)
    plt.close(fig)
def barres_types(chemin, noms, parts, avis, base):
    noms, parts, avis = noms[::-1], parts[::-1], avis[::-1]
    y = np.arange(len(noms))
    fig, ax = plt.subplots(figsize=(7.2, 2.9), dpi=150)
    fig.patch.set_facecolor(SURFACE); ax.set_facecolor(SURFACE)
    fig.subplots_adjust(left=0.40, right=0.94, top=0.78, bottom=0.14)
    ax.barh(y, parts, 0.55, color=BLEU)
    ax.axvline(base, color=ENCRE_DOUCE, lw=1, ls="--")
    ax.text(base + 0.8, len(noms) - 0.45, f"panel entier : {virgule(base)} %", fontsize=7,
            color=ENCRE_DOUCE)
    for yi, p, n in zip(y, parts, avis):
        ax.text(p + 0.8, yi, f"{virgule(p, 0)} %  ({n} avis)", va="center", fontsize=7,
                color=ENCRE)
    ax.set_yticks(y, noms, fontsize=7.5)
    axes_propres(ax)
    ax.set_xlim(0, max(parts) * 1.35)
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{virgule(v, 0)} %"))
    fig.text(0.012, 0.97, "Part des copies supprimées selon le lien avec leur jumeau",
             fontsize=10.5, color=ENCRE, va="top")
    fig.text(0.012, 0.89, "Panel 03B, copies de 80 caractères ou plus, similarité de 0,97 ou plus",
             fontsize=8, color=ENCRE_DOUCE, va="top")
    fig.savefig(chemin, dpi=150, facecolor=SURFACE)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Document
# ---------------------------------------------------------------------------
def P(doc, texte, style=None):
    p = doc.add_paragraph(style=style)
    for i, m in enumerate(texte.split("**")):
        if m:
            p.add_run(m).bold = i % 2 == 1
    return p


def puces(doc, textes):
    for t in textes:
        P(doc, t, "List Bullet")


def fond(cell, couleur):
    sh = OxmlElement("w:shd")
    sh.set(qn("w:val"), "clear"); sh.set(qn("w:color"), "auto"); sh.set(qn("w:fill"), couleur)
    cell._tc.get_or_add_tcPr().append(sh)


def tableau(doc, titre, entetes, lignes, largeurs, note=None):
    doc.add_paragraph(titre, style="TitreTableau")
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
    for i, rangee in enumerate([entetes] + lignes):
        for j, val in enumerate(rangee):
            c = t.rows[i].cells[j]
            c.width = Cm(largeurs[j])
            c.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            p = c.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT if j == 0 else WD_ALIGN_PARAGRAPH.RIGHT
            texte, gras = val if isinstance(val, tuple) else (val, False)
            r = p.add_run(str(texte)); r.font.size = Pt(9); r.bold = gras
            if i == 0:
                r.bold = True; r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF); fond(c, "322954")
            elif i % 2 == 0:
                fond(c, "F4F4F7")
    for j, gc in enumerate(t._tbl.tblGrid.findall(qn("w:gridCol"))):
        gc.set(qn("w:w"), str(int(largeurs[j] * 567)))
    if note:
        doc.add_paragraph(note, style="NoteTableau")


def figure(doc, chemin, legende, largeur=15.5):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(str(chemin), width=Cm(largeur))
    doc.add_paragraph(legende, style="Legende")


def document_vide():
    doc = Document(MODELE)
    corps = doc.element.body
    for e in list(corps):
        if e.tag != qn("w:sectPr"):
            corps.remove(e)
    for s in doc.sections:
        for zone in (s.header, s.footer, s.first_page_header, s.first_page_footer):
            for p in zone.paragraphs:
                for r in p.runs:
                    r.text = ""
    return doc


# ---------------------------------------------------------------------------
def main() -> int:
    FIGURES.mkdir(parents=True, exist_ok=True)

    # --- A : regroupement des textes US ------------------------------------
    a_reg = {(r["population"], r["vecteurs"]): r for r in lire(A / "A1-regroupements.csv")}
    a_grp = {int(r["groupe"]): r for r in lire(A / "A2-groupes.csv")
             if r["population"] == "sans_enseignes" and r["vecteurs"] == "corriges"}
    for g, (_, n, _) in GROUPES_A.items():
        verifier(int(a_grp[g]["n_avis"]) == n, f"partie A, groupe {g} : effectif changé")
    ar, ab = a_reg[("sans_enseignes", "corriges")], a_reg[("sans_enseignes", "bruts")]
    a_groupes = [r for g, r in a_grp.items() if g >= 0]
    a_hors = sum(r["hors_du_hasard"] != "" for r in a_groupes)
    a_trois = [a_grp[g] for g in (14, 33, 66)]
    a_n_trois = sum(int(r["n_supprimes"]) for r in a_trois)

    # --- B : antiparasitaires US ------------------------------------------------
    b_dec = lire(B / "A1-decoupages.csv")
    b_grp = lire(B / "A2-groupes.csv")
    b_vois = lire(B / "B1-voisins.csv")[0]
    b_per = lire(B / "A4-periodes.csv")

    def b_decoupage(pop, methode, k):
        return next(r for r in b_dec if r["population"] == pop and r["methode"] == methode
                    and r["k"] == str(k))

    def b_groupes(pop, k):
        return sorted((r for r in b_grp if r["population"] == pop and r["methode"] == "kmeans"
                       and r["k"] == str(k)), key=lambda r: int(r["longueur_mediane"]))

    kmeans = [(p, k) for p in (POP_TOUS, POP_RECENTS) for k in range(2, 11)]
    verifier(all(float(b_decoupage(p, "kmeans", k)[f"rang_{t}_pct"]) < SEUIL
                 for p, k in kmeans for t in ("periode", "fiche")),
             "partie B, un découpage KMeans dépasse le hasard")
    hdb = b_decoupage(POP_RECENTS, "hdbscan", "")
    verifier(float(hdb["rang_periode_pct"]) < SEUIL and float(hdb["rang_fiche_pct"]) < SEUIL,
             "partie B, HDBSCAN dépasse le hasard")
    verifier(float(b_vois["rang_periode_pct"]) < SEUIL and float(b_vois["rang_fiche_pct"]) < SEUIL,
             "partie B, les voisins dépassent le hasard")
    tous4, rec4 = b_groupes(POP_TOUS, 4), b_groupes(POP_RECENTS, 4)
    d_tous, d_rec = b_decoupage(POP_TOUS, "kmeans", 2), b_decoupage(POP_RECENTS, "kmeans", 2)
    per_tous = [r for r in b_per if r["population"] == POP_TOUS]
    hdb_grp = sorted((r for r in b_grp if r["population"] == POP_RECENTS
                      and r["methode"] == "hdbscan" and r["groupe"] != "-1"),
                     key=lambda r: -float(r["part_supprimee_pct"]))
    hdb_top = hdb_grp[0]
    # --- C : régression et copies -----------------------------------------
    eff80 = {(r["passage"], r["variable"]): r for r in lire(C80 / "07D_effets_6_passages.csv")}
    eff30 = {(r["passage"], r["variable"]): r for r in lire(C30 / "07D_effets_6_passages.csv")}
    cas80 = {(r["passage"], r["cas"]): r for r in lire(C80 / "07D_effectifs_signaux.csv")}
    cas30 = {(r["passage"], r["cas"]): r for r in lire(C30 / "07D_effectifs_signaux.csv")}
    bilan = {r["passage"]: r for r in lire(C80 / "07D_passages.csv")}
    t80 = {r["type"]: r for r in lire(D / "A1-types.csv")}
    t30 = {r["type"]: r for r in lire(D / "min30" / "A1-types.csv")}
    fiches = {(r["perimetre"], r["groupe"]): r for r in lire(E / "A2-memes-fiches.csv")}
    tc, tsr = "tous_complet", "tous_sans_retraits"
    verifier(int(t80["tous"]["avis"]) == int(cas80[(tc, "copie_ou_quasi")]["avis"])
             and int(t30["tous"]["avis"]) == int(cas30[(tc, "copie_ou_quasi")]["avis"]),
             "partie C, types de paires et régression ne portent pas sur les mêmes copies")

    def rr(effets, passage, var, d=1):
        r = effets[(passage, var)]
        net = float(r["borne_basse"]) > 1 or float(r["borne_haute"]) < 1
        return (f"×{virgule(r['risque_relatif'], d)} [{virgule(r['borne_basse'], d)} – "
                f"{virgule(r['borne_haute'], d)}]", net)

    for (passage, var), r in eff80.items():
        if var == "texte_court":
            verifier(float(r["borne_basse"]) <= 1 <= float(r["borne_haute"]),
                     f"texte court net dans {passage}")
        if var == "copie_ou_quasi":
            verifier(float(r["borne_basse"]) > 1, f"copie non nette dans {passage}")
    rrs = [float(eff80[(f"{p}_{j}", "copie_ou_quasi")]["risque_relatif"])
           for p, _ in PASSAGES for j in ("complet", "sans_retraits")]
    cop, lon = cas80[(tsr, "copie_ou_quasi")], cas80[(tsr, "texte_60_et_plus")]
    cop_c = cas80[(tc, "copie_ou_quasi")]
    base = 100 * int(bilan[tc]["suppressions"]) / int(bilan[tc]["avis"])
    f_cop = fiches[("sans les six enseignes", "copie ou quasi-copie")]
    f_aut = fiches[("sans les six enseignes", "autres avis des mêmes fiches")]

    def n(t, ty, c):
        return int(float(t[ty][c]))

    lies = TYPES[:3]
    n_lie, s_lie = sum(n(t80, ty, "avis") for ty in lies), sum(n(t80, ty, "supprimes") for ty in lies)
    n_sans, s_sans = (sum(n(t80, ty, "avis") for ty in TYPES[3:]),
                      sum(n(t80, ty, "supprimes") for ty in TYPES[3:]))
    un = t80["un auteur, plusieurs fiches"]
    ajout = {ty: (n(t30, ty, "avis") - n(t80, ty, "avis"),
                  n(t30, ty, "supprimes") - n(t80, ty, "supprimes")) for ty in TYPES}
    verifier(ajout["un auteur, plusieurs fiches"][0] == 0 and ajout["doublon"][0] == 0,
             "seuil 30 : ajouts côté même auteur")

    # --- Figures -------------------------------------------------------------
    fig1, fig2, fig3 = (FIGURES / "figure1-groupes-us.png", FIGURES / "figure2-antiparasitaires.png",
                        FIGURES / "figure3-copies.png")
    barres_paires(fig1, "Groupes de textes à retenir, avis US en anglais",
                  "Sans les quatre chaînes antiparasitaires ; attendus d'après le secteur et la note",
                  [GROUPES_A[g][0].split(" (")[0] for g in GROUPES_A],
                  [int(a_grp[g]["n_supprimes"]) for g in GROUPES_A],
                  [float(a_grp[g]["attendu_par_case"]) for g in GROUPES_A])
    barres_parts(fig2, [
        ("Tous les avis 5 étoiles", tous4, float(d_tous["part_supprimee_pct"])),
        ("Avis 5 étoiles publiés depuis juin 2026", rec4, float(d_rec["part_supprimee_pct"]))])
    barres_types(fig3, [NOMS_TYPES[ty] for ty in TYPES],
                 [float(t80[ty]["part_supprimee_pct"]) for ty in TYPES],
                 [n(t80, ty, "avis") for ty in TYPES], base)

    # --- Document ------------------------------------------------------------
    doc = document_vide()
    doc.add_paragraph("Ce que les textes disent des suppressions d'avis", style="Title")
    P(doc, f"Panel 03B : {espace(bilan[tc]['avis'])} avis, {espace(bilan[tc]['suppressions'])} "
           "suppressions, dont 26 168 avis avec texte. Études du 29 septembre 2026.")

    doc.add_heading("1. Ce qu'on a fait", level=1)
    P(doc, "Chaque avis avec texte est traduit en une liste de 768 nombres par le modèle e5-base "
           "(embedding) : deux textes au sens proche ont des listes proches.")

    doc.add_heading("Regrouper les textes américains", level=2)
    puces(doc, [
        f"**Avis US en anglais**, sans les quatre chaînes antiparasitaires : "
        f"{espace(ar['n_avis'])} avis, {espace(ar['n_supprimes'])} supprimés.",
        "**Retrait du secteur et de la note** : chaque avis perd la moyenne des avis de même "
        "secteur et de même note. Il reste ce qui le distingue : tournure, longueur, prénom, "
        "plainte précise.",
        "**Regroupement** : l'ACP résume les 768 nombres en 50 ; t-SNE place les avis sur une "
        "carte où les textes proches restent voisins ; HDBSCAN forme des groupes là où les avis "
        "sont serrés, laisse les avis isolés hors groupe et ne fixe pas le nombre de groupes.",
        "**Comparaison** : suppressions de chaque groupe face à celles attendues d'après son "
        "secteur et sa note, et face à 2 000 groupes tirés au hasard. Un groupe n'est retenu que "
        "s'il réapparaît quand on relance le calcul.",
    ])

    doc.add_heading("Zoom sur les antiparasitaires américains", level=2)
    puces(doc, [
        "**Tous les avis avec texte de 174 fiches** home services américaines (« pest » dans "
        "le nom, plus la chaîne Bulwark Exterminating), publiés depuis 2004 : 259 901 avis, "
        "1 086 supprimés pendant le suivi.",
        "**Embeddings calculés sur Colab (GPU)** avec le même modèle ; sur 2 075 avis déjà "
        "encodés en local, les vecteurs sont identiques (similarité d'au moins 0,9999).",
        f"**5 étoiles seulement** : {espace(d_tous['supprimes'])} des 1 086 suppressions ; les "
        "autres notes en portent trop peu pour être découpées.",
        f"**L'âge de l'avis est pris en compte** : la part supprimée va de "
        f"{pct(per_tous[0]['part_supprimee_pct'], 1)} pour les avis publiés en août 2026 à "
        f"{pct(per_tous[-1]['part_supprimee_pct'], 2)} avant 2023. Les attendus et les tirages se "
        "font à période de publication égale (8 périodes).",
        f"**Deux populations** : tous les avis 5 étoiles ({espace(d_tous['avis'])} avis, "
        f"{espace(d_tous['supprimes'])} supprimés), et ceux publiés depuis le 1er juin 2026 "
        f"({espace(d_rec['avis'])} avis, {d_rec['supprimes']} supprimés).",
        "**KMeans de 2 à 10 groupes** sur les deux ; **HDBSCAN** et les **voisins de texte** "
        "hors de la fiche sur les avis récents.",
        "**Deux tirages au hasard** : à période égale, puis à fiche et période égales.",
    ])
    doc.add_heading("Mesurer les copies dans la régression", level=2)
    puces(doc, [
        "**La régression réduite du 28/09** (note, pic d'avis de la fiche, photo, photos de "
        "l'auteur, Local Guide 4 et plus, réponse du propriétaire, secteur, exposition), sur six "
        "passages : US, Europe, tous ; complet, puis sans les 2 salles de sport espagnoles et les "
        "fiches antiparasitaires américaines (« sans retraits »).",
        "**Copie** : texte d'au moins 80 caractères dont l'avis le plus proche du panel a une "
        "similarité de 0,97 ou plus. Variante à 30 caractères.",
        "**Longueur** : texte de moins de 60 caractères, et avis sans texte, face aux textes de "
        "60 caractères ou plus.",
        "**Lien avec le jumeau** : chaque copie est rattachée à son avis le plus proche, même "
        "auteur ou non, même fiche ou non.",
        "**Contrôle** : sans ces variables, le calcul retrouve à l'identique la régression du 28/09.",
    ])

    doc.add_heading("2. Résultats", level=1)

    doc.add_heading("Les groupes de textes US", level=2)
    puces(doc, [
        f"**Les groupes décrivent la forme des avis** : avant retrait, "
        f"{pct(ab['part_secteur_principal_pct'])} des avis d'un groupe venaient de son secteur "
        f"principal ; après, {pct(ar['part_secteur_principal_pct'])} "
        f"(hasard : {pct(ar['part_secteur_principal_hasard_pct'])}).",
        f"**{a_hors} groupes sur {len(a_groupes)} s'écartent du hasard**, pour environ "
        f"{virgule(0.05 * len(a_groupes), 0)} attendus par le seul hasard.",
        f"**Trois groupes répartis sur plusieurs fiches sont plus supprimés** : jugements d'un à "
        f"trois mots, soins esthétiques où la praticienne est citée, plaintes sur des frais. Ils "
        f"portent {a_n_trois} des {espace(ar['n_supprimes'])} suppressions.",
        f"**Citer un employé ne suffit pas** : revêtements de sol, vendeur nommé, "
        f"{a_grp[0]['n_supprimes']} suppression pour {virgule(a_grp[0]['attendu_par_case'], 0)} "
        "attendues.",
    ])
    figure(doc, fig1, "Figure 1. Suppressions observées et attendues, groupes du tableau 1.")
    tableau(doc, "Tableau 1. Les groupes à retenir",
            ["Groupe de textes", "Avis", "Supprimés", "Attendus", "Répartition"],
            [[GROUPES_A[g][0], espace(a_grp[g]["n_avis"]), (a_grp[g]["n_supprimes"], True),
              virgule(a_grp[g]["attendu_par_case"]), GROUPES_A[g][2]] for g in GROUPES_A],
            [7.6, 1.4, 1.8, 1.8, 3.6],
            "Attendus : suppressions si chaque avis du groupe était supprimé au taux moyen de son "
            "secteur et de sa note.")

    doc.add_heading("Le zoom antiparasitaires", level=2)
    puces(doc, [
        f"**Aucun groupe de supprimés ne se forme** : à K = 4, les groupes de tous les avis "
        f"5 étoiles sont supprimés entre {pct(min(float(r['part_supprimee_pct']) for r in tous4), 2)} "
        f"et {pct(max(float(r['part_supprimee_pct']) for r in tous4), 2)} "
        f"(moyenne {pct(d_tous['part_supprimee_pct'], 2)}) ; ceux des avis récents entre "
        f"{pct(min(float(r['part_supprimee_pct']) for r in rec4), 1)} et "
        f"{pct(max(float(r['part_supprimee_pct']) for r in rec4), 1)} "
        f"(moyenne {pct(d_rec['part_supprimee_pct'], 1)}).",
        "**Aucun découpage KMeans ne dépasse le hasard**, de 2 à 10 groupes, à période égale "
        "comme à fiche égale (tableau 2).",
        f"**KMeans découpe surtout selon la longueur** : médianes de "
        f"{tous4[0]['longueur_mediane']} à {tous4[-1]['longueur_mediane']} caractères à K = 4.",
        f"**HDBSCAN** forme {len(hdb_grp)} petits groupes ; le plus supprimé compte "
        f"{hdb_top['supprimes']} suppressions sur {hdb_top['avis']} avis, un écart que le hasard "
        f"produit aussi ({pct(hdb['rang_periode_pct'])} des tirages à période égale font moins).",
        f"**Voisins** : un avis supprimé a {pct(b_vois['voisins_supprimes_si_supprime_pct'], 1)} "
        f"de voisins supprimés, un avis resté {pct(b_vois['voisins_supprimes_si_reste_pct'], 1)} ; "
        f"écart de {virgule(b_vois['ecart_points'])} point, dans la marge du hasard.",
    ])
    figure(doc, fig2, "Figure 2. Part des avis supprimés par groupe de textes (KMeans, K = 4), "
                      "avis 5 étoiles des fiches antiparasitaires américaines.")

    def cellule(pop, methode, k, tirage):
        v = float(b_decoupage(pop, methode, k)[f"rang_{tirage}_pct"])
        return (pct(v, 1), v > SEUIL)

    tableau(doc, "Tableau 2. Le groupe le plus supprimé dépasse-t-il le hasard ?",
            ["Découpage", "Tous 5 étoiles, période égale", "Tous 5 étoiles, fiche égale",
             "Récents, période égale", "Récents, fiche égale"],
            [[f"KMeans, K = {k}", cellule(POP_TOUS, "kmeans", k, "periode"),
              cellule(POP_TOUS, "kmeans", k, "fiche"), cellule(POP_RECENTS, "kmeans", k, "periode"),
              cellule(POP_RECENTS, "kmeans", k, "fiche")] for k in range(2, 11)]
            + [["HDBSCAN", "", "", cellule(POP_RECENTS, "hdbscan", "", "periode"),
                cellule(POP_RECENTS, "hdbscan", "", "fiche")]],
            [3.2, 3.4, 3.4, 3.2, 3.2],
            "Part des tirages où le groupe le plus supprimé dépasse moins ses attendus que dans "
            "l'observé. Au-dessus de 97,5 %, le découpage isolerait les suppressions ; aucune case "
            "n'y arrive. Une valeur très basse veut dire que les suppressions se répartissent "
            "entre les groupes plus régulièrement encore qu'au hasard. Récents : avis publiés depuis le 1er juin 2026. HDBSCAN n'est calculé que "
            "sur les avis récents.")
    doc.add_heading("Les copies", level=2)
    puces(doc, [
        f"**Une copie risque {virgule(eff80[(tsr, 'copie_ou_quasi')]['risque_relatif'], 0)} fois "
        f"plus d'être supprimée**, à caractéristiques égales et sans les retraits ; "
        f"×{virgule(min(rrs), 1)} à ×{virgule(max(rrs), 0)} selon le passage. Sur 10 000 copies, "
        f"{espace(cop['taux_pour_10000_avis'])} sont supprimées, contre "
        f"{espace(lon['taux_pour_10000_avis'])} pour les textes de 60 caractères ou plus.",
        f"**Ce sont les copies liées à une fiche ou à un auteur** : {n_lie} avis, "
        f"{pct(100 * s_lie / n_lie)} supprimés, le plus souvent déposés le même jour que leur "
        f"jumeau. Auteurs et fiches différents : {n_sans} avis, {s_sans} supprimés.",
        f"**Un auteur qui poste le même avis sur plusieurs succursales** voit son second avis "
        f"supprimé à {pct(un['supprime_si_second_depose_pct'])}, le premier à "
        f"{pct(un['supprime_si_premier_depose_pct'])}.",
        f"**Dans une même fiche**, {pct(f_cop['part_supprimee_pct'])} des copies sont supprimées "
        f"contre {pct(f_aut['part_supprimee_pct'])} des autres avis (sans les six enseignes).",
        f"**Ces avis sont rares** : {espace(cop_c['avis'])} sur {espace(bilan[tc]['avis'])}, "
        f"qui portent {cop_c['suppressions']} des {espace(bilan[tc]['suppressions'])} suppressions.",
        f"**À 30 caractères**, les copies passent à {espace(cas30[(tc, 'copie_ou_quasi')]['avis'])} "
        f"mais les suppressions à {cas30[(tc, 'copie_ou_quasi')]['suppressions']} : les ajouts "
        f"sont surtout des formules courantes sans lien ({ajout['rencontre'][0]} avis, "
        f"{ajout['rencontre'][1]} supprimés), et le risque tombe à "
        f"{rr(eff30, tsr, 'copie_ou_quasi')[0]}.",
        f"**La longueur n'a aucun effet** ({rr(eff80, tsr, 'texte_court', 2)[0]} pour un texte de "
        f"moins de 60 caractères) ; un avis sans texte est un peu moins supprimé sans les "
        f"retraits ({rr(eff80, tsr, 'sans_texte', 2)[0]}).",
    ])
    figure(doc, fig3, "Figure 3. Part des copies supprimées selon le lien avec leur jumeau.")
    lignes = [["Copie, 80 caractères ou plus"] + [rr(eff80, f"{p}_{j}", "copie_ou_quasi")
                                                  for p, _ in PASSAGES for j in ("complet", "sans_retraits")],
              ["Copie, 30 caractères ou plus"] + [rr(eff30, f"{p}_{j}", "copie_ou_quasi")
                                                  for p, _ in PASSAGES for j in ("complet", "sans_retraits")],
              ["Texte de moins de 60 car."] + [rr(eff80, f"{p}_{j}", "texte_court", 2)
                                               for p, _ in PASSAGES for j in ("complet", "sans_retraits")],
              ["Sans texte"] + [rr(eff80, f"{p}_{j}", "sans_texte", 2)
                                for p, _ in PASSAGES for j in ("complet", "sans_retraits")]]
    tableau(doc, "Tableau 3. Risque de suppression, six passages",
            ["Signal"] + [f"{nm} {'complet' if j == 'complet' else 'sans retraits'}"
                          for _, nm in PASSAGES for j in ("complet", "sans_retraits")],
            lignes, [3.4] + [2.35] * 6,
            "Risque par rapport à un texte de 60 caractères ou plus sans copie, à note, secteur, "
            "photo, auteur, réponse, pic d'avis et exposition égaux ; fourchette à 95 %. En gras : "
            "fourchette qui ne contient pas 1. Les lignes « copie » viennent de deux modèles, un "
            "par seuil.")
    tableau(doc, "Tableau 4. Les copies selon le lien avec leur jumeau",
            ["Lien avec le jumeau", "Avis", "Supprimés", "Part supprimée", "Texte identique",
             "Déposés à moins d'un jour"],
            [[NOMS_TYPES[ty], n(t80, ty, "avis"), n(t80, ty, "supprimes"),
              (pct(t80[ty]["part_supprimee_pct"]), ty == "tous"), pct(t80[ty]["texte_identique_pct"]),
              pct(t80[ty]["ecart_moins_d_un_jour_pct"])] for ty in TYPES + ["tous"]],
            [5.6, 1.4, 1.8, 2.2, 2.4, 3.0],
            "Copies de 80 caractères ou plus, tout le panel. Un auteur est repéré par le lien de "
            "son profil : une personne avec deux comptes compte pour deux.")

    doc.add_heading("3. Conclusion", level=1)
    puces(doc, [
        "**Le texte explique une petite part des suppressions** : aucun groupe de textes ne les "
        "isole, et la longueur n'a pas d'effet.",
        f"**Le seul signal net est la copie liée à une fiche ou à un auteur** : risque multiplié "
        f"par {virgule(eff80[(tsr, 'copie_ou_quasi')]['risque_relatif'], 0)}, mais sur "
        f"{pct(100 * int(cop_c['avis']) / int(bilan[tc]['avis']), 1)} des avis et environ "
        f"{pct(100 * int(cop_c['suppressions']) / int(bilan[tc]['suppressions']))} des suppressions. "
        "Pour un commerçant : ne pas publier le même avis sur plusieurs fiches, ne pas faire "
        "recopier un texte préparé.",
        "**Chez les antiparasitaires américains, les avis supprimés ne forment aucun groupe de "
        "textes** : sur 242 011 avis 5 étoiles, à âge égal, ils ressemblent aux avis restés en "
        "ligne.",
        "**Hors des chaînes, l'éloge court et générique est une tendance fragile** ; la longueur "
        "seule ne le capte pas. Le mesurer directement (prénom d'employé cité, détail concret) "
        "est la dernière piste texte.",
        "**Réserves** : 10 à 57 suppressions derrière chaque signal ; un seul modèle d'embedding "
        "(e5-base).",
    ])
    P(doc, "Sources : etudes-ponctuelles/2026-09-29-hdbscan-residus-us/, 2026-09-30-avis-antiparasitaires/, "
           "2026-09-29-quasi-copies/, 2026-09-28-embeddings-further/ ; logistic-regression-study/"
           "python/07D_regression_signaux_texte.py et output-study/2026-09-29-sorties-07D(-min30)/. "
           "Document écrit par etudes-ponctuelles/2026-09-29-synthese-textes/note.py.", "NoteTableau")

    doc.save(LIVRABLE)
    print(f"écrit : {LIVRABLE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
