# refacto_2 — panel 03D

Travail du 2026-09-30. Question : quelles caractéristiques d'un avis font qu'il est supprimé ?

**Panel :** 30 628 avis publiés du 6 au 17 août 2026, suivis jusqu'au 24 août, dont 1 191
supprimés, sur 5 281 fiches. Source : table BigQuery `dataset_reg`, tirée de la base complète
`reviews_doublons_cleaned_all`.

---

## Les fichiers

| Fichier | Ce qu'il fait | Sorties |
|---|---|---|
| [03D_adding_features.bqsql](03D_adding_features.bqsql) | construit la table `reviews_panel_features_03D`, une ligne par avis | table BigQuery |
| [03D_regression_logistique.py](03D_regression_logistique.py) | effet de chaque caractéristique, les autres tenues égales, 5 passages | [03D_effets.csv](sorties/03D_effets.csv), [03D_effectifs.csv](sorties/03D_effectifs.csv), [03D_effets.png](sorties/figures/03D_effets.png), [03D_effets_US.png](sorties/figures/03D_effets_US.png), [03D_effets_EU.png](sorties/figures/03D_effets_EU.png) |
| [03D_grilles.py](03D_grilles.py) | suppressions pour 1 000 avis, en grilles croisées | voir la section « Grilles » |
| [03D_reponse_par_secteur.py](03D_reponse_par_secteur.py) | effet de la réponse du propriétaire, par secteur et par note | [03D_reponse_par_secteur.csv](sorties/03D_reponse_par_secteur.csv), [03D_reponse_par_note.csv](sorties/03D_reponse_par_note.csv), 4 graphiques |
| [03D_courbe_de_vie.py](03D_courbe_de_vie.py) | part des avis encore en ligne sur leurs 21 premiers jours, US et Europe, avis de J-7 à J+14, base complète | [03D_courbe_de_vie.csv](sorties/03D_courbe_de_vie.csv), [03D_courbe_de_vie.png](sorties/figures/03D_courbe_de_vie.png) |
| [03D_courbe_de_vie_groupe_fixe.py](03D_courbe_de_vie_groupe_fixe.py) | la même courbe sur un groupe d'avis fixe (publiés du 10 au 17 août), et une courbe par date de publication | [03D_courbe_de_vie_groupe_fixe.csv](sorties/03D_courbe_de_vie_groupe_fixe.csv), [03D_courbe_de_vie_groupe_fixe.png](sorties/figures/03D_courbe_de_vie_groupe_fixe.png), [_A.png](sorties/figures/03D_courbe_de_vie_groupe_fixe_A.png), [_B.png](sorties/figures/03D_courbe_de_vie_groupe_fixe_B.png), [_B.csv](sorties/03D_courbe_de_vie_groupe_fixe_B.csv), [03D_courbe_de_vie_par_date.png](sorties/figures/03D_courbe_de_vie_par_date.png) |
| [03D_google_supprime_peu.py](03D_google_supprime_peu.py) | suppressions des avis publiés de 2004 à 2025, par année, et des avis publiés pendant le suivi, par âge ; tous pays | [03D_supprime_peu_anciens.csv](sorties/03D_supprime_peu_anciens.csv), [03D_supprime_peu_anciens.png](sorties/figures/03D_supprime_peu_anciens.png), [03D_supprime_peu_2026.csv](sorties/03D_supprime_peu_2026.csv), [03D_supprime_peu_2026.png](sorties/figures/03D_supprime_peu_2026.png), [03D_supprime_peu_recents.csv](sorties/03D_supprime_peu_recents.csv), [03D_supprime_peu_recents.png](sorties/figures/03D_supprime_peu_recents.png) |
| [sql/03D_avis_sans_rythme.sql](sql/03D_avis_sans_rythme.sql) | les 18 avis dont la fiche n'a reçu aucun avis l'année d'avant | [03D_avis_sans_rythme.csv](sorties/03D_avis_sans_rythme.csv) |

Pour tout refaire (environ une minute) :

