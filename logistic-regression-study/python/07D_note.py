#!/usr/bin/env python3
"""Ajoute la section « signaux de texte dans la régression » à
`livrables/regroupement-textes-us.docx`.

    PYTHONPATH=.venv/Lib/site-packages <python uv> logistic-regression-study/python/07D_note.py

Ordre de génération du document :
  1. etudes-ponctuelles/2026-09-29-hdbscan-residus-us/note.py   (réécrit tout)
  2. etudes-ponctuelles/2026-09-29-home-services-us/note.py     (section 4)
  3. ce script                                                   (section 5)
La section est insérée avant « Suite proposée », qui est renumérotée et dont
les puces sont remplacées. Relancé, le script remplace sa section.

Lit `output-study/2026-09-29-sorties-07D/` et, pour les copies, les sorties de
etudes-ponctuelles/2026-09-28-embeddings-further/. Aucun chiffre calculé ici.
Sans pandas (bloqué sur le poste depuis le 2026-09-29).
"""
from __future__ import annotations

# Remplacé le 2026-09-29 par etudes-ponctuelles/2026-09-29-synthese-textes/note.py,
# qui écrit livrables/regroupement-textes-us.docx en entier. Relancer ce script
# réécrirait l'ancienne structure du document.
raise SystemExit("remplacé par etudes-ponctuelles/2026-09-29-synthese-textes/note.py")


import csv
from pathlib import Path

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from docx.text.paragraph import Paragraph

RACINE = Path(__file__).resolve().parents[2]
SORTIES = RACINE / "logistic-regression-study" / "output-study" / "2026-09-29-sorties-07D"
COPIES = RACINE / "etudes-ponctuelles" / "2026-09-28-embeddings-further" / "sorties"
SORTIES_30 = RACINE / "logistic-regression-study" / "output-study" / "2026-09-29-sorties-07D-min30"
PAIRES = RACINE / "etudes-ponctuelles" / "2026-09-29-quasi-copies" / "sorties"
TYPES = ["un auteur, plusieurs fiches", "doublon", "gabarit sur une fiche",
         "gabarit sur une enseigne", "rencontre"]
NOMS_TYPES = {"un auteur, plusieurs fiches": "Même auteur, plusieurs fiches",
              "doublon": "Même auteur, même fiche",
              "gabarit sur une fiche": "Auteurs différents, même fiche",
              "gabarit sur une enseigne": "Auteurs différents, même enseigne",
              "rencontre": "Sans lien (autre enseigne)", "tous": "Total"}
LIVRABLE = RACINE / "livrables" / "regroupement-textes-us.docx"
TITRE = "5. Les signaux de texte dans la régression, panel 03B"
SUITE = "Suite proposée"
PASSAGES = [("tous", "Tous"), ("US", "US"), ("Europe", "Europe")]
SIGNAUX = [("copie_ou_quasi", "Copie ou quasi-copie"), ("texte_court", "Texte de moins de 60 car."),
           ("sans_texte", "Sans texte")]


def lire(chemin):
    with chemin.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def virgule(x, d=1):
    return f"{float(x):.{d}f}".replace(".", ",")


def espace(n):
    return f"{round(float(n)):,}".replace(",", " ")


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


def texte_titre(e) -> str:
    return "".join(t.text or "" for t in e.iter(qn("w:t"))).strip()


def preparer(doc):
    """Retire l'ancienne version de la section et rend l'élément « Suite
    proposée » devant lequel insérer."""
    corps = doc.element.body
    enfants = list(corps)
    debut = next((i for i, e in enumerate(enfants) if texte_titre(e) == TITRE), None)
    if debut is not None:
        fin = next(i for i, e in enumerate(enfants) if i > debut and texte_titre(e).endswith(SUITE))
        for e in enfants[debut:fin]:
            corps.remove(e)
    return next(p for p in doc.paragraphs if p.text.strip().endswith(SUITE))


