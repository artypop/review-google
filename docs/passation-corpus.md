# Passation : les deux corpus de l'étude des suppressions d'avis Google

Rédigé le 2026-10-12 pour reprendre le travail de Romain. Les résultats restitués au client sont dans
`Restitution.pdf`, transmis à part.

Toutes les tables sont dans BigQuery, projet `client-divers`, dataset `reviewflowz`.

---

## 1. D'où viennent les données

- **Le panel :** 9 048 fiches Google Maps tirées par région (US, Europe sans le Royaume-Uni),
  7 secteurs et 3 tailles de groupe : `mono` (1 établissement), `small` (4 à 10), `large` (20 à 50).
  Table `businesses`, une ligne par fiche, clé `cid`.
- **Le robot :** il a relevé tous les avis de chaque fiche une fois par jour, du 11 au 24 août 2026 :
  14 passages. **J = 11 août 2026, premier passage.** Table brute `reviews`.
- **Une suppression :** un avis que le robot ne retrouve plus à un passage. Colonne
  `deleted_detected_at`, remplie avec la date du premier passage où l'avis manque. Les premières
  suppressions sont constatées le 12 août (2e passage), les dernières le 24.
- **Ce qu'on ne voit pas :** un avis supprimé avant le 11 août n'est dans aucune table. Toute mesure
  sur des avis publiés avant le 11 août ne voit que ceux qui étaient encore en ligne ce jour-là.
- Heures en UTC. `created_at` = date de publication de l'avis.

### Les six enseignes signalées

Six enseignes concentrent des suppressions en masse : 4 chaînes antiparasitaires américaines et
2 salles de sport espagnoles du groupe The Boxer Club. Chaque résultat se donne avec et sans elles.

**Elles se repèrent par le nom dans `businesses`** (les 4 chaînes) **et par le `cid`** (les 2 salles).
C'est la définition de la restitution :

```sql
SELECT
  cid, name, country, industry, bucket,
  CASE
    WHEN LOWER(name) LIKE 'ecoshield pest solutions%' THEN 'EcoShield Pest Solutions'
    WHEN LOWER(name) LIKE 'insight pest solutions%'   THEN 'Insight Pest Solutions'
    WHEN LOWER(name) LIKE 'pointe pest control%'      THEN 'Pointe Pest Control'
    WHEN LOWER(name) LIKE 'bulwark exterminating%'    THEN 'Bulwark Exterminating'
    ELSE 'The Boxer Club'
  END AS enseigne,
  cid IN (SELECT cid FROM `client-divers.reviewflowz.biz_surveillance`) AS dans_biz_surveillance
FROM `client-divers.reviewflowz.businesses`
WHERE LOWER(name) LIKE 'ecoshield pest solutions%'
   OR LOWER(name) LIKE 'insight pest solutions%'
   OR LOWER(name) LIKE 'pointe pest control%'
   OR LOWER(name) LIKE 'bulwark exterminating%'
   OR cid IN ('3163466139043001754', '10346942689164695031')
ORDER BY enseigne, name;
```

Ce que donne cette liste dans `reviews_doublons_cleaned_all` (suppressions du 12 au 24 août, toutes
dates de publication) :

| Enseigne | Pays | Fiches | Avis | Avis supprimés | Avis 4-5★ | Avis 4-5★ supprimés |
|---|---|---:|---:|---:|---:|---:|
| EcoShield Pest Solutions | US | 35 | 166 162 | 538 | 156 680 | 508 |
| Bulwark Exterminating | US | 26 | 41 466 | 157 | 40 598 | 156 |
| Insight Pest Solutions | US | 21 | 23 676 | 351 | 22 979 | 343 |
| Pointe Pest Control | US | 20 | 57 591 | 192 | 56 710 | 192 |
| **4 chaînes** | US | **102** | 288 895 | 1 238 | 276 967 | 1 199 |
| The Boxer Club (2 fiches) | Espagne | 2 | 1 414 | 329 | 1 076 | 2 |
| **6 enseignes** | | **104** | 290 309 | 1 567 | 278 043 | 1 201 |

- Les 4 chaînes sont toutes en services à domicile, groupes `large` (20 à 50 établissements). Les
  2 salles sont en sport et bien-être, `large` aussi. Leurs cid : `10346942689164695031` (The Boxer
  Club) et `3163466139043001754` (Boutique The Boxer Club Dr Castelo).
- **Les 4 chaînes :** 1 238 des 4 590 suppressions de la base (27 %), presque toutes des avis 4-5★
  (1 199). Deux mouvements : des avis récents retirés environ 7 jours après leur publication, et des
  purges d'avis anciens les 12, 16 et 17 août.
- **Les 2 salles :** 329 suppressions, dont 317 sur leurs 328 avis 1 étoile, presque tous publiés du
  28 juillet au 5 août (297 avis publiés les 1er et 2 août, 295 supprimés), retirés surtout les 12 et
  16 août. Hors de cette attaque, ces fiches recevaient quelques avis par mois.