```
bq query --use_legacy_sql=false < logistic-regression-study/refacto_2/03D_adding_features.bqsql
uv run python logistic-regression-study/refacto_2/03D_regression_logistique.py
uv run python logistic-regression-study/refacto_2/03D_grilles.py
uv run python logistic-regression-study/refacto_2/03D_reponse_par_secteur.py
uv run python logistic-regression-study/refacto_2/03D_courbe_de_vie.py
uv run python logistic-regression-study/refacto_2/03D_courbe_de_vie_groupe_fixe.py
uv run python logistic-regression-study/refacto_2/03D_google_supprime_peu.py
```

### Les colonnes de la table

| Colonne | Définition |
|---|---|
| `star` | note, 1 à 5 étoiles |
| `has_photo` | photo jointe à l'avis |
| `text_chars` | longueur du texte, 0 sans texte |
| `palier_local_guide` | sans niveau / 1 à 4 / 5 et plus |
| `reviewer_photo_count` | photos publiées par l'auteur, vide mis à 0 |
| `reviewer_review_count` | avis publiés par l'auteur |
| `a_repondu` | le propriétaire a répondu, lu au dernier passage du robot |
| `taux_reponse_fiche` | part des avis de la fiche qui ont une réponse, sur toute la base |
| `secteur`, `bucket`, `region` | secteur, taille (mono / small / large), US ou EU |
| `enseigne_signalee` | fiche de `biz_surveillance` : les 4 chaînes antiparasitaires américaines et les 2 salles espagnoles |
| `n_avis_meme_jour_fiche`, `rythme_fiche`, `ratio_pic_fiche` | avis reçus par la fiche le jour du dépôt, face à sa moyenne par jour du 06/08/2025 au 05/08/2026 |

### Les découpages de la régression

| Caractéristique | Référence | Autres cases |
|---|---|---|
| note | 3 étoiles | 1, 2, 4, 5 étoiles |
| pic sur la fiche le jour du dépôt | pas de pic | pic : au moins 2 avis ce jour-là et plus de 3 fois le rythme habituel |
| niveau Local Guide | sans niveau | 1 à 4 ; 5 et plus |
| photo dans l'avis | sans photo | avec photo |
| texte | sans texte | 1 à 50 ; 51 à 200 ; plus de 200 caractères |
| photos publiées par l'auteur | 0 | 1 à 20 ; plus de 20 |
| avis publiés par l'auteur | 1 ou moins | 2 à 20 ; plus de 20 |
| réponse du propriétaire | n'a pas répondu | a répondu |
| secteur | automobile | les 6 autres |
| taille | mono | small ; large |
| taux de réponse de la fiche | taux médian des avis du panel, 47 % | effet pour 10 points de plus |
| région (passages « ensemble ») | Europe | États-Unis |

Passages : US, US sans les chaînes, EU, ensemble, ensemble sans les chaînes. L'Europe n'a aucune
fiche signalée dans ce panel.

---

## Résultats

### La régression, toutes caractéristiques égales

Source : [03D_effets.csv](sorties/03D_effets.csv), graphique [03D_effets.png](sorties/figures/03D_effets.png).
« ×0,46 » : l'avis de cette case disparaît 0,46 fois autant que l'avis de la référence.

| Case | Ensemble, toutes les fiches | Ensemble, sans les chaînes |
|---|---|---|
| 1 étoile (face à 3) | ×5,09 [2,61 à 9,94] | ×5,56 [2,75 à 11,24] |
| 2 étoiles | ×2,71 [1,32 à 5,60] | ×2,74 [1,30 à 5,77] |
| pic le jour du dépôt | ×1,87 [1,45 à 2,41] | ×1,67 [1,27 à 2,18] |
| Local Guide 1 à 4 (face à sans niveau) | ×0,57 [0,46 à 0,71] | ×0,47 [0,37 à 0,61] |
| Local Guide 5 et plus | ×0,39 [0,20 à 0,74] | ×0,31 [0,16 à 0,57] |
| auteur à plus de 20 photos | ×0,48 [0,30 à 0,76] | ×0,56 [0,34 à 0,93] |
| le propriétaire a répondu | ×0,46 [0,34 à 0,63] | ×0,32 [0,22 à 0,46] |
| services à domicile (face à automobile) | ×4,78 [2,82 à 8,10] | ×2,43 [1,33 à 4,44] |
| taille large (face à mono) | ×1,74 [1,04 à 2,93] | ×1,13 [0,66 à 1,94] |
| États-Unis (face à Europe) | ×2,10 [1,42 à 3,08] | ×1,80 [1,20 à 2,71] |

