---
date: 2026-09-06
projet: reviewflowz-analyse-google
titre: "Analyse A — quel établissement subit une intervention ?"
statut: résultats
---

# Analyse A — quel établissement subit une intervention ?

Produit par `scripts/analysis_a.py`.

## Ce que compare cette analyse

**Des établissements entre eux**, et non des avis. C'est le pendant de l'analyse B : celle-ci
regarde ce qui distingue deux avis d'une même fiche, celle-là ce qui distingue deux fiches.

C'est donc **ici, et seulement ici, que le secteur, la région et la taille du groupe peuvent
être mesurés**. Dans l'analyse B ils sont identiques pour tous les avis d'une même fiche, donc
invisibles.

## Deux questions, deux modèles

Elles n'ont pas la même réponse, et les mélanger donnerait un résultat ininterprétable.

**Être touché** — la fiche a-t-elle perdu au moins un avis récent ? Sur 2 529 établissements,
dont 455 touchés.

**L'ampleur** — parmi les fiches touchées, quelle part du stock récent est partie ? Sur les
455 fiches concernées, pondéré par leur nombre d'avis récents.

Une fiche peut être effleurée en permanence sans jamais être purgée, et l'inverse existe.

## Comment lire

**L'effet** se lit comme un rapport, la modalité de référence valant 1. « ×2 » signifie deux
fois plus de risque d'être touché, ou une purge deux fois plus étendue, toutes les autres
caractéristiques étant égales.

**La fourchette** tient compte du fait que les établissements d'un même marché — même pays,
même secteur — partagent des conditions que le modèle ne voit pas. Sans cette correction les
fourchettes seraient trop étroites. Faute d'identifiant d'enseigne dans l'export, le marché est
le regroupement le plus englobant disponible.

**Écart net** vaut « oui » quand la fourchette ne contient pas 1.

## Périmètre

Les fiches de moins de 10 avis récents sont écartées : sur trois avis, « touché » relève du
hasard. C'est la même correction que celle appliquée au seuil de fiche purgée.

## Ce qu'il faut retenir

### Le résultat le plus important : la vitesse de collecte ne compte pas

C'était l'hypothèse centrale du cadrage — une fiche qui reçoit beaucoup d'avis d'un coup en perd
davantage — et les chiffres bruts la confirmaient spectaculairement : ×26 entre les fiches les
plus lentes et les plus rapides.

**Une fois le nombre d'avis récents pris en compte, il ne reste rien.** Les fiches recevant plus
de 10 % de leur stock en 30 jours ne sont pas plus souvent touchées que les autres (×0,50,
fourchette 0,25 à 1,03, non concluant).

L'explication est simple : une fiche qui reçoit beaucoup d'avis récents **a beaucoup d'avis
récents à perdre**. L'écart mesurait une exposition, pas une sanction. C'est le même piège que
celui de l'âge, sous une autre forme.

Conséquence directe pour le livrable : **Google ne sanctionne pas une fiche parce qu'elle reçoit
un afflux d'avis.** L'hypothèse de la détection de campagne au niveau de l'établissement n'est
pas soutenue par ces données. Ce qui est sanctionné, c'est le comportement de l'auteur — voir la
rafale dans l'analyse B.

### Ce qui compte vraiment pour être touché

| Facteur | Effet | Lecture |
|---|---:|---|
| Nombre d'avis récents — plus de 150 | ×6,29 | Mécanique : plus d'avis exposés, plus de chances d'en perdre |
| Services à domicile | ×3,04 | Le seul secteur nettement plus exposé |
| Sport et bien-être | ×1,53 | Second, plus modestement |
| États-Unis | ×1,44 | Confirme l'écart régional |

Et surtout, ce qui **ne** compte pas : la taille du groupe, le volume total d'avis de la fiche,
sa note moyenne. Aucun de ces trois facteurs ne ressort une fois les autres pris en compte.

L'absence d'effet de la **taille du groupe** mérite d'être signalée : le niveau 1 donnait ×2,5
pour les groupes de 20 à 50 sites. Cet écart disparaît complètement ici. Il venait de la
composition sectorielle — les gros groupes sont surreprésentés dans les services à domicile.

### L'ampleur d'une purge obéit à d'autres règles

