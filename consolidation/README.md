# Consolidation — les chiffres du rapport, régénérables

Écrit le 2026-09-29. Un script par point du plan de Romain. Chaque script lance ses requêtes
dans BigQuery, écrit ses CSV dans `sorties/` et un graphique de contrôle dans
`sorties/figures/`. Une synthèse `.md` par point reprend les résultats.

## Lancer

Depuis la racine du dépôt, chaque script en moins d'une minute :

```bash
uv run python consolidation/1a_tables.py
uv run python consolidation/1b_entonnoir.py
uv run python consolidation/1c_secteurs.py
uv run python consolidation/1d_survie.py
uv run python consolidation/2_1_peu_de_suppressions.py
uv run python consolidation/2_2_deux_phenomenes.py
uv run python consolidation/2_3_taux.py
uv run python consolidation/3a_jour_par_jour.py
uv run python consolidation/3b_regression_reponse.py
uv run python consolidation/4_0_niveaux_local_guide.py
uv run python consolidation/4a_quelle_fiche.py
nice -n 19 uv run python consolidation/4b_quel_avis.py      # environ 1 minute
uv run python consolidation/5_reponse_jour_par_jour.py      # environ 20 secondes, plusieurs cœurs
```

Les requêtes lisent BigQuery et n'écrivent rien dedans. Clé de service : le seul `.json` de
`~/.gcp/`.

## Les synthèses

| Point | Synthèse | Scripts |
|---|---|---|
| 1. Le corpus | `1_corpus.md` | `1a`, `1b`, `1c`, `1d` |
| 2.1 Google supprime peu | `2_1_peu_de_suppressions.md` | `2_1_peu_de_suppressions.py` |
| 2.2 Les deux phénomènes | `2_2_deux_phenomenes.md` | `2_2_deux_phenomenes.py` |
| 2.3 Taux par caractéristique | `2_3_taux.md` | `2_3_taux.py` |
| 3. Réponse du propriétaire | `3_reponse_proprietaire.md` | `3a_jour_par_jour.py`, `3b_regression_reponse.py` |
| 4. Quelle fiche, quel avis dans la fiche | `4_quelle_fiche_quel_avis.md` | `4_0_niveaux_local_guide.py`, `4a_quelle_fiche.py`, `4b_quel_avis.py` |
| 5. Réponse du propriétaire, jour par jour | `5_reponse_jour_par_jour.md` | `5_reponse_jour_par_jour.py` |
| 6. Régression du panel (à faire) | `6_plan_regression_panel.md` : plan et questions à trancher | — |
| Pour Axel : sur quels avis on mesure, comment se lit une régression | `explication_pour_axel.md` | `axel_comparaison_perimetres.py` |

## Les CSV

Séparateur `;`, virgule décimale : import direct dans un Google Sheets en français
(Fichier > Importer > séparateur « point-virgule »). Chaque CSV donne les avis et les
suppressions à côté des taux, pour pouvoir regrouper des lignes dans Sheets.

