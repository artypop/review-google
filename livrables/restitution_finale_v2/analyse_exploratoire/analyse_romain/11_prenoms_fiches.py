"""11. Part de prénoms, vélocité et suppressions : séparer les fiches touchées en masse.

    uv run python consolidation/11_prenoms_fiches.py

Suite du point 10 et du mail d'Axel du 2026-10-07. Base complète nettoyée ;
marquage « l'avis cite un nom » d'Axel (`reviews_name_enriched`). Fiches retenues :
au moins 20 avis 4 et 5 étoiles avec texte, comme chez Axel.

  Étape A  qui est touché en masse (plus de 10 suppressions en 14 jours) ?
           Une ligne par fiche. Effet de la part de prénoms sans puis avec la
           vélocité, à secteur, région, taille, nombre d'avis, habitude de
           réponse et part d'avis 1-2 étoiles égaux. Contrôle : seuil relatif
           (au moins 5 suppressions et plus de 5 % des avis récents).
  Étape B  chez les fiches ordinaires (0 à 10 suppressions), suppressions
           réelles face aux suppressions attendues d'après l'âge de chaque avis.
  Étape C  dans les fiches touchées en masse, un avis avec nom face à un avis
           sans nom de la même fiche et du même âge.

Chaque étape sur trois périmètres : toutes les fiches, sans les 4 chaînes
antiparasitaires, sans les chaînes ni les 2 salles espagnoles.

Produit :
  sorties/11_fiches.csv              une ligne par fiche, colonnes de sql/11_fiches.sql
  sorties/11a_effets.csv             étape A : effets, fourchette à 95 %
  sorties/11a_taux.csv               étape A : part des fiches touchées en masse par tranche
  sorties/11a_croise.csv             étape A : part de prénoms × vélocité
  sorties/11b_reel_attendu.csv       étape B : réel / attendu par tranche
  sorties/11b_effets.csv             étape B : effets à caractéristiques égales
  sorties/11c_effets.csv             étape C : avis avec nom face à sans nom
  sorties/figures/11a_masse.png, 11b_ordinaires.png, 11c_avis_masse.png
"""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from matplotlib.ticker import FuncFormatter, NullFormatter

from commun import ENCRE, ENCRE_SECONDAIRE, FIGURES, ecrire_csv, figure, requete

PERIMETRES = {"toutes les fiches": lambda d: d,
              "sans les chaînes": lambda d: d[d["groupe"] != "chaines_antiparasitaires"],
              "sans les chaînes ni les salles": lambda d: d[d["groupe"] == "autres"]}
COULEURS = dict(zip(PERIMETRES, ["#2a78d6", "#1baf7a", "#eb6834"]))
NOMS = ["moins de 10 %", "10 à 25 %", "25 à 50 %", "50 % et plus"]
# Tranches de vélocité pour les comptages directs. Dans les modèles, la vélocité
# entre en continu, effet lu pour un doublement : sous 3 avis par mois, une seule
# fiche est touchée en masse, une tranche de référence serait presque vide.
VITESSES = ["moins de 3", "3 à 7", "7 à 15", "15 et plus"]
VITESSE = "vitesse : 2 fois plus d'avis par mois"
AGES = ["pendant", "m30j", "30_90j", "90_365j", "1_3ans", "p3ans"]
# Une case qui compte moins de 3 résultats positifs rejoint la référence : son
# effet ne se mesure pas (sinon le modèle ne converge pas).
MIN_POSITIFS = 3


def fois(v):
    return f"×{v:.2f}".replace(".", ",")


# ---------------------------------------------------------------------------
# Les fiches
# ---------------------------------------------------------------------------
f0 = requete("11_fiches")
ecrire_csv(f0, "11_fiches")
f = f0[f0["avis_45_texte"] >= 20].copy()
f["noms"] = pd.cut(f["part_noms"], [-1, 0.10, 0.25, 0.50, 2], labels=NOMS, right=False).astype(str)
f["vitesse"] = pd.cut(f["velocite_mois"], [-1, 3, 7, 15, 1e9], labels=VITESSES, right=False).astype(str)
f["masse"] = (f["categorie"] == "11 et plus").astype(int)
f["masse_relatif"] = ((f["supp_recents"] >= 5)
                      & (f["supp_recents"] > 0.05 * f["avis_recents"])).astype(int)
