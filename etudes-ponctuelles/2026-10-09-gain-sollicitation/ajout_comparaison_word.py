#!/usr/bin/env python3
"""Ajoute au Word la comparaison « à taille égale » : solliciter rapporte-t-il plus ?

    PYTHONPATH=".venv/Lib/site-packages;outils" <python uv> etudes-ponctuelles/2026-10-09-gain-sollicitation/ajout_comparaison_word.py

Demande de Matthieu du 2026-10-12 : un tableau et une conclusion pour savoir lequel est le
plus rentable, solliciter ou non. Le gain net est rapporté au stock d'avis en ligne au
départ, et comparé à taille égale : plus un commerce a d'avis, plus son gain en % est
faible, et les commerces à signes de sollicitation sont presque tous parmi les plus gros.

  tableau   gain net médian (en % du stock) par quart de stock, pour chaque groupe ;
            dernière ligne : l'écart à stock, secteur, région et taille de groupe égaux
            (régression linéaire, marges robustes), avec et sans les chaînes
            antiparasitaires
Inséré dans la partie 5, juste avant « 6. Ce qu'on peut répondre à Axel ». Le Word est
modifié sur place. Refuse de tourner deux fois. Chiffres lus dans solde_net_commerces.csv.
"""
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

RACINE = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location(
    "mise_en_forme", RACINE / "etudes-ponctuelles" / "2026-10-07-prenom-dans-les-fiches" / "document.py")
mf = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mf)
from docx import Document  # noqa: E402

WORD = RACINE / "livrables" / "restitution_finale_v2" / "analyse_exploratoire" / "fiches_touchees_nouveaux_avis.docx"
COMMERCES = RACINE / "livrables" / "restitution_finale_v2" / "gain_sollicitation" / "solde_net_commerces.csv"
TITRE = "Solliciter ou non : lequel rapporte le plus, à taille égale ?"


def pct(x: float, nd: int = 1) -> str:
    return f"{x:+.{nd}f} %".replace(".", ",").replace("-", "−")


def pts(x: float, nd: int = 1) -> str:
    return f"{x:+.{nd}f} point".replace(".", ",").replace("-", "−")


def nombre(x: float) -> str:
    return f"{x:,.0f}".replace(",", " ")


def ecart(d: pd.DataFrame) -> tuple[float, float, float, float]:
    m = smf.ols("net_pct ~ sollicitation + log_stock + C(industry) + C(region) + C(bucket)", d).fit(cov_type="HC1")
    lo, hi = m.conf_int().loc["sollicitation"]
    return m.params["sollicitation"], lo, hi, m.pvalues["sollicitation"]


def main() -> int:
    doc = Document(WORD)
    if any(p.text.startswith(TITRE) for p in doc.paragraphs):
        raise SystemExit("La comparaison est déjà dans le Word.")
    partie6 = next((p for p in doc.paragraphs if p.text.startswith("6. Ce qu'on peut répondre à Axel")), None)
    if partie6 is None:
        raise SystemExit("Titre « 6. Ce qu'on peut répondre à Axel » introuvable : le Word a été retouché.")

    c = pd.read_csv(COMMERCES, dtype={"cid": str})
    c["net_pct"] = c["solde_suivi_complet_pct"]
    c["sollicitation"] = (c["groupe"] == "prenoms_vitesse").astype(int)
    c["log_stock"] = np.log2(c["stock_depart"])
    c["quart"] = pd.qcut(c["stock_depart"], 4, labels=False)
    b, lo, hi, p = ecart(c)
    b2, lo2, hi2, p2 = ecart(c[~c["enseigne"]])
    n_sol, n_sans_ch = int(c["sollicitation"].sum()), int((c["sollicitation"] & ~c["enseigne"]).sum())

    lignes = []
    for q, x in c.groupby("quart"):
        borne = f"{nombre(x['stock_depart'].min())} à {nombre(x['stock_depart'].max())} avis"
        cell = {}
        for g, y in x.groupby("groupe"):
            cell[g] = f"{pct(y['net_pct'].median())} ({len(y)} commerces)"
        lignes.append([borne, cell.get("autres", "—"), cell.get("prenoms_vitesse", "aucun commerce")])
    lignes.append(["Écart à taille, secteur et région égaux",
                   "référence", f"{pts(b, 2)} (de {pts(lo, 2)[:-6]} à {pts(hi, 2)})"])
    lignes.append(["Même écart, sans les chaînes antiparasitaires",
                   "référence", f"{pts(b2, 2)} (de {pts(lo2, 2)[:-6]} à {pts(hi2, 2)}), non significatif"
                   if p2 >= 0.05 else f"{pts(b2, 2)} (de {pts(lo2, 2)[:-6]} à {pts(hi2, 2)})"])

    corps = doc.element.body
    avant = len(corps) - 1  # le dernier enfant est sectPr : les ajouts viennent avant lui
    mf.titre(doc, TITRE, 2)
    mf.paragraphe(doc, [("Pourquoi comparer à taille égale. ", True),
                        ("Plus un commerce a d'avis, plus son gain en pourcentage est faible ; or les "
                         "commerces à signes de sollicitation sont presque tous parmi les plus gros. "
                         "Comparer les moyennes des deux groupes (+0,9 % contre +1,3 %) les désavantage "
                         "donc à tort. Le tableau compare des commerces de même taille.", False)])
    mf.donnees(doc, "les 321 commerces de cette partie. Gain net : avis publiés du 7 au 17 août moins "
                    "avis perdus (nouveaux supprimés dans les 7 jours et anciens disparus), en % des "
                    "avis 4-5 étoiles en ligne au départ. Tailles : quarts du nombre d'avis en ligne au "
                    "départ. Dernières lignes : régression linéaire, marges d'incertitude à 95 %.")
    mf.tableau(doc, ["Avis en ligne au départ", "Autres commerces",
                     "Signes de sollicitation"], lignes, [5.6, 5.0, 6.0], taille=9)
    mf.paragraphe(doc, "", apres=2)
    mf.paragraphe(doc, [("Conclusion : solliciter est plus rentable. ", True),
                        (f"À taille, secteur et région égaux, les commerces à signes de sollicitation "
                         f"augmentent leur nombre d'avis de {pts(b, 1)[1:]} de "
                         f"plus que les autres en 11 jours. Ils obtiennent plus d'avis et, rapporté à leur "
                         "taille, n'en perdent pas plus : le « 20 avis perdus pour 100 publiés, contre 9 » "
                         "vient surtout de leur taille et des anciens avis, pas de la sollicitation. Chez "
                         "les plus gros commerces, où le groupe est le plus représenté, le gain médian passe "
                         f"de {lignes[3][1].split(' (')[0]} à {lignes[3][2].split(' (')[0]}.", False)],
                  avant=4)
    mf.paragraphe(doc, [("Réserve : ", True),
                        (f"ce résultat dépend en partie des chaînes antiparasitaires. Sans elles "
                         f"({n_sans_ch} commerces à signes de sollicitation au lieu de {n_sol}), l'écart "
                         f"va dans le même sens ({pts(b2, 1)}) mais n'est plus significatif.", False)],
                  taille=9.5)

    for el in [e for e in list(corps)[avant:] if e.tag.endswith("}p") or e.tag.endswith("}tbl")]:
        partie6._element.addprevious(el)
    doc.save(WORD)
    print(f"écart : {b:+.2f} pt [{lo:+.2f} ; {hi:+.2f}] p={p:.3f} ; sans chaînes {b2:+.2f} [{lo2:+.2f} ; {hi2:+.2f}] p={p2:.3f}")
    print(f"écrit : {WORD}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
