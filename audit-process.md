# Audit du process d'analyse — méthode, pas résultats

Portée : les fichiers `.md` d'`etude-exploratoire/documentations/` qui contiennent une analyse,
un rapport de vérification ou une synthèse de résultats. Exclus : notes de cadrage sans résultat
(`selection-listing.md`, `methodologie.md`, `plan-de-travail.md`), fichiers de suivi
(`BACKLOG.md`, `PASSATION.md`, `INDEX.md`), `CLAUDE.md`, `README.md`.

Avertissement : plusieurs citations ci-dessous contiennent des chiffres. Ce sont des chiffres de
méthode (seuils, tailles d'échantillon, définitions), cités pour montrer un changement de règle —
pas des résultats à communiquer. Les chiffres issus de `documentations/legacy/` restent
soumis à l'interdiction de citation de `CLAUDE.md`.

---

## Étape 1 — Inventaire

| Fichier | Contenu daté du | Écrit / commité le | Statut (INDEX.md) |
|---|---|---|---|
| `legacy/2026-09-04-...premieres-observations...md` | 2026-09-04 | 2026-09-06 | Périmé |
| `2026-09-06-facteurs-et-programme-danalyse.md` | 2026-09-06 | 2026-09-06 | Mixte |
| `legacy/2026-09-06-premiers-resultats-facteur-par-facteur.md` | 2026-09-06 | 2026-09-06 | Périmé |
| `legacy/2026-09-06-analyse-a-quel-etablissement.md` | 2026-09-06 | 2026-09-06 | Périmé |
| `legacy/2026-09-06-analyse-b-quel-avis-tombe.md` | 2026-09-06 | 2026-09-06 | Périmé |
| `reviewflowz-analyse-google.md` | activité au 2026-08-31 | 2026-09-06 | Mixte |
| `reviewflowz-analyse-google-decisions.md` | décisions du 2026-09-04 | 2026-09-06 | Mixte |
| `2026-09-06-reprise-qualification-des-suppressions.md` | 2026-09-06 (frontmatter), contenu de jour 2 | 2026-09-07 | Mixte |
| `legacy/2026-09-06-enquete-fiches-purgees-et-plan.md` | idem | 2026-09-07 | Périmé |
| `legacy/2026-09-06-controle-robustesse.md` | idem | 2026-09-07 | Périmé |
| `legacy/2026-09-06-test2-debordement-organique.md` | idem | 2026-09-07 | Périmé |
| `legacy/2026-09-06-synthese-etat-et-resultats.md` | idem | 2026-09-07 | Périmé |
| `2026-09-06-trouvailles-et-loups.md` | idem | 2026-09-07 | Mixte |
| `2026-09-06-verif-contenu-textuel.md` | idem | 2026-09-07 | Mixte |
| `2026-09-06-verif-reponse-proprietaire.md` | idem | 2026-09-07 | Mixte |
| `2026-09-08-age-a-la-suppression.md` | 2026-09-08 | 2026-09-09 | À jour |
| `2026-09-08-cas-attaque-salles-de-sport.md` | 2026-09-08 | 2026-09-09 | À jour |
| `2026-09-08-histogramme-age-des-suppressions.md` | 2026-09-08 | 2026-09-09 | À jour |
| `2026-09-08-note-de-methodo.md` | 2026-09-08 | 2026-09-09 | À jour |
| `2026-09-08-synthese-de-la-journee.md` | 2026-09-08 | 2026-09-09 | À jour |

`panel-summary.md` est exclu de la suite : il décrit la construction du panel (échantillonnage
géographique), jamais une méthode de mesure de la suppression, et n'a pas bougé depuis le
2026-09-06.

Les dates « écrit / commité » viennent de `git log --follow`, pas des frontmatters (qui portent
souvent la date du début de journée de travail, pas celle de la rédaction réelle). Le lot du
2026-09-09 correspond au déplacement massif des fichiers dans la nouvelle arborescence, pas
nécessairement à une réécriture de leur contenu.

---

## Étape 2 — Méthode par fichier

Regroupés par vague de travail. Chiffres omis sauf quand un seuil ou une taille d'échantillon
fait partie de la méthode elle-même.

### Vague 1 — 2026-09-04, premier passage sur l'export

**`legacy/...premieres-observations...`**
- Entrée : `local/exports.zip`, lignes de base (`NOT is_update`).
- Étapes : comptages croisés bruts (note, texte, photo, auteur Local Guide oui/non) sur tout le
  corpus, tous âges mélangés.
- Hypothèses / cas particuliers : aucune correction d'âge. Le README du souci d'unicité
  (`review_id` non unique), de resignature des URL photo et de mise à jour anticipée de
  l'histogramme est noté mais pas encore traité par une règle de calcul.

### Vague 2a — 2026-09-06, premier modèle

**`2026-09-06-facteurs-et-programme-danalyse.md`**
- Entrée : mêmes fichiers de base + `histograms`.
- Étapes : construction d'un risque quotidien par tranche d'âge (avis observé à un passage,
  disparu ou non au suivant) ; recalcul de tout écart « à âge comparable » en repondérant chaque
  groupe comme s'il avait la même répartition d'âge que la référence ; recalcul « à composition
  comparable » (secteur, taille, pays) quand deux groupes comparés diffèrent aussi par autre
  chose que l'âge.
- Hypothèses / cas particuliers : périmètre resserré aux avis de moins de 30 jours (borne fixée
  au point où la courbe de risque s'aplatit) ; deux analyses séparées décidées (établissement vs
  avis) parce qu'un seul modèle apprendrait les fiches à purge massive plutôt que la règle
  générale ; variable Local Guide redéfinie en palier de niveau plutôt qu'en oui/non ; champs
  vides (niveau absent, compteur à 0) traités comme un état transitoire « compte tout neuf »
  plutôt que comme une catégorie brute.

**`legacy/2026-09-06-premiers-resultats-facteur-par-facteur.md`**
- Entrée : `fresh_hazard.parquet` (avis récents, un avis × un passage).
- Étapes : risque quotidien par facteur, brut puis à âge comparable ; colonne additionnelle
  recalculée hors les fiches ayant perdu plus de 5 % de leur stock (et au moins 10 suppressions).
- Hypothèses / cas particuliers : un facteur à la fois, donc deux facteurs corrélés se comptent
  double — les modèles A/B sont nécessaires pour trancher ; ligne signalée « trop peu pour
  conclure » sous 20 disparitions ; aucune marge d'erreur donnée à ce niveau.

**`legacy/2026-09-06-analyse-a-quel-etablissement.md`**
- Entrée : `business_features.parquet`.
- Étapes : deux régressions logistiques distinctes — « touché » (oui/non) et « ampleur » (part du
  stock perdu, parmi les touchés) — avec erreurs-types groupées par marché (pays × secteur, faute
  d'identifiant d'enseigne).
- Hypothèses / cas particuliers : fiches de moins de 10 avis récents écartées (l'état « touché »
  y relève du hasard) ; trajectoire de note exclue du modèle malgré un écart brut marqué, parce
  que la note bouge mécaniquement quand des avis sont supprimés (causalité inverse suspectée, pas
  tranchée).

**`legacy/2026-09-06-analyse-b-quel-avis-tombe.md`**
- Entrée : mêmes tables, restreintes aux fiches touchées.
- Étapes : régression logistique conditionnelle, comparant uniquement des avis d'une même fiche
  un même jour (secteur, pays, taille, politique de modération s'annulent automatiquement) ;
  marge d'erreur par rééchantillonnage des établissements (pas des lignes, pour ne pas traiter
  deux avis d'une même fiche comme deux informations indépendantes).
- Hypothèses / cas particuliers : les journées de purge totale (aucun survivant dans la fiche ce
  jour-là) sortent du calcul faute de comparaison possible ; secteur / région / taille ne peuvent
  pas être des variables ici puisqu'ils sont constants dans une fiche.

### Vague 2b — 2026-09-06/07, qualification et robustesse

**`2026-09-06-reprise-qualification-des-suppressions.md`**
- Étapes proposées (pas encore exécutées dans les autres fichiers de cette vague) : un programme
  `qualification_suppressions.py` répondant à sept questions dans l'ordre (Q1 catégoriser chaque
  suppression en Revenue / Douteuse-listing tronqué / Douteuse-compteur stable / Réelle ; Q2 à Q7
  décrire, qualifier, dater, dénombrer).
- Règle proposée pour Q1 : un avis dont l'identifiant réapparaît vivant sur la même fiche n'est
  pas une suppression, quel que soit le délai de réapparition.
- Cas particuliers identifiés : compteur public Google qui ne bouge pas alors que le listing
  perd des avis (signal le plus fort) ; listing lu sur moins de pages que d'habitude le même
  jour.

**`legacy/2026-09-06-enquete-fiches-purgees-et-plan.md`**
- Étapes : preuve en trois points pour qualifier un défaut de collecte (pages lues en moins ce
  jour-là, compteur Google immobile, contrôle de complétude du pipeline mis en défaut) ; deux
  hypothèses concurrentes testées et écartées (campagne ancienne rattrapée, comptes bannis) par
  recoupement des dates de publication et des autres avis des mêmes auteurs.
- Règle proposée (Priorité 1) : ajouter dans `build_tables.py` un marqueur `fausse_suppression`
  pour tout avis dont l'identifiant réapparaît vivant sur la même fiche, et l'exclure du comptage
  des suppressions.

**`legacy/2026-09-06-controle-robustesse.md`**
- Entrée : sorties des analyses A et B.
- Étapes : rejeu des deux modèles sans les fiches ayant perdu plus de 5 % de leur stock et au
  moins 10 avis ; verdict fixé avant lecture des chiffres, sur quatre catégories (ne tient pas /
  fragile / à surveiller / tient), selon que l'effet change de sens ou que son amplitude est
  divisée/multipliée par plus de 2.
- Cas particulier : un effet dont l'estimation devient dégénérée (division par une case à zéro
  observation) est classé « non exploitable », pas « ne tient pas ».

