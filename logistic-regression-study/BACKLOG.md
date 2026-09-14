# Backlog — Étude régression logistique

Dernière mise à jour : 2026-09-14.

Légende : `[ ]` à faire · `[~]` en cours · `[x]` fait

---

## État au 2026-09-14 — à lire en premier

**Le panel a changé de forme le 2026-09-13.** Il a maintenant **une ligne par avis**, là où
l'ancien avait une ligne par avis et par vague. Une observation, un sort, aucune dépendance
entre lignes.

| Étape | Produit | Contenu |
|---|---|---|
| `sql/01_selection_panel.sql` | `reviews_panel_selection` | 225 757 avis, 24 colonnes |
| `sql/02_adding_features.sql` | `reviews_panel_features` | les mêmes avis, 42 colonnes |
| `07_regression_panel.py` | `2026-09-14-sorties-07/` | quatre passages, cinq fichiers chacun |

**Périmètre :** avis publiés entre le 2026-05-13 et le 2026-08-16, soit 90 jours avant la
vague 1 et jusqu'à la vague 6, pour que le dernier entrant soit encore observé 8 jours.
225 757 avis, 2 595 suppressions, 1,15 %, 8 205 fiches.

**L'ancienne chaîne est rangée**, sans être maintenue : `2026-09-11-sql/` pour les requêtes,
`2026-09-10-legacy/` pour les versions remplacées, `2026-09-10-sorties/` pour ses résultats.
`06_statsmodels_analysis_review_claude.py` tourne encore sur l'ancien panel ; il est remplacé
par `07_regression_panel.py`.

---

## Fait le 2026-09-14, deuxième session

### La régression est interprétée

- [x] **`2026-09-14-interpretation-panel.md`** — lecture des quatre passages, sans rien
      relancer. Résultat central : aux États-Unis l'avis 5 étoiles est supprimé **plus** souvent
      que l'avis 3 ou 4 étoiles (145,1 contre 65,3 et 60,5 pour 10 000 avis) ; en Europe il l'est
      presque trois fois moins que l'avis 1 étoile. Deux régimes opposés dans le même corpus.
      1 850 des 2 595 suppressions du panel frappent un avis 5 étoiles, soit **71,3 %**.
- [x] **Trois effets tiennent dans les quatre passages** : compte sans niveau Local Guide,
      secteur home_services, établissement américain. Trois changent de sens selon le
      découpage et ne doivent jamais être cités seuls : rafale d'auteur, pic d'afflux, texte
      long.
- [x] **Le passage Europe est mal calibré, et la cause n'est pas celle qu'on croyait.** Ce n'est
      pas le modèle qui se trompe, c'est l'échantillon de test : `decoupage()` tire 25 % des
      établissements au hasard, et en Europe ce tirage est tombé sur des fiches **2,3 fois moins
      touchées que le corpus** (0,327 % contre 0,760 %). Le modèle annonce le bon niveau, le test
      est plus calme, tout paraît surestimé — sur les dix déciles, pas seulement le dernier. Aux
      États-Unis et sur le corpus entier, l'écart est nul (1,429 % contre 1,448 % ; 1,138 %
      contre 1,149 %).
- [x] **Pourquoi l'Europe** : **2 fiches sur 4 106 portent 327 des 744 suppressions, soit 44 %.**
      Ce sont les deux salles de sport espagnoles attaquées, vérifiées fiche par fiche le
      2026-09-14 : Boutique The Boxer Club Dr Castelo (206 avis, 192 suppressions) et The Boxer
      Club (151 avis, 135 suppressions).
      **Les retirer ne suffit pas** : `Europe_sans_enseignes` garde un test 1,8 fois moins touché
      que son corpus (0,239 % contre 0,428 %), AUC 0,882.
- [x] **Réserve sur le drapeau `salle_de_sport_attaquee`, sans effet sur les chiffres.** Il repose
      sur `b.name` et non sur `cid`, donc il marque 13 fiches : les 2 attaquées, plus 11 autres
      salles « The Boxer Club » totalisant 90 avis et **aucune suppression**.
      `--sans-enseignes-signalees` les écarte à tort, sans changer un coefficient (90 avis sur
      210 670, 0 suppression sur 1 576). **Décision de Romain le 2026-09-14 : on n'y touche pas.**
      Le même drapeau pour les 4 chaînes antiparasitaires est correct, le multi-fiches y étant
      voulu (26, 19, 19, 24 fiches, conformes à `../CLAUDE.md`).
- [ ] **À faire : validation croisée par établissement, 5 plis**, en remplacement du tirage unique
      de `decoupage()`. Chaque fiche passe une fois en test, les prédictions hors échantillon sont
      rassemblées, AUC et calibration se lisent sur le corpus entier. Coût : ~1 minute, le modèle
      s'ajustant en 8 à 11 secondes. Voir `2026-09-14-interpretation-panel.md`, section 5.

### La réponse du commerçant

