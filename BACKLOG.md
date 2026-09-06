# Backlog — Analyse suppressions d'avis Google

Jalon livrable : **2026-09-15**. Dernière mise à jour : 2026-09-06.

Légende : `[ ]` à faire · `[~]` en cours · `[x]` fait · `[!]` bloqué / en attente

---

## En attente de Romain

- [~] **Vérif 2 — champs Local Guide vides sur les avis récents.**
  Fichier `data/verif_local_guide_null_recents.csv`, 30 liens (20 cas, 10 témoins).
  Question : sur les avis apparus pendant le suivi, le niveau est-il réellement absent du profil,
  ou le crawler ne l'a-t-il pas capté aux vagues 2-14 ?
  Enjeu : le taux de champs vides passe de 0,26 % (stock vague 1) à 7-9 % (flux) — écart trop net
  pour être ignoré. Non bloquant : à défaut, la strate récente est traitée à part et documentée
  comme réserve.

- [ ] **Arbitrage : maille de l'âge dans le modèle.** Spline continue (plus juste) ou paliers
  (plus communicable). Recommandation : spline pour l'estimation, paliers pour le livrable.

---

## Socle — à faire avant tout le reste

---

## Les deux analyses

- [x] **Analyse A — quel établissement subit une intervention.** `scripts/analysis_a.py` →
  `documentations/2026-09-06-analyse-a-quel-etablissement.md`.
  Deux modèles séparés : être touché (2 529 fiches d'au moins 10 avis récents, 455 touchées) et
  ampleur de la purge (455 fiches, pondéré par le stock récent). Erreurs-types groupées par
  marché (pays × secteur), faute d'identifiant d'enseigne dans l'export.
  **Résultat principal : la vitesse de collecte n'a aucun effet propre.** Le ×26 brut disparaît
  entièrement une fois le nombre d'avis récents pris en compte — c'était de l'exposition, pas une
  sanction. L'hypothèse de détection de campagne au niveau de la fiche n'est pas soutenue.
  Tiennent : services à domicile ×3,0, sport et bien-être ×1,5, États-Unis ×1,4.
  Ne tiennent pas : taille du groupe, volume total d'avis, note moyenne.
  Sur l'ampleur : les fiches de moins de 100 avis perdent ×6,5 plus de leur stock que les
  moyennes, celles de plus de 1 000 avis ×0,45. **Une intervention est un événement grave pour un
  indépendant, un incident pour une chaîne.**

- [~] **Analyse B — quel avis tombe dans une fiche touchée.** `scripts/analysis_b.py`.
  Effets calculés (26 modalités, `data/resultats/analyse_b_effets.csv`). **Marges d'erreur en
  cours** : rééchantillonnage des établissements, ~65 min, lancé détaché
  (log `data/resultats/analyse_b_run.log`).
  Périmètre : 584 fiches, 64 442 observations, 2 828 disparitions comparables sur 2 853.
  Comparaison faite avec une méthode plus rapide (indicatrices de strate + erreurs-types
  groupées) : coefficients concordants sauf la rafale, surestimée à 26 contre 19 — biais connu
  quand les groupes sont petits. La méthode conditionnelle est conservée.

- [ ] **Contrôle de robustesse.** Relancer A et B sans les 39 fiches à plus de 5 % de purge.
  Obligatoire, pas optionnel : ces fiches portent 19,5 % des suppressions.

---

## Tests ciblés — ce qui porte l'angle du livrable

- [ ] **Trancher la langue étrangère.** Le niveau 1 la donne protectrice (×0,56), à l'inverse de
  l'hypothèse « discordance de provenance » du cadrage. Soit Google y voit un signal de visite
  réelle, soit c'est un effet de secteur (`hospitality` concentre les avis touristiques et est
  peu supprimé). Le modèle B, qui neutralise la fiche, tranche. **Ne pas communiquer avant.**

- [ ] **Instruire l'effet d'édition (×1,7).** Un avis modifié après publication est plus
  supprimé. Non prévu au cadrage, facile à tester, actionnable côté conseil.

