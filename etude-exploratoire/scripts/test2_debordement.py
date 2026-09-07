"""
Test 2 — le débordement d'une purge sur le stock organique.

Ce test mesure les erreurs de modération plus directement que tout autre du jeu de données.

Raisonnement. Un avis publié il y a plus d'un an n'a rien à voir avec une campagne d'avis lancée
le mois dernier. S'il disparaît davantage dans les fiches qui reçoivent un afflux récent que
dans des fiches comparables qui n'en reçoivent pas, alors la modération de Google déborde de sa
cible : elle emporte des avis anciens et sans rapport. Un avis supprimé dans ce cas est une erreur de modération, et ce test la chiffre.

Périmètre. Le stock ancien : avis créés plus de 365 jours avant la vague 1, et présents dès la
vague 1. Cette double condition supprime la censure à droite — chaque avis est observé sur les
mêmes 13 intervalles inter-vagues.

Comparaison. Pas d'appariement un pour un, mais une standardisation directe sur la strate
`pays x secteur x taille de groupe x palier de volume` : le taux de chaque groupe de vélocité
est recalculé comme si tous les groupes avaient la même composition de strates. C'est la méthode
déjà employée partout ailleurs dans l'étude pour l'âge, appliquée ici au marché.

Deux contrôles accompagnent le résultat principal :
  - le même calcul en retirant les 24 fiches massivement purgées ;
  - le même calcul sur les avis de plus de trois ans, encore plus éloignés de toute campagne.

Usage :  uv run scripts/test2_debordement.py
"""

import pathlib
import sys

import duckdb
import numpy as np
import pandas as pd

AVIS = pathlib.Path("data/build/reviews_features.parquet")
BIZ = pathlib.Path("data/build/business_features.parquet")
WAVES = pathlib.Path("data/exports/exports/waves.parquet")
OUT = pathlib.Path("documentations/2026-09-06-test2-debordement-organique.md")
CSV = pathlib.Path("data/resultats/test2_debordement.csv")
BEGIN = "<!-- genere:test2 — regenere par scripts/test2_debordement.py, ne pas editer a la main -->"
END = "<!-- /genere:test2 -->"

VITESSE = """CASE WHEN b.velocity_30d < 0.01 THEN 'a_moins_1pct'
                  WHEN b.velocity_30d < 0.03 THEN 'b_1_3pct'
                  WHEN b.velocity_30d < 0.10 THEN 'c_3_10pct'
                  ELSE 'd_10pct_plus' END"""

LABELS = {"a_moins_1pct": "moins de 1 %", "b_1_3pct": "1 à 3 %",
          "c_3_10pct": "3 à 10 %", "d_10pct_plus": "10 % et plus"}

# Le stock ancien, observé sur les 13 mêmes intervalles pour tout le monde.
# L'exposition d'un avis supprimé s'arrête à la vague où il disparaît.
SQL = """
WITH w AS (SELECT wave, started_at FROM 'WAVES'),
     anc AS (
       SELECT a.row_id, a.cid, a.deleted, a.deleted_detected_at, a.age_days_w1,
              -- vague de disparition : la première dont le passage suit la détection
              CASE WHEN a.deleted THEN
                (SELECT min(w.wave) FROM w WHERE w.started_at >= a.deleted_detected_at)
              END AS wave_mort
       FROM 'AVIS' a
       WHERE NOT a.born_during_panel      -- présent dès la vague 1 : pas de censure à droite
         AND a.age_days_w1 > MINAGE       -- stock ancien
     )
SELECT b.country, b.industry, b.bucket,
       CASE WHEN b.n_reviews_panel < 100 THEN 'a_moins_100'
            WHEN b.n_reviews_panel < 250 THEN 'b_100_250'
            WHEN b.n_reviews_panel < 1000 THEN 'c_250_1000'
            ELSE 'd_1000_plus' END                        AS volume,
       VITESSE                                            AS vitesse,
       b.heavy_purge,
       count(*)                                           AS avis_anciens,
       sum(anc.deleted::INT)                              AS morts,
       -- expositions en passages : 13 pour un survivant, moins pour un avis disparu en route
       sum(CASE WHEN anc.deleted THEN greatest(coalesce(anc.wave_mort, 14) - 1, 1)
                ELSE 13 END)                              AS expositions
FROM anc JOIN 'BIZ' b USING (cid)
GROUP BY ALL
"""


def charge(c: duckdb.DuckDBPyConnection, min_age: int) -> pd.DataFrame:
    q = (SQL.replace("'AVIS'", f"'{AVIS.as_posix()}'")
            .replace("'BIZ'", f"'{BIZ.as_posix()}'")
            .replace("'WAVES'", f"'{WAVES.as_posix()}'")
            .replace("VITESSE", VITESSE)
            .replace("MINAGE", str(min_age)))
    return c.sql(q).df()