- **Aucun effet visible**, fourchettes qui contiennent 1 :
  - 4 et 5 étoiles face à 3 étoiles ;
  - photo dans l'avis ;
  - avis publiés par l'auteur ;
  - taux de réponse de la fiche ;
  - santé, sport, restauration, voyage, hôtellerie face à l'automobile.
- **Longueur du texte :** aucun effet sur toutes les fiches. Sans les chaînes, plus de 200 caractères donne ×1,42 [1,04 à 1,93].
- **Europe :** le texte y joue, de ×1,77 à ×1,93 face à l'avis sans texte. Seuls les avis de 51 à 200 caractères et de plus de 200 ont une fourchette au-dessus de 1.
- **Réponse du propriétaire selon la région :**
  - Europe : ×0,30 ;
  - États-Unis : ×0,51 ;
  - États-Unis sans les chaînes : ×0,33.

### Europe et États-Unis séparés, toutes les fiches

Source : [03D_effets.csv](sorties/03D_effets.csv), passages « US, tous » et « EU, tous ».
Graphiques : [États-Unis](sorties/figures/03D_effets_US.png) (17 104 avis, 940 suppressions,
chaînes comprises), [Europe](sorties/figures/03D_effets_EU.png) (13 524 avis, 251 suppressions).

| Case | États-Unis | Europe |
|---|---|---|
| 1 étoile (face à 3) | ×5,20 [1,85 à 14,57] | ×5,72 [2,32 à 14,11] |
| 2 étoiles | ×3,28 [0,93 à 11,57] | ×2,36 [1,01 à 5,54] |
| pic le jour du dépôt | ×1,84 [1,36 à 2,50] | ×1,89 [1,17 à 3,05] |
| Local Guide 1 à 4 | ×0,67 [0,52 à 0,85] | ×0,36 [0,24 à 0,54] |
| Local Guide 5 et plus | ×0,48 [0,21 à 1,12] | ×0,24 [0,09 à 0,66] |
| texte de 51 à 200 caractères | ×0,86 [0,66 à 1,13] | ×1,90 [1,07 à 3,38] |
| texte de plus de 200 caractères | ×1,03 [0,74 à 1,43] | ×1,93 [1,11 à 3,34] |
| auteur à plus de 20 photos | ×0,29 [0,14 à 0,60] | ×0,85 [0,40 à 1,82] |
| le propriétaire a répondu | ×0,51 [0,36 à 0,74] | ×0,30 [0,15 à 0,60] |
| services à domicile (face à automobile) | ×5,40 [2,96 à 9,84] | ×1,59 [0,46 à 5,48] |
| taille small (face à mono) | ×2,62 [1,44 à 4,77] | ×0,93 [0,36 à 2,39] |
| taille large | ×2,65 [1,58 à 4,42] | ×0,75 [0,32 à 1,78] |

- **Communs aux deux régions :** 1 étoile, pic le jour du dépôt, Local Guide 1 à 4, réponse du propriétaire.
- **Propres aux États-Unis :** services à domicile, taille small et large, auteur à plus de 20 photos.
  Les 4 chaînes sont toutes aux États-Unis, en services à domicile.
- **Propres à l'Europe :** le texte, à partir de 51 caractères.
- **Local Guide 1 à 4 et réponse** sont plus bas en Europe : ×0,36 et ×0,30, contre ×0,67 et ×0,51
  aux États-Unis. Les fourchettes des deux régions se recouvrent.
- **Aucun secteur** ne se distingue de l'automobile en Europe.

### Grilles : suppressions pour 1 000 avis

