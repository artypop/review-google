# 8. La réponse du propriétaire sur toute la base, à caractéristiques égales

| Commande | CSV |
|---|---|
| `nice -n 19 uv run python consolidation/8_regression_reponse_base.py` (environ 35 secondes, 2,8 Go de mémoire) | `8_effectifs.csv`, `8_effets.csv`, `8_fiches_par_case.csv`, `8_notes_par_case.csv` |

Chiffres du 2026-09-30. Base : `reviews_doublons_cleaned`, les avis publiés avant le 4 août 2026
sur les fiches dont l'habitude de réponse est connue. Suppressions constatées du 12 au 24 août.

## Le calcul

- **Population** : 4 488 470 avis, 6 905 fiches, 2 476 suppressions. Sans les 95 fiches
  signalées : 4 260 324 avis, 6 815 fiches, 1 765 suppressions (`8_effectifs.csv`, lignes « total
  du passage »).
- Le panel 03B (avis du 4 au 17 août) laisse ces avis de côté : ce point et le point 5 ne
  partagent aucun avis.
- Ce sont les avis du point 7, à partir de 8 jours d'âge et sur les fiches d'habitude connue. Les
  effectifs par case sont les mêmes qu'au point 7.
- Un avis est « répondu » si la réponse du propriétaire date d'avant le 11 août.
- Chaque effet compare l'avis répondu à l'avis sans réponse du même âge, sur des fiches de même
  habitude, toutes ces colonnes égales : note, niveau Local Guide, photos et avis de l'auteur,
  photo jointe, longueur du texte, secteur, taille, région.
- « ×0,50 » : l'avis répondu disparaît deux fois moins. La fourchette tient compte de ce que les
  avis d'une même fiche se ressemblent.
- Règle de citation (`commun.py`, seuils du 2026-09-30) : au moins 10 suppressions, sur au moins
  5 fiches, sans qu'une fiche en porte plus du quart, pour les avis répondus et pour les avis sans
  réponse. 30 effets de réponse sur 48 sont citables (`8_effets.csv`).
- La colonne `rapport_direct` de `8_effets.csv` redonne le rapport des deux taux du point 7.

---

## Résultats

États-Unis et Europe réunis, sans les 95 fiches signalées (`8_effets.csv`, passage « ensemble,
sans_enseignes »).

### Fiches qui répondent à plus de 75 % de leurs avis

| Âge le 11 août | Répondus : avis, suppressions | Sans réponse : avis, suppressions | Rapport direct (point 7) | À caractéristiques égales | Citable |
|---|---:|---:|---:|---:|---|
| 8 à 30 jours | 25 322 — 249 | 2 090 — 40 | ×0,51 | ×0,70 [0,43 à 1,15] | oui |
| 31 à 90 jours | 64 641 — 122 | 2 855 — 18 | ×0,30 | ×0,40 [0,17 à 0,96] | non |
| 91 à 365 jours | 253 645 — 131 | 7 546 — 19 | ×0,21 | ×0,26 [0,15 à 0,47] | oui |
| plus d'un an | 1 034 272 — 225 | 567 483 — 104 | ×1,19 | ×1,00 [0,76 à 1,31] | oui |

- **De 91 jours à un an, l'avis répondu disparaît 4 fois moins** (×0,26), à caractéristiques
  égales. Le rapport direct donnait ×0,21.
- **De 8 à 30 jours, ×0,70, et la fourchette contient 1** : les données ne tranchent pas. Le
  rapport direct donnait ×0,51.
- De 31 à 90 jours, ×0,40, non citable : TKE veterinary clinic Elversberg (cid
  `13197914448513377771`) porte 6 des 18 suppressions d'avis sans réponse, toutes le 19 août
  (`8_fiches_par_case.csv`).
- Au-delà d'un an, aucun écart : ×1,00.

### Un cas déroulé : pourquoi ×0,51 devient ×0,70

Avis de 8 à 30 jours, fiches qui répondent à plus de 75 % (`8_notes_par_case.csv`) :
- parmi les 25 322 avis répondus, 4,6 % portent 1 étoile ;
- parmi les 2 090 avis sans réponse, 15,9 % portent 1 étoile ;
- dans ce calcul, un avis 1 étoile disparaît 3,2 fois plus qu'un 5 étoiles
  (×3,22 [2,16 à 4,80], `8_effets.csv`).

