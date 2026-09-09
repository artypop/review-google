---
date: 2026-09-06
projet: reviewflowz-analyse-google
titre: "Contrôle de robustesse — sans les fiches attaquées"
statut: résultats
---

# Contrôle de robustesse — sans les fiches attaquées

Produit par `scripts/controle_robustesse.py`.

## Pourquoi ce contrôle est obligatoire

24 établissements portent 958 suppressions, 18 % du total. Deux d'entre eux, des salles de
sport espagnoles, en portent 399 à eux seuls. Un modèle ajusté sur l'ensemble peut très bien
décrire ces fiches plutôt que la modération de Google.

La liste des fiches est dans `data/resultats/fiches_massivement_purgees.csv`. Le seuil est
défini dans `scripts/build_tables.py` : plus de 5 % du stock perdu **et** au moins 10
suppressions — le plancher en volume évite qu'une fiche de 2 avis dont 1 supprimé compte comme
« purgée à 50 % ».

## Comment lire le verdict

Le critère est fixé avant d'avoir regardé les chiffres :

- **ne tient pas** — l'effet change de sens, il passe de l'autre côté de 1 ;
- **fragile** — l'amplitude est divisée ou multipliée par plus de 2 ;
- **à surveiller** — l'amplitude bouge de plus de moitié ;
- **tient** — le reste.

Les fourchettes ne figurent pas ici : le contrôle porte sur le déplacement des effets, pas sur
leur significativité, qui est traitée dans les notes A et B.

## Résultats

<!-- genere:controle — regenere par scripts/controle_robustesse.py, ne pas editer a la main -->

### Périmètres comparés

| | Avec les fiches attaquées | Sans |
|---|---:|---:|
| Analyse A — établissements | 2 516 | 2 512 |
| Analyse B — établissements | 514 | 510 |
| Analyse B — observations | 61 202 | 58 400 |
| Analyse B — disparitions | 2 623 | 2 241 |

### Verdict d'ensemble sur 68 effets testés

- **49 tiennent** ;
- 8 sont des **non-effets stables** — voisins de 1 dans les deux versions, ils ne mesurent rien, ni avant ni après ;
- 5 sont **fragiles** ;
- 6 **ne tiennent pas** ou ne sont pas exploitables.

#### Ce qui ne tient pas, ou n'est pas exploitable

| Analyse | Facteur | Modalité | Avec | Sans | Verdict |
|---|---|---|---:|---:|---|
| A | Nombre total d'avis de la fiche | 100 à 250 | ×0.90 | ×1.77 | NE TIENT PAS — change de sens |
| A | Note moyenne de la fiche | moins de 4,0 | ×1.88 | ×0.66 | NE TIENT PAS — change de sens |
| A | Secteur | automotive | ×0.79 | ×1.38 | NE TIENT PAS — change de sens |
| A | Secteur | hospitality | ×0.98 | ×1.40 | NE TIENT PAS — change de sens |
| A | Taille du groupe | groupe de 20 à 50 sites | ×1.25 | ×0.94 | NE TIENT PAS — change de sens |
| A | Vitesse de collecte — part du stock reçue en 30 jours | 10 % et plus | ×2.00 | ×0.74 | NE TIENT PAS — change de sens |

#### Ce qui est fragile

| Analyse | Facteur | Modalité | Avec | Sans | Verdict |
|---|---|---|---:|---:|---|
| A | Nombre d'avis récents de la fiche | plus de 150 | ×0.78 | ×0.50 | à surveiller — amplitude bouge de plus de moitié |
| A | Nombre total d'avis de la fiche | moins de 100 | ×4.88 | ×7.65 | à surveiller — amplitude bouge de plus de moitié |
| A | Nombre total d'avis de la fiche | plus de 1 000 | ×0.48 | ×0.87 | à surveiller — amplitude bouge de plus de moitié |
| A | Note moyenne de la fiche | 4,0 à 4,5 | ×0.97 | ×0.64 | à surveiller — amplitude bouge de plus de moitié |
| A | Secteur | wellness_fitness | ×4.07 | ×1.82 | fragile — amplitude divisée ou multipliée par plus de 2 |