- [x] **Divergence D9 fermée.** `analysis_b.py` lisait `has_reply`, l'état au dernier passage du
      robot recopié sur tous les précédents. La réponse y est maintenant datée, comme dans
      `verif_reponse_proprietaire.py`. **L'effet passe de ×0,30 à ×0,40** ; seul ce facteur
      bouge, les autres se déplacent de 1 à 5 %. Même corpus, mêmes 61 202 observations.
      **« ×0,30 » et « répondre protège 3,7 fois » ne sont plus citables.**
- [x] **Le CSV `data/resultats/analyse_b_effets.csv` était périmé** par rapport à la note qu'il
      accompagne : il portait rafale ×18,8 quand la note affichait ×5,30, et une colonne
      `significatif` à « True » partout alors que rien n'était calculé. Régénéré.
- [x] **L'écart entre ×0,40 et le ×1,02 de la régression est documenté**, avec le contrôle qui
      le trancherait — découper la tranche « 0 à 6 jours » de l'analyse B en jours pleins. Non
      lancé, demande son propre plan.
- [x] **La question d'Axel a une réponse.** `08_effet_reponse_commercant.py` lancé le
      2026-09-14 sur huit passages (quatre jalons × avec et sans enseignes). **Répondre dans les
      deux jours divise le risque par 1,8 hors des quatre chaînes antiparasitaires :
      ×0,56 [0,37 – 0,85], p = 0,007.** Sur le corpus complet, rien de mesurable : ×0,79
      [0,53 – 1,16]. Note : `2026-09-14-effet-reponse-commercant.md`. Détail en « À faire » n° 1,
      devenu fait.
- [x] **La clé BigQuery n'est plus codée en dur.** `07` et `08` prenaient
      `client-divers-8b012e5b7c73.json`, renommé en `client-divers-df744e79fa71.json` le
      2026-09-14 : le script échouait sur une `DefaultCredentialsError` qui ne disait pas qu'il
      s'agissait d'une rotation. `trouver_cle()` prend maintenant le seul `.json` de
      `~/.gcp/`, respecte `GOOGLE_APPLICATION_CREDENTIALS` s'il est posé, et s'arrête s'il y a
      plusieurs clés plutôt que d'en choisir une au hasard.

### Correctifs

- [x] **L'AUC est écrite dans `07_summary_*.txt`.** Elle ne figurait que dans le titre du
      graphique de calibration, donc illisible sans ouvrir une image. `ecrire_summary` est
      appelée deux fois, avant et après le calcul, et reconstruit le fichier entièrement.
- [x] **Tableau des quatre passages refait depuis les CSV** (voir plus bas), et « ×0,93,
      p = 0,649 » remplacé par la valeur versionnée.
- [x] **Réserve ajoutée sur la longueur du texte** : son signe s'inverse entre `tous` et
      `sans enseignes`, de ×0,66 à ×1,38 (p = 0,010). Elle était classée « ne tient pas ».

---

## Fait le 2026-09-14

### Modèle

- [x] **Écrit `07_regression_panel.py`**, sur le nouveau panel. Quatre passages : corpus entier,
      sans les six enseignes signalées, États-Unis, Europe. Chaque passage produit un CSV de
      coefficients, un fichier `summary` statsmodels, un CSV de croisements, un CSV et un
      graphique de calibration.
- [x] **L'âge entre comme variable de contrôle**, `log_age_vague1`. Le découpage du corpus selon
      l'âge est rendu impossible dans le script, à la demande de Romain. Sans l'âge, « avoir une
      réponse » ressortait protecteur alors que c'était l'âge déguisé. Valeur versionnée avec
      l'âge : **×1,018, p = 0,906** (`2026-09-14-sorties-07/07_coefficients_tous.csv`).
      *Corrigé le 2026-09-14 : ce point portait « ×0,79 à ×0,93, p = 0,649 ». Aucune de ces
      valeurs n'existe dans un fichier de sortie.*
- [x] **AUC 0,862** sur des établissements jamais vus, contre 0,717 sans l'âge. L'écart mesure ce
      que l'âge apportait au classement. Calibration suivie sur les dix tranches.
- [x] **Sous-échantillonnage retiré** (`TAUX_ECHANTILLON_NEGATIFS = 1.0`). Le modèle tourne sur
      les 225 757 avis en 8 à 11 secondes. Les deux fichiers de sortie donnent désormais la même
      constante, −6,7126. La mécanique de correction reste dans le code, documentée.
- [x] **Référence des notes : 5 étoiles**, la cellule la plus fournie (1 850 suppressions contre
      26 pour 3 étoiles). Le CSV porte en plus `risque_relatif_vs_3_etoiles`, qui rejoue la
      comparaison depuis l'avis neutre sans faire reposer l'estimation sur une cellule fine.
- [x] **Garde-fous contre les coefficients qui divergent** : colonne écartée sous 30 cas ou
      5 suppressions, avertissement si une catégorie de référence est trop fine. Écrits après un
      passage où trois variables sortaient à 10^8 et 10^10 sur le sous-corpus américain.
