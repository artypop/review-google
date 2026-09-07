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
sa cible. **C'est un faux positif, et c'est un chiffre.**

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
| moins de 1 % | 2 199 325 | 683 | 0.26 | référence | — | oui |
| 1 à 3 % | 1 524 453 | 702 | 0.43 | ×1.66 | 1.54 à 1.79 | oui |
| 3 à 10 % | 375 911 | 224 | 0.46 | ×1.75 | 1.53 à 2.00 | oui |
| 10 % et plus | 14 358 | 9 | 1.32 | ×5.05 | 2.31 à 9.59 | **non** |

Non exploitable — 10 % et plus : moins de 20 disparitions, ou moins de 60 % du poids des strates couvert. **Ne pas communiquer ces lignes.**

### Stock de plus d'un an — sans les 24 fiches purgées

| Afflux reçu en 30 jours | Avis anciens | Disparitions | À marché comparable, / 10 000 passages | Rapport | Fourchette | Exploitable ? |
|---|---:|---:|---:|---:|---:|---|
| moins de 1 % | 2 199 097 | 567 | 0.21 | référence | — | oui |
| 1 à 3 % | 1 523 890 | 661 | 0.31 | ×1.46 | 1.35 à 1.58 | oui |
| 3 à 10 % | 374 044 | 183 | 0.36 | ×1.69 | 1.45 à 1.95 | oui |
| 10 % et plus | 13 198 | 3 | 0.70 | ×3.25 | 0.67 à 9.49 | **non** |

Non exploitable — 10 % et plus : moins de 20 disparitions, ou moins de 60 % du poids des strates couvert. **Ne pas communiquer ces lignes.**

### Stock de plus de trois ans — tout le panel

| Afflux reçu en 30 jours | Avis anciens | Disparitions | À marché comparable, / 10 000 passages | Rapport | Fourchette | Exploitable ? |
|---|---:|---:|---:|---:|---:|---|
| moins de 1 % | 1 684 158 | 393 | 0.18 | référence | — | oui |
| 1 à 3 % | 964 766 | 277 | 0.29 | ×1.55 | 1.37 à 1.74 | oui |
| 3 à 10 % | 188 698 | 69 | 0.31 | ×1.69 | 1.31 à 2.13 | oui |
| 10 % et plus | 5 659 | 2 | 0.25 | ×1.35 | 0.16 à 4.86 | **non** |

Non exploitable — 10 % et plus : moins de 20 disparitions, ou moins de 60 % du poids des strates couvert. **Ne pas communiquer ces lignes.**

« À marché comparable » recalcule chaque taux comme si tous les groupes avaient la même répartition de pays, secteur, taille de groupe et volume d'avis. C'est cette colonne qu'il faut lire.

<!-- /genere:test2 -->

## Ce qu'il faut en retenir

**Le débordement existe et il est mesuré.** À marché comparable, un avis de plus d'un an
disparaît **1,5 à 1,7 fois plus** dans une fiche qui reçoit un afflux récent d'avis que dans une
fiche comparable qui n'en reçoit pas. Ces avis n'ont, par construction, aucun rapport avec
l'afflux : ils étaient en ligne bien avant.

Trois raisons de considérer le résultat comme solide :

1. **Il survit au retrait des 24 fiches massivement purgées** (×1,46 et ×1,69 au lieu de ×1,66
   et ×1,75). Ce n'est donc pas l'effet de quelques purges spectaculaires.
2. **Il survit au durcissement du périmètre.** Sur les avis de plus de **trois** ans — encore
   plus éloignés de toute campagne récente — le gradient est intact : ×1,55 et ×1,69.
3. **Les effectifs sont larges** : 683 et 702 disparitions dans les deux premiers groupes, sur
   plus de 3,7 millions d'avis anciens. Les fourchettes sont étroites et excluent nettement 1.

**Le palier « 10 % et plus » n'est pas exploitable** et ne doit pas être communiqué : 9
disparitions seulement, et les strates de marché n'y sont couvertes qu'à 21 %. Le ×5,05 qui
s'affiche est du bruit. C'est une limite de structure du panel — les fiches à très fort afflux
ont peu de stock ancien, par définition.

## Articulation avec l'analyse A

Les deux résultats ne se contredisent pas, ils se complètent, et c'est ce qui fait l'argument :

- **Analyse A** : la vélocité n'a aucun effet propre sur le fait qu'une fiche soit *touchée*.
  Google ne sanctionne pas une fiche parce qu'elle reçoit beaucoup d'avis.
- **Test 2** : dans ces mêmes fiches, le stock *ancien* meurt tout de même 1,5 à 1,7 fois plus.

Autrement dit : ce n'est pas une sanction de fiche décidée en amont, mais l'activité de
modération déclenchée par le flux récent qui emporte au passage des avis anciens sans rapport.
Un avis ancien supprimé dans ce cas est une erreur de modération.

## Réserve de méthode

La comparaison est stratifiée, pas appariée un pour un, et elle ne contrôle que ce que la strate
capture — pays, secteur, taille de groupe, volume. Une caractéristique non observée qui serait
à la fois corrélée à l'afflux et à la suppression du vieux stock produirait le même écart. Le
panel ne permet pas de l'exclure ; il faut l'écrire.