#### Tous les effets, côte à côte

##### Ampleur de la purge

| Facteur | Modalité | Avec | Sans | Verdict |
|---|---|---:|---:|---|
| Nombre d'avis récents de la fiche | 10 à 25 avis récents | ×1.07 | ×1.09 | non-effet des deux côtés — stable |
| Nombre d'avis récents de la fiche | 60 à 150 | ×0.79 | ×0.64 | tient |
| Nombre d'avis récents de la fiche | plus de 150 | ×0.78 | ×0.50 | à surveiller — amplitude bouge de plus de moitié |
| Nombre total d'avis de la fiche | 100 à 250 | ×0.90 | ×1.77 | NE TIENT PAS — change de sens |
| Nombre total d'avis de la fiche | moins de 100 | ×4.88 | ×7.65 | à surveiller — amplitude bouge de plus de moitié |
| Nombre total d'avis de la fiche | plus de 1 000 | ×0.48 | ×0.87 | à surveiller — amplitude bouge de plus de moitié |
| Note moyenne de la fiche | 4,0 à 4,5 | ×0.97 | ×0.64 | à surveiller — amplitude bouge de plus de moitié |
| Note moyenne de la fiche | 4,8 et plus | ×1.59 | ×1.43 | tient |
| Note moyenne de la fiche | moins de 4,0 | ×1.88 | ×0.66 | NE TIENT PAS — change de sens |
| Région | États-Unis | ×1.27 | ×1.51 | tient |
| Secteur | automotive | ×0.79 | ×1.38 | NE TIENT PAS — change de sens |
| Secteur | healthcare | ×2.34 | ×2.14 | tient |
| Secteur | home_services | ×2.79 | ×2.62 | tient |
| Secteur | hospitality | ×0.98 | ×1.40 | NE TIENT PAS — change de sens |
| Secteur | travel | ×1.79 | ×1.75 | tient |
| Secteur | wellness_fitness | ×4.07 | ×1.82 | fragile — amplitude divisée ou multipliée par plus de 2 |
| Taille du groupe | groupe de 20 à 50 sites | ×1.25 | ×0.94 | NE TIENT PAS — change de sens |
| Taille du groupe | groupe de 4 à 10 sites | ×0.79 | ×0.85 | tient |
| Vitesse de collecte — part du stock reçue en 30 jours | 10 % et plus | ×2.00 | ×0.74 | NE TIENT PAS — change de sens |
| Vitesse de collecte — part du stock reçue en 30 jours | 3 à 10 % | ×0.76 | ×0.88 | tient |
| Vitesse de collecte — part du stock reçue en 30 jours | moins de 1 % | ×1.41 | ×1.28 | tient |

##### Être touché

| Facteur | Modalité | Avec | Sans | Verdict |
|---|---|---:|---:|---|
| Nombre d'avis récents de la fiche | 10 à 25 avis récents | ×0.35 | ×0.35 | tient |
| Nombre d'avis récents de la fiche | 60 à 150 | ×2.43 | ×2.37 | tient |
| Nombre d'avis récents de la fiche | plus de 150 | ×5.87 | ×5.56 | tient |
| Nombre total d'avis de la fiche | 100 à 250 | ×1.55 | ×1.59 | tient |
| Nombre total d'avis de la fiche | moins de 100 | ×1.45 | ×1.57 | tient |
| Nombre total d'avis de la fiche | plus de 1 000 | ×0.97 | ×0.98 | non-effet des deux côtés — stable |
| Note moyenne de la fiche | 4,0 à 4,5 | ×0.92 | ×0.91 | non-effet des deux côtés — stable |
| Note moyenne de la fiche | 4,8 et plus | ×0.92 | ×0.93 | non-effet des deux côtés — stable |
| Note moyenne de la fiche | moins de 4,0 | ×1.38 | ×1.31 | tient |
| Région | États-Unis | ×1.40 | ×1.39 | tient |
| Secteur | automotive | ×1.52 | ×1.50 | tient |
| Secteur | healthcare | ×1.24 | ×1.20 | tient |
| Secteur | home_services | ×3.94 | ×3.89 | tient |
| Secteur | hospitality | ×1.16 | ×1.17 | tient |
| Secteur | travel | ×1.30 | ×1.29 | tient |
| Secteur | wellness_fitness | ×1.68 | ×1.60 | tient |
| Taille du groupe | groupe de 20 à 50 sites | ×1.27 | ×1.26 | tient |
| Taille du groupe | groupe de 4 à 10 sites | ×1.59 | ×1.60 | tient |
| Vitesse de collecte — part du stock reçue en 30 jours | 10 % et plus | ×0.55 | ×0.47 | tient |
| Vitesse de collecte — part du stock reçue en 30 jours | 3 à 10 % | ×0.81 | ×0.81 | tient |
| Vitesse de collecte — part du stock reçue en 30 jours | moins de 1 % | ×1.39 | ×1.38 | tient |