def poisson_ci(k: int, alpha: float = 0.05) -> tuple[float, float]:
    """Intervalle exact de Poisson sur un comptage, par la loi du khi-deux."""
    from scipy.stats import chi2
    lo = chi2.ppf(alpha / 2, 2 * k) / 2 if k > 0 else 0.0
    hi = chi2.ppf(1 - alpha / 2, 2 * (k + 1)) / 2
    return lo, hi


def standardise(g: pd.DataFrame) -> pd.DataFrame:
    """Taux brut et taux standardisé sur la strate pays x secteur x taille x volume."""
    g = g.copy()
    g["strate"] = (g["country"] + "|" + g["industry"] + "|" + g["bucket"] + "|" + g["volume"])
    poids = g.groupby("strate")["expositions"].sum()
    poids = poids / poids.sum()

    rows = []
    for vit, sub in g.groupby("vitesse"):
        s = sub.groupby("strate")[["morts", "expositions", "avis_anciens"]].sum()
        taux = (s["morts"] / s["expositions"]).reindex(poids.index)
        # une strate absente du groupe n'apporte rien : son poids est redistribué
        dispo = poids[taux.notna()]
        std = float((taux[taux.notna()] * (dispo / dispo.sum())).sum()) if len(dispo) else np.nan
        rows.append({
            "vitesse": LABELS.get(vit, vit),
            "fiches_strates": len(s),
            "avis_anciens": int(sub["avis_anciens"].sum()),
            "morts": int(sub["morts"].sum()),
            "expositions": int(sub["expositions"].sum()),
            "couverture_strates_pct": 100 * float(dispo.sum()),
            "risque_brut_pour_10k": 1e4 * sub["morts"].sum() / sub["expositions"].sum(),
            "risque_standardise_pour_10k": 1e4 * std,
        })
    d = pd.DataFrame(rows)
    ordre = [LABELS[k] for k in ["a_moins_1pct", "b_1_3pct", "c_3_10pct", "d_10pct_plus"]]
    d["vitesse"] = pd.Categorical(d["vitesse"], ordre, ordered=True)
    d = d.sort_values("vitesse").reset_index(drop=True)
    ref = d[d["vitesse"] == LABELS["a_moins_1pct"]]["risque_standardise_pour_10k"]
    base = float(ref.iloc[0]) if len(ref) and ref.iloc[0] > 0 else np.nan
    d["rapport_vs_moins_1pct"] = d["risque_standardise_pour_10k"] / base

    # Intervalle de Poisson sur le nombre de morts, reporté proportionnellement sur le taux
    # standardisé. Approximation assumée : elle borne le bruit de comptage, rien de plus.
    lo, hi = [], []
    for _, r in d.iterrows():
        m = r["morts"]
        if m == 0 or np.isnan(r["rapport_vs_moins_1pct"]):
            lo.append(np.nan); hi.append(np.nan); continue
        pl, ph = poisson_ci(int(m))
        lo.append(r["rapport_vs_moins_1pct"] * pl / m)
        hi.append(r["rapport_vs_moins_1pct"] * ph / m)
    d["rapport_borne_basse"], d["rapport_borne_haute"] = lo, hi

    # Une cellule mince ou mal couverte par les strates n'est pas exploitable : on le dit.
    d["fiabilite"] = np.where(
        (d["morts"] < 20) | (d["couverture_strates_pct"] < 60),
        "NON EXPLOITABLE — trop peu de disparitions ou strates mal couvertes", "exploitable")
    return d


def main() -> None:
    for p in (AVIS, BIZ, WAVES):
        if not p.exists():
            sys.exit(f"Fichier absent : {p}. Lancer d'abord : uv run scripts/build_tables.py")
    c = duckdb.connect(config={"memory_limit": "2GB"})

    g365 = charge(c, 365)
    scenarios = {
        "Stock de plus d'un an — tout le panel": standardise(g365),
        "Stock de plus d'un an — sans les 24 fiches purgées":
            standardise(g365[~g365["heavy_purge"].astype(bool)]),
        "Stock de plus de trois ans — tout le panel": standardise(charge(c, 1095)),
    }
    for nom, d in scenarios.items():
        print(f"\n{nom}")
        print(d.to_string(index=False))

    out = pd.concat([d.assign(scenario=nom) for nom, d in scenarios.items()], ignore_index=True)
    CSV.parent.mkdir(parents=True, exist_ok=True)
    out.round(3).to_csv(CSV, index=False, sep=";", decimal=",", encoding="utf-8-sig")
    print(f"\nÉcrit : {CSV}")
    write_note(scenarios)
    print(f"Écrit : {OUT}")


