---
date: 2026-09-06
projet: reviewflowz-analyse-google
titre: "Premiers résultats, facteur par facteur"
statut: résultats
---

# Premiers résultats, facteur par facteur

Sur les **104 083 avis de moins de 30 jours** du panel, dont **2 637 ont été
supprimés** pendant les quatorze jours de collecte.

Tableaux produits par `scripts/level1_bivariate.py`. Ils remplacent ceux de la note du
4 septembre, qui comparaient des avis d'âges différents et donnaient des résultats faussés.

## Comment lire ces tableaux

**Le risque quotidien.** Chaque avis a été observé à chaque passage du robot. La question posée
est : à ce passage, est-il encore là ? Le risque est la part d'avis qui disparaissent d'un
passage au suivant. Un risque de 0,5 % veut dire : sur 1 000 avis en ligne, 5 auront disparu au
passage suivant.

Ce n'est pas la probabilité qu'un avis finisse par être supprimé — celle-là s'accumule sur
plusieurs jours et elle est bien plus élevée.

**Les colonnes.**

- *Observations* : le nombre de fois où un avis a été vérifié. Un avis vu à dix passages compte
  pour dix. C'est ce qui permet de comparer équitablement des avis suivis plus ou moins
  longtemps.
- *Disparitions* : le nombre d'avis effectivement supprimés.
- *Risque brut* : disparitions divisées par observations.
- *Risque à âge comparable* : le même calcul, mais refait tranche d'âge par tranche d'âge, puis
  recombiné comme si tous les groupes avaient la même répartition d'âge. **C'est la colonne à
  lire.**
- *Écart* : le rapport entre le risque du groupe et celui de la ligne de référence, signalée en
  gras. « ×2 » se lit « deux fois plus supprimé ».

**Quand les deux colonnes de risque diffèrent, l'écart entre elles mesure exactement ce que la
différence d'âge apportait.** Une ligne signalée « trop peu pour conclure » compte moins de
20 disparitions.

**Ce que ces tableaux ne font pas.** Ils regardent un facteur à la fois. Deux facteurs liés — par
exemple le niveau Local Guide et le nombre d'avis de l'auteur — se comptent donc deux fois. Il
faut les modèles A et B pour savoir lequel compte vraiment. Aucune marge d'erreur n'est donnée
ici : elle serait trompeuse tant que le regroupement par établissement n'est pas traité, ce que
seuls les modèles font.

## Résultats

<!-- genere:level1 — regenere par scripts/level1_bivariate.py, ne pas editer a la main -->
### Note

| | Observations | Disparitions | Risque brut | Risque à âge comparable | Écart | Écart hors fiches attaquées |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 73 813 | 634 | 0.859 % | 0.841 % | ×9.19 | ×3.98 |
| 2 | 25 505 | 51 | 0.200 % | 0.197 % | ×2.15 | ×1.69 |
| 3 | 36 545 | 24 | 0.066 % | 0.065 % | ×0.71 | ×0.68 |
| **4** (réf.) | 95 922 | 89 | 0.093 % | 0.091 % | réf. | réf. |
| 5 | 902 526 | 1 839 | 0.204 % | 0.205 % | ×2.24 | ×2.25 |

### Présence de texte

| | Observations | Disparitions | Risque brut | Risque à âge comparable | Écart | Écart hors fiches attaquées |
|---|---:|---:|---:|---:|---:|---:|
| avec texte | 825 400 | 1 857 | 0.225 % | 0.225 % | ×0.89 | ×1.21 |
| **note seule** (réf.) | 308 911 | 780 | 0.252 % | 0.252 % | réf. | réf. |

### Longueur du texte

| | Observations | Disparitions | Risque brut | Risque à âge comparable | Écart | Écart hors fiches attaquées |
|---|---:|---:|---:|---:|---:|---:|
| **a. note seule** (réf.) | 308 911 | 780 | 0.252 % | 0.252 % | réf. | réf. |
| b. 1-50 | 162 940 | 411 | 0.252 % | 0.253 % | ×1.00 | ×1.28 |
| c. 51-150 | 282 543 | 652 | 0.231 % | 0.232 % | ×0.92 | ×1.25 |
| d. 151-400 | 238 369 | 507 | 0.213 % | 0.212 % | ×0.84 | ×1.19 |
| e. 400+ | 141 548 | 287 | 0.203 % | 0.202 % | ×0.80 | ×1.11 |

### Photos jointes

| | Observations | Disparitions | Risque brut | Risque à âge comparable | Écart | Écart hors fiches attaquées |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 46 625 | 69 | 0.148 % | 0.151 % | ×0.62 | ×0.65 |
| 2+ | 58 078 | 57 | 0.098 % | 0.099 % | ×0.41 | ×0.47 |
| **aucune** (réf.) | 1 029 608 | 2 511 | 0.244 % | 0.244 % | réf. | réf. |

### Réponse du propriétaire

| | Observations | Disparitions | Risque brut | Risque à âge comparable | Écart | Écart hors fiches attaquées |
|---|---:|---:|---:|---:|---:|---:|
| avec réponse | 616 730 | 1 315 | 0.213 % | 0.216 % | ×0.88 | ×0.80 |
| **sans réponse** (réf.) | 517 581 | 1 322 | 0.255 % | 0.246 % | réf. | réf. |

### Langue hors langue dominante de la fiche

| | Observations | Disparitions | Risque brut | Risque à âge comparable | Écart | Écart hors fiches attaquées |
|---|---:|---:|---:|---:|---:|---:|
| **langue locale** (réf.) | 1 038 239 | 2 521 | 0.243 % | 0.243 % | réf. | réf. |
| langue étrangère | 96 072 | 116 | 0.121 % | 0.120 % | ×0.49 | ×0.53 |