- **Dans le corpus 2** (avis publiés du 7 au 17 août), les 6 enseignes portent 1 815 avis 4-5★. La
  restitution passe de 24 191 à 22 378 avis en les retirant (1 813).

**Ne pas utiliser la table `biz_surveillance` comme liste des enseignes.** Elle ne contient que
95 de ces 104 fiches : il lui manque 8 succursales EcoShield dont le nom est suivi d'une ville
(« EcoShield Pest Solutions Houston »…) et « Bulwark Exterminating Corporate ». La colonne
`dans_biz_surveillance` de la requête les signale.

Exclure les enseignes dans une requête :

```sql
WITH enseignes AS (
  SELECT cid FROM `client-divers.reviewflowz.businesses`
  WHERE LOWER(name) LIKE 'ecoshield pest solutions%'
     OR LOWER(name) LIKE 'insight pest solutions%'
     OR LOWER(name) LIKE 'pointe pest control%'
     OR LOWER(name) LIKE 'bulwark exterminating%'
     OR cid IN ('3163466139043001754', '10346942689164695031')
)
SELECT ...
FROM `client-divers.reviewflowz.reviews_doublons_cleaned_all` r
WHERE r.cid NOT IN (SELECT cid FROM enseignes)
```

---

## 2. Corpus 1 : `reviews_doublons_cleaned_all` (la base complète)

