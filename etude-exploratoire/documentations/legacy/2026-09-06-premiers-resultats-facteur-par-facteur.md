---
date: 2026-09-06
projet: reviewflowz-analyse-google
titre: "Premiers résultats, facteur par facteur"
statut: résultats
---

# Premiers résultats, facteur par facteur

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

Sur les **104 662 avis de moins de 30 jours** du panel, dont **2 853 ont été
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

## Ce qu'il faut retenir

Deux corrections sont appliquées à chaque chiffre, et il faut les avoir en tête pour lire la
suite.

**À âge comparable.** L'âge pèse plus que tout le reste. Comparer deux groupes sans l'égaliser
revient surtout à mesurer lequel est le plus jeune.

**Hors 24 fiches purgées.** 24 établissements ont perdu plus de 5 % de leurs avis **et au moins
10 avis** — jusqu'à un tiers de leur fiche pour les plus touchés. Ils portent à eux seuls **23 %
des suppressions** du périmètre. Ils ne sont pas exclus des tableaux, mais chaque tableau donne en dernière colonne
ce que devient l'écart quand on les retire. **Quand les deux dernières colonnes divergent, c'est
la dernière qui dit la vérité sur le cas général.**

### Ce qui fragilise un avis

| Ce qui fragilise | Écart | Hors 24 fiches | Tient ? |
|---|---:|---:|---|
| L'auteur a publié plusieurs avis le même jour, sur des fiches différentes | ×16,9 | **×14,4** | oui |
| La fiche est dans les services à domicile | ×6,9 | **×5,9** | oui |
| L'auteur n'a aucun niveau Local Guide | ×6,6 | ×5,5 | oui |
| L'avis met 1 étoile (comparé à 4 étoiles) | ×8,2 | **×4,6** | affaibli de moitié |
| Compte tout neuf : premier avis jamais publié | ×4,7 | ×3,9 | oui |
| La fiche est aux États-Unis | ×1,7 | **×2,8** | renforcé |
| La fiche appartient à un groupe de 20 à 50 sites | ×2,5 | ×2,1 | oui |
| L'auteur a noté plusieurs établissements du panel | ×2,0 | ×1,8 | oui |
| L'avis met 5 étoiles (comparé à 4 étoiles) | ×2,0 | ×2,1 | oui |
| L'avis a été modifié depuis sa publication | ×1,7 | ×1,6 | oui |
| La fiche est dans le sport et bien-être | ×6,1 | **×1,8** | s'effondre |

### Ce qui protège un avis

| Ce qui protège | Écart | Hors 24 fiches |
|---|---:|---:|
| L'auteur est Local Guide de niveau 6 ou plus | ×0,27 | ×0,34 |
| L'auteur a écrit plus de 100 avis | ×0,31 | ×0,39 |
| L'avis contient deux photos ou plus | ×0,43 | ×0,53 |
| L'avis est rédigé dans une autre langue que celle de la fiche | ×0,56 | ×0,70 |
| L'avis met 3 étoiles | ×0,66 | ×0,78 |
| L'avis fait plus de 400 caractères | ×0,80 | ×0,90 |
| Le propriétaire a répondu à l'avis | ×0,86 | ×1,00 |

Tous les effets protecteurs s'atténuent une fois les 24 fiches retirées, sans changer de sens —
sauf la réponse du propriétaire, qui devient exactement neutre. Voir plus bas.

## Le résultat principal : la rafale

Un auteur qui publie plusieurs avis sur des établissements différents **dans la même journée**
voit ses avis supprimés quatorze fois plus que les autres. En clair : 2,5 % de ces avis
disparaissent d'un passage du robot au suivant, contre 0,18 % pour un avis ordinaire.

C'est la signature d'une ferme à avis, et c'est de loin le comportement que Google sanctionne le
plus durement. C'est aussi le seul effet de cette ampleur qui résiste à tous les contrôles :
réparti sur 165 fiches différentes, la plus touchée n'en portant que 19 %, et il reste à ×14,4
sans les 24 fiches purgées.

## Trois conclusions que le contrôle corrige

**Le secteur sport et bien-être n'est pas un secteur à risque.** Il affichait ×6,1, le deuxième
plus élevé. Sans les fiches purgées, il tombe à ×1,8 et rejoint le peloton. Deux salles de sport
espagnoles portaient tout l'effet. En revanche les **services à domicile tiennent à ×5,9** : là,
le risque est réel et réparti.

**L'écart entre 1 étoile et 4 étoiles est deux fois moins grand qu'annoncé** : ×4,6 et non ×8,2.
Les fiches massivement purgées perdaient beaucoup d'avis négatifs, ce qui gonflait l'effet
général. Un avis 1 étoile reste le plus exposé, mais dans un rapport de 5 environ, pas de 8.

