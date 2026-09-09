---
date: 2026-09-06
projet: reviewflowz-analyse-google
titre: "Test 2 — la modération déborde-t-elle sur le stock ancien ?"
statut: résultats
---

# Test 2 — la modération déborde-t-elle sur le stock ancien ?

Produit par `scripts/test2_debordement.py`.

## La question, et pourquoi c'est celle qui porte le livrable

Un avis publié il y a plus d'un an n'a aucun rapport avec une campagne d'avis lancée le mois
dernier. Si Google le supprime davantage dans les fiches qui reçoivent un afflux récent que
dans des fiches comparables sans afflux, alors la modération emporte des avis sans rapport avec
sa cible. Un avis supprimé dans ce cas est une erreur de modération.

C'est le seul endroit de l'étude où l'angle du livrable devient une mesure plutôt qu'une
inférence indirecte.

## Ce qui est comparé

- **Le stock ancien** : avis créés plus de 365 jours avant la vague 1, et déjà présents à la
  vague 1. La seconde condition écarte la censure à droite — tous les avis retenus sont observés
  sur les mêmes treize intervalles entre passages.
- **Groupés par afflux reçu** : la part du stock que la fiche a reçue dans les 30 derniers jours.
- **À marché comparable** : chaque taux est recalculé comme si tous les groupes avaient la même
  répartition de pays, secteur, taille de groupe et volume. Sans cette correction, on mesurerait
  surtout que les fiches à fort afflux sont américaines et dans les services à domicile.

## Ce que le test ne prouve pas

- Une association, pas une causalité. Les fiches à fort afflux peuvent différer par autre chose
  que ce que la strate capture.
- Un avis ancien supprimé n'est pas nécessairement légitime : un faux avis ancien reste possible.
  L'argument est probabiliste — il porte sur un écart entre groupes comparables, pas sur le
  statut d'un avis donné.
- Le sens de la vélocité est lui-même en cause : l'analyse A a montré qu'elle n'a **aucun effet
  propre** sur le risque qu'une fiche soit touchée. Ce test porte sur une autre grandeur, le
  stock ancien, et se lit indépendamment.

## Résultats

<!-- genere:test2 — regenere par scripts/test2_debordement.py, ne pas editer a la main -->

### Stock de plus d'un an — tout le panel

| Afflux reçu en 30 jours | Avis anciens | Disparitions | À marché comparable, / 10 000 passages | Rapport | Fourchette | Exploitable ? |
|---|---:|---:|---:|---:|---:|---|
| moins de 1 % | 2 199 325 | 555 | 0.21 | référence | — | oui |
| 1 à 3 % | 1 524 453 | 643 | 0.30 | ×1.46 | 1.35 à 1.57 | oui |
| 3 à 10 % | 375 892 | 184 | 0.37 | ×1.76 | 1.51 à 2.03 | oui |
| 10 % et plus | 14 377 | 9 | 1.32 | ×6.32 | 2.89 à 11.99 | **non** |

Non exploitable — 10 % et plus : moins de 20 disparitions, ou moins de 60 % du poids des strates couvert. **Ne pas communiquer ces lignes.**

### Stock de plus d'un an — sans les fiches attaquées

| Afflux reçu en 30 jours | Avis anciens | Disparitions | À marché comparable, / 10 000 passages | Rapport | Fourchette | Exploitable ? |
|---|---:|---:|---:|---:|---:|---|
| moins de 1 % | 2 199 325 | 555 | 0.21 | référence | — | oui |
| 1 à 3 % | 1 515 967 | 642 | 0.31 | ×1.46 | 1.35 à 1.58 | oui |
| 3 à 10 % | 374 870 | 184 | 0.37 | ×1.76 | 1.52 à 2.04 | oui |
| 10 % et plus | 13 416 | 7 | 1.32 | ×6.31 | 2.54 à 12.99 | **non** |

Non exploitable — 10 % et plus : moins de 20 disparitions, ou moins de 60 % du poids des strates couvert. **Ne pas communiquer ces lignes.**

### Stock de plus de trois ans — tout le panel

| Afflux reçu en 30 jours | Avis anciens | Disparitions | À marché comparable, / 10 000 passages | Rapport | Fourchette | Exploitable ? |
|---|---:|---:|---:|---:|---:|---|
| moins de 1 % | 1 684 158 | 315 | 0.15 | référence | — | oui |
| 1 à 3 % | 964 766 | 244 | 0.19 | ×1.27 | 1.12 à 1.44 | oui |
| 3 à 10 % | 188 693 | 51 | 0.20 | ×1.39 | 1.04 à 1.83 | oui |
| 10 % et plus | 5 664 | 2 | 0.25 | ×1.70 | 0.21 à 6.12 | **non** |

Non exploitable — 10 % et plus : moins de 20 disparitions, ou moins de 60 % du poids des strates couvert. **Ne pas communiquer ces lignes.**

« À marché comparable » recalcule chaque taux comme si tous les groupes avaient la même répartition de pays, secteur, taille de groupe et volume d'avis. C'est cette colonne qu'il faut lire.

<!-- /genere:test2 -->