**`legacy/2026-09-06-test2-debordement-organique.md`**
- Entrée : avis créés plus de 365 jours avant la première vague et déjà présents à la vague 1
  (condition qui écarte la censure à droite : tous suivis sur les mêmes 13 intervalles).
- Étapes : groupement par part du stock reçue dans les 30 derniers jours ; taux recalculé « à
  marché comparable » (même répartition pays/secteur/taille/volume dans chaque groupe).
- Cas particulier : palier « 10 % et plus » écarté comme non exploitable sous un double critère
  — moins de 20 disparitions, ou moins de 60 % du poids des strates de marché couvert.

**`legacy/2026-09-06-synthese-etat-et-resultats.md`**
- Compile les sorties des programmes ci-dessus sans étape de calcul propre ; documente l'ordre de
  lancement des scripts et les règles de restitution (risque relatif, AUC/calibration jamais
  exactitude, split train/test par établissement et par auteur).

**`2026-09-06-trouvailles-et-loups.md`**
- Pas de calcul propre : reclasse chaque résultat déjà produit selon trois niveaux de fiabilité
  face au recomptage à venir (solide / à recalculer / invalidé), et liste les vérifications non
  faites (L1 à L15) par ordre de priorité pour la reprise.

**`2026-09-06-verif-contenu-textuel.md`**
- Entrée : `text`, sur les seules suppressions du périmètre récent.
- Étapes : onze marqueurs par expression régulière (insulte, lien, e-mail, téléphone, majuscules,
  ponctuation, répétition de caractère, texte court, charabia, symboles, vocabulaire publicitaire)
  ; comparaison du taux de marqueur entre supprimés et survivants, à âge comparable.
