# Suppressions d'avis Google — le projet en une lecture

---

## 1. Ce qu'on cherche

Google supprime une partie des avis déposés sur les fiches Google Maps. Les commerçants le
constatent sans comprendre ce qui déclenche ces retraits.

**L'étude cherche à déterminer quelles caractéristiques d'un avis font qu'il est supprimé.**
La note, la longueur du texte, le profil de l'auteur, le secteur du commerce, le moment du
dépôt : lesquelles pèsent, et de combien.

Commanditaire : Axel, dirigeant de ReviewFlowz, un outil de gestion d'avis clients.

---

## 2. Les données

Un robot a suivi **9 048 établissements Google Maps pendant quatorze jours**, du 11 au 24 août
2026. Chaque jour, il relève la totalité des avis de chaque fiche. Au total **4,88 millions
d'avis** qui s'étendent de 2004 au 24 août 2026.

Le panel couvre sept secteurs, deux régions — États-Unis et Europe hors Royaume-Uni — et trois
tailles d'entreprise : une entreprise unique, un groupe de 4 à 10 entreprises, de 20 à 50 entreprises. Il a été construit pour que chaque combinaison soit représentée, avec environ 420 fiches par case.

**Un avis présent un jour et absent le lendemain est compté comme supprimé.**

Les fichiers d'origine contiennent le nom de l'auteur, le lien vers son profil et le texte des
avis. Ils ne sont pas versionnés.

Exemples d'un avis unique :

| ID      | place_id                    | cid                  | review_id                                                            | is_update | change_field | star | text                                          | language | created_at                     | updated_at                     | review_link                                                                                                                            | reviewer_name       | reviewer_avatar                                                                                                                                                                                                                          | reviewer_review_count | reviewer_photo_count | local_guide | local_guide_level | n_photos | photo_urls | reply_text                                                                                                                                                                                                                                                                                                                   | reply_date              | first_seen_at           | last_seen_at            | deleted_detected_at     |
| ------- | --------------------------- | -------------------- | -------------------------------------------------------------------- | --------- | ------------ | ---- | --------------------------------------------- | -------- | ------------------------------ | ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------- | ------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------- | -------------------- | ----------- | ----------------- | -------- | ---------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------- | ----------------------- | ----------------------- | ----------------------- |
| 3851964 | ChI... | 164... | Ci9... | FALSE     | null         | 5    | Nice work always consistent and professional! | en       | 2026-08-04 16:57:08.179033 UTC | 2026-08-04 16:57:08.179033 UTC | ... | Stephanie Shoemaker | ... | 12                    | 7                    | FALSE       | 3                 | 0        | null       | Hello Stephanie! Thank you for your five-star rating of our services... | 2026-08-04 18:45:37 UTC | 2026-08-11 06:05:12 UTC | 2026-08-15 06:10:05 UTC | 2026-08-16 06:09:58 UTC |

Exemples d'un avis modifié (texte) :
| ID      | place_id | cid     | review_id                                                            | is_update | change_field | star | text                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                | language | created_at                     | updated_at                     | review_link                                                                                                                            | reviewer_name | reviewer_avatar                                                                                                                                                                                                                                | reviewer_review_count | reviewer_photo_count | local_guide | local_guide_level | n_photos | photo_urls | reply_text                                                                                                                                                                                                                                                                                                                           | reply_date              | first_seen_at           | last_seen_at            | deleted_detected_at     |     |
| ------- | -------- | ------- | -------------------------------------------------------------------- | --------- | ------------ | ---- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- | ------------------------------ | ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------- | ------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------- | -------------------- | ----------- | ----------------- | -------- | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------- | ----------------------- | ----------------------- | ----------------------- | --- |
| 4861065 | C...     | 1345... | Ci9... | TRUE      | text         | 5    | A big shout out to my new facial... | en       | 2026-06-28 17:12:21.085429 UTC | 2026-08-16 17:43:35.272280 UTC | ...                                                                                                                                    | Adriana Peri  | ...                                                                                                                                                                                                                                            | 24                    | 3                    | TRUE        | 5                 | 0        | null       | Hi Adriana... | 2026-07-01 18:22:12 UTC | 2026-08-17 06:27:07 UTC | 2026-08-22 06:24:47 UTC | 2026-08-23 06:28:05 UTC |
| 4701785 | C...     | 1345... | Ci9... | FALSE     | null         | 5    | A big shout out to my new facial guru..      | en       | 2026-06-28 17:12:21.085429 UTC | 2026-06-28 17:12:21.085429 UTC | ... | Adriana Peri  |...  | 24                    | 3                    | TRUE        | 5                 | 0        | null       | Hi Adriana,.... | 2026-07-01 18:22:12 UTC | 2026-08-11 06:19:03 UTC | 2026-08-16 06:25:29 UTC | null                    |