f["log10_avis"] = np.log10(f["avis"])
f["log2_velocite"] = np.log2(f["velocite_mois"] + 0.1)
f["part_1_2_10pts"] = 10 * f["part_1_2_etoiles"]
print(f"  {len(f)} fiches à 20 avis 4-5 étoiles avec texte ou plus, {f['masse'].sum()} touchées en masse")

COMMUNES = {"secteur": "automotive", "region": "Europe", "taille": "mono", "habitude": "75 % ou moins"}


def colonnes(d, y, caracs):
    """Variables 0/1 d'un modèle ; une case à moins de MIN_POSITIFS rejoint la référence."""
    X = pd.DataFrame(index=d.index)
    for carac, reference in caracs.items():
        for case in sorted(set(d[carac]) - {reference}):
            if d.loc[d[carac] == case, y].sum() >= MIN_POSITIFS:
                X[f"{carac} : {case}"] = (d[carac] == case).astype(float)
    return X


def effets(m, prefixes, **cles):
    marges = m.conf_int()
    return [{**cles, "colonne": c, "effet": round(float(np.exp(m.params[c])), 2),
             "fourchette_basse": round(float(np.exp(marges.loc[c, 0])), 2),
             "fourchette_haute": round(float(np.exp(marges.loc[c, 1])), 2)}
            for c in m.params.index if c.startswith(prefixes)]


# ---------------------------------------------------------------------------
# Étape A : qui est touché en masse ?
# ---------------------------------------------------------------------------
taux_a, effets_a = [], []
for perimetre, choisir in PERIMETRES.items():
    d = choisir(f)
    for carac, cases in [("noms", NOMS), ("vitesse", VITESSES)]:
        for case in cases:
            c = d[d[carac] == case]
            taux_a.append({"perimetre": perimetre, "caracteristique": carac, "tranche": case,
                           "fiches": len(c), "touchees_en_masse": int(c["masse"].sum()),
                           "pct": round(100 * c["masse"].mean(), 1),
                           "touchees_seuil_relatif": int(c["masse_relatif"].sum())})
    for y, avec_vitesse in [("masse", False), ("masse", True), ("masse_relatif", True)]:
        X = colonnes(d, y, {"noms": "moins de 10 %", **COMMUNES})
        X["log10_avis"] = d["log10_avis"]
        if avec_vitesse:
            X[VITESSE] = d["log2_velocite"]
        X["part_1_2_etoiles : +10 points"] = d["part_1_2_10pts"]
        m = sm.GLM(d[y], sm.add_constant(X), family=sm.families.Binomial()).fit(cov_type="HC1")
        modele = ("seuil relatif" if y == "masse_relatif"
                  else "avec la vélocité" if avec_vitesse else "sans la vélocité")
        print(f"  A {perimetre}, {modele} : {len(d)} fiches, {d[y].sum()} touchées, converge {m.converged}")
        effets_a += effets(m, ("noms", "vitesse"), perimetre=perimetre, modele=modele,
                           fiches=len(d), touchees=int(d[y].sum()))
# Croisement part de prénoms × vélocité : fiches et fiches touchées en masse.
croise = (f.groupby(["groupe", "noms", "vitesse"])
          .agg(fiches=("cid", "size"), touchees_en_masse=("masse", "sum"),
               velocite_mediane=("velocite_mois", "median")).reset_index())
croise = pd.concat([
    croise.assign(perimetre="toutes les fiches"),
    croise[croise["groupe"] == "autres"].assign(perimetre="sans les chaînes ni les salles")])
