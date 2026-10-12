#!/usr/bin/env python3
"""Jour de publication contre jour de suppression, pour les deux groupes d'enseignes,
fiche n° 9 des faits saignants.

    PYTHONPATH=".venv/Lib/site-packages;outils" <python uv> etudes-ponctuelles/2026-10-06-bulles-enseignes/graphique.py

Demande de Matthieu du 2026-10-06, après la réunion avec Romain : refaire le graphique
à bulles du Word des faits saignants, en deux graphiques séparés.
  - les 4 chaînes antiparasitaires américaines, avis 4-5 étoiles ;
  - les 2 salles de sport espagnoles, avis 1 étoile.
Abscisse : jour où le robot constate la suppression. Ordonnée : jour de publication.
Une bulle par couple (publication, suppression), d'autant plus grosse qu'il y a d'avis
supprimés. L'aire de la bulle est proportionnelle au nombre d'avis, à la même échelle
sur les deux graphiques.

Base : reviews_doublons_cleaned_all (doublons retirés), une ligne par avis. Les deux
groupes sont repérés par les colonnes de features_reviews_doublons_cleaned_all (chaînes
sur le début du nom, salles sur leur cid, voir 03C_features_corpus.py), jointes par
review_id.

Suppression : deleted_detected_at renseigné, sans règle des 2 jours (règle de Matthieu
du 2026-10-05 pour une base sans doublons). Mesuré le 2026-10-06 : 1 199 avis 4-5
étoiles des chaînes ont disparu, 1 163 avec la règle des 2 jours ; les 36 d'écart sont
tous vus disparus le 24 août, dernier passage, sans recul pour confirmer. Pour les
salles, 317 avis 1 étoile avec les deux règles. Les dates de suppression sont les mêmes
avec les deux règles.

Le robot passe du 11 au 24 août : une suppression n'est vue qu'à partir du 12.

Fenêtre de publication, décidée avec Romain à la réunion du 2026-10-06 (réu_06_10.docx,
00:28:35) : « faut pas remonter au 1er juillet […] maximum 22 » pour les chaînes, et le
31 juillet pour les salles, dont l'attaque date des 1er et 2 août. Une ligne par jour à
partir de là. Les avis supprimés publiés avant sont regroupés sur une ligne à part, en
bas du graphique, pour que les totaux restent complets : côté chaînes, il y a des avis
de plusieurs années ; côté salles, un seul avis, publié le 28 juillet.

Sorties :
  livrables/restitution_finale/graphiques/faits-saignants/graphiques/bulles_chaines_antiparasitaires.png
  livrables/restitution_finale/graphiques/faits-saignants/graphiques/bulles_salles_espagnoles.png
  livrables/restitution_finale/graphiques/faits-saignants/donnees/bulles_chaines_antiparasitaires.csv
  livrables/restitution_finale/graphiques/faits-saignants/donnees/bulles_salles_espagnoles.csv
"""
import sys
from datetime import date, timedelta
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "outils"))
from local import connexion  # noqa: E402

FEATURES = RACINE / "data" / "local" / "features_reviews_doublons_cleaned_all.parquet"
SORTIE = RACINE / "livrables" / "restitution_finale" / "graphiques" / "faits-saignants"

# Palette des graphiques de la restitution (2026-10-05-phenomenes-par-jour).
BLEU = "#2a78d6"
ENCRE, ENCRE_2, GRILLE, FOND = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"

PREMIERE_SUPPRESSION = date(2026, 8, 12)  # lendemain du premier passage du robot
DERNIERE_SUPPRESSION = date(2026, 8, 24)
# Premier jour de publication affiché ; avant, une seule ligne « avant le ... ».
DEBUT_CHAINES = date(2026, 7, 22)
DEBUT_SALLES = date(2026, 7, 31)
POINTS_PAR_AVIS = 5  # aire de bulle, en points², pour un avis supprimé
TAILLES_LEGENDE = (1, 10, 50, 100)

