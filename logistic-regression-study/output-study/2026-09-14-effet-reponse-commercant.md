---
date: 2026-09-14
projet: reviewflowz-analyse-google
titre: "Répondre vite à un avis le protège-t-il ?"
statut: résultats
---

# Répondre vite à un avis le protège-t-il ?

Produit par `08_effet_reponse_commercant.py`, précédé de
`../sql/controle_C_reponses_au_jalon.bqsql`. Sorties dans `2026-09-14-sorties-08/`.

C'est la question du client d'Axel. Elle a une réponse, avec une condition importante.

## Le résultat

**Une fois les quatre chaînes antiparasitaires américaines écartées, répondre dans les deux
jours divise le risque de suppression par 1,8 : ×0,56, fourchette [0,37 – 0,85], p = 0,007.**
Dénominateur : 14 170 avis encore en ligne à la fin de leur 2e jour, dont 5 604 avec une
réponse (39,5 %), et 316 suppressions entre le 3e et le 8e jour.

**Sur le corpus complet, l'effet n'est pas mesurable : ×0,79 [0,53 – 1,16], p = 0,232.**
Dénominateur : 15 193 avis, 505 suppressions.

**Comment le dire à l'oral ou dans un mail :** « répondre dans les deux jours divise à peu près
par deux le risque qu'un avis récent soit supprimé, sauf sur quatre chaînes américaines de
traitement antiparasitaire où Google supprime des avis pour une raison qu'on n'a pas identifiée.
Ces quatre chaînes sont assez grosses pour effacer l'effet quand on regarde tout le monde
ensemble. »

Annoncer le ×0,56 sans dire qu'il exclut ces quatre chaînes serait faux.

## Ce que le montage compare

Le piège de cette question est connu : un avis qui a survécu trois semaines a eu trois semaines
pour recevoir une réponse, un avis supprimé au troisième jour n'en a eu que trois. Compter les
réponses à la fin de l'histoire revient en partie à compter qui a survécu. C'est ce défaut qui
donnait « répondre protège 3,7 fois » dans l'analyse B.

Le montage l'évite par construction :

```
 jour 0        jour 2                          jour 8
 |-------------|-------------------------------|
 publication   JALON                           fin de la fenêtre
               tout le monde est en ligne      on compte qui a disparu
               on note qui a déjà une réponse  entre le 3e et le 8e jour
```

Personne ne peut recevoir de réponse après sa suppression, puisque la réponse est relevée avant
que la période de risque commence. L'âge n'a pas à être contrôlé : tous les avis ont le même âge
au jalon et la même durée d'exposition ensuite.

Population : les 15 248 avis publiés du 11 au 16 août, seuls avis dont on a vu les premiers
jours. 55 ont disparu avant le jalon et sortent de l'étude ; il en reste **15 193**.

## Pourquoi les quatre chaînes changent tout

Elles pèsent **1 021 avis sur 15 193, soit 6,7 %**, et portent **189 des 505 suppressions, soit
37,4 %**. Leur taux de suppression est de 18,5 %, contre 2,2 % sur le reste de la population.

Chez elles, Google retire des avis positifs, et la part d'avis répondus y est la même
qu'ailleurs (38,0 % contre 39,5 %). La réponse n'y marque donc rien : elle accompagne des avis
que Google retire pour une raison que l'étude n'a pas identifiée. Ces 189 suppressions, très
concentrées, tirent l'effet moyen vers 1.

Cela se voit avant tout modèle. Taux de suppression entre le 3e et le 8e jour, pour 10 000 avis
du groupe :

| | Corpus complet | Sans les chaînes |
|---|---:|---:|
| Sans réponse au jalon | 323,9 | 253,3 |
| Avec réponse au jalon | **345,5** | **176,7** |
| Rapport brut | ×1,07 | ×0,70 |

Sur le corpus complet, l'avis répondu est **légèrement plus** supprimé. Une fois les chaînes
retirées, il l'est nettement moins. Le modèle ajusté renforce encore l'écart, de ×0,70 à ×0,56.

## L'effet tient quand on déplace le jalon

Le jalon à 2 jours est un choix. Les réponses arrivent vite — 19,5 % le jour même, 14,4 % à
1 jour, 5,5 % à 2 jours, et 50,6 % des avis n'en ont aucune — donc couper à 2 jours n'est pas
neutre. Quatre jalons ont été essayés, la fenêtre se terminant chaque fois au 8e jour :

