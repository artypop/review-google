#!/usr/bin/env python3
"""
==============================================================================
Script : 03C_ajout_prenom.py
Entrées : data/bigquery/03C_7_17_aout.parquet
          data/local/axel_file/reviews_name_enriched.parquet (annotation d'Axel)
Sortie  : data/local/03C_7_17_aout_prenom.parquet (non versionné)

Ajoute au corpus 03C la présence d'un prénom dans le texte de l'avis, reprise
de l'annotation d'Axel. Écrit le 2026-10-05 à la demande de Matthieu. Le
corpus d'origine n'est pas modifié.

    PYTHONPATH=.venv/Lib/site-packages <python uv> logistic-regression-study/python/03C_ajout_prenom.py

------------------------------------------------------------------------------
L'ANNOTATION D'AXEL
------------------------------------------------------------------------------
2 675 861 avis 4 et 5 étoiles avec texte, de toute la base. Prénom détecté par
GLiNER (`has_name`) : 0,66 % de fausses détections, 93 % des prénoms trouvés,
d'après son document. Le parquet contient 333 `review_id` en double : on garde
la ligne dont le texte est celui du 03C, sinon on prend le OU des lignes.

------------------------------------------------------------------------------
LES COLONNES AJOUTÉES
------------------------------------------------------------------------------
  prenom          TRUE / FALSE, NULL quand on ne sait pas.
  prenom_source   d'où vient la valeur :
    axel                    avis retrouvé chez Axel, texte identique ;
    axel_texte_modifie      avis retrouvé, mais le texte a changé entre les
                            deux extractions : l'annotation porte sur l'autre
                            version du texte ;
    sans_texte              4-5 étoiles sans texte : FALSE, pas de prénom
                            possible ;
    introuvable             4-5 étoiles avec texte absent chez Axel : NULL.
                            Au 2026-10-05, ce sont tous des versions modifiées
                            (`is_update`) ;
    hors_annotation         1 à 3 étoiles, qu'Axel n'a pas annotés : NULL.

La suppression n'est pas recalculée : dans 03C, les doublons sont déjà retirés,
un avis disparu (`deleted_detected_at` renseigné) est supprimé. Règle de
Matthieu du 2026-10-05.
==============================================================================
"""
from __future__ import annotations

import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "outils"))
from local import connexion  # noqa: E402

AXEL = RACINE / "data" / "local" / "axel_file" / "reviews_name_enriched.parquet"
SORTIE = RACINE / "data" / "local" / "03C_7_17_aout_prenom.parquet"

SQL = """
WITH
axel AS (
  SELECT c.review_id,
         bool_or(a.has_name) FILTER (a.text = c.text) AS prenom_meme_texte,
         bool_or(a.has_name)                          AS prenom_tout_texte
  FROM "03C_7_17_aout" c
  JOIN read_parquet('{axel}') a USING (review_id)
  GROUP BY c.review_id
)
SELECT c.*,
  CASE WHEN c.star <= 3                                  THEN NULL
       WHEN length(trim(coalesce(c.text, ''))) = 0       THEN FALSE
       ELSE coalesce(x.prenom_meme_texte, x.prenom_tout_texte) END AS prenom,
  CASE WHEN c.star <= 3                                  THEN 'hors_annotation'
       WHEN length(trim(coalesce(c.text, ''))) = 0       THEN 'sans_texte'
       WHEN x.prenom_meme_texte IS NOT NULL              THEN 'axel'
       WHEN x.prenom_tout_texte IS NOT NULL              THEN 'axel_texte_modifie'
       ELSE 'introuvable' END                                      AS prenom_source
FROM "03C_7_17_aout" c
LEFT JOIN axel x USING (review_id)
"""


def main() -> None:
    con = connexion("4GB")
    con.execute(f"COPY ({SQL.format(axel=AXEL.as_posix())}) "
                f"TO '{SORTIE.as_posix()}' (FORMAT parquet, COMPRESSION zstd)")

    n, distincts, n_corpus = con.execute(f"""
        SELECT count(*), count(DISTINCT review_id),
               (SELECT count(*) FROM "03C_7_17_aout")
        FROM '{SORTIE.as_posix()}'""").fetchone()
    print(f"[03C prénom] écrit : {SORTIE}\n  {n:,} avis".replace(",", " "))
    if not n == distincts == n_corpus:
        raise SystemExit("La jointure a dupliqué ou perdu des avis.")

    print("\n  source               avis  prénom  sans  inconnu  supprimés")
    for ligne in con.execute(f"""
        SELECT prenom_source, count(*), count(*) FILTER (prenom),
               count(*) FILTER (NOT prenom), count(*) FILTER (prenom IS NULL),
               count(*) FILTER (deleted_detected_at IS NOT NULL)
        FROM '{SORTIE.as_posix()}' GROUP BY 1 ORDER BY 2 DESC""").fetchall():
        print("  {:<18s} {:>7} {:>7} {:>5} {:>8} {:>10}".format(*ligne))


if __name__ == "__main__":
    main()