def write_note(scenarios: dict[str, pd.DataFrame]) -> None:
    f = lambda n: f"{n:,}".replace(",", " ")  # noqa: E731
    b = [BEGIN, ""]
    for nom, d in scenarios.items():
        b.append(f"### {nom}")
        b.append("")
        b.append("| Afflux reçu en 30 jours | Avis anciens | Disparitions | "
                 "À marché comparable, / 10 000 passages | Rapport | Fourchette | Exploitable ? |")
        b.append("|---|---:|---:|---:|---:|---:|---|")
        for _, r in d.iterrows():
            est = r["rapport_vs_moins_1pct"]
            if r["vitesse"] == LABELS["a_moins_1pct"]:
                rap, four = "référence", "—"
            elif np.isnan(est):
                rap, four = "—", "—"
            else:
                rap = f"×{est:.2f}"
                four = ("—" if np.isnan(r["rapport_borne_basse"])
                        else f"{r['rapport_borne_basse']:.2f} à {r['rapport_borne_haute']:.2f}")
            fia = "oui" if r["fiabilite"] == "exploitable" else "**non**"
            b.append(f"| {r['vitesse']} | {f(int(r['avis_anciens']))} | {f(int(r['morts']))} | "
                     f"{r['risque_standardise_pour_10k']:.2f} | {rap} | {four} | {fia} |")
        b.append("")
        mauvais = d[d["fiabilite"] != "exploitable"]["vitesse"].tolist()
        if mauvais:
            b.append(f"Non exploitable — {', '.join(str(x) for x in mauvais)} : moins de "
                     "20 disparitions, ou moins de 60 % du poids des strates couvert. "
                     "**Ne pas communiquer ces lignes.**")
            b.append("")
    b.append("« À marché comparable » recalcule chaque taux comme si tous les groupes avaient la "
             "même répartition de pays, secteur, taille de groupe et volume d'avis. C'est cette "
             "colonne qu'il faut lire.")
    b.append("")
    b.append(END)
    body = "\n".join(b)

    head = """---
date: 2026-09-06
projet: reviewflowz-analyse-google
titre: "Test 2 — la modération déborde-t-elle sur le stock ancien ?"
statut: résultats
---

# Test 2 — la modération déborde-t-elle sur le stock ancien ?

Produit par `scripts/test2_debordement.py`.

## La question, et pourquoi c'est celle qui porte le livrable

Un avis publié il y a plus d'un an n'a aucun rapport avec une campagne d'avis lancée le mois
dernier. Si Google le supprime davantage dans les fiches qui reçoivent un afflux récent que
dans des fiches comparables sans afflux, alors la modération emporte des avis sans rapport avec
sa cible. Un avis supprimé dans ce cas est une erreur de modération.

C'est le seul endroit de l'étude où l'angle du livrable devient une mesure plutôt qu'une
inférence indirecte.

## Ce qui est comparé

- **Le stock ancien** : avis créés plus de 365 jours avant la vague 1, et déjà présents à la
  vague 1. La seconde condition écarte la censure à droite — tous les avis retenus sont observés
  sur les mêmes treize intervalles entre passages.
- **Groupés par afflux reçu** : la part du stock que la fiche a reçue dans les 30 derniers jours.
- **À marché comparable** : chaque taux est recalculé comme si tous les groupes avaient la même
  répartition de pays, secteur, taille de groupe et volume. Sans cette correction, on mesurerait
  surtout que les fiches à fort afflux sont américaines et dans les services à domicile.

## Ce que le test ne prouve pas

- Une association, pas une causalité. Les fiches à fort afflux peuvent différer par autre chose
  que ce que la strate capture.
- Un avis ancien supprimé n'est pas nécessairement légitime : un faux avis ancien reste possible.
  L'argument est probabiliste — il porte sur un écart entre groupes comparables, pas sur le
  statut d'un avis donné.
- Le sens de la vélocité est lui-même en cause : l'analyse A a montré qu'elle n'a **aucun effet
  propre** sur le risque qu'une fiche soit touchée. Ce test porte sur une autre grandeur, le
  stock ancien, et se lit indépendamment.

## Résultats

"""
    if OUT.exists() and BEGIN in (prev := OUT.read_text(encoding="utf-8")) and END in prev:
        OUT.write_text(prev[: prev.index(BEGIN)] + body + prev[prev.index(END) + len(END):],
                       encoding="utf-8")
    else:
        OUT.write_text(head + body + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
