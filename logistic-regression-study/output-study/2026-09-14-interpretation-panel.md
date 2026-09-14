---
date: 2026-09-14
projet: reviewflowz-analyse-google
titre: "Ce que dit la régression sur le panel reconstruit"
statut: résultats
---

# Ce que dit la régression sur le panel reconstruit

Lecture des quatre passages de `07_regression_panel.py` du 2026-09-14, tous dans
`2026-09-14-sorties-07/`. **Aucun calcul n'a été relancé pour écrire cette note** : chaque
chiffre cité est dans un de ces fichiers, nommé à côté de lui.

## Le corpus

225 757 avis publiés du 2026-05-13 au 2026-08-16, sur 8 205 fiches. Une ligne par avis.
2 595 d'entre eux ont disparu, soit **1,15 % des 225 757**.

Quatre passages :

| Passage | Avis | Suppressions | Taux | Fichiers |
|---|---:|---:|---:|---|
| `tous` | 225 757 | 2 595 | 1,15 % | `07_*_tous.*` |
| `tous_sans_enseignes` | 210 670 | 1 576 | 0,75 % | `07_*_tous_sans_enseignes.*` |
| `US` | 127 813 | 1 851 | 1,45 % | `07_*_US.*` |
| `Europe` | 97 944 | 744 | 0,76 % | `07_*_Europe.*` |

Les six enseignes signalées — quatre chaînes antiparasitaires américaines et deux salles de
sport espagnoles — portent **1 019 des 2 595 suppressions, soit 39,3 %**. C'est pourquoi
chaque effet est lu deux fois, avec et sans elles.

Tous les risques relatifs qui suivent sont **à âge comparable** : `log_age_vague1` est dans le
modèle. Son propre coefficient n'est pas un résultat et n'est pas cité ici.

---

## 1. Le résultat principal : deux phénomènes opposés dans le même corpus

Le taux de suppression par note, avant tout modèle (`07_croisements_US.csv` et
`07_croisements_Europe.csv`), sur 10 000 avis de chaque groupe :

| Note | États-Unis | Europe |
|---|---:|---:|
| 1 étoile | 262,0 | 584,6 |
| 2 étoiles | 96,5 | 95,5 |
| 3 étoiles | 65,3 | 24,4 |
| 4 étoiles | 60,5 | 24,0 |
| 5 étoiles | **145,1** | 35,7 |

Lecture d'une case : sur 10 000 avis 5 étoiles déposés sur une fiche américaine du panel,
145 ont disparu ; sur 10 000 avis 5 étoiles européens, 36 ont disparu.

Aux États-Unis, l'avis 5 étoiles est supprimé **plus souvent** que l'avis 3 ou 4 étoiles.
En Europe, il l'est presque trois fois moins que l'avis 1 étoile. Ce sont deux régimes
différents, et les agréger les moyenne l'un avec l'autre.

En volume, sur les 1 851 suppressions américaines, **1 590 frappent un avis 5 étoiles, soit
85,9 %** ; 185 frappent un avis 1 étoile, soit 10,0 %. Sur les 744 suppressions européennes,
422 frappent un avis 1 étoile (56,7 %) et 260 un avis 5 étoiles (34,9 %).

**C'est l'angle faux positifs commandé par Axel.** Sur le panel entier, 1 850 des 2 595
suppressions portent sur un avis 5 étoiles, soit **71,3 %**. Retirer les six enseignes
signalées ne change pas ce constat : 1 193 des 1 576 restantes, soit 75,7 %.

Le risque relatif de 1 étoile (×6,34 sur `tous`) décrit donc une minorité des suppressions.
Il est à citer avec la part de volume à côté, sans quoi il oriente vers le mauvais sujet.

---

## 2. Ce qui tient dans les quatre passages

Trois effets vont dans le même sens partout, et survivent au retrait des six enseignes.

### Un compte d'auteur sans niveau Local Guide

| Passage | Risque relatif | Intervalle |
|---|---:|---|
| tous | ×2,30 | [1,89 – 2,79] |
| sans enseignes | ×2,51 | [1,92 – 3,28] |
| US | ×1,83 | [1,43 – 2,35] |
| Europe | ×3,73 | [2,51 – 5,53] |

Référence : un compte de guide établi. C'est **le seul effet qui se renforce** quand on
retire les six enseignes, ce qui veut dire qu'il ne vient pas d'elles.

Son poids réel est petit : ces comptes sont 3 903 avis sur 225 757 (1,7 % du panel) et portent
319 des 2 595 suppressions (12,3 %).

### Le secteur home_services

