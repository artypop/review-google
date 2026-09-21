#!/usr/bin/env python3
"""La copie locale dit-elle la même chose que BigQuery ?

    python outils/controle_copie_locale.py

Deux contrôles, dans cet ordre.

1. **Les six passages du modèle**, recomptés sur `reviews_panel_features`.
   Ils doivent redonner les effectifs publiés dans `docs/05-resume-regressions.md`.

2. **La reconstruction du panel depuis `reviews`**, qui rejoue les deux règles
   de `sql/01_selection_panel.sql` — un seul enregistrement par `review_id`,
   publication entre les deux bornes — puis la cible de `sql/02`, où
   `supprime` vaut `deleted_detected_at_day IS NOT NULL`.

   Le contrôle porte sur les identifiants, pas seulement sur les totaux : deux
   corpus de même taille peuvent contenir des avis différents.

À lancer après chaque nouveau tirage. Un écart veut dire que la copie et
BigQuery ont divergé, et aucun chiffre local ne vaut tant qu'il n'est pas
expliqué.
"""

from __future__ import annotations

from local import PUBLICATION_DEBUT, PUBLICATION_FIN, PREMIERE_VAGUE, connexion

ATTENDU = {
    "tous": (225_757, 2_595),
    "tous sans enseignes": (210_670, 1_576),
    "US": (127_813, 1_851),
    "US sans enseignes": (113_173, 1_159),
    "Europe": (97_944, 744),
    "Europe sans enseignes": (97_497, 417),
}

SANS_ENSEIGNES = "NOT chaine_antiparasitaire_us AND NOT salle_de_sport_attaquee"

PASSAGES = {
    "tous": "TRUE",
    "tous sans enseignes": SANS_ENSEIGNES,
    "US": "region = 'US'",
    "US sans enseignes": f"region = 'US' AND {SANS_ENSEIGNES}",
    "Europe": "region = 'Europe'",
    "Europe sans enseignes": f"region = 'Europe' AND {SANS_ENSEIGNES}",
}


def controler_passages(con) -> bool:
    print("=== Les six passages du modèle ===\n")
    print(f"{'passage':24s} {'avis':>9s} {'suppressions':>13s}  verdict")
    tout_va_bien = True
    for nom, filtre in PASSAGES.items():
        avis, supprimes = con.execute(
            f"SELECT COUNT(*), SUM(supprime::INT) FROM reviews_panel_features WHERE {filtre}"
        ).fetchone()
        attendu = ATTENDU[nom]
        juste = (avis, supprimes) == attendu
        tout_va_bien &= juste
        verdict = "conforme" if juste else f"ATTENDU {attendu[0]:,} / {attendu[1]:,}"
        print(f"{nom:24s} {avis:>9,} {supprimes:>13,}  {verdict}")
    return tout_va_bien


def controler_reconstruction(con) -> bool:
    con.execute(f"""
    CREATE OR REPLACE VIEW panel_local AS
    WITH un_seul_enregistrement AS (
      SELECT review_id FROM reviews GROUP BY review_id HAVING COUNT(*) = 1
    )
    SELECT r.review_id,
           r.deleted_detected_at IS NOT NULL AS supprime,
           CAST(r.created_at AS DATE) >= DATE '{PREMIERE_VAGUE}' AS ne_pendant_la_surveillance
    FROM reviews r
    JOIN un_seul_enregistrement USING (review_id)
    WHERE CAST(r.created_at AS DATE)
          BETWEEN DATE '{PUBLICATION_DEBUT}' AND DATE '{PUBLICATION_FIN}'
    """)

    print("\n=== Le panel reconstruit depuis `reviews` ===\n")
    print(con.execute("""
    SELECT 'local (depuis reviews)' AS source, COUNT(*) AS avis,
           SUM(supprime::INT) AS suppressions FROM panel_local
    UNION ALL
    SELECT 'BigQuery (sql/01 + sql/02)', COUNT(*), SUM(supprime::INT)
    FROM reviews_panel_features
    """).df().to_string(index=False))

    ecarts = con.execute("""
    SELECT
      (SELECT COUNT(*) FROM (SELECT review_id FROM panel_local
                             EXCEPT SELECT review_id FROM reviews_panel_features)) AS local_seulement,
      (SELECT COUNT(*) FROM (SELECT review_id FROM reviews_panel_features
                             EXCEPT SELECT review_id FROM panel_local)) AS bigquery_seulement
    """).fetchone()

    print(f"\nAvis présents d'un seul côté : {ecarts[0]} en local, {ecarts[1]} dans BigQuery.")
    if ecarts == (0, 0):
        print("Les 225 757 identifiants sont les mêmes des deux côtés.")
        return True
    print("Écart à expliquer avant d'utiliser un chiffre local. "
          "Première piste : le fuseau horaire, voir local.py.")
    return False


def main() -> None:
    con = connexion()
    tables = {r[0] for r in con.execute("SHOW TABLES").fetchall()}

    if "reviews_panel_features" not in tables:
        raise SystemExit("`reviews_panel_features` manque. "
                         "Lancer : python outils/tirer_tables.py reviews_panel_features")

    passages = controler_passages(con)

    if "reviews" in tables:
        reconstruction = controler_reconstruction(con)
    else:
        print("\n`reviews` n'est pas tirée, la reconstruction est sautée.")
        reconstruction = True

    print("\n" + ("Copie locale fidèle." if passages and reconstruction
                  else "Copie locale en écart. Ne rien publier tant que ce n'est pas expliqué."))


if __name__ == "__main__":
    main()
