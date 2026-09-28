#!/usr/bin/env python3
"""Écrit `livrables/embeddings_further.docx` à partir des CSV de `calcul.py`.

    .venv/Scripts/python.exe etudes-ponctuelles/2026-09-28-embeddings-further/note.py

Aucun chiffre n'est calculé ici. Mise en page reprise des notes du 2026-09-28
(`2026-09-28-secteurs-et-concentration/note.py`, dont les fonctions de mise en
forme sont importées).
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from docx import Document  # noqa: E402
from docx.enum.text import WD_ALIGN_PARAGRAPH  # noqa: E402
from docx.shared import Cm, Pt  # noqa: E402

DOSSIER = Path(__file__).resolve().parent
RACINE = DOSSIER.parents[1]
SORTIES = DOSSIER / "sorties"
FIGURE = SORTIES / "figure1-tranches-similarite.png"
LIVRABLE = RACINE / "livrables" / "embeddings_further.docx"

_spec = importlib.util.spec_from_file_location(
    "mise_en_forme", RACINE / "etudes-ponctuelles" / "2026-09-28-secteurs-et-concentration" / "note.py")
mf = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mf)
P, tableau, styler, virgule, espace = mf.P, mf.tableau, mf.styler, mf.virgule, mf.espace


def csv(nom):
    return pd.read_csv(SORTIES / nom)


def figure():
    t = csv("A6-tranches-similarite.csv")
    fig, ax = plt.subplots(figsize=(6.6, 3.8), dpi=150)
    fig.patch.set_facecolor(mf.SURFACE); ax.set_facecolor(mf.SURFACE)
    fig.subplots_adjust(left=0.08, right=0.98, top=0.78, bottom=0.2)
    for c in ("top", "right", "left"):
        ax.spines[c].set_visible(False)
    ax.spines["bottom"].set_color(mf.GRILLE)
    ax.tick_params(colors=mf.ENCRE_DOUCE, labelsize=8, length=0)
    ax.grid(True, axis="y", color=mf.GRILLE, lw=1, zorder=0)
    ax.set_axisbelow(True)
    tranches = list(t["tranche"].unique())
    larg = 0.38
    for decal, (p, couleur) in zip((-larg / 2, larg / 2), (("tout le panel", mf.BLEU),
                                                          ("sans les six enseignes", mf.GRIS))):
        d = t[t["perimetre"] == p].set_index("tranche").reindex(tranches)
        x = range(len(tranches))
        barres = ax.bar([i + decal for i in x], d["part_supprimee_pct"], width=larg,
                        color=couleur, zorder=3,
                        label="Tout le panel" if p == "tout le panel" else "Sans les six enseignes")
        for b, v in zip(barres, d["part_supprimee_pct"]):
            ax.text(b.get_x() + b.get_width() / 2, v + 1, f"{virgule(v, 0)} %", ha="center",
                    fontsize=7, color=mf.ENCRE)
    ax.set_xticks(range(len(tranches)), tranches)
    ax.set_yticks([0, 20, 40, 60], ["0 %", "20 %", "40 %", "60 %"])
    ax.set_ylim(0, 72)
    ax.set_xlabel("Similarité avec l'avis le plus proche du panel", fontsize=8.5,
                  color=mf.ENCRE_DOUCE, labelpad=6)
    leg = ax.legend(frameon=False, fontsize=8, loc="upper left")
    for tx in leg.get_texts():
        tx.set_color(mf.ENCRE_DOUCE)
    fig.text(0.012, 0.975, "Part des avis supprimés selon la ressemblance à un autre avis",
             fontsize=11, color=mf.ENCRE, va="top")
    fig.text(0.012, 0.91, "Avis d'au moins 80 caractères du panel 03B. À partir de 0,97, les "
             "deux textes sont réécrits l'un de l'autre.",
             fontsize=8.5, color=mf.ENCRE_DOUCE, va="top")
    fig.savefig(FIGURE, dpi=150, facecolor=mf.SURFACE)
    plt.close(fig)


def main() -> int:
    figure()
    a1 = csv("A1-classes.csv")
    a2 = csv("A2-memes-fiches.csv")
    a3 = csv("A3-ordre-dans-la-paire.csv")
    a7 = csv("A7-rapport-a-la-fiche.csv")
    b1 = csv("B1-intra-fiche.csv")

    def cl(p, c, col):
        return a1[(a1["perimetre"] == p) & (a1["classe"] == c)].iloc[0][col]

    def mf_part(groupe):
        return virgule(a2[(a2["perimetre"] == "sans les six enseignes")
                          & (a2["groupe"] == groupe)].iloc[0]["part_supprimee_pct"])

    def b(perimetre, note, col):
        return b1[(b1["perimetre"] == perimetre) & (b1["note"] == note)].iloc[0][col]

    rapport = (b("sans les six enseignes", "toutes notes", "contraste_observe")
               / b("sans les six enseignes, sans copies ni quasi-copies", "toutes notes",
                   "contraste_observe"))
    fiches_1 = b1.loc[b1["note"] == "1 étoile", "fiches"]

    doc = Document()
    styler(doc)
    pied = doc.sections[0].footer.paragraphs[0]
    r = pied.add_run("ReviewFlowz · Embeddings, pistes complémentaires · Septembre 2026")
    r.font.size = Pt(8.5); r.font.color.rgb = mf.GR
    doc.add_paragraph("Embeddings : deux pistes complémentaires", style="Title")
    doc.add_paragraph("ReviewFlowz · 28 septembre 2026", style="Subtitle")
    P(doc, "Suite de la section 5 d'analyses-complémentaires : regrouper les textes par thème "
           "ne distingue pas les avis supprimés une fois le secteur connu. Deux autres usages des "
           "vecteurs de texte sont testés ici, sur les 26 168 avis avec texte du panel 03B, "
           "toutes régions.")

    # 1 -------------------------------------------------------------------------
    doc.add_heading("1. Les avis presque identiques", level=1)
    for texte in (
            "Pour chaque avis, on cherche le texte le plus proche parmi les 26 167 autres et on "
            "mesure leur ressemblance (similarité, de 0 à 1).",
            "Les seuils ont été calés en lisant des paires : avec ce modèle, 0,94 à 0,97 réunit "
            "deux avis différents sur le même sujet ; à partir de 0,97, les deux textes sont "
            "réécrits l'un de l'autre ; à 0,99, 81 % des paires ont un texte identique.",
            "Seuls les textes d'au moins 80 caractères sont classés : deux « Great service » "
            "identiques ne disent rien."):
        P(doc, texte, "List Bullet")

    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(str(FIGURE), width=Cm(15.5))
    doc.add_paragraph("Figure 1. Part des avis supprimés selon la ressemblance à un autre avis.",
                      style="Legende")

    noms = {"copie": "Copie (0,99 et plus)", "quasi-copie": "Quasi-copie (0,97 à 0,99)",
            "même sujet": "Même sujet (0,94 à 0,97)",
            "sans jumeau": "Sans jumeau (moins de 0,94)",
            "texte de moins de 80 caractères": "Texte de moins de 80 caractères"}
    lignes = []
    for c, nom in noms.items():
        row = [nom]
        for p_ in ("tout le panel", "sans les six enseignes"):
            row += [espace(cl(p_, c, "avis")), espace(cl(p_, c, "supprimes")),
                    f"{virgule(cl(p_, c, 'part_supprimee_pct'))} %"]
        lignes.append(row)
    tableau(doc, "Tableau 1. Suppressions selon que l'avis a un jumeau",
            ["Classe", "Avis", "Supprimés", "Part", "Avis", "Supprimés", "Part"],
            lignes, [5.0, 1.8, 1.9, 1.6, 1.8, 1.9, 1.6])
    P(doc, "Colonnes 2 à 4 : tout le panel. Colonnes 5 à 7 : sans les six enseignes signalées. "
           f"Les {espace(cl('tout le panel', 'copie', 'supprimes'))} copies supprimées se répartissent "
           f"sur {int(cl('tout le panel', 'copie', 'fiches_touchees'))} fiches ; la plus touchée en "
           f"porte {virgule(cl('tout le panel', 'copie', 'part_supp_fiche_la_plus_touchee_pct'), 0)} %, "
           f"{virgule(cl('sans les six enseignes', 'copie', 'part_supp_fiche_la_plus_touchee_pct'), 0)} % "
           "sans les enseignes.", "NoteTableau")

    lignes = [[r.groupe[0].upper() + r.groupe[1:], espace(r.fiches), espace(r.avis), espace(r.supprimes),
               f"{virgule(r.part_supprimee_pct)} %"] for r in a2.itertuples()
              if r.perimetre == "sans les six enseignes"]
    tableau(doc, "Tableau 2. Dans les fiches qui ont au moins une copie ou quasi-copie, sans les six "
                 "enseignes", ["Avis d'au moins 80 caractères", "Fiches", "Avis", "Supprimés",
                               "Part supprimée"], lignes, [6.4, 2.2, 2.2, 2.4, 2.8])
    P(doc, "Même fiche, même secteur : la différence ne vient pas de la fiche.", "NoteTableau")

    def r7(p_, c, col):
        return a7[(a7["perimetre"] == p_) & (a7["classe"] == c)].iloc[0][col]

    def rapport_fiche(p_, c):
        borne = lambda x: virgule(x, 0 if x >= 100 else 1)
        return (f"×{virgule(r7(p_, c, 'rapport_observe_attendu'))} "
                f"[{borne(r7(p_, c, 'borne_basse'))} à {borne(r7(p_, c, 'borne_haute'))}]")

    lignes = []
    for c, nom in list(noms.items())[:4]:
        row = [nom]
        for p_ in ("tout le panel", "sans les six enseignes"):
            row += [espace(r7(p_, c, "supprimes")),
                    virgule(r7(p_, c, "attendus_au_taux_de_la_fiche"), 1), rapport_fiche(p_, c)]
        lignes.append(row)
    tableau(doc, "Tableau 3. Suppressions rapportées au taux de suppression de chaque fiche",
            ["Classe", "Observés", "Attendus", "Rapport", "Observés", "Attendus", "Rapport"],
            lignes, [4.2, 1.75, 1.75, 2.55, 1.75, 1.75, 2.55])
    P(doc, "Attendus : suppressions qu'aurait la classe si chaque avis était supprimé au taux des "
           "avis ordinaires de sa fiche (sans jumeau à 0,94 ou plus, l'avis lui-même exclu). "
           "Observés : suppressions constatées. Rapport : observés divisés par attendus ; ×1 = comme le reste de la fiche. Entre "
           "crochets : fourchette à 95 % par tirage des fiches. Colonnes 2 à 4 : tout le panel ; "
           "5 à 7 : sans les six enseignes. "
           f"{int(r7('tout le panel', 'copie', 'avis_ecartes_sans_fiche_ordinaire'))} copies sont "
           "écartées, leur fiche n'ayant aucun avis ordinaire.", "NoteTableau")

    x = a3[a3["perimetre"] == "sans les six enseignes"].set_index(["premier_supprime",
                                                                   "second_supprime"])["paires"]
    get = lambda a, b: int(x.get((a, b), 0))
    tableau(doc, "Tableau 4. Paires de jumeaux : lequel est supprimé ? Sans les six enseignes",
            ["Premier publié", "Second publié", "Paires"],
            [["Supprimé", "Supprimé", get(True, True)],
             ["Resté en ligne", "Supprimé", get(False, True)],
             ["Supprimé", "Resté en ligne", get(True, False)],
             ["Resté en ligne", "Resté en ligne", get(False, False)]],
            [5.5, 5.5, 3.0])
    P(doc, "Un avis supprimé puis republié par son auteur donnerait « supprimé, resté en ligne » : "
           f"{get(True, False)} paires seulement. Quand la paire perd un avis, le plus souvent elle perd "
           "les deux, ou seulement le second publié.", "NoteTableau")

    doc.add_paragraph("À retenir", style="TitreTableau")
    for texte in (
            f"**Un avis recopié est supprimé {virgule(cl('sans les six enseignes', 'copie', 'part_supprimee_pct'), 0)} "
            f"fois sur 100**, contre {virgule(cl('sans les six enseignes', 'sans jumeau', 'part_supprimee_pct'))} % "
            "pour un avis sans jumeau (sans les six enseignes). La part supprimée monte avec la "
            "ressemblance dès 0,97.",
            f"**Fiche par fiche, l'effet tient** : un avis recopié est supprimé "
            f"{virgule(r7('tout le panel', 'copie', 'rapport_observe_attendu'), 0)} fois plus que les "
            f"autres avis de sa fiche, une quasi-copie {virgule(r7('tout le panel', 'quasi-copie', 'rapport_observe_attendu'), 1)} "
            "fois plus. Sans les enseignes, les copies sont surtout sur des fiches qui perdent "
            f"peu d'avis ({virgule(r7('sans les six enseignes', 'copie', 'attendus_au_taux_de_la_fiche'), 1)} "
            f"suppressions attendues, {int(r7('sans les six enseignes', 'copie', 'supprimes'))} observées).",
            f"**Entre 0,94 et 0,97, aucun effet** : {rapport_fiche('tout le panel', 'même sujet')} au taux de "
            "la fiche. La légère hausse de la figure 1 dans cette zone vient des fiches, pas du "
            "texte : le seuil utile est bien 0,97.",
            "**Ce n'est pas la suppression qui crée la copie** : les republications après "
            "suppression sont rares.",
            f"**Le volume est faible** : {espace(cl('tout le panel', 'copie', 'avis') + cl('tout le panel', 'quasi-copie', 'avis'))} "
            f"avis sur 26 168, pour {espace(cl('tout le panel', 'copie', 'supprimes') + cl('tout le panel', 'quasi-copie', 'supprimes'))} "
            "suppressions. Le signal est fort mais n'explique qu'une petite part des suppressions."):
        P(doc, texte, "List Bullet")

    # 2 -------------------------------------------------------------------------
    h = doc.add_heading("2. Supprimés et restés sur une même fiche", level=1)
    h.paragraph_format.page_break_before = True
    for texte in (
            "On ne compare que des avis de la même fiche et de la même note : secteur, fiche et "
            "note sont identiques par construction.",
            "Cases retenues : au moins 2 avis supprimés et 1 resté en ligne. Dans chaque case, on "
            "mesure si les supprimés se ressemblent plus entre eux qu'ils ne ressemblent aux "
            "restés (contraste positif).",
            "Comparaison : 2 000 permutations des étiquettes « supprimé / resté » à l'intérieur de "
            "chaque case."):
        P(doc, texte, "List Bullet")

    lignes = []
    for r in b1.itertuples():
        net = bool(r.au_dessus_du_hasard)
        lignes.append([r.perimetre.replace("tout le panel", "Tout le panel")
                       .replace("sans les six enseignes", "Sans les six enseignes")
                       .replace("Tout le panel, sans", "Tout le panel, sans")
                       .replace(", sans copies", ", sans copies"),
                       r.note, espace(r.cases), espace(r.supprimes),
                       virgule(r.contraste_observe * 1000, 1), virgule(r.hasard_borne_haute * 1000, 1),
                       f"{virgule(r.part_tirages_au_dessus_pct, 1)} %" + (" ▲" if net else "")])
    tableau(doc, "Tableau 5. Les supprimés d'une fiche se ressemblent-ils plus entre eux ?",
            ["Périmètre", "Note", "Cases", "Supprimés", "Contraste", "Hasard",
             "Tirages au-dessus"], lignes, [4.9, 2.2, 1.3, 2.0, 1.8, 1.7, 2.7])
    P(doc, "Contraste et hasard (seuil des 97,5 % de tirages) en millièmes de similarité. Tirages au-dessus : part des 2 000 "
           "permutations qui atteignent le contraste observé ; ▲ sous 2,5 %. « Sans copies » : "
           "après retrait des avis classés copie ou quasi-copie en partie 1.", "NoteTableau")

    doc.add_paragraph("À retenir", style="TitreTableau")
    for texte in (
            "**Oui, sur une même fiche les supprimés se ressemblent plus entre eux**, toutes notes "
            "et en 5 étoiles, avec ou sans les enseignes.",
            "**L'écart tient surtout aux copies** : sans elles, il disparaît sur tout le panel "
            f"({virgule(b('tout le panel, sans copies ni quasi-copies', 'toutes notes', 'part_tirages_au_dessus_pct'))} % "
            "des tirages au-dessus) et ne reste qu'un résidu faible sans les enseignes "
            f"({virgule(b('sans les six enseignes, sans copies ni quasi-copies', 'toutes notes', 'part_tirages_au_dessus_pct'))} % "
            f"des tirages, contraste divisé par {virgule(rapport)}).",
            f"**En 1 étoile, rien ne ressort** : {int(fiches_1.min())} à {int(fiches_1.max())} "
            "fiches seulement ont assez de suppressions."):
        P(doc, texte, "List Bullet")

    # 3 -------------------------------------------------------------------------
    doc.add_heading("Ce que les embeddings apportent", level=1)
    for texte in (
            "Le seul signal net est la **copie** : un avis dont le texte existe déjà, presque mot "
            "pour mot, est très souvent supprimé, à fiche égale.",
            "Hors copies, le contenu du texte ne distingue presque pas un avis supprimé d'un avis "
            "resté en ligne, ni par thème (section 5 d'analyses-complémentaires), ni sur une même "
            "fiche.",
            "La copie est une variable simple à ajouter au modèle de régression : « l'avis a un "
            "jumeau à 0,97 ou plus »."):
        P(doc, texte, "List Bullet")

    doc.add_heading("Réserves", level=1)
    for texte in (
            "Le jumeau est cherché dans le seul panel 03B (26 168 avis avec texte) : une copie d'un "
            "avis plus ancien ou d'une autre fiche hors panel n'est pas vue. Le nombre de copies est "
            "un plancher.",
            "Les seuils 0,97 et 0,99 sont propres à ce modèle de vecteurs (e5-base).",
            "Effectifs réduits : 42 copies et 82 quasi-copies sans les enseignes."):
        P(doc, texte, "List Bullet")
    P(doc, "Sources : etudes-ponctuelles/2026-09-28-embeddings-further/ (calcul.py, note.py, "
           "sorties/*.csv). Vecteurs : data/embeddings/03B_e5base.parquet. Aucun texte d'avis dans "
           "les fichiers versionnés.", "NoteTableau")

    doc.core_properties.title = "Embeddings : deux pistes complémentaires"
    doc.core_properties.author = "Cartelis"
    doc.save(LIVRABLE)
    print(f"écrit : {LIVRABLE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
