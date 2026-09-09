---
date: 2026-09-04
projet: reviewflowz-analyse-google
titre: "Premières observations sur l'export vagues 1-14"
---

# Premières observations sur l'export vagues 1-14

> ## PÉRIMÉ — déplacé le 2026-09-08
>
> Les résultats chiffrés de ce document sont calculés sur le comptage d'avant la correction des
> suppressions (résurrections et bugs d'édition non retirés). Ses verdicts en dépendent, donc
> **aucun de ses chiffres ne doit être cité ni communiqué**.
>
> Comptage de référence aujourd'hui : **4 747 suppressions** sur 5 230 disparitions brutes.
> Définition : `../../scripts/suppressions_corrigees.py`.
> Résultats à jour : `../2026-09-08-synthese-de-la-journee.md` et `../INDEX.md`.
>
> Le document est conservé pour sa méthode, ses pièges documentés et ses questions ouvertes.

Observations produites en lisant `local/exports.zip` (hors dépôt, gitignoré) et son
`exports/README.md`. Tous les comptages portent sur les lignes de base — filtre
`NOT is_update` — soit **4 878 151 avis** et **5 230 suppressions**, taux d'ensemble
**0,107 %**. Les 5 314 du README incluent des lignes de version.

## Ce que l'export contient

14 vagues quotidiennes du 11 au 24 août 2026, recensement complet du listing à chaque passage.
9 048 établissements échantillonnés par groupe : 3 336 `mono`, 2 856 `small` (4-10 sites),
2 856 `large` (20-50). Sept secteurs à 1 428 établissements, sauf `travel` à 480. 41 pays, dont
un seul hors Europe (US) ; le Royaume-Uni est absent.

## Premières observations bivariées

### Note : effet non monotone, et le chiffre GMBapi s'effondre

| Note | Avis | Supprimés | Taux |
|---|---:|---:|---:|
| 1 étoile | 313 589 | 994 | 0,317 % |
| 2 étoiles | 118 596 | 131 | 0,110 % |
| 3 étoiles | 249 156 | 119 | 0,048 % |
| 4 étoiles | 694 451 | 241 | 0,035 % |
| 5 étoiles | 3 502 359 | 3 745 | 0,107 % |

Les 1 étoile sont supprimés trois fois plus que la moyenne et **neuf fois plus que les
4 étoiles**. La note la plus sûre est 4, pas une extrémité.

Surtout : 71,6 % des suppressions portent sur des 5 étoiles, mais les 5 étoiles sont 71,8 % du
panel. Le « 73 % des suppressions concernent des 5 étoiles » de GMBapi ne mesure donc aucun
ciblage — c'est la composition de la base. Première croyance du marché infirmée par les
données, en une requête.

### Auteur Local Guide : l'effet le plus fort observé à ce stade

| Auteur | Avis | Supprimés | Taux |
|---|---:|---:|---:|
| Local Guide | 2 498 805 | 1 384 | 0,055 % |
| Non Local Guide | 2 379 346 | 3 846 | 0,162 % |

Facteur 2,9. À confronter au niveau 2 : le statut Local Guide est corrélé au nombre d'avis
publiés, donc une partie de l'effet peut passer par l'ancienneté du compte.

### Texte : présence et longueur

| Contenu | Avis | Supprimés | Taux |
|---|---:|---:|---:|
| Sans texte (note seule) | 1 708 497 | 1 350 | 0,079 % |
| Avec texte | 3 169 654 | 3 880 | 0,122 % |
| — 1 à 50 caractères | 789 394 | 800 | 0,101 % |
| — 51 à 150 | 1 110 234 | 1 401 | 0,126 % |
| — 151 à 400 | 868 713 | 1 100 | 0,127 % |
| — plus de 400 | 401 313 | 579 | 0,144 % |

Le risque croît avec la longueur, mais l'écart reste faible — 0,10 % à 0,14 % — bien loin du
facteur 3 du statut Local Guide.

### Photo : effet quasi nul

Avec photo 0,088 % (263 sur 300 129), sans photo 0,108 % (4 967 sur 4 578 022). L'écart ne
justifie probablement pas de retenir la caractéristique seule, mais elle reste candidate en
interaction.

## Ce que la rareté change pour la modélisation

Le taux de 0,107 % n'empêche pas la régression logistique : ce qui compte est le nombre
d'événements, et 5 230 en autorise une centaine de paramètres à raison d'une dizaine
d'événements par paramètre. Quatre points de mise en œuvre :

1. **Coût de calcul** — sous-échantillonner les négatifs (un pour vingt) donne les mêmes odds
   ratios ; seule la constante est décalée et se corrige analytiquement si des probabilités
   absolues sont nécessaires.
2. **Présentation** — les probabilités prédites vaudront toutes ~0,1 %, inexploitables pour le
   client. Les résultats se donnent en risque relatif.
3. **Évaluation** — l'exactitude est inutilisable : prédire « jamais supprimé » atteint
   99,89 %. AUC et calibration.
4. **Sous-groupes** — les 19 cellules secteur × taille vont de 63 à 1 557 événements, quatre
   cellules `mono` sous 100 (`hospitality/mono` à 63). Les interactions y seront mal estimées.
   Le random forest du niveau 3 est bien plus exposé à cette rareté que la régression.

Répartition des suppressions : par secteur, `home_services` 2 135, `wellness_fitness` 855,
`healthcare` 603, `automotive` 519, `food_beverage` 495, `hospitality` 390, `travel` 233. Par
taille, `large` 3 048, `small` 1 393, `mono` 789 — à rapporter au volume d'avis de chaque
strate avant toute lecture.

## Quatre pièges du dataset

1. **`review_id` n'est pas unique.** 2 012 lignes de version après édition (`is_update`) et
   617 résurrections d'avis supprimés puis réapparus. L'état vivant s'obtient avec
   `NOT is_update AND deleted_detected_at IS NULL`. Un `count(*)` brut surestime.
2. **Les URL de photos sont resignées à chaque collecte.** Les comparer d'une vague à l'autre
   fait voir un changement sur tous les avis avec photo, en permanence. Elles ne sont pas un
   signal.
3. **L'histogramme se met à jour avant le listing.** Dater une suppression sur la baisse de
   `histograms.total` la place une à deux vagues trop tôt et compte des suppressions qui n'ont
   pas eu lieu. Le listing est la source de vérité.
4. **Données personnelles.** `reviewer_name`, `reviewer_avatar`, `review_link` et `text`
   identifient des personnes. Le README impose de ne pas rediffuser et de retirer les colonnes
   auteur si l'analyse s'en passe.

## Restes à instruire

Le panel ne couvre ni les groupes de 2-3 sites ni ceux de 11-19 : l'effet de taille
s'interprète sur trois paliers, pas comme une courbe continue.

L'hypothèse du cadrage selon laquelle Google filtre les insultes avant publication est
vérifiable maintenant, sur les 3,17 M de textes non vides.

Les variables d'établissement du cadrage absentes de l'export — adresse, téléphone, complétion
de la fiche — sont abandonnées. La note moyenne se reconstruit depuis `histograms`, avec en
prime sa trajectoire sur les 14 vagues.
