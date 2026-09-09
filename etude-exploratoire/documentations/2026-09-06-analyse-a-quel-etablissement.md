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

**Être touché** — la fiche a-t-elle perdu au moins un avis récent ? Sur 2 516 établissements,
dont 396 touchés.

**L'ampleur** — parmi les fiches touchées, quelle part du stock récent est partie ? Sur les
396 fiches concernées, pondéré par leur nombre d'avis récents.

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

## Résultats

<!-- genere:analysea — regenere par scripts/analysis_a.py, ne pas editer a la main -->
## Être touché

### Vitesse de collecte — part du stock reçue en 30 jours

Comparé à : **1 à 3 %**.

| Modalité | Effet | Fourchette | Écart net ? |
|---|---:|---:|---|
| moins de 1 % | ×1.39 | 0.90 à 2.14 | non |
| 3 à 10 % | ×0.81 | 0.60 à 1.10 | non |
| 10 % et plus | ×0.55 | 0.26 à 1.14 | non |

### Secteur

Comparé à : **food_beverage**.

| Modalité | Effet | Fourchette | Écart net ? |
|---|---:|---:|---|
| automotive | ×1.52 | 1.13 à 2.02 | oui |
| healthcare | ×1.24 | 0.75 à 2.05 | non |
| home_services | ×3.94 | 2.92 à 5.32 | oui |
| hospitality | ×1.16 | 0.80 à 1.69 | non |
| travel | ×1.30 | 0.66 à 2.58 | non |
| wellness_fitness | ×1.68 | 1.24 à 2.28 | oui |

### Taille du groupe

Comparé à : **site unique**.

| Modalité | Effet | Fourchette | Écart net ? |
|---|---:|---:|---|
| groupe de 20 à 50 sites | ×1.27 | 0.60 à 2.68 | non |
| groupe de 4 à 10 sites | ×1.59 | 0.86 à 2.94 | non |

### Région

Comparé à : **Europe**.

| Modalité | Effet | Fourchette | Écart net ? |
|---|---:|---:|---|
| États-Unis | ×1.40 | 1.06 à 1.84 | oui |

### Nombre total d'avis de la fiche

Comparé à : **250 à 1 000**.

| Modalité | Effet | Fourchette | Écart net ? |
|---|---:|---:|---|
| moins de 100 | ×1.45 | 0.35 à 6.05 | non |
| 100 à 250 | ×1.55 | 1.01 à 2.39 | oui |
| plus de 1 000 | ×0.97 | 0.65 à 1.44 | non |

### Note moyenne de la fiche

Comparé à : **4,5 à 4,8**.

| Modalité | Effet | Fourchette | Écart net ? |
|---|---:|---:|---|
| moins de 4,0 | ×1.38 | 0.83 à 2.28 | non |
| 4,0 à 4,5 | ×0.92 | 0.64 à 1.33 | non |
| 4,8 et plus | ×0.92 | 0.60 à 1.41 | non |

### Nombre d'avis récents de la fiche

Comparé à : **25 à 60**.

| Modalité | Effet | Fourchette | Écart net ? |
|---|---:|---:|---|
| 10 à 25 avis récents | ×0.35 | 0.24 à 0.49 | oui |
| 60 à 150 | ×2.43 | 1.47 à 4.02 | oui |
| plus de 150 | ×5.87 | 2.52 à 13.69 | oui |

## Ampleur de la purge

### Vitesse de collecte — part du stock reçue en 30 jours

Comparé à : **1 à 3 %**.

| Modalité | Effet | Fourchette | Écart net ? |
|---|---:|---:|---|
| moins de 1 % | ×1.41 | 0.97 à 2.06 | non |
| 3 à 10 % | ×0.76 | 0.53 à 1.10 | non |
| 10 % et plus | ×2.00 | 0.80 à 4.98 | non |

### Secteur

Comparé à : **food_beverage**.

| Modalité | Effet | Fourchette | Écart net ? |
|---|---:|---:|---|
| automotive | ×0.79 | 0.42 à 1.51 | non |
| healthcare | ×2.34 | 1.50 à 3.65 | oui |
| home_services | ×2.79 | 2.00 à 3.89 | oui |
| hospitality | ×0.98 | 0.46 à 2.05 | non |
| travel | ×1.79 | 0.62 à 5.20 | non |
| wellness_fitness | ×4.07 | 1.75 à 9.49 | oui |

### Taille du groupe

Comparé à : **site unique**.

| Modalité | Effet | Fourchette | Écart net ? |
|---|---:|---:|---|
| groupe de 20 à 50 sites | ×1.25 | 0.77 à 2.03 | non |
| groupe de 4 à 10 sites | ×0.79 | 0.49 à 1.28 | non |

### Région

Comparé à : **Europe**.

| Modalité | Effet | Fourchette | Écart net ? |
|---|---:|---:|---|
| États-Unis | ×1.27 | 0.77 à 2.09 | non |

### Nombre total d'avis de la fiche

Comparé à : **250 à 1 000**.

| Modalité | Effet | Fourchette | Écart net ? |
|---|---:|---:|---|
| moins de 100 | ×4.88 | 2.58 à 9.23 | oui |
| 100 à 250 | ×0.90 | 0.44 à 1.86 | non |
| plus de 1 000 | ×0.48 | 0.25 à 0.93 | oui |

### Note moyenne de la fiche

Comparé à : **4,5 à 4,8**.

| Modalité | Effet | Fourchette | Écart net ? |
|---|---:|---:|---|
| moins de 4,0 | ×1.88 | 0.67 à 5.29 | non |
| 4,0 à 4,5 | ×0.97 | 0.50 à 1.87 | non |
| 4,8 et plus | ×1.59 | 1.16 à 2.20 | oui |

### Nombre d'avis récents de la fiche

Comparé à : **25 à 60**.

| Modalité | Effet | Fourchette | Écart net ? |
|---|---:|---:|---|
| 10 à 25 avis récents | ×1.07 | 0.72 à 1.58 | non |
| 60 à 150 | ×0.79 | 0.54 à 1.15 | non |
| plus de 150 | ×0.78 | 0.45 à 1.34 | non |

<!-- /genere:analysea -->