- [x] Ajouté `region`, `chaine_antiparasitaire_us` et `salle_de_sport_attaquee` à `sql/02`, pour
      relancer les modèles par région et sans les enseignes signalées, d'une clause `WHERE`.

### Résultats, quatre passages

**Tableau refait le 2026-09-14 depuis les CSV de `2026-09-14-sorties-07/`.** La version
précédente portait six valeurs qui ne correspondaient à aucun fichier versionné — rafale ×9,21,
1 étoile ×6,17, home_services ×5,69, auteur sans niveau ×2,51, américain ×2,13, 4 étoiles ×0,60.
Elles venaient d'un passage non conservé ; le dossier `sorties/` est vide. Les AUC, elles,
coïncidaient. Seuls les CSV font foi, puisqu'ils sont les seuls régénérables.

| | Tout | Sans les 6 enseignes | US | Europe |
|---|---|---|---|---|
| Avis | 225 757 | 210 670 | 127 813 | 97 944 |
| Suppressions | 2 595 | 1 576 | 1 851 | 744 |
| AUC | 0,862 | 0,819 | 0,843 | 0,819 |
| Rafale d'auteur | ×9,54 | ×5,28 | **×49,30** | ×0,90 |
| Avis 1 étoile | ×6,34 | ×3,56 | ×2,41 | ×12,54 |
| Secteur home_services | ×5,73 | ×3,16 | ×4,79 | ×1,24 |
| Auteur sans niveau Local Guide | ×2,30 | ×2,51 | ×1,83 | ×3,73 |
| Établissement américain | ×1,99 | ×2,14 | — | — |
| Avis 4 étoiles | ×0,62 | ×0,68 | ×0,60 | ×0,82 |

Le profil d'auteur est le seul effet qui **se renforce** quand on retire les six enseignes
signalées. La rafale d'auteur reste un phénomène américain, porté par Insight Pest Solutions.

**Le coefficient de rafale s'exprime par point de logarithme et n'est pas lisible tel quel.**
Traduit en nombre d'avis déposés le même jour par le même auteur : passer de 1 à 2 avis vaut
×2,50 sur `tous` et ×4,86 aux États-Unis ; passer de 1 à 4 avis vaut ×7,90 et ×35,57. Les
effectifs sont minces : 1 681 avis à 2 dépôts ou plus sur 225 757, et la cellule « 4 avis le
même jour » porte 44 des 2 595 suppressions. Ces 44 sont **entièrement** dans les enseignes
signalées : une fois celles-ci retirées, la cellule compte 56 avis et 0 suppression.

**Ne tiennent pas :** la réponse du commerçant (**×1,018, p = 0,906**), la longueur du texte
(voir la réserve ci-dessous), la langue minoritaire (×1,011, p = 0,952).

**Réserve sur la longueur du texte, relevée le 2026-09-14.** « Ne tient pas » vaut pour le
passage `tous` (×0,66, p = 0,069 sur la tranche 201+). Sans les six enseignes, le même effet
sort à **×1,38, p = 0,010** : le signe s'inverse et devient net. Les taux bruts disent la même
chose — la colonne est plate sur le corpus entier et croissante sans les enseignes (52,3 → 94,2
suppressions pour 10 000 avis). C'est le seul effet du panel dont le signe s'inverse de façon
significative. À examiner avant toute publication.

### Découverte : quatre chaînes antiparasitaires américaines

- [x] **692 suppressions, dont 673 sur des avis 4 ou 5 étoiles**, soit 26,7 % des suppressions du
      panel. EcoShield, Insight Pest, Pointe Pest Control, Bulwark. Détail dans `../CLAUDE.md`,
      Conventions de Restitution point 5.
- [x] **Aucune caractéristique disponible ne les explique.** Auteurs ordinaires (87,1 % de guides
      établis parmi les supprimés, même niveau moyen que les survivants), textes tous différents
      (3,6 % de répétition), pas de pic d'afflux (ratio médian 1,95 contre 3,88 ailleurs).
- [x] **Le motif est général, pas propre à ce secteur.** Taxonomie bâtie sur tout le panel :
      **114 fiches perdent leurs avis positifs et portent 63,2 % des suppressions**, réparties
      sur les 7 secteurs et 2 régions. 15 fiches nettoient des avis négatifs (16,4 %). Portes de
      garage, restaurant japonais, montgolfières, cardiologie, hôtel espagnol, salle de sport
      allemande.
- [x] **Elles restent dans le corpus** (décision de Romain). Les drapeaux permettent de relancer
      sans elles.

---

## Fait le 2026-09-13

### `sql/01_selection_panel.sql`

- [x] Trois colonnes sans information retirées : `is_update` (FALSE partout), `changed_fields`
      (vide partout), `local_guide` (simple seuil sur `local_guide_level` : 1 à 3 donne FALSE,
      4 à 10 donne TRUE).