GROUPES = {
    "chaines": dict(
        filtre="f.chaine_antiparasitaire AND r.star >= 4",
        fichier="bulles_chaines_antiparasitaires",
        etoiles="4-5 étoiles",
    ),
    "salles": dict(
        filtre="f.salle_espagnole AND r.star = 1",
        fichier="bulles_salles_espagnoles",
        etoiles="1 étoile",
    ),
}


def espace(n: float) -> str:
    return f"{n:,.0f}".replace(",", " ")


def jm(d: date) -> str:
    return d.strftime("%d/%m")


def charger(con, filtre: str) -> pd.DataFrame:
    return con.sql(f"""
        SELECT r.review_id, r.cid, r.star,
               r.created_at::DATE          AS publie_le,
               r.deleted_detected_at::DATE AS supprime_le
        FROM reviews_doublons_cleaned_all r
        JOIN read_parquet('{FEATURES.as_posix()}') f USING (review_id)
        WHERE {filtre}
    """).df()


def cellules(avis: pd.DataFrame, debut: date | None) -> pd.DataFrame:
    """Une ligne par couple (jour de publication, jour de suppression)."""
    s = avis.dropna(subset=["supprime_le"]).copy()
    s["publie_le"] = pd.to_datetime(s["publie_le"]).dt.date
    s["supprime_le"] = pd.to_datetime(s["supprime_le"]).dt.date
    s["ligne"] = s["publie_le"].astype(str)
    if debut is not None:
        s.loc[s["publie_le"] < debut, "ligne"] = "avant"
    c = (s.groupby(["ligne", "supprime_le"]).size().rename("avis_supprimes").reset_index())
    return c


def graphique(c: pd.DataFrame, groupe: dict, titre: str, sous_titre: str, debut: date,
              fin: date, ligne_avant: bool, diagonale: bool, hauteur: float) -> Path:
    fig, ax = plt.subplots(figsize=(8.5, hauteur), dpi=150)
    fig.patch.set_facecolor(FOND)
    ax.set_facecolor(FOND)

    haut = (fin - debut).days
    # Écart entre le premier jour affiché et la ligne « avant », à proportion du nombre de
    # jours, pour que la ligne ne flotte pas sous un graphique de quelques jours.
    ecart = max(1.5, round(haut / 9))

    def y_de(ligne: str) -> float:
        return -ecart if ligne == "avant" else (date.fromisoformat(ligne) - debut).days

    x = [(d - PREMIERE_SUPPRESSION).days for d in c["supprime_le"]]
    y = [y_de(v) for v in c["ligne"]]
    ax.scatter(x, y, s=POINTS_PAR_AVIS * c["avis_supprimes"], color=BLEU, alpha=0.55,
               edgecolor=BLEU, linewidth=0.6, zorder=4)

    n_jours = (DERNIERE_SUPPRESSION - PREMIERE_SUPPRESSION).days
    ax.set_xlim(-0.7, n_jours + 0.7)
    ax.set_xticks(range(n_jours + 1))
    ax.set_xticklabels([jm(PREMIERE_SUPPRESSION + timedelta(i)) for i in range(n_jours + 1)])

    ticks = list(range(0, haut + 1))
    labels = [jm(debut + timedelta(t)) for t in ticks]
    if ligne_avant:
        ticks = [-ecart] + ticks
        labels = [f"avant le {jm(debut)}"] + labels
        ax.axhline(-ecart / 2, color=GRILLE, lw=1, zorder=1)
    ax.set_yticks(ticks)
    ax.set_yticklabels(labels)
    ax.set_ylim(-ecart * 1.5 if ligne_avant else -0.8, haut + 0.8)

    poignees = [ax.scatter([], [], s=POINTS_PAR_AVIS * n, color=BLEU, alpha=0.55,
                           edgecolor=BLEU, linewidth=0.6) for n in TAILLES_LEGENDE]
    etiquettes = [f"{n} avis supprimé{'s' if n > 1 else ''}" for n in TAILLES_LEGENDE]
    if diagonale:
        # Un avis supprimé 7 jours après sa publication : publié le jour de suppression - 7.
        xs = [-0.7, n_jours + 0.7]
        ys = [(PREMIERE_SUPPRESSION - timedelta(7) - debut).days + v for v in xs]
        poignees += ax.plot(xs, ys, ls=(0, (4, 3)), color=ENCRE_2, lw=0.9, zorder=3)
        etiquettes.append("supprimé 7 jours après sa publication")

    ax.tick_params(colors=ENCRE_2, labelsize=7.5, length=0)
    ax.grid(color=GRILLE, lw=0.6, zorder=0)
    for cote in ["top", "right", "left", "bottom"]:
        ax.spines[cote].set_visible(False)
    ax.set_xlabel("jour où le robot constate la suppression (août 2026)", color=ENCRE_2,
                  fontsize=8)
    ax.set_ylabel("jour de publication de l'avis", color=ENCRE_2, fontsize=8)

    # En-tête en pouces depuis le haut, pour garder les mêmes écarts quelle que soit la
    # hauteur de la figure.
    fig.text(0.01, 1 - 0.12 / hauteur, titre, va="top", fontsize=11, color=ENCRE)
    fig.text(0.01, 1 - 0.42 / hauteur, sous_titre, va="top", fontsize=7.5,
             color=ENCRE_2, linespacing=1.5)
    fig.legend(poignees, etiquettes, loc="upper left",
               bbox_to_anchor=(0.005, 1 - 1.0 / hauteur), ncol=len(poignees),
               frameon=False, fontsize=7.5, labelcolor=ENCRE, columnspacing=2.2,
               handletextpad=1.1, borderpad=0.2)
    fig.tight_layout(rect=(0, 0, 1, 1 - 1.3 / hauteur))

    chemin = SORTIE / "graphiques" / f"{groupe['fichier']}.png"
    fig.savefig(chemin, facecolor=FOND)
    plt.close(fig)
    return chemin


