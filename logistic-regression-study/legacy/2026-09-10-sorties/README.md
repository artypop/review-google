# Sorties — régression logistique sur les avis récents

Produites par [`../06_statsmodels_analysis_review_claude.py`](../06_statsmodels_analysis_review_claude.py),
qui les réécrit entièrement à chaque exécution. Instantané du 2026-09-09 à 21h56, sur les tables
BigQuery en v3 (`sql/04_avis_features-v3.sql` et `sql/05_panel_final-v3.sql`).

## Périmètre

Les avis de moins de 3 mois à leur première vague de suivi : **239 491 avis, 2 894 267 lignes
avis-vague, 2 919 suppressions**, soit 10,09 suppressions pour 10 000 lignes avis-vague.

**L'unité comptée est la ligne avis-vague, pas l'avis.** Un avis apparaît une fois par vague où
il était encore en ligne. Tout taux de ce dossier a ce dénominateur.

## Les fichiers

| Fichier | Contenu |
|---|---|
| `06_coefficients.csv` | Les deux modèles, complet et hors fiches attaquées, en risque relatif avec bornes et p-value. La colonne `modele` distingue les deux. |
| `06_croisements_par_age.csv` | Taux de suppression par caractéristique, séparé par tranche d'âge. À lire avant les coefficients : il montre les effets bruts, sans ajustement. |
| `06_calibration.csv`, `06_calibration.png` | Risque annoncé contre risque observé, sur des établissements jamais vus à l'entraînement. |
| `06_fiches_attaquees.csv` | Les 4 fiches écartées du modèle robuste, avec les compteurs qui déclenchent la règle. |
| `06_journal_execution.txt` | Sortie console complète : contrôles du panel, volumétrie, tableaux de coefficients, AUC, et les réserves de lecture. |

## À savoir avant de citer un chiffre

- **Restituer en risque relatif**, jamais en probabilité absolue.
- **Ne pas lire `langue_etrangere_au_pays` comme un effet de langue.** Elle compare un code de
  langue à un code de pays : 71 % des avis américains y sont comptés « étrangers » parce que
  `en` n'est pas `us`. Elle mesure surtout « établissement américain ».
- **La protection du texte long ne tient pas** : ×0,50 dans le modèle complet, ×0,74 sans les
  fiches attaquées.
- Les avis encore en ligne au dernier passage n'ont pas fini leur histoire : leur sort est
  inconnu, pas négatif.
- AUC 0,884 sur des établissements jamais vus, calibration juste sur les dix tranches.

Réserves complètes dans [`../BACKLOG.md`](../BACKLOG.md), section « Fait le 2026-09-09 ».
