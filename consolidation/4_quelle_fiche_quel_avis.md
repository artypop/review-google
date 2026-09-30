# 4. Quelle fiche est touchée, quel avis tombe dans la fiche

| Commande | CSV |
|---|---|
| `uv run python consolidation/4_0_niveaux_local_guide.py` | `4_0_niveaux_local_guide.csv` |
| `uv run python consolidation/4a_quelle_fiche.py` | `4a_effectifs.csv`, `4a_effets.csv`, `4a_fiches_touchees.csv` |
| `nice -n 19 uv run python consolidation/4b_quel_avis.py` (environ 1 minute) | `4b_effectifs.csv`, `4b_effets.csv`, `4b_fiches_par_case.csv` |

Chiffres du 2026-09-29. Panel 03B : avis publiés du 4 au 17 août 2026.

**Pourquoi deux régressions.** Retirer les enseignes « à problème » une par une ne couvre que
celles qu'on a repérées. On sépare donc deux questions :
- **4a, quelle fiche se fait toucher** : une ligne par fiche. Chaque fiche compte une fois,
  qu'elle perde 1 avis ou 30.
- **4b, quel avis tombe dans une fiche touchée** : on ne compare que des avis de la même fiche, le
  même jour. Tout ce qui tient à la fiche s'annule : secteur, pays, taille, politique de
  modération, et le fait d'être une chaîne ou une salle.

**Lecture d'un effet.** « ×2 » veut dire deux fois plus de chances, toutes les autres colonnes
égales. La fourchette donne les valeurs compatibles avec les données ; quand elle contient 1, les
données ne tranchent pas.

**Règle de citation** (`commun.py`, seuils du 2026-09-30) : la case et sa référence ont au moins
10 suppressions, sur au moins 5 fiches, sans qu'une fiche en porte plus du quart. Seuls les effets
« citables » sont repris ci-dessous. Les seuils du 2026-09-29 étaient 20 suppressions et
10 fiches : le 4a ne change pas (38 effets citables sur 68), le 4b passe de 108 à 124 effets
citables sur 154.

---

## 4.0 Les paliers Local Guide (`4_0_niveaux_local_guide.csv`)

Suppressions pour 10 000 avis, par niveau, sans enseignes, US et Europe réunis :

| Niveau | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|---|---:|---:|---:|---:|---:|---:|---:|
| pour 10 000 | 353 | 278 | 264 | 255 | 143 | 65 | 133 |

- Le niveau 4 se comporte comme les niveaux 1 à 3. Le niveau 5 est nettement plus bas, le 6
  plus bas encore.
- Le niveau 7 repose sur 12 suppressions, et les niveaux 8 à 10 sur 1.
- Paliers retenus : sans niveau (600 pour 10 000), 1 à 4, 5 et plus.

---

## 4a. Quelle fiche est touchée (`4a_effets.csv`)

1 890 fiches ont au moins 5 avis dans le panel. 262 en perdent au moins un, et portent 1 256
suppressions. Sans enseignes : 1 813 fiches, 214 touchées, 785 suppressions.

### Ce qui distingue les fiches touchées

| Face à… | Colonne | Tous | Sans enseignes | US, sans enseignes |
|---|---|---:|---:|---:|
| automobile | services à domicile | ×3,03 [1,82 à 5,02] | ×2,01 [1,15 à 3,49] | ×2,36 [1,24 à 4,49] |
| pas plus d'avis que d'habitude | 1 à 2 fois son rythme habituel | ×1,49 [0,97 à 2,28] | ×1,87 [1,14 à 3,07] | ×1,76 [0,96 à 3,20] |
| pas plus d'avis que d'habitude | plus de 2 fois son rythme habituel | ×1,48 [0,93 à 2,36] | ×1,69 [0,99 à 2,88] | ×1,22 [0,62 à 2,43] |
| Europe | États-Unis | ×1,43 [1,03 à 1,99] | ×1,30 [0,93 à 1,83] | — |

- À taille, région et habitude égales, une fiche de services à domicile a 2 fois plus de chances
  qu'une fiche automobile de perdre un avis, même sans les 4 chaînes.
- Une fiche qui reçoit, sur les 14 jours, 1 à 2 fois son rythme habituel d'avis a 1,9 fois plus
  de chances d'en perdre un (sans enseignes). Au-delà de 2 fois, ×1,69 et la fourchette touche 1.

### Ce que les données ne tranchent pas

- Taille : small ×1,53 [0,94 à 2,50], large ×1,14 [0,70 à 1,85], face aux mono (sans enseignes).
- Habitude de réponse : fiche qui répond à plus de 75 %, ×0,95 [0,69 à 1,31].
- Santé, hôtellerie, sport et bien-être : fourchettes qui contiennent 1.

### Non citables

- Restauration et voyage : une seule fiche porte plus du quart de leurs suppressions (31 % pour la
  restauration).
- **Europe** : aucun effet de secteur, de taille ou d'afflux n'est citable. Les cases de
  référence ne passent pas la règle : 7 fiches automobiles dont une porte 56 % des suppressions,
  16 mono dont une porte 34 %, 8 suppressions sur les fiches sans afflux (`4a_effectifs.csv`).

---

## 4b. Quel avis tombe dans une fiche touchée (`4b_effets.csv`)

Comparaison possible sur 314 fiches et 738 journées de fiche : 6 350 avis, soit 16 519
avis-jours, et 1 314 des 1 355 suppressions. Sans enseignes : 4 888 avis, 841 suppressions. Les 41 autres tombent des jours où la fiche n'avait qu'un avis en ligne, ou
les a tous perdus : rien à comparer.