- [ ] **Confirmer l'effet de la réponse du propriétaire.** Protectrice au niveau 1 (×0,86) après
  retournement du signe. Seul levier directement actionnable par le client, donc à valider dans
  le modèle B avant d'en faire une recommandation. Vérifier l'antériorité `reply_date` vs
  `deleted_detected_at` pour écarter l'inversion causale.

- [x] **Test 1 — la vélocité, nette de l'exposition. Tranché : l'effet n'existe pas.**
  Traité dans l'analyse A. Les fiches recevant plus de 10 % de leur stock en 30 jours ne sont pas
  plus souvent touchées (×0,50, fourchette 0,25 à 1,03). Le ×26 brut mesurait le fait qu'une
  fiche à fort afflux a simplement plus d'avis récents à perdre.
  Pour le livrable : **Google ne sanctionne pas une fiche parce qu'elle reçoit un afflux
  d'avis.** Ce qui est sanctionné, c'est le comportement de l'auteur (la rafale, analyse B).

- [ ] **Test 2 — débordement sur l'organique.** Dans les fiches à forte vélocité, le stock ancien
  (plus de 12 mois) est-il davantage supprimé que dans des fiches témoins appariées sur secteur,
  taille, pays et volume ? **C'est la mesure de faux positifs la plus directe que ce jeu de
  données permette.** Priorité haute pour le livrable.
  Note : ce test **utilise** le stock ancien comme grandeur mesurée. Le recentrage sur les avis
  frais porte sur la question « qu'est-ce qui fait supprimer un avis », pas sur les données.

- [ ] **Test 3 — vérification de la visite, sur `home_services`.** Via `author_id` : à l'intérieur
  d'une même fiche, comparer les auteurs dont l'empreinte pays coïncide avec celle de la fiche à
  ceux dont elle diverge. Réserve : défini sur 5,2 % du corpus seulement, maille pays grossière,
  conclura probablement sur un intervalle large. À tenter, à ne pas promettre.

- [ ] **Vérif hypothèse insultes** (point ouvert du plan de travail §6). Sur les 3,17 M de textes
  non vides. Quel que soit le résultat, trop rare pour entrer au modèle : c'est une observation
  de livrable.

---

## Optionnel — si le temps le permet

- [!] **Machine learning en contrôle. Suspendu — fait tomber VSCode.** `scripts/machine_learning.py`.
  Trois modèles (logistique, forêt aléatoire, gradient boosting), deux passages : tout le panel
  puis sans les 24 fiches purgées. Découpage par établissement et par auteur, évaluation en AUC
  et précision moyenne, importance par permutation.
  La machine a 7 Go de RAM et le script la saturait. Rendu inoffensif depuis, non relancé :
  gradient boosting seul par défaut (la forêt aléatoire passe derrière `--avec-foret`),
  matrices en float32, option `--echantillon N`, plafond mémoire DuckDB à 1 Go.
  **À relancer détaché quand la machine est libre**, jamais en même temps qu'un autre calcul.
- [ ] Mention d'un employé par NER. Coût : une passe sur 3,2 M de textes pour un signal non
  mesuré. À décider après les résultats du niveau 2.

---

## Fait

- [x] **2026-09-06 — Plafond mémoire à 1 Go sur toutes les requêtes DuckDB.** La machine a 7 Go ;
  deux calculs lourds simultanés l'ont saturée et fait tomber l'éditeur. Note : `ulimit -v` est
  inutilisable ici, DuckDB réserve un large espace d'adressage virtuel et refuse de démarrer.

