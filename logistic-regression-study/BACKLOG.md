# Backlog — Étude régression logistique

Dernière mise à jour : 2026-09-09.

Légende : `[ ]` à faire · `[~]` en cours · `[x]` fait

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

## À faire — plan pour la prochaine séance

### 1. Finaliser la table de caractéristiques

Reprendre ce qui existe déjà dans `etude-exploratoire/scripts/build_tables.py` plutôt que
recalculer de zéro — la plupart des caractéristiques ci-dessous y sont déjà construites.

Caractéristiques retenues :
- note (`star`)
- longueur du texte (`has_text`, `text_chars`)
- photos (`n_photos`, `has_photo`)
- réponse du propriétaire (`has_reply`) — réserve connue : une réponse retirée après coup est
  invisible dans l'export
- nombre d'avis du critique (`reviewer_review_count`)
- statut et niveau Local Guide (`local_guide`, `local_guide_level`) — à vérifier avant de les
  lire séparément : le niveau n'est peut-être qu'une autre mesure du nombre d'avis du critique
- langue de l'avis (`language`)
- écart entre la langue de l'avis et la langue habituelle du magasin (`lang_off_modal` dans
  l'ancienne étude) — plus informatif qu'une langue de magasin, qui n'existe pas dans les
  données brutes (seul le pays y figure)
- plusieurs avis du même auteur le même jour (`author_same_day_burst`) — le résultat le plus
  solide de l'ancienne étude
- âge de l'avis à chaque vague (`age_days`) — facteur dominant, indispensable
- secteur, pays, taille du groupe — comme variables de contrôle, pas comme résultat

À construire :
- [ ] avis dont le texte contient un prénom — à documenter comme imparfait, comme le dictionnaire
      d'insultes de l'ancienne étude (couvre 7 langues sur 41 pays)

Écarté sans élément nouveau :
- avis contenant un lien : zéro suppression observée dans l'ancienne étude, filtré par Google
  avant la mise en ligne

### 2. Écrire le programme `statsmodels`

Script Python : lecture de `avis_deleted_panel` depuis BigQuery vers pandas, jointure avec les
caractéristiques du point 1, régression logistique avec `statsmodels`.

### 3. Vérifier la pertinence de chaque caractéristique avant le modèle complet

Reprendre la méthode de l'ancienne étude qui a bien fonctionné : un tableau croisé par
caractéristique, stratifié par âge, avant de faire confiance à un effet dans le modèle à
plusieurs variables. Objectif : écarter tout de suite une caractéristique qui ne montre rien en
bivarié, et comprendre celles qui montrent quelque chose avant de les combiner.

### 4. Chercher des effets cumulés

Une fois les effets isolés compris et validés à l'étape 3 — pas avant, pour éviter de chercher
des combinaisons sur du bruit. Exemple de question : un avis sans texte, posté en rafale, sur un
magasin à forte vélocité, cumule-t-il un risque plus élevé que la somme de ces trois effets pris
séparément ?
