"""10. Vérification des tableaux d'Axel sur les fiches très touchées (mail du 2026-10-07).

    uv run python consolidation/10_fiches_attaquees.py

Axel classe les fiches selon leurs suppressions en 14 jours : aucune, 1 à 10,
11 et plus (ses « flagged »). Chaque tableau est refait sur deux bases : la
sienne (table brute `reviews` sans les avis modifiés, 5 230 disparitions) et la
nôtre (`reviews_doublons_cleaned_all`, avis modifiés compris, 4 590
suppressions). Le bloc commun est `sql/10_commun.sql`.

Produit :
  sorties/10_croisement.csv     catégorie Axel × catégorie nettoyée, fiches en plus chez nous
  sorties/10_tab3_taux.csv      tableaux 1 et 3 : fiches, suppressions, part supprimée
  sorties/10_tab4_jours.csv     tableau 4 : étalement des suppressions sur les 13 jours
  sorties/10_tab5_age.csv       tableau 5 : âge des avis à la suppression, et du stock
  sorties/10_tab5_resume.csv    tableau 5, bas : âge médian, moins de 7 et 30 jours, plus d'un an
"""
from commun import SQL, client, ecrire_csv

COMMUN = (SQL / "10_commun.sql").read_text(encoding="utf-8")

for nom in ["10_croisement", "10_tab3_taux", "10_tab4_jours", "10_tab5_age", "10_tab5_resume"]:
    texte = COMMUN + "\n" + (SQL / f"{nom}.sql").read_text(encoding="utf-8")
    df = client().query(texte).to_dataframe()
    ecrire_csv(df, nom)
    print(df.to_string(index=False))