- [x] **2026-09-06 — Le projet devient exploitable en dehors de la session.**
  `pyproject.toml` et `uv.lock` renseignés (les dépendances n'étaient pas déclarées), `README.md`
  écrit, `main.py` du gabarit supprimé.
  - `scripts/query.py` — interroger les tables en SQL, sans écrire de code. `--tables`,
    `--colonnes`, `--exemples`, `--csv`, ou console interactive.
  - `explore.py` — cellules `# %%` pour charger les tables dans Data Wrangler sous VS Code.
  - Les résultats chiffrés sortent aussi en CSV dans `data/resultats/`.

- [x] **2026-09-06 — Seuil « fiche purgée » corrigé.** Il ne comportait qu'une part (plus de 5 %
  des avis), sans plancher en volume : une fiche de 2 avis dont 1 supprimé comptait comme
  « purgée à 50 % ». 7 des 37 fiches étaient dans ce cas. Plancher de 10 suppressions ajouté,
  on passe à **24 fiches**, 958 suppressions, 18 % du total.
  Liste exportée : `data/resultats/fiches_massivement_purgees.csv`.
  Deux familles distinctes s'y lisent : purges d'avis **récents** (salles de sport espagnoles,
  note en forte hausse, gros flux récent — signature de campagne) et purges d'avis **anciens**
  sur des fiches dormantes en Europe (0 % d'avis reçus en 30 jours). La seconde famille est la
  matière du Test 2.

- [x] **2026-09-06 — Bug corrigé dans `build_tables.py` : `died` valait NULL au lieu de FALSE**
  pour les avis survivants. Les comptages restaient justes (`sum(died::INT)` ignore les NULL)
  mais la colonne était inutilisable pour la modélisation, et faussait le repérage des
  comparaisons exploitables : 1 809 disparitions retenues au lieu de 2 828. Contrôle ajouté.

- [x] **2026-09-06 — Colonne de contrôle systématique au niveau 1.** Chaque tableau donne
  désormais l'écart recalculé sans les 24 fiches purgées. Auparavant ce contrôle n'existait que
  sur trois facteurs, à côté, et n'était pas vérifiable.
  Il change trois conclusions : `wellness_fitness` s'effondre de ×6,1 à ×1,8 (deux salles de
  sport espagnoles portaient tout), l'écart 1 étoile / 4 étoiles passe de ×8,2 à ×4,6, et
  l'écart États-Unis / Europe **s'élargit** de ×1,7 à ×2,7.

- [x] **2026-09-06 — Niveau 1 : bivariés stratifiés sur l'âge.**
  `scripts/level1_bivariate.py` → `documentations/2026-09-06-premiers-resultats-facteur-par-facteur.md`.
  15 facteurs, risque par vague brut **et** standardisé sur l'âge, sur le périmètre frais
  (104 662 avis, 2 853 suppressions, 1 137 276 expositions).
  Effet le plus fort : **rafale auteur ×16,9** (plusieurs avis le même jour). Vérifié robuste
  après retrait des 5 fiches les plus purgées, et réparti sur 165 fiches.
  **Quatre résultats de la note du 04/09 sont renversés** par la standardisation et le
  recentrage : texte, longueur, photo et réponse du propriétaire changent de signe ou d'ordre
  de grandeur.
  Partie générée entre marqueurs `<!-- genere:level1 -->`, interprétation écrite à la main
  autour : un re-run ne l'efface pas (idempotence vérifiée).

- [x] **2026-09-06 — Tables d'analyse construites.** `scripts/build_tables.py`, 20 s d'exécution,
  sorties dans `data/build/` (gitignoré) :
  - `reviews_features.parquet` — 4 878 151 lignes, 1 par avis de base. **Corpus entier, stock
    ancien conservé.** Indicatrice `is_fresh` pour le périmètre de modélisation.
  - `business_features.parquet` — 9 048 établissements, dont 1 399 touchés. Support analyse A.
    Contient `velocity_30d`, `purge_share`, `heavy_purge`, trajectoire de note depuis `histograms`.
  - `fresh_hazard.parquet` — 1 137 276 lignes (avis frais × vague où il est vivant), cible `died`.
    Support analyse B en temps discret : gère la troncature à gauche et la censure à droite.
  Neuf contrôles de cohérence intégrés au script, tous au vert. Résultats connus reproduits à
  l'identique depuis les tables (courbe de risque, signature compte neuf, gradient de vélocité).
  Aucune colonne identifiante écrite : l'auteur est réduit à un hash md5, le texte à sa longueur.

