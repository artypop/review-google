"""
Vérification du contenu textuel — la suppression a-t-elle une cause visible dans le texte ?

Question posée, et volontairement posée avant les modèles : les avis que Google supprime
sont-ils simplement des insultes, du spam ou du charabia ? Si oui, l'étude n'a pas de sujet.
Si non — si la grande majorité des avis supprimés sont des textes ordinaires — alors l'angle
faux positifs tient, et ce script en donne la mesure.

Méthode. Onze marqueurs calculés par expression régulière sur le texte brut, sans modèle et
sans apprentissage : tout est reproductible à l'identique. Le texte lui-même ne sort jamais du
script — seuls des booléens par avis sont écrits, dans `data/build/text_flags.parquet`.

Le risque est mesuré comme au niveau 1 : sur les lignes avis x vague de `fresh_hazard`, donc en
risque par passage, brut et standardisé sur l'âge, avec la colonne de contrôle sans les fiches
massivement purgées.

Limite assumée sur le lexique d'obscénités : il couvre EN, FR, DE, ES, IT, NL, PT. Le panel
compte 41 pays ; le grec et le polonais notamment ne sont pas couverts. Le chiffre est donc un
plancher, jamais un compte exhaustif.

Usage :  uv run scripts/verif_texte.py
"""

import pathlib
import sys

import duckdb
import numpy as np
import pandas as pd

RAW = pathlib.Path("data/exports/exports/reviews.parquet")
AVIS = pathlib.Path("data/build/reviews_features.parquet")
HAZ = pathlib.Path("data/build/fresh_hazard.parquet")
BIZ = pathlib.Path("data/build/business_features.parquet")
FLAGS = pathlib.Path("data/build/text_flags.parquet")
OUT = pathlib.Path("documentations/2026-09-06-verif-contenu-textuel.md")
CSV = pathlib.Path("data/resultats/verif_texte_marqueurs.csv")
BEGIN = "<!-- genere:veriftexte — regenere par scripts/verif_texte.py, ne pas editer a la main -->"
END = "<!-- /genere:veriftexte -->"

AGE_BAND = """CASE WHEN age_days < 3 THEN '0-2j' WHEN age_days < 7 THEN '3-6j'
   WHEN age_days < 14 THEN '7-13j' WHEN age_days < 21 THEN '14-20j'
   WHEN age_days < 30 THEN '21-29j' ELSE '30j+' END"""

# Lexique d'obscénités et d'insultes. Racines volontairement larges (le suffixe est libre),
# ancrées sur une frontière de mot pour éviter les faux positifs par inclusion.
OBSCENE = "|".join([
    # EN
    r"fuck", r"shit", r"bitch", r"asshole", r"bastard", r"cunt", r"dickhead", r"scumbag",
    r"moron", r"idiot", r"retard", r"douchebag", r"jerk", r"crook", r"scam", r"liar",
    r"thief", r"thieves", r"fraud", r"rip.?off", r"disgusting", r"pathetic",
    # FR
    r"merde", r"connard", r"connasse", r"salaud", r"salope", r"enfoir", r"encul",
    r"putain", r"pute", r"abruti", r"crétin", r"cretin", r"escroc", r"arnaque",
    r"voleur", r"menteur", r"incompétent", r"incompetent", r"honteux",
    # DE
    r"scheiss", r"scheiß", r"arschloch", r"wichser", r"hurensohn", r"idiot",
    r"betrüger", r"betruger", r"abzocke", r"lügner", r"lugner", r"unverschämt",
    # ES
    r"mierda", r"cabrón", r"cabron", r"gilipollas", r"puta", r"joder", r"estafa",
    r"estafador", r"ladrón", r"ladron", r"mentiroso", r"vergüenza", r"verguenza",
    # IT
    r"merda", r"stronzo", r"cazzo", r"coglione", r"truffa", r"ladro", r"bugiardo",
    # NL / PT
    r"klootzak", r"oplichter", r"kut", r"merda", r"vigarista", r"ladrão", r"ladrao",
])

