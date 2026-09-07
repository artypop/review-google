"""
Analyse B — dans une fiche qui perd des avis, lequel tombe ?

Principe. On ne compare que des avis d'une même fiche, un même jour. Concrètement : parmi les
avis de cette salle de sport encore en ligne le 17 août, lesquels ont disparu au passage
suivant ? La réponse est agrégée sur toutes les fiches et tous les jours.

Ce que ça règle, et qui justifie le détour :

  - tout ce qui est propre à la fiche disparaît de l'équation — secteur, pays, taille,
    clientèle, politique de modération — puisque c'est identique pour les avis comparés ;
  - une journée où Google purge la totalité d'une fiche n'apporte aucune comparaison utile et
    sort d'elle-même du calcul. Les fiches massivement purgées cessent de peser ;
  - la date sort aussi : les jours où Google supprime beaucoup ne biaisent plus les
    comparaisons, puisqu'on ne compare que des avis du même jour.

Conséquence à retenir : secteur, région et taille du groupe **ne peuvent pas** figurer ici. Ils
sont constants dans une fiche. Ils relèvent de l'analyse A. Ils n'apparaissent qu'en croisement
(l'effet de la note est-il le même aux États-Unis et en Europe ?).

Marges d'erreur : par rééchantillonnage des établissements, pas des lignes. Deux avis d'une même
fiche ne sont pas deux informations indépendantes ; les marges affichées par défaut par un
modèle l'oublient et sont trop étroites.

Usage :  uv run scripts/analysis_b.py [--bootstrap N]
"""

import argparse
import os
import pathlib
import sys
import warnings

# Un seul coeur. Sans ça, statsmodels et numpy saturent toutes les unités de calcul pendant
# des heures et WSL finit par lâcher la connexion de VSCode. À poser AVANT l'import de numpy.
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
           "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_v, "1")

import duckdb
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.discrete.conditional_models import ConditionalLogit

SRC = pathlib.Path("data/build/fresh_hazard.parquet")
BIZ = pathlib.Path("data/build/business_features.parquet")
OUT = pathlib.Path("documentations/2026-09-06-analyse-b-quel-avis-tombe.md")
CSV = pathlib.Path("data/resultats/analyse_b_effets.csv")
TIRAGES = pathlib.Path("data/resultats/analyse_b_tirages.csv")
BEGIN = "<!-- genere:analyseb — regenere par scripts/analysis_b.py, ne pas editer a la main -->"
END = "<!-- /genere:analyseb -->"

# Chaque entrée : (colonne construite, libellé lisible, modalité de référence)
BLOCKS = [
    ("note", "Note de l'avis", "4 etoiles"),
    ("age", "Âge de l'avis au moment du passage", "b_7_13j"),
    ("texte", "Texte de l'avis", "c_51_150c"),
    ("photos", "Photos jointes", "a_aucune"),
    ("reponse", "Réponse du propriétaire", "a_sans"),
    ("langue", "Langue de l'avis", "a_langue_locale"),
    ("edition", "Avis modifié depuis publication", "a_non_modifie"),
    ("niveau_lg", "Niveau Local Guide de l'auteur", "b_niveau_1_3"),
    ("volume_auteur", "Nombre d'avis publiés par l'auteur", "d_3_20_avis"),
    ("multi_fiches", "Auteur présent sur plusieurs fiches du panel", "a_une_fiche"),
    ("rafale", "Auteur ayant publié plusieurs avis le même jour", "a_non"),
]