- [x] Ajouté `ne_pendant_la_surveillance`, qui sépare les deux populations du panel :
      **210 509 avis déjà en ligne à la vague 1** (0,95 % supprimés) et **15 248 nés pendant la
      surveillance** (3,92 %). Les premiers n'ont jamais été observés pendant leurs premiers
      jours de vie.
- [x] Documenté ce que le filtre `COUNT(*) = 1` écarte, et pourquoi la décision est assumée.

### `sql/02_adding_features.sql` — quatre corrections de fond

- [x] **La réponse du commerçant est datée.** `reply_text IS NOT NULL` décrivait l'état au
      dernier passage du robot : un survivant avait eu 13 jours de plus pour recevoir une
      réponse qu'un avis supprimé au 3e jour. Trois colonnes remplacent l'ancienne, dont
      `reponse_avant_surveillance` (120 230 avis), figée avant le début du risque.
- [x] **Le profil d'auteur est arrêté à la veille de l'avis examiné.** Compter tous les avis d'un
      auteur revenait à juger son avis de mai avec des avis d'août. Réserve : 99,3 % de ces
      compteurs valent zéro, le corpus ne couvrant que 9 048 commerces.
- [x] **Le rythme habituel des fiches est gelé sur les 12 mois précédant la vague 1.** Il était
      calculé sur les 90 jours de la fenêtre, qui contiennent le pic lui-même : une attaque de
      100 avis gonflait la moyenne servant à la mesurer. Les fiches au ratio mécaniquement égal
      à 1 passent de **750 à 80**, et seuls 12 avis n'ont plus de rythme calculable.
- [x] **`langue_etrangere_au_pays` refaite** sur `concordance_pays_langue`, qui couvre 100 % des
      pays du panel. Elle comparait un code de langue à un code de pays, ce qui marquait 73,5 %
      des avis dont 71 % des américains parce que `en` n'est pas `us`. La proportion tombe à
      **12,8 %**. Toutes les langues du pays sont acceptées, quel que soit leur rang : le
      français en Belgique cesse d'être étranger (394 avis concernés).
- [x] Ajouté `langue_inconnue` : 61 338 avis, 27 % du panel, n'ont pas de langue détectée.
- [x] `COALESCE(reviewer_review_count, 0)` retiré : aucune valeur vide, et il transformerait un
      jour un « on ne sait pas » en « aucun avis », qui est un signal fort.
- [x] Les trois colonnes d'auteur qui se recouvraient remplacées par `situation_auteur`, à trois
      situations exclusives. Taux bruts : guide établi 0,95 %, niveau connu sans avis déclaré
      2,05 %, **aucun niveau 8,17 %**.
- [x] Ajouté `n_avis_meme_jour_auteur`, calculée sur tout le corpus. Taux brut : 1,12 % à un avis
      seul, 9,01 % à trois, **44,00 % à quatre**.
- [x] `QUALIFY ROW_NUMBER()` retiré : code mort depuis le filtre de `01`.

### Contrôles écrits

- [x] `sql/controle_A_suppressions_certaines_ecartees.sql` et
      `sql/controle_B_disparus_puis_revenus_ecartes.sql`, six requêtes, pour examiner un par un
      les 731 avis écartés par le filtre.

---

## Cadrage à valider avec Axel — avant de tirer des conclusions

- **Axel insiste sur la vélocité** : combien de temps un avis reste en ligne avant sa
  suppression. C'est exactement ce que mesurent `jours_en_ligne_avant_suppression` et
  `jours_sous_surveillance_avant_suppression` — utilisables comme résultat à présenter (« en
  moyenne, X jours en ligne »), pas comme variable d'entrée du modèle (voir la réserve
  ci-dessous). À garder au centre du rapport, même si le modèle de régression, lui, prédit un
  événement (supprimé ou non) et pas une durée.
- **Le périmètre pourrait se restreindre aux avis récents supprimés**, comme évoqué le
  2026-09-06 pour l'étude d'origine (voir `etude-exploratoire/CLAUDE.md` / son historique :
  périmètre décidé sur les avis de 30 jours ou moins). Romain doit valider ce cadrage avec Axel
  avant de lancer la régression logistique — les outils (table, script `statsmodels`) se
  construisent demain quel que soit ce choix, mais le périmètre exact des lignes à analyser
  reste ouvert jusqu'à cette validation.

---

## Fait le 2026-09-10

### Le critère « fiche attaquée » examiné sur la concentration des dépôts

- [x] **Les 4 fiches du critère n'ont jamais été vérifiées une par une.** La vérification
      documentée porte sur les 24 fiches de l'ancien critère des 5 %. Sur les 4 nouvelles, le
      seul commentaire écrit expliquait pourquoi elles apparaissent, pas pourquoi elles sont
      des attaques.