Taux comptés directement, rien n'est tenu égal. Case hachurée : moins de 100 avis.

| Grille | CSV |
|---|---|
| [secteur × note](sorties/figures/03D_grille_secteur_note.png) | [03D_grille_secteur_note.csv](sorties/03D_grille_secteur_note.csv) |
| [réponse × note](sorties/figures/03D_grille_reponse_note.png) | [03D_grille_reponse_note.csv](sorties/03D_grille_reponse_note.csv) |
| [secteur × réponse](sorties/figures/03D_grille_reponse_secteur.png), et [sans les chaînes](sorties/figures/03D_grille_reponse_secteur_sans_enseignes.png) | [03D_grille_reponse_secteur.csv](sorties/03D_grille_reponse_secteur.csv) |

- Sur 1 000 avis, 39 disparaissent. Sans les chaînes, 28.
- **Par note :** 1 étoile 72,5 ; 2 étoiles 29,4 ; 3 étoiles 9,6 ; 4 étoiles 15,0 ; 5 étoiles 40,1.
- **Par secteur :** les services à domicile sont à 111,2, et à 57,2 sans les chaînes. Restauration et hôtellerie sont les moins touchées : 15,3 et 16,1.
- **Les 5 étoiles** disparaissent plus que les 3 et 4 étoiles, surtout à cause des services à domicile : 550 suppressions sur 4 873 avis 5 étoiles.

### La réponse du propriétaire, par secteur et par note

Graphiques :
- [par secteur, autres caractéristiques égales](sorties/figures/03D_reponse_par_secteur.png) ;
- [par secteur, écart direct](sorties/figures/03D_reponse_par_secteur_direct.png) ;
- [par note, écart direct](sorties/figures/03D_reponse_par_note_direct.png) ;
- [par note, écart direct, sans le secteur des services à domicile](sorties/figures/03D_reponse_par_note_direct_sans_services_a_domicile.png) :
  25 242 avis, 592 suppressions ; toutes notes −60 % [−72 à −44], 1 étoile −58 %, 5 étoiles −61 %.

« −63 % » : l'avis répondu disparaît 63 % de moins que l'avis sans réponse. « Direct » : les deux
taux comptés à la main, rien n'est tenu égal.

| Secteur | Écart direct | Autres caractéristiques égales | Taux avec / sans réponse, pour 1 000 |
|---|---|---|---|
| Santé | −76 % [−89 à −49] | −86 % [−94 à −67] | 16,9 / 71,0 |
| Restauration | −74 % [−91 à −28] | −88 % [−96 à −66] | 5,9 / 22,7 |
| Automobile | −63 % [−80 à −34] | −73 % [−86 à −48] | 16,1 / 44,0 |
| Voyage | −58 % [−92 à +126] | −76 % [−96 à +35] | 14,3 / 33,6 |
| Hôtellerie | −51 % [−72 à −17] | −57 % [−76 à −24] | 10,7 / 21,9 |
| Sport et bien-être | −37 % [−74 à +49] | −46 % [−78 à +36] | 24,5 / 39,1 |
| Services à domicile | +2 % [−35 à +59] | −19 % [−51 à +32] | 112,0 / 110,3 |
| Tous secteurs | −29 % [−47 à −4] | −54 % [−66 à −37] | 32,5 / 45,5 |

- **Sans les chaînes**, les services à domicile passent à −33 % en direct, et tous secteurs réunis à −50 %.
- **Par note, en direct :**
  - 1 étoile : −43 % [−64 à −12] ;
  - 5 étoiles : −27 % [−49 à +4], et −49 % sans les chaînes ;
  - 2, 3 et 4 étoiles : 3 à 25 suppressions par case, trop peu pour trancher.
- **La colonne « autres caractéristiques égales »** vient d'un calcul qui ne compare pas exactement des taux. Les deux mesures sont presque égales quand moins d'un avis sur dix disparaît. Les services à domicile, à 111 pour 1 000, font exception.

### Pourquoi « tous secteurs » donne −29 % en direct

