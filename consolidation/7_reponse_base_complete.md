# 7. La réponse du propriétaire sur toute la base

| Commande | CSV |
|---|---|
| `uv run python consolidation/7_reponse_base_complete.py` (environ 10 secondes) | `7_reponse_base_complete.csv`, `7_controle.csv` |

Chiffres du 2026-09-30. Base : `reviews_doublons_cleaned_all`, les avis publiés avant le 11 août 2026,
donc déjà en ligne au premier passage du robot. Suppressions constatées du 12 au 24 août.

## Le calcul

- Un avis est « répondu » si la réponse du propriétaire date d'avant le 11 août. Une réponse
  arrivée pendant le suivi ne compte pas.
- Chaque avis est rangé dans une case : son âge le 11 août, l'habitude de réponse de sa fiche, sa
  région, la taille de l'entreprise.
- Dans chaque case, on compte les avis et ceux qui disparaissent, pour les répondus et pour les
  autres. Le rapport des deux taux se lit « ×0,5 : l'avis répondu disparaît deux fois moins ».
- C'est un calcul direct, sans modèle. La note, le secteur et le profil de l'auteur ne sont pas
  tenus égaux.
- Règle de citation (`commun.py`, seuils du 2026-09-30) : au moins 10 suppressions, sur au moins
  5 fiches, sans qu'une fiche en porte plus du quart, pour les avis répondus et pour les avis sans
  réponse.

## La population (`7_controle.csv`)

| | Avis | Suppressions |
|---|---:|---:|
| Base complète | 4 876 933 | 4 590 |
| Publiés avant le 11 août : la population de ce point | 4 843 936 | 3 744 |
| — répondus avant le 11 août | 2 063 752 | 1 842 |
| — sans réponse au 11 août | 2 780 184 | 1 902 |
| Publiés à partir du 11 août : couverts par le point 5 | 32 997 | 846 |

---

## Résultats

Suppressions pour 10 000 avis, États-Unis et Europe réunis, toutes tailles, sans les 95 fiches
signalées. Source : `7_reponse_base_complete.csv`, lignes `sans_enseignes`, `ensemble`, `toutes`.

### Tous âges réunis, l'avis répondu disparaît un peu plus : ×1,33

- 6,2 pour 10 000 avis répondus, 4,7 pour 10 000 avis sans réponse.
- Ce chiffre mélange les âges. Parmi les avis de 8 à 30 jours, 29 628 sont répondus et 23 670 ne
  le sont pas. Parmi les avis de plus d'un an, 1 533 868 sont répondus et 2 380 286 ne le sont pas.
  Les avis répondus sont plus souvent récents, et un avis récent disparaît environ 30 fois plus
  qu'un avis de plus d'un an (chez les répondus, 93,8 pour 10 000 contre 3,1).

### Fiches qui répondent à plus de 75 % de leurs avis

| Âge le 11 août | Répondus : avis, suppressions, pour 10 000 | Sans réponse : avis, suppressions, pour 10 000 | Rapport | Citable |
|---|---:|---:|---:|---|
| 1 à 7 jours | 6 112 — 100 — 163,6 | 2 508 — 93 — 370,8 | ×0,44 | oui |
| 8 à 30 jours | 25 322 — 249 — 98,3 | 2 090 — 40 — 191,4 | ×0,51 | oui |
| 31 à 90 jours | 64 641 — 122 — 18,9 | 2 855 — 18 — 63,0 | ×0,30 | non |
| 91 à 365 jours | 253 655 — 132 — 5,2 | 7 546 — 19 — 25,2 | ×0,21 | oui |
| plus d'un an | 1 072 517 — 310 — 2,9 | 578 524 — 120 — 2,1 | ×1,39 | oui |

- Pendant le premier mois, l'avis répondu disparaît 2 fois moins.
- De 91 jours à un an, il disparaît 5 fois moins (×0,21). La case de référence compte
  19 suppressions d'avis sans réponse, sur 17 fiches.
- De 31 à 90 jours, ×0,30, non citable : une fiche porte 33 % des 18 suppressions d'avis sans
  réponse.
- Au-delà d'un an, aucune protection : 2,9 contre 2,1 pour 10 000.
- Sur ces fiches, l'avis de moins d'un an resté sans réponse est rare : 14 999 avis, contre
  349 730 répondus (somme des quatre premières lignes).

### Fiches qui répondent à 75 % ou moins

| Âge le 11 août | Répondus : avis, suppressions, pour 10 000 | Sans réponse : avis, suppressions, pour 10 000 | Rapport | Citable |
|---|---:|---:|---:|---|
| 1 à 7 jours | 863 — 26 — 301,3 | 6 912 — 181 — 261,9 | ×1,15 | non |
| 8 à 30 jours | 4 115 — 29 — 70,5 | 21 002 — 159 — 75,7 | ×0,93 | oui |
| 31 à 90 jours | 11 170 — 50 — 44,8 | 46 366 — 111 — 23,9 | ×1,87 | non |
| 91 à 365 jours | 50 105 — 39 — 7,8 | 167 766 — 108 — 6,4 | ×1,21 | oui |
| plus d'un an | 409 299 — 138 — 3,4 | 1 647 348 — 353 — 2,1 | ×1,57 | oui |

- Aucune protection visible. Les trois cases citables donnent ×0,93, ×1,21 et ×1,57.
- Les cases à 1 à 7 jours et à 31 à 90 jours ne sont pas citables : une seule fiche porte la moitié
  des suppressions d'avis répondus (50 % et 52 %).

