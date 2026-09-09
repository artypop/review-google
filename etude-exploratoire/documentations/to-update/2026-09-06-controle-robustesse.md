---
date: 2026-09-06
projet: reviewflowz-analyse-google
titre: "Contrôle de robustesse — sans les 24 fiches massivement purgées"
statut: résultats
---

# Contrôle de robustesse — sans les 24 fiches massivement purgées

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

Produit par `scripts/controle_robustesse.py`.

## Pourquoi ce contrôle est obligatoire

24 établissements portent 958 suppressions, 18 % du total. Deux d'entre eux, des salles de
sport espagnoles, en portent 399 à eux seuls. Un modèle ajusté sur l'ensemble peut très bien
décrire ces 24 fiches plutôt que la modération de Google.

La liste des 24 fiches est dans `data/resultats/fiches_massivement_purgees.csv`. Le seuil est
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

| | Avec les 24 fiches | Sans |
|---|---:|---:|
| Analyse A — établissements | 2 529 | 2 506 |
| Analyse B — établissements | 584 | 568 |
| Analyse B — observations | 64 442 | 59 519 |
| Analyse B — disparitions | 2 828 | 2 177 |

### Verdict d'ensemble sur 68 effets testés

- **45 tiennent** ;
- 13 sont des **non-effets stables** — voisins de 1 dans les deux versions, ils ne mesurent rien, ni avant ni après ;
- 3 sont **fragiles** ;
- 7 **ne tiennent pas** ou ne sont pas exploitables.

#### Ce qui ne tient pas, ou n'est pas exploitable

| Analyse | Facteur | Modalité | Avec | Sans | Verdict |
|---|---|---|---:|---:|---|
| A | Nombre total d'avis de la fiche | 100 à 250 | ×1.00 | ×1.14 | NE TIENT PAS — change de sens |
| A | Note moyenne de la fiche | moins de 4,0 | ×1.84 | ×0.73 | NE TIENT PAS — change de sens |
| A | Secteur | automotive | ×0.86 | ×1.48 | NE TIENT PAS — change de sens |
| A | Secteur | hospitality | ×0.95 | ×1.24 | NE TIENT PAS — change de sens |
| A | Taille du groupe | groupe de 20 à 50 sites | ×1.26 | ×0.94 | NE TIENT PAS — change de sens |
| A | Vitesse de collecte — part du stock reçue en 30 jours | 10 % et plus | ×2.09 | ×0.62 | NE TIENT PAS — change de sens |
| A | Nombre total d'avis de la fiche | moins de 100 | ×0.70 | ×0.00 | NON EXPLOITABLE — estimation dégénérée, pas un effet |

#### Ce qui est fragile

| Analyse | Facteur | Modalité | Avec | Sans | Verdict |
|---|---|---|---:|---:|---|
| A | Nombre d'avis récents de la fiche | plus de 150 | ×0.87 | ×0.48 | à surveiller — amplitude bouge de plus de moitié |
| A | Nombre total d'avis de la fiche | plus de 1 000 | ×0.45 | ×0.86 | à surveiller — amplitude bouge de plus de moitié |
| A | Secteur | wellness_fitness | ×3.58 | ×1.30 | fragile — amplitude divisée ou multipliée par plus de 2 |

#### Tous les effets, côte à côte

##### Ampleur de la purge

| Facteur | Modalité | Avec | Sans | Verdict |
|---|---|---:|---:|---|
| Nombre d'avis récents de la fiche | 10 à 25 avis récents | ×1.00 | ×0.98 | non-effet des deux côtés — stable |
| Nombre d'avis récents de la fiche | 60 à 150 | ×0.85 | ×0.68 | tient |
| Nombre d'avis récents de la fiche | plus de 150 | ×0.87 | ×0.48 | à surveiller — amplitude bouge de plus de moitié |
| Nombre total d'avis de la fiche | 100 à 250 | ×1.00 | ×1.14 | NE TIENT PAS — change de sens |
| Nombre total d'avis de la fiche | moins de 100 | ×6.49 | ×nan | non calculable |
| Nombre total d'avis de la fiche | plus de 1 000 | ×0.45 | ×0.86 | à surveiller — amplitude bouge de plus de moitié |
| Note moyenne de la fiche | 4,0 à 4,5 | ×1.00 | ×0.71 | tient |
| Note moyenne de la fiche | 4,8 et plus | ×1.41 | ×1.34 | tient |
| Note moyenne de la fiche | moins de 4,0 | ×1.84 | ×0.73 | NE TIENT PAS — change de sens |
| Région | États-Unis | ×1.14 | ×1.29 | tient |
| Secteur | automotive | ×0.86 | ×1.48 | NE TIENT PAS — change de sens |
| Secteur | healthcare | ×2.42 | ×2.14 | tient |
| Secteur | home_services | ×2.97 | ×2.47 | tient |
| Secteur | hospitality | ×0.95 | ×1.24 | NE TIENT PAS — change de sens |
| Secteur | travel | ×1.78 | ×1.67 | tient |
| Secteur | wellness_fitness | ×3.58 | ×1.30 | fragile — amplitude divisée ou multipliée par plus de 2 |
| Taille du groupe | groupe de 20 à 50 sites | ×1.26 | ×0.94 | NE TIENT PAS — change de sens |
| Taille du groupe | groupe de 4 à 10 sites | ×0.88 | ×1.00 | tient |
| Vitesse de collecte — part du stock reçue en 30 jours | 10 % et plus | ×2.09 | ×0.62 | NE TIENT PAS — change de sens |
| Vitesse de collecte — part du stock reçue en 30 jours | 3 à 10 % | ×0.77 | ×0.77 | tient |
| Vitesse de collecte — part du stock reçue en 30 jours | moins de 1 % | ×1.62 | ×1.44 | tient |

