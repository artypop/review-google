"""
Machine learning sur le panel — contrôle, pas modèle de référence.

À quoi ça sert, et à quoi ça ne sert pas
---------------------------------------
Les modèles à base d'arbres (forêt aléatoire, gradient boosting) trouvent seuls des combinaisons
et des seuils qu'une régression ignore si on ne les a pas prévus. Ils répondent à deux questions
que les analyses A et B ne posent pas :

  1. l'ensemble des caractéristiques permet-il réellement de prédire une suppression, ou
     tourne-t-on autour du hasard ?
  2. reste-t-il un signal qu'on n'a pas vu — un effet qui n'apparaît que dans une combinaison
     particulière ?

Ils ne remplacent pas l'analyse B. Ils ne donnent pas d'effet chiffré interprétable
(« ×3 à note égale »), qui est ce que le livrable doit contenir. Et leur classement
d'importance favorise mécaniquement les variables à nombreuses valeurs.

Trois précautions, sans lesquelles le résultat serait faux
----------------------------------------------------------
  - **Découpage par établissement.** Un découpage au hasard mettrait des avis d'une même fiche
    des deux côtés : le modèle reconnaîtrait la fiche au lieu d'apprendre une règle. Les auteurs
    présents des deux côtés sont retirés du test pour la même raison.
  - **Jamais le taux de bonnes réponses.** Répondre « jamais supprimé » donne 97 % de réussite
    sur ce périmètre. On mesure la capacité à classer (AUC) et la précision moyenne.
  - **Contrôle sans les fiches purgées.** Sans lui, le modèle apprend surtout à reconnaître les
    24 établissements massivement purgés.

Mémoire
-------
La machine de travail a 7 Go et ce script l'a déjà saturée. Par défaut il n'entraîne donc que
le gradient boosting, qui travaille sur des histogrammes compressés et tient dans quelques
centaines de méga-octets. La forêt aléatoire, beaucoup plus gourmande, est en option.

    uv run scripts/machine_learning.py                    # léger, recommandé
    uv run scripts/machine_learning.py --avec-foret       # ajoute la forêt aléatoire
    uv run scripts/machine_learning.py --echantillon 40000

Toujours le lancer détaché du terminal, avec un plafond mémoire, pour qu'un dérapage ne fasse
pas tomber l'éditeur :

    setsid nohup bash -c 'ulimit -v 2500000; exec uv run scripts/machine_learning.py' \
      > data/resultats/ml_run.log 2>&1 < /dev/null &

Usage :  uv run scripts/machine_learning.py [--avec-foret] [--echantillon N]
"""

import argparse
import pathlib
import sys
import warnings

import duckdb
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import GroupShuffleSplit
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

SRC = pathlib.Path("data/build/reviews_features.parquet")
BIZ = pathlib.Path("data/build/business_features.parquet")
OUT = pathlib.Path("documentations/2026-09-06-machine-learning-controle.md")
CSV = pathlib.Path("data/resultats/ml_importance_variables.csv")
BEGIN = "<!-- genere:ml — regenere par scripts/machine_learning.py, ne pas editer a la main -->"
END = "<!-- /genere:ml -->"
SEED = 12345

SQL = """
SELECT a.cid, a.author_key, a.deleted::INT AS y,

       -- durée d'observation : un avis publié la veille du dernier passage a eu moins
       -- d'occasions de disparaître. Sans ça le modèle apprendrait surtout la date.
       date_diff('day', a.first_seen_at, TIMESTAMP '2026-08-24 07:00:00') AS jours_observes,

       a.age_days_w1 AS age_jours, a.star AS note,
       a.has_text::INT AS a_du_texte, a.text_chars AS longueur_texte,
       a.n_photos AS nb_photos, a.has_reply::INT AS reponse_proprietaire,
       a.lang_off_modal::INT AS langue_etrangere, a.was_edited::INT AS avis_modifie,

       coalesce(a.local_guide_level, 0) AS niveau_local_guide,
       a.lg_level_missing::INT AS niveau_absent,
       a.reviewer_review_count AS nb_avis_auteur, a.rc_zero::INT AS compteur_a_zero,
       a.reviewer_photo_count AS nb_photos_auteur,
       a.new_account::INT AS compte_neuf,
       a.author_n_panel_biz AS nb_fiches_auteur,
       a.author_same_day_burst::INT AS rafale_auteur,

       e.velocity_30d AS vitesse_collecte, e.n_reviews_panel AS taille_fiche,
       e.mean_star_panel AS note_moyenne_fiche, e.mean_star_delta AS variation_note_fiche,
       (e.region = 'US')::INT AS etats_unis,
       e.industry AS secteur, e.bucket AS taille_groupe,
       e.heavy_purge::INT AS fiche_purgee
FROM 'REVIEWS' a JOIN 'BIZ' e USING (cid)
WHERE a.is_fresh
"""

DROP = ["cid", "author_key", "y", "secteur", "taille_groupe", "fiche_purgee"]