| Jalon | Avis | Avec réponse | Suppressions | Corpus complet | Sans les chaînes |
|---|---:|---:|---:|---:|---:|
| fin du jour 1 | 14 216 | 33,7 % | 362 | ×0,86 [0,59 – 1,24] | **×0,59** [0,40 – 0,88] |
| fin du jour 2 | 14 170 | 39,5 % | 316 | ×0,79 [0,53 – 1,16] | **×0,56** [0,37 – 0,85] |
| fin du jour 3 | 14 146 | 43,4 % | 292 | ×0,70 [0,46 – 1,05] | **×0,46** [0,30 – 0,72] |
| fin du jour 4 | 14 136 | 45,7 % | 282 | ×0,71 [0,47 – 1,08] | **×0,48** [0,31 – 0,76] |

Les colonnes « Avis », « Avec réponse » et « Suppressions » sont celles du passage sans les
chaînes. Les quatre passages sans les chaînes excluent 1, avec des p de 0,001 à 0,009. Les
quatre passages sur le corpus complet contiennent 1. Le résultat ne dépend donc pas du seuil
choisi ; il dépend du retrait des chaînes.

## Les autres effets du même modèle

Sur le passage sans les chaînes, jalon 2 (`08_coefficients_jalon2_fenetre6_sans_enseignes.csv`) :

| Caractéristique | Risque relatif | Fourchette |
|---|---:|---|
| Avis 1 étoile (réf. 5 étoiles) | ×3,10 | [1,82 – 5,28] |
| Compte sans niveau Local Guide | ×2,39 | [1,54 – 3,69] |
| Établissement américain | ×2,06 | [1,15 – 3,68] |
| Secteur home_services | ×2,13 | [0,97 – 4,68] |
| **Réponse dans les 2 jours** | **×0,56** | **[0,37 – 0,85]** |

Ils vont dans le même sens que la régression sur le panel entier, ce qui est rassurant sur le
montage : il ne produit pas un monde à part.

## Ce que ce résultat ne dit pas

- **Le sens de la causalité n'est pas établi.** Le commerçant qui répond en deux jours est aussi
  celui qui surveille sa fiche, qui signale les avis qu'il juge illégitimes, et qui soigne sa
  présence en ligne. Le modèle contrôle le secteur, la région, la taille de la fiche, la note et
  le profil de l'auteur. Il ne contrôle pas l'attention portée à la fiche. Répondre pourrait
  n'être que le marqueur de cette attention, sans en être la cause.
- **Une réponse retirée est invisible.** `changed_fields` ne contient que `star` et `text`,
  jamais `reply`. Un avis dont la réponse a été effacée avant le dernier passage est compté
  « sans réponse ».
- **Le résultat porte sur les 8 premiers jours de vie de l'avis.** Le pic de
  suppression tombe au 7e jour, donc la fenêtre couvre l'essentiel du risque, mais pas tout.
- **Il ne vaut pas pour les quatre chaînes antiparasitaires.** Chez elles, aucune caractéristique
  disponible n'explique les suppressions, la réponse pas davantage.
- **La puissance est limitée.** Avec 316 suppressions, le montage ne pouvait repérer qu'une
  protection d'au moins 45 % ou une aggravation d'au moins 83 %. Un résultat non significatif
  sur le corpus complet ne prouve donc pas l'absence d'effet.

## Où ce chiffre se place par rapport aux deux autres

Trois mesures de la réponse du commerçant coexistent. Elles ne portent ni sur la même
population, ni sur la même question.

| Chiffre | Ce qu'il mesure | Population |
|---|---|---|
| **×1,02** [0,75 – 1,38] | une réponse arrivée **avant le 11 août** | 225 757 avis de 0 à 90 jours |
| **×0,40** | une réponse présente **au passage précédent** | 61 202 observations d'avis de moins de 30 jours, sur 514 fiches touchées |
| **×0,56** [0,37 – 0,85] | une réponse arrivée **dans les 2 premiers jours** | 14 170 avis nés du 11 au 16 août, hors chaînes |

Le ×1,02 répond à « un avis qui porte déjà une réponse depuis longtemps est-il mieux protégé ? »
La réponse est non.

Le ×0,56 répond à « répondre vite à un avis qui vient de tomber sert-il à quelque chose ? »
La réponse est oui, hors des quatre chaînes.

C'est la seconde question que pose le client d'Axel.

**« ×0,30 » et « répondre protège 3,7 fois » restent non citables** : ils venaient de la réponse
figée à son état final.

## Régénérer

Depuis `logistic-regression-study/` :

```bash
python python/08_effet_reponse_commercant.py                             # corpus complet
python python/08_effet_reponse_commercant.py --sans-enseignes-signalees  # à citer
python python/08_effet_reponse_commercant.py --jalon-jours 3 --fenetre-jours 5 --sans-enseignes-signalees
```

Le contrôle préalable, en lecture seule : `../sql/controle_C_reponses_au_jalon.bqsql`. Ses quatre
requêtes donnent le dénominateur, le croisement qui décide, la répartition des délais de réponse
et le poids des enseignes signalées.