Le rapport direct ×0,51 comptait donc en partie la note. À note égale :
- avis 5 étoiles : 210 disparus sur 21 210 répondus (99 pour 10 000), 19 sur 1 391 sans réponse
  (137 pour 10 000), soit ×0,72 ;
- avis 1 étoile : 28 disparus sur 1 156 répondus (242 pour 10 000), 16 sur 333 sans réponse
  (480 pour 10 000), soit ×0,50.

Même lecture de 91 jours à un an, avis 5 étoiles : 114 disparus sur 217 616 répondus (5,2 pour
10 000), 9 sur 4 525 sans réponse (19,9 pour 10 000), soit ×0,26.

### Fiches qui répondent à 75 % ou moins

| Âge le 11 août | Répondus : avis, suppressions | Sans réponse : avis, suppressions | Rapport direct (point 7) | À caractéristiques égales | Citable |
|---|---:|---:|---:|---:|---|
| 8 à 30 jours | 4 115 — 29 | 21 002 — 159 | ×0,93 | ×0,91 [0,45 à 1,87] | oui |
| 31 à 90 jours | 11 170 — 50 | 46 366 — 111 | ×1,87 | ×1,79 [0,64 à 4,96] | non |
| 91 à 365 jours | 50 105 — 39 | 167 762 — 107 | ×1,22 | ×1,14 [0,64 à 2,02] | oui |
| plus d'un an | 394 355 — 82 | 1 607 595 — 280 | ×1,19 | ×1,00 [0,70 à 1,42] | oui |

- Aucune protection visible : les trois fourchettes citables contiennent 1.
- De 31 à 90 jours, non citable : Cedar Park Overhead Doors (cid `10505273405281271038`) porte 26
  des 50 suppressions d'avis répondus, du 12 au 23 août (`8_fiches_par_case.csv`).

### Par région, fiches qui répondent à plus de 75 %, sans enseignes

| | 8 à 30 jours | 31 à 90 jours | 91 à 365 jours | plus d'un an |
|---|---:|---:|---:|---:|
| États-Unis | ×0,78 [0,40 à 1,51] | ×0,54 [0,23 à 1,24] | ×0,28 [0,13 à 0,57] | ×1,17 [0,83 à 1,64] |
| Europe | ×0,40 [0,19 à 0,83] | ×0,15 [0,02 à 0,91], non citable | ×0,23 [0,09 à 0,60], non citable | ×0,88 [0,58 à 1,32] |

- États-Unis : les quatre effets sont citables. Seul celui de 91 jours à un an a une fourchette
  entièrement sous 1.
- Europe : de 8 à 30 jours, l'avis répondu disparaît 2,5 fois moins (×0,40), sur 42 suppressions
  d'avis répondus et 15 d'avis sans réponse. Les deux cases suivantes reposent sur 7 suppressions
  d'avis sans réponse.

### Avec les enseignes signalées

- Fiches qui répondent à plus de 75 % : ×1,00 [0,60 à 1,67] de 8 à 30 jours, ×0,33 [0,18 à 0,58]
  de 91 jours à un an, ×1,08 [0,83 à 1,41] au-delà d'un an.
- Fiches qui répondent à 75 % ou moins, 8 à 30 jours : ×1,64 [0,94 à 2,85], non citable. Les deux
  salles espagnoles portent 129 des 159 suppressions d'avis répondus : The Boxer Club (cid
  `10346942689164695031`, 72 suppressions du 12 au 23 août) et Boutique The Boxer Club Dr Castelo
  (cid `3163466139043001754`, 57 suppressions du 16 au 23 août).

### Les autres colonnes, pour mémoire (sans enseignes)

Colonnes de contrôle, sur les avis publiés avant le 4 août :
- note, face aux 5 étoiles : 1 étoile ×3,22 [2,16 à 4,80], 2 étoiles ×2,13 [1,55 à 2,93],
  3 étoiles ×1,98 [1,52 à 2,58] ;