**Contenu :** 4 876 933 avis de 8 997 fiches (51 fiches n'ont aucun avis), publiés du
30/09/2004 au 24/08/2026, dont **4 590 supprimés** pendant le suivi. Une ligne par avis
(`review_id`). Mêmes colonnes que `reviews`.

**Construction :**

| Étape | Avis | Avis supprimés |
|---|---:|---:|
| 1. table brute `reviews`, 4 880 163 lignes | 4 877 534 | 5 192 |
| 2. une ligne par avis : la plus récemment modifiée, puis la plus récemment vue | 4 877 534 | 4 697 |
| 3. sans les avis qui ont disparu puis sont revenus | 4 876 933 | 4 590 |

- **Étape 2 :** un avis modifié par son auteur, ou disparu puis revenu, a plusieurs lignes dans
  `reviews`. On en garde une. 495 avis avaient une ligne marquée disparue alors que leur dernière
  version est en ligne.
- **Étape 3 :** un avis à plusieurs lignes n'est gardé que si sa dernière ligne est une modification
  de l'auteur (`is_update`). Les 601 autres ont disparu puis sont revenus : la plupart sont des
  ratés du robot (absents un seul jour). Ils sortent, avec leurs 107 suppressions.
- **Avis modifiés gardés.** Depuis le 2026-09-30, la base garde aussi les avis modifiés plus d'un an
  après leur publication (125 253 avis, 555 suppressions). L'ancienne table
  `reviews_doublons_cleaned` les excluait : ne plus l'utiliser.
- **Décision de Romain du 2026-10-08 :** on reste sur cette base nettoyée, même quand nos chiffres
  divergent de ceux d'Axel (le client), qui travaille sur la table brute `reviews` sans les avis
  modifiés (5 230 disparitions). Exemple : avec son seuil de plus de 10 suppressions en 14 jours, il
  compte 111 fiches très touchées, la base nettoyée 97. 7 de ses 111 fiches sont de petites fiches
  européennes dont les « suppressions » sont des doublons d'enregistrement.

**Colonnes utiles :**

- l'avis : `review_id`, `cid`, `star`, `text`, `language`, `n_photos`, `created_at`, `updated_at`,
  `is_update` ;
- l'auteur : `reviewer_review_count`, `reviewer_photo_count`, `local_guide`, `local_guide_level` ;
  `reviewer_name`, `review_link` et `reviewer_avatar` sont des données personnelles, à ne jamais
  recopier dans un livrable ;
- la réponse du propriétaire : `reply_text`, `reply_date` (écrasée en place : une réponse retirée
  ne laisse aucune trace) ;
- le suivi : `first_seen_at`, `last_seen_at`, `deleted_detected_at`.

**Pièges :**

- La ligne gardée d'un avis modifié porte le `first_seen_at` de la modification. Pour le premier jour
  où l'avis a été vu, prendre `MIN(first_seen_at)` dans `reviews` par `review_id`.
- Les 4 590 suppressions portent sur des avis de toutes dates de publication. 56 % concernent des
  avis publiés en juillet-août 2026 (2 579).

---

## 3. Corpus 2 : `03C_7_17_aout_prenom` (les nouveaux avis, avec le prénom)

**Contenu :** les 27 828 avis de la base complète publiés (`created_at`) **du 7 au 17 août 2026**,
dont 1 081 supprimés. Avis 4 et 5 étoiles : 24 248, dont 905 supprimés. C'est un sous-ensemble
exact de `reviews_doublons_cleaned_all` (contrôlé : aucun avis absent de la base, aucun doublon).
Mêmes colonnes, plus deux :

| Colonne | Contenu |
|---|---|
| `prenom` | l'avis cite un nom de personne (vrai / faux) |
| `prenom_source` | d'où vient la valeur, voir ci-dessous |

| `prenom_source` | Avis | Dont `prenom` vrai | Sens |
|---|---:|---:|---|
| `axel` | 17 180 | 6 826 | avis 4-5 étoiles avec texte, annotation d'Axel |
| `axel_texte_modifie` | 97 | 38 | annotation d'Axel, sur un texte modifié depuis |
| `sans_texte` | 6 916 | 0 | avis 4-5 étoiles sans texte |
| `introuvable` | 55 | 0 | avis 4-5 étoiles absents de l'annotation d'Axel |
| `hors_annotation` | 3 580 | 0 | avis 1 à 3 étoiles, non annotés |

- **L'annotation vient d'Axel**, table `reviews_name_enriched` (2 675 861 lignes, 2 675 519 avis
  4 et 5 étoiles avec texte, colonne `has_name`), jointe par `review_id`. Son modèle (GLiNER) manque
  environ 7 % des noms et en invente 0,7 % selon son test, jugé par des IA.
- **`prenom` = faux ne veut pas toujours dire « pas de prénom »** : pour `sans_texte`,
  `introuvable` et `hors_annotation`, l'information manque. Pour une analyse des prénoms, filtrer
  `prenom_source IN ("axel", "axel_texte_modifie")`.
- La même table sans les deux colonnes existe : `03C_7_17_aout`.
- Pour refaire ces tables : avis de `reviews_doublons_cleaned_all` avec
  `DATE(created_at) BETWEEN "2026-08-07" AND "2026-08-17"`, joints à `reviews_name_enriched` par
  `review_id`.

### Pourquoi le corpus s'arrête aux avis publiés le 17 août

- Les suppressions d'avis neufs se concentrent aux **6e et 7e jours** après la publication : la
  moitié des avis 4-5 étoiles supprimés dans leurs 13 premiers jours le sont ces deux jours-là
  (641 sur 1 272, graphique 1.1 de la restitution).
- Le robot passe pour la dernière fois le **24 août**. Un avis publié le 17 août est donc suivi
  jusqu'à son 7e jour ; un avis publié le 18 août ne serait suivi que 6 jours et manquerait le pic.
- Arrêter au 17 garantit que **chaque avis du corpus est suivi au moins jusqu'à son 7e jour**. Les
  analyses sur ce corpus comptent les avis supprimés « au plus tard à leur 7e jour », ce qui met tous
  les avis à égalité.
- Avec des avis publiés jusqu'au 24, les plus récents compteraient comme « non supprimés » faute de
  temps d'observation, et le taux de suppression serait sous-estimé.

### Pourquoi il commence aux avis publiés le 7 août

- Un avis publié le 7 août a 4 jours au premier passage du robot (11 août). Le premier jour où une
  suppression peut être constatée, le 12 août, est son 5e jour. Ses 6e et 7e jours (13 et 14 août)
  sont donc observés.
- Le 7 août est la date la plus ancienne qui garde l'observation à partir du 5e jour de vie, avant
  le pic des 6e et 7e jours.
- Ce qu'on perd : une suppression faite au 1er, 2e ou 3e jour d'un avis publié du 7 au 10 août n'est
  pas vue. Ces premiers jours pèsent peu : 1,9 et 2,5 avis supprimés pour 1 000 aux 1er et 2e jours,
  contre 18,6 au 7e (graphique 1.1).

**Ne pas prendre d'avis publiés avant le 7 août.** Un avis supprimé avant le premier passage du
robot n'est dans aucune table : on ne voit que les avis qui ont survécu jusqu'au 11 août.

- Exemple : deux avis publiés le 4 août. Le premier est supprimé à son 6e jour, le 10 août. Le
  robot ne l'a jamais vu : il n'est pas dans la base. Le second est encore en ligne le 11 août : il y
  est, et compte comme un avis « qui a passé ses 6e et 7e jours sans être supprimé ».
- Un avis publié le 5 août a son 6e jour le 11 août : une suppression ce jour-là a lieu avant ou au
  premier passage, elle n'est pas vue. Dès le 5 août, une partie du pic manque.
- Plus on remonte dans le temps, plus le pic des 6e et 7e jours tombe avant le premier passage :
  les avis supprimés disparaissent du calcul, les survivants restent, et le taux de suppression est
  sous-estimé sans qu'on puisse le corriger.
- Un avis publié le 6 août a encore ses 6e et 7e jours observés (12 et 13 août), mais de justesse.
  À partir du 7 août, on observe l'avis dès son 5e jour, avec un jour de marge avant le pic.