---

## 3. Ce qu'on a trouvé

### Un avis supprimé l'est presque toujours avant le huitième jour

Sur les avis déposés pendant la première semaine de suivi, **695 ont été supprimés. 311 d'entre
eux l'ont été exactement sept jours après leur publication.**

| Délai avant suppression | Suppressions | Part |
|---|---:|---:|
| 1 à 5 jours | 129 | 18,6 % |
| **6 jours** | **167** | **24,0 %** |
| **7 jours** | **311** | **44,7 %** |
| 8 jours et plus | 88 | 12,7 % |

**Sept suppressions sur dix tombent au sixième ou au septième jour.** Le motif se répète pour
chaque journée de dépôt, du 11 au 17 août, ce qui écarte l'hypothèse d'un événement isolé.

Sur cette semaine, 17 659 avis ont été déposés et 695 supprimés : **3,9 %**.

Ce délai régulier oriente vers un traitement automatique déclenché à date fixe. Les données ne
permettent pas de le confirmer.

### Le risque s'effondre ensuite

Passé les premiers jours, un avis ne risque presque plus rien. Entre un avis du jour et un avis
de trois mois, **le risque est divisé par 21**.

C'est de loin le facteur le plus puissant de l'étude, et il oblige à comparer des avis de même
âge. Deux groupes d'avis d'âges différents auront toujours des taux de suppression très
différents, quelles que soient leurs autres caractéristiques.

### Le secteur pèse lourd

Sur les 225 757 avis du corpus de modélisation :

| Secteur | Avis | Supprimés | Taux |
|---|---:|---:|---:|
| Services à domicile | 42 640 | 1 189 | **2,79 %** |
| Voyage | 14 881 | 129 | 0,87 % |
| Sport et bien-être | 23 808 | 205 | 0,86 % |
| Automobile | 28 794 | 205 | 0,71 % |
| Santé | 31 318 | 216 | 0,69 % |
| Hôtellerie | 39 463 | 168 | 0,43 % |
| Restauration | 44 496 | 156 | **0,35 %** |

**Un avis déposé chez un artisan ou un prestataire à domicile a huit fois plus de chances d'être
supprimé qu'un avis de restaurant.**

### La note supprimée n'est pas la même des deux côtés de l'Atlantique

Sur 10 000 avis de chaque groupe, combien ont disparu :

| Note | États-Unis | Europe |
|---|---:|---:|
| 1 étoile | 262 | 585 |
| 3 étoiles | 65 | 24 |
| 4 étoiles | 61 | 24 |
| **5 étoiles** | **145** | **36** |

**Aux États-Unis, un avis 5 étoiles est supprimé plus souvent qu'un avis 3 ou 4 étoiles.** En
Europe, l'avis 1 étoile domine largement.

En volume, sur l'ensemble du panel, **71 % des avis supprimés portaient 5 étoiles**. Les
suppressions ne visent donc pas principalement les avis négatifs.

### Le profil de l'auteur compte

À âge, secteur et région comparables :

