#!/usr/bin/env python3
"""Évolution du solde net d'avis du 7 au 17 août : fiches « prénoms et vitesse élevés » et autres.

    PYTHONPATH=".venv/Lib/site-packages;outils" <python uv> etudes-ponctuelles/2026-10-09-gain-sollicitation/solde_par_jour.py

Demande de Matthieu du 2026-10-09, pour répondre à Romain : la sollicitation d'avis
rapporte-t-elle ? Choix validés par Matthieu :

  commerces    au moins 15 avis 4-5 étoiles publiés du 7 au 17 août dans 03C
               (data/local/03C_7_17_aout_prenom.parquet), fiche relevée jusqu'au 24 août,
               part de prénoms mesurable (au moins 20 avis annotés par Axel avant le 7 août)
  groupe « prénoms et vitesse élevés »
               part de prénoms >= 50 % (avis 4-5 étoiles avec texte publiés avant le 7 août,
               annotation d'Axel) ET vitesse dans le quart le plus rapide des commerces
               retenus (avis reçus par mois, toutes notes, du 7 août 2025 au 6 août 2026 :
               définitions d'Axel, comme 2026-10-06-velocite-prenom)
  autres       tous les autres commerces retenus
  solde net    chaque jour : avis 4-5 étoiles publiés ce jour-là (03C) moins avis 4-5 étoiles
               dont la disparition est notée ce jour-là (nouveaux de 03C ou anciens, de la
               base), cumulé depuis le 7 août, en % des avis 4-5 étoiles en ligne au départ
               (publiés avant le 7 août, pas disparus avant)
  période      du 7 au 17 août. Le suivi commence le 11 août : du 7 au 10, on voit les
               publications (les avis encore là le 11) mais aucune disparition ; les
               disparitions des jours précédents sont notées en bloc le 12. Zone grisée.

Les six enseignes sont gardées (aucun filtre demandé) ; leur présence est imprimée.

Sorties : livrables/restitution_finale_v2/gain_sollicitation/
  solde_net_par_jour_prenoms_vitesse.png, solde_net_par_jour_autres.png
  solde_net_par_jour.csv     une ligne par groupe et par jour
  solde_net_commerces.csv    une ligne par commerce : groupe, indicateurs, bilan
"""
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.ticker import FixedLocator, MultipleLocator  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "outils"))
from local import connexion  # noqa: E402

pd.set_option("display.width", 220)
CORPUS = RACINE / "data" / "local" / "03C_7_17_aout_prenom.parquet"
AXEL = RACINE / "data" / "local" / "axel_file" / "reviews_name_enriched.parquet"
SORTIE = RACINE / "livrables" / "restitution_finale_v2" / "gain_sollicitation"
DEBUT, FIN, PREMIER_RELEVE, DERNIER_RELEVE = "2026-08-07", "2026-08-17", "2026-08-11", "2026-08-24"
MIN_AVIS_03C, MIN_ANNOTES, SEUIL_PRENOM, QUANTILE_VITESSE = 15, 20, 0.50, 0.75
GROUPES = {"prenoms_vitesse": "Prénoms ≥ 50 % et vitesse dans le quart haut", "autres": "Autres commerces"}

CHAINES_ANTIPARASITAIRES = ("ecoshield pest solutions", "insight pest solutions",
                            "pointe pest control", "bulwark exterminating")
CID_SALLES_ESPAGNOLES = ("3163466139043001754", "10346942689164695031")

# Palette de référence du skill dataviz.
BLEU = "#2a78d6"
ENCRE, ENCRE_2, GRILLE, FOND, ZONE = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb", "#efeeea"

SQL_COMMERCES = f"""
WITH fin AS (SELECT cid, max(CAST(last_seen_at AS DATE)) AS fs
             FROM reviews_doublons_cleaned_all GROUP BY cid),
c AS (SELECT cid, count(*) AS avis_03c FROM '{CORPUS.as_posix()}'
      WHERE star >= 4 GROUP BY cid),
prenom AS (SELECT cid, count(*) AS avis_annotes, avg(has_name::INT) AS part_prenom
           FROM '{AXEL.as_posix()}' WHERE CAST(created_at AS DATE) < DATE '{DEBUT}' GROUP BY cid),
vitesse AS (SELECT cid, count(*) / 12.0 AS avis_par_mois FROM reviews_doublons_cleaned_all
            WHERE CAST(created_at AS DATE) BETWEEN DATE '2025-08-07' AND DATE '2026-08-06'
            GROUP BY cid)
SELECT c.cid, b.name, if(b.country = 'US', 'US', 'Europe') AS region, b.industry, b.bucket,
       coalesce({{chaines}}, FALSE) OR c.cid IN ({{salles}}) AS enseigne,
       c.avis_03c, coalesce(p.avis_annotes, 0) AS avis_annotes, p.part_prenom,
       coalesce(v.avis_par_mois, 0) AS avis_par_mois
FROM c JOIN businesses b ON b.cid = c.cid JOIN fin f ON f.cid = c.cid
LEFT JOIN prenom p ON p.cid = c.cid LEFT JOIN vitesse v ON v.cid = c.cid
WHERE f.fs >= DATE '{DERNIER_RELEVE}' AND c.avis_03c >= {MIN_AVIS_03C}
"""

