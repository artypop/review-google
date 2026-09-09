---
date: 2026-09-06
projet: reviewflowz-analyse-google
titre: "Reprise — qualifier les suppressions avant de les analyser"
statut: plan, à valider par Romain
---

# Reprise de l'étude

> ## MIXTE — vérifié le 2026-09-08
>
> **Méthode, décisions et questions ouvertes : toujours valables.**
> **Chiffres de résultat : périmés**, calculés avant la correction du comptage. Dans ce
> document : 509 sur 5 230, 617 résurrections, la cascade 5 314 / 5 230 / 2 705 / 2 853.
>
> Comptage de référence aujourd'hui : **4 747 suppressions** sur 5 230 disparitions brutes.
> Résultats à jour : `2026-09-08-synthese-de-la-journee.md`. Inventaire : `INDEX.md`.

Ce document remplace le programme d'analyse précédent. Il part d'un constat : l'étude a
modélisé des suppressions sans jamais vérifier ce que contenait ce qu'elle comptait.

---

## Partie 1 — Ce qui est faux, et pourquoi

### Cinq défauts, tous dans le comptage des suppressions

**1. Des avis « supprimés » qui reviennent.** 509 des 5 230 suppressions (9,7 %) concernent un
avis qui réapparaît vivant sur la même fiche. Sur le périmètre de l'étude : 124 sur 2 853.
Le README de l'export l'annonçait — « Deletions are not always permanent », 617 résurrections —
et le filtre n'a pas été posé.

**2. Un défaut de collecte pris pour de la modération.** Sept entreprises perdent 162 avis le
même jour parce que le robot a lu une page de listing au lieu de deux. Les 162 reviennent au
passage suivant. Le compteur public de Google n'a jamais bougé. Ces sept entreprises figurent
parmi les 24 « massivement purgées » qui servent de référence à tous les contrôles.

**3. Le périmètre « avis récents » contient des avis anciens.** Sa définition retient tout avis
vu pour la première fois pendant les 14 jours. Ce groupe contient 819 avis de plus de 30 jours,
dont 588 de plus d'un an, jusqu'à 13 ans. Ils portent 154 des 2 853 suppressions.

Leur taux de suppression est de **18,8 %**, contre 2,5 % pour les vrais avis récents. Ce sont
très probablement les mêmes artefacts de collecte qu'au point 2 : des avis que le robot n'avait
pas vus au premier passage.

**4. Les réponses de propriétaire ne sont pas suivies.** L'export ne les versionne jamais :
`changed_fields` ne contient que `star` et `text` sur les 2 012 lignes d'historique, jamais
`reply`. **Une réponse retirée est invisible.** Le résultat « répondre protège 3,7 fois » ne
peut pas être vérifié contre ce cas.

**5. Le passage de 5 314 à 2 853 n'a jamais été écrit.**

| | |
|---|---:|
| Lignes marquées supprimées dans l'export | 5 314 |
| dont lignes d'historique d'édition, pas des avis | −84 |
| **Avis supprimés** | **5 230** |
| dont avis de plus de 30 jours | −2 525 |
| **Avis récents supprimés** | **2 705** |
| ajouts dus au défaut n° 3 | +148 |
| chiffre utilisé dans toute l'étude | **2 853** |

### Ce que ça emporte

Tous les résultats chiffrés : niveau 1, analyse A, analyse B, Test 2, contrôle de robustesse.
Ils comptent tous une population mal définie.

### Ce que ça n'emporte pas

Les programmes, les tables et les méthodes de calcul. Une fois le comptage corrigé, l'ensemble
se recalcule en une quinzaine de minutes. Ce sont les résultats qui tombent, pas l'outillage.

### La cause

Il n'y a jamais eu d'étape de qualification des suppressions. L'étude est passée du fichier brut
à la modélisation sans poser la question : *qu'est-ce qu'une suppression dans ces données, et
est-ce que ce que je compte existe vraiment ?*

---

## Partie 2 — Étape 0 : qualifier les suppressions

**Rien d'autre ne démarre avant.** Un programme, `scripts/qualification_suppressions.py`, qui
répond à sept questions dans l'ordre. Chacune produit un tableau ; aucune ne suppose la réponse
de la suivante.

### Q1 — Combien de suppressions, et lesquelles sont réelles ?

Classer les 5 230 en quatre catégories, et donner l'effectif de chacune :

| Catégorie | Comment on la reconnaît |
|---|---|
| **Revenue** | l'identifiant de l'avis réapparaît vivant sur la même fiche |
| **Douteuse — listing tronqué** | le robot a lu moins de pages que d'habitude ce jour-là sur cette fiche |
| **Douteuse — compteur Google stable** | la fiche perd des avis mais le total affiché par Google ne bouge pas |
| **Réelle** | aucun des trois signaux ci-dessus |