| Caractéristique de l'avis ou de son auteur | Risque |
|---|---:|
| Compte sans niveau Local Guide | ×2,5 |
| Avis déposé aux États-Unis | ×2,1 |
| Avis 1 étoile, comparé à 5 étoiles | ×3,6 |
| Plusieurs avis du même auteur le même jour | ×5,3 |

Le compte sans niveau Local Guide est le seul de ces effets qui se renforce quand on retire les
enseignes au comportement particulier. Les autres en dépendent davantage.

### Répondre vite divise le risque par deux

Parmi les avis encore en ligne à la fin de leur deuxième jour, **ceux dont le commerçant avait
déjà répondu ont été supprimés 1,8 fois moins souvent** dans les six jours suivants :
risque ×0,56, fourchette [0,37 – 0,85].

Le résultat tient quand on déplace le moment de l'observation : ×0,59 au premier jour, ×0,56 au
deuxième, ×0,46 au troisième, ×0,48 au quatrième.

Deux réserves. L'effet disparaît quand on inclut quatre chaînes américaines de traitement
antiparasitaire, qui portent 37 % des suppressions de cette population et dont les suppressions
restent inexpliquées. Et le sens de la cause n'est pas établi : un commerçant qui répond en deux
jours est aussi un commerçant qui surveille sa fiche et signale les avis qu'il juge illégitimes.

### The Boxer Club en Espagne attaqué

Deux salles de sport espagnoles ont perdu **327 avis sur les 357** qu'elles avaient dans le
corpus, soit 92 %, presque tous notés 1 étoile et déposés en quelques jours. On pense à une attaque
par faux avis suivie d'un nettoyage par Google (probablement à la demande du propriétaire, car les suppressions arrivent ).

Elles représentent 13 % de toutes les suppressions du corpus. Tous les calculs sont donc faits
deux fois, avec et sans elles.

### Le poids des fiches espagnoles et parasitaires dans le panel

|Groupe|Fiches|Avis|Suppressions|Part du total|Taux|
|---|---|---|---|---|---|
|4 chaînes antiparasitaires US|88|14 640|692|**26,7 %**|4,73 %|
|2 salles de sport espagnoles|13|447|327|**12,6 %**|73,15 %|
|Tout le reste|8 104|210 670|1 576|60,7 %|0,75 %|

---

## 4. Comment on a fait

### Le corpus de modélisation

**225 757 avis publiés entre le 13 mai et le 16 août 2026**, sur 8 205 fiches, dont 2 595
supprimés — 1,15 %.

Les deux bornes répondent chacune à une contrainte :

- **90 jours avant le début du suivi.** Au-delà, un avis ne risque plus assez pour apporter de
  l'information.
- **Le 16 août.** Un avis déposé ce jour-là est encore observé pendant huit jours avant la fin
  du suivi, ce qui laisse le temps de voir s'il est supprimé.

Le corpus contient deux populations distinctes. **210 509 avis étaient déjà en ligne au premier
passage** : on ne connaît pas leurs premiers jours. **15 248 ont été publiés pendant le suivi** :
on les a vus naître. C'est sur ces derniers que repose la mesure de l'effet des réponses.

### Le modèle

Une régression logistique : pour chaque avis, on cherche ce qui fait varier sa probabilité
d'être supprimé, toutes les autres caractéristiques étant tenues constantes.

Les résultats se lisent en risque relatif. « ×2 » signifie deux fois plus supprimé qu'un avis
identique par ailleurs. Les crochets donnent la marge d'incertitude ; quand elle contient 1,
aucun écart n'est mesurable.

Quatre précautions gouvernent la construction :

1. **L'âge entre systématiquement dans le modèle.** Sans lui, il déteint sur toutes les autres
   caractéristiques. Un avis qui porte une réponse est en général un avis ancien, et un avis
   ancien ne risque presque plus rien : sans correction, on conclurait que les réponses
   protègent alors qu'on mesure de l'âge.
