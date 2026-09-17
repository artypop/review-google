# Suppressions d'avis Google : synthèse générale au 2026-09-17

Pour Axel et Romain. À valider par Romain avant diffusion.

Cette note rassemble ce qui est consolidé au 17 septembre. Elle remplace les synthèses partielles du jour, qui restent dans le même dossier : `2026-09-17-synthese-07.md` (modèle sur tout le panel), `2026-09-17-synthese-modele-A.md` (8 premiers jours), `2026-09-17-synthese-08.md` (réponse du propriétaire).

---

## 1. En bref

- **Le risque se joue dans la première semaine de l'avis.** Sept suppressions sur dix tombent au 6e ou au 7e jour.
- **L'avis 1 étoile est supprimé 3 à 4 fois plus** qu'un avis 5 étoiles comparable. La plupart des avis supprimés portent quand même 5 étoiles, puisqu'ils sont les plus nombreux : 80 % des suppressions américaines et 62 % des européennes, hors enseignes.
- **L'auteur sans niveau Local Guide** voit ses avis supprimés 2 à 3 fois plus. Un auteur avec beaucoup de photos ou beaucoup d'avis est moins touché. Le niveau Local Guide élevé ne protège pas en lui-même.
- **Plusieurs avis publiés le même jour par un même auteur** multiplient le risque par 3 à 5, sur peu d'avis.
- **Répondre vite protège sur les fiches qui répondent à presque tous leurs avis** : l'avis déjà répondu y est supprimé 2,5 fois moins. Sur les fiches qui répondent de temps en temps, l'avis répondu est plutôt plus supprimé.
- **Six enseignes portent 39 % des suppressions du panel** : 692 pour les quatre chaînes antiparasitaires américaines et 327 pour les deux salles de sport espagnoles, sur 2 595. Chaque résultat est donné sans elles.
- **Les caractéristiques disponibles expliquent une part limitée des suppressions.** À date de publication comparable, les 10 % d'avis jugés les plus risqués contiennent 22 à 31 % des suppressions, contre 10 % pour un tirage au hasard.

---

## 2. Les populations étudiées

| | Avis | Dont chaînes antiparasitaires | Dont salles de sport | Suppressions | Dont chaînes | Dont salles |
|---|---:|---:|---:|---:|---:|---:|
| Panel entier (modèle 07) | 225 757 | 14 640 | 357 | 2 595 | 692 | 327 |
| États-Unis | 127 813 | 14 640 | 0 | 1 851 | 692 | 0 |
| Europe | 97 944 | 0 | 357 | 744 | 0 | 327 |
| 8 premiers jours, publiés du 10 au 16 août (modèle A) | 17 679 | 1 148 | 0 | 661 | 216 | 0 |
| Réponse du propriétaire, au 2e jour (08) | 17 615 | 1 148 | 0 | 597 | 216 | 0 |

- Le panel couvre les avis publiés du 13 mai au 16 août 2026, suivis du 11 au 24 août, sur 8 205 fiches.
- Le modèle A et le 08 portent sur les avis publiés du 10 au 16 août, dont on a vu les premiers jours. Le modèle A retire 56 avis supprimés après leur 8e jour, dont 5 des chaînes. Le 08 retire en plus les avis disparus avant le 2e jour, 64 au total.
- Les fiches repérées comme enseignes viennent de la table `biz_surveillance` : 93 succursales américaines des quatre chaînes et les 2 salles espagnoles.
- **Une réserve de comptage** : le script 07 retire encore les salles par leur nom d'enseigne. Son passage « Europe sans enseignes » écarte donc 90 avis de plus que le repérage par `cid`, et ces 90 avis ne portent aucune suppression.

---

## 3. Quand un avis disparaît

**Sur les avis publiés pendant la première semaine de suivi : 695 supprimés, dont 311 exactement au 7e jour.**

