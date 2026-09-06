# ReviewFlowz — Analyse des suppressions d'avis Google

Étude quantitative : quelles caractéristiques d'un avis Google sont associées à sa suppression
par Google. Angle du livrable : les **faux positifs** — si une caractéristique anodine prédit
fortement la suppression, c'est un indice indirect que Google supprime des avis légitimes.

Commanditaire : Axel, directeur de ReviewFlowz. Jalon livrable : **2026-09-15**.

## Où sont les choses

| Chemin | Contenu |
|---|---|
| `documentations/` | Notes de cadrage, méthodologie, décisions, analyses. Tout le contexte métier. |
| `data/exports/exports/*.parquet` | Le jeu de données. **Gitignoré**, jamais committé. |
| `data/*.csv` | Échantillons de vérification manuelle. Gitignoré aussi. |
| `BACKLOG.md` | État d'avancement et prochaines étapes. À tenir à jour. |

Note de référence sur les facteurs et le programme d'analyse :
`documentations/2026-09-06-facteurs-et-programme-danalyse.md`.

## Les données

14 vagues quotidiennes du 11 au 24 août 2026, recensement complet du listing d'avis de
9 048 établissements (7 secteurs, US + Europe hors Royaume-Uni). **4 878 151 avis de base,
5 230 suppressions, taux 0,107 %.**

Schéma détaillé dans `data/exports/exports/README.md`.

Outil : DuckDB en lecture directe sur les parquet. `reviews.parquet` fait 834 Mo — ne jamais le
charger entier en pandas, toujours agréger en SQL.

```python
import duckdb
c = duckdb.connect()
c.sql("CREATE VIEW r AS SELECT * FROM 'reviews.parquet' WHERE NOT is_update")
```

## Pièges du jeu de données — à respecter systématiquement

1. **`review_id` n'est pas une clé unique.** Filtrer `NOT is_update` pour obtenir les lignes de
   base. Sans ce filtre, tout comptage est faux (2 012 lignes de version + 617 résurrections).
2. **Toujours stratifier sur l'âge de l'avis.** L'âge est le facteur dominant (×163 entre moins
   de 7 jours et plus de 3 ans). Un bivarié en marge est confondu et donne des chiffres faux.
3. **Les suppressions sont concentrées.** 84 % des établissements n'en ont aucune ; 39 fiches
   portent 19,5 % du total. Un modèle sur le pool complet apprend à reconnaître ces fiches, pas
   des caractéristiques d'avis. D'où les deux analyses séparées (voir ci-dessous).
4. **Censure à droite.** Les avis apparus pendant le suivi ont une fenêtre d'observation plus
   courte. Pour comparer des taux bruts, restreindre à la cohorte présente en vague 1.
5. **Les URL de photos sont resignées à chaque collecte** : jamais un signal de changement.
6. **L'histogramme se met à jour avant le listing** : le listing est la source de vérité pour
   dater une suppression.

## Périmètre — décidé le 2026-09-06

**La modélisation cible les avis frais (≤ 30 jours).** Justifié par la courbe de risque : le
risque de suppression par vague culmine à 7-13 jours (0,50 %), puis s'effondre — divisé par 15 à
30 jours, par 156 à un an. Le périmètre frais fait 106 761 avis et 2 853 suppressions, soit un
taux de **2,67 %** contre 0,107 % sur le corpus entier : le problème d'événement rare disparaît,
les probabilités redeviennent présentables, tout tourne en secondes.

**Le stock ancien reste dans les données et n'est pas écarté.** Ce qu'on ne cherche pas à faire,
c'est expliquer ce qui fait supprimer un avis *ancien* — sauf si un résultat pertinent émerge.
Le stock ancien reste mobilisé pour :
- le **Test 2** (débordement d'une purge sur l'organique), où les avis anciens sont précisément
  la grandeur mesurée ;
- les **features d'établissement** (vélocité, historique, trajectoire de note) ;
- toute **comparaison ou contrôle** frais / ancien.

## Architecture d'analyse — décidée le 2026-09-06

**Deux analyses séparées, pas un modèle unique.**

- **Analyse A — quel établissement subit une intervention.** Unité : l'établissement
  (n = 9 048, 1 399 touchés). Régresseurs : vélocité de collecte, secteur, taille, pays, volume,
  note moyenne et sa trajectoire.
- **Analyse B — quel avis tombe dans une fiche qui perd des avis.** Unité : l'avis, restreint aux
  1 399 établissements touchés. **Logistique conditionnelle à effets fixes d'établissement** :
  l'effet fixe absorbe tout le contexte de fiche, ne laisse subsister que la comparaison entre
  avis d'une même fiche, et neutralise la domination des fiches purgées.

Erreurs-types groupées au niveau du groupe d'enseignes.

## Conventions

- **Restituer en risque relatif, jamais en probabilité absolue** (elles vaudront toutes ~0,1 %).
- **Évaluer par AUC et calibration, jamais par exactitude** (prédire « jamais supprimé » donne
  99,89 %).
- Découpage train/test **par établissement et par auteur**, jamais aléatoire par ligne.
- Sous-échantillonnage des négatifs autorisé pour le coût de calcul : les odds ratios sont
  inchangés, seule la constante se corrige.
- Contrôle obligatoire : relancer sans les 39 fiches à plus de 5 % de purge et vérifier que les
  conclusions tiennent.

## Données personnelles — contrainte ferme

`reviewer_name`, `reviewer_avatar`, `review_link` et `text` identifient des personnes. Le README
de l'export interdit la rediffusion.

- `data/` est gitignoré. **Ne jamais committer de données, même un extrait.**
- Ne jamais faire figurer de nom d'auteur ou de lien d'avis dans une note de `documentations/`.
- Retirer les colonnes auteur dès qu'une analyse s'en passe.

## Ce qui a été écarté, et pourquoi

Ne pas reproposer sans élément nouveau :

- **Score de génération par IA** — détecteurs non fiables et biaisés contre les non-natifs
  (Liang et al., 2023). Intenable dans une étude sur les faux positifs.
- **Redondance exacte de texte intra-établissement** — 7 646 avis sur 2,9 M. Signal inexistant.
- **Adresse, téléphone, complétion de fiche** — absents de l'export.
- **Expérimentations contrôlées** (poster des avis tests) — conditions d'utilisation, et illégal
  au Royaume-Uni depuis le DMCC Act.

## Style de restitution attendu

Français, direct, pas d'introduction ni de conclusion de politesse. Listes plutôt que
paragraphes. Chaque affirmation chiffrée est sourcée sur une requête reproductible. Les notes
d'analyse vont dans `documentations/`, datées, au format des notes existantes.
