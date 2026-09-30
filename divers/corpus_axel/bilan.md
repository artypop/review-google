# Bilan — la consolidation refaite sur le corpus d'Axel

Chiffres du 2026-09-30. Même code que `consolidation/`, autre table en entrée.

| Commande | Sortie |
|---|---|
| `uv run python divers/corpus_axel/lancer.py 0_controle_corpus` | `sorties/0_controle_corpus.csv`, `sorties/0b_avis_ajoutes.csv` |
| `nice -n 19 uv run python divers/corpus_axel/lancer.py` | les CSV et figures de la consolidation, mêmes noms, dans `sorties/` ; environ 4 minutes, dont 3 pour le 4b |
| `uv run python divers/corpus_axel/comparer.py` | `sorties/comparaison.csv` : chaque chiffre sur 03B, sur le corpus d'Axel, et l'écart |

---

## En bref

- Le corpus d'Axel ajoute 2 680 avis aux 35 751 du panel. Ces 2 680 avis sont tous supprimés.
- Les 88 taux du point 2.3 sont multipliés par 1,4 à 12,6, selon la part d'avis ajoutés dans
  chaque case (`sorties/comparaison.csv`). L'ordre des notes change, et l'effet des comptes sans
  niveau Local Guide disparaît.
- Des résultats de la consolidation disparaissent ou s'affaiblissent : les services à domicile,
  l'afflux d'avis sur la fiche, la protection de la réponse du propriétaire, l'écart entre
  l'avis 1 étoile et l'avis 5 étoiles dans une même fiche (×5,13 sur le panel, ×3,28 ici).
- Des résultats apparaissent, qui n'existent pas sur le panel : la taille de l'entreprise, le
  secteur sport et bien-être, un avis 3 étoiles plus exposé que le 5 étoiles, et un risque 9 à
  11 fois plus élevé pour les avis de 14 jours et plus.
- Le point 3 (réponse dans les deux jours) ne bouge pas d'un chiffre.

---

## 1. Les deux corpus

| | Panel 03B | Corpus d'Axel |
|---|---:|---:|
| Avis | 35 751 | 38 431 |
| dont supprimés | 1 355 | 4 035 |
| Publiés du 4 au 17 août 2026 | 35 751 | 35 751 |
| Publiés à d'autres dates | 0 | 2 680, tous supprimés |
| Suppressions pour 10 000 avis | 379 | 1 050 |

Source : `sorties/0_controle_corpus.csv`. 1 050 = 4 035 / 38 431. Sur la base entière, il
disparaît 8,5 avis pour 10 000 pendant les 14 jours de suivi (`consolidation/1_corpus.md`).

**Les 2 680 avis ajoutés** (`sorties/0b_avis_ajoutes.csv`) :
- 801 publiés avant le 11 août 2025, dont le plus ancien en 2014 ;
- 1 735 publiés du 11 août 2025 au 3 août 2026 ;
- 144 publiés du 18 au 24 août 2026 ;
- 813 avaient plus d'un an le jour de leur disparition ;
- 1 743 portent 5 étoiles, 661 portent 1 étoile ;
- 726 sont sur les 95 fiches signalées (4 chaînes antiparasitaires, 2 salles espagnoles).

---

## 2. Ce qui change

### Les taux par caractéristique (2.3 et 4.0)

Suppressions pour 10 000 avis, États-Unis et Europe réunis.

| Caractéristique | Panel 03B | Corpus d'Axel | Fichier |
|---|---:|---:|---|
| 5 étoiles | 385 | 946 | `2_3_note.csv` |
| 4 étoiles | 156 | 510 | |
| 3 étoiles | 101 | 751 | |
| 2 étoiles | 364 | 1 140 | |
| 1 étoile | 732 | 2 678 | |
| Auteur sans niveau Local Guide, sans enseignes | 600 | 855 | `2_3_local_guide.csv` |
| Auteur de niveau 1 à 4, sans enseignes | 274 | 881 | |
| Auteur sans photo publiée | 464 | 1 223 | `2_3_photos_auteur.csv` |
| Auteur à plus de 100 photos | 80 | 348 | |
| Secteur sport et bien-être | 377 | 1 789 | `2_3_secteur.csv` |
| Secteur services à domicile | 1 053 | 2 131 | |
| Fiche à moins de 10 avis d'historique | 94 | 997 | `2_3_habitude_reponse_fiche.csv` |
| Niveau Local Guide 4, sans enseignes | 255 | 829 | `4_0_niveaux_local_guide.csv` |
| Niveau Local Guide 5, sans enseignes | 143 | 631 | |