# Un marqueur = (nom de colonne, libellé lisible, expression SQL booléenne sur `t` = le texte)
MARKERS = [
    ("m_obscene", "Insulte ou obscénité (lexique 7 langues)",
     rf"regexp_matches(lower(t), '\b({OBSCENE})')"),
    ("m_url", "Contient un lien web",
     r"regexp_matches(lower(t), '(https?://|www\.|\.com\b|\.net\b|\.org\b)')"),
    ("m_email", "Contient une adresse e-mail",
     r"regexp_matches(t, '[[:alnum:]._%+-]+@[[:alnum:].-]+\.[a-zA-Z]{2,}')"),
    ("m_phone", "Contient un numéro de téléphone",
     r"regexp_matches(t, '(\+[0-9]{1,3}[ .-]?)?([0-9][ .-]?){9,}')"),
    ("m_caps", "Écrit intégralement en majuscules (plus de 15 caractères)",
     r"length(t) > 15 AND t = upper(t) AND regexp_matches(t, '[A-ZÀ-Þ]')"),
    # RE2 (le moteur de DuckDB) n'a pas de rétro-référence : les répétitions sont énumérées.
    ("m_punct", "Ponctuation excessive (!!! ou ???)",
     r"regexp_matches(t, '(!{3,}|\?{3,})')"),
    ("m_repeat", "Caractère répété cinq fois ou plus",
     "regexp_matches(lower(t), '(" + "|".join(ch + "{5,}" for ch in "abcdefghijklmnopqrstuvwxyz") + ")')"),
    # Restreint aux avis qui ont un texte : sinon ce marqueur ne fait que compter les
    # avis « note seule », déjà comptés à part et qui ne relèvent d'aucun motif de suppression.
    ("m_tresscourt", "Texte présent mais de moins de 10 caractères",
     r"trim(t) <> '' AND length(trim(t)) < 10"),
    ("m_novoyelle", "Aucune voyelle sur au moins 12 caractères (charabia)",
     r"length(regexp_replace(t, '[^[:alpha:]]', '', 'g')) >= 12 "
     r"AND NOT regexp_matches(lower(t), '[aeiouyàáâäãåèéêëìíîïòóôöõùúûüaeiou]')"),
    ("m_nonalpha", "Moins d'un tiers de lettres (émojis, symboles, chiffres)",
     r"length(t) >= 10 AND "
     r"length(regexp_replace(t, '[^[:alpha:]]', '', 'g'))::DOUBLE / length(t) < 0.33"),
    ("m_promo", "Vocabulaire promotionnel ou de sollicitation",
     r"regexp_matches(lower(t), "
     r"'\b(call us|contact us|visit our|discount|promo code|coupon|appelez|contactez|"
     r"réduction|reduction|code promo|descuento|rabatt|whatsapp|telegram)\b')"),
]


def build_flags(c: duckdb.DuckDBPyConnection) -> None:
    """Calcule les marqueurs sur le texte brut et n'écrit que des booléens."""
    cols = ",\n           ".join(f"coalesce({expr}, FALSE) AS {name}"
                                 for name, _, expr in MARKERS)
    any_expr = " OR ".join(name for name, _, _ in MARKERS)
    c.sql(f"""
        COPY (
          SELECT row_id, has_text,
                 {cols},
                 ({any_expr}) AS m_any
          FROM (
            SELECT r.id AS row_id,
                   (r.text IS NOT NULL AND trim(r.text) <> '') AS has_text,
                   coalesce(r.text, '') AS t
            FROM '{RAW.as_posix()}' r
            WHERE NOT r.is_update
          )
        ) TO '{FLAGS.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)
    """)