LABELS = {
    "1 etoile": "1 étoile", "2 etoiles": "2 étoiles", "3 etoiles": "3 étoiles",
    "4 etoiles": "4 étoiles", "5 etoiles": "5 étoiles",
    "a_0_6j": "0 à 6 jours", "b_7_13j": "7 à 13 jours", "c_14_20j": "14 à 20 jours",
    "d_21_29j": "21 à 29 jours", "e_30j_plus": "30 jours et plus",
    "a_note_seule": "note seule, sans texte", "b_1_50c": "1 à 50 caractères",
    "c_51_150c": "51 à 150 caractères", "d_151_400c": "151 à 400 caractères",
    "e_400c_plus": "plus de 400 caractères",
    "a_aucune": "aucune photo", "b_une": "une photo", "c_deux_plus": "deux photos ou plus",
    "a_sans": "sans réponse", "b_avec": "avec réponse du propriétaire",
    "a_langue_locale": "langue de la fiche", "b_langue_etrangere": "autre langue",
    "a_non_modifie": "non modifié", "b_modifie": "modifié depuis publication",
    "a_niveau_absent": "aucun niveau", "b_niveau_1_3": "niveau 1 à 3",
    "c_niveau_4_5": "niveau 4 ou 5", "d_niveau_6_plus": "niveau 6 et plus",
    "a_compteur_0": "compteur à 0", "b_1_2_avis": "1 ou 2 avis", "d_3_20_avis": "3 à 20 avis",
    "e_21_100_avis": "21 à 100 avis", "f_100_avis_plus": "plus de 100 avis",
    "a_une_fiche": "une seule fiche", "b_plusieurs_fiches": "plusieurs fiches",
    "a_non": "non", "b_rafale": "rafale le même jour",
}

SQL = """
SELECT s.cid, s.wave, s.died::INT AS y,
       s.star || CASE WHEN s.star = 1 THEN ' etoile' ELSE ' etoiles' END AS note,
       CASE WHEN s.age_days < 7 THEN 'a_0_6j' WHEN s.age_days < 14 THEN 'b_7_13j'
            WHEN s.age_days < 21 THEN 'c_14_20j' WHEN s.age_days < 30 THEN 'd_21_29j'
            ELSE 'e_30j_plus' END AS age,
       CASE WHEN NOT s.has_text THEN 'a_note_seule' WHEN s.text_chars <= 50 THEN 'b_1_50c'
            WHEN s.text_chars <= 150 THEN 'c_51_150c' WHEN s.text_chars <= 400 THEN 'd_151_400c'
            ELSE 'e_400c_plus' END AS texte,
       CASE WHEN s.n_photos = 0 THEN 'a_aucune' WHEN s.n_photos = 1 THEN 'b_une'
            ELSE 'c_deux_plus' END AS photos,
       CASE WHEN s.has_reply THEN 'b_avec' ELSE 'a_sans' END AS reponse,
       CASE WHEN s.lang_off_modal THEN 'b_langue_etrangere' ELSE 'a_langue_locale' END AS langue,
       CASE WHEN s.was_edited THEN 'b_modifie' ELSE 'a_non_modifie' END AS edition,
       CASE WHEN s.lg_level_missing THEN 'a_niveau_absent'
            WHEN s.local_guide_level <= 3 THEN 'b_niveau_1_3'
            WHEN s.local_guide_level <= 5 THEN 'c_niveau_4_5'
            ELSE 'd_niveau_6_plus' END AS niveau_lg,
       CASE WHEN s.rc_zero THEN 'a_compteur_0' WHEN s.reviewer_review_count <= 2 THEN 'b_1_2_avis'
            WHEN s.reviewer_review_count <= 20 THEN 'd_3_20_avis'
            WHEN s.reviewer_review_count <= 100 THEN 'e_21_100_avis'
            ELSE 'f_100_avis_plus' END AS volume_auteur,
       CASE WHEN s.author_n_panel_biz > 1 THEN 'b_plusieurs_fiches'
            ELSE 'a_une_fiche' END AS multi_fiches,
       CASE WHEN s.author_same_day_burst THEN 'b_rafale' ELSE 'a_non' END AS rafale,
       s.region, b.heavy_purge
FROM s JOIN b USING (cid)
WHERE b.n_fresh_deleted > 0
"""


def load() -> pd.DataFrame:
    if not SRC.exists():
        sys.exit(f"Table absente : {SRC}. Lancer d'abord : uv run scripts/build_tables.py")
    c = duckdb.connect(config={'memory_limit': '1GB'})
    c.sql(f"CREATE VIEW s AS SELECT * FROM '{SRC.as_posix()}'")
    c.sql(f"CREATE VIEW b AS SELECT * FROM '{BIZ.as_posix()}'")
    return c.sql(SQL).df()