- **L'ordre des notes change.** Sur le panel, l'avis 3 étoiles est le moins supprimé. Sur le
  corpus d'Axel, il passe au-dessus du 4 étoiles.
- **L'effet des comptes sans niveau disparaît.** Sur le panel, sans les enseignes, un compte sans
  niveau perd 2,2 fois plus d'avis qu'un compte de niveau 1 à 4 (600 contre 274). Sur le corpus
  d'Axel : 855 contre 881.
- **L'écart lié aux photos de l'auteur se réduit.** 5,8 fois plus de suppressions sans photo
  qu'avec plus de 100 photos sur le panel ; 3,5 fois sur le corpus d'Axel.
- **Le secteur sport et bien-être passe de 377 à 1 789.** 597 avis ajoutés dans ce secteur, tous
  supprimés.
- **La coupure entre les niveaux 4 et 5 s'atténue.** Le niveau 4 perd 1,8 fois plus d'avis que le
  niveau 5 sur le panel, 1,3 fois sur le corpus d'Axel.

### Un cas déroulé : les avis 3 étoiles

- Panel : 1 194 avis 3 étoiles publiés du 4 au 17 août, 12 supprimés. 101 pour 10 000.
- Le corpus d'Axel y ajoute 84 avis 3 étoiles publiés à d'autres dates. Les 84 sont supprimés :
  ils sont entrés dans la table parce qu'ils ont disparu.
- Total : 1 278 avis, 96 supprimés. 751 pour 10 000.
- Les avis 3 étoiles publiés aux mêmes dates que ces 84 et restés en ligne ne sont pas dans la
  table. Le taux de 751 compte 84 suppressions sans les avis qui auraient dû figurer au
  dénominateur.

Le même mécanisme joue dans chaque case. Une case gonfle d'autant plus qu'elle reçoit d'avis
ajoutés : 661 avis 1 étoile ajoutés pour 2 487 dans le panel, 1 743 avis 5 étoiles ajoutés pour
28 112.

### Le point 3 : identique

- 0 chiffre changé sur 1 020 dans `3a_jour_par_jour.csv`, `3b_effectifs.csv` et `3b_effets.csv`
  (`sorties/comparaison.csv`).
- Le point 3 ne garde que les avis vus par le robot dès leur publication et suivis jusqu'à leur
  8e jour. Aucun avis ajouté ne remplit ces conditions : 17 473 avis des deux côtés
  (`3_population.csv`, étape 3).

### Quelle fiche est touchée (4a)

| | Panel 03B | Corpus d'Axel |
|---|---:|---:|
| Fiches dans le calcul | 1 890 | 1 969 |
| Fiches qui perdent au moins un avis | 262 | 732 |
| Suppressions portées par ces fiches | 1 256 | 3 503 |

Source : `4a_effectifs.csv`, passage « ensemble, tous ».

Effets sans les enseignes signalées (`4a_effets.csv`, passage « ensemble, sans_enseignes ») :

| Face à… | Colonne | Panel 03B | Corpus d'Axel |
|---|---|---:|---:|
| automobile | services à domicile | ×2,01 [1,15 à 3,49] | ×1,21 [0,80 à 1,83] |
| pas plus d'avis que d'habitude | 1 à 2 fois le rythme habituel | ×1,87 [1,14 à 3,07] | ×0,87 [0,65 à 1,18] |
| mono | small | ×1,53 [0,94 à 2,50] | ×1,52 [1,11 à 2,07] |
| mono | large | ×1,14 [0,70 à 1,85] | ×1,43 [1,05 à 1,94] |
| automobile | sport et bien-être | ×1,68 [0,90 à 3,11] | ×1,66 [1,08 à 2,55] |

- Deux résultats du panel disparaissent : les services à domicile et l'afflux.
- Trois effets que le panel ne tranche pas deviennent nets : small, large, sport et bien-être.

### Réponse du propriétaire, jour par jour (5)

| | Panel 03B | Corpus d'Axel |
|---|---:|---:|
| Avis-jours | 379 961 | 395 576 |
| Suppressions | 1 349 | 3 965 |

