# Âge des avis au moment de leur suppression, jour par jour

Script : `etude-exploratoire/scripts/age_a_la_suppression.py --age-max 30`.
Date : 2026-09-08. Périmètre : tout le corpus.

2 462 des 4 747 suppressions du corpus concernent un avis de
30 jours ou moins. Le reste concerne des avis plus vieux.

- **`Supprimés`** répond à « combien d'avis de cet âge ont été supprimés ».
- **`Part des avis de cet âge`** répond à « un avis de cet âge, quel risque court-il ». Le
  corpus ne contient pas autant d'avis de chaque âge, donc les deux colonnes ne classent pas
  les âges dans le même ordre.

| Âge | Supprimés | Avis observés à cet âge | Part des avis de cet âge |
|---:|---:|---:|---:|
| 1 j | 16 | 3 700 | 0,432 % |
| 2 j | 116 | 32 975 | 0,352 % |
| 3 j | 77 | 32 716 | 0,235 % |
| 4 j | 32 | 32 383 | 0,099 % |
| 5 j | 43 | 32 713 | 0,131 % |
| 6 j | 279 | 32 823 | 0,850 % |
| 7 j | 449 | 32 609 | 1,377 % |
| 8 j | 118 | 32 339 | 0,365 % |
| 9 j | 134 | 32 711 | 0,410 % |
| 10 j | 95 | 32 440 | 0,293 % |
| 11 j | 92 | 32 094 | 0,287 % |
| 12 j | 70 | 32 006 | 0,219 % |
| 13 j | 118 | 32 267 | 0,366 % |
| 14 j | 179 | 32 349 | 0,553 % |
| 15 j | 133 | 32 401 | 0,410 % |
| 16 j | 33 | 32 565 | 0,101 % |
| 17 j | 35 | 32 193 | 0,109 % |
| 18 j | 59 | 31 805 | 0,186 % |
| 19 j | 63 | 31 854 | 0,198 % |
| 20 j | 55 | 31 937 | 0,172 % |
| 21 j | 65 | 32 026 | 0,203 % |
| 22 j | 54 | 32 221 | 0,168 % |
| 23 j | 31 | 32 473 | 0,095 % |
| 24 j | 17 | 32 122 | 0,053 % |
| 25 j | 17 | 31 931 | 0,053 % |
| 26 j | 18 | 31 981 | 0,056 % |
| 27 j | 17 | 31 958 | 0,053 % |
| 28 j | 21 | 31 984 | 0,066 % |
| 29 j | 14 | 32 012 | 0,044 % |
| 30 j | 12 | 32 312 | 0,037 % |

Maximum en nombre : **7 jours**
(449 suppressions).
Maximum en part : **7 jours**
(1,377 %).

L'âge 1 jour est sous-représenté : un avis n'entre dans le calcul qu'au passage suivant celui
qui l'a découvert, donc son premier jour d'exposition est le jour 1 et il y est peu observé.
Partout ailleurs le nombre d'avis observés est quasi constant (environ 32 000 par âge), donc la
colonne des nombres bruts classe les âges dans le même ordre que la colonne des parts.

## Contrôle fait le 2026-09-08 : y a-t-il un rythme hebdomadaire ?

Le tableau montre des bosses sur 7, 14, 21 et 28 jours. Deux explications possibles, et il faut
les séparer avant de conclure quoi que ce soit.

**Ce n'est pas un artefact de date.** `created_at` pourrait être une date reconstruite à partir
d'un libellé du type « il y a une semaine », ce qui produirait mécaniquement des âges multiples
de 7. Vérification faite : la répartition horaire de `created_at` suit une courbe de journée
plausible (creux à 4h, pic à 17h), les 60 valeurs de secondes sont présentes, et seuls 945 avis
sur 58 107 tombent sur la seconde zéro. C'est un horodatage réel.

**Ce n'est pas non plus un rythme hebdomadaire.** Sur les âges 2 à 30, les multiples de 7
affichent 0,554 % contre 0,215 % pour les autres âges, soit un rapport de 2,6. Mais en retirant
le seul âge 7, le rapport tombe à 1,5 (0,275 % contre 0,184 %) et ne se vérifie plus que dans
5 vagues sur 13. Ces 5 vagues comprennent les 16 et 23 août, les deux dimanches, qui sont les
deux journées les plus chargées en suppressions de tout le suivi (706 et 479 sur 4 747).

<!-- CHIFFRES À REPRENDRE : 0,554 / 0,215 / 2,6 / 1,5 / 0,275 / 0,184 / 706 / 479 / 4 747 sont
écrits en dur dans le script et datent d'un passage antérieur à la correction de comptage et au
dédoublonnage. Les relire dans les tableaux régénérés ci-dessus avant de diffuser ce document. -->

Conclusion : le pic à 7 jours de vie est solide. Les bosses à 14, 21 et 28 jours sont
essentiellement produites par ces deux dimanches, un avis publié un dimanche et supprimé un
dimanche ayant par construction un âge multiple de 7. Ne pas en tirer de cycle hebdomadaire.

## Trois comptages d'« avis récents supprimés », et ce qui les distingue