# Mouvements par commerce et par jour, avis 4-5 étoiles. Nouveaux : 03C. Anciens : la base.
SQL_MOUVEMENTS = f"""
WITH nouveaux AS (
  SELECT cid, created_at AS publie, deleted_detected_at AS disparu FROM '{CORPUS.as_posix()}'
  WHERE star >= 4),
anciens AS (
  SELECT cid, CAST(deleted_detected_at AS DATE) AS disparu FROM reviews_doublons_cleaned_all
  WHERE star >= 4 AND CAST(created_at AS DATE) < DATE '{DEBUT}')
SELECT cid, jour, sum(publies) AS publies, sum(nouveaux_disparus) AS nouveaux_disparus,
       sum(anciens_disparus) AS anciens_disparus
FROM (
  SELECT cid, publie AS jour, 1 AS publies, 0 AS nouveaux_disparus, 0 AS anciens_disparus FROM nouveaux
  UNION ALL
  SELECT cid, disparu, 0, 1, 0 FROM nouveaux WHERE disparu IS NOT NULL
  UNION ALL
  SELECT cid, disparu, 0, 0, 1 FROM anciens WHERE disparu IS NOT NULL
)
WHERE cid IN (SELECT cid FROM retenus)
GROUP BY ALL
"""

SQL_STOCK = f"""
SELECT cid, count(*) AS stock_depart FROM reviews_doublons_cleaned_all
WHERE star >= 4 AND CAST(created_at AS DATE) < DATE '{DEBUT}'
  AND (deleted_detected_at IS NULL OR CAST(deleted_detected_at AS DATE) >= DATE '{DEBUT}')
  AND cid IN (SELECT cid FROM retenus)
GROUP BY cid
"""


def commerces(con) -> pd.DataFrame:
    chaines = " OR ".join(f"lower(b.name) LIKE '{n}%'" for n in CHAINES_ANTIPARASITAIRES)
    salles = ", ".join(f"'{c}'" for c in CID_SALLES_ESPAGNOLES)
    f = con.execute(SQL_COMMERCES.format(chaines=chaines, salles=salles)).df()
    print(f"commerces avec au moins {MIN_AVIS_03C} avis 4-5 étoiles dans 03C, relevés jusqu'au "
          f"{DERNIER_RELEVE} : {len(f)}")
    sans = f["avis_annotes"] < MIN_ANNOTES
    print(f"  écartés, moins de {MIN_ANNOTES} avis annotés avant le {DEBUT} (part de prénoms "
          f"non mesurable) : {int(sans.sum())}")
    f = f[~sans].copy()
    seuil_vitesse = f["avis_par_mois"].quantile(QUANTILE_VITESSE)
    f["groupe"] = np.where((f["part_prenom"] >= SEUIL_PRENOM) & (f["avis_par_mois"] >= seuil_vitesse),
                           "prenoms_vitesse", "autres")
    print(f"  retenus : {len(f)} ; seuil de vitesse (quart haut) : {seuil_vitesse:.1f} avis par mois")
    print("  " + f.groupby("groupe").agg(commerces=("cid", "size"), dont_enseignes=("enseigne", "sum"))
          .to_string().replace("\n", "\n  "))
    return f