| Fichier | Contenu |
|---|---|
| `1a_tables.csv` | lignes, avis, fiches, pays, dates, suppressions de `reviews`, `reviews_doublons_cleaned`, `businesses` |
| `1a_fiches_par_case.csv` | fiches par région, secteur et taille |
| `1b_entonnoir.csv` | de l'export brut à 03B, étape par étape, et quatre contrôles à 0 |
| `1b_retires_365_jours_par_fiche.csv` | fiches qui perdent des avis supprimés à cause de la règle des 365 jours |
| `1b_retires_365_jours_profil.csv` | les mêmes suppressions comptées par note, secteur, mois de modification, jour de disparition |
| `1c_avis_secteur_taille.csv` | avis et fiches par secteur et taille, part du corpus |
| `1c_suppressions_secteur_region.csv` | suppressions pour 10 000 avis par secteur, Europe / US |
| `1d_survie.csv` | avis publiés de J-7 à J+7 : suppressions par âge, encore en ligne sur 10 000 |
| `2_1a_par_annee.csv` | base complète : suppressions pour 10 000 avis par année de publication |
| `2_1b_par_age.csv` | avis publiés de J-30 à J+13 : suppressions par âge |
| `2_1b_resume.csv` | les mêmes : jours 1 à 8 comparés au 9e jour et après |
| `2_2_resume.csv` | chaînes et salles, par enseigne : avis, suppressions, notes, délais |
| `2_2a_calendrier.csv` | avis supprimés par jour de publication × jour de suppression |
| `2_2b_delai.csv` | avis supprimés par délai entre publication et suppression |
| `2_2c_auteurs.csv` | profil des auteurs, supprimés et conservés |
| `2_2_par_jour.csv` | avis supprimés par jour de publication et par jour de suppression |
| `2_3_<caractéristique>.csv` | 11 fichiers, un par caractéristique : suppressions pour 10 000 avis, US / Europe |
| `3_population.csv` | la population du point 3, étape par étape |
| `3a_jour_par_jour.csv` | suppressions du 3e au 8e jour, par habitude, réponse, taille |
| `3b_effectifs.csv` | avis et suppressions par délai × habitude, avant le modèle |
| `axel_comparaison_perimetres.csv` | taux par note et par profil d'auteur, sur notre panel et sur la table « J-7 à J+7 + toutes les suppressions » |
| `3b_fiches_par_case.csv` | les fiches derrière les suppressions de chaque case : cid, enseigne, dates |
| `4_0_niveaux_local_guide.csv` | suppressions pour 10 000 avis par niveau Local Guide, US / Europe |
| `4a_effectifs.csv`, `4a_effets.csv` | quelle fiche est touchée : effectifs par case, effets et règle de citation |
| `4a_fiches_touchees.csv` | les fiches touchées : cid, enseigne, dates de première et dernière suppression |
| `4b_effectifs.csv`, `4b_effets.csv` | quel avis tombe dans la même fiche le même jour : effectifs, effets |
| `4b_fiches_par_case.csv` | les fiches derrière les suppressions de chaque case, avec les jours |
| `5_effectifs.csv`, `5_effets.csv` | réponse du propriétaire jour par jour : effectifs, effets |
| `5_fiches_par_case.csv` | les fiches derrière les suppressions de chaque case, avec les jours |
| `3b_effets.csv` | effets de la régression, avec fourchette |

Chaque CSV porte une colonne `perimetre` : `tous`, puis `sans_enseignes`, sans les 95 fiches
de `biz_surveillance` (les 4 chaînes antiparasitaires US au nom exact, 93 fiches, et les
2 salles espagnoles).

## Les tables utilisées

| Table BigQuery | Sert à |
|---|---|
| `reviews_doublons_cleaned` | la base complète : 1a à 1d, 2.1, 2.2 |
| `reviews_panel_features_03B` | 2.3 et 3 |
| `reviews` | 1a, 1b, et le jour de première observation d'un avis (1d, 2.1b) |
| `businesses`, `biz_surveillance` | secteur, pays, taille ; enseignes signalées |

Une suppression : la ligne gardée de l'avis dans `reviews_doublons_cleaned` a
`deleted_detected_at` rempli. `1_corpus.md` explique la construction.

## Requête de vérification, à lancer à la main

`sql/verif_avis_modifies_plus_d_un_an.sql` liste les 555 avis supprimés que la règle des
365 jours retire de la base : fiche, note, texte, dates, auteur, lien. À lancer dans la console
BigQuery. Le résultat contient des données personnelles : ne pas l'exporter dans le dépôt.

## Règle de citation des régressions 4 et 5

Un effet se cite si sa case et sa case de référence ont au moins 20 suppressions, réparties sur
au moins 10 fiches, sans qu'une fiche en porte plus du quart (`commun.py`, décidé le
2026-09-29). Chaque CSV d'effets porte la colonne `citable`.

## Organisation

```
commun.py        connexion BigQuery, écriture des CSV, style des graphiques
sql/             une requête par CSV, expliquée en tête
sorties/         les CSV
sorties/figures/ les graphiques de contrôle
```
