---
date: 2026-09-06
projet: reviewflowz-analyse-google
titre: "Analyse B — dans une fiche qui perd des avis, lequel tombe ?"
statut: résultats
---

# Analyse B — dans une fiche qui perd des avis, lequel tombe ?

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

- **584 établissements**, ceux qui ont perdu au moins un avis récent
- **64 442 observations** — un avis vérifié à un passage du robot
- **2 828 disparitions** effectivement comparables
- **25 disparitions écartées** : elles surviennent lors de purges totales, où aucun avis
  de la fiche ne survit ce jour-là. Aucune comparaison n'y est possible.

## Comment lire les résultats

**L'effet** se lit comme un rapport de risque, la modalité de référence valant 1. « ×2 » signifie
deux fois plus supprimé qu'un avis identique par ailleurs, dans la même fiche, le même jour.

**La fourchette** est obtenue en retirant et rejouant au hasard les établissements
0 fois. On rééchantillonne les établissements et non les lignes, parce que deux avis
d'une même fiche ne sont pas deux informations indépendantes — les marges d'erreur affichées par
défaut par un modèle l'oublient et sont trop étroites.

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
| 1 étoile | ×3.33 | 2.17 à 5.12 | oui |
| 2 étoiles | ×2.07 | 1.22 à 3.51 | oui |
| 3 étoiles | ×0.81 | 0.42 à 1.55 | non |
| 5 étoiles | ×1.12 | 0.88 à 1.43 | non |

### Âge de l'avis au moment du passage

Comparé à : **7 à 13 jours**.

| Modalité | Effet | Fourchette | Écart net ? |
|---|---:|---:|---|
| 0 à 6 jours | ×0.46 | 0.37 à 0.57 | oui |
| 14 à 20 jours | ×0.29 | 0.24 à 0.37 | oui |
| 21 à 29 jours | ×0.14 | 0.10 à 0.19 | oui |
| 30 jours et plus | ×0.18 | 0.14 à 0.23 | oui |

### Texte de l'avis

Comparé à : **51 à 150 caractères**.

| Modalité | Effet | Fourchette | Écart net ? |
|---|---:|---:|---|
| note seule, sans texte | ×0.95 | 0.81 à 1.13 | non |
| 1 à 50 caractères | ×1.09 | 0.92 à 1.30 | non |
| 151 à 400 caractères | ×1.15 | 0.98 à 1.35 | non |
| plus de 400 caractères | ×0.96 | 0.73 à 1.26 | non |

### Photos jointes

Comparé à : **aucune photo**.

| Modalité | Effet | Fourchette | Écart net ? |
|---|---:|---:|---|
| une photo | ×0.77 | 0.57 à 1.03 | non |
| deux photos ou plus | ×0.80 | 0.57 à 1.12 | non |

### Réponse du propriétaire

Comparé à : **sans réponse**.

| Modalité | Effet | Fourchette | Écart net ? |
|---|---:|---:|---|
| avec réponse du propriétaire | ×0.27 | 0.20 à 0.38 | oui |

### Langue de l'avis

Comparé à : **langue de la fiche**.

| Modalité | Effet | Fourchette | Écart net ? |
|---|---:|---:|---|
| autre langue | ×1.11 | 0.84 à 1.48 | non |

### Avis modifié depuis publication

Comparé à : **non modifié**.

| Modalité | Effet | Fourchette | Écart net ? |
|---|---:|---:|---|
| modifié depuis publication | ×2.00 | 1.63 à 2.45 | oui |

### Niveau Local Guide de l'auteur

Comparé à : **niveau 1 à 3**.

| Modalité | Effet | Fourchette | Écart net ? |
|---|---:|---:|---|
| aucun niveau | ×1.66 | 1.32 à 2.09 | oui |
| niveau 4 ou 5 | ×1.16 | 0.96 à 1.40 | non |
| niveau 6 et plus | ×0.71 | 0.43 à 1.15 | non |

### Nombre d'avis publiés par l'auteur

Comparé à : **3 à 20 avis**.

| Modalité | Effet | Fourchette | Écart net ? |
|---|---:|---:|---|
| compteur à 0 | ×1.20 | 0.94 à 1.53 | non |
| 1 ou 2 avis | ×1.00 | 0.86 à 1.15 | non |
| 21 à 100 avis | ×0.72 | 0.55 à 0.94 | oui |
| plus de 100 avis | ×0.79 | 0.42 à 1.51 | non |

### Auteur présent sur plusieurs fiches du panel

Comparé à : **une seule fiche**.

| Modalité | Effet | Fourchette | Écart net ? |
|---|---:|---:|---|
| plusieurs fiches | ×0.94 | 0.75 à 1.18 | non |

### Auteur ayant publié plusieurs avis le même jour

Comparé à : **non**.

| Modalité | Effet | Fourchette | Écart net ? |
|---|---:|---:|---|
| rafale le même jour | ×26.45 | 17.66 à 39.64 | oui |

<!-- /genere:analyseb -->