- Cas particulier : script n'écrit que des booléens dans sa sortie, jamais le texte lui-même
  (contrainte RGPD).

**`2026-09-06-verif-reponse-proprietaire.md`**
- Étapes : mesure du délai médian réponse/avis ; vérification que, sur les avis supprimés ayant
  une réponse, la réponse précède toujours la suppression (test de l'inversion causale) ; calcul
  de l'effet selon deux méthodes de comptage — réponse figée à l'état final du panel (méthode
  utilisée dans l'analyse B), contre réponse « datée », comptée seulement à partir du jour où
  elle existe vraiment.
- Cas particulier : l'export ne versionne pas les réponses retirées — seule leur présence/absence
  au dernier passage est connue, jamais un retrait en cours de suivi.

### Vague 3 — 2026-09-08, comptage corrigé

**`2026-09-08-note-de-methodo.md`**
- Étapes : implémente enfin une règle de qualification (différente de celle proposée en vague 2b,
  voir Étape 3-D1) dans `suppressions_corrigees.py`, seule copie hors BigQuery d'une logique
  définie dans `logistic-regression-study/sql/01_build_avis_deleted_panel.sql` ; vérifie que
  `created_at` est un horodatage réel (distribution horaire plausible, secondes non concentrées
  sur zéro) avant d'exclure l'hypothèse d'une date reconstruite.
- Cas particuliers : documente trois constructions écartées (cohorte glissante, matrice vague ×
  âge, exposition par âge) après avoir constaté que le nombre d'avis observés est quasi constant
  d'un âge à l'autre — rendant inutile toute pondération.

**`2026-09-08-age-a-la-suppression.md`**
- Entrée : corpus entier, comptage corrigé.
- Étapes : suppressions par âge en jours (1 à 30) ; pour distinguer un effet d'âge d'une purge
  ponctuelle sur un pic donné, trois contrôles systématiques — étalement sur les journées de
  suivi, étalement sur les établissements, tenue de l'écart après retrait des deux journées les
  plus chargées.
- Cas particulier : introduit et documente trois définitions concurrentes d'« avis récent
  supprimé » (codes D1/D2/D3), selon que l'âge de référence est celui à la suppression ou celui
  au premier passage, et selon la borne stricte ou large à 30 jours.

**`2026-09-08-histogramme-age-des-suppressions.md`**
- Étapes : même comptage, regroupé en tranches larges ; risque cumulé sur les 30 premiers jours
  obtenu en enchaînant les risques quotidiens jour par jour (pas une simple moyenne) ; contrôle de
  censure séparé, restreint aux avis déjà présents à la vague 1 pour neutraliser le biais des avis
  entrés en cours de suivi.

**`2026-09-08-cas-attaque-salles-de-sport.md`**
- Étapes : les deux fiches sont désormais traitées séparément, chaque part rapportée au listing de
  sa propre fiche (changement de méthode explicite par rapport à la vague 2b, voir Étape 3-D6) ;
  distingue la note affichée par Google (histogramme public) de la note moyenne des seuls avis
  restés en ligne.

**`2026-09-08-synthese-de-la-journee.md`**
- Compile les résultats ci-dessus avec, pour chacun, la commande qui le régénère ; ajoute une
  section « conséquence pour la régression logistique » qui fixe la définition du périmètre de
  modélisation sur la date de publication plutôt que la date de première observation.

---

## Étape 3 — Changements de méthode, dans l'ordre chronologique

### D1 — Règle de qualification d'une suppression (résurrection)

- **Avant** : `legacy/2026-09-06-enquete-fiches-purgees-et-plan.md`, Priorité 1 —
  > « Ajouter une règle dans `build_tables.py` : un avis dont l'identifiant réapparaît vivant sur
  > la même fiche n'est pas une suppression. »
- **Après** : `2026-09-08-note-de-methodo.md`, « Le socle » —
  > « Raté de collecte : l'avis est absent un seul jour puis revient à l'identique. [...] Les avis
  > absents 2 jours ou plus avant de revenir restent comptés comme supprimés, à la date de leur
  > première disparition. »
- Nature : hypothèse corrigée. La règle implémentée est plus étroite que la règle proposée deux
  jours plus tôt — elle n'exclut que les retours en 1 jour (glitch de collecte), pas toute
  résurrection quel que soit le délai.

### D2 — Définition du périmètre « avis récent »

- **Avant** : `2026-09-06-facteurs-et-programme-danalyse.md`, périmètre fixé sur les avis « vus
  pour la première fois pendant le suivi » (implicite dans le chiffre 106 761 / 2 853, bâti sur
  `fresh_hazard.parquet`).
- **Après** : `2026-09-08-synthese-de-la-journee.md`, « Conséquence pour la régression
  logistique » —
  > « Le périmètre restreint sur l'âge de l'avis, pas sur son sort [...]. » et la définition D2/D3
  > fondée sur `age_days` calculé depuis `created_at` (date de publication), jamais la date de
  > première observation.
- Nature : hypothèse corrigée, documentée aussi dans `2026-09-06-reprise-qualification-des-
  suppressions.md`, Partie 3 point 1 : « "Avis récent" doit vouloir dire "publié il y a moins de
  30 jours", vérifié sur la date de publication et non sur la date de première observation. » Le
  défaut trouvé : la première définition laissait entrer des avis vieux de plusieurs années dans
  le périmètre « récent » simplement parce qu'ils réapparaissaient pendant le suivi.

### D3 — Variable Local Guide

- **Avant** : `legacy/2026-09-04-...premieres-observations...md`, tableau à deux lignes
  « Local Guide / Non Local Guide » (variable binaire).
- **Après** : `2026-09-06-facteurs-et-programme-danalyse.md`, § 1.4 —
  > « Le oui/non n'est rien d'autre que "niveau supérieur ou égal à 4". [...] On garde donc le
  > niveau, en trois paliers (1-3 / 4-5 / 6 et plus), et on abandonne le oui/non. »
- Nature : règle nouvelle, remplaçant une variable jugée trop grossière une fois le niveau
  disponible examiné palier par palier.

### D4 — Champs vides (« niveau absent », « compteur à 0 »)

- **Avant** : vague 1, ces champs n'apparaissent pas comme facteur — seulement la variable
  Local Guide binaire.
- **Après** : `2026-09-06-facteurs-et-programme-danalyse.md`, § 1.5 —
  > « Ces deux champs sont des états transitoires, pas des catégories. [...] Sur les avis récents,
  > les deux vides ensemble forment une signature nette : premier avis d'un compte créé de la
  > veille. »
- Nature : étape ajoutée, issue d'une vérification manuelle sur des profils réels (30 puis 45
  profils) qui a montré que le champ vide ne signifie pas la même chose selon l'ancienneté de
  l'avis.

### D5 — Correction systématique par âge vs vérification préalable du dénominateur

- **Avant** : `2026-09-06-facteurs-et-programme-danalyse.md`, § 3.3 —
  > « Toujours recalculer à âge comparable. » Règle appliquée sans exception dans
  > `level1_bivariate.py` (une colonne « risque à âge comparable » recalculée pour chaque facteur).
- **Après** : `2026-09-08-note-de-methodo.md`, « Le fait qui rend tout simple » puis « Erreurs de
  méthode » —
  > « Le corpus contient à peu près autant d'avis de chaque âge [...]. Ce fait n'a été constaté
  > qu'à la fin de la session, après trois constructions destinées à contourner un problème de
  > dénominateur qui n'existait pas. [...] Vérifier la platitude du dénominateur avant de
  > construire quoi que ce soit. »
- Nature : étape ajoutée en amont (contrôle de platitude), qui aurait rendu inutiles trois
  constructions de la vague 3 si elle avait été faite d'abord. Ne contredit pas la règle « âge
  comparable » de la vague 2a, mais change l'ordre des opérations recommandé.

### D6 — Cas des deux salles de sport : fiches combinées vs séparées

- **Avant** : `legacy/2026-09-06-enquete-fiches-purgees-et-plan.md`, Partie 2 — traite les
  deux fiches comme un seul paquet (« 399 avis supprimés à elles deux [...] 361 avis d'une étoile
  publiés en deux jours sur une fiche notée 4,95 »).
- **Après** : `2026-09-08-cas-attaque-salles-de-sport.md`, en-tête —
  > « Les deux fiches sont traitées séparément, et chaque part est rapportée au listing de sa
  > propre fiche. Les versions précédentes de ce cas additionnaient les deux fiches puis
  > rapportaient le total à l'une d'elles, ce qui donnait des parts fausses. »
- Nature : erreur corrigée. Documentée aussi dans `BONNES-ET-MAUVAISES-PRATIQUES.md`, écueil 1.

### D7 — Note affichée par Google vs moyenne des avis restants

- **Avant** : `legacy/2026-09-06-enquete-fiches-purgees-et-plan.md` présente « sur une fiche
  notée 4,95 » comme la note de la fiche.
- **Après** : `2026-09-08-cas-attaque-salles-de-sport.md`, tableau des correctifs —
  > « "sur une fiche notée 4,95" → Google affichait 3,81 sur A et 4,67 sur B au 11/08 [...] 4,95
  > était la note moyenne des avis restés en ligne, jamais celle affichée par la fiche. »
- Nature : hypothèse corrigée — confusion entre deux grandeurs distinctes (note publique de la
  fiche à un instant donné, moyenne calculée a posteriori sur un sous-ensemble d'avis).

### D8 — Marge d'erreur de la rafale d'auteur (analyse B) : méthode rapide vs bootstrap complet

- **Avant** : `legacy/2026-09-06-analyse-b-quel-avis-tombe.md`, table des résultats —
  effet « rafale le même jour » ×26,45, calculé avec la méthode indiquée dans
  `legacy/2026-09-06-synthese-etat-et-resultats.md` comme `analysis_b.py --marges-rapides`.
- **Après** : même fichier `synthese-etat-et-resultats.md`, Partie C —
  > « Le chiffre de la rafale est à manier avec précaution : la méthode rapide utilisée pour les
  > fourchettes le surestime. La valeur de référence est 18,8, pas 26. » — obtenu par
  > `analysis_b.py --bootstrap 30`, un rééchantillonnage complet des établissements plutôt qu'une
  > approximation rapide.
- Nature : étape de calcul remplacée (méthode d'estimation de la marge d'erreur), à l'intérieur de
  la même vague de travail, avant même la correction du comptage.

### D9 — Réponse du propriétaire : état figé vs réponse datée

- **Avant** : `legacy/2026-09-06-analyse-b-quel-avis-tombe.md` et
  `legacy/2026-09-06-premiers-resultats-facteur-par-facteur.md` mesurent la réponse comme
  présente/absente à l'état final du panel, reportée sur tous les passages antérieurs.
- **Après (partiel, pas généralisé)** : `2026-09-06-verif-reponse-proprietaire.md`, § 3 — calcule
  l'effet une seconde fois avec la réponse « comptée seulement une fois publiée » et note l'écart
  (« +9 % » de déplacement de l'effet). Le fichier lui-même conclut : « **Reste à refaire
  l'analyse B avec la réponse datée** pour donner un chiffre définitif. »
- Nature : changement de méthode identifié et testé, mais non répercuté dans l'analyse B au
  moment de la vague 3 — aucun des cinq fichiers du 2026-09-08 ne referme ce point.

### D10 — Contrôle de robustesse hors fiches massivement purgées

- **Avant** : absent de la vague 1 et de la première version de l'analyse A/B (vague 2a) — ces
  fichiers ne comportent aucune étape de retrait des fiches à purge massive.
- **Après** : `legacy/2026-09-06-controle-robustesse.md`, introduit comme étape à part entière —
  seuil : plus de 5 % du stock perdu **et** au moins 10 suppressions, verdict à quatre catégories
  fixé avant lecture des chiffres. Étape maintenue à l'identique en vague 3
  (`2026-09-08-histogramme-age-des-suppressions.md`, § 5, même seuil).
- Nature : étape ajoutée en vague 2b, puis conservée sans modification de règle jusqu'à la vague
  3 — seul l'effectif de fiches concernées change (parce que le comptage sous-jacent change),
  pas la définition du seuil.

### D11 — Vérification « effet d'âge ou purge » pour un pic ponctuel

- **Avant** : aucune méthode de ce type dans les vagues 1 et 2 — l'analyse A/B et le niveau 1
  contrôlent l'âge globalement, mais ne testent pas si un pic localisé (ex. un jour précis) est
  un artefact de quelques fiches.
- **Après** : `2026-09-08-age-a-la-suppression.md`, « Le pic à 7 jours : effet d'âge ou purge ? »
  — trois contrôles systématiques (étalement sur les journées, étalement sur les établissements,
  tenue après retrait des deux journées les plus chargées), repris comme méthode générale dans
  `BONNES-ET-MAUVAISES-PRATIQUES.md` : « Trois questions pour distinguer un effet d'un accident :
  sur combien de journées ? sur combien d'unités ? survit-il au retrait des cas extrêmes ? »
- Nature : étape ajoutée, généralisée en règle de méthode pour la suite du projet.

---

## Étape 4 — Points de divergence à trancher

**Point de divergence n°1 (D1).** Au jour 2, la règle proposée excluait toute suppression dont
l'avis réapparaît vivant, quel que soit le délai. Au jour 3, la règle implémentée n'exclut que
les retours en 1 jour ; un avis absent 2 jours ou plus reste compté comme supprimé même s'il
revient ensuite. Pourquoi ce resserrement, et lequel des deux critères doit trancher pour la
suite — la réapparition seule, ou la réapparition combinée à un délai ?

**Point de divergence n°2 (D2).** Au jour 1, le périmètre « avis récent » était défini sur la
date de première observation par le robot. Au jour 3, il est défini sur la date de publication
(`created_at`). Les deux définitions donnent des ensembles différents. Laquelle doit être
citée dans le livrable comme « le » périmètre de l'étude ?

**Point de divergence n°3 (D3).** Le statut Local Guide a été mesuré en oui/non, puis en palier
de niveau. Le tableau bivarié de la vague 1 (oui/non) n'a jamais été refait en palier sur le
même périmètre pour comparer directement les deux lectures. Faut-il republier le tableau du
jour 1 avec la variable corrigée avant de l'écarter, ou l'écarter sans le refaire ?

**Point de divergence n°4 (D5).** La règle « toujours recalculer à âge comparable » (jour 1)
et la règle « vérifier d'abord si le dénominateur est plat » (jour 3) coexistent. Sur les avis
récents (2 à 30 jours), le second contrôle dit que le premier calcul est superflu. Faut-il
garder la standardisation par âge partout par prudence, ou la retirer là où la platitude du
dénominateur a été vérifiée ?

**Point de divergence n°5 (D6, D7).** Le cas des salles de sport a été publié une première fois
avec des fiches combinées et une note confondue, puis republié corrigé. Les chiffres corrigés
(2026-09-08) n'ont pas encore été confrontés au contrôle de robustesse ni au Test 2, calculés
avant la correction. Faut-il attendre le recalcul complet de ces deux étapes avant de citer quoi
que ce soit sur ce cas dans le livrable ?

**Point de divergence n°6 (D8).** Deux méthodes de calcul de marge d'erreur coexistent pour
l'analyse B : rapide (`--marges-rapides`) et bootstrap complet (`--bootstrap`). La méthode rapide
a été utilisée pour produire les premiers tableaux, remplacée ensuite pour l'effet de rafale
seulement. Les autres effets de l'analyse B ont-ils été recalculés en bootstrap complet, ou
certains restent-ils sur la méthode rapide sans que ce soit signalé dans le fichier de résultats ?

**Point de divergence n°7 (D9).** L'effet de la réponse du propriétaire a été mesuré deux fois :
état figé au dernier passage, et réponse datée. L'écart entre les deux (+9 % rapporté) n'a
jamais été répercuté dans l'analyse B elle-même. Faut-il regénérer l'analyse B avec la réponse
datée avant le 15 septembre, ou publier le chiffre actuel avec la réserve écrite ?

**Point de divergence n°8 (D10).** Le seuil du contrôle de robustesse (>5 % du stock **et** ≥10
suppressions) a été fixé une fois, en vague 2b, et jamais rediscuté depuis — y compris après la
correction du comptage qui change l'effectif de fiches concernées (39 puis 24). Ce seuil doit-il
être revérifié maintenant que le comptage sous-jacent a changé, ou reste-t-il valable tel quel ?

**Point de divergence n°9 (D11).** La méthode de contrôle « effet d'âge ou purge » (trois
vérifications) n'a été appliquée qu'au pic de 7 jours. Elle n'a pas été appliquée aux autres
motifs candidats à un artefact — notamment le pic du 16 août signalé dans
`2026-09-08-age-a-la-suppression.md` (un seul établissement portant 26 % des suppressions du
jour). Cette méthode doit-elle être appliquée systématiquement à chaque anomalie relevée dans le
projet avant publication, ou seulement sur demande ?