##### Analyse B — quel avis tombe

| Facteur | Modalité | Avec | Sans | Verdict |
|---|---|---:|---:|---|
| Auteur ayant publié plusieurs avis le même jour | rafale le même jour | ×5.30 | ×5.33 | tient |
| Auteur présent sur plusieurs fiches du panel | plusieurs fiches | ×1.23 | ×1.23 | tient |
| Avis modifié depuis publication | modifié depuis publication | ×1.94 | ×1.99 | tient |
| Langue de l'avis | autre langue | ×1.11 | ×1.05 | tient |
| Niveau Local Guide de l'auteur | aucun niveau | ×1.55 | ×1.50 | tient |
| Niveau Local Guide de l'auteur | niveau 4 ou 5 | ×1.18 | ×1.20 | tient |
| Niveau Local Guide de l'auteur | niveau 6 et plus | ×0.70 | ×0.71 | tient |
| Nombre d'avis publiés par l'auteur | 1 ou 2 avis | ×1.01 | ×1.00 | non-effet des deux côtés — stable |
| Nombre d'avis publiés par l'auteur | 21 à 100 avis | ×0.72 | ×0.70 | tient |
| Nombre d'avis publiés par l'auteur | compteur à 0 | ×1.29 | ×1.34 | tient |
| Nombre d'avis publiés par l'auteur | plus de 100 avis | ×0.75 | ×0.73 | tient |
| Note de l'avis | 1 étoile | ×3.57 | ×3.20 | tient |
| Note de l'avis | 2 étoiles | ×2.24 | ×2.60 | tient |
| Note de l'avis | 3 étoiles | ×0.94 | ×0.91 | non-effet des deux côtés — stable |
| Note de l'avis | 5 étoiles | ×1.24 | ×1.26 | tient |
| Photos jointes | deux photos ou plus | ×0.70 | ×0.70 | tient |
| Photos jointes | une photo | ×0.79 | ×0.81 | tient |
| Réponse du propriétaire | avec réponse du propriétaire | ×0.30 | ×0.33 | tient |
| Texte de l'avis | 1 à 50 caractères | ×1.12 | ×1.13 | tient |
| Texte de l'avis | 151 à 400 caractères | ×1.13 | ×1.12 | tient |
| Texte de l'avis | note seule, sans texte | ×1.00 | ×0.96 | non-effet des deux côtés — stable |
| Texte de l'avis | plus de 400 caractères | ×1.01 | ×0.98 | non-effet des deux côtés — stable |
| Âge de l'avis au moment du passage | 0 à 6 jours | ×0.44 | ×0.44 | tient |
| Âge de l'avis au moment du passage | 14 à 20 jours | ×0.31 | ×0.31 | tient |
| Âge de l'avis au moment du passage | 21 à 29 jours | ×0.16 | ×0.15 | tient |
| Âge de l'avis au moment du passage | 30 jours et plus | ×0.19 | ×0.19 | tient |

<!-- /genere:controle -->