### Par région et par taille, fiches qui répondent à plus de 75 %

Entre parenthèses : suppressions d'avis répondus / d'avis sans réponse. Les cases sans mention
sont citables.

| | 1 à 7 jours | 8 à 30 jours | 31 à 90 jours | 91 à 365 jours |
|---|---:|---:|---:|---:|
| États-Unis | ×0,45 (81 / 59) | ×0,61 (207 / 25) | ×0,45 (106 / 11) | ×0,23 (97 / 12) |
| Europe | ×0,31 (19 / 34), non citable | ×0,27 (42 / 15) | ×0,09 (16 / 7), non citable | ×0,16 (35 / 7), non citable |
| Mono + small | ×0,55 (55 / 55) | ×0,81 (143 / 19) | ×0,34 (91 / 13), non citable | ×0,21 (73 / 13) |
| Large | ×0,36 (45 / 38) | ×0,29 (106 / 21) | ×0,25 (31 / 5), non citable | ×0,23 (59 / 6), non citable |

- Aux États-Unis, l'avis répondu disparaît 1,6 à 4 fois moins à tous les âges jusqu'à un an.
- En Europe, une seule case est citable : 8 à 30 jours, ×0,27.

### Avec les enseignes signalées

- Fiches qui répondent à plus de 75 %, toutes fiches : ×0,91 à 1 à 7 jours, ×0,68 à 8 à 30 jours.
- Les 4 chaînes répondent à presque tous leurs avis et en perdent beaucoup. Le point 5 donnait le
  même constat : ×0,84 sur les `large` avec les chaînes.

### Un cas déroulé

Avis de 8 à 30 jours, fiches qui répondent à plus de 75 %, sans enseignes :
- 25 322 avis répondus, 249 disparus : 98,3 pour 10 000 ;
- 2 090 avis sans réponse, 40 disparus : 191,4 pour 10 000 ;
- 98,3 / 191,4 = ×0,51.

---

## Ce que ce point ajoute au point 5

| | Point 5 | Point 7 |
|---|---|---|
| Avis | 35 095, publiés du 4 au 17 août | 4 843 936, publiés avant le 11 août |
| Suppressions | 1 349 | 3 744 |
| Réponse | datée jour par jour | état au 11 août |
| À caractéristiques égales | âge, note, région | âge et habitude seulement |
| Fiches à plus de 75 %, premiers jours | ×0,36 et ×0,33 (mono + small) ; ×0,24 et ×0,23 (large sans enseignes) | ×0,55 (mono + small) ; ×0,36 (large sans enseignes) |

- Les deux calculs vont dans le même sens sur les fiches qui répondent à plus de 75 %.
- Le point 7 ajoute : l'écart se voit encore de 8 à 30 jours (×0,51) et de 91 jours à un an
  (×0,21) ; la case de 31 à 90 jours n'est pas citable ; l'écart n'existe plus au-delà d'un an.
- Sur les fiches qui répondent à 75 % ou moins, aucun des deux calculs ne montre de protection.

## Rapprochement avec les comptages faits dans la console (`7_controle.csv`)

- Avis avec une réponse au dernier passage du robot : 2 082 232, dont 2 319 supprimés.
- Parmi eux, publiés après le 1er août : 26 033, dont 786 supprimés.
- Le point 7 retient 1 842 de ces 2 319 suppressions. Les autres : 155 sur des avis publiés avant
  le 11 août et répondus le 11 août ou après, comptés ici « sans réponse » ; 322 sur des avis
  publiés à partir du 11 août (2 319 − 1 842 − 155).

---

## Réserves

- **Un taux direct compte tout ce qui accompagne la réponse** : la note, le secteur, le profil de
  l'auteur. Aucune marge d'incertitude n'est calculée ; la règle de citation est le seul garde-fou.
  Le point 8 (`8_regression_reponse_base.md`) refait le calcul en tenant ces caractéristiques
  égales : ×0,51 devient ×0,66 [0,40 à 1,08] de 8 à 30 jours, ×0,21 devient ×0,25 [0,14 à 0,44]
  de 91 jours à un an.
- **Un avis ancien présent le 11 août a survécu jusque-là.** Les résultats se lisent « parmi les
  avis encore en ligne le 11 août ».
- **L'habitude de réponse est mesurée sur les avis d'août 2025 à août 2026.** Pour un avis de plus
  d'un an, elle décrit la fiche d'aujourd'hui. Sur les fiches qui répondent à plus de 75 %,
  578 524 avis de plus d'un an n'ont pas de réponse.
- Un avis publié du 11 août 2025 au 3 août 2026 entre dans l'habitude de sa propre fiche.
- **Réponse arrivée pendant le suivi** : 4 669 avis publiés avant le 11 août ont reçu leur réponse
  le 11 août ou après, dont 155 supprimés. Ils comptent « sans réponse ». Pour les avis de 1 à
  7 jours, le point 5 fait référence.
- Le sens de la cause reste ouvert : le propriétaire peut s'abstenir de répondre aux avis qu'il
  signale. Une réponse retirée est invisible.
- **La tranche « plus d'un an » contient les avis modifiés plus d'un an après leur publication**
  (`1_corpus.md`, réserves). Leur âge se compte depuis la publication : un avis de 2023 réécrit
  en juillet 2026 y est rangé avec les avis anciens restés intacts.
