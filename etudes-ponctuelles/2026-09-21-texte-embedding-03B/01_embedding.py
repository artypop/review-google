"""
Etape 1 : encodage des textes du panel 03B.

Modele : intfloat/multilingual-e5-base, 768 dimensions, multilingue.
Choisi parce que 37 % des textes du panel ne sont pas en anglais et que les
cases de comparaison descendent a quelques dizaines d'avis supprimes, ou
l'ecart de qualite entre modeles se paie.

Population encodee : les 26 168 avis du panel qui portent un texte non vide.
Les avis sans texte sont hors champ, cf. l'etape 0.

Parametrage, et pourquoi :
  prefixe "query: "        demande par e5 des deux cotes d'une comparaison
  max_seq_length = 512     la valeur du modele. Couper a 256 tronquerait
                           environ 3 textes sur 100, et plus souvent du cote
                           des supprimes, qui sont plus longs
  vecteurs normalises      la distance cosinus devient un simple produit
  lots de 32               tient dans la memoire disponible
  8 fils                   sur 14 coeurs, laisse la machine utilisable

Les textes sont tries par longueur avant encodage, puis remis dans l'ordre
d'origine. Un lot ne contient alors que des textes de taille voisine, ce qui
evite de payer les textes courts au prix des longs.

Sortie : data/embeddings/03B_e5base.parquet
  review_id, vecteur en float16, plus les colonnes de lecture (note, langue,
  supprime, longueur, drapeaux d'enseigne). Aucun texte, aucun nom d'auteur,
  aucun lien d'avis. `data/` est dans .gitignore.

Reprise : si le fichier de sortie existe deja, le script s'arrete sans rien
refaire. Passer --refaire pour le regenerer.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[2]
PANEL = RACINE / "data" / "bigquery" / "03B_reviews_panel_filtered_08_04_to_08_26.parquet"
BUSINESSES = RACINE / "data" / "bigquery" / "businesses.parquet"
SORTIE = RACINE / "data" / "embeddings" / "03B_e5base.parquet"

MODELE = "intfloat/multilingual-e5-base"
PREFIXE = "query: "
LONGUEUR_MAX = 512
TAILLE_LOT = 32
N_FILS = 8
TAILLE_TRANCHE = 512  # nombre de textes entre deux lignes d'avancement

CID_SALLES_ATTAQUEES = ("3163466139043001754", "10346942689164695031")

# Racines de nom des quatre chaines antiparasitaires americaines.
# L'egalite exacte de nom utilisee par sql/03B_adding_features.bqsql attrape
# 85 fiches et rate 10 succursales nommees « EcoShield Pest Solutions Houston »,
# « Bulwark Exterminating Corporate » et ainsi de suite, qui pesent 342 avis et
# 9 suppressions. Le prefixe les attrape. Le drapeau du projet n'est pas
# touche : l'elargissement vaut pour cette etude, et l'ecart est consigne dans
# la lecture.
RACINES_CHAINES_US = (
    "ecoshield pest solutions",
    "insight pest",
    "pointe pest control",
    "bulwark exterminating",
)


def journal(message: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {message}", flush=True)


def charger_textes() -> pd.DataFrame:
    """Les avis du panel qui portent un texte, avec leurs colonnes de lecture."""
    clauses = " OR ".join(f"lower(b.name) LIKE '{r}%'" for r in RACINES_CHAINES_US)
    con = duckdb.connect(config={"memory_limit": "2GB", "threads": 4})
    df = con.execute(f"""
    SELECT
      p.review_id,
      p.cid,
      p.star                                            AS note,
      COALESCE(p."language", 'inconnue')                AS langue,
      p.deleted_detected_at IS NOT NULL                 AS supprime,
      TRIM(p.text)                                      AS texte,
      LENGTH(TRIM(p.text))                              AS n_caracteres,
      (p.cid IN {CID_SALLES_ATTAQUEES})                 AS salle_attaquee,
      ({clauses})                                       AS chaine_us
    FROM read_parquet(?) p
    LEFT JOIN read_parquet(?) b USING (cid)
    WHERE p.text IS NOT NULL AND LENGTH(TRIM(p.text)) > 0
    ORDER BY p.review_id
    """, [PANEL.as_posix(), BUSINESSES.as_posix()]).df()
    con.close()
    df["enseigne_signalee"] = df["salle_attaquee"] | df["chaine_us"]
    return df


def encoder(textes: list[str]) -> np.ndarray:
    import torch
    from sentence_transformers import SentenceTransformer

    torch.set_num_threads(N_FILS)
    journal(f"chargement du modele {MODELE} (telechargement au premier appel)")
    modele = SentenceTransformer(MODELE, device="cpu")
    modele.max_seq_length = LONGUEUR_MAX
    journal(f"modele pret, {modele.get_sentence_embedding_dimension()} dimensions, "
            f"longueur maximale {modele.max_seq_length}")

    n = len(textes)
    # Tri par longueur : des lots homogenes, donc pas de remplissage inutile.
    ordre = np.argsort([len(t) for t in textes], kind="stable")
    tries = [PREFIXE + textes[i] for i in ordre]

    morceaux = []
    depart = time.time()
    journal(f"encodage de {n} textes, {TAILLE_TRANCHE} par ligne d'avancement")
    for debut in range(0, n, TAILLE_TRANCHE):
        tranche = tries[debut:debut + TAILLE_TRANCHE]
        morceaux.append(modele.encode(
            tranche,
            batch_size=TAILLE_LOT,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        ))
        fait = min(debut + TAILLE_TRANCHE, n)
        ecoule = time.time() - depart
        reste = ecoule / fait * (n - fait)
        journal(f"  {fait:>6}/{n}  {100 * fait / n:5.1f}%  "
                f"ecoule {ecoule / 60:5.1f} min  reste environ {reste / 60:5.1f} min")

    vecteurs_tries = np.vstack(morceaux)
    vecteurs = np.empty_like(vecteurs_tries)
    vecteurs[ordre] = vecteurs_tries  # remise dans l'ordre d'origine
    journal(f"encodage termine en {(time.time() - depart) / 60:.1f} min")
    return vecteurs


def main() -> None:
    parseur = argparse.ArgumentParser()
    parseur.add_argument("--refaire", action="store_true",
                         help="regenere le fichier meme s'il existe")
    args = parseur.parse_args()

    if SORTIE.exists() and not args.refaire:
        journal(f"{SORTIE} existe deja, rien a faire. Passer --refaire pour le regenerer.")
        return

    journal("lecture des textes")
    df = charger_textes()
    journal(f"{len(df)} textes, dont {int(df['supprime'].sum())} supprimes ; "
            f"{int((~df['enseigne_signalee']).sum())} hors enseignes signalees, "
            f"dont {int((df['supprime'] & ~df['enseigne_signalee']).sum())} supprimes")

    vecteurs = encoder(df["texte"].tolist())

    journal("ecriture du fichier de sortie")
    sortie = df.drop(columns=["texte"]).copy()
    sortie["vecteur"] = list(vecteurs.astype("float16"))
    SORTIE.parent.mkdir(parents=True, exist_ok=True)
    sortie.to_parquet(SORTIE, index=False)
    journal(f"ecrit : {SORTIE} ({SORTIE.stat().st_size / 1e6:.1f} Mo, "
            f"{len(sortie)} lignes, {vecteurs.shape[1]} dimensions)")


if __name__ == "__main__":
    sys.exit(main())
