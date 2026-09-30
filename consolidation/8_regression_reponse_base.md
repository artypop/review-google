# 8. La réponse du propriétaire sur toute la base, à caractéristiques égales

| Commande | CSV |
|---|---|
| `nice -n 19 uv run python consolidation/8_regression_reponse_base.py` (environ 50 secondes, 2,8 Go de mémoire) | `8_effectifs.csv`, `8_effets.csv`, `8_fiches_par_case.csv`, `8_notes_par_case.csv` |

Chiffres du 2026-09-30. Base : `reviews_doublons_cleaned_all`, les avis publiés avant le 4 août 2026
sur les fiches dont l'habitude de réponse est connue. Suppressions constatées du 12 au 24 août.

## Le calcul

- **Population** : 4 609 086 avis, 6 905 fiches, 3 030 suppressions. Sans les 95 fiches
  signalées : 4 364 321 avis, 6 815 fiches, 1 997 suppressions (`8_effectifs.csv`, lignes « total
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
| 8 à 30 jours | 25 322 — 249 | 2 090 — 40 | ×0,51 | ×0,66 [0,40 à 1,08] | oui |
| 31 à 90 jours | 64 641 — 122 | 2 855 — 18 | ×0,30 | ×0,39 [0,16 à 0,93] | non |
| 91 à 365 jours | 253 655 — 132 | 7 546 — 19 | ×0,21 | ×0,25 [0,14 à 0,44] | oui |
| plus d'un an | 1 072 517 — 310 | 578 524 — 120 | ×1,39 | ×1,11 [0,83 à 1,47] | oui |

- **De 91 jours à un an, l'avis répondu disparaît 4 fois moins** (×0,25), à caractéristiques
  égales. Le rapport direct donnait ×0,21.
- **De 8 à 30 jours, ×0,66, et la fourchette contient 1** : les données ne tranchent pas. Le
  rapport direct donnait ×0,51.
- De 31 à 90 jours, ×0,39, non citable : TKE veterinary clinic Elversberg (cid
  `13197914448513377771`) porte 6 des 18 suppressions d'avis sans réponse, toutes le 19 août
  (`8_fiches_par_case.csv`).
- Au-delà d'un an, aucune protection : ×1,11, et la fourchette contient 1.

### Un cas déroulé : pourquoi ×0,51 devient ×0,66

Avis de 8 à 30 jours, fiches qui répondent à plus de 75 % (`8_notes_par_case.csv`) :
- parmi les 25 322 avis répondus, 4,6 % portent 1 étoile ;
- parmi les 2 090 avis sans réponse, 15,9 % portent 1 étoile ;
- dans ce calcul, un avis 1 étoile disparaît 2,9 fois plus qu'un 5 étoiles
  (×2,85 [1,93 à 4,21], `8_effets.csv`).

Le rapport direct ×0,51 comptait donc en partie la note. À note égale :
- avis 5 étoiles : 210 disparus sur 21 210 répondus (99 pour 10 000), 19 sur 1 391 sans réponse
  (137 pour 10 000), soit ×0,72 ;
- avis 1 étoile : 28 disparus sur 1 156 répondus (242 pour 10 000), 16 sur 333 sans réponse
  (480 pour 10 000), soit ×0,50.

Même lecture de 91 jours à un an, avis 5 étoiles : 115 disparus sur 217 626 répondus (5,3 pour
10 000), 9 sur 4 525 sans réponse (19,9 pour 10 000), soit ×0,27.

### Fiches qui répondent à 75 % ou moins

| Âge le 11 août | Répondus : avis, suppressions | Sans réponse : avis, suppressions | Rapport direct (point 7) | À caractéristiques égales | Citable |
|---|---:|---:|---:|---:|---|
| 8 à 30 jours | 4 115 — 29 | 21 002 — 159 | ×0,93 | ×0,91 [0,45 à 1,83] | oui |
| 31 à 90 jours | 11 170 — 50 | 46 366 — 111 | ×1,87 | ×1,76 [0,66 à 4,74] | non |
| 91 à 365 jours | 50 105 — 39 | 167 766 — 108 | ×1,21 | ×1,12 [0,63 à 2,00] | oui |
| plus d'un an | 409 299 — 138 | 1 647 348 — 353 | ×1,57 | ×1,27 [0,86 à 1,89] | oui |

- Aucune protection visible : les trois fourchettes citables contiennent 1.
- De 31 à 90 jours, non citable : Cedar Park Overhead Doors (cid `10505273405281271038`) porte 26
  des 50 suppressions d'avis répondus, du 12 au 23 août (`8_fiches_par_case.csv`).

### Par région, fiches qui répondent à plus de 75 %, sans enseignes

| | 8 à 30 jours | 31 à 90 jours | 91 à 365 jours | plus d'un an |
|---|---:|---:|---:|---:|
| États-Unis | ×0,72 [0,37 à 1,40] | ×0,52 [0,22 à 1,20] | ×0,25 [0,12 à 0,52] | ×1,37 [0,96 à 1,96] |
| Europe | ×0,41 [0,20 à 0,83] | ×0,15 [0,02 à 0,92], non citable | ×0,24 [0,09 à 0,61], non citable | ×0,84 [0,56 à 1,27] |

- États-Unis : les quatre effets sont citables. Seul celui de 91 jours à un an a une fourchette
  entièrement sous 1.
- Europe : de 8 à 30 jours, l'avis répondu disparaît 2,4 fois moins (×0,41), sur 42 suppressions
  d'avis répondus et 15 d'avis sans réponse. Les deux cases suivantes reposent sur 7 suppressions
  d'avis sans réponse.

### Le seuil de 75 % : ce que donnent d'autres coupures

Test du 2026-09-30 : `nice -n 19 uv run python consolidation/9_seuil_habitude.py 8` (2 min 20, 4 Go
de mémoire), sortie `9_seuil_habitude_point8.csv`. Mêmes avis, mêmes colonnes ; seule la coupure de
l'habitude change.

Fiches au-dessus de la coupure, sans enseignes :

| Coupure | 8 à 30 jours | 31 à 90 jours | 91 à 365 jours | plus d'un an |
|---|---:|---:|---:|---:|
| 50 % | ×0,82 [0,54 à 1,23] | ×0,62 [0,31 à 1,23] | ×0,47 [0,29 à 0,76] | ×1,17 [0,92 à 1,50] |
| 75 % | ×0,66 [0,40 à 1,08] | ×0,39 [0,16 à 0,93], non citable | ×0,25 [0,14 à 0,44] | ×1,11 [0,83 à 1,47] |
| 90 % | ×0,47 [0,27 à 0,82] | ×0,23 [0,09 à 0,63], non citable | ×0,23 [0,11 à 0,46] | ×1,13 [0,83 à 1,55] |

- **De 91 jours à un an, la protection apparaît aux trois coupures**, citable à chaque fois.
- **Avant un an, l'effet se renforce quand la coupure monte.** À 90 %, l'avis répondu de 8 à
  30 jours disparaît 2 fois moins : ×0,47 [0,27 à 0,82], citable.
- Au-delà d'un an, aucune protection, quelle que soit la coupure : ×1,17, ×1,11 et ×1,13,
  fourchettes qui contiennent 1.
- Les fiches au-dessus de 75 % sont surtout des fiches au-dessus de 90 % : 22 220 des 25 322 avis
  répondus de 8 à 30 jours.

Fiches sous la coupure, sans enseignes :
- coupure à 90 % : ×1,02 [0,58 à 1,81] de 8 à 30 jours, ×0,81 [0,49 à 1,37] de 91 jours à un an,
  ×1,20 [0,84 à 1,70] au-delà ; les trois fourchettes contiennent 1 ;
- coupure à 50 % : seule la case de plus d'un an est citable, ×0,98 [0,62 à 1,55].

Quatre tranches (25 % ou moins, 25 à 50, 50 à 75, plus de 75), sans enseignes :
- sous 75 %, les seules cases citables sont celles de plus d'un an : ×1,06 [0,59 à 1,88],
  ×1,25 [0,73 à 2,11] et ×1,80 [1,03 à 3,16]. La troisième, fiches de 50 à 75 %, a une
  fourchette au-dessus de 1 : 69 suppressions d'avis répondus, dont un quart sur une fiche ;
- entre 8 jours et un an, sur les 9 cases sous 75 %, 3 sortent faute de 5 suppressions d'avis
  répondus et 6 ne sont pas citables ;
- avant un an, la tranche de 50 à 75 % donne ×1,39, ×2,60 et ×1,92, non citables : 8 à 19 suppressions d'avis
  sans réponse, et une fiche porte jusqu'à 65 % des suppressions d'avis répondus.
- Les données ne montrent donc pas une progression régulière tranche par tranche : sous 75 %, il
  y a trop peu de suppressions pour la voir ou l'exclure.

Ce que le test établit :
- la protection sur les fiches qui répondent à presque tout existe à 50, 75 et 90 % ;
- les fiches qui répondent à plus de 90 % forment l'essentiel du groupe « plus de 75 % », et
  l'effet y est au moins aussi fort ;
- 75 % reste le réglage des points 5 et 8. Passer à 90 % parce qu'il donne un effet plus net
  reviendrait à choisir la coupure d'après le résultat.

### Avec les enseignes signalées

- Fiches qui répondent à plus de 75 % : ×0,88 [0,53 à 1,47] de 8 à 30 jours, ×0,28 [0,16 à 0,50]
  de 91 jours à un an.
- Au-delà d'un an, sur ces fiches, l'avis répondu disparaît 1,4 fois plus : ×1,36 [1,05 à 1,75],
  citable. 138 des 448 suppressions d'avis répondus de cette case sont sur les fiches signalées ;
  sans elles, ×1,11 [0,83 à 1,47].
- Fiches qui répondent à 75 % ou moins, 8 à 30 jours : ×1,79 [1,00 à 3,22], non citable. Les deux
  salles espagnoles portent 129 des 159 suppressions d'avis répondus : The Boxer Club (cid
  `10346942689164695031`, 72 suppressions du 12 au 23 août) et Boutique The Boxer Club Dr Castelo
  (cid `3163466139043001754`, 57 suppressions du 16 au 23 août).

