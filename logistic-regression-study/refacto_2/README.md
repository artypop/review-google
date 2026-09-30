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
| [03D_regression_logistique.py](03D_regression_logistique.py) | effet de chaque caractéristique, les autres tenues égales, 5 passages | [03D_effets.csv](sorties/03D_effets.csv), [03D_effectifs.csv](sorties/03D_effectifs.csv), [03D_effets.png](sorties/figures/03D_effets.png) |
| [03D_grilles.py](03D_grilles.py) | suppressions pour 1 000 avis, en grilles croisées | voir la section « Grilles » |
| [03D_reponse_par_secteur.py](03D_reponse_par_secteur.py) | effet de la réponse du propriétaire, par secteur et par note | [03D_reponse_par_secteur.csv](sorties/03D_reponse_par_secteur.csv), [03D_reponse_par_note.csv](sorties/03D_reponse_par_note.csv), 4 graphiques |
| [sql/03D_avis_sans_rythme.sql](sql/03D_avis_sans_rythme.sql) | les 18 avis dont la fiche n'a reçu aucun avis l'année d'avant | [03D_avis_sans_rythme.csv](sorties/03D_avis_sans_rythme.csv) |

Pour tout refaire (environ une minute) :

```
bq query --use_legacy_sql=false < logistic-regression-study/refacto_2/03D_adding_features.bqsql
uv run python logistic-regression-study/refacto_2/03D_regression_logistique.py
uv run python logistic-regression-study/refacto_2/03D_grilles.py
uv run python logistic-regression-study/refacto_2/03D_reponse_par_secteur.py
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
