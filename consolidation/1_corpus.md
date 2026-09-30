# 1. Le corpus

| Commande | CSV |
|---|---|
| `uv run python consolidation/1a_tables.py` | `1a_tables.csv`, `1a_fiches_par_case.csv` |
| `uv run python consolidation/1b_entonnoir.py` | `1b_entonnoir.csv` |
| `uv run python consolidation/1c_secteurs.py` | `1c_avis_secteur_taille.csv`, `1c_suppressions_secteur_region.csv` |
| `uv run python consolidation/1d_survie.py` | `1d_survie.csv` |

Chiffres du 2026-09-30. Base complète : `reviews_doublons_cleaned_all`.

---

## 1.1 Ce que contiennent les tables

### `businesses` : une ligne par fiche Google Maps

- 9 048 fiches, 41 pays (`1a_tables.csv`).
- Colonnes :
  - `cid` : identifiant de la fiche, clé de jointure avec les avis ;
  - `name` : nom de l'enseigne à la construction du panel ;
  - `country` : pays ; tout ce qui n'est pas `US` est rangé en Europe ;
  - `industry` : un des 7 secteurs ;
  - `bucket` : taille du groupe, `mono` (1 établissement), `small` (4 à 10), `large` (20 à 50) ;
  - `review_count_at_build` : nombre d'avis annoncé par Google en juillet 2026.
- Le tirage (`1a_fiches_par_case.csv`) : environ 238 fiches par case région × secteur × taille.
  Le voyage n'a que des `mono`, 240 fiches par région.
- Un groupe tiré entre avec tous ses établissements. Les groupes de 2-3, de 11-19 et de plus de
  50 établissements sont absents.

### `reviews` : l'export du robot

- 4 880 163 lignes pour 4 877 534 avis, publiés du 30/09/2004 au 24/08/2026, sur 8 997 fiches.
  51 fiches n'ont aucun avis (`1a_tables.csv`).
- Le robot a relevé la totalité des avis de chaque fiche une fois par jour, du 11 au 24 août 2026 :
  14 passages. J = 11 août.
