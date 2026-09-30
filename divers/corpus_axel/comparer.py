"""Met côte à côte les sorties de la consolidation (03B) et celles du corpus d'Axel.

    uv run python divers/corpus_axel/comparer.py

Lit les CSV de même nom dans `consolidation/sorties/` et dans
`divers/corpus_axel/sorties/`, et écrit `sorties/comparaison.csv` : une ligne par
chiffre.

  fichier        le CSV d'où vient le chiffre
  ligne          la ligne du CSV (passage, modalité, colonne du modèle…)
  mesure         la colonne du CSV (avis, suppressions, pour_10000, risque_relatif…)
  valeur_03B     le chiffre de la consolidation
  valeur_axel    le même chiffre sur le corpus d'Axel
  ecart          valeur_axel − valeur_03B, pour les nombres
  change         oui si les deux valeurs diffèrent

Aucun calcul sur les avis ici : seulement la lecture de CSV déjà produits.
"""
from pathlib import Path

import pandas as pd

ICI = Path(__file__).resolve().parent
SORTIES_03B = ICI.parents[1] / "consolidation" / "sorties"
SORTIES_AXEL = ICI / "sorties"

# Pour chaque CSV, les colonnes qui désignent la ligne. Les autres sont des mesures.
CLES = {
    **{f"2_3_{c}": ["modalite", "perimetre"] for c in [
        "note", "texte", "longueur_texte", "photo_jointe", "local_guide", "photos_auteur",
        "avis_auteur", "secteur", "taille", "habitude_reponse_fiche",
        "avis_sur_la_fiche_le_meme_jour"]},
    "3_population": ["ordre", "etape"],
    "3a_jour_par_jour": ["perimetre", "taille", "habitude", "reponse_au_2e_jour",
                         "jour_apres_publication"],
    "3b_effectifs": ["taille", "perimetre", "habitude", "delai"],
    "3b_effets": ["passage", "colonne"],
    "4_0_niveaux_local_guide": ["perimetre", "niveau"],
    "4a_effectifs": ["passage", "caracteristique", "modalite"],
    "4a_effets": ["passage", "colonne"],
    "4b_effectifs": ["passage", "caracteristique", "modalite"],
    "4b_effets": ["passage", "colonne"],
    "5_effectifs": ["passage", "habitude", "reponse"],
    "5_effets": ["passage", "colonne"],
}


def lire(dossier: Path, nom: str) -> pd.DataFrame:
    return pd.read_csv(dossier / f"{nom}.csv", sep=";", decimal=",", dtype={c: str for c in CLES[nom]})


morceaux = []
for nom, cles in CLES.items():
    if not (SORTIES_AXEL / f"{nom}.csv").exists():
        print(f"  {nom}.csv : pas encore produit sur le corpus d'Axel, ignoré")
        continue
    a, b = lire(SORTIES_03B, nom), lire(SORTIES_AXEL, nom)
    mesures = [c for c in a.columns if c not in cles]
    # Une ligne du CSV absente d'un côté reste dans la comparaison, avec une valeur vide.
    long_a = a.melt(id_vars=cles, value_vars=mesures, var_name="mesure", value_name="valeur_03B")
    long_b = b.melt(id_vars=cles, value_vars=mesures, var_name="mesure", value_name="valeur_axel")
    m = long_a.merge(long_b, on=cles + ["mesure"], how="outer")
    m.insert(0, "ligne", m[cles].fillna("").agg(" | ".join, axis=1))
    m.insert(0, "fichier", nom)
    morceaux.append(m[["fichier", "ligne", "mesure", "valeur_03B", "valeur_axel"]])
    print(f"  {nom}.csv : {len(a)} lignes sur 03B, {len(b)} sur le corpus d'Axel")

c = pd.concat(morceaux, ignore_index=True)
x, y = pd.to_numeric(c["valeur_03B"], errors="coerce"), pd.to_numeric(c["valeur_axel"], errors="coerce")
c["ecart"] = (y - x).round(2)
vides = c["valeur_03B"].isna() & c["valeur_axel"].isna()
egales = (c["valeur_03B"].astype(str) == c["valeur_axel"].astype(str)) | (x == y) | vides
c["change"] = (~egales).map({True: "oui", False: "non"})
c.to_csv(SORTIES_AXEL / "comparaison.csv", sep=";", decimal=",", index=False)
print(f"  sorties/comparaison.csv : {len(c)} chiffres comparés, {int((c['change'] == 'oui').sum())} changent")
print(c.groupby("fichier")["change"].apply(lambda s: f"{int((s == 'oui').sum())} sur {len(s)}").to_string())