croise = (croise.groupby(["perimetre", "noms", "vitesse"])
          .agg(fiches=("fiches", "sum"), touchees_en_masse=("touchees_en_masse", "sum")).reset_index())
croise["pct"] = (100 * croise["touchees_en_masse"] / croise["fiches"]).round(1)
ecrire_csv(croise, "11a_croise")
taux_a, effets_a = pd.DataFrame(taux_a), pd.DataFrame(effets_a)
ecrire_csv(taux_a, "11a_taux")
ecrire_csv(effets_a, "11a_effets")

# ---------------------------------------------------------------------------
# Étape B : fiches ordinaires, suppressions réelles face aux attendues.
# Le risque de chaque tranche d'âge est celui des fiches ordinaires du périmètre.
# ---------------------------------------------------------------------------
reel_b, effets_b = [], []
for perimetre, choisir in PERIMETRES.items():
    d = choisir(f)
    d = d[d["masse"] == 0].copy()
    risque = {a: d[f"supp_{a}"].sum() / d[f"avis_{a}"].sum() for a in AGES}
    d["attendu"] = sum(d[f"avis_{a}"] * risque[a] for a in AGES)
    for carac, cases in [("noms", NOMS), ("vitesse", VITESSES)]:
        for case in cases:
            c = d[d[carac] == case]
            reel_b.append({"perimetre": perimetre, "caracteristique": carac, "tranche": case,
                           "fiches": len(c), "suppressions": int(c["suppressions"].sum()),
                           "attendues": round(c["attendu"].sum(), 1),
                           "reel_sur_attendu": round(c["suppressions"].sum() / c["attendu"].sum(), 2)})
    d = d[d["attendu"] > 0]
    for avec_vitesse in [False, True]:
        X = colonnes(d, "suppressions", {"noms": "moins de 10 %", "secteur": "automotive",
                                         "region": "Europe", "taille": "mono"})
        if avec_vitesse:
            X[VITESSE] = d["log2_velocite"]
        m = sm.GLM(d["suppressions"], sm.add_constant(X), family=sm.families.Poisson(),
                   offset=np.log(d["attendu"])).fit(cov_type="HC1")
        modele = "avec la vélocité" if avec_vitesse else "sans la vélocité"
        print(f"  B {perimetre}, {modele} : {len(d)} fiches, {d['suppressions'].sum()} suppressions")
        effets_b += effets(m, ("noms", "vitesse"), perimetre=perimetre, modele=modele,
                           fiches=len(d), suppressions=int(d["suppressions"].sum()))
reel_b, effets_b = pd.DataFrame(reel_b), pd.DataFrame(effets_b)
ecrire_csv(reel_b, "11b_reel_attendu")
ecrire_csv(effets_b, "11b_effets")

# ---------------------------------------------------------------------------
# Étape C : dans les fiches touchées en masse, avis avec nom face à sans nom,
# même fiche et même âge. Une variable par fiche et par tranche d'âge.
# ---------------------------------------------------------------------------
a0 = requete("11_avis_masse")
a0["a_un_nom"] = a0["a_un_nom"].astype(bool)
effets_c = []
for perimetre, choisir in PERIMETRES.items():
    a = choisir(a0)
    a = a[a["cid"].isin(f["cid"])]
    brut = a.groupby("a_un_nom")[["avis", "suppressions"]].sum()
    X = pd.get_dummies(a[["cid", "age"]], drop_first=True, dtype=float)
    X["avis avec nom"] = a["a_un_nom"].astype(float)
    m = sm.GLM(a["suppressions"], sm.add_constant(X), family=sm.families.Poisson(),
               offset=np.log(a["avis"])).fit(cov_type="cluster",
                                             cov_kwds={"groups": pd.factorize(a["cid"])[0]})
    marges = m.conf_int()
    effets_c.append({
        "perimetre": perimetre, "fiches": a["cid"].nunique(),
        "avis_avec_nom": int(brut.loc[True, "avis"]), "supprimes_avec_nom": int(brut.loc[True, "suppressions"]),
        "avis_sans_nom": int(brut.loc[False, "avis"]), "supprimes_sans_nom": int(brut.loc[False, "suppressions"]),
        "rapport_brut": round((brut.loc[True, "suppressions"] / brut.loc[True, "avis"])
                              / (brut.loc[False, "suppressions"] / brut.loc[False, "avis"]), 2),
        "effet_meme_fiche_meme_age": round(float(np.exp(m.params["avis avec nom"])), 2),
        "fourchette_basse": round(float(np.exp(marges.loc["avis avec nom", 0])), 2),
        "fourchette_haute": round(float(np.exp(marges.loc["avis avec nom", 1])), 2)})