### Les autres colonnes, pour mémoire (sans enseignes)

Colonnes de contrôle, sur les avis publiés avant le 4 août :
- note, face aux 5 étoiles : 1 étoile ×2,85 [1,93 à 4,21], 2 étoiles ×1,92 [1,40 à 2,62],
  3 étoiles ×1,76 [1,36 à 2,29] ;
- auteur sans niveau Local Guide, face aux niveaux 1 à 4 : ×4,86 [3,32 à 7,10] ;
- auteur à plus de 20 photos, face à l'auteur sans photo : ×0,54 [0,43 à 0,68] ;
- services à domicile, face à l'automobile : ×3,15 [2,09 à 4,75] ;
- fiche aux États-Unis, face à l'Europe : ×1,65 [1,32 à 2,06] ;
- photo jointe : ×0,96 [0,75 à 1,23].

---

## Les trois calculs sur la réponse

| | Point 5 | Point 7 | Point 8 |
|---|---|---|---|
| Avis | 35 095, publiés du 4 au 17 août | 4 843 936, publiés avant le 11 août | 4 609 086, publiés avant le 4 août, habitude connue |
| Suppressions | 1 349 | 3 744 | 3 030 |
| Réponse | datée jour par jour | état au 11 août | état au 11 août |
| Tenu égal | âge au jour près, note, région | âge par tranche, habitude | âge par tranche, habitude, note, profil de l'auteur, photo, texte, secteur, taille, région |
| Fiches à plus de 75 %, sans enseignes | premiers jours : ×0,36 et ×0,33 (mono + small), ×0,24 et ×0,23 (large) | 8 à 30 jours ×0,51 ; 91 à 365 jours ×0,21 | 8 à 30 jours ×0,66 [0,40 à 1,08] ; 91 à 365 jours ×0,25 [0,14 à 0,44] |
| Fiches à 75 % ou moins | un effet citable, fourchette qui contient 1 | ×0,93, ×1,21, ×1,57 | ×0,91, ×1,12, ×1,27, fourchettes qui contiennent 1 |