def series(con, f: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    con.register("retenus", f[["cid"]])
    m = con.execute(SQL_MOUVEMENTS).df()
    stock = con.execute(SQL_STOCK).df()
    jours = pd.date_range(DEBUT, FIN, freq="D")
    m["jour"] = pd.to_datetime(m["jour"])
    m = m[m["jour"].between(jours[0], jours[-1])]
    grille = pd.MultiIndex.from_product([f["cid"], jours], names=["cid", "jour"])
    m = m.groupby(["cid", "jour"])[["publies", "nouveaux_disparus", "anciens_disparus"]].sum()
    m = m.reindex(grille, fill_value=0).reset_index()
    m = m.merge(f[["cid", "groupe"]], on="cid").merge(stock, on="cid", how="left")
    m["stock_depart"] = m["stock_depart"].fillna(0)
    m["net"] = m["publies"] - m["nouveaux_disparus"] - m["anciens_disparus"]
    m = m.sort_values(["cid", "jour"])
    m["solde_cumule"] = m.groupby("cid")["net"].cumsum()
    m["solde_pct"] = 100 * m["solde_cumule"] / m["stock_depart"].replace(0, np.nan)

    lignes = []
    for (g, j), x in m.groupby(["groupe", "jour"]):
        cum = x[["publies", "nouveaux_disparus", "anciens_disparus"]]
        lignes.append({"groupe": g, "jour": j.date(), "commerces": len(x),
                       "stock_depart": int(x["stock_depart"].sum()),
                       "publies_jour": int(cum["publies"].sum()),
                       "nouveaux_disparus_jour": int(cum["nouveaux_disparus"].sum()),
                       "anciens_disparus_jour": int(cum["anciens_disparus"].sum()),
                       "solde_cumule": int(x["solde_cumule"].sum()),
                       "solde_pct_groupe": 100 * x["solde_cumule"].sum() / x["stock_depart"].sum(),
                       "solde_pct_mediane": x["solde_pct"].median(),
                       "solde_pct_q1": x["solde_pct"].quantile(0.25),
                       "solde_pct_q3": x["solde_pct"].quantile(0.75),
                       "commerces_solde_negatif": int((x["solde_cumule"] < 0).sum())})
    return pd.DataFrame(lignes), m


def bilan_commerces(con, f: pd.DataFrame, m: pd.DataFrame) -> pd.DataFrame:
    """Au 17 août, et avec les disparitions des nouveaux avis jusqu'au 24 août (7 jours de suivi)."""
    fin17 = m[m["jour"] == FIN][["cid", "stock_depart", "solde_cumule", "solde_pct"]]
    tot = m.groupby("cid")[["publies", "nouveaux_disparus", "anciens_disparus"]].sum().reset_index()
    tard = con.execute(f"""
        SELECT cid, count(*) AS nouveaux_disparus_apres_17
        FROM '{CORPUS.as_posix()}'
        WHERE star >= 4 AND deleted_detected_at > DATE '{FIN}'
          AND date_diff('day', created_at, deleted_detected_at) <= 7
          AND cid IN (SELECT cid FROM retenus)
        GROUP BY cid""").df()
    b = (f.merge(fin17, on="cid").merge(tot, on="cid").merge(tard, on="cid", how="left"))
    b["nouveaux_disparus_apres_17"] = b["nouveaux_disparus_apres_17"].fillna(0).astype(int)
    b["solde_suivi_complet"] = b["solde_cumule"] - b["nouveaux_disparus_apres_17"]
    b["solde_suivi_complet_pct"] = 100 * b["solde_suivi_complet"] / b["stock_depart"].replace(0, np.nan)
    return b


def figure(j: pd.DataFrame, groupe: str, n: int, ymin: float, ymax: float, chemin: Path) -> None:
    d = j[j["groupe"] == groupe].copy()
    d["jour"] = pd.to_datetime(d["jour"])
    fig, ax = plt.subplots(figsize=(8, 4.6), dpi=150)
    fig.patch.set_facecolor(FOND)
    ax.set_facecolor(FOND)
    ax.axvspan(pd.Timestamp(DEBUT) - pd.Timedelta(hours=12), pd.Timestamp(PREMIER_RELEVE) - pd.Timedelta(hours=12),
               color=ZONE, zorder=0, lw=0)
    ax.text(pd.Timestamp("2026-08-08 12:00"), ymax - 0.04 * (ymax - ymin),
            "avant le suivi :\npublications seules,\npertes non observées", ha="center", va="top",
            fontsize=7, color=ENCRE_2)
    ax.axhline(0, color=ENCRE_2, lw=1, zorder=1)
    ax.fill_between(d["jour"], d["solde_pct_q1"], d["solde_pct_q3"], color=BLEU, alpha=0.15, lw=0,
                    zorder=2, label="la moitié centrale des commerces")
    ax.plot(d["jour"], d["solde_pct_mediane"], color=BLEU, lw=1.2, ls="--", zorder=3,
            label="commerce médian")
    ax.plot(d["jour"], d["solde_pct_groupe"], color=BLEU, lw=2.2, marker="o", ms=4, zorder=4,
            label="ensemble du groupe")
    der = d.iloc[-1]
    ax.annotate(f"{der['solde_pct_groupe']:+.1f} %".replace(".", ",").replace("-", "−"),
                (der["jour"], der["solde_pct_groupe"]), xytext=(6, 0), textcoords="offset points",
                va="center", fontsize=8.5, color=ENCRE, fontweight="bold")
    ax.set_ylim(ymin, ymax)
    ax.set_xlim(pd.Timestamp(DEBUT) - pd.Timedelta(hours=12), pd.Timestamp(FIN) + pd.Timedelta(hours=30))
    ax.xaxis.set_major_locator(FixedLocator(mdates.date2num(pd.date_range(DEBUT, FIN, freq="D"))))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m"))
    ax.yaxis.set_major_locator(MultipleLocator(0.5))
    ax.yaxis.set_major_formatter(plt.FuncFormatter(
        lambda v, _: "0 %" if abs(v) < 1e-9 else f"{v:+.1f} %".replace(".", ",").replace("-", "−")))
    ax.grid(axis="y", color=GRILLE, lw=0.8, zorder=0)
    ax.tick_params(colors=ENCRE_2, labelsize=8, length=0)
    for cote in ["top", "right", "left"]:
        ax.spines[cote].set_visible(False)
    ax.spines["bottom"].set_color(GRILLE)
    ax.set_ylabel("solde net cumulé, en % des avis en ligne au 7 août", color=ENCRE_2, fontsize=8)
    neg = int(der["commerces_solde_negatif"])
    fig.text(0.01, 0.975, f"Solde net d'avis du 7 au 17 août : {GROUPES[groupe].lower()}",
             va="top", fontsize=11, color=ENCRE)
    stock = f"{int(der['stock_depart']):,}".replace(",", " ")
    fig.text(0.01, 0.915, f"{n} commerces, {stock} avis 4-5 étoiles en ligne au départ ; "
             f"{neg} commerces en solde négatif au 17 août",
             va="top", fontsize=8, color=ENCRE_2)
    ax.legend(loc="upper left", bbox_to_anchor=(0.37, 1.0), frameon=False, fontsize=7.5, labelcolor=ENCRE)
    fig.text(0.01, 0.015,
             "Données : corpus 03C (avis 4-5 étoiles publiés du 7 au 17 août 2026) et base des avis pour les anciens avis. "
             f"Commerces avec au moins {MIN_AVIS_03C} avis 4-5 étoiles\ndans 03C, relevés jusqu'au 24 août. "
             "Solde net = avis publiés − avis disparus (nouveaux et anciens), cumulé depuis le 7 août. "
             "Prénoms : avis publiés avant le 7 août (annotation\nd'Axel) ; vitesse : avis par mois sur l'année "
             "précédente ; quart haut = 25 % des commerces retenus les plus rapides. Les disparitions du 7 au 11 août "
             "sont notées le 12.",
             fontsize=6.3, color=ENCRE_2, va="bottom")
    fig.subplots_adjust(left=0.1, right=0.93, top=0.86, bottom=0.2)
    fig.savefig(chemin, facecolor=FOND)
    plt.close(fig)


def main() -> None:
    con = connexion("6GB")
    f = commerces(con)
    j, m = series(con, f)
    b = bilan_commerces(con, f, m)

    print("\n== Par jour ==\n" + j.round(2).to_string(index=False))
    synthese = b.groupby("groupe").agg(
        commerces=("cid", "size"), stock_depart=("stock_depart", "sum"), publies=("publies", "sum"),
        nouveaux_disparus_au_17=("nouveaux_disparus", "sum"), anciens_disparus=("anciens_disparus", "sum"),
        solde_au_17=("solde_cumule", "sum"), nouveaux_disparus_apres_17=("nouveaux_disparus_apres_17", "sum"),
        solde_suivi_complet=("solde_suivi_complet", "sum"),
        commerces_negatifs_au_17=("solde_cumule", lambda s: int((s < 0).sum())),
        commerces_negatifs_suivi_complet=("solde_suivi_complet", lambda s: int((s < 0).sum())))
    synthese["solde_au_17_pct"] = 100 * synthese["solde_au_17"] / synthese["stock_depart"]
    synthese["solde_suivi_complet_pct"] = 100 * synthese["solde_suivi_complet"] / synthese["stock_depart"]
    print("\n== Synthèse ==\n" + synthese.T.round(2).to_string())

    SORTIE.mkdir(parents=True, exist_ok=True)
    j.to_csv(SORTIE / "solde_net_par_jour.csv", index=False)
    b.sort_values(["groupe", "solde_suivi_complet_pct"]).to_csv(SORTIE / "solde_net_commerces.csv", index=False)
    # Même échelle pour les deux graphiques, pour qu'ils se comparent.
    ymin = min(0, j["solde_pct_q1"].min()) - 0.25
    ymax = max(j["solde_pct_q3"].max(), j["solde_pct_groupe"].max()) * 1.12 + 0.5
    for g, nom in [("prenoms_vitesse", "solde_net_par_jour_prenoms_vitesse.png"),
                   ("autres", "solde_net_par_jour_autres.png")]:
        figure(j, g, int((f["groupe"] == g).sum()), ymin, ymax, SORTIE / nom)
    print(f"\nécrit dans {SORTIE}")


if __name__ == "__main__":
    main()