### Ce qui fait tomber un avis, dans la même fiche, le même jour

| Face à… | Colonne | Tous | Sans enseignes |
|---|---|---:|---:|
| 5 étoiles | 1 étoile | ×3,45 [2,61 à 4,56] | ×5,13 [3,73 à 7,06] |
| 5 étoiles | 2 étoiles | ×2,10 [1,24 à 3,54] | ×2,82 [1,59 à 5,02] |
| 5 étoiles | 4 étoiles | ×0,55 [0,38 à 0,80] | ×0,56 [0,36 à 0,89] |
| avis de 9 à 13 jours | avis de 7 jours | ×9,31 [7,61 à 11,39] | ×7,11 [5,49 à 9,22] |
| avis de 9 à 13 jours | avis de 6 jours | ×3,20 [2,58 à 3,96] | ×2,77 [2,10 à 3,66] |
| Local Guide 1 à 4 | sans niveau Local Guide | ×1,45 [1,16 à 1,82] | ×1,56 [1,19 à 2,03] |
| auteur sans photo | auteur à plus de 20 photos | ×0,41 [0,25 à 0,68] | ×0,41 [0,24 à 0,72] |
| auteur à 1 avis déclaré | auteur à 2 à 20 avis | ×0,86 [0,73 à 1,02] | ×0,75 [0,61 à 0,93] |
| pas de réponse | réponse déjà là, fiche qui répond à plus de 75 % | ×0,21 [0,15 à 0,30] | ×0,21 [0,15 à 0,31] |
| pas de réponse | réponse déjà là, fiche qui répond à 75 % ou moins | ×0,41 [0,27 à 0,62] | non citable |

- **Dans une fiche touchée, l'avis 1 étoile tombe 5 fois plus que l'avis 5 étoiles** (sans
  enseignes). Il tombe 4,9 fois plus aux États-Unis et 4,7 fois plus en Europe.
- **L'avis déjà répondu tombe 5 fois moins que l'avis sans réponse de la même fiche**, sur les
  fiches qui répondent à plus de 75 %. Le chiffre est le même avec et sans enseignes. Sans
  enseignes : 2 158 avis répondus, 245 suppressions sur 85 fiches (`4b_effectifs.csv`).
- Sur les fiches qui répondent à 75 % ou moins, l'avis répondu tombe aussi moins :
  - ×0,41, avec les enseignes, sur 88 suppressions et 27 fiches ;
  - sans enseignes, ×0,56 [0,34 à 0,94], non citable : une fiche porte 35 % des suppressions.
- Le compte sans niveau Local Guide tombe 1,5 fois plus. L'auteur à plus de 20 photos tombe
  2,4 fois moins.
- La photo jointe et la longueur du texte ne changent rien : toutes les fourchettes contiennent 1.
- Le 7e jour de l'avis reste le jour le plus risqué, dans la même fiche comme ailleurs.
- Devenus citables avec les seuils du 2026-09-30, hors colonnes d'âge (`4b_effets.csv`) :
  - avis 3 étoiles, tous : ×0,67 [0,33 à 1,34], les données ne tranchent pas ;
  - avis 2 étoiles aux États-Unis : ×2,57 [1,23 à 5,37], et ×4,55 [2,04 à 10,15] sans enseignes ;
  - avis 4 étoiles en Europe : ×0,51 [0,27 à 0,97], et ×0,52 [0,28 à 0,98] sans enseignes ;
  - auteur à plus de 20 photos aux États-Unis : ×0,28 [0,14 à 0,55] ;
  - trois autres dont la fourchette contient 1 : 4 étoiles aux États-Unis sans enseignes,
    2 étoiles et auteur à plus de 20 photos en Europe sans enseignes.

### Ce que change le retrait des enseignes

- L'effet de la réponse ne bouge pas (×0,21 et ×0,21). Comparer dans la même fiche a bien
  neutralisé les chaînes et les salles.
- L'effet de la note 1 étoile passe de ×3,45 à ×5,13. Dans les fiches des 4 chaînes, l'écart
  entre avis 1 étoile et 5 étoiles est plus faible qu'ailleurs.

---

## Ce que 4 dit du point 3

Au 3b et au 5, sur les fiches qui répondent à 75 % ou moins, l'avis répondu semblait disparaître
plus. Dans la même fiche, il disparaît moins, ou autant. L'écart du 3b et du 5 vient surtout de
Cedar Park Overhead Doors (cid `10505273405281271038`) : une fiche qui répond peu, qui a répondu
le jour même à certains avis, et qui en perd beaucoup (`5_fiches_par_case.csv`).

---

## Réserves

- 4b ne dit que ce qui se passe dans les fiches touchées. Il ne dit pas ce que Google vise dans
  l'absolu.
- Dans 4b, la fourchette traite les journées d'une même fiche comme indépendantes. La règle de
  citation écarte les effets portés par quelques fiches.
- Les caractéristiques de l'auteur sont lues au dernier passage où l'avis est vu.
- « Sans niveau » et « 1 avis déclaré » décrivent souvent le même compte neuf : les deux colonnes
  se partagent l'effet.
- 4a : le nombre d'avis de la fiche sert de contrôle et ne se cite pas. Les fiches avec moins de
  5 avis dans le panel sont hors du calcul, et 7 fiches sans historique en sont retirées (aucune
  touchée).
- Le sens de la cause reste ouvert pour la réponse : un propriétaire qui conteste un avis peut
  s'abstenir d'y répondre. Les données ne montrent pas les signalements.