##### Être touché

| Facteur | Modalité | Avec | Sans | Verdict |
|---|---|---:|---:|---|
| Nombre d'avis récents de la fiche | 10 à 25 avis récents | ×0.38 | ×0.38 | tient |
| Nombre d'avis récents de la fiche | 60 à 150 | ×2.23 | ×2.19 | tient |
| Nombre d'avis récents de la fiche | plus de 150 | ×6.29 | ×6.15 | tient |
| Nombre total d'avis de la fiche | 100 à 250 | ×1.47 | ×1.27 | tient |
| Nombre total d'avis de la fiche | moins de 100 | ×0.70 | ×0.00 | NON EXPLOITABLE — estimation dégénérée, pas un effet |
| Nombre total d'avis de la fiche | plus de 1 000 | ×0.98 | ×1.00 | non-effet des deux côtés — stable |
| Note moyenne de la fiche | 4,0 à 4,5 | ×0.97 | ×0.96 | non-effet des deux côtés — stable |
| Note moyenne de la fiche | 4,8 et plus | ×1.07 | ×1.05 | non-effet des deux côtés — stable |
| Note moyenne de la fiche | moins de 4,0 | ×1.38 | ×1.37 | tient |
| Région | États-Unis | ×1.44 | ×1.41 | tient |
| Secteur | automotive | ×1.16 | ×1.18 | tient |
| Secteur | healthcare | ×1.04 | ×1.07 | non-effet des deux côtés — stable |
| Secteur | home_services | ×3.04 | ×2.88 | tient |
| Secteur | hospitality | ×0.98 | ×0.97 | non-effet des deux côtés — stable |
| Secteur | travel | ×0.94 | ×0.97 | non-effet des deux côtés — stable |
| Secteur | wellness_fitness | ×1.53 | ×1.40 | tient |
| Taille du groupe | groupe de 20 à 50 sites | ×1.18 | ×1.22 | tient |
| Taille du groupe | groupe de 4 à 10 sites | ×1.37 | ×1.43 | tient |
| Vitesse de collecte — part du stock reçue en 30 jours | 10 % et plus | ×0.50 | ×0.40 | tient |
| Vitesse de collecte — part du stock reçue en 30 jours | 3 à 10 % | ×0.73 | ×0.72 | tient |
| Vitesse de collecte — part du stock reçue en 30 jours | moins de 1 % | ×1.17 | ×1.17 | tient |

##### Analyse B — quel avis tombe

| Facteur | Modalité | Avec | Sans | Verdict |
|---|---|---:|---:|---|
| Auteur ayant publié plusieurs avis le même jour | rafale le même jour | ×18.83 | ×18.25 | tient |
| Auteur présent sur plusieurs fiches du panel | plusieurs fiches | ×0.96 | ×1.01 | non-effet des deux côtés — stable |
| Avis modifié depuis publication | modifié depuis publication | ×1.92 | ×2.02 | tient |
| Langue de l'avis | autre langue | ×1.11 | ×1.08 | non-effet des deux côtés — stable |
| Niveau Local Guide de l'auteur | aucun niveau | ×1.59 | ×1.58 | tient |
| Niveau Local Guide de l'auteur | niveau 4 ou 5 | ×1.16 | ×1.16 | tient |
| Niveau Local Guide de l'auteur | niveau 6 et plus | ×0.73 | ×0.75 | tient |
| Nombre d'avis publiés par l'auteur | 1 ou 2 avis | ×1.01 | ×0.97 | non-effet des deux côtés — stable |
| Nombre d'avis publiés par l'auteur | 21 à 100 avis | ×0.74 | ×0.72 | tient |
| Nombre d'avis publiés par l'auteur | compteur à 0 | ×1.21 | ×1.24 | tient |
| Nombre d'avis publiés par l'auteur | plus de 100 avis | ×0.82 | ×0.83 | tient |
| Note de l'avis | 1 étoile | ×3.20 | ×3.47 | tient |
| Note de l'avis | 2 étoiles | ×2.08 | ×2.59 | tient |
| Note de l'avis | 3 étoiles | ×0.79 | ×0.96 | tient |
| Note de l'avis | 5 étoiles | ×1.19 | ×1.25 | tient |
| Photos jointes | deux photos ou plus | ×0.79 | ×0.83 | tient |
| Photos jointes | une photo | ×0.77 | ×0.75 | tient |
| Réponse du propriétaire | avec réponse du propriétaire | ×0.31 | ×0.33 | tient |
| Texte de l'avis | 1 à 50 caractères | ×1.10 | ×1.09 | non-effet des deux côtés — stable |
| Texte de l'avis | 151 à 400 caractères | ×1.15 | ×1.17 | tient |
| Texte de l'avis | note seule, sans texte | ×0.97 | ×0.95 | non-effet des deux côtés — stable |
| Texte de l'avis | plus de 400 caractères | ×0.98 | ×0.99 | non-effet des deux côtés — stable |
| Âge de l'avis au moment du passage | 0 à 6 jours | ×0.48 | ×0.55 | tient |
| Âge de l'avis au moment du passage | 14 à 20 jours | ×0.32 | ×0.32 | tient |
| Âge de l'avis au moment du passage | 21 à 29 jours | ×0.15 | ×0.15 | tient |
| Âge de l'avis au moment du passage | 30 jours et plus | ×0.20 | ×0.20 | tient |

<!-- /genere:controle -->