def design(d: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Matrice d'indicatrices, une modalité de référence retirée par bloc."""
    parts, names = [], []
    for col, _, ref in BLOCKS:
        dummies = pd.get_dummies(d[col], prefix=col, dtype=float)
        refcol = f"{col}_{ref}"
        if refcol not in dummies.columns:
            sys.exit(f"Référence absente : {refcol}")
        dummies = dummies.drop(columns=[refcol])
        parts.append(dummies)
        names += list(dummies.columns)
    return pd.concat(parts, axis=1), names


def informative(d: pd.DataFrame) -> pd.DataFrame:
    """Ne garder que les strates fiche x jour où des avis tombent ET d'autres survivent."""
    d = d.copy()
    d["strate"] = d["cid"] + "_w" + d["wave"].astype(str)
    g = d.groupby("strate")["y"].agg(["sum", "count"])
    keep = g[(g["sum"] > 0) & (g["sum"] < g["count"])].index
    return d[d["strate"].isin(keep)].copy()


def fit(d: pd.DataFrame) -> pd.Series:
    X, names = design(d)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        res = ConditionalLogit(d["y"].to_numpy(), X.to_numpy(),
                               groups=d["strate"].to_numpy()).fit(disp=False)
    return pd.Series(res.params, index=names)


def marges_rapides(d: pd.DataFrame) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Marges d'erreur en 3 minutes, sans rééchantillonnage.

    Au lieu de refaire l'analyse 30 fois sur des tirages au sort d'établissements, on écrit
    les strates fiche x jour comme autant de colonnes du modèle, et on demande des erreurs-types
    groupées par établissement — deux avis d'une même fiche n'étant pas deux informations
    indépendantes. Le résultat est directement une fourchette.

    Écart connu avec la méthode de référence : la rafale d'auteur y est surestimée (26 contre
    19). Sur tous les autres facteurs les deux méthodes concordent. **Ne pas utiliser cette
    méthode pour communiquer l'effet de la rafale.**
    """
    X, names = design(d)
    strates = pd.get_dummies(d["strate"], prefix="s", dtype=np.float32).iloc[:, 1:]
    M = np.hstack([X.to_numpy(np.float32), strates.to_numpy(np.float32)])
    del strates
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        res = sm.Logit(d["y"].to_numpy(), M).fit(
            method="lbfgs", maxiter=300, disp=False,
            cov_type="cluster", cov_kwds={"groups": d["cid"].to_numpy()})
    k = len(names)
    co = pd.Series(res.params[:k], index=names)
    se = pd.Series(res.bse[:k], index=names)
    return co, co - 1.96 * se, co + 1.96 * se


def bootstrap(d: pd.DataFrame, n: int, seed: int = 12345) -> pd.DataFrame:
    """Rééchantillonner les ÉTABLISSEMENTS, pas les lignes : c'est l'unité indépendante.

    Chaque tirage est écrit sur disque dès qu'il est calculé. Un arrêt en cours de route
    ne perd rien : relancer la même commande reprend là où on s'était arrêté.
    """
    done = pd.DataFrame()
    if TIRAGES.exists():
        done = pd.read_csv(TIRAGES)
        if len(done) >= n:
            print(f"  {len(done)} tirages déjà en réserve, rien à recalculer", file=sys.stderr)
            return done
        print(f"  reprise : {len(done)} tirages déjà faits, {n - len(done)} restants",
              file=sys.stderr)

    rng = np.random.default_rng(seed)
    cids = d["cid"].unique()
    by_cid = {k: v for k, v in d.groupby("cid")}
    # Rejouer les tirages déjà faits pour ne pas rejouer la même graine deux fois
    for _ in range(len(done)):
        rng.choice(cids, size=len(cids), replace=True)

    failed = 0
    for i in range(len(done), n):
        pick = rng.choice(cids, size=len(cids), replace=True)
        rep = pd.concat([by_cid[k].assign(strate=lambda x, j=j: x["strate"] + f"#{j}")
                         for j, k in enumerate(pick)], ignore_index=True)
        try:
            row = fit(informative(rep))
            done = pd.concat([done, row.to_frame().T], ignore_index=True)
            TIRAGES.parent.mkdir(parents=True, exist_ok=True)
            done.to_csv(TIRAGES, index=False)   # sauvegarde après chaque tirage
        except Exception:  # noqa: BLE001 — un tirage dégénéré est écarté, pas fatal
            failed += 1
        del rep
        print(f"  tirage {i + 1}/{n}", file=sys.stderr, flush=True)
    if failed:
        print(f"  ({failed} tirages écartés)", file=sys.stderr)
    return done


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--bootstrap", type=int, default=0,
                   help="marges par rééchantillonnage : le plus juste, mais ~2 min PAR tirage")
    p.add_argument("--marges-rapides", action="store_true",
                   help="marges en 3 min au lieu d'une heure (réserve : surestime la rafale)")
    a = p.parse_args()

    raw = load()
    d = informative(raw)
    n_biz, n_obs, n_death = d["cid"].nunique(), len(d), int(d["y"].sum())
    lost = int(raw["y"].sum()) - n_death
    print(f"Comparaisons utilisables : {n_biz} fiches, {n_obs} observations, {n_death} disparitions")
    print(f"Écartées : {lost} disparitions survenues lors de purges totales (aucune comparaison possible)")

    if a.marges_rapides:
        print("Marges d'erreur, méthode rapide (~3 min)...")
        coefs, lo, hi = marges_rapides(d)
        methode = "rapide"
    else:
        coefs = fit(d)
        methode = "bootstrap" if a.bootstrap else "aucune"

    if a.marges_rapides:
        pass
    elif a.bootstrap:
        print(f"Marges d'erreur par rééchantillonnage des fiches ({a.bootstrap} tirages)...")
        bs = bootstrap(d, a.bootstrap)
        lo, hi = bs.quantile(0.025), bs.quantile(0.975)
    else:
        lo = hi = pd.Series(np.nan, index=coefs.index)

    rows = []
    for col, label, ref in BLOCKS:
        for name in coefs.index:
            if not name.startswith(f"{col}_"):
                continue
            mod = name[len(col) + 1:]
            rows.append({
                "facteur": label,
                "modalite": LABELS.get(mod, mod),
                "reference": LABELS.get(ref, ref),
                "effet": float(np.exp(coefs[name])),
                "borne_basse": float(np.exp(lo[name])) if name in lo.index else np.nan,
                "borne_haute": float(np.exp(hi[name])) if name in hi.index else np.nan,
            })
    out = pd.DataFrame(rows)
    # Sans marges d'erreur on ne peut rien affirmer : la colonne reste vide, jamais « oui ».
    ecarte_1 = (out["borne_basse"] > 1) | (out["borne_haute"] < 1)
    out["ecart_net"] = np.where(out["borne_basse"].isna(), "non calculé",
                                np.where(ecarte_1, "oui", "non"))

    CSV.parent.mkdir(parents=True, exist_ok=True)
    out.round(3).to_csv(CSV, index=False, sep=";", decimal=",", encoding="utf-8-sig")
    print(f"Écrit : {CSV}")

    write_note(out, n_biz, n_obs, n_death, lost, a.bootstrap, methode)
    print(f"Écrit : {OUT}")


def write_note(out: pd.DataFrame, n_biz: int, n_obs: int, n_death: int,
               lost: int, nboot: int, methode: str = "bootstrap") -> None:
    f = lambda n: f"{n:,}".replace(",", " ")  # noqa: E731
    blocks = []
    for label in out["facteur"].unique():
        sub = out[out["facteur"] == label]
        ref = sub["reference"].iloc[0]
        blocks.append(f"### {label}\n")
        blocks.append(f"Comparé à : **{ref}**.\n")
        blocks.append("| Modalité | Effet | Fourchette | Écart net ? |")
        blocks.append("|---|---:|---:|---|")
        for _, r in sub.iterrows():
            fourch = ("—" if np.isnan(r["borne_basse"])
                      else f"{r['borne_basse']:.2f} à {r['borne_haute']:.2f}")
            blocks.append(f"| {r['modalite']} | ×{r['effet']:.2f} | {fourch} | "
                          f"{r['ecart_net']} |")
        blocks.append("")
    body = f"{BEGIN}\n" + "\n".join(blocks) + f"\n{END}"

    head = f"""---