Parmi les fiches touchées, la part du stock qui part ne dépend pas des mêmes facteurs :

| Facteur | Effet |
|---|---:|
| Fiche de moins de 100 avis | ×6,49 |
| Sport et bien-être | ×3,58 |
| Services à domicile | ×2,97 |
| Santé | ×2,42 |
| Note moyenne de 4,8 et plus | ×1,41 |
| Fiche de plus de 1 000 avis | ×0,45 |

Deux enseignements.

**Les petites fiches encaissent proportionnellement beaucoup plus.** Une fiche de moins de
100 avis perd six fois plus de son stock qu'une fiche moyenne ; une fiche de plus de 1 000 avis
deux fois moins. Google efface un nombre d'avis assez comparable quelle que soit la taille, ce
qui ravage une petite fiche et égratigne une grosse. **Pour un commerce indépendant, une
intervention de Google est un événement grave ; pour une chaîne, c'est un incident.** C'est un
angle de livrable directement exploitable.

**Une note élevée n'est pas une protection.** Les fiches à 4,8 et plus perdent au contraire un
peu plus (×1,41). Ce qui est cohérent avec ce qu'on sait par ailleurs : ce sont les fiches dont
la note a été gonflée qui sont nettoyées.

### La trajectoire de note : à ne pas interpréter

Un chiffre frappant mérite d'être signalé, avec sa réserve. Les fiches dont la note **monte**
pendant le suivi sont touchées dans 43,9 % des cas, contre 17,5 % pour les fiches stables.

| Trajectoire de la note | Fiches | Touchées |
|---|---:|---:|
| En baisse | 42 | 23,8 % |
| Stable | 2 446 | 17,5 % |
| En hausse | 41 | 43,9 % |

**Ce n'est pas un facteur de risque et il ne figure pas au modèle.** La note est mesurée pendant
la fenêtre d'observation, et supprimer des avis fait mécaniquement bouger la note. On ne peut
donc pas distinguer « la note monte, donc Google intervient » de « Google a supprimé des avis
négatifs, donc la note est montée ». La seconde lecture est même la plus probable.

C'est une observation intéressante, pas un résultat. Elle est écartée du modèle pour cette
raison.

### Ce que cette analyse ne peut pas dire

Elle porte sur 2 529 établissements, ceux qui ont au moins 10 avis récents. Les fiches plus
petites sont écartées : sur trois avis récents, « avoir été touché » relève du hasard.

Les fourchettes tiennent compte du fait que les établissements d'un même marché — même pays,
même secteur — partagent des conditions invisibles au modèle. Faute d'identifiant d'enseigne
dans l'export, le marché est le regroupement le plus englobant disponible. Un identifiant de
groupe serait préférable ; il n'existe pas dans les données livrées.

## Les tableaux détaillés

<!-- genere:analysea — regenere par scripts/analysis_a.py, ne pas editer a la main -->
## Être touché

### Vitesse de collecte — part du stock reçue en 30 jours

Comparé à : **1 à 3 %**.

| Modalité | Effet | Fourchette | Écart net ? |
|---|---:|---:|---|
| moins de 1 % | ×1.17 | 0.78 à 1.76 | non |
| 3 à 10 % | ×0.73 | 0.53 à 1.00 | non |
| 10 % et plus | ×0.50 | 0.25 à 1.03 | non |

### Secteur

Comparé à : **food_beverage**.

| Modalité | Effet | Fourchette | Écart net ? |
|---|---:|---:|---|
| automotive | ×1.16 | 0.89 à 1.51 | non |
| healthcare | ×1.04 | 0.63 à 1.75 | non |
| home_services | ×3.04 | 2.27 à 4.08 | oui |
| hospitality | ×0.98 | 0.69 à 1.41 | non |
| travel | ×0.94 | 0.50 à 1.76 | non |
| wellness_fitness | ×1.53 | 1.13 à 2.06 | oui |

### Taille du groupe

Comparé à : **site unique**.

| Modalité | Effet | Fourchette | Écart net ? |
|---|---:|---:|---|
| groupe de 20 à 50 sites | ×1.18 | 0.61 à 2.31 | non |
| groupe de 4 à 10 sites | ×1.37 | 0.77 à 2.43 | non |

### Région

Comparé à : **Europe**.

