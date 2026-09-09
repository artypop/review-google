# Histogramme de l'âge des avis supprimés

Date : 2026-09-08. Script : `etude-exploratoire/scripts/histogramme_age_suppressions.py`.
Objet : estimation large de la répartition par âge des suppressions, pour le mail à Axel.

Suivi : 14 vagues quotidiennes, 13 intervalles comparables (vagues 2 à 14).
Corpus : 4 877 534 avis de base, 4 747 suppressions retenues sur 5 230
disparitions brutes (correction des bugs d'édition et des ratés de collecte d'un jour, même
définition que `logistic-regression-study/sql/01_build_avis_deleted_panel.sql`).

L'âge d'un avis est compté depuis `created_at`, la date de publication donnée par Google.

---

## 1. Où tombent les suppressions — répartition par âge

Sur 100 avis supprimés, combien avaient tel âge au moment de leur suppression.

  moins de 1 mois      ############################################ 2 450
  1 à 3 mois           ########                                     453
  3 à 6 mois           ###                                          183
  6 à 12 mois          ####                                         223
  plus de 1 an         ##########################                   1 438

| Âge à la suppression | Suppressions (14 j) | Part | Projection sur 12 mois |
|---|---:|---:|---:|
| moins de 1 mois | 2 450 | 51,6 % | 68 788 |
| 1 à 3 mois | 453 | 9,5 % | 12 719 |
| 3 à 6 mois | 183 | 3,9 % | 5 138 |
| 6 à 12 mois | 223 | 4,7 % | 6 261 |
| plus de 1 an | 1 438 | 30,3 % | 40 375 |

Projection sur 12 mois = observé × 365 / 13, à volume et à comportement constants.
Ordre de grandeur seulement.

## 2. Risque de suppression par tranche d'âge

Même découpage, mais rapporté au nombre d'avis exposés. Une observation = un avis vivant à un
passage du robot.

| Âge de l'avis | Avis exposés | Observations | Suppressions | Risque par jour | Projection sur 12 mois |
|---|---:|---:|---:|---:|---:|
| moins de 1 mois | 101 392 | 907 588 | 2 450 | 0,2699 % | 62,72 % |
| 1 à 3 mois | 168 325 | 1 819 565 | 453 | 0,0249 % | 8,69 % |
| 3 à 6 mois | 205 046 | 2 358 227 | 183 | 0,0078 % | 2,79 % |
| 6 à 12 mois | 361 092 | 4 355 169 | 223 | 0,0051 % | 1,85 % |
| plus de 1 an | 4 147 161 | 53 708 075 | 1 438 | 0,0027 % | 0,97 % |

Lecture de la projection : elle suppose que l'avis reste toute l'année dans sa tranche. Vrai
seulement pour « plus de 1 an ». Pour les tranches plus jeunes, l'avis vieillit et change de
tranche en cours de route : le chiffre répond à « et si le risque de cette tranche durait un
an », pas à « que devient un avis de cet âge sur un an ».

## 3. Contrôle de censure — cohorte présente à la vague 1

Les avis apparus pendant le suivi sont observés moins longtemps que les autres. Ce tableau les
écarte : tous les avis comptés ici ont été suivis les 14 jours complets.

| Âge au 11 août | Avis | Suppressions | Part supprimée en 14 j |
|---|---:|---:|---:|
| moins de 1 mois | 72 725 | 1 664 | 2,288 % |
| 1 à 3 mois | 138 261 | 371 | 0,268 % |
| 3 à 6 mois | 178 633 | 147 | 0,082 % |
| 6 à 12 mois | 340 449 | 201 | 0,059 % |
| plus de 1 an | 4 114 047 | 1 391 | 0,034 % |

## 4. Risque cumulé sur le premier mois de vie d'un avis

Un avis ne passe pas un an dans la tranche « moins de 1 mois » : il en sort en vieillissant. Le
chiffre utile pour un avis neuf est donc le risque cumulé sur ses 30 premiers jours, obtenu en
enchaînant les probabilités de survie de chaque jour d'âge.

**7,65 % des avis neufs sont supprimés dans leurs 30 premiers jours** (risque
cumulé, jours d'âge 0 à 29).

Le détail jour par jour est dans `2026-09-08-age-a-la-suppression.md`.

Le chiffre de 7,65 % enchaîne des risques quotidiens mesurés sur 13 jours pour
couvrir 30 jours d'âge. Il est sensible au pic de 7-13 jours : si ce pic est un accident de la
fenêtre observée, le cumul baisse d'autant.

Ce pic est isolé jour par jour dans `2026-09-08-age-a-la-suppression.md` : il tombe à 7 jours de
vie exactement, avec 449 suppressions contre 279 à 6 jours et 118 à 8 jours.

## 5. Contrôle — la répartition sans les fiches attaquées

4 fiches portent la signature d'une attaque par avis négatifs — au moins
10 suppressions, presque toutes à 1 étoile, presque toutes sur des avis écrits dans le mois —
soit
385 suppressions (8,1 % du total).
Tableau 1 recalculé sans elles :

| Âge à la suppression | Suppressions | Part |
|---|---:|---:|
| moins de 1 mois | 2 070 | 47,5 % |
| 1 à 3 mois | 451 | 10,3 % |
| 3 à 6 mois | 183 | 4,2 % |
| 6 à 12 mois | 223 | 5,1 % |
| plus de 1 an | 1 435 | 32,9 % |

## Limites à dire à Axel

- 14 jours d'observation. Toute projection annuelle suppose que ces 14 jours sont représentatifs.
  Rien ne le garantit : une vague de purge tombée dans la fenêtre gonflerait tout, une fenêtre
  calme sous-estimerait tout.
- Les suppressions sont très concentrées : 85,4 % des
  établissements n'en ont aucune, et les 4 fiches ayant perdu plus de 5 % de leurs
  avis portent 8,1 % du total. Un taux moyen ne décrit aucun établissement en
  particulier.
- Le jour d'âge 0 est absent du cumul du § 4 : un avis n'est comparable qu'à partir du passage
  qui suit celui où le robot l'a découvert, donc son premier jour d'exposition est le jour 1.
  Ce qui se passe dans les vingt-quatre premières heures d'un avis n'est pas mesuré ici.
- L'âge vient de `created_at`, la date de publication annoncée par Google. Un avis réédité garde
  sa date de publication d'origine.
- Les tranches sont des tranches d'âge à la date du passage du robot, pas des cohortes suivies
  dans le temps. Un même avis peut apparaître dans deux tranches si son anniversaire tombe
  pendant les 14 jours ; c'est marginal sauf à la frontière du mois.

## Fichiers produits

- `data/resultats/histogramme_age_suppressions.csv` (gitignoré) — tableaux 1 à 3 fusionnés.