Source : `5_effectifs.csv`, lignes « total du passage », mono + small et large additionnés.

Effets sur mono + small (`5_effets.csv`) :

| Colonne | Panel 03B | Corpus d'Axel |
|---|---:|---:|
| Réponse le jour même, fiche qui répond à plus de 75 % | ×0,36 [0,20 à 0,63] | ×0,49 [0,32 à 0,74] |
| Réponse le lendemain, fiche qui répond à plus de 75 % | ×0,33 [0,18 à 0,60] | ×0,44 [0,30 à 0,65] |
| Avis de 14 jours et plus, face aux avis de 9 à 13 jours | ×0,55 [0,32 à 0,95] | ×11,11 [8,75 à 14,11] |
| Note 3 ou 4 étoiles, face aux 5 étoiles | ×0,60 [0,37 à 0,98] | ×0,91 [0,71 à 1,18] |

- **La protection de la réponse s'affaiblit.** Sur les fiches qui répondent à plus de 75 %, la
  case « réponse le jour même » passe de 80 à 260 suppressions pour 180 avis de plus : les
  180 avis ajoutés sont tous supprimés (`5_effectifs.csv`).
- **Les avis de 14 jours et plus paraissent 11 fois plus exposés.** Un avis ancien ajouté compte
  1 à 13 lignes, et la dernière est sa disparition. Ses voisins du même âge restés en ligne n'ont
  aucune ligne.
- **Une aggravation apparaît sur les fiches `large` qui répondent peu** : réponse à 3 jours et
  plus, ×2,91 [2,15 à 3,94], sur 263 suppressions contre 18 dans le panel. 223 viennent des deux
  salles espagnoles : Boutique The Boxer Club Dr Castelo (cid `3163466139043001754`, 120
  suppressions du 13 au 23 août) et The Boxer Club (cid `10346942689164695031`, 103 suppressions
  du 12 au 23 août), source `5_fiches_par_case.csv`. La règle de citation écarte cette case.

### Quel avis tombe dans la même fiche, le même jour (4b)

| | Panel 03B | Corpus d'Axel |
|---|---:|---:|
| Journées de fiche comparées | 738 | 1 906 |
| Avis-jours | 16 519 | 38 426 |
| Suppressions | 1 314 | 3 757 |
| Fiches | 314 | 1 007 |

Source : `4b_effectifs.csv`, passage « ensemble, tous », ligne « total du passage ».

Effets sans les enseignes signalées (`4b_effets.csv`, passage « ensemble, sans_enseignes ») :

| Face à… | Colonne | Panel 03B | Corpus d'Axel |
|---|---|---:|---:|
| 5 étoiles | 1 étoile | ×5,13 [3,73 à 7,06] | ×3,28 [2,73 à 3,94] |
| 5 étoiles | 3 étoiles | ×0,90 [0,43 à 1,88], non citable | ×1,45 [1,08 à 1,95] |
| 5 étoiles | 4 étoiles | ×0,56 [0,36 à 0,89] | ×0,88 [0,70 à 1,11] |
| niveau 1 à 4 | sans niveau Local Guide | ×1,56 [1,19 à 2,03] | ×1,28 [1,05 à 1,55] |
| auteur sans photo | auteur à plus de 20 photos | ×0,41 [0,24 à 0,72] | ×0,67 [0,51 à 0,87] |
| auteur à 1 avis ou moins | auteur à 2 à 20 avis | ×0,75 [0,61 à 0,93] | ×0,99 [0,87 à 1,13] |
| pas de réponse | réponse déjà là, fiche qui répond à plus de 75 % | ×0,21 [0,15 à 0,31] | ×0,34 [0,27 à 0,42] |
| pas de réponse | réponse déjà là, fiche qui répond à 75 % ou moins | ×0,56 [0,34 à 0,94], non citable | ×1,41 [1,07 à 1,86] |
| avis de 9 à 13 jours | avis de 14 jours et plus | ×0,59 [0,41 à 0,85] | ×9,11 [7,74 à 10,71] |

- **Les effets nets du panel se rapprochent de ×1** : la note 1 étoile, la note 4 étoiles, le
  compte sans niveau Local Guide, les photos de l'auteur, le nombre d'avis de l'auteur, la réponse
  sur les fiches qui répondent à plus de 75 %.