date: 2026-09-06
projet: reviewflowz-analyse-google
titre: "Analyse B — dans une fiche qui perd des avis, lequel tombe ?"
statut: résultats
---

# Analyse B — dans une fiche qui perd des avis, lequel tombe ?

Produit par `scripts/analysis_b.py`.

## Ce que compare cette analyse

**Uniquement des avis d'une même fiche, un même jour.** La question posée est : parmi les avis
de cet établissement encore en ligne ce jour-là, lesquels ont disparu au passage suivant ?

C'est ce qui distingue l'analyse B des tableaux facteur par facteur. Là-bas, on comparait tous
les avis du panel entre eux, et un écart pouvait venir du type d'établissement plutôt que de
l'avis. Ici, tout ce qui est propre à la fiche s'annule : secteur, pays, taille, clientèle,
politique de modération. Et la date s'annule aussi, donc les jours de forte suppression ne
faussent plus la comparaison.

**Les fiches purgées cessent de peser.** Quand Google efface tous les avis d'une fiche un jour
donné, il n'y a plus de survivant à comparer : la journée n'apporte rien et sort du calcul. Plus
besoin de retirer les fiches problématiques à la main.

## Sur quoi porte le calcul

- **{f(n_biz)} établissements**, ceux qui ont perdu au moins un avis récent
- **{f(n_obs)} observations** — un avis vérifié à un passage du robot
- **{f(n_death)} disparitions** effectivement comparables
- **{f(lost)} disparitions écartées** : elles surviennent lors de purges totales, où aucun avis
  de la fiche ne survit ce jour-là. Aucune comparaison n'y est possible.

