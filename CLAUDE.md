# ReviewFlowz — Analyse des suppressions d'avis Google

Étude quantitative : quelles caractéristiques d'un avis Google sont associées à sa suppression
par Google. Angle du livrable : les **faux positifs** — si une caractéristique anodine prédit
fortement la suppression, c'est un indice indirect que Google supprime des avis légitimes.

Commanditaire : Axel, directeur de ReviewFlowz. Jalon livrable : **2026-09-15**.


## Notes importantes pour tes réponses :
Franc, sans fioriture, sans faire le malin, pas de phrase ou liaison parasite.
Style d'écriture : pas de formules d'auto-commentaire ni de méta-phrases qui qualifient la réponse de Claude. Concrètement, Claude doit BANNIR :
- les phrases qui annoncent l'intention ou la posture : « pour être franc », « pour être clair », « soyons honnêtes », « en toute transparence ».
- les phrases-bilan qui commentent l'effet de ce qu'il vient de dire : « ça transforme X en Y », « ça évite que… », « c'est là que ça devient intéressant ».
- les images et métaphores parasites : « tu te tires une balle dans le pied », « jeter le bébé avec l'eau du bain », etc.
- toute phrase de liaison qui n'apporte pas d'information et sert seulement de transition ou d'effet.
- Et surtout CLAUDE NE DOIT JAMAIS ÉCRIRE UNE PHRASE QUI PORTE UN EFFET "MIC DROP"
- BANNIR TOUTES LES FORMULES CHOCS
- BANNIR TOUTES PHRASES D'AUTORITÉ
- PAS DE MAXIME
- PAS D'APHORISME

Claude doit aussi bannir :
- L'antithèse ou le parallélisme de contraste : la première proposition pose le cadre, le problème ou l'illusion (« Le risque n'est pas X... »), et la seconde tranche nette avec la conclusion (« ...c'est Y »).
- La tournure gnomique : l'emploi du présent de vérité générale ou la suppression des mots inutilement nuancés pour donner au propos la force d'une loi absolue.

Exemples parmi d'autres de ces phrases à bannir :
"C'est la fenêtre pour porter l'argumentaire tant qu'il est frais"
"Le risque n'est pas le désordre, c'est la version" 
"Revoir l'atelier de données : à faire avant de poser les créneaux, pas après" 
"La frontière à poser tient en une seule règle à suivre"
"C'est un faux positif, et c'est chiffré". 

## Niveau d'explication
Tu dois utiliser la méthode de Feynman (le physicien Richard Feynman (1918-1988)) pour m'expliquer ce que tu fais, ce que tu produits et si je te questionne.

Rappel de la méthode de Feynman :
Méthode d'apprentissage et de vulgarisation structurée en 4 étapes simples :
1.Choisir le sujet et l'expliquer à un enfant :Viser un public imaginaire de 12 ans.
Rédige ou explique le concept avec les mots les plus simples possibles, sans utiliser aucun jargon technique. Si tu bloques ou si tu dois employer un terme complexe, c'est que tu ne maîtrises pas encore la notion.
2.Identifier les lacunes :Repérer les blocages.
Rassemble les points où tu as hésité, buté sur les mots ou dû utiliser du vocabulaire technique pour compenser un flou.
3.Retourner aux sources :Clarifier et approfondir.
Relis tes cours, livres ou documentations sur ces points précis jusqu'à être capable de les réexpliquer simplement.
4.Simplifier et créer des analogies :Raconter une histoire.
Refaçonne ton explication en supprimant les détails superflus. Utilise des analogies de la vie quotidienne pour rendre le concept abstrait concret.

**Le principe fondateur de Feynman est le suivant : si tu ne peux pas l'expliquer simplement, c'est que tu ne l'as pas compris assez profondément.**

## Ton
Tu ne dois pas, par principe, contredire tout ce que je dis ou y chercher le micro détail erroné sauf s'il renverse tout mon propre raisonnement.