def couverture(c: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """Part des avis portant chaque marqueur, supprimés contre survivants, périmètre frais."""
    rows = []
    for name, label, _ in MARKERS + [("m_any", "**Au moins un marqueur**", "")]:
        r = c.sql(f"""
            SELECT
              count(*) FILTER (deleted)                         AS n_supp,
              count(*) FILTER (deleted AND {name})              AS n_supp_flag,
              count(*) FILTER (NOT deleted)                     AS n_surv,
              count(*) FILTER (NOT deleted AND {name})          AS n_surv_flag
            FROM fr
        """).df().iloc[0]
        rows.append({
            "marqueur": label,
            "avis_supprimes": int(r.n_supp),
            "supprimes_avec_marqueur": int(r.n_supp_flag),
            "part_supprimes_pct": 100 * r.n_supp_flag / r.n_supp if r.n_supp else np.nan,
            "part_survivants_pct": 100 * r.n_surv_flag / r.n_surv if r.n_surv else np.nan,
        })
    d = pd.DataFrame(rows)
    d["sur_representation"] = d["part_supprimes_pct"] / d["part_survivants_pct"]
    return d


def risque(c: duckdb.DuckDBPyConnection, name: str) -> pd.DataFrame:
    """Risque par passage, brut et standardisé sur l'âge, avec et sans les fiches purgées."""
    g = c.sql(f"""
        SELECT {name} AS porte, {AGE_BAND} AS age_band,
               count(*) AS expo, sum(died::INT) AS morts,
               count(*) FILTER (NOT heavy_purge) AS expo_sp,
               sum(CASE WHEN NOT heavy_purge THEN died::INT ELSE 0 END) AS morts_sp
        FROM hz GROUP BY 1, 2
    """).df()
    poids = g.groupby("age_band")["expo"].sum()
    poids = poids / poids.sum()
    poids_sp = g.groupby("age_band")["expo_sp"].sum()
    poids_sp = poids_sp / poids_sp.sum()

    out = []
    for porte, sub in g.groupby("porte"):
        s = sub.set_index("age_band")
        taux = (s["morts"] / s["expo"]).reindex(poids.index).fillna(0)
        taux_sp = (s["morts_sp"] / s["expo_sp"].replace(0, np.nan)).reindex(poids_sp.index).fillna(0)
        out.append({
            "porte": bool(porte),
            "expositions": int(s["expo"].sum()),
            "morts": int(s["morts"].sum()),
            "risque_brut_pct": 100 * s["morts"].sum() / s["expo"].sum(),
            "risque_standardise_pct": 100 * float((taux * poids).sum()),
            "risque_std_sans_purgees_pct": 100 * float((taux_sp * poids_sp).sum()),
        })
    return pd.DataFrame(out).sort_values("porte")


def main() -> None:
    for p in (RAW, AVIS, HAZ, BIZ):
        if not p.exists():
            sys.exit(f"Fichier absent : {p}. Lancer d'abord : uv run scripts/build_tables.py")

    c = duckdb.connect(config={"memory_limit": "2GB"})
    print("Calcul des marqueurs sur le texte brut...")
    build_flags(c)
    print(f"Écrit : {FLAGS}")

    c.sql(f"""CREATE VIEW fr AS
              SELECT a.*, f.* EXCLUDE (row_id, has_text)
              FROM '{AVIS.as_posix()}' a JOIN '{FLAGS.as_posix()}' f USING (row_id)
              WHERE a.is_fresh""")
    c.sql(f"""CREATE VIEW hz AS
              SELECT h.*, f.* EXCLUDE (row_id, has_text), b.heavy_purge
              FROM '{HAZ.as_posix()}' h
              JOIN '{FLAGS.as_posix()}' f USING (row_id)
              JOIN '{BIZ.as_posix()}' b USING (cid)""")

    cov = couverture(c)
    ris = {name: risque(c, name) for name, _, _ in MARKERS}
    ris["m_any"] = risque(c, "m_any")

    # part des avis supprimés sans aucun texte, pour compléter le tableau
    sans_texte = c.sql("""
        SELECT count(*) FILTER (deleted AND NOT has_text) AS n,
               count(*) FILTER (deleted) AS tot FROM fr""").df().iloc[0]

    rows = []
    for name, label, _ in MARKERS + [("m_any", "Au moins un marqueur", "")]:
        r = ris[name]
        avec = r[r["porte"]]
        sans = r[~r["porte"]]
        rr = (avec["risque_standardise_pct"].iloc[0] / sans["risque_standardise_pct"].iloc[0]
              if len(avec) and len(sans) and sans["risque_standardise_pct"].iloc[0] else np.nan)
        rr_sp = (avec["risque_std_sans_purgees_pct"].iloc[0]
                 / sans["risque_std_sans_purgees_pct"].iloc[0]
                 if len(avec) and len(sans) and sans["risque_std_sans_purgees_pct"].iloc[0]
                 else np.nan)
        cv = cov[cov["marqueur"].str.strip("*") == label.strip("*")].iloc[0]
        rows.append({
            "marqueur": label,
            "avis_frais_porteurs": int(avec["expositions"].iloc[0]) if len(avec) else 0,
            "part_des_supprimes_pct": cv["part_supprimes_pct"],
            "part_des_survivants_pct": cv["part_survivants_pct"],
            "risque_std_avec_pct": avec["risque_standardise_pct"].iloc[0] if len(avec) else np.nan,
            "risque_std_sans_pct": sans["risque_standardise_pct"].iloc[0] if len(sans) else np.nan,
            "rapport_de_risque": rr,
            "rapport_sans_fiches_purgees": rr_sp,
        })
    out = pd.DataFrame(rows)
    CSV.parent.mkdir(parents=True, exist_ok=True)
    out.round(3).to_csv(CSV, index=False, sep=";", decimal=",", encoding="utf-8-sig")
    print(f"Écrit : {CSV}")

    write_note(out, cov, int(sans_texte.n), int(sans_texte.tot))
    print(f"Écrit : {OUT}")


def write_note(out: pd.DataFrame, cov: pd.DataFrame, n_sans_texte: int, n_supp: int) -> None:
    f = lambda n: f"{n:,}".replace(",", " ")  # noqa: E731
    any_row = out[out["marqueur"] == "Au moins un marqueur"].iloc[0]

    b = [BEGIN, ""]
    b.append("### Combien d'avis supprimés portent un marqueur visible")
    b.append("")
    b.append(f"Sur **{f(n_supp)} avis frais supprimés** :")
    b.append("")
    b.append(f"- **{any_row['part_des_supprimes_pct']:.1f} %** portent au moins un des "
             f"onze marqueurs ;")
    b.append(f"- contre **{any_row['part_des_survivants_pct']:.1f} %** des avis frais survivants ;")
    b.append(f"- {f(n_sans_texte)} ({100 * n_sans_texte / n_supp:.1f} %) n'ont aucun texte du "
             f"tout : une note seule, sur laquelle aucun marqueur ne peut se prononcer.")
    b.append("")
    b.append("### Marqueur par marqueur")
    b.append("")
    b.append("| Marqueur | Part des supprimés | Part des survivants | Risque ×, à âge comparable | Sans les 24 fiches purgées |")
    b.append("|---|---:|---:|---:|---:|")
    for _, r in out.iterrows():
        fmt = lambda v: ("—" if np.isnan(v) else  # noqa: E731
                         "aucune suppression" if v == 0 else f"×{v:.2f}")
        rr, rs = fmt(r["rapport_de_risque"]), fmt(r["rapport_sans_fiches_purgees"])
        b.append(f"| {r['marqueur']} | {r['part_des_supprimes_pct']:.2f} % | "
                 f"{r['part_des_survivants_pct']:.2f} % | {rr} | {rs} |")
    b.append("")
    b.append("« Part des supprimés » = parmi les avis frais supprimés, combien portent ce "
             "marqueur. « Risque × » = combien de fois plus un avis porteur disparaît à chaque "
             "passage, à âge comparable, qu'un avis non porteur.")
    b.append("")
    b.append(END)
    body = "\n".join(b)

    head = f"""---
date: 2026-09-06
projet: reviewflowz-analyse-google
titre: "Le texte des avis supprimés a-t-il une cause visible ?"
statut: résultats
---

# Le texte des avis supprimés a-t-il une cause visible ?

Produit par `scripts/verif_texte.py`.

## Pourquoi cette vérification passe avant les modèles

Toute l'étude repose sur une hypothèse non vérifiée jusqu'ici : que les avis supprimés par
Google ne sont pas, dans leur masse, des insultes, du spam ou du charabia. Si c'était le cas,
il n'y aurait pas de faux positifs à mesurer — juste une modération qui fonctionne.

Onze marqueurs, calculés par expression régulière, sans modèle et sans apprentissage. Chacun
est un motif de suppression légitime et évident.

## Ce que la mesure ne dit pas

- Le lexique d'obscénités couvre EN, FR, DE, ES, IT, NL, PT. Le panel compte 41 pays : le grec
  et le polonais notamment ne sont pas couverts. Le taux affiché est un **plancher**.
- Un marqueur n'est pas une preuve de faute. Un avis contenant un numéro de téléphone peut être
  parfaitement légitime.
- L'inverse est plus important : **l'absence de marqueur n'est pas une preuve d'innocence.** Un
  faux avis bien écrit n'en porte aucun. Ce test borne la part des suppressions qui ont une
  explication évidente ; il ne prouve pas que le reste est un faux positif.

## Protection des données

Le script lit `text` mais n'en écrit jamais rien : `data/build/text_flags.parquet` ne contient
que l'identifiant de ligne et des booléens.

## Résultats

"""
    if OUT.exists() and BEGIN in (prev := OUT.read_text(encoding="utf-8")) and END in prev:
        OUT.write_text(prev[: prev.index(BEGIN)] + body + prev[prev.index(END) + len(END):],
                       encoding="utf-8")
    else:
        OUT.write_text(head + body + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