×5,73 [3,29 – 9,98] sur `tous`, **×3,16 [1,84 – 5,42] une fois les quatre chaînes
antiparasitaires retirées**. L'effet ne se résume donc pas à ces chaînes, même si elles en
sont la plus grosse part : home_services porte 1 189 des 2 595 suppressions du panel (45,8 %),
et 1 138 des 1 851 suppressions américaines (61,5 %).

### Un établissement américain

×1,99 [1,53 – 2,59] sur `tous`, ×2,14 [1,56 – 2,93] sans les enseignes. À âge, note, secteur
et profil d'auteur comparables, un avis déposé sur une fiche américaine disparaît deux fois
plus souvent qu'un avis européen.

---

## 3. La réponse du commerçant : l'écart brut est un effet d'âge

C'est le point que la note doit trancher, parce que c'est le seul levier que le client
actionne lui-même.

**Avant tout modèle** (`07_croisements_tous.csv`), sur 10 000 avis de chaque groupe :

| | Avis | Suppressions | Sur 10 000 avis |
|---|---:|---:|---:|
| Sans réponse au démarrage | 105 527 | 1 512 | 143,3 |
| Avec réponse au démarrage | 120 230 | 1 083 | 90,1 |

L'avis déjà répondu paraît donc 1,6 fois moins supprimé.

**À âge comparable, il ne reste rien** (`07_coefficients_*.csv`, ligne
`reponse_avant_surveillance`) :

| Passage | Risque relatif | Intervalle | p |
|---|---:|---|---:|
| tous | **1,02** | [0,75 – 1,38] | 0,91 |
| sans enseignes | 0,80 | [0,58 – 1,09] | 0,15 |
| US | 0,96 | [0,67 – 1,38] | 0,82 |
| Europe | 0,86 | [0,65 – 1,14] | 0,30 |

### Pourquoi l'écart brut disparaît

Un avis vieux de trois mois a deux propriétés en même temps : il a eu le temps de recevoir une
réponse, et il ne risque presque plus rien. Un avis d'hier n'a ni l'un ni l'autre. Comparer les
deux groupes sans tenir compte de l'âge, c'est comparer des avis vieux à des avis jeunes en
croyant comparer des avis répondus à des avis non répondus.

Le tableau mesuré le 2026-09-14 sur ce panel (`07_regression_panel.py:28-33`) :

| Âge à la vague 1 | Avis | Supprimés | Réponse déjà présente |
|---|---:|---:|---:|
| né pendant la surveillance | 12 664 | 3,76 % | 15,6 % |
| 0 à 7 j | 20 396 | 3,77 % | 39,0 % |
| 8 à 30 j | 56 599 | 1,71 % | 54,5 % |
| 31 à 60 j | 69 479 | 0,38 % | 58,1 % |
| 61 à 90 j | 66 619 | 0,18 % | 58,7 % |

Le risque est divisé par 21 du haut en bas, pendant que la part d'avis déjà répondus passe de
15,6 % à 58,7 %. Les deux colonnes bougent ensemble parce qu'elles dépendent toutes deux de
l'âge, pas l'une de l'autre.

### Ce que ce résultat permet de dire, et ce qu'il ne permet pas

- **Il permet de dire** que l'écart brut de 143,3 contre 90,1 ne prouve aucune protection.
- **Il ne permet pas de dire que répondre ne sert à rien.** L'intervalle [0,75 – 1,38] reste
  compatible avec une protection d'un quart comme avec une aggravation d'un tiers. Le modèle dit
  qu'il ne voit pas d'effet, ce qui n'est pas la même chose que dire qu'il n'y en a pas.
- La mesure porte sur `reponse_avant_surveillance`, c'est-à-dire une réponse arrivée **avant le
  11 août**. Elle ne mesure pas l'effet de répondre vite à un avis qui vient de tomber. C'est
  une autre question, et c'est celle que le client d'Axel pose. Elle est traitée par
  `08_effet_reponse_commercant.py`, **écrit mais jamais lancé** faute d'accès BigQuery sur la
  machine de travail.

### Trois chiffres coexistent. Les voici côte à côte

| Chiffre | Source | Population | Contrôle de l'âge |
|---|---|---|---|
| **×1,02** [0,75 – 1,38] | `07_regression_panel.py` | 225 757 avis de 0 à 90 jours, 8 205 fiches | logarithme, continu |
| **×0,40** | `analysis_b.py`, réponse datée | 61 202 observations d'avis de moins de 30 jours, 514 fiches | 5 tranches |
| **×0,56** [0,37 – 0,85] | `08_effet_reponse_commercant.py`, jalon J+2, hors les 4 chaînes | 14 170 avis nés du 11 au 16 août | sans objet : jalon fixe |