effets_c = pd.DataFrame(effets_c)
ecrire_csv(effets_c, "11c_effets")
print(effets_c.to_string(index=False))


# ---------------------------------------------------------------------------
# Graphiques
# ---------------------------------------------------------------------------
def points(ax, e, cases, prefixe, reference):
    """Effets d'une caractéristique, un point par périmètre, référence sur ×1."""
    for i, (perimetre, couleur) in enumerate(COULEURS.items()):
        x = np.arange(len(cases)) + (i - 1) * 0.22
        ax.scatter(x[0], 1, s=30, facecolor="#fcfcfb", edgecolor=ENCRE_SECONDAIRE, zorder=3)
        for xi, case in zip(x[1:], cases[1:]):
            r = e[(e["perimetre"] == perimetre) & (e["colonne"] == f"{prefixe} : {case}")]
            if r.empty:
                continue
            r = r.iloc[0]
            ax.errorbar(xi, r["effet"], yerr=[[r["effet"] - r["fourchette_basse"]],
                                              [r["fourchette_haute"] - r["effet"]]],
                        fmt="o", color=couleur, capsize=3, label=perimetre if xi == x[1] else None)
            ax.text(xi + 0.04, r["effet"], fois(r["effet"]), fontsize=7, va="center", color=ENCRE)
    ax.axhline(1, color=ENCRE, linestyle="--", linewidth=1)
    ax.set_yscale("log")
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"×{v:g}".replace(".", ",")))
    ax.yaxis.set_minor_formatter(NullFormatter())
    ax.set_xticks(range(len(cases)), [f"{c}\n(référence)" if c == reference else c for c in cases],
                  fontsize=8.5)
    ax.grid(axis="x", visible=False)


def enregistrer(fig, nom, titre, sous_titre):
    fig.suptitle(titre, x=0.02, ha="left", fontsize=12, color=ENCRE)
    fig.text(0.02, 0.92, sous_titre, ha="left", va="top", fontsize=8.5, color=ENCRE_SECONDAIRE)
    fig.tight_layout(rect=(0, 0, 1, 0.84))
    FIGURES.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURES / f"{nom}.png", dpi=150)
    plt.close(fig)
    print(f"  sorties/figures/{nom}.png")


fig, axes = figure(1, 3, largeur=16, hauteur=5.6)
for ax, modele in [(axes[0][0], "sans la vélocité"), (axes[0][1], "avec la vélocité")]:
    points(ax, effets_a[effets_a["modele"] == modele], NOMS, "noms", NOMS[0])
    ax.set_title(f"Part de prénoms, {modele}", loc="left", fontsize=10.5)
ax = axes[0][2]
for i, (perimetre, couleur) in enumerate(COULEURS.items()):
    r = taux_a[(taux_a["perimetre"] == perimetre) & (taux_a["caracteristique"] == "vitesse")]
    r = r.set_index("tranche").loc[VITESSES]
    barres = ax.bar(np.arange(len(VITESSES)) + (i - 1) * 0.27, r["pct"], width=0.25, color=couleur)
    ax.bar_label(barres, labels=[f"{n}" for n in r["touchees_en_masse"]], fontsize=7, padding=2)