### Avis édité depuis publication

| | Observations | Disparitions | Risque brut | Risque à âge comparable | Écart | Écart hors fiches attaquées |
|---|---:|---:|---:|---:|---:|---:|
| **non édité** (réf.) | 1 053 166 | 2 350 | 0.223 % | 0.222 % | réf. | réf. |
| édité | 81 145 | 287 | 0.354 % | 0.357 % | ×1.61 | ×1.75 |

### Niveau Local Guide

| | Observations | Disparitions | Risque brut | Risque à âge comparable | Écart | Écart hors fiches attaquées |
|---|---:|---:|---:|---:|---:|---:|
| a. absent | 46 953 | 367 | 0.782 % | 0.692 % | ×2.66 | ×2.32 |
| **b. 1-3** (réf.) | 705 277 | 1 781 | 0.253 % | 0.261 % | réf. | réf. |
| c. 4-5 | 257 523 | 415 | 0.161 % | 0.162 % | ×0.62 | ×0.67 |
| d. 6+ | 124 558 | 74 | 0.059 % | 0.060 % | ×0.23 | ×0.26 |

### Signature compte neuf (niveau absent + compteur 0)

| | Observations | Disparitions | Risque brut | Risque à âge comparable | Écart | Écart hors fiches attaquées |
|---|---:|---:|---:|---:|---:|---:|
| **autre** (réf.) | 1 088 866 | 2 280 | 0.209 % | 0.214 % | réf. | réf. |
| compte neuf | 45 445 | 357 | 0.786 % | 0.583 % | ×2.73 | ×2.19 |

Le recalcul à âge comparable déplace nettement le chiffre : compte neuf (0.786 % → 0.583 %). Une partie de l'effet apparent n'était que de la différence d'âge.

### Nombre d'avis de l'auteur

| | Observations | Disparitions | Risque brut | Risque à âge comparable | Écart | Écart hors fiches attaquées |
|---|---:|---:|---:|---:|---:|---:|
| a. compteur 0 | 130 841 | 695 | 0.531 % | 0.446 % | ×1.97 | ×1.43 |
| b. 1-2 | 257 811 | 601 | 0.233 % | 0.244 % | ×1.08 | ×0.97 |
| **c. 3-20** (réf.) | 516 385 | 1 128 | 0.218 % | 0.226 % | réf. | réf. |
| d. 21-100 | 172 206 | 179 | 0.104 % | 0.106 % | ×0.47 | ×0.46 |
| e. 100+ | 57 068 | 34 | 0.060 % | 0.061 % | ×0.27 | ×0.28 |

### Présence de l'auteur sur plusieurs fiches du panel

| | Observations | Disparitions | Risque brut | Risque à âge comparable | Écart | Écart hors fiches attaquées |
|---|---:|---:|---:|---:|---:|---:|
| **1 fiche** (réf.) | 1 057 844 | 2 298 | 0.217 % | 0.217 % | réf. | réf. |
| 2 fiches ou plus | 76 467 | 339 | 0.443 % | 0.445 % | ×2.05 | ×2.40 |

### Rafale auteur (plusieurs avis le même jour)

| | Observations | Disparitions | Risque brut | Risque à âge comparable | Écart | Écart hors fiches attaquées |
|---|---:|---:|---:|---:|---:|---:|
| **non** (réf.) | 1 126 926 | 2 525 | 0.224 % | 0.224 % | réf. | réf. |
| rafale | 7 385 | 112 | 1.517 % | 1.427 % | ×6.37 | ×7.03 |

### Région

| | Observations | Disparitions | Risque brut | Risque à âge comparable | Écart | Écart hors fiches attaquées |
|---|---:|---:|---:|---:|---:|---:|
| **EU** (réf.) | 511 672 | 826 | 0.161 % | 0.162 % | réf. | réf. |
| US | 622 639 | 1 811 | 0.291 % | 0.290 % | ×1.79 | ×3.12 |

### Secteur

| | Observations | Disparitions | Risque brut | Risque à âge comparable | Écart | Écart hors fiches attaquées |
|---|---:|---:|---:|---:|---:|---:|
| automotive | 143 613 | 212 | 0.148 % | 0.146 % | ×1.92 | ×1.89 |
| **food_beverage** (réf.) | 213 582 | 167 | 0.078 % | 0.076 % | réf. | réf. |
| healthcare | 150 415 | 227 | 0.151 % | 0.160 % | ×2.11 | ×2.02 |
| home_services | 201 527 | 1 173 | 0.582 % | 0.587 % | ×7.72 | ×7.72 |
| hospitality | 226 707 | 184 | 0.081 % | 0.080 % | ×1.05 | ×1.05 |
| travel | 83 827 | 114 | 0.136 % | 0.137 % | ×1.81 | ×1.81 |
| wellness_fitness | 114 640 | 560 | 0.488 % | 0.490 % | ×6.44 | ×2.34 |

### Taille du groupe

| | Observations | Disparitions | Risque brut | Risque à âge comparable | Écart | Écart hors fiches attaquées |
|---|---:|---:|---:|---:|---:|---:|
| large | 515 026 | 1 636 | 0.318 % | 0.316 % | ×2.54 | ×1.98 |
| **mono** (réf.) | 259 623 | 323 | 0.124 % | 0.124 % | réf. | réf. |
| small | 359 662 | 678 | 0.189 % | 0.189 % | ×1.52 | ×1.52 |

<!-- /genere:level1 -->
