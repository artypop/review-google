#!/usr/bin/env python3
"""Gain d'avis de la sollicitation : les 84 fiches les plus touchées et les autres.

    PYTHONPATH=".venv/Lib/site-packages;outils" <python uv> etudes-ponctuelles/2026-10-09-gain-sollicitation/calcul.py

Question de Romain (réunion du 2026-10-08), reprise par Matthieu le 2026-10-09 :
  1. Hors les fiches les plus touchées : la sollicitation fait-elle gagner des avis ? À chiffrer.
  2. Sur les fiches les plus touchées : sont-elles perdantes ?

------------------------------------------------------------------------------
LE BILAN D'UNE FICHE, SUR LA SEMAINE DU 11 AU 17 AOÛT 2026 (avis 4-5 étoiles)
------------------------------------------------------------------------------
  attendus            ce que la fiche reçoit d'habitude en 7 jours : avis 4-5 étoiles des
                      365 jours avant le 11 août, ramenés à 7 jours
  publiés             avis publiés du 11 au 17 août
  nouveaux supprimés  parmi eux, disparus au plus tard 7 jours après leur publication
  gardés              publiés - nouveaux supprimés
  anciens disparus    avis publiés avant le 11 août dont la disparition est notée du 11
                      au 17 août (même semaine). Compté à part, jamais mêlé aux nouveaux.
  solde               gardés - anciens disparus : la fiche a-t-elle plus ou moins d'avis
                      en ligne qu'avant la semaine ?
  surplus             publiés - attendus : les avis en plus du rythme habituel, ce que la
                      sollicitation a apporté
  gain net            surplus - nouveaux supprimés - anciens disparus : ce qui reste de la
                      sollicitation une fois toutes les pertes de la semaine retirées
Suppression = disparition notée (`deleted_detected_at`), doublons déjà retirés de la base.
Fiches relevées jusqu'au 24 août.

------------------------------------------------------------------------------
LES GROUPES
------------------------------------------------------------------------------
  84 fiches    celles de l'étude du 2026-10-08 (1 % des fiches qui ont perdu le plus d'avis
               de tous âges du 11 au 24 août, six enseignes non comprises)
  chaînes      les quatre chaînes antiparasitaires (les deux salles espagnoles n'ont aucun
               avis publié après le 5 août ; elles sont avec les chaînes pour les anciens
               avis disparus)
  autres       toutes les autres fiches, découpées selon l'intensité de la semaine :
               publiés / attendus

Sorties : livrables/restitution_finale_v2/gain_sollicitation/
  bilan_groupes.csv, bilan_par_intensite.csv, bilan_fiches.csv (une ligne par fiche)
  bilan_gain_sollicitation.png
"""
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "outils"))
from local import connexion  # noqa: E402

pd.set_option("display.width", 220)
SORTIE = RACINE / "livrables" / "restitution_finale_v2" / "gain_sollicitation"
LISTE_84 = RACINE / "etudes-ponctuelles" / "2026-10-08-bilan-84-fiches" / "sorties" / "bilan_84_fiches.csv"
DEBUT, FIN, DERNIER_RELEVE = "2026-08-11", "2026-08-17", "2026-08-24"
JOURS, HORIZON_J = 7, 7

CHAINES_ANTIPARASITAIRES = ("ecoshield pest solutions", "insight pest solutions",
                            "pointe pest control", "bulwark exterminating")
CID_SALLES_ESPAGNOLES = ("3163466139043001754", "10346942689164695031")
CLASSES = [(-np.inf, 0, "aucun avis publié"), (0, 1, "rythme habituel ou moins (≤ ×1)"),
           (1, 2, "de ×1 à ×2"), (2, 4, "de ×2 à ×4"), (4, np.inf, "plus de ×4")]

# Palette de référence du skill dataviz.
BLEU, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
ENCRE, ENCRE_2, GRILLE, FOND = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"

SQL = f"""
WITH fin AS (SELECT cid, max(CAST(last_seen_at AS DATE)) AS fs
             FROM reviews_doublons_cleaned_all GROUP BY cid),
a AS (
  SELECT r.cid, CAST(r.created_at AS DATE) AS publie, CAST(r.deleted_detected_at AS DATE) AS disparu
  FROM reviews_doublons_cleaned_all r JOIN fin f USING (cid)
  WHERE r.star >= 4 AND f.fs >= DATE '{DERNIER_RELEVE}'
)
SELECT a.cid, b.name, if(b.country = 'US', 'US', 'Europe') AS region, b.industry,
       coalesce({{chaines}}, FALSE) OR a.cid IN ({{salles}}) AS enseigne,
       count(*) FILTER (publie BETWEEN DATE '{DEBUT}' - INTERVAL 365 DAY AND DATE '{DEBUT}' - INTERVAL 1 DAY)
         * {JOURS} / 365.0 AS attendus,
       count(*) FILTER (publie BETWEEN DATE '{DEBUT}' AND DATE '{FIN}') AS publies,
       count(*) FILTER (publie BETWEEN DATE '{DEBUT}' AND DATE '{FIN}'
                        AND date_diff('day', publie, disparu) <= {HORIZON_J}) AS nouveaux_supprimes,
       count(*) FILTER (publie < DATE '{DEBUT}' AND disparu BETWEEN DATE '{DEBUT}' AND DATE '{FIN}')
         AS anciens_disparus
FROM a JOIN businesses b ON b.cid = a.cid
GROUP BY ALL
"""


