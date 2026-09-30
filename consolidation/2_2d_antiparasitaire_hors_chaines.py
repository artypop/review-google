"""2.2d. Les fiches antiparasitaires américaines hors des 4 chaînes montrent-elles le même phénomène ?

    uv run python consolidation/2_2d_antiparasitaire_hors_chaines.py

LA QUESTION
  « Sans enseignes » retire les 95 fiches de `biz_surveillance` : les 4 chaînes
  au nom exact et les 2 salles. Le 07C retirait plus large : tout
  l'antiparasitaire américain repéré par mots-clés. Les fiches qui font la
  différence perdent-elles leurs avis comme les 4 chaînes (5 étoiles, 6 ou
  7 jours après la publication, par blocs), ou comme le reste du panel ?

  Ce script ne change aucun périmètre : il décrit ces fiches, pour décider.

Produit :
  sorties/2_2d_antiparasitaire_hors_chaines.csv   une ligne par fiche : cid, enseigne, dates
  sorties/2_2d_antiparasitaire_par_enseigne.csv   les mêmes, regroupées par enseigne, puis le total
"""
import pandas as pd

from commun import ecrire_csv, requete

fiches = requete("2_2d_antiparasitaire_hors_chaines")
ecrire_csv(fiches, "2_2d_antiparasitaire_hors_chaines")

COMPTES = ["avis", "suppressions", "suppressions_5_etoiles", "suppressions_1_etoile",
           "suppressions_a_6_ou_7_jours", "suppressions_a_plus_de_30_jours",
           "panel_avis", "panel_suppressions"]


def resume(d, enseigne):
    """Une ligne de synthèse pour un groupe de fiches."""
    touchees = d[d["suppressions"] > 0]
    ligne = {"enseigne": enseigne, "fiches": len(d), "fiches_touchees": len(touchees),
             **{c: int(d[c].sum()) for c in COMPTES}}
    ligne["pour_10000"] = round(10000 * ligne["suppressions"] / ligne["avis"], 1) if ligne["avis"] else None
    ligne["panel_pour_10000"] = (round(10000 * ligne["panel_suppressions"] / ligne["panel_avis"])
                                 if ligne["panel_avis"] else None)
    ligne["premiere_suppression"] = touchees["premiere_suppression"].min() if len(touchees) else None
    ligne["derniere_suppression"] = touchees["derniere_suppression"].max() if len(touchees) else None
    ligne["suppressions_le_jour_le_plus_charge"] = int(d["suppressions_le_jour_le_plus_charge"].max())
    return ligne


# Une succursale d'une des 4 chaînes se range sous le nom de sa chaîne.
fiches["groupe"] = fiches["succursale_de"].fillna(fiches["enseigne"])
lignes = [resume(d, ("succursales de " if d["succursale_de"].notna().any() else "") + nom)
          for nom, d in fiches.groupby("groupe")]
par_enseigne = pd.DataFrame(lignes).sort_values(["suppressions", "avis"], ascending=False)
total = pd.DataFrame([resume(fiches, "TOTAL, fiches antiparasitaires hors biz_surveillance"),
                      resume(fiches[fiches["succursale_de"].notna()], "dont succursales des 4 chaînes"),
                      resume(fiches[fiches["panel_avis"] > 0], "dont fiches présentes dans le panel 03B")])
ecrire_csv(pd.concat([par_enseigne, total], ignore_index=True), "2_2d_antiparasitaire_par_enseigne")
print(total.to_string(index=False))