def ligne_du_bas(n: int, debut: date) -> str:
    s = "s" if n > 1 else ""
    return (f"Ligne du bas : {espace(n)} avis supprimé{s} publié{s} avant le "
            f"{debut.day} juillet")


def main():
    con = connexion()
    (SORTIE / "graphiques").mkdir(parents=True, exist_ok=True)
    (SORTIE / "donnees").mkdir(parents=True, exist_ok=True)

    # Les 4 chaînes antiparasitaires, avis 4-5 étoiles.
    g = GROUPES["chaines"]
    a = charger(con, g["filtre"])
    c = cellules(a, DEBUT_CHAINES)
    sup = a.dropna(subset=["supprime_le"])
    par_jour = sup.groupby(pd.to_datetime(sup["supprime_le"]).dt.date).size()
    deux = par_jour.nlargest(2).sort_index()
    avant = int((pd.to_datetime(sup["publie_le"]).dt.date < DEBUT_CHAINES).sum())
    recents = a[pd.to_datetime(a["publie_le"]).dt.date >= DEBUT_CHAINES]
    print(f"chaînes : {a['cid'].nunique()} fiches, {len(a)} avis 4-5★, {len(sup)} supprimés, "
          f"dont {avant} publiés avant le {DEBUT_CHAINES}")
    print(f"  publiés depuis le {DEBUT_CHAINES} : {len(recents)}, dont "
          f"{recents['supprime_le'].notna().sum()} supprimés")
    print(f"  plus grosse bulle : {c['avis_supprimes'].max()} avis")
    print("  suppressions par jour :\n" + par_jour.to_string())
    # Après le retrait en masse : combien sont retirés 6 à 8 jours après leur publication.
    apres = sup[pd.to_datetime(sup["supprime_le"]).dt.date > deux.index[1]]
    age = (pd.to_datetime(apres["supprime_le"]) - pd.to_datetime(apres["publie_le"])).dt.days
    a_7_jours = int(age.between(6, 8).sum())
    print(f"  après le {deux.index[1]} : {len(apres)} supprimés, dont {a_7_jours} 6 à 8 jours "
          f"après publication ({int((age == 7).sum())} à 7 jours pile)")
    titre = (f"Chaînes antiparasitaires : {espace(deux.sum())} avis retirés en masse les "
             f"{deux.index[0].day} et {deux.index[1].day} août, puis au bout de 7 jours")
    sous_titre = (
        f"4 chaînes américaines ({a['cid'].nunique()} fiches) : {espace(len(sup))} de leurs "
        f"{espace(len(a))} avis 4-5 étoiles ont disparu entre le 12 et le 24 août 2026. "
        f"Après le {deux.index[1].day} août, {a_7_jours} des {len(apres)} avis\n"
        f"retirés l'ont été 6 à 8 jours après leur publication. "
        f"{ligne_du_bas(avant, DEBUT_CHAINES)}, dont certains depuis plusieurs années.\n"
        f"Le robot passe du 11 au 24 août : une suppression n'est vue qu'à partir du 12. Les "
        f"{espace(par_jour.get(DERNIERE_SUPPRESSION, 0))} avis vus disparus le 24, dernier "
        f"passage, ne sont pas confirmés.")
    fin = max(pd.to_datetime(sup["publie_le"]).dt.date)
    p1 = graphique(c, g, titre, sous_titre, DEBUT_CHAINES, fin, True, True, 7.4)
    d1 = SORTIE / "donnees" / f"{g['fichier']}.csv"
    c.rename(columns={"ligne": "publie_le"}).to_csv(d1, index=False)

    # Les 2 salles de sport espagnoles, avis 1 étoile.
    g = GROUPES["salles"]
    a = charger(con, g["filtre"])
    c = cellules(a, DEBUT_SALLES)
    sup = a.dropna(subset=["supprime_le"])
    pub = pd.to_datetime(sup["publie_le"]).dt.date
    avant = int((pub < DEBUT_SALLES).sum())
    rafale = int(pub.isin([date(2026, 8, 1), date(2026, 8, 2)]).sum())
    par_jour = sup.groupby(pd.to_datetime(sup["supprime_le"]).dt.date).size()
    deux = par_jour.nlargest(2).sort_index()
    print(f"\nsalles : {a['cid'].nunique()} fiches, {len(a)} avis 1★, {len(sup)} supprimés, "
          f"dont {rafale} publiés les 1er et 2 août")
    print(f"  plus grosse bulle : {c['avis_supprimes'].max()} avis")
    print("  suppressions par jour :\n" + par_jour.to_string())
    titre = (f"Salles de sport espagnoles : {espace(rafale)} avis 1 étoile publiés les 1er et "
             f"2 août, retirés surtout les {deux.index[0].day} et {deux.index[1].day} août")
    sous_titre = (
        f"2 salles de sport espagnoles : {espace(len(sup))} de leurs {espace(len(a))} avis "
        f"1 étoile ont disparu entre le 12 et le 24 août 2026, dont {espace(deux.sum())} les "
        f"{deux.index[0].day} et {deux.index[1].day} août.\n"
        f"Le robot passe du 11 au 24 août : une suppression n'est vue qu'à partir du 12. "
        f"{ligne_du_bas(avant, DEBUT_SALLES)}.")
    p2 = graphique(c, g, titre, sous_titre, DEBUT_SALLES, max(pub), True, False, 4.6)
    d2 = SORTIE / "donnees" / f"{g['fichier']}.csv"
    c.rename(columns={"ligne": "publie_le"}).to_csv(d2, index=False)

    for f in (p1, d1, p2, d2):
        print(f"écrit : {f}")


if __name__ == "__main__":
    main()
