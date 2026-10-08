# 10. Les fiches très touchées : vérification des tableaux d'Axel

| Commande | CSV |
|---|---|
| `uv run python consolidation/10_fiches_attaquees.py` | `10_croisement.csv`, `10_tab3_taux.csv`, `10_tab4_jours.csv`, `10_tab5_age.csv`, `10_tab5_resume.csv` |

Chiffres du 2026-10-08. Mail d'Axel du 2026-10-07 : il classe les fiches selon leurs suppressions
en 14 jours, aucune, 1 à 10, 11 et plus (« flagged »).

Deux bases :
- **base d'Axel :** la table brute `reviews`, sans les avis modifiés (lignes `is_update`). Toute
  disparition compte, ratés d'un jour et bugs d'enregistrement compris : 5 230 disparitions.
- **base nettoyée :** `reviews_doublons_cleaned_all`, la base complète de la consolidation, avis
  modifiés compris : 4 590 suppressions. Décision de Romain du 2026-10-08 : on garde notre
  nettoyage, même si des fiches divergent de celles d'Axel.

---

## Ses chiffres sont retrouvés exactement

| Tableau | Base d'Axel, refaite ici | Ses chiffres |
|---|---|---|
| 1 : fiches 1 à 10 / 11 et plus | 1 288 / 111 fiches, 2 216 / 3 014 suppressions | identiques |
| 3 : part supprimée, 11 et plus | 1,25 % de tous les avis, 22,6 % des récents, 18,2 % des publiés pendant le suivi | identiques |
| 3 : part supprimée, 1 à 10 | 0,13 %, 2,0 %, 3,1 % | identiques |
| 4 : jours avec suppression, 11 et plus / 3 à 10 | 6,2 / 3,1 jours ; jour le plus chargé 42 % / 44 % ; 10 / 24 fiches à 80 % en un jour | identiques |
| 5 : âge à la suppression | médiane 18 / 199 jours ; 7 jours ou moins 21 % / 23 % ; 30 jours ou moins 60 % / 37 % ; plus d'un an 24 % / 45 % | 18 / 200 jours, mêmes parts |

- « Récents » chez Axel : avis publiés depuis le 12 juillet, soit 30 jours avant le premier passage du
  robot, avis publiés pendant le suivi compris.
- Ses 8 995 fiches sont nos 8 997 moins les 2 fiches retirées de Google.
- Seule différence : la part du stock dans les tranches de moins de 8 jours (tableau 5). Il date
  l'âge du stock d'un autre jour que le 11 août. Les tranches au-delà de 30 jours concordent.

## Fiche par fiche : sa catégorie et la nôtre (`10_croisement.csv`)

| Catégorie Axel | Catégorie nettoyée | Fiches | Suppressions Axel | Suppressions nettoyées |
|---|---|---:|---:|---:|
| 11 et plus | 11 et plus | 96 | 2 756 | 2 657 |
| 11 et plus | 1 à 10 | 8 | 96 | 64 |
| 11 et plus | aucune | 7 | 162 | 0 |
| 1 à 10 | 11 et plus | 1 | 10 | 12 |
| 1 à 10 | 1 à 10 | 1 123 | 1 971 | 1 849 |
| 1 à 10 | aucune | 164 | 235 | 0 |
| aucune | 1 à 10 | 8 | 0 | 8 |
| aucune | aucune | 7 590 | 0 | 0 |

- 96 de nos 97 fiches « 11 et plus » sont dans les 111 d'Axel. La 97e est Bulwark Exterminating
  (cid `17461188179245106693`) : 10 suppressions chez Axel, 12 chez nous, dont 2 avis modifiés
  qu'il exclut.
- 8 fiches sans suppression chez Axel en ont une chez nous : un avis modifié chacune.
- Les 7 fiches « 11 et plus » chez Axel et sans suppression chez nous sont de petites fiches
  européennes : 28 à 75 lignes dans la table brute, 5 ou 6 avis une fois les doublons retirés. Leurs
  11 à 35 « suppressions » sont des doublons d'enregistrement.

## Les mêmes tableaux sur la base nettoyée

| | 11 et plus | 1 à 10 |
|---|---:|---:|
| Fiches | 97 | 1 139 |
| Suppressions | 2 669 | 1 921 |
| Part de tous les avis supprimée | 1,16 % | 0,13 % |
| Part des avis récents supprimée | 21,3 % | 2,1 % |
| Part des avis publiés pendant le suivi supprimée | 17,7 % | 3,3 % |
| Âge médian à la suppression | 18 jours | 126 jours |
| Supprimés à 7 jours ou moins | 21 % | 23 % |
| Supprimés à 30 jours ou moins | 61 % | 40 % |
| Supprimés à plus d'un an | 22 % | 41 % |

Tableau 4 (fiches 11 et plus / 3 à 10, soit 97 / 143 fiches) : 6,4 / 3,3 jours avec suppression ;
jour le plus chargé 42 % / 44 % ; 5 / 19 fiches à 80 % en un jour.

Toutes les fiches sans les 11 et plus : 8 900 fiches, 0,041 % des avis supprimés, 0,79 % des
récents, 1,28 % des publiés pendant le suivi.

## Ce qui change d'une base à l'autre

- Les conclusions d'Axel tiennent : les fiches à 11 suppressions et plus perdent surtout des avis
  récents (âge médian 18 jours), sur 6 jours en moyenne ; les autres perdent surtout des avis
  anciens, sur 3 jours.
- Ses 111 fiches comptent 7 fiches dont les suppressions sont des doublons, et 8 qui passent sous
  le seuil une fois le nettoyage fait. Une fiche le franchit chez nous. On a 97 fiches.

## Réserves

- Les catégories sont définies par le nombre de suppressions : les 11 et plus sont plus touchées
  par construction. Le tableau 3 ne prouve rien sur leur risque. Les tableaux 4 et 5 décrivent la
  forme des suppressions, et ceux-là apportent une information.
- Le seuil de 11 est absolu : il classe plus facilement une fiche de plusieurs milliers d'avis.
- Un avis supprimé avant le 11 août n'est pas dans la base : les suppressions d'avis très récents
  sont sous-comptées dans les deux bases.