- Sur les fiches qui répondent à plus de 75 %, les trois calculs vont dans le même sens.
- L'écart est net sur les premiers jours de l'avis (point 5) et de 91 jours à un an (point 8).
- De 8 à 30 jours, une partie de l'écart du point 7 venait de la note. À caractéristiques égales,
  la fourchette contient 1 sur l'ensemble et aux États-Unis. En Europe : ×0,41 [0,20 à 0,83].
- Au-delà d'un an, aucune protection : ×1,11 [0,83 à 1,47].
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
- 61 suppressions d'avis publiés avant le 4 août tombent sur des fiches d'habitude inconnue et
  sortent du calcul : 3 091 (`axel_comparaison_perimetres.csv`) moins 3 030.
- Europe sans enseignes, 8 à 30 jours, fiches à 75 % ou moins : 2 suppressions d'avis répondus. La
  case sort du passage (`8_effets.csv`, colonne `remarque`).
- **La tranche « plus d'un an » contient les avis modifiés plus d'un an après leur publication**
  (`1_corpus.md`, réserves). Leur âge se compte depuis la publication : un avis de 2023 réécrit
  en juillet 2026 y est rangé avec les avis anciens restés intacts.

## Écarté

- Le calcul direct sur les lignes par fiche, sans passer d'abord par les combinaisons de
  caractéristiques : mêmes effets et mêmes fourchettes, 20 secondes contre 4 sur le passage
  « Europe, sans_enseignes ».
- DuckDB : autorisé par Romain pour ce point, non utilisé. BigQuery regroupe les 4,6 millions
  d'avis en 994 805 lignes, qui tiennent en mémoire.
