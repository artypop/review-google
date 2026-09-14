---
date: 2026-09-06
projet: reviewflowz-analyse-google
titre: "Analyse B — dans une fiche qui perd des avis, lequel tombe ?"
statut: résultats
---

# Analyse B — dans une fiche qui perd des avis, lequel tombe ?

Produit par `scripts/analysis_b.py`.

> ## La réponse du propriétaire est datée depuis le 2026-09-14
>
> **L'effet passe de ×0,30 à ×0,40.** Seul ce facteur bouge ; les autres se déplacent de 1 à
> 5 %, ce qui est le réajustement normal du modèle quand une variable change. Même corpus,
> mêmes 514 fiches, mêmes 61 202 observations, mêmes 2 623 disparitions.
>
> **Ce qui était mesuré avant.** `has_reply` donnait l'état de la réponse au dernier passage du
> robot, recopié sur tous les passages précédents. Un avis supprimé au 3e jour n'avait pas eu le
> temps d'en recevoir une ; un avis observé 13 jours en avait reçu une. « Avoir une réponse »
> mesurait donc en partie « avoir survécu ».
>
> **Ce qui est mesuré maintenant.** La réponse ne compte qu'à partir du passage qui suit sa date
> réelle de publication (`reply_date`).
>
> **Deux chiffres à ne plus citer : « ×0,30 » et « répondre protège 3,7 fois ».**
>
> **Réserve, et elle est importante.** Le ×0,40 n'est pas comparable au ×1,02 de la régression
> sur le panel (`../../logistic-regression-study/2026-09-14-interpretation-panel.md`). Ce ne
> sont ni la même population, ni la même unité, ni le même contrôle de l'âge — voir la section
> « Pourquoi ce chiffre diffère de celui de la régression » plus bas.
>
> Ferme la divergence D9 de `../audit-methode.md`.

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
| 1 étoile | ×3.61 | — | non calculé |
| 2 étoiles | ×2.36 | — | non calculé |
| 3 étoiles | ×0.98 | — | non calculé |
| 5 étoiles | ×1.26 | — | non calculé |

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
| note seule, sans texte | ×1.02 | — | non calculé |
| 1 à 50 caractères | ×1.13 | — | non calculé |
| 151 à 400 caractères | ×1.12 | — | non calculé |
| plus de 400 caractères | ×0.99 | — | non calculé |

### Photos jointes

Comparé à : **aucune photo**.

| Modalité | Effet | Fourchette | Écart net ? |
|---|---:|---:|---|
| une photo | ×0.78 | — | non calculé |
| deux photos ou plus | ×0.71 | — | non calculé |

### Réponse du propriétaire

Comparé à : **sans réponse**.

| Modalité | Effet | Fourchette | Écart net ? |
|---|---:|---:|---|
| avec réponse du propriétaire | ×0.40 | — | non calculé |

### Langue de l'avis

Comparé à : **langue de la fiche**.

| Modalité | Effet | Fourchette | Écart net ? |
|---|---:|---:|---|
| autre langue | ×1.09 | — | non calculé |

### Avis modifié depuis publication

Comparé à : **non modifié**.

| Modalité | Effet | Fourchette | Écart net ? |
|---|---:|---:|---|
| modifié depuis publication | ×1.95 | — | non calculé |

### Niveau Local Guide de l'auteur

Comparé à : **niveau 1 à 3**.

| Modalité | Effet | Fourchette | Écart net ? |
|---|---:|---:|---|
| aucun niveau | ×1.54 | — | non calculé |
| niveau 4 ou 5 | ×1.20 | — | non calculé |
| niveau 6 et plus | ×0.70 | — | non calculé |

### Nombre d'avis publiés par l'auteur

Comparé à : **3 à 20 avis**.

| Modalité | Effet | Fourchette | Écart net ? |
|---|---:|---:|---|
| compteur à 0 | ×1.30 | — | non calculé |
| 1 ou 2 avis | ×1.02 | — | non calculé |
| 21 à 100 avis | ×0.71 | — | non calculé |
| plus de 100 avis | ×0.75 | — | non calculé |

### Auteur présent sur plusieurs fiches du panel

Comparé à : **une seule fiche**.

| Modalité | Effet | Fourchette | Écart net ? |
|---|---:|---:|---|
| plusieurs fiches | ×1.24 | — | non calculé |

### Auteur ayant publié plusieurs avis le même jour

Comparé à : **non**.

| Modalité | Effet | Fourchette | Écart net ? |
|---|---:|---:|---|
| rafale le même jour | ×5.09 | — | non calculé |

<!-- /genere:analyseb -->

## Pourquoi ce chiffre diffère de celui de la régression

L'analyse B donne **×0,40** pour la réponse du propriétaire. La régression sur le panel donne
**×1,02 [0,75 – 1,38]**
(`../../logistic-regression-study/2026-09-14-interpretation-panel.md`, section 3).

Les deux sont calculés sur la réponse datée. Ils ne se contredisent pas, ils ne mesurent pas la
même chose. Quatre différences, de la plus lourde à la plus légère.

| | Analyse B | Régression sur le panel |
|---|---|---|
| Population | avis de moins de 30 jours, sur les **514 fiches** ayant perdu au moins un avis récent | **225 757 avis** de 0 à 90 jours, sur 8 205 fiches |
| Unité comptée | l'observation : un avis à un passage du robot — **61 202** | l'avis — **225 757** |
| Ce que dit la variable | une réponse existait au début de **ce passage-là** | une réponse existait **avant le 11 août** |
| Contrôle de l'âge | 5 tranches, dont « 0 à 6 jours » en un seul bloc | logarithme de l'âge, continu |

**La dernière ligne est l'explication la plus probable de l'écart, et ce n'est qu'une
hypothèse.** Dans l'analyse B, les avis de 0 à 6 jours forment un seul groupe. Or c'est
exactement l'intervalle où les deux choses qu'on cherche à démêler bougent le plus vite : la
moitié des réponses arrivent dans la journée qui suit l'avis, et le risque de suppression
culmine au 7e jour. Deux avis du même bloc « 0 à 6 jours » peuvent donc avoir des risques très
différents et des probabilités d'avoir déjà une réponse très différentes, sans que le modèle
puisse les séparer. Il resterait alors, à l'intérieur du bloc, une part du mécanisme que le
datage était censé retirer.

**Le contrôle qui trancherait**, non lancé : refaire l'analyse B en découpant « 0 à 6 jours »
en jours pleins (0, 1, 2, 3, 4, 5, 6) et regarder si l'effet de la réponse se déplace encore
vers 1. S'il ne bouge plus, le ×0,40 tient et l'écart avec la régression vient de la
population. S'il continue de monter, l'effet restant était encore de l'âge.

**En attendant, ce qui est solide :** l'effet protecteur affiché par l'analyse B était
surestimé d'un tiers, et la régression sur le panel ne trouve aucune protection mesurable une
fois l'âge finement contrôlé. Les deux méthodes vont dans le même sens ; elles ne s'accordent
pas encore sur l'ampleur.