- [x] **Mesuré le pic de dépôt** (avis supprimés déposés le même jour civil, sur
      `reviews_features.parquet`, 4 747 suppressions, panel entier) :

      | Fiche | Suppressions | Jours de dépôt distincts | Étalement | Pic même jour |
      |---|---:|---:|---:|---:|
      | Boutique The Boxer Club Dr Castelo (ES) | 229 | 9 | 1 651 j | 112 |
      | The Boxer Club (ES) | 135 | 5 | 4 j | 55 |
      | MedVet Cleveland (US) | 11 | 8 | 24 j | 3 |
      | Fox Rent A Car Denver (US) | 10 | 7 | 1 210 j | 3 |

      Fox perd un avis 5 étoiles sans texte déposé le 24 avril 2023, supprimé après 1 207 jours
      en ligne. Sur les 114 fiches à 10 suppressions ou plus, il n'y a rien entre un pic de 8 et
      un pic de 55.
- [x] **Décidé d'ajouter une quatrième condition** : au moins 10 avis supprimés déposés le même
      jour civil, mesurée sur `created_at`. Seules les deux salles espagnoles restent classées
      attaquées. **Pas encore écrit dans le code.**
- [x] Corrigé deux erreurs de documentation : Fox Rent A Car est à 80 % à 1 étoile et non 100 %
      (`06_fiches_attaquees.csv` donne `part_1_etoile = 0.8`), et le troisième seuil se lit
      « écrits moins de 30 jours avant leur suppression », pas « depuis moins de 30 jours ».

### L'hypothèse de l'afflux d'avis est tranchée

- [x] `ratio_pic_journalier_fiche` — pour chaque avis, le nombre d'avis reçus par la fiche le
      jour du dépôt rapporté à sa moyenne quotidienne — sort à **+0,275 (p = 0,002)** dans le
      modèle complet et à **−0,024 (p = 0,72)** hors les 4 fiches attaquées, sur
      2 537 suppressions. L'effet apparent vient des fiches attaquées.
- [x] `velocity_30d`, côté exploratoire, ne montre rien non plus : 14,5 %, 15,2 %, 17,4 %,
      15,9 % de fiches touchées selon la tranche, sans gradient, et les trois modalités du
      modèle ont une fourchette qui contient 1.
- [x] Les deux variables n'ont jamais été mises dans le même modèle, et rien ne trace une
      décision de ne pas le faire : chacune n'existe que d'un côté — `velocity_30d` en DuckDB
      (`build_tables.py:261`), `ratio_pic_journalier_fiche` en BigQuery
      (`sql/04_avis_features-v3.sql:159`) — et le point 3.B de `../CLAUDE.md` interdit de
      dupliquer une logique d'un moteur à l'autre. Les deux mesures répondent déjà la même
      chose séparément.

### Analyse A relancée après correction des scripts

- [x] `build_tables.py` puis `analysis_a.py` relancés. Le ×5,872 sur le nombre d'avis récents
      au-delà de 150 est reconduit à l'identique, fourchette **2,519 à 13,69**, et les
      396 fiches touchées se retrouvent dans la table reconstruite.
- [x] L'effet est mécanique : la tranche de référence (25 à 60 avis récents, médiane 37) donne
      un risque de 0,58 % par avis ; appliqué à une fiche de 202 avis récents, ce même risque
      prédit un rapport de cotes de 9,3, et on en mesure 5,9. Il n'y a pas d'écart résiduel
      qu'un ciblage des grosses fiches par Google serait nécessaire pour expliquer.
- [x] Le chemin de sortie de `analysis_a.py` était relatif à `etude-exploratoire/` alors que la
      table se lit depuis la racine ; corrigé.

### Divers

- [x] Écrit la requête BigQuery de concordance pays → langues qui doit corriger
      `langue_etrangere_au_pays` : 41 pays, 44 couples pays × langue, trois langues pour la
      Suisse, deux pour la Belgique. **Reste à exécuter et à joindre au calcul de la variable.**
- [x] Les sorties du tirage du 2026-09-09 ont été rangées dans `2026-09-10-sorties/`. Le
      dossier `sorties/` est vide en attendant le prochain tirage, qui le remplira à nouveau —
      les chemins cités dans `PASSATION.md` pointent vers ce dossier vide.

### À faire, dans l'ordre

- [ ] Écrire la condition de concentration : constante et condition dans
      `etude-exploratoire/scripts/suppressions_corrigees.py`, colonne
      `n_deleted_pic_journalier` dans `build_tables.py`, même condition dans la requête
      `SQL_FICHES_ATTAQUEES` de `06_statsmodels_analysis_review_claude.py` — qui devra joindre
      `reviews` pour lire `created_at`, ce qui change son coût de lecture. Les seuils sont
      déclarés deux fois et se modifient ensemble.
- [ ] Relancer le modèle de robustesse sur 2 fiches retirées au lieu de 4, et produire la table
      avant / après des coefficients.