ax.set_xticks(range(len(VITESSES)), VITESSES, fontsize=8.5)
ax.set_ylabel("% des fiches touchées en masse")
ax.set_title("Vélocité, avis par mois (au-dessus : fiches touchées)", loc="left", fontsize=10.5)
ax.grid(axis="x", visible=False)
axes[0][0].set_ylabel("chances d'être touchée en masse, face à la référence")
axes[0][0].legend(fontsize=8, loc="upper left")
enregistrer(fig, "11a_masse",
            "Étape A : quelles fiches sont touchées en masse (plus de 10 suppressions en 14 jours) ?",
            f"{len(f)} fiches à 20 avis 4-5 étoiles avec texte ou plus. Secteur, région, taille, nombre "
            "d'avis, habitude de réponse et part d'avis 1-2 étoiles tenus égaux. Trait : fourchette à 95 %.")

fig, axes = figure(1, 2, largeur=14, hauteur=5.6)
for ax, carac, cases, titre in [(axes[0][0], "noms", NOMS, "Part de prénoms"),
                                (axes[0][1], "vitesse", VITESSES, "Vélocité, avis par mois")]:
    for i, (perimetre, couleur) in enumerate(COULEURS.items()):
        r = reel_b[(reel_b["perimetre"] == perimetre) & (reel_b["caracteristique"] == carac)]
        r = r.set_index("tranche").loc[cases]
        barres = ax.bar(np.arange(len(cases)) + (i - 1) * 0.27, r["reel_sur_attendu"], width=0.25,
                        color=couleur, label=perimetre)
        ax.bar_label(barres, labels=[f"{v:.2f}".replace(".", ",") for v in r["reel_sur_attendu"]],
                     fontsize=7, padding=2)
    ax.axhline(1, color=ENCRE, linestyle="--", linewidth=1)
    ax.set_xticks(range(len(cases)), cases, fontsize=8.5)
    ax.set_title(titre, loc="left", fontsize=10.5)
    ax.grid(axis="x", visible=False)
axes[0][0].set_ylabel("suppressions réelles / attendues d'après l'âge des avis")
axes[0][0].legend(fontsize=8, loc="upper left")
enregistrer(fig, "11b_ordinaires",
            "Étape B : chez les fiches ordinaires (0 à 10 suppressions), perdent-elles plus que l'âge "
            "de leurs avis ne le laisse attendre ?",
            "1 = la fiche perd ce que l'âge de ses avis laisse attendre. Attendu : chaque avis reçoit le risque "
            "moyen de sa tranche d'âge chez les fiches ordinaires du périmètre.")

fig, axes = figure(1, 1, largeur=9, hauteur=5)
ax = axes[0][0]
for i, r in effets_c.reset_index(drop=True).iterrows():
    ax.errorbar(i, r["effet_meme_fiche_meme_age"],
                yerr=[[r["effet_meme_fiche_meme_age"] - r["fourchette_basse"]],
                      [r["fourchette_haute"] - r["effet_meme_fiche_meme_age"]]],
                fmt="o", color=COULEURS[r["perimetre"]], capsize=4)
    ax.text(i + 0.06, r["effet_meme_fiche_meme_age"],
            f"{fois(r['effet_meme_fiche_meme_age'])} ({r['fiches']} fiches)", fontsize=8, va="center")
ax.axhline(1, color=ENCRE, linestyle="--", linewidth=1)
ax.set_xticks(range(len(effets_c)), effets_c["perimetre"], fontsize=8.5)
ax.set_xlim(-0.5, len(effets_c) - 0.2)
ax.set_ylabel("avis avec nom face à sans nom")
ax.grid(axis="x", visible=False)
enregistrer(fig, "11c_avis_masse",
            "Étape C : dans les fiches touchées en masse, l'avis qui cite un nom part-il plus ?",
            "Avis 4-5 étoiles avec texte. Comparaison dans la même fiche et la même tranche d'âge. "
            "Trait : fourchette à 95 %.")

print(taux_a.to_string(index=False))
print(effets_a.to_string(index=False))
print(reel_b.to_string(index=False))
print(effets_b.to_string(index=False))