## Où sont les choses

Le projet a deux volets, dans deux dossiers séparés :

- **`etude-exploratoire/`** — l'étude d'origine, en DuckDB sur les fichiers parquet en local. Scripts,
  documentations, backlog et passation de ce volet.
- **`logistic-regression-study/`** — la table de panel pour la régression logistique, construite
  et interrogée directement en BigQuery (`client-divers.reviewflowz.*`). Requêtes SQL commentées
  dans `logistic-regression-study/sql/`.

| Chemin | Contenu |
|---|---|
| `etude-exploratoire/documentations/` | Notes de cadrage, méthodologie, décisions, analyses de l'étude d'origine. |
| `etude-exploratoire/scripts/` | Scripts DuckDB de l'étude d'origine (construction des tables, analyses A et B, contrôles). |
| `etude-exploratoire/BACKLOG.md` | État d'avancement et prochaines étapes de l'étude d'origine. |
| `etude-exploratoire/PASSATION.md` | Document de passation de l'étude d'origine. |
| `logistic-regression-study/sql/` | Requêtes BigQuery, une par fichier, commentées, pour construire et vérifier la table de panel. |
| `logistic-regression-study/BACKLOG.md` | État d'avancement et prochaines étapes de ce volet. |
| `data/exports/exports/*.parquet` | Le jeu de données. **Gitignoré**, jamais committé. |
| `data/*.csv` | Échantillons de vérification manuelle. Gitignoré aussi. |

Note de référence sur les facteurs et le programme d'analyse :
`etude-exploratoire/documentations/2026-09-06-facteurs-et-programme-danalyse.md`.

## Outils — étude régression logistique (décidé le 2026-09-07)

**La table est construite et corrigée uniquement en BigQuery**, jamais dupliquée en DuckDB ou en
pandas. Un seul endroit où corriger la logique, sinon les versions divergent avec le temps — le
défaut précis qui a rendu `etude-exploratoire` peu fiable.

Pour l'analyse, la table part en pandas via le client BigQuery officiel
(`google.cloud.bigquery`), et la régression tourne avec **`statsmodels`**, pas `scikit-learn` :
`statsmodels` affiche directement les coefficients et leur marge d'incertitude, ce qui manque à
`scikit-learn` sans travail supplémentaire — utile pour un livrable qui doit justifier chaque
chiffre.

**`deleted_detected_at` seul ne suffit pas à définir une suppression.** Un avis peut disparaître
puis revenir : sur 5 230 disparitions détectées, 509 concernent un avis qui revient. Deux causes
identifiées, corrigées dans `logistic-regression-study/sql/01_build_avis_deleted_panel.sql` :

- 24 sont un bug de collecte confirmé (même auteur, même note, même date, texte réécrit) — jamais
  une suppression ;
- le reste est tranché par la durée d'absence : 1 jour = raté de collecte (jamais compté), 2
  jours ou plus = vraie suppression, comptée à la première disparition.

**Les colonnes de vélocité ne sont pas des variables d'entrée du modèle.**
`jours_en_ligne_avant_suppression` et `jours_sous_surveillance_avant_suppression` ne sont connues
que pour un avis déjà supprimé — les utiliser en entrée reviendrait à prédire un événement avec
une information qu'on n'a qu'après qu'il s'est produit. Elles servent de statistique descriptive
dans le rapport. La variable de temps à utiliser dans le modèle est l'âge de l'avis à chaque
vague (`age_days`), connue à l'avance quelle que soit l'issue.

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
- Ne jamais faire figurer de nom d'auteur ou de lien d'avis dans une note de `etude-exploratoire/documentations/`.
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
d'analyse de l'étude d'origine vont dans `etude-exploratoire/documentations/`, datées, au format des
notes existantes. Les requêtes de la régression logistique vont dans
`logistic-regression-study/sql/`, une par fichier, commentées.
