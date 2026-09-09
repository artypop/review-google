---
date: 2026-09-06
projet: reviewflowz-analyse-google
titre: "Analyse B — dans une fiche qui perd des avis, lequel tombe ?"
statut: résultats
---

# Analyse B — dans une fiche qui perd des avis, lequel tombe ?

Produit par `scripts/analysis_b.py`.

## Ce que compare cette analyse

**Uniquement des avis d'une même fiche, un même jour.** La question posée est : parmi les avis
de cet établissement encore en ligne ce jour-là, lesquels ont disparu au passage suivant ?

C'est ce qui distingue l'analyse B des tableaux facteur par facteur. Là-bas, on comparait tous
les avis du panel entre eux, et un écart pouvait venir du type d'établissement plutôt que de
l'avis. Ici, tout ce qui est propre à la fiche s'annule : secteur, pays, taille, clientèle,
politique de modération. Et la date s'annule aussi, donc les jours de forte suppression ne
faussent plus la comparaison.

**Les fiches purgées cessent de peser.** Quand Google efface tous les avis d'une fiche un jour
donné, il n'y a plus de survivant à comparer : la journée n'apporte rien et sort du calcul. Plus
besoin de retirer les fiches problématiques à la main.

## Sur quoi porte le calcul

- **514 établissements**, ceux qui ont perdu au moins un avis récent
- **61 202 observations** — un avis vérifié à un passage du robot
- **2 623 disparitions** effectivement comparables
- **14 disparitions écartées** : elles surviennent lors de purges totales, où aucun avis
  de la fiche ne survit ce jour-là. Aucune comparaison n'y est possible.

## Comment lire les résultats

**L'effet** se lit comme un rapport de risque, la modalité de référence valant 1. « ×2 » signifie
deux fois plus supprimé qu'un avis identique par ailleurs, dans la même fiche, le même jour.

**La fourchette** est obtenue en retirant et rejouant au hasard les établissements 0 fois :
on rééchantillonne les établissements et non les lignes,
parce que deux avis d'une même fiche ne sont pas deux informations indépendantes — les marges
affichées par défaut par un modèle l'oublient et sont trop étroites.



**Écart net** vaut « oui » quand la fourchette ne contient pas 1, c'est-à-dire quand on peut
exclure l'absence d'effet.

## Ce qui ne peut pas figurer ici

Le secteur, la région et la taille du groupe sont identiques pour tous les avis d'une même fiche.
L'analyse B ne peut donc rien en dire — c'est le prix de sa rigueur, et c'est l'objet de
l'analyse A.

## Résultats

<!-- genere:analyseb — regenere par scripts/analysis_b.py, ne pas editer a la main -->
### Note de l'avis

Comparé à : **4 étoiles**.

| Modalité | Effet | Fourchette | Écart net ? |
|---|---:|---:|---|
| 1 étoile | ×3.57 | — | non calculé |
| 2 étoiles | ×2.24 | — | non calculé |
| 3 étoiles | ×0.94 | — | non calculé |
| 5 étoiles | ×1.24 | — | non calculé |

### Âge de l'avis au moment du passage

Comparé à : **7 à 13 jours**.

| Modalité | Effet | Fourchette | Écart net ? |
|---|---:|---:|---|
| 0 à 6 jours | ×0.44 | — | non calculé |
| 14 à 20 jours | ×0.31 | — | non calculé |
| 21 à 29 jours | ×0.16 | — | non calculé |
| 30 jours et plus | ×0.19 | — | non calculé |

### Texte de l'avis

Comparé à : **51 à 150 caractères**.

| Modalité | Effet | Fourchette | Écart net ? |
|---|---:|---:|---|
| note seule, sans texte | ×1.00 | — | non calculé |
| 1 à 50 caractères | ×1.12 | — | non calculé |
| 151 à 400 caractères | ×1.13 | — | non calculé |
| plus de 400 caractères | ×1.01 | — | non calculé |

### Photos jointes

Comparé à : **aucune photo**.

| Modalité | Effet | Fourchette | Écart net ? |
|---|---:|---:|---|
| une photo | ×0.79 | — | non calculé |
| deux photos ou plus | ×0.70 | — | non calculé |

### Réponse du propriétaire

Comparé à : **sans réponse**.

| Modalité | Effet | Fourchette | Écart net ? |
|---|---:|---:|---|
| avec réponse du propriétaire | ×0.30 | — | non calculé |

### Langue de l'avis

Comparé à : **langue de la fiche**.

| Modalité | Effet | Fourchette | Écart net ? |
|---|---:|---:|---|
| autre langue | ×1.11 | — | non calculé |

### Avis modifié depuis publication

Comparé à : **non modifié**.

| Modalité | Effet | Fourchette | Écart net ? |
|---|---:|---:|---|
| modifié depuis publication | ×1.94 | — | non calculé |

### Niveau Local Guide de l'auteur

Comparé à : **niveau 1 à 3**.

| Modalité | Effet | Fourchette | Écart net ? |
|---|---:|---:|---|
| aucun niveau | ×1.55 | — | non calculé |
| niveau 4 ou 5 | ×1.18 | — | non calculé |
| niveau 6 et plus | ×0.70 | — | non calculé |

### Nombre d'avis publiés par l'auteur

Comparé à : **3 à 20 avis**.

| Modalité | Effet | Fourchette | Écart net ? |
|---|---:|---:|---|
| compteur à 0 | ×1.29 | — | non calculé |
| 1 ou 2 avis | ×1.01 | — | non calculé |
| 21 à 100 avis | ×0.72 | — | non calculé |
| plus de 100 avis | ×0.75 | — | non calculé |

### Auteur présent sur plusieurs fiches du panel

Comparé à : **une seule fiche**.

| Modalité | Effet | Fourchette | Écart net ? |
|---|---:|---:|---|
| plusieurs fiches | ×1.23 | — | non calculé |

### Auteur ayant publié plusieurs avis le même jour

Comparé à : **non**.

| Modalité | Effet | Fourchette | Écart net ? |
|---|---:|---:|---|
| rafale le même jour | ×5.30 | — | non calculé |

<!-- /genere:analyseb -->