Chaque secteur est entre −76 % et −37 %, sauf les services à domicile (+2 %). Le total tombe à
−29 % parce que les services à domicile pèsent plus lourd chez les avis répondus.

- **Chez les avis répondus :** 3 046 avis de services à domicile sur 15 633 (19 %), et 341
  suppressions sur 508 (67 %).
- **Chez les avis sans réponse :** 2 340 avis de services à domicile sur 14 995 (16 %), et 258
  suppressions sur 683 (38 %).
- **Sans ce secteur :** 13,3 suppressions pour 1 000 avis répondus, 33,6 pour 1 000 avis sans
  réponse, soit −60 %. Ce calcul retire aussi les 4 chaînes, toutes classées en services à
  domicile.
- **Autres caractéristiques égales :** le calcul compare chaque avis à un avis du même secteur :
  le total y est à −54 %.

Source : [03D_reponse_par_secteur.csv](sorties/03D_reponse_par_secteur.csv),
[03D_grille_reponse_secteur.csv](sorties/03D_grille_reponse_secteur.csv).

### Courbe de vie d'un avis sur ses 21 premiers jours

Source : [03D_courbe_de_vie.csv](sorties/03D_courbe_de_vie.csv), graphique
[03D_courbe_de_vie.png](sorties/figures/03D_courbe_de_vie.png). Base complète
`reviews_doublons_cleaned_all`, avis publiés de J-7 à J+14 (J = 11 août 2026, premier passage du
robot). Le suivi s'arrête le 24 août : le dernier âge observé est 20 jours, le 21e reste vide.

| Encore en ligne | 5e jour | 7e jour | 14e jour | 20e jour |
|---|---:|---:|---:|---:|
| États-Unis | 98,9 % | 95,6 % | 93,4 % | 92,8 % |
| États-Unis, sans les chaînes | 99,0 % | 97,0 % | 95,6 % | 94,9 % |
| Europe | 97,9 % | 97,2 % | 96,5 % | 95,1 % |
| Europe, sans les 2 salles espagnoles | 97,9 % | 97,2 % | 96,6 % | 95,6 % |

- **États-Unis :** la chute se fait aux 6e et 7e jours, 238 puis 377 avis disparus sur environ
  18 000 en ligne la veille. Sans les chaînes, 135 puis 190.
- **Europe :** les pertes commencent dès le 2e jour, puis la courbe descend lentement.
- **Avis observés par jour d'âge :** 3 289 (US) et 394 (Europe) au 1er jour, environ 18 000 et
  14 500 du 2e au 7e, 9 428 et 7 929 au 14e, 1 313 et 1 141 au 20e. Les derniers jours reposent
  sur les seuls avis publiés du 4 au 10 août.

#### Vérification sur un groupe d'avis fixe

Les mêmes avis suivis du début à la fin : publiés du 10 au 17 août, 11 415 aux États-Unis, 8 931 en
Europe. Compte direct, jours 1 et 2 regroupés en « 48 h ». Graphiques :
[groupe fixe](sorties/figures/03D_courbe_de_vie_groupe_fixe.png),
[une courbe par date de publication](sorties/figures/03D_courbe_de_vie_par_date.png).

| Encore en ligne | 48 h | 5e jour | 6e jour | 7e jour |
|---|---:|---:|---:|---:|
| États-Unis | 99,7 % | 99,3 % | 97,8 % | 95,3 % |
| États-Unis, sans les chaînes | 99,7 % | 99,4 % | 98,4 % | 97,0 % |
| Europe | 99,6 % | 99,1 % | 98,8 % | 98,1 % |

- **États-Unis :** au 7e jour, 95,3 % sur le groupe fixe, 95,6 % sur la courbe enchaînée.
  Chaque date de publication du 10 au 17 août fait son saut aux 6e et 7e jours : 3,4 % à 6,0 %
  des avis disparus au 7e jour selon la date. Le saut suit l'âge de l'avis, quel que soit le jour
  du calendrier. L'enchaînement des jours tient.