def load() -> pd.DataFrame:
    if not SRC.exists():
        sys.exit(f"Table absente : {SRC}. Lancer d'abord : uv run scripts/build_tables.py")
    c = duckdb.connect(config={'memory_limit': '1GB'})
    sql = SQL.replace("'REVIEWS'", f"'{SRC.as_posix()}'").replace("'BIZ'", f"'{BIZ.as_posix()}'")
    d = c.sql(sql).df()
    # secteur et taille en indicatrices : les arbres de scikit-learn n'acceptent pas le texte
    d = pd.concat([d, pd.get_dummies(d["secteur"], prefix="secteur", dtype="int8"),
                   pd.get_dummies(d["taille_groupe"], prefix="taille", dtype="int8")], axis=1)
    # float32 plutôt que float64 : deux fois moins de mémoire, précision largement suffisante
    num = [c for c in d.columns if d[c].dtype == "float64"]
    d[num] = d[num].astype("float32")
    return d


def split(d: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Découpage par établissement, puis retrait des auteurs présents des deux côtés."""
    gss = GroupShuffleSplit(n_splits=1, test_size=0.30, random_state=SEED)
    itr, ite = next(gss.split(d, groups=d["cid"]))
    train, test = d.iloc[itr].copy(), d.iloc[ite].copy()
    fuite = set(train["author_key"]) & set(test["author_key"])
    test = test[~test["author_key"].isin(fuite)]
    return train, test


def evaluate(name: str, model, train: pd.DataFrame, test: pd.DataFrame,
             features: list[str]) -> dict:
    Xtr, ytr = train[features], train["y"]
    Xte, yte = test[features], test["y"]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        model.fit(Xtr, ytr)
        p = model.predict_proba(Xte)[:, 1]
    return {
        "modele": name,
        "auc": roc_auc_score(yte, p),
        "precision_moyenne": average_precision_score(yte, p),
        "taux_base": yte.mean(),
        "_model": model, "_p": p,
    }


def run(d: pd.DataFrame, titre: str, avec_foret: bool = False) -> tuple[pd.DataFrame, pd.DataFrame]:
    train, test = split(d)
    features = [c for c in d.columns if c not in DROP]
    print(f"\n--- {titre} ---")
    print(f"  entraînement {len(train):,} avis / {train.cid.nunique()} fiches / "
          f"{int(train.y.sum())} supprimés".replace(",", " "))
    print(f"  test         {len(test):,} avis / {test.cid.nunique()} fiches / "
          f"{int(test.y.sum())} supprimés".replace(",", " "))

    models = [
        # add_indicator : le fait qu'une valeur manque est conservé comme information,
        # au lieu d'être noyé dans la médiane. Voir la discussion sur le compteur à 0.
        ("Régression logistique (référence)",
         make_pipeline(SimpleImputer(strategy="median", add_indicator=True), StandardScaler(),
                       LogisticRegression(max_iter=2000, class_weight="balanced"))),
        ("Gradient boosting",
         HistGradientBoostingClassifier(max_iter=250, learning_rate=0.08, random_state=SEED)),
    ]
    if avec_foret:
        models.append(
            ("Forêt aléatoire",
             make_pipeline(SimpleImputer(strategy="median", add_indicator=True),
                           RandomForestClassifier(n_estimators=200, min_samples_leaf=50, n_jobs=2,
                                                  class_weight="balanced_subsample",
                                                  random_state=SEED))))
    results = [evaluate(n, m, train, test, features) for n, m in models]
    perf = pd.DataFrame([{k: v for k, v in r.items() if not k.startswith("_")} for r in results])
    print(perf.round(4).to_string(index=False))

    best = max(results, key=lambda r: r["auc"])
    print(f"  importance des variables sur : {best['modele']}")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        imp = permutation_importance(best["_model"], test[features], test["y"],
                                     n_repeats=5, random_state=SEED, n_jobs=1,
                                     scoring="roc_auc")
    importance = (pd.DataFrame({"variable": features, "importance": imp.importances_mean})
                  .sort_values("importance", ascending=False).reset_index(drop=True))
    return perf.assign(perimetre=titre), importance.assign(perimetre=titre)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--avec-foret", action="store_true",
                   help="ajouter la forêt aléatoire (gourmande en mémoire)")
    p.add_argument("--echantillon", type=int, default=0,
                   help="ne garder que N avis tirés au hasard, pour un essai rapide")
    a = p.parse_args()

    d = load()
    if a.echantillon and a.echantillon < len(d):
        # tirage par établissement : garder les fiches entières, sinon le découpage n'a plus de sens
        cids = d["cid"].drop_duplicates().sample(frac=1.0, random_state=SEED)
        garde, n = [], 0
        for cid in cids:
            garde.append(cid)
            n += int((d["cid"] == cid).sum())
            if n >= a.echantillon:
                break
        d = d[d["cid"].isin(garde)]
        print(f"Échantillon : {len(d)} avis sur {d.cid.nunique()} fiches")
    print(f"Périmètre frais : {len(d):,} avis, {int(d.y.sum())} supprimés, "
          f"taux {100 * d.y.mean():.2f} %".replace(",", " "))

    perf_all, imp_all = run(d, "Tout le panel", a.avec_foret)
    sans = d[d["fiche_purgee"] == 0]
    perf_ctrl, imp_ctrl = run(sans, "Sans les 24 fiches purgées", a.avec_foret)

    perf = pd.concat([perf_all, perf_ctrl], ignore_index=True)
    imp = pd.concat([imp_all, imp_ctrl], ignore_index=True)

    CSV.parent.mkdir(parents=True, exist_ok=True)
    imp.round(5).to_csv(CSV, index=False, sep=";", decimal=",", encoding="utf-8-sig")
    print(f"\nÉcrit : {CSV}")
    write_note(perf, imp)
    print(f"Écrit : {OUT}")


def write_note(perf: pd.DataFrame, imp: pd.DataFrame) -> None:
    blocks = [BEGIN, "### Capacité à prédire\n",
              "| Périmètre | Modèle | AUC | Précision moyenne | Taux de suppression |",
              "|---|---|---:|---:|---:|"]
    for _, r in perf.iterrows():
        blocks.append(f"| {r['perimetre']} | {r['modele']} | {r['auc']:.3f} | "
                      f"{r['precision_moyenne']:.3f} | {100 * r['taux_base']:.2f} % |")
    blocks.append("")
    for per in imp["perimetre"].unique():
        sub = imp[imp["perimetre"] == per].head(15)
        blocks.append(f"### Variables les plus utiles — {per}\n")
        blocks.append("| Variable | Perte d'AUC si on la brouille |")
        blocks.append("|---|---:|")
        for _, r in sub.iterrows():
            blocks.append(f"| {r['variable']} | {r['importance']:.4f} |")
        blocks.append("")
    blocks.append(END)
    body = "\n".join(blocks)

    head = """---
date: 2026-09-06
projet: reviewflowz-analyse-google
titre: "Machine learning — contrôle des effets non prévus"
statut: résultats
---

# Machine learning — contrôle des effets non prévus

Produit par `scripts/machine_learning.py`.

## Pourquoi ce modèle existe, et ce qu'il ne fait pas

Il répond à deux questions que les analyses A et B ne posent pas :

1. l'ensemble des caractéristiques permet-il vraiment de prédire une suppression, ou
   tourne-t-on autour du hasard ?
2. reste-t-il un signal qu'on n'a pas vu, qui n'apparaîtrait que dans une combinaison
   particulière ?

**Ce n'est pas le modèle de référence de l'étude.** Il ne produit pas d'effet chiffré
interprétable du type « ×3 à note égale », qui est ce que le livrable doit contenir. Son
classement d'importance favorise en outre les variables à nombreuses valeurs. Il sert de
contrôle : si une variable y ressort alors qu'on l'avait négligée, il faut retourner l'examiner
dans l'analyse B.

## Comment lire les chiffres

**L'AUC** est la capacité à classer : si on prend un avis supprimé et un avis conservé au
hasard, c'est la probabilité que le modèle donne le score le plus élevé au supprimé. 0,5 = pas
mieux que pile ou face. 1 = séparation parfaite. Au-delà de 0,80 le signal est net.

**La précision moyenne** compte davantage ici, parce que les suppressions sont rares. Elle se
compare au taux de suppression indiqué dans la dernière colonne : une précision moyenne de 0,20
quand le taux vaut 0,03 signifie que le modèle fait sept fois mieux que le hasard.

**Le taux de bonnes réponses n'est pas donné, volontairement.** Répondre « jamais supprimé » en
atteindrait 97 % sans rien apprendre.

**L'importance** est mesurée en brouillant une variable au hasard et en regardant combien d'AUC
on perd. C'est plus fiable que l'importance fournie par défaut, qui surestime les variables à
nombreuses valeurs.

## Trois précautions appliquées

**Découpage par établissement.** Entraînement et test ne partagent aucune fiche. Un découpage au
hasard laisserait des avis d'une même fiche des deux côtés, et le modèle reconnaîtrait la fiche
au lieu d'apprendre une règle. Les auteurs présents des deux côtés sont retirés du test.

**Durée d'observation incluse comme variable.** Un avis publié la veille du dernier passage a eu
moins d'occasions de disparaître. Sans cette variable, le modèle apprendrait surtout la date de
publication.

**Un second passage sans les 24 fiches massivement purgées.** Elles portent 23 % des
suppressions. Si les performances s'effondrent sans elles, c'est qu'on avait surtout appris à
reconnaître ces établissements.

## Résultats

"""
    if OUT.exists() and BEGIN in (prev := OUT.read_text(encoding="utf-8")) and END in prev:
        OUT.write_text(prev[: prev.index(BEGIN)] + body + prev[prev.index(END) + len(END):],
                       encoding="utf-8")
    else:
        OUT.write_text(head + body + "\n", encoding="utf-8")


if __name__ == "__main__":
    sys.stdout.reconfigure(line_buffering=True)
    main()