| Délai avant suppression | Suppressions | Part |
|---|---:|---:|
| 1 à 5 jours | 129 | 18,6 % |
| 6 jours | 167 | 24,0 % |
| 7 jours | 311 | 44,7 % |
| 8 jours et plus | 88 | 12,7 % |

Le motif se répète pour chaque journée de dépôt. Il oriente vers un traitement automatique déclenché à date fixe, sans que les données permettent de le confirmer.

**Les enseignes ne suivent pas ce calendrier.** Délais mesurés sur le panel (`sql/controle_D_delai_suppression_enseignes.bqsql`) :

| Groupe | Suppressions | Délai médian | Délai le plus court |
|---|---:|---:|---:|
| Deux salles de sport | 327 | 15 jours | 9 jours |
| Quatre chaînes antiparasitaires | 692 | 7 à 21 jours selon la période de publication | 3 jours |
| Reste des États-Unis | 1 159 | 7 à 30 jours selon la période | 1 jour |
| Reste de l'Europe | 417 | 6 à 23 jours selon la période | 1 jour |

Les avis publiés avant le 4 août ne peuvent disparaître qu'à 9 jours ou plus, puisque le robot arrive le 11 août : leur délai médian n'est pas comparable à celui des avis publiés pendant le suivi.

---

## 4. Ce qui distingue un avis supprimé

### 4.1 Sur tout le panel, à date de publication comparable

Modèle 07, sans les enseignes. Entre parenthèses, la valeur obtenue avec elles.