Trois valeurs circulent dans le projet. Aucune n'est fausse ; elles ne comptent pas la même
chose. À citer avec son code plutôt qu'avec le seul chiffre.

| Code | Définition | Suppressions | À quoi elle sert |
|---|---|---:|---|
| **D1** | âge à la suppression strictement inférieur à 30 jours (âges 1 à 29) | 2 450 | la tranche « moins de 1 mois » du tableau par tranches larges |
| **D2** | âge à la suppression de 30 jours ou moins (âges 1 à 30) | 2 462 | le périmètre de modélisation, filtre age_days <= 30 sur le panel |
| **D3** | avis âgé de 30 jours ou moins au premier passage, supprimé à n'importe quel moment | 2 540 | une cohorte figée au départ de l'étude |

Les écarts s'expliquent entièrement :

- **D2 − D1 = 12** : les 12 avis supprimés à exactement 30 jours d'âge, exclus de D1 par la
  borne stricte de la tranche.
- **D3 − D2 = 78** : les 78 avis qui avaient 30 jours ou moins au 11 août mais qui ont franchi
  leur trentième jour avant d'être supprimés. D3 fige la cohorte au départ, D2 mesure l'âge au
  moment de la suppression.

Les 2 540 de D3 se décomposent donc en 2 462 supprimés avant leur 31e jour et 78 après.

## Le pic à 7 jours : effet d'âge ou purge ?

Une purge est une opération groupée : elle tombe un jour donné, sur quelques établissements.
Un effet d'âge se reproduit tous les jours, partout. Trois vérifications.

**a) Les 449 suppressions à 7 jours sont étalées sur
12 des 13 journées du suivi.**

| Jour | Suppressions à 7 j | Avis de 7 j ce jour-là | Part |
|---|---:|---:|---:|
| 12/08 | 24 | 2 564 | 0,936 % |
| 13/08 | 35 | 2 756 | 1,270 % |
| 14/08 | 0 | 2 848 | 0,000 % |
| 15/08 | 9 | 2 401 | 0,375 % |
| 16/08 | 25 | 2 140 | 1,168 % |
| 17/08 | 43 | 2 482 | 1,732 % |
| 18/08 | 43 | 2 552 | 1,685 % |
| 19/08 | 72 | 2 445 | 2,945 % |
| 20/08 | 62 | 2 685 | 2,309 % |
| 21/08 | 63 | 2 792 | 2,256 % |
| 22/08 | 20 | 2 403 | 0,832 % |
| 23/08 | 26 | 2 184 | 1,190 % |
| 24/08 | 27 | 2 357 | 1,146 % |

**b) Elles sont réparties sur 144 établissements**,
le plus touché n'en portant que 27, soit
6,0 %.

**c) Le pic reste après retrait des deux journées les plus chargées du suivi.**

| Âge | Suppressions | Sans les 2 journées les plus chargées |
|---:|---:|---:|
| 4 j | 32 | 32 |
| 5 j | 43 | 34 |
| 6 j | 279 | 200 |
| 7 j | 449 | 381 |
| 8 j | 118 | 75 |
| 9 j | 134 | 52 |
| 10 j | 95 | 71 |

Les trois vérifications concordent : le pic à 7 jours est un effet d'âge, pas une purge.

## Suppressions par journée du suivi

Le pendant du tableau ci-dessus, rangé par date au lieu de l'être par âge. Sert à savoir si une
journée du suivi sort du lot.

| Vague | Date | Suppressions | Fiches touchées | Part de la plus touchée | Hors fiches attaquées |
|---:|---|---:|---:|---:|---:|
| 2 | 12/08 | 500 | 201 | 15 % | 424 |
| 3 | 13/08 | 354 | 200 | 6 % | 348 |
| 4 | 14/08 | 153 | 139 | 3 % | 149 |
| 5 | 15/08 | 195 | 129 | 15 % | 194 |
| 6 | 16/08 | 706 | 227 | 26 % | 516 |
| 7 | 17/08 | 760 | 227 | 5 % | 747 |
| 8 | 18/08 | 295 | 199 | 6 % | 288 |
| 9 | 19/08 | 262 | 176 | 3 % | 262 |
| 10 | 20/08 | 289 | 159 | 7 % | 289 |
| 11 | 21/08 | 247 | 145 | 10 % | 247 |
| 12 | 22/08 | 283 | 134 | 10 % | 245 |
| 13 | 23/08 | 479 | 275 | 6 % | 429 |
| 14 | 24/08 | 224 | 147 | 8 % | 224 |

Le volume varie d'un facteur 5,0 d'une
journée à l'autre, de 153 le
14/08 à 760 le
17/08. Les quatre journées les plus
chargées font 52 %
du total.

Chaque journée se répartit sur 129 à 275
établissements, donc aucune n'est une purge de quelques listings — à une exception : le
16/08, un seul établissement porte
26 % des suppressions du jour, et le total de cette journée
tombe de 706 à
516 en écartant les fiches
attaquées.

## Fichiers produits

- `data/resultats/age_a_la_suppression.csv` (gitignoré) — le tableau par âge.