- **Europe :** 98,1 % au 7e jour sur le groupe fixe, 97,2 % sur la courbe enchaînée. L'écart vient
  du 1er jour de la courbe enchaînée : 5 disparus sur 394 avis, soit 1,3 point de perte. Selon la
  date de publication, de 0,9 % à 3,2 % des avis ont disparu au 7e jour.
- **Avis vus pour la première fois après 2 jours :** 129 aux États-Unis, 95 en Europe. Une
  disparition avant le premier passage du robot reste invisible.

#### Le groupe fixe prolongé à 14 jours, deux versions

- **A, avis du 10 août seulement** ([graphique](sorties/figures/03D_courbe_de_vie_groupe_fixe_A.png),
  lignes `2026-08-10` de [03D_courbe_de_vie_groupe_fixe.csv](sorties/03D_courbe_de_vie_groupe_fixe.csv)) :
  1 381 avis aux États-Unis, 1 140 en Europe, les mêmes du début à la fin. Au 14e jour : 94,3 %
  et 96,3 % encore en ligne.
- **B, groupe qui rétrécit** ([graphique](sorties/figures/03D_courbe_de_vie_groupe_fixe_B.png),
  [CSV](sorties/03D_courbe_de_vie_groupe_fixe_B.csv)) : chaque jour, les avis du 10 au 17 août
  suivis jusque-là. 11 415 et 8 931 avis jusqu'au 7e jour, 1 381 et 1 140 au 14e. Au 14e jour,
  B est égal à A.
- **Réserve sur B :** aux États-Unis, la part encore en ligne remonte de 93,7 % au 12e jour à 94,3 %
  au 14e. Les avis du 11 et du 12 août, qui ont perdu plus, sortent du groupe ces jours-là.

### Google supprime peu une fois l'avis publié

Base complète, tous pays, avis rangés selon leur date de publication (created_at).

Les trois graphiques ont la même mesure et la même échelle (0 à 200) : suppressions d'une journée
pour 10 000 avis en ligne. Pour les avis publiés avant le suivi, c'est le total des 13 jours où une
disparition peut être constatée (12 au 24 août) divisé par 13.

- **Avis publiés de 2004 à 2025** ([graphique](sorties/figures/03D_supprime_peu_anciens.png),
  [CSV](sorties/03D_supprime_peu_anciens.csv)) : 1 523 suppressions sur 4 389 888 avis en 13 jours,
  soit 0,27 par jour pour 10 000. Sans les enseignes, 1 099 sur 4 169 346, soit 0,20.
  - de 2014 à 2022 : 0,09 à 0,21 par jour pour 10 000 ;
  - 2023 à 2025 : 0,29, 0,45 et 0,56.
- **Avis publiés de janvier à juillet 2026** ([graphique](sorties/figures/03D_supprime_peu_2026.png),
  [CSV](sorties/03D_supprime_peu_2026.csv)) : 1 127 suppressions sur 429 098 avis en 13 jours, soit
  2,02 par jour pour 10 000. Sans les enseignes, 849 sur 404 230, soit 1,62.
  - janvier à avril : 0,47 à 0,80 par jour pour 10 000 ;
  - mai : 1,09 ; juin : 2,33 ; juillet : 6,55 (4,97 sans les enseignes).
- **Avis publiés du 11 au 23 août** ([graphique](sorties/figures/03D_supprime_peu_recents.png),
  [CSV](sorties/03D_supprime_peu_recents.csv)) : 846 suppressions sur 32 805 avis, soit 2,6 %.
  Sans les enseignes, 607 sur 30 670, soit 2,0 %.
  - 6e et 7e jours : 98 et 179 suppressions du jour pour 10 000 avis en ligne la veille (67 et
    105 sans les enseignes) ;
  - du 9e au 13e jour : 0 à 15 pour 10 000 ;
  - au 13e jour, 2 481 avis seulement sont encore suivis.

---

## Réserves

- **La réponse est lue au dernier passage du robot.** Un avis resté en ligne jusqu'au 24 août a
  eu jusqu'à 18 jours pour recevoir une réponse, un avis supprimé au 2e jour seulement 2. Une
  partie de l'effet de la réponse vient de là.