**L'écart entre les États-Unis et l'Europe est plus grand qu'annoncé, pas plus petit** : ×2,8 au
lieu de ×1,7. C'est contre-intuitif et c'est logique : les fiches purgées étaient surtout
européennes, elles gonflaient artificiellement le niveau européen. Une fois retirées, les
États-Unis apparaissent nettement plus agressifs sur les avis récents.

## Quatre résultats du 4 septembre changent de sens

Deux corrections cumulées en sont responsables : le calcul à âge comparable, et le recentrage sur
les avis récents.

| | Note du 4 septembre | Maintenant |
|---|---|---|
| Avis avec texte contre note seule | le texte **augmentait** le risque | le texte **protège** — ×0,89 |
| Longueur du texte | « le risque croît avec la longueur » | il **décroît** : au-delà de 400 caractères, ×0,80 |
| Photos | « effet quasi nul » | **protection nette** : deux photos et plus, ×0,53 |
| Réponse du propriétaire | associée à **plus** de suppressions | neutre, voir ci-dessous |

**Sur la réponse du propriétaire, il faut être prudent.** Elle paraissait protectrice (×0,86),
mais une fois les 24 fiches purgées retirées l'effet disparaît complètement : ×1,00, soit aucune
différence. C'est le seul levier directement actionnable par le client, et à ce stade **on ne
peut rien en dire**. L'analyse B, qui compare des avis d'une même fiche, tranchera.

## Deux surprises à instruire

**Un avis en langue étrangère est moins supprimé** — ×0,70 après contrôle, contre ×0,56 avant.
L'effet s'atténue mais reste protecteur.

C'est l'inverse de ce que supposait le cadrage, qui postulait qu'un auteur géographiquement
improbable serait davantage sanctionné. Deux explications tiennent encore :

- Google considère qu'un touriste étranger prouve une visite réelle ;
- ou la langue étrangère est simplement plus fréquente dans l'hôtellerie, le secteur le moins
  supprimé du panel — auquel cas on mesure le secteur, pas la langue.

L'analyse B tranchera, puisqu'elle neutralise la fiche. **À ne pas communiquer avant.**

**Un avis modifié après publication est 60 % plus supprimé.** Facteur non prévu au cadrage.
L'hypothèse la plus simple est qu'une modification le fait repasser devant les filtres.

## Pourquoi il n'y a pas d'étude séparée par région ni par secteur

C'est une question de méthode, pas un oubli.

**La région et le secteur sont dans les tableaux**, en bas, comme n'importe quel autre facteur.
Ce qui n'est pas fait ici, c'est de refaire toute l'analyse séparément pour les États-Unis et
pour l'Europe, comme le plan de travail l'envisageait.

Trois raisons.

**Une étude séparée ne permet aucun test.** Deux analyses côte à côte donnent deux tableaux : on
voit que les chiffres diffèrent, sans savoir si l'écart est réel ou du bruit. En gardant tout
ensemble et en croisant, on obtient une réponse chiffrée à « l'effet est-il le même des deux
côtés ? ». Et on peut toujours présenter le résultat en deux tableaux pour le client.

**Découper multiplie les petites cellules, et les petites cellules mentent.** C'est exactement ce
qu'on vient de voir : deux salles de sport espagnoles faisaient apparaître le secteur sport et
bien-être comme le deuxième plus risqué d'Europe. Plus on découpe, plus ce genre d'accident
devient probable.

**Les données réclament des croisements, pas des séparations.** L'asymétrie entre régions est
très inégale selon le secteur : les services à domicile comptent 1 990 suppressions aux
États-Unis contre 145 en Europe, alors que l'automobile, la restauration et l'hôtellerie sont
quasiment identiques des deux côtés. Une étude « États-Unis » et une étude « Europe » moyennent
chacune ces régimes opposés. Un croisement région × secteur les distingue.

**Où ça se traite concrètement.** La région, le secteur et la taille du groupe sont des
caractéristiques de l'établissement, pas de l'avis : ils sont identiques pour tous les avis d'une
même fiche. Ils relèvent donc de l'**analyse A**, qui compare des établissements entre eux. Dans
l'**analyse B**, qui compare des avis à l'intérieur d'une même fiche, ils ne peuvent apparaître
que sous forme de croisements — « l'effet de la note est-il le même aux États-Unis et en
Europe ? ».

## Ce que ça arrête pour la suite

**Entrent dans l'analyse B** : la rafale d'auteur, la note, le niveau Local Guide, la signature
de compte neuf, la présence de l'auteur sur plusieurs fiches, les photos, la longueur du texte,
la réponse du propriétaire, la langue et la modification.