- Colonnes :
  - l'avis : `review_id` (identifiant Google, répété quand l'avis a plusieurs lignes), `star`,
    `text`, `language`, `n_photos` (photos jointes), `created_at` (publication), `updated_at`
    (dernière modification par l'auteur), `is_update` et `changed_fields` (ligne écrite quand
    l'auteur change la note ou le texte) ;
  - l'auteur : `review_link`, `reviewer_name`, `reviewer_avatar` (données personnelles),
    `reviewer_review_count` (avis déclarés), `reviewer_photo_count` (photos publiées sur son
    profil), `local_guide`, `local_guide_level` (1 à 10) ;
  - la réponse du propriétaire : `reply_text`, `reply_date`. Elle est écrasée en place : une
    réponse retirée ne laisse aucune trace ;
  - le suivi : `first_seen_at` (premier passage qui voit l'avis), `last_seen_at` (dernier),
    `deleted_detected_at` (premier passage qui ne le trouve plus, vide s'il est en ligne le
    24 août).
- Heures en UTC.

---

## 1.2 Comment le corpus est construit

`1b_entonnoir.csv` rejoue la construction de `reviews_doublons_cleaned_all`, étape par étape.

| Étape | Avis | Avis supprimés |
|---|---:|---:|
| 1. export brut, 4 880 163 lignes | 4 877 534 | 5 192 |
| 2. une ligne par avis, la dernière version | 4 877 534 | 4 697 |
| 3. sans les avis qui ont clignoté | 4 876 933 | 4 590 |
| 4. publiés du 4 au 17 août, J-7 à J+6 | 35 751 | 1 355 |

- Étape 2 : un avis modifié ou revenu a plusieurs lignes. On garde la plus récemment modifiée,
  puis la plus récemment vue. 495 avis avaient une ligne marquée disparue et sont en ligne dans
  leur dernière version.
- Étape 3 : un avis à plusieurs lignes est gardé seulement si sa dernière ligne est une
  modification de l'auteur. Les 601 autres ont disparu puis sont revenus. Ils sortent, avec
  107 suppressions.
- L'étape 3 donne exactement la table `reviews_doublons_cleaned_all` : mêmes avis, mêmes avis
  supprimés. L'étape 4 donne exactement la table 03B. Les cinq contrôles de `1b_entonnoir.csv`
  sont à 0.
- Jusqu'au 2026-09-29, la base était `reviews_doublons_cleaned`, qui écartait en plus les avis
  modifiés plus de 365 jours après leur publication : 125 253 avis, dont 555 supprimés (écart
  entre `1a_tables.csv` du commit `61394d9` et celui d'aujourd'hui). Ces avis sont maintenant
  dans la base. Aucun n'a été publié du 4 au 17 août : 03B est inchangée.

**Une suppression** : la ligne gardée de l'avis a `deleted_detected_at` rempli. Les premières sont
constatées le 12 août (2e passage), les dernières le 24.

**La base complète** : l'étape 3, `reviews_doublons_cleaned_all`. **Le panel 03B** : l'étape 4,
utilisé aux points 2.3 et 3.

---

## 1.3 Résultats

### La base complète

- 4 876 933 avis, dont 2 627 609 aux États-Unis et 2 249 324 en Europe.
- 4 590 disparaissent pendant les 14 jours de suivi : 9,4 pour 10 000 avis.
  US 12,4, Europe 5,9 (`1c_suppressions_secteur_region.csv`, ligne « Tous secteurs »).
- Sans enseignes : 4 627 581 avis, 3 067 suppressions, 6,6 pour 10 000. US 8,6, Europe 4,5.

### Avis par secteur (`1c_avis_secteur_taille.csv`)

| Secteur | Avis | Part du corpus |
|---|---:|---:|
| Restauration | 1 183 078 | 24,3 % |
| Hôtellerie | 990 568 | 20,3 % |
| Services à domicile | 761 023 | 15,6 % |
| Automobile | 653 857 | 13,4 % |
| Santé | 558 901 | 11,5 % |
| Sport et bien-être | 512 023 | 10,5 % |
| Voyage | 217 483 | 4,5 % |

- Le détail mono / small / large est dans le CSV.
- Sans enseignes, les services à domicile perdent 247 938 avis : 93 fiches `large` des 4 chaînes.

### Suppressions pour 10 000 avis, par secteur (`1c_suppressions_secteur_region.csv`)

| Secteur | US | US sans enseignes | Europe | Europe sans enseignes |
|---|---:|---:|---:|---:|
| Services à domicile | 35,3 | 24,7 | 4,0 | 4,0 |
| Sport et bien-être | 10,4 | 10,4 | 16,8 | 6,5 |
| Voyage | 9,4 | 9,4 | 10,7 | 10,7 |
| Santé | 11,7 | 11,7 | 5,0 | 5,0 |
| Automobile | 6,8 | 6,8 | 4,2 | 4,2 |
| Hôtellerie | 3,2 | 3,2 | 3,6 | 3,6 |
| Restauration | 3,3 | 3,3 | 3,4 | 3,4 |

- Les services à domicile américains sont le secteur le plus touché, avec ou sans les 4 chaînes.
- Le sport européen passe de 16,8 à 6,5 sans les 2 salles espagnoles.
- Hôtellerie et restauration sont au même niveau des deux côtés, autour de 3 pour 10 000.

### Survie des avis publiés de J-7 à J+7 (`1d_survie.csv`)

Avis publiés du 4 au 18 août. Lecture : sur 10 000 avis publiés, combien sont encore en ligne à
chaque âge.

| Encore en ligne sur 10 000 | au 8e jour | au 20e jour |
|---|---:|---:|
| ensemble | 9 619 | 9 412 |
| ensemble, sans enseignes | 9 715 | 9 559 |
| US | 9 508 | 9 286 |
| US, sans enseignes | 9 673 | 9 500 |
| Europe | 9 684 | 9 498 |
| Europe, sans enseignes | 9 684 | 9 548 |

- Le 7e jour compte le plus de disparitions : 137 pour 10 000 avis en ligne la veille
  (84 sans enseignes). Aux États-Unis, 208 (118 sans enseignes).
- En Europe, les pertes commencent plus tôt : au 2e jour, 41 pour 10 000 contre 26 aux
  États-Unis.

---

## 1.4 Réserves à écrire dans ce chapitre

- Les suppressions sont celles des 14 jours de suivi. La base contient des avis publiés depuis
  2004, mais un avis supprimé avant le 11 août n'y figure pas.
- La base contient 125 253 avis modifiés plus d'un an après leur publication, dont 555 supprimés :
  44 pour 10 000, contre 8,5 pour le reste de la base (4 035 sur 4 751 680). Leur âge se compte
  depuis la publication : un avis de 2023 réécrit en juillet 2026 est rangé dans les avis de
  plus d'un an aux points 2.1, 7 et 8.
- Courbe de survie : un avis publié le 4 août n'est vu qu'à partir du 11, à 7 jours. Les premiers
  jours de la courbe reposent sur les avis publiés pendant le suivi. Au 1er jour, 2 308 avis
  seulement sont observés.
- Les 4 chaînes sont repérées sur leur nom exact : une dizaine de succursales au nom suivi d'une
  ville restent dans le périmètre « sans enseignes ».
