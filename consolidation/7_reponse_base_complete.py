"""7. La réponse du propriétaire sur toute la base, taux directs.

    uv run python consolidation/7_reponse_base_complete.py

LA QUESTION
  Parmi les avis déjà en ligne le 11 août 2026, ceux qui avaient une réponse
  du propriétaire disparaissent-ils moins, du 12 au 24 août, que ceux qui n'en
  avaient pas, à âge et habitude de fiche comparables ?

CE QUE CE CALCUL AJOUTE AU POINT 5
  Le point 5 suit les avis de 03B jour par jour : 1 349 suppressions, sur des
  avis de moins de 14 jours dont la réponse arrive pendant le suivi. Ici, la
  réponse date d'avant le suivi, et tous les avis de la base publiés avant le
  11 août comptent, avec leurs suppressions.

LECTURE
  Une ligne = une case : périmètre, région, taille, habitude de la fiche, âge.
  Pour les avis répondus et pour les avis sans réponse : avis, suppressions,
  suppressions pour 10 000 avis, fiches touchées, part de la première fiche.
  `rapport` : taux des avis répondus divisé par celui des avis sans réponse.
  « ×0,5 » : l'avis répondu disparaît deux fois moins.

  C'est un calcul direct, sans modèle : la note, le secteur et le profil de
  l'auteur ne sont pas tenus égaux. `citable` applique la règle de `commun.py`
  aux deux cases comparées.

Produit :
  sorties/7_controle.csv               totaux de la base, rapprochement des comptages
  sorties/7_reponse_base_complete.csv  une ligne par case
  sorties/figures/7_reponse_base_complete.png
"""
import numpy as np

from commun import (COULEURS, MIN_FICHES_CITABLE, MIN_SUPPRESSIONS_CITABLE,
                    PART_MAX_PREMIERE_FICHE, ecrire_csv, enregistrer, figure, requete)

controle = requete("7_controle")
print(controle.to_string(index=False))
ecrire_csv(controle, "7_controle")

df = requete("7_reponse_base_complete")
mesures = ["avis", "suppressions", "fiches", "fiches_touchees", "suppressions_de_la_premiere_fiche"]
df[mesures] = df[mesures].astype(int)

# Contrôle : les tranches d'âge redonnent la population du point 7.
cases = df[(df["perimetre"] == "tous") & (df["region"] == "ensemble") & (df["taille"] == "toutes")
           & (df["habitude"] == "toutes") & (df["age"] != "0. tous âges")]
attendu = controle.loc[controle["ordre"] == 2].iloc[0]
print(f"  contrôle : {cases['avis'].sum()} avis et {cases['suppressions'].sum()} suppressions dans les "
      f"cases, {attendu['avis']} et {attendu['suppressions']} attendus")

df["part_de_la_premiere_fiche"] = (df["suppressions_de_la_premiere_fiche"]
                                   / df["suppressions"].where(df["suppressions"] > 0)).round(2)
df["citable"] = ((df["suppressions"] >= MIN_SUPPRESSIONS_CITABLE)
                 & (df["fiches_touchees"] >= MIN_FICHES_CITABLE)
                 & (df["part_de_la_premiere_fiche"] <= PART_MAX_PREMIERE_FICHE))
df["pour_10000"] = (10000 * df["suppressions"] / df["avis"]).round(1)

# Avis répondus et avis sans réponse côte à côte, une ligne par case.
cles = ["perimetre", "region", "taille", "habitude", "age"]
colonnes = ["avis", "suppressions", "pour_10000", "fiches_touchees", "part_de_la_premiere_fiche", "citable"]
large = df.pivot(index=cles, columns="reponse", values=colonnes)
large.columns = [f"{reponse}_{mesure}" for mesure, reponse in large.columns]
large = large[[f"{r}_{m}" for r in ["repondu", "sans_reponse"] for m in colonnes]].reset_index()
for r in ["repondu", "sans_reponse"]:
    for m in ["avis", "suppressions", "fiches_touchees"]:
        large[f"{r}_{m}"] = large[f"{r}_{m}"].astype("Int64")
    large[f"{r}_pour_10000"] = large[f"{r}_pour_10000"].astype(float)
    large[f"{r}_part_de_la_premiere_fiche"] = large[f"{r}_part_de_la_premiere_fiche"].astype(float)

# Le rapport se calcule sur les taux non arrondis.
taux = {r: large[f"{r}_suppressions"].astype(float) / large[f"{r}_avis"].astype(float)
        for r in ["repondu", "sans_reponse"]}
large["rapport"] = (taux["repondu"] / taux["sans_reponse"].where(taux["sans_reponse"] > 0)).round(2)
large["citable"] = np.where(large["repondu_citable"].fillna(False).astype(bool)
                            & large["sans_reponse_citable"].fillna(False).astype(bool), "oui", "non")
large = large.drop(columns=["repondu_citable", "sans_reponse_citable"])

ORDRE = {"perimetre": ["tous", "sans_enseignes"], "region": ["ensemble", "US", "Europe"],
         "taille": ["toutes", "mono + small", "large"],
         "habitude": ["toutes", "plus de 75 %", "75 % ou moins", "inconnue"]}
for col, ordre in ORDRE.items():
    large[f"_{col}"] = large[col].map(ordre.index)
large = large.sort_values([f"_{c}" for c in ORDRE] + ["age"]).drop(columns=[f"_{c}" for c in ORDRE])
large["age"] = large["age"].str.split(". ", n=1).str[1]  # le numéro ne servait qu'au tri
ecrire_csv(large, "7_reponse_base_complete")

# Contrôle : avis répondus et sans réponse par âge, un panneau par périmètre et par habitude.
GRIS = "#b0afa9"
fig, axes = figure(2, 2, largeur=12, hauteur=8)
for ligne, perimetre in zip(axes, ["tous", "sans_enseignes"]):
    for ax, habitude in zip(ligne, ["plus de 75 %", "75 % ou moins"]):
        p = large[(large["perimetre"] == perimetre) & (large["region"] == "ensemble")
                  & (large["taille"] == "toutes") & (large["habitude"] == habitude)
                  & (large["age"] != "tous âges")]
        x = np.arange(len(p))
        ax.bar(x - 0.2, p["repondu_pour_10000"], width=0.38, color=COULEURS["ensemble"], label="avis répondu")
        ax.bar(x + 0.2, p["sans_reponse_pour_10000"], width=0.38, color=GRIS, label="sans réponse")
        ax.set_xticks(x, p["age"])
        ax.set_title(f"fiche qui répond à {habitude} — {perimetre}")
        ax.set_ylabel("suppressions pour 10 000 avis")
        ax.legend()
fig.suptitle("Avis en ligne le 11 août : suppressions du 12 au 24 août, selon la réponse et l'âge")
enregistrer(fig, "7_reponse_base_complete")