**Trois questions lui sont explicitement posées** : la réponse du propriétaire est-elle neutre ou
protectrice ? La langue étrangère protège-t-elle vraiment, ou n'est-ce que du secteur ? Et
l'écart entre régions tient-il à caractéristiques d'avis égales ?

## Les tableaux détaillés

<!-- genere:level1 — regenere par scripts/level1_bivariate.py, ne pas editer a la main -->
### Note

| | Observations | Disparitions | Risque brut | Risque à âge comparable | Écart | Écart hors 24 fiches purgées |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 74 177 | 687 | 0.926 % | 0.907 % | ×8.19 | ×4.50 |
| 2 | 25 620 | 57 | 0.222 % | 0.219 % | ×1.98 | ×1.88 |
| 3 | 36 747 | 27 | 0.073 % | 0.073 % | ×0.66 | ×0.76 |
| **4** (réf.) | 96 238 | 108 | 0.112 % | 0.111 % | réf. | réf. |
| 5 | 904 494 | 1 974 | 0.218 % | 0.219 % | ×1.98 | ×2.11 |

### Présence de texte

| | Observations | Disparitions | Risque brut | Risque à âge comparable | Écart | Écart hors 24 fiches purgées |
|---|---:|---:|---:|---:|---:|---:|
| avec texte | 827 595 | 2 008 | 0.243 % | 0.243 % | ×0.89 | ×1.29 |
| **note seule** (réf.) | 309 681 | 845 | 0.273 % | 0.273 % | réf. | réf. |

### Longueur du texte

| | Observations | Disparitions | Risque brut | Risque à âge comparable | Écart | Écart hors 24 fiches purgées |
|---|---:|---:|---:|---:|---:|---:|
| **a. note seule** (réf.) | 309 681 | 845 | 0.273 % | 0.273 % | réf. | réf. |
| b. 1-50 | 163 360 | 438 | 0.268 % | 0.268 % | ×0.98 | ×1.27 |
| c. 51-150 | 283 217 | 708 | 0.250 % | 0.251 % | ×0.92 | ×1.27 |
| d. 151-400 | 239 068 | 552 | 0.231 % | 0.230 % | ×0.84 | ×1.30 |
| e. 400+ | 141 950 | 310 | 0.218 % | 0.218 % | ×0.80 | ×1.32 |

### Photos jointes

| | Observations | Disparitions | Risque brut | Risque à âge comparable | Écart | Écart hors 24 fiches purgées |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 46 615 | 83 | 0.178 % | 0.181 % | ×0.69 | ×0.78 |
| 2+ | 58 166 | 65 | 0.112 % | 0.113 % | ×0.43 | ×0.54 |
| **aucune** (réf.) | 1 032 495 | 2 705 | 0.262 % | 0.262 % | réf. | réf. |

### Réponse du propriétaire

| | Observations | Disparitions | Risque brut | Risque à âge comparable | Écart | Écart hors 24 fiches purgées |
|---|---:|---:|---:|---:|---:|---:|
| avec réponse | 618 142 | 1 406 | 0.227 % | 0.231 % | ×0.86 | ×0.79 |
| **sans réponse** (réf.) | 519 134 | 1 447 | 0.279 % | 0.269 % | réf. | réf. |

### Langue hors langue dominante de la fiche

| | Observations | Disparitions | Risque brut | Risque à âge comparable | Écart | Écart hors 24 fiches purgées |
|---|---:|---:|---:|---:|---:|---:|
| **langue locale** (réf.) | 1 041 171 | 2 713 | 0.261 % | 0.261 % | réf. | réf. |
| langue étrangère | 96 105 | 140 | 0.146 % | 0.145 % | ×0.56 | ×0.60 |

### Avis édité depuis publication

| | Observations | Disparitions | Risque brut | Risque à âge comparable | Écart | Écart hors 24 fiches purgées |
|---|---:|---:|---:|---:|---:|---:|
| **non édité** (réf.) | 1 055 571 | 2 534 | 0.240 % | 0.239 % | réf. | réf. |
| édité | 81 705 | 319 | 0.390 % | 0.393 % | ×1.65 | ×1.71 |

### Niveau Local Guide

| | Observations | Disparitions | Risque brut | Risque à âge comparable | Écart | Écart hors 24 fiches purgées |
|---|---:|---:|---:|---:|---:|---:|
| a. absent | 47 061 | 412 | 0.875 % | 1.827 % | ×6.61 | ×7.48 |
| **b. 1-3** (réf.) | 706 644 | 1 892 | 0.268 % | 0.276 % | réf. | réf. |
| c. 4-5 | 258 329 | 456 | 0.177 % | 0.178 % | ×0.64 | ×0.74 |
| d. 6+ | 125 242 | 93 | 0.074 % | 0.075 % | ×0.27 | ×0.33 |