**Le ×0,56 est le seul des trois qui réponde à la question du client d'Axel** — répondre vite à
un avis qui vient de tomber. Le ×1,02 ci-dessus mesure autre chose : l'effet d'une réponse
ancienne sur un avis déjà installé. Détail et réserves dans
`2026-09-14-effet-reponse-commercant.md`. Sur le corpus complet, ce même montage donne ×0,79
[0,53 – 1,16], que le modèle ne distingue pas de « aucun effet ». Annoncer le ×0,56 sans
dire qu'il exclut ces quatre chaînes serait faux.

Le ×0,40 date du 2026-09-14 : `analysis_b.py` lisait jusque-là `has_reply`, l'état de la réponse
au dernier passage du robot recopié sur tous les passages précédents. Une fois la réponse datée,
son effet est passé de ×0,30 à ×0,40, et **seul ce facteur a bougé** — les 25 autres se sont
déplacés de 1 à 5 %, sur le même corpus et les mêmes 2 623 disparitions.

Les deux chiffres ne se contredisent pas : ni la population, ni l'unité comptée, ni la finesse
du contrôle de l'âge ne sont les mêmes. L'explication la plus probable de l'écart, et le
contrôle qui la trancherait, sont écrits dans
`../etude-exploratoire/documentations/2026-09-06-analyse-b-quel-avis-tombe.md`, dernière section.

### Trois chiffres à ne plus citer

- **« La réponse du propriétaire protège 3,7 fois »** et **« ×0,30 »**, de l'analyse B. Ils
  mesuraient en partie « avoir survécu assez longtemps pour recevoir une réponse ». Remplacés
  par ×0,40, avec les réserves ci-dessus.
- **« ×0,93, p = 0,649 »** (`BACKLOG.md`, corrigé le 2026-09-14). Cette valeur n'existait dans
  aucun fichier de sortie. La valeur versionnée est 1,018, p = 0,906.

---

## 4. Trois effets qui changent de sens selon le découpage

Aucun des trois ne doit être cité sans préciser sur quel passage il est lu.

| Effet | tous | sans enseignes | US | Europe |
|---|---:|---:|---:|---:|
| Rafale d'auteur (`log_burst`) | ×9,54 | ×5,28 | **×49,30** | ×0,90 |
| Pic d'afflux sur la fiche | ×1,40 | ×0,87 | ×0,84 | **×2,17** |
| Texte de plus de 200 caractères | ×0,66 | **×1,38** | ×1,10 | ×0,51 |

### La rafale d'auteur est américaine, et repose sur très peu d'avis

Le coefficient s'exprime par point de logarithme, ce qui le rend illisible tel quel. Traduit
en nombre d'avis déposés le même jour par le même auteur, à partir de `07_coefficients_tous.csv`
et `07_coefficients_US.csv` :

| Passage de 1 à… | tous | US |
|---|---:|---:|
| 2 avis le même jour | ×2,50 | ×4,86 |
| 3 avis | ×4,78 | ×14,91 |
| 4 avis | ×7,90 | ×35,57 |

Les effectifs qui portent cet effet sont minces. Sur le panel entier, 1 681 avis ont 2 dépôts
ou plus le même jour, sur 225 757. Et le gros du signal tient à une seule cellule
(`07_croisements_tous.csv`) : **100 avis à 4 dépôts le même jour, dont 44 supprimés**, soit
1,7 % des 2 595 suppressions.

Ces 44 suppressions sont entièrement dans les enseignes signalées. Preuve dans
`07_croisements_tous_sans_enseignes.csv` : une fois ces enseignes retirées, la cellule
« 4 avis le même jour » compte 56 avis et **0 suppression**. Aux États-Unis seuls, elle compte
72 avis et 44 suppressions, soit 61 % du groupe.

### Le texte long : l'effet apparaît quand on retire les enseignes

Taux bruts par tranche de texte, sur 10 000 avis :

| Tranche | tous | sans enseignes |
|---|---:|---:|
| Sans texte | 120,1 | 52,3 |
| 1 à 50 car. | 121,8 | 75,6 |
| 51 à 200 car. | 111,8 | 78,2 |
| Plus de 200 car. | 109,3 | **94,2** |

Sur le corpus entier, la colonne est plate. Une fois les six enseignes retirées, elle devient
croissante : un avis long est supprimé près de deux fois plus souvent qu'un avis sans texte.
Les enseignes signalées écrasaient ce gradient parce qu'elles perdent massivement des avis
longs et positifs.

