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
| 3851964 | ChI... | 164... | Ci9... | FALSE     | null         | 5    | [texte de l'avis] | en       | 2026-08-04 16:57:08.179033 UTC | 2026-08-04 16:57:08.179033 UTC | ... | [nom] | ... | 12                    | 7                    | FALSE       | 3                 | 0        | null       | [réponse] | 2026-08-04 18:45:37 UTC | 2026-08-11 06:05:12 UTC | 2026-08-15 06:10:05 UTC | 2026-08-16 06:09:58 UTC |

Exemples d'un avis modifié (texte) :
| ID      | place_id | cid     | review_id                                                            | is_update | change_field | star | text                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                | language | created_at                     | updated_at                     | review_link                                                                                                                            | reviewer_name | reviewer_avatar                                                                                                                                                                                                                                | reviewer_review_count | reviewer_photo_count | local_guide | local_guide_level | n_photos | photo_urls | reply_text                                                                                                                                                                                                                                                                                                                           | reply_date              | first_seen_at           | last_seen_at            | deleted_detected_at     |     |
| ------- | -------- | ------- | -------------------------------------------------------------------- | --------- | ------------ | ---- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- | ------------------------------ | ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------- | ------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------- | -------------------- | ----------- | ----------------- | -------- | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------- | ----------------------- | ----------------------- | ----------------------- | --- |
| 4861065 | C...     | 1345... | Ci9... | TRUE      | text         | 5    | [texte modifié] | en       | 2026-06-28 17:12:21.085429 UTC | 2026-08-16 17:43:35.272280 UTC | ...                                                                                                                                    | [nom]       | ...                                                                                                                                                                                                                                            | 24                    | 3                    | TRUE        | 5                 | 0        | null       | [réponse] | 2026-07-01 18:22:12 UTC | 2026-08-17 06:27:07 UTC | 2026-08-22 06:24:47 UTC | 2026-08-23 06:28:05 UTC |
| 4701785 | C...     | 1345... | Ci9... | FALSE     | null         | 5    | [texte d'origine] | en       | 2026-06-28 17:12:21.085429 UTC | 2026-06-28 17:12:21.085429 UTC | ... | [nom]       |...  | 24                    | 3                    | TRUE        | 5                 | 0        | null       | [réponse] | 2026-07-01 18:22:12 UTC | 2026-08-11 06:19:03 UTC | 2026-08-16 06:25:29 UTC | null                    |

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

Sur les 225 757 avis du corpus de modélisation, suppressions pour 10 000 avis. Les enseignes
retirées sont les quatre chaînes antiparasitaires (services à domicile) et les deux salles de
sport espagnoles (sport et bien-être).

| Secteur | Avis | Suppressions | Pour 10 000 | Sans enseignes : avis | Suppressions | Pour 10 000 |
|---|---:|---:|---:|---:|---:|---:|
| Services à domicile | 42 640 | 1 189 | **279** | 28 000 | 497 | **178** |
| Sport et bien-être | 24 165 | 532 | 220 | 23 808 | 205 | 86 |
| Voyage | 14 881 | 129 | 87 | 14 881 | 129 | 87 |
| Automobile | 28 794 | 205 | 71 | 28 794 | 205 | 71 |
| Santé | 31 318 | 216 | 69 | 31 318 | 216 | 69 |
| Hôtellerie | 39 463 | 168 | 43 | 39 463 | 168 | 43 |
| Restauration | 44 496 | 156 | **35** | 44 496 | 156 | **35** |

**Un avis déposé chez un prestataire de services à domicile est supprimé 8 fois plus souvent
qu'un avis de restaurant, et 5 fois plus sans les quatre chaînes.** À note, auteur et date de
publication égaux, l'écart reste net aux États-Unis : ×3,2 par rapport à l'automobile.

Source : `logistic-regression-study/output-study/2026-09-17-sorties-07/07_croisements_tous*.csv`.
Les salles sont retirées par leur `cid`. Le script 07 les retire encore par leur nom, ce qui
écarte 90 avis de plus, sans aucune suppression : son fichier donne 23 718 avis pour le sport.

### La note supprimée n'est pas la même des deux côtés de l'Atlantique

Sur 10 000 avis de chaque groupe, combien ont disparu :

| Note | États-Unis | sans les chaînes | Europe | sans les salles |
|---|---:|---:|---:|---:|
| 1 étoile | 262 | 259 | 585 | 152 |
| 3 étoiles | 65 | 63 | 24 | 24 |
| 4 étoiles | 61 | 40 | 24 | 24 |
| **5 étoiles** | **145** | **97** | **36** | **36** |

**Aux États-Unis, un avis 5 étoiles est supprimé plus souvent qu'un avis 3 ou 4 étoiles**, avec
ou sans les chaînes. En Europe, l'avis 1 étoile domine, surtout à cause des deux salles de sport.

En volume, sur l'ensemble du panel, **71 % des avis supprimés portaient 5 étoiles** (1 850 sur
2 595) et 23 % portaient 1 étoile (607). Les suppressions ne visent donc pas principalement les
avis négatifs.

**Deux lectures à ne pas confondre.** « L'avis 1 étoile est supprimé 3,5 fois plus » compare deux
avis : 259 suppressions pour 10 000 avis 1 étoile aux États-Unis, contre 97 pour 10 000 avis
5 étoiles. La composition des suppressions est autre chose : hors chaînes, 80 % des avis
supprimés aux États-Unis portent 5 étoiles, parce que ces avis sont 85 % du corpus.

Source : `07_croisements_US*.csv`, `07_croisements_Europe*.csv`.

### Le profil de l'auteur compte

À date de publication, secteur et région comparables, sans les six enseignes (tout le panel) :

| Caractéristique de l'avis ou de son auteur | Risque | Avec les enseignes |
|---|---:|---:|
| Avis 1 étoile, comparé à 5 étoiles | ×3,6 | ×6,6 |
| Compte sans niveau Local Guide, comparé aux niveaux 1 à 3 | ×2,5 | ×2,4 |
| Avis déposé aux États-Unis | ×2,1 | ×2,0 |
| 4 avis du même auteur le même jour, comparé à 1 | ×4,3 | ×7,4 |
| Auteur à 100 photos, comparé à 0 | ×0,47 | ×0,47 |
| Auteur à 20 avis, comparé à 2 | ×0,76 | ×0,78 |

Le niveau Local Guide 4 et plus ne protège pas : à photos et nombre d'avis égaux, ces auteurs
sont supprimés autant que les niveaux 1 à 3, et plus en Europe.

Le compte sans niveau, les photos et le nombre d'avis de l'auteur ne bougent pas quand on retire
les enseignes. La note et la rafale en dépendent fortement.

Source : `07_coefficients_tous_sans_enseignes.csv` et `07_coefficients_tous.csv` ; synthèse
`logistic-regression-study/output-study/2026-09-17-synthese-07.md`.

### Dans les huit premiers jours de l'avis

Sur les avis publiés du 10 au 16 août, suivis jusqu'à leur 8e jour, sans les quatre chaînes :
l'avis 1 étoile est supprimé 3 fois plus souvent (États-Unis ×3,2, Europe ×3,0), l'auteur sans
niveau Local Guide 2 à 3 fois plus (×2,2 et ×2,9). En Europe, un avis avec du texte l'est 2 fois
plus qu'un avis sans texte.

Ces caractéristiques ne suffisent pas à repérer les avis supprimés : les 10 % d'avis jugés les
plus risqués contiennent 23 à 26 % des suppressions.

Source : `logistic-regression-study/output-study/2026-09-17-synthese-modele-A.md`.

### Répondre vite protège, sur les fiches qui répondent à tout

Avis publiés du 10 au 16 août, encore en ligne à la fin de leur 2e jour, sans les quatre chaînes.
On regarde s'ils ont déjà une réponse, puis s'ils disparaissent du 3e au 8e jour.

**Sur les fiches qui répondent à plus de 75 % de leurs avis, l'avis déjà répondu est supprimé
2,5 fois moins souvent : ×0,40 (entre ×0,25 et ×0,65).** Le résultat tient quel que soit le jour
où l'on regarde la réponse, du 1er au 6e jour (×0,32 à ×0,47).

Sur les fiches qui répondent à 25 à 75 % de leurs avis, l'avis répondu est plutôt **plus**
supprimé (×2,0 au 2e jour, sur 30 suppressions). Toutes fiches confondues, l'effet moyen vaut
×0,59.

Réserves. Avec les quatre chaînes, aucun effet n'est net. Le sens de la cause n'est pas établi :
le propriétaire peut laisser sans réponse un avis qu'il signale, ou répondre à un avis qu'il
conteste. Les données ne montrent ni les signalements ni le contenu des réponses.

Source : `logistic-regression-study/output-study/2026-09-17-synthese-08.md`.

### The Boxer Club en Espagne attaqué

Deux salles de sport espagnoles ont perdu **327 avis sur les 357** qu'elles avaient dans le
corpus, soit 92 %, presque tous notés 1 étoile. Les suppressions tombent entre 9 et 22 jours après
la publication, bien après le pic habituel du 7e jour (`sql/controle_D_delai_suppression_enseignes.bqsql`).
On pense à une attaque par faux avis suivie d'un nettoyage par Google, probablement à la demande
du propriétaire. C'est une hypothèse : les données ne montrent pas les signalements.

Elles représentent 13 % de toutes les suppressions du corpus. Tous les calculs sont donc faits
deux fois, avec et sans elles.

### Le poids des fiches espagnoles et parasitaires dans le panel

|Groupe|Fiches|Avis|Suppressions|Part du total|Taux|
|---|---|---|---|---|---|
|4 chaînes antiparasitaires US|88|14 640|692|**26,7 %**|4,73 %|
|2 salles de sport espagnoles|2|357|327|**12,6 %**|91,6 %|
|Tout le reste|8 115|210 760|1 576|60,7 %|0,75 %|

Enseignes repérées par la table `biz_surveillance` et, pour les salles, par leur `cid`. L'ancien
repérage par nom comptait 13 fiches « The Boxer Club », dont 11 sans aucune suppression.

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

1. **La date de publication entre systématiquement dans le modèle.** Depuis le 2026-09-17, sous
   la forme d'un oui / non : le 8e jour de l'avis tombe-t-il pendant le suivi (avis publiés du
   3 au 16 août) ? Sans elle, elle déteint sur toutes les autres caractéristiques : les avis
   récents sont 5 fois plus supprimés que les anciens.
2. **Aucune caractéristique mesurée après le moment qu'elle prétend expliquer.** Le délai avant
   suppression, par exemple, n'est connu que pour les avis déjà supprimés.
3. **Les avis d'une même fiche ne comptent pas comme des informations indépendantes.** Le panel
   a été tiré par groupe d'établissements, et les calculs en tiennent compte.
4. **Chaque résultat est produit deux fois**, avec et sans les six enseignes au comportement
   particulier — les deux boutiques espagnoles et quatre chaînes américaines.
5. **La qualité du modèle se mesure en cinq tours par établissement.** Chaque fiche est notée une
   fois par un modèle qui ne l'a jamais vue, et on regarde quelle part des suppressions tombe
   dans les 10 % d'avis jugés les plus risqués.

### La chaîne technique

| Étape | Fichier |
|---|---|
| Construire le corpus | `logistic-regression-study/sql/01_selection_panel.bqsql` |
| Calculer les caractéristiques (version d'origine) | `logistic-regression-study/sql/02_adding_features.bqsql` |
| Calculer les caractéristiques (palier Local Guide, photos, habitude de réponse) | `logistic-regression-study/sql/03_adding_features.bqsql` |
| Ajuster le modèle sur tout le panel | `logistic-regression-study/python/07_regression_panel.py` |
| Mesurer l'effet des réponses | `logistic-regression-study/python/08_effet_reponse_commercant.py` |
| Modèle des 8 premiers jours | `logistic-regression-study/python/10_modele_A_8_premiers_jours.py` |

Les tables vivent dans BigQuery : `reviews_panel_features` (02) et
`reviews_panel_features_03` (03), lue par les scripts 07, 08 et 10. Les sorties chiffrées sont dans
`logistic-regression-study/output-study/`.

**`sql/02_adding_features.bqsql` ne se modifie pas sans l'accord de Romain.** Le changer oblige à
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
   corpus, presque toutes sur des avis 4 et 5 étoiles. Les textes sont tous différents et il n'y a
   pas d'afflux soudain. Une piste : leurs textes citent très souvent un technicien par son
   prénom. Un fait nouveau : 44 avis de ces chaînes viennent d'auteurs qui ont publié 4 avis ou
   plus le même jour sur leurs succursales, et les 44 ont été supprimés. Ils ne font que 44 des
   692 suppressions des chaînes.
2. **Chercher d'autres attaques par faux avis** dans le panel. Deux ont été trouvées ; aucune
   recherche systématique n'a été faite.
3. **Comprendre ce qui se passe au septième jour.** C'est le motif le plus net de l'étude et il
   n'a pas d'explication.
4. **Comprendre pourquoi la réponse joue en sens opposés** selon l'habitude de réponse de la
   fiche. Il faudrait connaître le contenu des réponses ou les signalements.
5. **Construire le modèle des suppressions tardives**, après le 8e jour. Il n'a pas été fait.

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