- **La durée de suivi n'est pas tenue égale.**
  - Un avis du 6 août n'est vu qu'à partir du 11 : ses 5 premiers jours échappent au robot.
  - Un avis du 17 août est suivi 7 jours.
  - 19 avis publiés du 15 au 17 août n'ont été vus que le 24 août, sans jour de suivi. 17 d'entre eux portent 1 ou 2 étoiles. Ils comptent « non supprimés ».
- **Le taux de réponse de la fiche** est calculé sur tous ses avis, toutes dates. L'avis examiné et sa propre réponse y entrent.
- **Les 2 salles espagnoles n'ont aucun avis dans ce panel.** Leur attaque date du 1er au 5 août. Le retrait des enseignes ne retire donc que les 4 chaînes : 85 fiches, 1 924 avis, 401 suppressions.
- **18 avis ont un rythme de fiche nul.** Leur fiche n'avait reçu aucun avis dans l'année d'avant. Leur rythme est mis à 0,1 avis par jour (décision de Romain) : 7 sont en pic, 11 non.
- **Le sens de la cause reste ouvert.** Un propriétaire peut s'abstenir de répondre à un avis qu'il conteste. Les données ne montrent pas les signalements.

---

## Pourquoi la consolidation trouvait un effet de réponse plus net

La consolidation (points 3, 4b, 5, 8) trouve ×0,21 à ×0,36 sur les fiches qui répondent à plus de
75 %. Les différences de méthode :

1. **Le moment où la réponse compte.** Au point 5, l'avis compte « sans réponse » jusqu'au jour
   de la réponse, puis « répondu » à partir du lendemain. Il est comparé chaque jour à un avis du
   même âge encore sans réponse.
2. **L'habitude de la fiche.** La consolidation mesure la réponse séparément sur les fiches qui
   répondent à plus de 75 % et sur les autres. La protection n'apparaît que sur les premières.
   03D mélange toutes les fiches.
3. **L'âge de l'avis** est tenu égal jour par jour au point 5, et pas dans 03D.
4. **Comparer dans la même fiche** (4b) neutralise les chaînes : ×0,21 avec et sans elles.

Un calcul jour par jour sur 03D a été fait puis retiré du code (voir ci-dessous). Sur les fiches
qui répondent à plus de 75 %, il donnait ×0,46 [0,31 à 0,67], et ×0,29 [0,20 à 0,42] sans les
chaînes. C'est le même ordre que la consolidation.

---

## Essayé puis abandonné

- **Délai de réponse en trois tranches** (jour même ou lendemain, 2 à 7 jours, plus de 7 jours).
  Les 597 avis répondus après 7 jours n'avaient aucune suppression : pour être répondu au 8e jour,
  un avis doit encore être en ligne. Remplacé par une seule colonne.
- **« Répondu dans les 2 jours »**, face à tout le reste : ×0,80 [0,59 à 1,08]. La référence
  contenait des avis répondus plus tard, déjà protégés. Remplacé par « a répondu ».
- **Écarter les 18 avis sans rythme de fiche** : remplacé par un rythme mis à 0,1 avis par jour.
- **La grille secteur × note sans les chaînes** : retirée, les chaînes vont en commentaire.
- **Le calcul jour par jour** (`sql/03D_jours.sql`, `03D_regression_jour_par_jour.py`) : code
  retiré par retour en arrière. Ses sorties restent, et ne peuvent plus être refaites :
  - [03D_jours_effets.csv](sorties/03D_jours_effets.csv) ;
  - [03D_jours_effectifs.csv](sorties/03D_jours_effectifs.csv) ;
  - [03D_jours_effets.png](sorties/figures/03D_jours_effets.png).

---

## Reste ouvert

- **Sorties du calcul jour par jour** (`03D_jours_*`) : à garder ou à supprimer, décision de Romain.
- **Le graphique par note sans les services à domicile** n'a pas de version « sans les chaînes » :
  les 4 chaînes sont déjà retirées avec le secteur.