- [ ] Trancher le périmètre d'âge : 90 jours aujourd'hui, 242 081 avis et 3 006 suppressions ;
      120 jours en donnent 305 042 et 3 070 ; 180 jours 417 552 et 3 151. Passer à 180 ajoute
      72 % d'avis pour 4,8 % de suppressions. Changer `AGE_MAX_PREMIERE_VAGUE` ne suffit pas :
      la dernière tranche d'âge est ouverte et deviendrait dominante, le commentaire de la
      ligne 142 devient faux, et les noms de fichiers de sortie sont fixes, donc le tirage
      écraserait les résultats à 90 jours cités ici.
- [ ] Écrire une règle de verdict chiffrée pour le test de robustesse de la régression. Elle
      existe côté exploratoire (`documentations/2026-09-06-controle-robustesse.md`) — ne tient
      pas, fragile, à surveiller, tient — et pas côté régression, où la comparaison des deux
      colonnes se fait à l'œil.

## Fait le 2026-09-09

### Table de panel : deux défauts de construction corrigés

- [x] **`avis_panel_final` comptait 766 suppressions deux fois.** 5 503 lignes à `deleted = 1`
      pour 4 737 avis réellement supprimés. Cause : `05_panel_final-v2.sql` joignait `reviews`
      et `avis_features`, deux tables non dédoublonnées, donc chaque avis disparu puis revenu
      sortait multiplié par 4 à chaque vague. Corrigé par `sql/04_avis_features-v3.sql` et
      `sql/05_panel_final-v3.sql`, exécutés le 2026-09-09. Contrôle après exécution :
      63 148 730 lignes pour autant de couples (avis, vague), et 4 737 lignes supprimées.
- [x] **Fuite de données du futur sur la rafale d'auteur.** La ligne en double vient de la
      disparition de l'avis, et elle était comptée dans les avis du même auteur le même jour.
      Sur les 602 avis concernés, 229 sont supprimés — 38 %, contre 0,1 % dans le corpus. Après
      correction, l'effet passe de ×7,2 à ×3,9 pour un auteur qui poste 3 avis le même jour.
- [x] Ajouté `author_key` à `avis_features`, nécessaire au découpage entraînement / test par
      auteur exigé par les Conventions de Restitution.

### Programme statsmodels

- [x] **Écrit `06_statsmodels_analysis_review_claude.py`.** Périmètre : les avis de moins de
      3 mois à leur première vague, 239 491 avis et 2 894 267 lignes avis-vague, chargés en
      351 Mo au lieu des 20 Go que demandait le `SELECT *` initial.
- [x] Retiré le repli qui fabriquait 15 000 lignes aléatoires quand BigQuery ne répondait pas,
      et imprimait des coefficients d'allure crédible. Le script s'arrête maintenant.
- [x] GLM binomial, marges d'incertitude groupées par établissement, sous-échantillonnage des
      négatifs à 5 % avec correction de la constante **et** des probabilités prédites.
- [x] Variables qui se recouvraient, recombinées : `rc_zero` / `lg_level_missing` /
      `new_account` en une variable à quatre situations exclusives, `has_text` /
      `log_text_chars` en tranches de longueur. Avant, `new_account` sortait à ×0,49 — un signe
      négatif pour une caractéristique qui augmente le risque.
- [x] AUC 0,884 sur des établissements jamais vus, calibration juste sur les dix tranches.

### Résultats

- 44 % des 2 919 suppressions du périmètre frappent un avis 4 ou 5 étoiles, rédigé, isolé, écrit
  par un compte établi. **C'est le chiffre pour Axel.**
- Le pic est entre 4 et 7 jours, pas au dépôt. Six suppressions sur dix tombent entre le 4e et
  le 14e jour.
- Un avis 5 étoiles passe de 14,2 à 71,3 suppressions pour 10 000 lignes avis-vague entre
  0-3 jours et 4-7 jours.
- Réponse du commerçant ×0,68, et ×0,63 sans les fiches attaquées : le seul effet qui se
  renforce quand on les retire.
- Secteur home_services ×5,17. L'étude exploratoire trouve ×3,94 de son côté.

### À ne pas citer

- [ ] **`langue_etrangere_au_pays` est défectueuse.** Elle compare un code de langue à un code
      de pays : 71 % des avis américains sont comptés « étrangers » parce que `en` n'est pas
      `us`, 60 % des autrichiens parce que `de` n'est pas `at`. Son ×2,15 mesure
      « établissement américain ». À reconstruire avec une table pays -> langues officielles.
- [ ] **Ajouter `country` comme variable à part entière.** Aucune variable de pays n'entre dans
      le modèle, donc l'effet pays se réfugie dans la variable de langue.
- [ ] La protection du texte long ne tient pas : ×0,50 dans le modèle complet, ×0,74 sans les
      fiches attaquées. Les faux avis sont courts et supprimés, ce qui fait paraître le texte
      court risqué.

## Fait le 2026-09-07

- [x] Repéré que `deleted_detected_at` seul surcompte les suppressions : 509 avis sur 5 230
      disparaissent puis reviennent (voir `etude-exploratoire/BACKLOG.md`, même défaut déjà
      signalé côté ancienne étude).