| | États-Unis | Europe |
|---|---|---|
| Avis 1 étoile, comparé à 5 étoiles | ×3,5 (×2,4) | ×4,1 (×14,4) |
| Auteur sans niveau Local Guide, comparé aux niveaux 1 à 3 | ×2,3 (×2,0) | ×3,0 (×3,5) |
| Auteur à 100 photos, comparé à 0 photo | ×0,42 (×0,36) | pas d'écart net |
| Auteur à 20 avis, comparé à 2 | pas d'écart net | ×0,51 (×0,41) |
| 4 avis du même auteur le même jour, comparé à 1 | ×5,0 (×33) | ×3,2 (pas d'écart net) |
| Jour où la fiche reçoit 5 fois son rythme habituel | ×0,71 (pas d'écart net) | ×1,32 (×2,5) |
| Services à domicile, comparé à l'automobile | ×3,2 (×4,5) | pas d'écart net |

**Sans effet net** : la photo dans l'avis, la longueur du texte, une langue inhabituelle pour la fiche, la taille du groupe.

**Le palier Local Guide 4 et plus ne protège pas.** En chiffres bruts, ces auteurs perdent moins d'avis (28 pour 10 000 en Europe, contre 41 pour les niveaux 1 à 3). À photos et nombre d'avis égaux, ils en perdent autant aux États-Unis et plus en Europe : ×1,7.

### 4.2 Dans les huit premiers jours de l'avis

Modèle A, avis publiés du 10 au 16 août, sans les chaînes.

| | États-Unis | Europe |
|---|---|---|
| Avis 1 étoile | ×3,2 | ×3,0 |
| Auteur sans niveau Local Guide | ×2,2 | ×2,9 |
| Avis avec du texte, comparé à un avis sans texte | pas d'écart net | ×2,2 à ×2,5 |
| Jour d'affluence sur la fiche | ×0,74 | pas d'écart net |

Les deux modèles se rejoignent sur la note et sur le profil de l'auteur.

### 4.3 En chiffres bruts, par note

Suppressions pour 10 000 avis du panel :

| Note | États-Unis | Sans les chaînes | Europe | Sans les salles |
|---|---:|---:|---:|---:|
| 1 étoile | 262 | 259 | 585 | 152 |
| 3 étoiles | 65 | 63 | 24 | 24 |
| 4 étoiles | 61 | 40 | 24 | 24 |
| 5 étoiles | 145 | 97 | 36 | 36 |

**Deux questions différentes.** Le tableau ci-dessus dit le risque d'un avis selon sa note. Le
tableau ci-dessous dit de quoi sont faits les avis supprimés, hors enseignes :

| Note | États-Unis : part des avis | Part des suppressions | Europe : part des avis | Part des suppressions |
|---|---:|---:|---:|---:|
| 1 étoile | 5,7 % | 14 % | 7,1 % | 25 % |
| 2 étoiles | 1,7 % | 2 % | 2,7 % | 4 % |
| 3 étoiles | 2,1 % | 1 % | 4,2 % | 2 % |
| 4 étoiles | 5,5 % | 2 % | 11,5 % | 6 % |
| 5 étoiles | 85,0 % | 80 % | 74,5 % | 62 % |

Un avis 1 étoile court plus de risque, et l'essentiel des avis qui disparaissent porte 5 étoiles.
Sur tout le panel, enseignes comprises, 1 850 des 2 595 avis supprimés portaient 5 étoiles, soit
71 %, et 607 portaient 1 étoile, soit 23 %.

### 4.4 En chiffres bruts, par secteur

Suppressions pour 10 000 avis du panel :

| Secteur | Avis | Suppressions | Pour 10 000 | Sans enseignes : avis | Suppressions | Pour 10 000 |
|---|---:|---:|---:|---:|---:|---:|
| Services à domicile | 42 640 | 1 189 | 279 | 28 000 | 497 | 178 |
| Sport et bien-être | 24 165 | 532 | 220 | 23 808 | 205 | 86 |
| Voyage | 14 881 | 129 | 87 | 14 881 | 129 | 87 |
| Automobile | 28 794 | 205 | 71 | 28 794 | 205 | 71 |
| Santé | 31 318 | 216 | 69 | 31 318 | 216 | 69 |
| Hôtellerie | 39 463 | 168 | 43 | 39 463 | 168 | 43 |
| Restauration | 44 496 | 156 | 35 | 44 496 | 156 | 35 |

Les 14 640 avis des chaînes antiparasitaires appartiennent aux services à domicile, les 357 avis des salles au sport et bien-être.

---

## 5. La réponse du propriétaire

Modèle 08, avis publiés du 10 au 16 août, encore en ligne à la fin de leur 2e jour, sans les chaînes : 16 467 avis, dont 6 536 avec une réponse, et 381 suppressions du 3e au 8e jour.

| L'habitude de la fiche | Avis | Suppressions | Effet d'une réponse présente au 2e jour |
|---|---:|---:|---|
| Répond à plus de 75 % de ses avis | 8 353 | 191 | ×0,40 (entre ×0,25 et ×0,65) |
| Répond à 25 à 75 % | 3 107 | 75 | ×2,0 (entre ×1,04 et ×4,0) |
| Répond à moins de 25 % | 4 716 | 113 | trop peu d'avis répondus pour mesurer |
| Moins de 10 avis l'an dernier | 291 | 2 | trop peu de suppressions |

- Sur les fiches qui répondent presque toujours, le résultat tient du 1er au 6e jour de lecture : de ×0,32 à ×0,47.
- L'effet moyen, toutes habitudes confondues, vaut ×0,59. Il mélange les deux situations.
- Avec les chaînes (1 148 avis de plus, dont 454 répondus et 216 supprimés), aucun effet n'est net.
- Au 7e jour, la mesure devient impossible : il ne reste que 45 suppressions à compter, au 8e jour.

---

## 6. Les six enseignes

| Groupe | Fiches | Avis | Suppressions | Part des suppressions du panel | Taux |
|---|---:|---:|---:|---:|---:|
| 4 chaînes antiparasitaires US | 88 | 14 640 | 692 | 26,7 % | 4,73 % |
| 2 salles de sport espagnoles | 2 | 357 | 327 | 12,6 % | 91,6 % |
| Tout le reste | 8 115 | 210 760 | 1 576 | 60,7 % | 0,75 % |

**Les salles de sport** perdent 92 % de leurs avis du panel, presque tous 1 étoile, entre 9 et 22 jours après publication. L'hypothèse retenue est une attaque par faux avis suivie d'un nettoyage, probablement à la demande du propriétaire. Les données ne montrent pas les signalements.

**Les quatre chaînes** perdent surtout des avis 4 et 5 étoiles, et rien n'explique ces retraits :

- **Aucun afflux soudain** (`sql/controle_E_afflux_chaines_antiparasitaires.bqsql`). EcoShield passe d'environ 280 avis par semaine en février à 560 dès le 6 avril, puis 700 à 750 en mai-juin : une montée durable, quatre mois avant le suivi. Jour par jour, du 13 mai au 16 août, la journée la plus chargée d'EcoShield fait 161 avis pour une médiane de 99.
- **Un fait nouveau** : 44 avis de ces chaînes viennent d'auteurs ayant publié 4 avis ou plus le même jour sur leurs succursales, et les 44 ont été supprimés. Hors chaînes, 34 avis américains sont dans ce cas, et aucun n'a été supprimé. Ces 44 avis pèsent 44 des 692 suppressions des chaînes.
- Leur présence fait passer la rafale de ×5 à ×33 aux États-Unis et l'avis 1 étoile de ×3,5 à ×2,4.

---

## 7. Ce que valent les modèles

On range les avis du plus risqué au moins risqué, chaque fiche étant notée par un modèle qui ne l'a jamais vue, puis on compte les suppressions dans les 10 % d'avis les plus risqués. Un tirage au hasard en trouverait 10 %.

| Modèle et population | Tous les avis | Avis publiés du 3 au 16 août | Avis publiés avant |
|---|---|---|---|
| 07, États-Unis sans enseignes | 41 % | 22 % | 26 % |
| 07, Europe sans enseignes | 51 % | 30 % | 31 % |
| Modèle A, États-Unis sans chaînes | 23 % | — | — |
| Modèle A, Europe | 26 % | — | — |

- **La première colonne du 07 profite de la date de publication.** Les avis publiés du 3 au 16 août sont 15 % du panel américain et portent la moitié des suppressions.
- **Les colonnes par période, et le modèle A, mesurent ce qu'apportent la note, l'auteur et le reste** : 2 à 3 fois mieux qu'un tirage au hasard.
- **Le niveau annoncé est juste** : 1 151 suppressions annoncées pour 1 134 constatées aux États-Unis, 409 pour 409 en Europe, 288 pour 283 dans le modèle A américain.

---

## 8. Réserves qui valent pour tout le document

- **La cause d'une suppression est inconnue.** Traitement automatique, signalement du propriétaire, contestation d'un tiers : rien dans les données ne tranche.
- **On ne voit que les avis publiés.** Le filtrage avant mise en ligne est invisible.
- **Un avis supprimé avant le 11 août n'est dans aucune table.** Les volumes anciens et les rythmes de fiche sont calculés sur les avis survivants.
- **Une réponse retirée est invisible** : l'avis compte comme sans réponse.
- **Le profil de l'auteur** (niveau, photos, nombre d'avis) est relevé au dernier passage du robot.
- **La fenêtre d'observation est de 14 jours.** Une suppression à six mois est hors de portée.
- **Le panel ne couvre pas tout** : 41 pays dont un seul hors d'Europe, sans le Royaume-Uni, sans les groupes de 2 à 3 ni de 11 à 19 établissements.
- **Les avis publiés du 7 au 9 août sont écartés du modèle A** : la moitié de leurs suppressions tombent après le 8e jour, et la règle du modèle les retire.

---

## 9. Ce qui a été décidé et changé le 17 septembre

| Décision | Ce qu'elle remplace |
|---|---|
| Palier Local Guide : sans niveau, 1 à 3, 4 et plus | le profil d'auteur à trois situations, qui rangeait 92 % des avis dans une seule case |
| Photos de l'auteur ajoutées au modèle | — |
| Habitude de réponse de la fiche ajoutée au 08 | — |
| Date de publication en oui / non : le 8e jour tombe-t-il pendant le suivi ? | l'âge au 11 août en logarithme, qui valait 0 pour les 15 248 avis publiés pendant le suivi |
| Qualité mesurée en cinq tours par établissement | un tirage unique d'un quart des fiches, tombé en Europe sur des fiches 2,3 fois moins touchées |
| Courbe de ciblage | le graphique de calibration, dont 8 points sur 10 s'entassaient sous 1,5 % |
| Enseignes repérées par `biz_surveillance` | le repérage par nom, qui comptait 11 salles de sport en trop |
| Réponse du propriétaire retirée du 07 | sa présence dans le modèle du panel ; elle est étudiée par le 08 |
| Modèle A limité aux avis publiés du 10 au 16 août | la période du 7 au 16 août |

**Écarté après essai** :
- le script `09_simplified_reg.py`, qui utilise `a_une_reponse`, l'état de la réponse au dernier passage du robot. Cette colonne mesure en partie la survie de l'avis, et ses chiffres ne sont pas à citer ;
- l'ajout au modèle A d'avis plus anciens jamais supprimés : ils ont déjà franchi le filtre des premiers jours, et ils gonfleraient les effets ;
- le comptage des avis supprimés à 9 jours ou plus comme restés en ligne, dans le modèle A et le 08 : la durée d'observation varie selon la date de publication.

---

## 10. Questions ouvertes

1. **Les quatre chaînes antiparasitaires.** Elles portent 692 des 2 595 suppressions, surtout sur des avis 4 et 5 étoiles, sans afflux ni caractéristique qui les explique. Piste ouverte : leurs textes citent souvent un technicien par son prénom.
2. **Le 7e jour.** C'est le motif le plus net de l'étude et il n'a pas d'explication.
3. **La réponse qui joue en sens opposés** selon l'habitude de la fiche.
4. **Les suppressions tardives**, après le 8e jour : aucun modèle ne les couvre.
5. **D'autres attaques par faux avis** dans le panel : deux ont été trouvées, aucune recherche systématique n'a été faite.
6. **Les documents `docs/03-resultats.md`, `docs/05-resume-regressions.md` et `docs/BACKLOG.md`** citent encore les chiffres du 14 et du 15 septembre.

---

## 11. Refaire les calculs

Depuis la racine du projet :

```bash
# Caractéristiques (table reviews_panel_features_03)
bq query --use_legacy_sql=false < logistic-regression-study/sql/03_adding_features.bqsql

# Modèle sur tout le panel, six passages
nice -n 19 .venv/bin/python logistic-regression-study/python/07_regression_panel.py --region US --sans-enseignes-signalees
nice -n 19 .venv/bin/python logistic-regression-study/python/07_regression_panel.py --region Europe --sans-enseignes-signalees

# Huit premiers jours de l'avis, trois passages
nice -n 19 .venv/bin/python logistic-regression-study/python/10_modele_A_8_premiers_jours.py

# Réponse du propriétaire
nice -n 19 .venv/bin/python logistic-regression-study/python/08_effet_reponse_commercant.py --sans-enseignes-signalees --reponse-par-habitude

# Contrôles en lecture seule
bq query --use_legacy_sql=false < logistic-regression-study/sql/controle_D_delai_suppression_enseignes.bqsql
bq query --use_legacy_sql=false < logistic-regression-study/sql/controle_E_afflux_chaines_antiparasitaires.bqsql
```

Sorties : `logistic-regression-study/output-study/2026-09-17-sorties-07/`, `-sorties-08/`, `-sorties-10/`.