Le recalcul à âge comparable déplace nettement le chiffre : a. absent (0.875 % → 1.827 %). Une partie de l'effet apparent n'était que de la différence d'âge.

### Signature compte neuf (niveau absent + compteur 0)

| | Observations | Disparitions | Risque brut | Risque à âge comparable | Écart | Écart hors 24 fiches purgées |
|---|---:|---:|---:|---:|---:|---:|
| **autre** (réf.) | 1 091 863 | 2 480 | 0.227 % | 0.232 % | réf. | réf. |
| compte neuf | 45 413 | 373 | 0.821 % | 1.092 % | ×4.71 | ×4.64 |

Le recalcul à âge comparable déplace nettement le chiffre : compte neuf (0.821 % → 1.092 %). Une partie de l'effet apparent n'était que de la différence d'âge.

### Nombre d'avis de l'auteur

| | Observations | Disparitions | Risque brut | Risque à âge comparable | Écart | Écart hors 24 fiches purgées |
|---|---:|---:|---:|---:|---:|---:|
| a. compteur 0 | 131 151 | 735 | 0.560 % | 0.469 % | ×1.94 | ×1.39 |
| b. 1-2 | 258 211 | 654 | 0.253 % | 0.265 % | ×1.09 | ×0.93 |
| **c. 3-20** (réf.) | 517 584 | 1 211 | 0.234 % | 0.242 % | réf. | réf. |
| d. 21-100 | 172 873 | 211 | 0.122 % | 0.125 % | ×0.51 | ×0.54 |
| e. 100+ | 57 457 | 42 | 0.073 % | 0.075 % | ×0.31 | ×0.34 |

### Présence de l'auteur sur plusieurs fiches du panel

| | Observations | Disparitions | Risque brut | Risque à âge comparable | Écart | Écart hors 24 fiches purgées |
|---|---:|---:|---:|---:|---:|---:|
| **1 fiche** (réf.) | 1 060 525 | 2 492 | 0.235 % | 0.235 % | réf. | réf. |
| 2 fiches ou plus | 76 751 | 361 | 0.470 % | 0.472 % | ×2.01 | ×2.31 |

### Rafale auteur (plusieurs avis le même jour)

| | Observations | Disparitions | Risque brut | Risque à âge comparable | Écart | Écart hors 24 fiches purgées |
|---|---:|---:|---:|---:|---:|---:|
| **non** (réf.) | 1 125 665 | 2 455 | 0.218 % | 0.218 % | réf. | réf. |
| rafale | 11 611 | 398 | 3.428 % | 3.673 % | ×16.85 | ×14.72 |

### Région

| | Observations | Disparitions | Risque brut | Risque à âge comparable | Écart | Écart hors 24 fiches purgées |
|---|---:|---:|---:|---:|---:|---:|
| **EU** (réf.) | 513 860 | 933 | 0.182 % | 0.182 % | réf. | réf. |
| US | 623 416 | 1 920 | 0.308 % | 0.306 % | ×1.68 | ×2.66 |

### Secteur

| | Observations | Disparitions | Risque brut | Risque à âge comparable | Écart | Écart hors 24 fiches purgées |
|---|---:|---:|---:|---:|---:|---:|
| automotive | 144 609 | 234 | 0.162 % | 0.161 % | ×1.81 | ×1.82 |
| **food_beverage** (réf.) | 214 153 | 195 | 0.091 % | 0.089 % | réf. | réf. |
| healthcare | 150 964 | 255 | 0.169 % | 0.179 % | ×2.02 | ×2.02 |
| home_services | 202 193 | 1 224 | 0.605 % | 0.610 % | ×6.88 | ×5.88 |
| hospitality | 226 849 | 205 | 0.090 % | 0.088 % | ×1.00 | ×0.99 |
| travel | 83 857 | 121 | 0.144 % | 0.146 % | ×1.64 | ×1.57 |
| wellness_fitness | 114 651 | 619 | 0.540 % | 0.540 % | ×6.09 | ×1.80 |

### Taille du groupe

| | Observations | Disparitions | Risque brut | Risque à âge comparable | Écart | Écart hors 24 fiches purgées |
|---|---:|---:|---:|---:|---:|---:|
| large | 517 227 | 1 749 | 0.338 % | 0.337 % | ×2.45 | ×2.03 |
| **mono** (réf.) | 259 844 | 358 | 0.138 % | 0.138 % | réf. | réf. |
| small | 360 205 | 746 | 0.207 % | 0.208 % | ×1.51 | ×1.73 |

<!-- /genere:level1 -->