def bilan(d: pd.DataFrame) -> dict:
    s = {k: d[k].sum() for k in ["attendus", "publies", "nouveaux_supprimes", "anciens_disparus"]}
    gardes = s["publies"] - s["nouveaux_supprimes"]
    surplus = s["publies"] - s["attendus"]
    gain = surplus - s["nouveaux_supprimes"] - s["anciens_disparus"]
    return {"fiches": len(d), "avis_attendus": round(s["attendus"]), "avis_publies": int(s["publies"]),
            "nouveaux_supprimes": int(s["nouveaux_supprimes"]), "gardes": int(gardes),
            "anciens_disparus": int(s["anciens_disparus"]), "solde": int(gardes - s["anciens_disparus"]),
            "surplus": round(surplus), "gain_net": round(gain),
            "nouveaux_supprimes_pour_100_publies": round(100 * s["nouveaux_supprimes"] / s["publies"], 1)
            if s["publies"] else np.nan,
            "pertes_pour_100_publies": round(100 * (s["nouveaux_supprimes"] + s["anciens_disparus"])
                                             / s["publies"], 1) if s["publies"] else np.nan,
            "gain_net_pour_100_surplus": round(100 * gain / surplus, 1) if surplus > 0 else np.nan,
            "fiches_solde_negatif": int((d["solde"] < 0).sum()),
            "fiches_gain_net_negatif": int(((d["gain_net"] < 0) & (d["surplus"] > 0)).sum()),
            "fiches_avec_surplus": int((d["surplus"] > 0).sum())}


def figure(groupes: pd.DataFrame, chemin: Path) -> None:
    """Pour 100 avis publiés : gardés, nouveaux supprimés, anciens disparus. Barres horizontales."""
    g = groupes[groupes["avis_publies"] > 0].iloc[::-1].reset_index(drop=True)
    gardes = 100 * g["gardes"] / g["avis_publies"]
    nouv = 100 * g["nouveaux_supprimes"] / g["avis_publies"]
    anc = 100 * g["anciens_disparus"] / g["avis_publies"]
    h = 0.55 * len(g) + 2.3
    fig, ax = plt.subplots(figsize=(9.5, h), dpi=150)
    fig.patch.set_facecolor(FOND)
    ax.set_facecolor(FOND)
    y = np.arange(len(g))
    ax.barh(y, gardes, color=BLEU, height=0.55, edgecolor=FOND, linewidth=1.5, label="nouveaux avis gardés")
    ax.barh(y, -nouv, color=ORANGE, height=0.55, edgecolor=FOND, linewidth=1.5,
            label="nouveaux avis supprimés (7 jours)")
    ax.barh(y, -anc, left=-nouv, color=AQUA, height=0.55, edgecolor=FOND, linewidth=1.5,
            label="anciens avis disparus la même semaine")
    for i in y:
        ax.text(gardes[i] + 1.5, i, f"{gardes[i]:.0f}", va="center", fontsize=8, color=ENCRE)
        perte = nouv[i] + anc[i]
        ax.text(-perte - 1.5, i, f"−{perte:.0f}", va="center", ha="right", fontsize=8, color=ENCRE)
        solde = gardes[i] - anc[i]
        ax.text(138, i, f"{solde:+.0f}".replace("-", "−"), va="center", ha="right", fontsize=8.5,
                color=ENCRE, fontweight="bold")
    ax.text(138, len(g) - 0.35, "solde", ha="right", va="bottom", fontsize=8, color=ENCRE_2)
    ax.axvline(0, color=ENCRE_2, lw=1)
    ax.set_yticks(y)
    ax.set_yticklabels([f"{r['groupe']}\n({r['fiches']} fiches, {r['avis_publies']} avis publiés)"
                        for _, r in g.iterrows()], fontsize=8, color=ENCRE)
    borne = max(80, float((nouv + anc).max()) + 15)
    ax.set_xlim(-borne, 140)
    ax.set_xticks([t for t in [-150, -100, -50, 0, 50, 100] if t >= -borne])
    ax.set_xticklabels([f"{abs(t)}" for t in ax.get_xticks()])
    ax.grid(axis="x", color=GRILLE, lw=0.8, zorder=0)
    ax.set_axisbelow(True)
    ax.tick_params(colors=ENCRE_2, labelsize=8, length=0)
    for cote in ["top", "right", "left"]:
        ax.spines[cote].set_visible(False)
    ax.spines["bottom"].set_color(GRILLE)
    ax.set_xlabel("pour 100 avis 4-5 étoiles publiés dans la semaine", color=ENCRE_2, fontsize=8)
    fig.text(0.01, 1 - 0.12 / h, "Ce que les fiches gardent et perdent, pour 100 nouveaux avis publiés",
             va="top", fontsize=11.5, color=ENCRE)
    fig.legend(loc="upper left", bbox_to_anchor=(0.005, 1 - 0.45 / h), frameon=False, fontsize=8,
               labelcolor=ENCRE, ncol=3, handlelength=1.2)
    fig.text(0.01, 0.08 / h,
             "Données : base des avis (doublons retirés), avis 4-5 étoiles, fiches relevées jusqu'au 24 août 2026. "
             "Nouveaux avis : publiés du 11 au 17 août, supprimés s'ils ont\ndisparu dans les 7 jours. "
             "Anciens avis : publiés avant le 11 août, disparus du 11 au 17 août. Solde = gardés − anciens disparus. "
             "Intensité = avis publiés / rythme habituel\n(avis 4-5 étoiles des 365 jours précédents, ramenés à "
             "7 jours). 84 fiches : celles de l'étude du 8 octobre.",
             fontsize=6.8, color=ENCRE_2, va="bottom")
    fig.subplots_adjust(left=0.33, right=0.97, top=1 - 0.85 / h, bottom=1.0 / h)
    fig.savefig(chemin, facecolor=FOND)
    plt.close(fig)