## Comment lire les résultats

**L'effet** se lit comme un rapport de risque, la modalité de référence valant 1. « ×2 » signifie
deux fois plus supprimé qu'un avis identique par ailleurs, dans la même fiche, le même jour.

**La fourchette** {"est calculée par la méthode rapide" if methode == "rapide" else
f"est obtenue en retirant et rejouant au hasard les établissements {f(nboot)} fois"} :
{"les strates fiche x jour entrent comme colonnes du modèle et les marges sont groupées par établissement" if methode == "rapide" else "on rééchantillonne les établissements et non les lignes"},
parce que deux avis d'une même fiche ne sont pas deux informations indépendantes — les marges
affichées par défaut par un modèle l'oublient et sont trop étroites.

{"**Réserve sur cette méthode.** Elle surestime l'effet de la rafale d'auteur (26 contre 19 avec la méthode de référence). Sur tous les autres facteurs les deux méthodes concordent. Ne pas communiquer le chiffre de la rafale à partir de cette version." if methode == "rapide" else ""}

**Écart net** vaut « oui » quand la fourchette ne contient pas 1, c'est-à-dire quand on peut
exclure l'absence d'effet.

## Ce qui ne peut pas figurer ici

Le secteur, la région et la taille du groupe sont identiques pour tous les avis d'une même fiche.
L'analyse B ne peut donc rien en dire — c'est le prix de sa rigueur, et c'est l'objet de
l'analyse A.

## Résultats

"""
    if OUT.exists() and BEGIN in (prev := OUT.read_text(encoding="utf-8")) and END in prev:
        OUT.write_text(prev[: prev.index(BEGIN)] + body + prev[prev.index(END) + len(END):],
                       encoding="utf-8")
    else:
        OUT.write_text(head + body + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