Le modèle dit la même chose : ×0,66 (p = 0,07) sur `tous`, ×1,38 (p = 0,010) sans les
enseignes. **C'est le seul effet du panel dont le signe s'inverse de façon significative des
deux côtés.** Il mérite un examen à part avant d'être publié.

### Le pic d'afflux est européen

×2,17 [1,76 – 2,68] en Europe, ×0,84 [0,69 – 1,02] aux États-Unis. Traduit : une fiche
européenne qui reçoit dix fois son rythme habituel un jour donné voit ses avis de ce jour
supprimés ×3,74 plus souvent ; aux États-Unis l'effet est absent, voire légèrement inverse.
C'est cohérent avec le reste : en Europe les suppressions suivent des dépôts massifs d'avis
négatifs, aux États-Unis elles frappent un flux régulier d'avis positifs.

---

## 5. Ce que vaut le modèle

| Passage | AUC | Calibration |
|---|---:|---|
| tous | 0,862 | bonne sur les dix déciles |
| US | 0,843 | bonne |
| sans enseignes | 0,819 | légère sous-estimation en haut |
| Europe | 0,819 | **inexploitable** — voir plus bas |
| Europe sans enseignes | 0,882 | **inexploitable** pour la même raison |

L'AUC est lue sur des établissements que le modèle n'a jamais vus, auteurs chevauchants
retirés du test (`07_regression_panel.py:538-553`). 0,862 se lit : présenté avec un avis
supprimé et un avis resté en ligne tirés au hasard, le modèle donne le score le plus élevé au
bon dans 86 % des cas.

**Réserve importante sur cette AUC** : elle est en grande partie portée par l'âge, qui est une
variable de contrôle et non un résultat. Le `BACKLOG.md` note 0,717 sans l'âge. C'est ce
second chiffre qui mesure ce que les caractéristiques de l'avis apportent.

**Le passage Europe est mal calibré et ne doit pas servir à annoncer un risque.** Sur son
dernier décile (`07_calibration_Europe.csv`), le modèle annonce 3,72 % de suppression et on en
observe 1,47 %.

### Ce n'est pas le modèle qui se trompe, c'est l'échantillon de test

Vérifié le 2026-09-14. Le taux de suppression du sous-ensemble tiré pour le test se compare
ainsi à celui du corpus dont il sort :

| Passage | Taux observé sur le test | Taux du corpus | Écart |
|---|---:|---:|---:|
| tous | 1,138 % | 1,149 % | aucun |
| US | 1,429 % | 1,448 % | aucun |
| Europe | 0,327 % | 0,760 % | **le test est 2,3 fois moins touché** |
| Europe sans enseignes | 0,239 % | 0,428 % | **1,8 fois moins touché** |

`decoupage()` met de côté 25 % des établissements tirés au hasard. En Europe, ce tirage est
tombé sur des fiches nettement moins touchées que la moyenne. Le modèle annonce le bon niveau,
celui du corpus ; le test se trouve être plus calme. Tout paraît donc surestimé, sur les dix
déciles et pas seulement sur le dernier.

**Pourquoi l'Europe et pas les États-Unis.** Le risque européen est beaucoup plus concentré :
**2 fiches sur 4 106 portent 327 des 744 suppressions, soit 44 %.** Ce sont les deux salles de
sport espagnoles attaquées, vérifiées fiche par fiche le 2026-09-14 :

| Fiche | Avis dans le panel | Suppressions |
|---|---:|---:|
| Boutique The Boxer Club Dr Castelo | 206 | 192 |
| The Boxer Club — la salle attaquée | 151 | 135 |

Avec 744 événements aussi mal répartis, un tirage de 25 % des fiches change le taux de base du
simple au double. Aux États-Unis, 1 851 suppressions mieux réparties rendent le tirage stable.

**Retirer ces fiches ne suffit pas** : le passage `Europe_sans_enseignes` garde un test 1,8 fois
moins touché que son corpus. La concentration subsiste au-delà d'elles.

**Réserve sur le drapeau, sans effet sur les chiffres ci-dessus.** `salle_de_sport_attaquee`
repose sur le nom d'enseigne et non sur l'identifiant de fiche. Il marque donc 13 fiches : les
2 attaquées, plus 11 autres salles « The Boxer Club » qui totalisent 90 avis et **aucune
suppression**. `--sans-enseignes-signalees` les écarte à tort, sans que cela change un
coefficient. Le même drapeau pour les 4 chaînes antiparasitaires est correct : le multi-fiches
y est voulu, et les comptes (26, 19, 19, 24) correspondent à `CLAUDE.md`.

### La correction