- auteur sans niveau Local Guide, face aux niveaux 1 à 4 : ×4,87 [3,31 à 7,16] ;
- auteur à plus de 20 photos, face à l'auteur sans photo : ×0,56 [0,43 à 0,71] ;
- services à domicile, face à l'automobile : ×2,48 [1,60 à 3,83] ;
- fiche aux États-Unis, face à l'Europe : ×1,49 [1,18 à 1,87] ;
- photo jointe : ×0,98 [0,75 à 1,27].

---

## Les trois calculs sur la réponse

| | Point 5 | Point 7 | Point 8 |
|---|---|---|---|
| Avis | 35 095, publiés du 4 au 17 août | 4 718 683, publiés avant le 11 août | 4 488 470, publiés avant le 4 août, habitude connue |
| Suppressions | 1 349 | 3 189 | 2 476 |
| Réponse | datée jour par jour | état au 11 août | état au 11 août |
| Tenu égal | âge au jour près, note, région | âge par tranche, habitude | âge par tranche, habitude, note, profil de l'auteur, photo, texte, secteur, taille, région |
| Fiches à plus de 75 %, sans enseignes | premiers jours : ×0,36 et ×0,33 (mono + small), ×0,24 et ×0,23 (large) | 8 à 30 jours ×0,51 ; 91 à 365 jours ×0,21 | 8 à 30 jours ×0,70 [0,43 à 1,15] ; 91 à 365 jours ×0,26 [0,15 à 0,47] |
| Fiches à 75 % ou moins | un effet citable, fourchette qui contient 1 | ×0,93, ×1,22, ×1,19 | ×0,91, ×1,14, ×1,00, fourchettes qui contiennent 1 |

- Sur les fiches qui répondent à plus de 75 %, les trois calculs vont dans le même sens.
- L'écart est net sur les premiers jours de l'avis (point 5) et de 91 jours à un an (point 8).
- De 8 à 30 jours, une partie de l'écart du point 7 venait de la note. À caractéristiques égales,
  la fourchette contient 1 sur l'ensemble et aux États-Unis. En Europe : ×0,40 [0,19 à 0,83].
- Au-delà d'un an, aucun écart.
- Sur les fiches qui répondent à 75 % ou moins, aucun des trois calculs ne montre de protection.

---

## Réserves

- **Dans une tranche, l'âge n'est pas tenu égal au jour près.** De 8 à 30 jours, le risque baisse
  vite avec l'âge : 25 suppressions pour 10 000 avis au 8e jour, 4 au 30e (`2_1b_par_age.csv`,
  sans enseignes). Si les avis sans réponse de cette tranche sont plus récents ou plus anciens que
  les avis répondus, l'effet en compte une partie.
- **Sur les fiches qui répondent à plus de 75 %, l'avis sans réponse est rare.** Les cases de
  référence comptent 40, 18 et 19 suppressions.
- **Le sens de la cause reste ouvert.** Le propriétaire peut s'abstenir de répondre aux avis qu'il
  signale. Une réponse retirée est invisible.
- Un avis ancien présent le 11 août a survécu jusque-là : les résultats se lisent « parmi les avis
  encore en ligne le 11 août ».
- Le profil de l'auteur est lu au dernier passage du robot, en août 2026, même pour un avis de 2019.
- L'habitude de réponse est mesurée sur les avis d'août 2025 à août 2026. Pour un avis de plus d'un
  an, elle décrit la fiche d'aujourd'hui. Un avis publié du 11 août 2025 au 3 août 2026 entre dans
  l'habitude de sa propre fiche.
- 60 suppressions d'avis publiés avant le 4 août tombent sur des fiches d'habitude inconnue et
  sortent du calcul : 2 536 (`axel_comparaison_perimetres.csv`) moins 2 476.
- Europe sans enseignes, 8 à 30 jours, fiches à 75 % ou moins : 2 suppressions d'avis répondus. La
  case sort du passage (`8_effets.csv`, colonne `remarque`).
- La règle des 365 jours a retiré 555 suppressions de la base avant ce calcul (`1_corpus.md`).

## Écarté

- Le calcul direct sur les lignes par fiche, sans passer d'abord par les combinaisons de
  caractéristiques : mêmes effets et mêmes fourchettes, 20 secondes contre 4 sur le passage
  « Europe, sans_enseignes ».
- DuckDB : autorisé par Romain pour ce point, non utilisé. BigQuery regroupe les 4,5 millions
  d'avis en 983 948 lignes, qui tiennent en mémoire.