- [x] Identifié 24 de ces 509 comme un bug de collecte confirmé : même auteur, même note, même
      date de dépôt, texte totalement différent — une modification d'avis mal cataloguée comme
      suppression + retour, pas une vraie suppression.
- [x] Mesuré la durée d'absence des 471 autres avis ressuscités : 71 % sont absents un seul
      jour. Décidé un seuil à 2 jours : absent 1 jour = raté de collecte (jamais compté
      supprimé) ; absent 2 jours ou plus = vraie suppression, comptée à sa première disparition.
- [x] Construit `client-divers.reviewflowz.avis_deleted_panel` en BigQuery : une ligne par avis
      et par vague où il est vivant, `deleted` à 1 la seule vague où il est vu supprimé, jamais
      avant, jamais après. Requêtes dans `logistic-regression-study/sql/`.
- [x] Ajouté deux colonnes de vélocité : jours en ligne avant suppression (depuis la vraie date
      de dépôt) et jours sous surveillance avant suppression (depuis le premier passage de notre
      robot). **Ce sont des statistiques descriptives du rapport, pas des variables d'entrée du
      modèle** — voir la réserve ci-dessous.
- [x] Décidé l'outillage : la table est construite et corrigée uniquement en BigQuery. Pas de
      version dupliquée en DuckDB ou pandas — un seul endroit où corriger, sinon les versions
      divergent avec le temps (exactement le défaut qui a rendu l'ancienne étude peu fiable).
      Le tableau part ensuite en pandas via le client BigQuery officiel, et la régression tourne
      avec `statsmodels` — cette librairie affiche directement les coefficients et leur marge
      d'incertitude, ce que `scikit-learn` ne fait pas sans travail supplémentaire.
- [x] Renommé l'ancien dossier `quick-study` en `etude-exploratoire` : son contenu a pris un
      dimanche entier mais aucun résultat n'est valable — l'étude a été menée sans vérification
      préalable des données, avec des changements de définition en cours de route. Sa
      méthodologie reste une référence, ses chiffres sont à reprendre depuis cette nouvelle étude.

## Réserve à garder en tête

**`jours_en_ligne_avant_suppression` et `jours_sous_surveillance_avant_suppression` ne sont pas
des caractéristiques utilisables dans la régression.** On ne les connaît que pour un avis déjà
supprimé — les utiliser comme variable d'entrée reviendrait à prédire un événement avec une
information qu'on n'a qu'après qu'il s'est produit. Elles servent à décrire les avis supprimés
dans le rapport (« en moyenne, X jours en ligne avant suppression »), pas à nourrir le modèle.
La variable de temps qui remplace ça dans le modèle est l'âge de l'avis à chaque vague
(`age_days`, déjà calculé dans l'ancienne étude) : elle est connue à l'avance, quelle que soit
l'issue.

## À faire — au 2026-09-14

### 1. Répondre à la question du client d'Axel : répondre vite protège-t-il ? — FAIT

**Lancé le 2026-09-14. Résultat dans `2026-09-14-effet-reponse-commercant.md`.**

**Oui, hors des quatre chaînes antiparasitaires : ×0,56 [0,37 – 0,85], p = 0,007.** Sur le
corpus complet l'effet n'est pas mesurable, ×0,79 [0,53 – 1,16], p = 0,232. Annoncer le ×0,56
sans dire qu'il exclut ces quatre chaînes serait faux.

Les chaînes pèsent 1 021 avis sur 15 193 (6,7 %) et 189 des 505 suppressions (37,4 %). Chez
elles la part d'avis répondus est la même qu'ailleurs (38,0 % contre 39,5 %), donc la réponse
n'y marque rien et tire l'effet moyen vers 1.

**L'effet tient sur quatre jalons** — fin du jour 1, 2, 3 et 4, fenêtre se terminant chaque fois
au 8e jour : ×0,59 / ×0,56 / ×0,46 / ×0,48 sans les chaînes, tous avec une fourchette qui exclut
1 (p de 0,001 à 0,009) ; ×0,86 / ×0,79 / ×0,70 / ×0,71 sur le corpus complet, tous contenant 1.
Le résultat ne dépend pas du seuil choisi, il dépend du retrait des chaînes.

**Les trois chiffres du BACKLOG sont confirmés par BigQuery**, à un arrondi près : 15 193 avis
au jalon (exact), 505 suppressions (exact), et 5 992 avis avec réponse au jalon au lieu des
6 000 annoncés. Les 6 000 comptaient sur les 15 248 avis avant le filtrage au jalon ; 8 d'entre
eux ont disparu avant.

Deux fichiers :

| Fichier | Rôle |
|---|---|
| `sql/controle_C_reponses_au_jalon.sql` | **à lancer en premier**, lecture seule. Sort les effectifs du croisement et la répartition des délais de réponse |
| `08_effet_reponse_commercant.py` | le modèle. `--jalon-jours` (défaut 2), `--fenetre-jours` (défaut 6), `--sans-enseignes-signalees` |

Montage retenu — cohorte à jalon fixe, sur les **15 248 avis nés pendant la surveillance**,
seuls avis dont on a vu les premiers jours :

- garder les avis encore en ligne à la fin du 2e jour : **15 193 sur 15 248** ;
- caractéristique : une réponse était là au jalon — **6 000 avis, 39 %** ;
- cible : suppression entre le 3e et le 8e jour — **505 suppressions**.

Tout le monde est vivant au jalon, la réponse est connue au jalon, la suppression est comptée
après. L'âge n'entre donc pas dans ce modèle : tous les avis ont le même âge au jalon et la
même durée d'exposition ensuite. C'est la différence avec `07`, où `log_age_vague1` est
indispensable.

Le seuil de 2 jours est un choix : 64 % des réponses arrivent dans les 24 h, 80 % dans les
3 jours. La requête 3 du contrôle C sort la répartition complète pour en juger.

**Réserve de puissance, mesurée.** Sur 14 170 avis et 316 suppressions, le montage ne repérait
qu'une protection d'au moins 45 % ou une aggravation d'au moins 83 %. L'effet trouvé (44 % de
protection) est donc tout juste au-dessus de ce que ce corpus permet de voir. Le script imprime
cet effet minimal détectable à chaque passage.

**Ce que le résultat ne dit pas.** Le sens de la causalité n'est pas établi : le commerçant qui
répond en deux jours est aussi celui qui surveille sa fiche et signale les avis qu'il juge
illégitimes. Le modèle contrôle secteur, région, taille de fiche, note et profil d'auteur, pas
l'attention portée à la fiche. Et une réponse retirée reste invisible dans l'export.

Contrôles de mécanique passés le 2026-09-14 sur données fabriquées, avant l'accès BigQuery :
aucun avis supprimé avant le jalon ne reste dans le corpus, la cible ne déborde pas de la
fenêtre, une suppression tardive n'y entre pas, une réponse absente ou tardive n'est jamais
comptée au jalon, et le garde-fou qui refuse une fenêtre dépassant le 8e jour se déclenche.

### 2. Les quatre transformations faites en Python, à remonter dans `sql/02`

Décision du 2026-09-14 : elles restent en Python tant que les seuils bougent.

| Colonne | Ce que c'est |
|---|---|
| `taille_texte` | `text_chars` découpé en 4 tranches |
| `log_burst` | logarithme de `n_avis_meme_jour_auteur` |
| `secteur` | `industry`, secteurs sous 1 % regroupés en « autres » |
| `log_age_vague1` | logarithme de `age_a_la_vague1_j` |

Le défaut connu : quelqu'un qui lit `sql/02` ne saura pas que les secteurs rares sont regroupés
ni où sont coupées les tranches de texte. C'est le même défaut que celui corrigé ailleurs dans
le projet pour la règle de suppression et pour la règle de fiche attaquée.

### 3. Le motif du prénom, laissé ouvert

Les textes supprimés des chaînes antiparasitaires **nomment très souvent un technicien** : sur
12 textes tirés au hasard, « Ian Anderson » revient 4 fois, plus Devin, Jake, Tristan, Tristin,
Elizabeth. Hors de ces chaînes, environ la moitié des textes supprimés nomment quelqu'un.

**Rien n'a été construit, volontairement.** Une caractéristique taillée sur ces chaînes serait
ajustée sur 88 des 114 fiches concernées, exactement le biais signalé par Romain. La piste à
suivre serait la **répétition d'un même prénom sur les avis d'une fiche**, construite sans
regarder les chaînes, puis testée hors d'elles.

### 4. Les six enseignes signalées, à surveiller dans chaque restitution

Elles portent **39,3 % des suppressions du panel**. Tout chiffre présenté à Axel doit être
accompagné de sa version sans elles. `07_regression_panel.py --sans-enseignes-signalees` le
fait en une commande.

### 5. Chercher des effets cumulés

Seulement après avoir compris les effets isolés. Exemple : un avis sans texte, posté en rafale,
sur une fiche à fort afflux, cumule-t-il un risque plus élevé que la somme des trois effets ?

### Écarté, sans élément nouveau

- **Avis contenant un lien** : zéro suppression observée dans l'étude exploratoire, filtré par
  Google avant la mise en ligne.
- **Effet « avis modifié »** : non mesurable sur ce panel, le filtre `COUNT(*) = 1` écarte les
  543 avis édités de la fenêtre. Accepté par Romain le 2026-09-13.
- **Caractéristiques de campagne d'auteur** (même enseigne, note uniforme, même secteur) :
  testées le 2026-09-13, elles ne séparent rien. Capfun a déposé 12 avis 5 étoiles le même jour
  sur 12 campings d'une même chaîne, deux jours avant la vague 1, et aucun n'a été supprimé.