Remplacer le tirage unique par une validation croisée par établissement, en 5 plis : chaque
fiche passe une fois et une seule en test, les prédictions hors échantillon sont rassemblées,
et l'AUC comme la calibration se lisent alors sur le corpus entier. Le taux de base du test est
mécaniquement le bon, et le hasard du tirage disparaît. Le modèle s'ajuste en 8 à 11 secondes,
donc 5 plis coûtent environ une minute.

Non fait à ce jour. Tant que ça n'est pas fait : **les coefficients européens se lisent en
risque relatif, les probabilités qu'ils produisent ne se citent pas.**

Une limite que cette correction ne lèvera pas : quand les 2 fiches attaquées tombent dans le pli
de test, le modèle ne les a pas vues et sous-estimera leur risque ; quand elles sont côté
entraînement, il surestimera ailleurs. La moyenne devient juste, la dispersion reste. C'est la
concentration du phénomène européen, qu'aucune méthode d'évaluation ne fait disparaître.

---

## 6. Réserves de lecture

- **`supprime` vaut `deleted_detected_at IS NOT NULL`** (`sql/02_adding_features.sql:169`),
  sans la règle des 2 jours d'absence utilisée ailleurs dans le projet. Ce n'est pas une
  omission : `HAVING COUNT(*) = 1` (`sql/01_selection_panel.sql:54-59`) a déjà écarté tout avis
  disparu puis revenu, donc il n'y a plus de résurrection à trier. Les 2 595 suppressions de ce
  panel ne se comparent pas directement aux 4 737 du corpus entier : ni le périmètre ni la
  règle ne sont les mêmes.
- **731 avis sont écartés du corpus**, soit 0,3 % des avis mais environ 3 % des suppressions.
  L'exclusion n'est pas neutre vis-à-vis de la cible. Conséquence directe sur cette note : les
  avis déposés en rafale sont 52 % des écartés, donc l'effet « rafale d'auteur » ci-dessus est
  mesuré sur un corpus qui en a déjà perdu la moitié.
- **Les avis encore en ligne au dernier passage n'ont pas fini leur histoire.** Un avis compté
  « non supprimé » peut l'être le lendemain du dernier relevé.
- **`langue_etrangere_au_pays` n'est pas dans le modèle** et ne doit pas être citée : en Europe
  elle mesure le tourisme (92,8 % des avis croates y sont « étrangers »).
- **Le coefficient de `log_age_vague1` n'est pas un résultat.** Il est là pour que les autres
  se lisent à âge comparable.

---

## 7. Régénérer ces chiffres

Les quatre passages, depuis `logistic-regression-study/` :

```bash
python 07_regression_panel.py
python 07_regression_panel.py --sans-enseignes-signalees
python 07_regression_panel.py --region US
python 07_regression_panel.py --region Europe
```

Chaque passage écrit dans `{date du jour}-sorties-07/`. Relancé un autre jour, il crée un
nouveau dossier au lieu d'écraser celui-ci.

Les conversions de coefficients logarithmiques de la section 4 se refont ainsi :

```python
import math
# risque relatif d'un passage de a à b avis le même jour, coefficient log_burst
math.exp(coef * (math.log1p(b) - math.log1p(a)))
```

## 8. Divergence trouvée et corrigée le 2026-09-14

Le tableau de résultats de `BACKLOG.md` portait six valeurs qui ne correspondaient à aucun
fichier de `2026-09-14-sorties-07/` : rafale ×9,21 contre ×9,54, 1 étoile ×6,17 contre ×6,34,
home_services ×5,69 contre ×5,73, auteur sans niveau ×2,51 contre ×2,30, américain ×2,13
contre ×1,99, 4 étoiles ×0,60 contre ×0,62. Les AUC, elles, coïncidaient. Ces valeurs venaient
d'un passage qui n'a pas été conservé — le dossier `sorties/` est vide.

Le tableau du `BACKLOG.md` a été refait depuis les CSV. **Les CSV de `2026-09-14-sorties-07/`
font foi**, puisqu'ils sont les seuls régénérables par une commande.

Deux autres valeurs ont été retirées le même jour, faute de source :

- **`50,0 % contre 35,0 %`** sur la part d'avis répondus chez les chaînes antiparasitaires
  (`CLAUDE.md`). Une seule occurrence dans tout le dépôt, absente des scripts et des CSV.
  L'observation est conservée, l'ampleur retirée jusqu'à ce qu'une requête la reproduise.
- **`107 821 / 2 540 / 2,36 %`** et **D3 = 2 540** dans `PASSATION.md`, valeurs d'avant le
  dédoublonnage du 2026-09-09. Remplacées par 106 144 / 2 637 / 2,48 % et D3 = 2 637.