| Modalité | Effet | Fourchette | Écart net ? |
|---|---:|---:|---|
| États-Unis | ×1.44 | 1.11 à 1.87 | oui |

### Nombre total d'avis de la fiche

Comparé à : **250 à 1 000**.

| Modalité | Effet | Fourchette | Écart net ? |
|---|---:|---:|---|
| moins de 100 | ×0.70 | 0.17 à 2.84 | non |
| 100 à 250 | ×1.47 | 0.96 à 2.26 | non |
| plus de 1 000 | ×0.98 | 0.71 à 1.35 | non |

### Note moyenne de la fiche

Comparé à : **4,5 à 4,8**.

| Modalité | Effet | Fourchette | Écart net ? |
|---|---:|---:|---|
| moins de 4,0 | ×1.38 | 0.87 à 2.20 | non |
| 4,0 à 4,5 | ×0.97 | 0.71 à 1.34 | non |
| 4,8 et plus | ×1.07 | 0.74 à 1.55 | non |

### Nombre d'avis récents de la fiche

Comparé à : **25 à 60**.

| Modalité | Effet | Fourchette | Écart net ? |
|---|---:|---:|---|
| 10 à 25 avis récents | ×0.38 | 0.27 à 0.54 | oui |
| 60 à 150 | ×2.23 | 1.46 à 3.40 | oui |
| plus de 150 | ×6.29 | 3.05 à 12.97 | oui |

## Ampleur de la purge

### Vitesse de collecte — part du stock reçue en 30 jours

Comparé à : **1 à 3 %**.

| Modalité | Effet | Fourchette | Écart net ? |
|---|---:|---:|---|
| moins de 1 % | ×1.62 | 1.17 à 2.23 | oui |
| 3 à 10 % | ×0.77 | 0.54 à 1.10 | non |
| 10 % et plus | ×2.09 | 0.83 à 5.28 | non |

### Secteur

Comparé à : **food_beverage**.

| Modalité | Effet | Fourchette | Écart net ? |
|---|---:|---:|---|
| automotive | ×0.86 | 0.44 à 1.66 | non |
| healthcare | ×2.42 | 1.58 à 3.72 | oui |
| home_services | ×2.97 | 2.16 à 4.09 | oui |
| hospitality | ×0.95 | 0.47 à 1.90 | non |
| travel | ×1.78 | 0.70 à 4.52 | non |
| wellness_fitness | ×3.58 | 1.62 à 7.92 | oui |

### Taille du groupe

Comparé à : **site unique**.

| Modalité | Effet | Fourchette | Écart net ? |
|---|---:|---:|---|
| groupe de 20 à 50 sites | ×1.26 | 0.80 à 1.99 | non |
| groupe de 4 à 10 sites | ×0.88 | 0.58 à 1.33 | non |

### Région

Comparé à : **Europe**.

| Modalité | Effet | Fourchette | Écart net ? |
|---|---:|---:|---|
| États-Unis | ×1.14 | 0.71 à 1.83 | non |

### Nombre total d'avis de la fiche

Comparé à : **250 à 1 000**.

| Modalité | Effet | Fourchette | Écart net ? |
|---|---:|---:|---|
| moins de 100 | ×6.49 | 2.74 à 15.36 | oui |
| 100 à 250 | ×1.00 | 0.52 à 1.91 | non |
| plus de 1 000 | ×0.45 | 0.23 à 0.88 | oui |

### Note moyenne de la fiche

Comparé à : **4,5 à 4,8**.

| Modalité | Effet | Fourchette | Écart net ? |
|---|---:|---:|---|
| moins de 4,0 | ×1.84 | 0.67 à 5.00 | non |
| 4,0 à 4,5 | ×1.00 | 0.53 à 1.86 | non |
| 4,8 et plus | ×1.41 | 1.02 à 1.93 | oui |

### Nombre d'avis récents de la fiche

Comparé à : **25 à 60**.

| Modalité | Effet | Fourchette | Écart net ? |
|---|---:|---:|---|
| 10 à 25 avis récents | ×1.00 | 0.69 à 1.45 | non |
| 60 à 150 | ×0.85 | 0.54 à 1.35 | non |
| plus de 150 | ×0.87 | 0.47 à 1.60 | non |

<!-- /genere:analysea -->