def main() -> None:
    con = connexion("6GB")
    chaines = " OR ".join(f"lower(b.name) LIKE '{n}%'" for n in CHAINES_ANTIPARASITAIRES)
    salles = ", ".join(f"'{c}'" for c in CID_SALLES_ESPAGNOLES)
    d = con.execute(SQL.format(chaines=chaines, salles=salles)).df()
    if d["cid"].duplicated().any():
        raise SystemExit("fiche en double")
    top = pd.read_csv(LISTE_84, dtype={"cid": str})["cid"]
    d["top_84"] = d["cid"].isin(top)
    print(f"{len(d)} fiches relevées jusqu'au {DERNIER_RELEVE} ; 84 fiches retrouvées : {int(d['top_84'].sum())}")
    if d.loc[d["top_84"], "enseigne"].any():
        raise SystemExit("une enseigne parmi les 84 fiches")

    d["attendus"] = d["attendus"].clip(lower=JOURS / 365)  # plancher : 1 avis par an
    d["gardes"] = d["publies"] - d["nouveaux_supprimes"]
    d["solde"] = d["gardes"] - d["anciens_disparus"]
    d["surplus"] = d["publies"] - d["attendus"]
    d["gain_net"] = d["surplus"] - d["nouveaux_supprimes"] - d["anciens_disparus"]
    d["intensite"] = d["publies"] / d["attendus"]
    d["classe"] = pd.cut(d["intensite"], [c[0] for c in CLASSES] + [np.inf],
                         labels=[c[2] for c in CLASSES], right=True).astype(str)
    d.loc[d["publies"] == 0, "classe"] = "aucun avis publié"
    d["groupe"] = np.where(d["top_84"], "84 fiches", np.where(d["enseigne"], "chaînes", "autres"))

    lignes = [{"groupe": "Autres fiches", **bilan(d[d["groupe"] == "autres"])},
              {"groupe": "84 fiches les plus touchées", **bilan(d[d["groupe"] == "84 fiches"])},
              {"groupe": "Chaînes antiparasitaires et salles espagnoles", **bilan(d[d["groupe"] == "chaînes"])}]
    groupes = pd.DataFrame(lignes)
    intens = []
    for _, _, nom in CLASSES:
        for gr, lib in [("autres", "Autres fiches"), ("84 fiches", "84 fiches")]:
            x = d[(d["groupe"] == gr) & (d["classe"] == nom)]
            if len(x):
                intens.append({"groupe": lib, "intensite": nom, **bilan(x)})
    intens = pd.DataFrame(intens)

    print("\n== Groupes ==\n" + groupes.T.to_string())
    print("\n== Par intensité de la semaine ==\n" + intens.to_string(index=False))

    SORTIE.mkdir(parents=True, exist_ok=True)
    groupes.to_csv(SORTIE / "bilan_groupes.csv", index=False)
    intens.to_csv(SORTIE / "bilan_par_intensite.csv", index=False)
    d.drop(columns=["top_84"]).sort_values(["groupe", "solde"]).to_csv(SORTIE / "bilan_fiches.csv", index=False)

    fig_lignes = [groupes.iloc[1].to_dict() | {"groupe": "84 fiches les plus touchées"},
                  groupes.iloc[2].to_dict() | {"groupe": "Chaînes antiparasitaires"}]
    for _, r in intens[intens["groupe"] == "Autres fiches"].iterrows():
        if r["intensite"] != "aucun avis publié":
            fig_lignes.append(r.to_dict() | {"groupe": f"Autres fiches, {r['intensite']}"})
    figure(pd.DataFrame(fig_lignes)[["groupe", "fiches", "avis_publies", "gardes", "nouveaux_supprimes",
                                     "anciens_disparus"]], SORTIE / "bilan_gain_sollicitation.png")
    print(f"\nécrit dans {SORTIE}")


if __name__ == "__main__":
    main()