def refaire_suite(doc, suite, puces_suite):
    """Renumérote « Suite proposée » après la dernière section et remplace ses puces."""
    numeros = [int(p.text.split(".")[0]) for p in doc.paragraphs
               if p.style.name == "Heading 1" and p.text[:1].isdigit()
               and not p.text.strip().endswith(SUITE)]
    for r in suite.runs:
        r.text = ""
    suite.runs[0].text = f"{max(numeros) + 1}. {SUITE}"
    e = suite._p.getnext()
    while (e is not None and e.tag == qn("w:p")
           and Paragraph(e, suite._parent).style.name == "List Bullet"):
        suivant = e.getnext()
        e.getparent().remove(e)
        e = suivant
    n_avant = len(doc.element.body)
    puces(doc, puces_suite)
    for p in reversed(list(doc.element.body)[n_avant - 1:-1]):
        suite._p.addnext(p)


def main() -> int:
    effets = {(r["passage"], r["variable"]): r for r in lire(SORTIES / "07D_effets_6_passages.csv")}
    eff = {(r["passage"], r["cas"]): r for r in lire(SORTIES / "07D_effectifs_signaux.csv")}
    bilan = {r["passage"]: r for r in lire(SORTIES / "07D_passages.csv")}
    ordre = {(r["perimetre"], r["premier_supprime"], r["second_supprime"]): int(r["paires"])
             for r in lire(COPIES / "A3-ordre-dans-la-paire.csv")}
    fiches = {(r["perimetre"], r["groupe"]): r for r in lire(COPIES / "A2-memes-fiches.csv")}
    effets30 = {(r["passage"], r["variable"]): r
                for r in lire(SORTIES_30 / "07D_effets_6_passages.csv")}
    eff30 = {(r["passage"], r["cas"]): r for r in lire(SORTIES_30 / "07D_effectifs_signaux.csv")}
    t80 = {r["type"]: r for r in lire(PAIRES / "A1-types.csv")}
    t30 = {r["type"]: r for r in lire(PAIRES / "min30" / "A1-types.csv")}
    if int(t80["tous"]["avis"]) != int(eff[("tous_complet", "copie_ou_quasi")]["avis"]):
        raise SystemExit("types de paires et régression ne portent pas sur les mêmes copies")
    if int(t30["tous"]["avis"]) != int(eff30[("tous_complet", "copie_ou_quasi")]["avis"]):
        raise SystemExit("seuil 30 : types de paires et régression ne se recouvrent pas")

    def rr(passage, var, d=2):
        r = effets[(passage, var)]
        net = float(r["borne_basse"]) > 1 or float(r["borne_haute"]) < 1
        return (f"×{virgule(r['risque_relatif'], d)} [{virgule(r['borne_basse'], d)} – "
                f"{virgule(r['borne_haute'], d)}]", net)

    def rr30(passage, var, d=1):
        r = effets30[(passage, var)]
        net = float(r["borne_basse"]) > 1 or float(r["borne_haute"]) < 1
        return (f"×{virgule(r['risque_relatif'], d)} [{virgule(r['borne_basse'], d)} – "
                f"{virgule(r['borne_haute'], d)}]", net)

    for (passage, var), r in effets.items():
        if var == "texte_court" and (float(r["borne_basse"]) > 1 or float(r["borne_haute"]) < 1):
            raise SystemExit(f"texte court net dans {passage} : texte à réécrire")
        if var == "copie_ou_quasi" and float(r["borne_basse"]) <= 1:
            raise SystemExit(f"copie non nette dans {passage} : texte à réécrire")

    tsr, tc = "tous_sans_retraits", "tous_complet"
    cop, lon = eff[(tsr, "copie_ou_quasi")], eff[(tsr, "texte_60_et_plus")]
    cop_c = eff[(tc, "copie_ou_quasi")]
    rrs = [float(effets[(f"{p}_{j}", "copie_ou_quasi")]["risque_relatif"])
           for p, _ in PASSAGES for j in ("complet", "sans_retraits")]
    se = "sans les six enseignes"
    f_cop, f_autres = fiches[(se, "copie ou quasi-copie")], fiches[(se, "autres avis des mêmes fiches")]
    deux, second, premier = (ordre[(se, "True", "True")], ordre[(se, "False", "True")],
                             ordre[(se, "True", "False")])

    doc = Document(LIVRABLE)
    suite = preparer(doc)
    n_avant = len(doc.element.body)

    doc.add_heading(TITRE, level=1)
    doc.add_heading("Ce qu'on a fait", level=2)
    puces(doc, [
        "**Base** : la régression réduite du 28/09 (note, pic d'avis de la fiche, photo, photos "
        "de l'auteur, Local Guide 4 et plus, réponse du propriétaire, secteur, contrôles "
        f"d'exposition), sur le panel 03B : {espace(bilan[tc]['avis'])} avis, "
        f"{espace(bilan[tc]['suppressions'])} suppressions.",
        "**Signal 1, copie** : texte d'au moins 80 caractères dont l'avis le plus proche du panel "
        "est quasi identique (similarité de 0,97 ou plus entre embeddings, seuil fixé le 28/09 à "
        "la lecture des paires).",
        "**Signal 2, texte court** : moins de 60 caractères, comparé aux textes de 60 caractères "
        "ou plus ; les avis sans texte sont une troisième catégorie.",
        "**Six passages** : US, Europe, tous ; complet, puis sans les 2 salles de sport espagnoles "
        "et sans les fiches américaines de traitement antiparasitaire, comme le 28/09.",
        "**Vérification** : sans les signaux, le calcul retrouve à l'identique les coefficients "
        "du 28/09.",
    ])

    doc.add_heading("Résultats", level=2)
    puces(doc, [
        f"**Un avis copié ou quasi copié risque {virgule(effets[(tsr, 'copie_ou_quasi')]['risque_relatif'], 0)} "
        "fois plus d'être supprimé**, à caractéristiques égales, sans les retraits. Le risque est "
        f"multiplié par {virgule(min(rrs), 1)} à {virgule(max(rrs), 0)} selon le passage.",
        f"**En nombre d'avis** : sur 10 000 avis copiés, {espace(cop['taux_pour_10000_avis'])} sont "
        f"supprimés, contre {espace(lon['taux_pour_10000_avis'])} pour un texte de 60 caractères ou "
        "plus (sans les retraits).",
        f"**L'effet tient à l'intérieur des fiches** (étude du 28/09, sans les six enseignes) : "
        f"dans les fiches qui ont une copie, "
        f"{virgule(f_cop['part_supprimee_pct'], 0)} % des copies sont supprimées, contre "
        f"{virgule(f_autres['part_supprimee_pct'], 0)} % de leurs autres avis.",
        f"**Google supprime surtout le doublon ou les deux avis** (même source) : sur les paires "
        f"de copies, les "
        f"deux avis sont supprimés {deux} fois, seul le second {second} fois, seul le premier "
        f"{premier} fois. Un auteur qui republie son avis après une suppression explique peu de cas.",
        f"**Le poids reste faible** : {espace(cop_c['avis'])} avis copiés sur "
        f"{espace(bilan[tc]['avis'])}, qui portent {espace(cop_c['suppressions'])} des "
        f"{espace(bilan[tc]['suppressions'])} suppressions.",
        "**Le texte court n'a aucun effet** dans les six passages "
        f"({rr(tsr, 'texte_court')[0]} sans les retraits). L'éloge court des sections 1 et 4 ne "
        "se retrouve pas par la seule longueur : s'il existe, il tient au caractère générique "
        "du texte, que cette mesure ne capte pas.",
        f"**Un avis sans texte est un peu moins supprimé** sans les retraits "
        f"({rr(tsr, 'sans_texte')[0]}) ; les autres passages ne permettent pas de conclure.",
    ])

    lignes = []
    for var, nom in SIGNAUX:
        lignes.append([nom] + [rr(f"{p}_{j}", var) for p, _ in PASSAGES
                               for j in ("complet", "sans_retraits")])
    tableau(doc, "Tableau 5. Risque relatif des signaux de texte, six passages",
            ["Signal"] + [f"{n} {'complet' if j == 'complet' else 'sans retraits'}"
                          for _, n in PASSAGES for j in ("complet", "sans_retraits")],
            lignes, [3.2] + [2.4] * 6,
            "Risque relatif et fourchette à 95 %, à note, secteur, photo, auteur, réponse, pic "
            "d'avis et exposition égaux. Référence : texte de 60 caractères ou plus, sans copie. "
            "En gras : fourchette qui ne contient pas 1. Sans retraits : sans les 2 salles de "
            "sport espagnoles et les fiches antiparasitaires américaines.")

    tableau(doc, "Tableau 6. Avis et suppressions par cas, tous les avis",
            ["Cas", "Avis", "Supprimés", "Pour 10 000 avis", "Avis (sans retraits)",
             "Supprimés (sans retraits)", "Pour 10 000 (sans retraits)"],
            [[nom, espace(eff[(tc, c)]["avis"]), espace(eff[(tc, c)]["suppressions"]),
              espace(eff[(tc, c)]["taux_pour_10000_avis"]), espace(eff[(tsr, c)]["avis"]),
              espace(eff[(tsr, c)]["suppressions"]), espace(eff[(tsr, c)]["taux_pour_10000_avis"])]
             for c, nom in (("copie_ou_quasi", "Copie ou quasi-copie"),
                            ("texte_court", "Texte de moins de 60 car."),
                            ("texte_60_et_plus", "Texte de 60 car. ou plus"),
                            ("sans_texte", "Sans texte"))],
            [4.0, 1.6, 1.8, 2.0, 2.3, 2.5, 2.5],
            "Comptes bruts, sans modèle. Une copie est aussi un texte de 60 caractères ou plus : "
            "les lignes ne s'additionnent pas.")

    # --- Qui sont les copies -------------------------------------------------
    def entier(t, ty, c):
        return int(float(t[ty][c]))

    lie = [ty for ty in TYPES[:3]]
    n_lie = sum(entier(t80, ty, "avis") for ty in lie)
    s_lie = sum(entier(t80, ty, "supprimes") for ty in lie)
    n_sans = sum(entier(t80, ty, "avis") for ty in TYPES[3:])
    s_sans = sum(entier(t80, ty, "supprimes") for ty in TYPES[3:])
    jour_lie = sum(entier(t80, ty, "avis") * float(t80[ty]["ecart_moins_d_un_jour_pct"])
                   for ty in lie) / n_lie
    un = t80["un auteur, plusieurs fiches"]
    gab = t80["gabarit sur une fiche"]
    doc.add_heading("Qui sont les copies", level=2)
    puces(doc, [
        "**Méthode** : pour chaque copie, son avis le plus proche est rattaché à l'un de cinq "
        "types, selon qu'il a le même auteur (même lien de profil) et la même fiche ou la même "
        "enseigne.",
        f"**Les copies supprimées sont liées à une fiche ou à un auteur** : {n_lie} avis de ce "
        f"type, {s_lie} supprimés ({virgule(100 * s_lie / n_lie, 0)} %), dont "
        f"{virgule(jour_lie, 0)} % déposés à moins d'un jour de leur jumeau. Auteurs et fiches "
        f"différents : {n_sans} avis, {s_sans} supprimés.",
        f"**Même auteur, plusieurs fiches** : une personne poste le même avis le même jour sur "
        f"plusieurs succursales, moins souvent en 5 étoiles ({virgule(un['note_5_pct'], 0)} %) ; "
        f"le second avis posté est supprimé à "
        f"{virgule(un['supprime_si_second_depose_pct'], 0)} %, le premier à "
        f"{virgule(un['supprime_si_premier_depose_pct'], 0)} %.",
        f"**Auteurs différents, même fiche** : des 5 étoiles ({virgule(gab['note_5_pct'], 0)} %) "
        "déposés à quelques minutes ou heures d'intervalle, paraphrases autour d'un même employé "
        f"ou textes strictement identiques ({virgule(gab['texte_identique_pct'], 0)} %) venus de "
        "comptes différents. Cela ressemble à des avis sollicités ou préparés, sans que les "
        "données le prouvent.",
    ])
    tableau(doc, "Tableau 7. Les copies selon le lien avec leur jumeau (seuil 80 caractères)",
            ["Lien avec le jumeau", "Avis", "Supprimés", "Part supprimée", "Texte identique",
             "Déposés à moins d'un jour"],
            [[NOMS_TYPES[ty], entier(t80, ty, "avis"), entier(t80, ty, "supprimes"),
              (f"{virgule(t80[ty]['part_supprimee_pct'], 0)} %", ty == "tous"),
              f"{virgule(t80[ty]['texte_identique_pct'], 0)} %",
              f"{virgule(t80[ty]['ecart_moins_d_un_jour_pct'], 0)} %"]
             for ty in TYPES + ["tous"]],
            [5.4, 1.4, 1.8, 2.2, 2.4, 3.0],
            "Tout le panel 03B. Pour comparaison, 3,8 % des avis du panel sont supprimés. Un même "
            "auteur est repéré par le lien de son profil : une personne avec deux comptes compte "
            "pour deux auteurs. Une paire mutuelle compte pour ses deux avis.")

    # --- Seuil de 30 caractères ---------------------------------------------
    ajout = {ty: (entier(t30, ty, "avis") - entier(t80, ty, "avis"),
                  entier(t30, ty, "supprimes") - entier(t80, ty, "supprimes")) for ty in TYPES}
    c80, c30 = eff[(tc, "copie_ou_quasi")], eff30[(tc, "copie_ou_quasi")]
    if ajout["un auteur, plusieurs fiches"][0] or ajout["doublon"][0]:
        raise SystemExit("seuil 30 : ajouts côté même auteur, texte à réécrire")
    doc.add_heading("Seuil de 30 caractères au lieu de 80", level=2)
    puces(doc, [
        f"**Le nombre de copies fait plus que doubler** ({espace(c80['avis'])} à "
        f"{espace(c30['avis'])} avis), **les suppressions presque pas** "
        f"({espace(c80['suppressions'])} à {espace(c30['suppressions'])}).",
        f"**Les ajouts sont surtout des ressemblances sans lien** : "
        f"{ajout['rencontre'][0]} avis, {ajout['rencontre'][1]} supprimés. Ce sont des formules "
        "courtes et courantes écrites par des personnes différentes, sur des fiches sans lien.",
        f"**Côté même fiche, {ajout['gabarit sur une fiche'][0]} avis ajoutés pour "
        f"{ajout['gabarit sur une fiche'][1]} suppressions** ; aucun ajout côté même auteur.",
        f"**Le risque relatif est divisé par deux environ** "
        f"({rr(tsr, 'copie_ou_quasi', 1)[0]} à 80 caractères, "
        f"{rr30(tsr, 'copie_ou_quasi')[0]} à 30, sans les retraits). Sous 80 caractères, une "
        "similarité de 0,97 signale surtout deux textes courts qui se ressemblent par hasard.",
    ])
    tableau(doc, "Tableau 8. Risque relatif de la copie selon le seuil de longueur",
            ["Passage", "80 caractères", "30 caractères"],
            [[f"{n} {'complet' if j == 'complet' else 'sans retraits'}",
              rr(f"{p}_{j}", "copie_ou_quasi", 1), rr30(f"{p}_{j}", "copie_ou_quasi")]
             for p, n in PASSAGES for j in ("complet", "sans_retraits")],
            [5.0, 4.5, 4.5],
            "Même modèle qu'au tableau 5 ; seule change la longueur minimale d'un texte pour "
            "compter comme copie. En gras : fourchette qui ne contient pas 1.")

    doc.add_heading("Limites", level=2)
    puces(doc, [
        f"{espace(cop_c['suppressions'])} suppressions de copies : l'effet est fort et sa "
        "fourchette large.",
        "Le seuil de 0,97 vient d'une lecture de paires ; un autre seuil déplacerait un peu les "
        "effectifs.",
        "Le texte court est une mesure grossière de l'éloge générique.",
        "La réponse du propriétaire reste à lire comme une association, comme le 28/09.",
    ])

    nouveaux = list(doc.element.body)[n_avant - 1:-1]
    for e in nouveaux:
        suite._p.addprevious(e)
    refaire_suite(doc, suite, [
        "Mesurer le caractère générique de l'éloge court, que la longueur ne capte pas : prénom "
        "d'employé cité (modèle GLiNER), présence d'un détail concret.",
        "Tester ces deux variables dans la même régression que la section 5.",
    ])
    doc.save(LIVRABLE)
    print(f"écrit : {LIVRABLE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
