---
date: 2026-09-06
projet: reviewflowz-analyse-google
titre: "Pourquoi ces entreprises ont perdu leurs avis — enquête et plan d'action"
statut: résultats et décisions à prendre
---

# Pourquoi ces entreprises ont perdu leurs avis

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

Enquête sur les 24 entreprises les plus touchées du panel. Toutes les requêtes sont
reproductibles ; elles seront rassemblées dans un programme (voir le plan d'action).

---

# Partie 1 — Les 7 vitrines endormies : ce ne sont pas des suppressions

## Le résultat

**Sept des vingt-quatre entreprises « massivement purgées » n'ont jamais rien perdu.**
Leurs 162 avis « supprimés » sont un défaut de collecte du robot.

| Entreprise | Avis « perdus » | Avis revenus ensuite |
|---|---:|---:|
| Mikel Coffee Company | 35 | **35** |
| Fair Doctors Duisburg | 34 | **34** |
| REDDY Küchen Eislingen | 23 | **23** |
| Occasions Cavallari | 23 | **23** |
| DetailCar La Concha | 18 | **18** |
| JET Waschstraße | 18 | **18** |
| MEGA Malereinkaufsgen. | 11 | **11** |

**100 % de retour.** Pas un seul avis n'a réellement disparu.

## La preuve, en trois points

**1. Le robot a lu moins de pages ce jour-là.** Le journal de collecte le montre pour chacune
des sept, au passage du 12 août :

| | Passage 1 (11/08) | Passage 2 (12/08) | Passage 3 (13/08) |
|---|---|---|---|
| Pages lues | 2 | **1** | 2 |
| Avis trouvés | tous | ceux de la page 1 | tous |
| Verdict du pipeline | — | « 35 avis supprimés » | « 35 avis nouveaux » |

Le robot n'a récupéré que la première page du listing, et le pipeline a conclu que les avis de
la deuxième page avaient été supprimés. Le lendemain, il relit les deux pages et les avis
« reviennent ».

**2. Le compteur de Google n'a pas bougé.** Si Google avait vraiment effacé 35 des 40 avis de
Mikel Coffee, son compteur public serait tombé à 5. Il est resté à 40, du premier au dernier
passage. Idem pour les six autres.

| Entreprise | Total Google au 11/08 | Total Google au 24/08 |
|---|---:|---:|
| Mikel Coffee | 40 | 40 |
| DetailCar | 23 | 23 |
| JET Waschstraße | 23 | 23 |
| REDDY Küchen | 28 | 28 |
| Fair Doctors | 39 | 40 |
| MEGA | 16 | 17 |
| Cavallari | 28 | 29 |

**3. Le contrôle de complétude n'a rien vu.** Les sept passages sont marqués « complets » dans
`wave_progress`, alors que le listing était tronqué de moitié. Le contrôle décrit dans le README
de l'export — « une entreprise ne compte pour un passage que si le listing complet a été
récupéré » — n'a pas détecté un listing d'une page au lieu de deux.

## Deux hypothèses écartées en chemin

- **Une campagne d'avis ancienne rattrapée par Google.** Non : les avis concernés sont étalés
  de 2016 à 2026, un auteur différent à chaque fois, jamais deux le même jour.
- **Des comptes bannis par Google.** Non : ces 210 auteurs ont 19 autres avis ailleurs dans le
  panel, et **aucun** n'a été touché.

## L'ampleur sur tout le panel

Le même défaut existe ailleurs.

| | Nombre |
|---|---:|
| Suppressions comptées dans le panel | 5 230 |
| **Dont l'avis est réapparu ensuite** | **509 (9,7 %)** |
| Suppressions sur le périmètre de l'étude (avis récents) | 2 853 |
| **Dont l'avis est réapparu ensuite** | **124 (4,3 %)** |

Le taux de retour est le plus élevé sur les premiers passages — 28,6 % le 12 août, 35,3 % le
14 août — et tombe à 3-4 % ensuite. **Les 9,7 % sont un plancher** : un avis disparu au dernier
passage n'a pas eu le temps de revenir, on ne peut pas savoir s'il serait revenu.

## Ce que ça change

- **Le vrai nombre de suppressions est d'au plus 4 721, pas 5 230.** Le taux passe de 0,107 % à
  0,097 %.
- **Sur le périmètre de l'étude, 124 des 2 853 suppressions sont fausses** (4,3 %). Les analyses
  A et B, le niveau 1 et le Test 2 les comptent toutes comme réelles.
- **Sept des vingt-quatre entreprises « purgées » doivent sortir de cette liste.** Le contrôle
  de robustesse les retire actuellement pour de mauvaises raisons.
- **C'est aussi un résultat en soi pour le livrable** : le listing public de Google sert des
  réponses incomplètes sans le signaler. Une entreprise qui surveille ses avis avec un outil du
  marché voit donc régulièrement des avis « disparaître » puis revenir. À vérifier avant de
  l'affirmer : c'est peut-être le robot de collecte et non Google.

---

# Partie 2 — Les salles de sport : une attaque par avis négatifs

## Ce qui s'est passé

Les deux salles de sport espagnoles (399 avis supprimés à elles deux) sont l'inverse exact :
**aucune de leurs suppressions n'est revenue.** Ce sont de vraies suppressions.

Leur contenu est sans ambiguïté.

| | Avis supprimés | Avis restés en ligne |
|---|---:|---:|
| Nombre | 399 | 1 085 |
| Note moyenne | **1,05** | 4,95 |
| Part de 1 étoile | **96 %** | 1 % |
| Part de 5 étoiles | 1 % | 98 % |
| Âge médian | **0 an** (tout récents) | 3 ans |
| Sans aucun texte | **68 %** | 27 % |
| Auteur sans niveau Local Guide | 23 % | 0 % |

**Le calendrier est encore plus net :**

| Jour de publication | Avis publiés puis supprimés | Note moyenne |
|---|---:|---:|
| 1er août 2026 | 162 | 1,01 |
| **2 août 2026** | **199** | **1,01** |
| 3 au 5 août 2026 | 34 | ~1,2 |

**361 avis d'une étoile publiés en deux jours** sur une fiche notée 4,95, par 363 comptes
différents, dont 68 % sans un mot de texte. Google les a effacés dix à quatorze jours plus tard.

## Ce que contenaient ces avis : rien

Sur les 399 avis supprimés :

- **270 n'avaient aucun texte** — une étoile, rien d'autre.
- **1 seul** contenait une insulte.
- 12 déclenchent l'un des onze contrôles textuels.

Il n'y avait rien à lire. Le signal n'était pas dans le texte, il était dans le **rythme** :
361 notes d'une étoile en 48 heures.

## Ce que ça veut dire

**Ce n'est pas un faux positif, c'est de la modération réussie.** Une entreprise s'est fait
attaquer, Google a nettoyé. C'est important pour le livrable, à double titre :

1. Il faut le dire, sinon l'étude paraît à charge. Google fait correctement son travail quand
   le signal est massif et évident.
2. **Ces 399 avis faussent tous les résultats où ils entrent.** Ils expliquent à eux seuls
   pourquoi « 1 étoile » et « secteur sport et bien-être » sortaient si forts avant le contrôle
   de robustesse — et pourquoi le secteur s'effondre de 3,6 à 1,3 quand on les retire.

---

# Partie 3 — Plan d'action

## Priorité 1 — Corriger le comptage des suppressions

**Ce qu'il faut faire.** Ajouter une règle dans `build_tables.py` : un avis dont l'identifiant
réapparaît vivant sur la même fiche n'est pas une suppression. Une colonne `fausse_suppression`
le marque, et `deleted` l'exclut.

**Pourquoi c'est la priorité.** Tous les chiffres de l'étude reposent sur le comptage des
suppressions. 4,3 % d'entre elles sont fausses sur le périmètre de l'étude, et elles sont
concentrées sur quelques fiches, donc elles ne se répartissent pas au hasard.

**Ce qu'il faut relancer ensuite** — dans cet ordre, chaque étape dépend de la précédente :

```bash
uv run scripts/build_tables.py            # 20 s
uv run scripts/level1_bivariate.py        # 10 s
nice -n 19 uv run scripts/analysis_a.py   # 2 min
nice -n 19 uv run scripts/analysis_b.py --marges-rapides   # 3 min 30
nice -n 19 uv run scripts/controle_robustesse.py           # 7 min
uv run scripts/test2_debordement.py       # 1 min
uv run scripts/verif_texte.py             # 2 min
```

**Effet attendu.** La liste des entreprises purgées passe de 24 à 17. Les chiffres du niveau 1
et du Test 2 bougent à la marge. L'analyse B ne devrait presque pas bouger, les fausses
suppressions étant sur des avis anciens.

**Risque à surveiller.** Le Test 2 mesure la mortalité du vieux stock. Les 162 fausses
suppressions portent justement sur du vieux stock, dans des entreprises sans activité récente —
donc dans le groupe de référence du test. Les retirer devrait **renforcer** le résultat
(le groupe de référence meurt moins qu'annoncé), mais il faut le vérifier et pas le supposer.

## Priorité 2 — Mesurer l'ampleur réelle du défaut de collecte

**Ce qu'il faut faire.** Un programme `scripts/verif_collecte.py` qui repère tous les passages
où le robot a lu moins de pages que d'habitude pour une entreprise donnée, et croise avec les
suppressions détectées ce jour-là.

**Pourquoi.** Les 509 retours sont ce qu'on peut prouver. Un avis disparu au dernier passage,
ou disparu et jamais recollecté, reste compté comme supprimé alors qu'il ne l'est peut-être pas.
Le nombre de pages lues donne une deuxième mesure, indépendante du retour de l'avis.

**Ce que ça produit.** Un chiffre à porter en réserve du livrable : « x % des suppressions
détectées par ce type de collecte sont des artefacts ». C'est une limite de méthode qu'il vaut
mieux annoncer que se faire opposer.

## Priorité 3 — Traiter les attaques par avis négatifs à part

**Ce qu'il faut faire.** Repérer dans tout le panel les épisodes du type « beaucoup d'avis d'une
même note en peu de jours sur une fiche », les compter, et les sortir du calcul principal.

**Pourquoi.** Les 399 avis des salles de sport pèsent 14 % des suppressions du périmètre de
l'étude. Tant qu'ils y sont, on ne mesure pas « ce qui fait supprimer un avis », on mesure
« Google a nettoyé deux attaques ».

**Ce que ça produit deux choses :**
- des résultats principaux débarrassés d'un cas particulier écrasant ;
- un chapitre du livrable sur ce que Google fait **bien**, qui rend le reste crédible.

## Priorité 4 — Rassembler l'enquête dans un programme

Toutes les requêtes de cette note ont été passées à la main. Elles doivent tenir dans
`scripts/enquete_fiches_purgees.py` pour être rejouables et vérifiables.

## Ce qui est suspendu en attendant

- **Ne rien communiquer à Axel avant la priorité 1.** Tous les chiffres actuels comptent
  509 suppressions qui n'en sont pas.
- Le Test 3 et le contrôle par machine learning passent après.

## Ce qui n'est pas affecté

La vérification du contenu textuel tient : 94 % des avis supprimés sans faute visible. Retirer
162 avis anciens revenus ne peut pas la renverser, et les 399 avis des salles de sport, sans
texte à 68 %, ne portent pas d'insultes non plus.