2. **Aucune caractéristique mesurée après le moment qu'elle prétend expliquer.** Le délai avant
   suppression, par exemple, n'est connu que pour les avis déjà supprimés.
3. **Les avis d'une même fiche ne comptent pas comme des informations indépendantes.** Le panel
   a été tiré par groupe d'établissements, et les calculs en tiennent compte.
4. **Chaque résultat est produit deux fois**, avec et sans les six enseignes au comportement
   particulier — les deux boutiques espagnoles et quatre chaînes américaines.

### La chaîne technique

| Étape | Fichier |
|---|---|
| Construire le corpus | `logistic-regression-study/sql/01_selection_panel.sql` |
| Calculer les 42 caractéristiques | `logistic-regression-study/sql/02_adding_features.sql` |
| Ajuster le modèle | `logistic-regression-study/python/07_regression_panel.py` |
| Mesurer l'effet des réponses | `logistic-regression-study/python/08_effet_reponse_commercant.py` |

Les deux tables vivent dans BigQuery. Les sorties chiffrées sont dans
`logistic-regression-study/output-study/`.

**`sql/02_adding_features.sql` ne se modifie pas sans l'accord de Romain.** Le changer oblige à
reconstruire la table et à relancer tous les modèles.

---

## 5. Ce que l'étude ne peut pas dire

**On ne voit que les avis publiés.** Les avis bloqués avant mise en ligne sont invisibles. Aucun
avis contenant un lien n'a été supprimé pendant le suivi, alors qu'il en existe dans le panel :
ce filtrage-là se fait en amont.

**On ne sait pas distinguer un faux avis d'une erreur de modération.** L'étude montre que la
plupart des avis supprimés ne contiennent aucune faute visible — ni insulte, ni spam, ni
charabia. Elle ne prouve pas qu'ils sont authentiques.

**On ne connaît pas la cause d'une suppression.** Traitement automatique, signalement du
commerçant, contestation d'un tiers : rien dans les données ne permet de trancher.

**La fenêtre est de quatorze jours.** Les suppressions rapides sont visibles. Une révision à six
mois ne l'est pas.

**Le panel ne couvre pas tout** : 41 pays dont un seul hors d'Europe, sans le Royaume-Uni, et
sans les groupes de 2 à 3 ni de 11 à 19 établissements.

---

## 6. Ce qui reste ouvert

1. **Quatre chaînes américaines de traitement antiparasitaire** portent 27 % des suppressions du
   corpus, presque toutes sur des avis 4 et 5 étoiles. Aucune caractéristique disponible ne les
   explique : les auteurs sont ordinaires, les textes tous différents, il n'y a pas d'afflux
   soudain. Une piste : leurs textes citent très souvent un technicien par son prénom.
2. **Chercher d'autres attaques par faux avis** dans le panel. Deux ont été trouvées ; aucune
   recherche systématique n'a été faite.
3. **Comprendre ce qui se passe au septième jour.** C'est le motif le plus net de l'étude et il
   n'a pas d'explication.
4. **Améliorer la mesure de qualité du modèle.** La méthode actuelle met de côté un quart des
   établissements une seule fois. En Europe, ce tirage est tombé sur des fiches deux fois moins
   touchées que la moyenne, ce qui rend les niveaux de risque qu'il annonce inutilisables.

---

## 7. Pour aller plus loin

| | |
|---|---|
| `docs/01-etude.md` | le corpus et les choix de modélisation en détail |
| `docs/02-donnees.md` | les définitions et les pièges du jeu de données |
| `docs/03-resultats.md` | tous les résultats, avec leurs fourchettes et réserves |
| `docs/04-enseignements.md` | les contrôles à passer avant de publier un chiffre |
| `docs/BACKLOG.md` | l'état d'avancement |
| `logistic-regression-study/output-study/` | les sorties chiffrées et les notes qui les commentent |