- [x] **2026-09-06 — Périmètre arrêté : la modélisation cible les avis frais (≤ 30 j).**
  Justifié par la courbe de risque (pic à 7-13 j, effondrement ensuite). Taux 2,67 % contre
  0,107 % : le problème d'événement rare disparaît.
  **Le stock ancien reste dans les données** — ce qu'on ne cherche pas, c'est expliquer la
  suppression d'un avis *ancien*, sauf résultat pertinent. Il reste mobilisé pour le Test 2, les
  features d'établissement et les comparaisons. Décidé par Romain.
- [x] **2026-09-06 — Architecture arrêtée : deux analyses séparées** (A établissement,
  B avis à effets fixes). Décidé par Romain.
- [x] **2026-09-06 — Vérif 1, champs Local Guide vides sur le stock ancien.** 45 profils ouverts
  manuellement. Résultat : 45/45 vivants, séparation parfaite 30/30 sans niveau vs 15/15 avec.
  Ce ne sont ni des comptes suspendus, ni des comptes neufs (médiane 52 avis, remontent à 2012),
  et le profil reste public et normal — 28/30 affichent leur compteur d'avis, jusqu'à 652.
  Lecture principale : **comptes non inscrits au programme Local Guides**, qui est sur adhésion
  volontaire. Pas de confirmation directe côté Google, donc lecture principale et non fait établi.
  Conséquence : caractéristique légitime, antérieure à l'avis, elle entre au modèle. Et elle porte
  l'argument central du livrable — ne pas être inscrit au programme de contributeurs de Google
  multiplie par 16 à 19 le risque de suppression, à âge égal.
  Précaution : ces comptes publient plus que la moyenne (110 avis contre 43) — vérifier que
  l'effet tient à volume d'avis égal.

- [x] **2026-09-06 — `reviewer_review_count = 0` élucidé comme piège, pas comme facteur.**
  4,9 % du corpus. Ce n'est pas un compte sans avis : 3 656 auteurs annoncés à 0 ont 2 à 12 avis
  dans notre propre panel. Mécanisme inconnu, et indépendant du niveau Local Guide manquant.
  À âge égal l'effet disparaît complètement sauf sur les avis de moins de 30 jours — l'écart brut
  ×3,3 était purement un effet de composition par âge.
  Traitement retenu : valeur manquante avec indicatrice, **jamais un zéro numérique** (le
  logarithme prévu au plan de travail serait indéfini).
  Soulevé par Romain.

- [x] **2026-09-06 — Note de cadrage des facteurs et du programme d'analyse.**
  `documentations/2026-09-06-facteurs-et-programme-danalyse.md`.
- [x] **2026-09-06 — `.gitignore` créé.** `data/` était committable : 872 Mo et des données
  personnelles, alors que le README de l'export interdit la rediffusion. Rien n'avait été
  committé, pas de rattrapage d'historique nécessaire.

---

## Réserves à porter au livrable

Elles ne se lèvent pas par l'analyse, elles s'écrivent.

- Fenêtre de 14 jours : on capte les suppressions rapides, pas les révisions de stock à 6 mois,
  alors que le réentraînement rétroactif est le mécanisme des vagues observées en 2025.
- Le filtrage pré-publication est invisible par construction : toute conclusion porte sur les
  avis publiés puis supprimés, jamais sur ceux qui n'ont jamais paru.
- Vrais faux avis et faux positifs sont indistinguables par scraping. L'argument tient sur une
  inférence indirecte, pas sur une mesure.
- Le panel ne couvre pas les groupes de 2-3 ni de 11-19 sites : l'effet de taille s'interprète sur
  trois paliers, pas comme une courbe continue.
- 41 pays dont un seul hors Europe (US) : analyse géographique possible par région, pas par pays.
- Royaume-Uni hors panel : la comparaison des régimes juridiques se fait sans le pays du DMCC Act.