Le troisième critère est le plus fort : c'est celui qui a permis de comprendre les sept vitrines.
Le README de l'export prévient que le compteur peut être en avance sur le listing, jamais en
retard. Un listing qui perd 35 avis quand le compteur reste à 40 est une anomalie de collecte.

### Q2 — À quoi ressemble une suppression réelle ?

Sur les seules suppressions réelles, décrire sans modèle : note, âge, longueur du texte,
photos, langue, type de compte, jour de disparition, délai entre publication et disparition.
Comparer systématiquement aux avis restés en ligne.

**Ce que cette étape aurait dû produire dès le départ.** Elle ne coûte rien et elle oriente tout
le reste.

### Q3 — Que contiennent les avis supprimés ?

Les onze contrôles textuels existants (`verif_texte.py`), rejoués sur les seules suppressions
réelles. Plus : les mots les plus sur-représentés dans les avis supprimés par rapport aux avis
restés en ligne, en agrégé, sans jamais faire figurer un texte ni un auteur dans une note.

### Q4 — Les suppressions arrivent-elles isolées ou par paquets ?

Pour chaque fiche et chaque jour, compter les suppressions. Séparer :

- les fiches qui perdent **un** avis un jour donné ;
- celles qui en perdent **plusieurs d'un coup**, et à quelle note.

Les 399 avis d'une étoile des salles de sport sont un paquet. Les traiter comme 399 événements
indépendants fausse tout ce qui les inclut.

### Q5 — Combien d'attaques par avis négatifs dans le panel ?

Repérer les épisodes du type « beaucoup d'avis de même note en peu de jours sur une fiche ».
Les compter, mesurer combien Google en a nettoyé, en combien de temps.

**Résultat attendu à double usage** : sortir ces cas des résultats principaux, et fournir au
livrable le chapitre sur ce que Google fait bien.

### Q6 — Que valent les réponses de propriétaire comme variable ?

Établir noir sur blanc ce que l'export permet et ne permet pas :

- la présence d'une réponse est-elle l'état au dernier passage où l'avis a été vu, ou l'état
  final du panel ?
- une réponse ajoutée pendant le suivi est-elle datée de façon exploitable ?
- une réponse retirée est-elle détectable ? *(Réponse déjà connue : non.)*

Selon le résultat, la variable est utilisable, utilisable avec réserve écrite, ou écartée.

### Q7 — Quelle part du panel est fiable ?

Par fiche : nombre de passages où le listing semble tronqué, écarts entre compteur Google et
listing, suppressions revenues. Produire une liste de fiches à exclure ou à traiter à part.

---

## Partie 3 — Ce qui vient après, et seulement après

1. **Redéfinir le périmètre.** « Avis récent » doit vouloir dire « publié il y a moins de
   30 jours », vérifié sur la date de publication et non sur la date de première observation.
2. **Reconstruire les tables** avec le comptage corrigé et le périmètre corrigé.
3. **Rejouer les analyses** dans l'ordre : niveau 1, A, B, contrôle de robustesse, Test 2.
4. **Comparer les résultats avant / après** et écrire ce qui a changé. C'est cette comparaison
   qui dira si les conclusions actuelles tenaient par chance ou pas du tout.

---

## Partie 4 — Ce qu'il faut décider maintenant

**a. Le calendrier.** Le jalon est au 2026-09-15. L'étape 0 est incompressible : sans elle on
repart dans le mur. Trois options :

- livrer au 15 avec l'étape 0 et des résultats réduits mais fiables ;
- livrer au 15 les seuls résultats qui ne dépendent pas du comptage, et annoncer le reste ;
- décaler.

**b. Ce qu'on dit à Axel, et quand.** Les chiffres déjà présentés, s'il y en a, sont faux.

**c. Le sort des sept fiches et des attaques.** Exclusion pure, ou traitement à part avec un
chapitre dédié.

---

## Ce qui survit probablement

À vérifier après recalcul, pas à supposer :

- **Le contenu textuel** — 94 % des avis supprimés sans faute visible. Les 509 avis revenus sont
  anciens, et les 399 avis des salles de sport sont sans texte à 68 %. Ni les uns ni les autres
  ne peuvent renverser ce chiffre, mais il doit être recalculé.
- **La forme de la courbe d'âge** — le risque culmine à 7-13 jours puis s'effondre. Les
  artefacts identifiés portent sur des avis anciens et devraient donc l'accentuer, pas la créer.

## Ce qui est le plus menacé

- **Le Test 2**, qui est le chiffre du livrable. Il mesure la mortalité du vieux stock, et c'est
  précisément sur le vieux stock que portent les artefacts. Le sens de l'erreur est incertain :
  les sept fiches sont dans le groupe de référence, ce qui devrait renforcer le résultat, mais
  d'autres artefacts non identifiés peuvent jouer dans l'autre sens.
- **Tout ce qui touche aux 24 fiches purgées**, dont sept n'ont rien perdu.