- **Deux effets changent de sens.** L'avis 3 étoiles paraît plus exposé que le 5 étoiles. Sur les
  fiches qui répondent peu, l'avis répondu paraît plus exposé que l'avis sans réponse.
- **Les avis de 14 jours et plus paraissent 9 fois plus exposés** : 1 613 suppressions contre 67
  dans le panel (`4b_effectifs.csv`).
- Comparer dans la même fiche le même jour annule ce qui tient à la fiche. Le défaut du corpus
  reste entier : dans une fiche, les avis anciens présents sont ceux qui ont disparu.
- Le passage « Europe, tous » n'aboutit pas sur le corpus d'Axel : le calcul ne trouve pas de
  solution stable, et ses effets ne se citent pas (`4b_effets.csv`, colonne `remarque`). Les six
  passages aboutissent sur le panel.

---

## 3. Les problèmes soulevés

1. **Un avis ajouté n'a aucun voisin resté en ligne.** Un avis de 2019 entre dans la table parce
   qu'il a disparu. Les avis de 2019 conservés n'y sont pas. Tout taux et tout effet compte ces
   suppressions sans leur dénominateur.
2. **La règle de citation ne repère pas ce défaut.** Elle compte des suppressions et des fiches.
   Avec 2 680 suppressions de plus, 56 effets sur 68 sont citables au 4a, contre 38 sur le
   panel ; 36 sur 48 au 5, contre 15 (`4a_effets.csv`, `5_effets.csv`, colonne `citable`, seuils
   du 2026-09-30 : 10 suppressions, 5 fiches, aucune fiche au-delà du quart).
3. **« Fiche touchée » change de sens au 4a.** Une fiche qui perd un seul avis de 2019 compte
   comme touchée : 732 fiches contre 262.
4. **L'afflux ne mesure plus un afflux.** Le 4a compare les avis de la fiche présents dans la
   table à son rythme habituel. Les avis anciens supprimés y comptent comme des avis reçus en
   août.
5. **Le seuil de 5 avis par fiche laisse entrer 79 fiches de plus**, grâce à leurs avis supprimés.
6. **1 735 avis ajoutés ont été publiés pendant l'année qui sert à mesurer l'habitude de réponse
   de leur fiche** (11 août 2025 au 3 août 2026). Ces avis entrent dans l'habitude à laquelle on
   les compare ensuite.
7. **Le profil de l'auteur est lu en août 2026.** Pour un avis de 2019, le niveau Local Guide,
   le nombre d'avis et de photos sont ceux de l'auteur sept ans plus tard.
8. **Les intitulés des sorties décrivent le panel.** `3_population.csv` affiche « 1. panel 03B »
   pour 38 431 avis publiés du 2014-10-07 au 2026-08-23.
9. **Le 4b prend 3 minutes 14 secondes**, contre une minute sur le panel : 1 906 journées de
   fiche contre 739, et une fiche qui perd 151 avis le même jour contre 14 au plus
   (`sorties/0c_taille_4b.csv`). Son passage « Europe, tous » n'aboutit pas.
10. **La première version de `corpus_axel` était une copie de 03B.** La jointure rendait les
    35 751 avis du panel et aucun avis ajouté. La table a été reconstruite le 2026-09-30 ;
    `0_controle_corpus.csv` vérifie son contenu.

---

## 4. Réserves

- Le point 7 de la liste est une explication probable de la disparition de l'effet « sans
  niveau ». Elle n'a pas été vérifiée.
- Les six enseignes signalées portent 726 des 2 680 avis ajoutés. Chaque CSV garde sa version
  `sans_enseignes`.

---

## 5. Ce qui a été écrit

| Fichier | Rôle |
|---|---|
| `lancer.py` | exécute les scripts de `consolidation/` tels quels ; remplace `reviews_panel_features_03B` par `reviews_panel_features_axel` dans les requêtes ; écrit dans `divers/corpus_axel/sorties/` |
| `comparer.py` | met côte à côte les CSV des deux corpus |
| `sql/0_controle_corpus.sql`, `sql/0b_avis_ajoutes.sql` | contenu de `corpus_axel` et profil des avis ajoutés |
| `sql/1_features_axel.bqsql` | la requête de 03B, deux lignes changées : table écrite, table lue |

Une table créée dans BigQuery : `client-divers.reviewflowz.reviews_panel_features_axel`
(38 431 lignes). Aucun fichier de `consolidation/` n'a été modifié.
