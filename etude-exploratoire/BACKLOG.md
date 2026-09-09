# Backlog — Analyse suppressions d'avis Google

Dernière mise à jour : 2026-09-09.

Légende : `[ ]` à faire · `[~]` en cours · `[x]` fait · `[!]` bloqué

---

## État du projet au 2026-09-09

Le comptage des suppressions est corrigé **et** la table maîtresse est dédoublonnée. La
référence reste `scripts/suppressions_corrigees.py` en local et
`logistic-regression-study/sql/01_build_avis_deleted_panel.sql` en BigQuery :
**5 230 lignes de disparition, portées par 5 109 avis distincts, -> 4 747 suppressions
retenues en DuckDB, 4 737 en BigQuery.** L'écart de 10 tient à la mesure du délai d'absence,
détail dans `../CLAUDE.md` point 4.

- **Valides** : les quatre notes du 2026-09-08, plus les cinq documents relancés le 2026-09-09
  (analyses A et B, contrôle de robustesse, Test 2, facteur par facteur). Liste dans
  `documentations/INDEX.md`.
- **Périmés** : trois documents restent dans `documentations/legacy/`, ceux qui n'ont pas de
  script pour les régénérer. Aucun de leurs chiffres ne doit être cité.
- **Toujours valables** : les méthodes, décisions et questions ouvertes des documents mixtes
  restés dans `documentations/`.

## Fait le 2026-09-09 : trois défauts corrigés dans la chaîne locale

- [x] **`build_tables.py` n'appliquait pas la correction de comptage.** Son `deleted` valait
      `deleted_detected_at IS NOT NULL`, la disparition brute. Seuls 3 scripts sur 15
      importaient `suppressions_corrigees.py`, et c'est exactement pourquoi les documents de
      `legacy/` portaient le comptage d'avant correction. La cible vient maintenant de
      `death_at`, et `reviews_features` expose les deux dates, la corrigée et la brute.
- [x] **`WHERE NOT is_update` ne rend pas une ligne par avis.** 617 avis — ceux qui ont disparu
      puis sont revenus — ont plusieurs enregistrements de base. `base` dédoublonne maintenant
      en gardant la première observation, la seule certainement antérieure à la suppression.
- [x] **La fuite que ce doublon créait.** `author_agg` calculait
      `count(*) > 1 AND span <= 1` : un auteur n'ayant écrit qu'un seul avis, mais dont l'avis
      avait disparu puis était revenu, sortait étiqueté « rafale ». La caractéristique lisait
      donc en partie la suppression qu'on lui demandait de prédire. Vérifié sur un jeu construit
      et mesuré côté BigQuery : l'effet des rafales passe de ×7,2 à ×3,9.
- [x] **La règle « fiche massivement purgée » est remplacée.** Voir `../CLAUDE.md`, Conventions
      de Restitution point 5, pour la nouvelle définition et le détail des trois familles que
      l'ancienne mélangeait. Les seuils sont dans `suppressions_corrigees.py`, en un seul
      exemplaire, utilisés par `build_tables.py` et par la vue `fiches_attaquees`.
- [x] **Deux contrôles de `build_tables.py` validaient l'ancien comportement** : « avis de base
      = 4 878 151 » figeait le compte avant dédoublonnage, « suppressions = 5 230 » comptait des
      événements. Remplacés par des contrôles structurels.
- [x] Relancé `build_tables.py`, puis les analyses A et B, le contrôle de robustesse, le Test 2
      et le facteur par facteur. Tous les contrôles de cohérence passent.

## Résultats du 2026-09-09

- **L'analyse B tient entièrement.** Ses 26 effets survivent au retrait des fiches attaquées.
  Les plus forts : rafale d'auteur ×5,30, avis 1 étoile ×3,57, avis modifié depuis publication
  ×1,94. Le premier effet protecteur est la réponse du propriétaire, ×0,30.
- **Un avis 5 étoiles est plus supprimé qu'un avis 4 étoiles** (×1,24). Le tri ne vise pas que
  les avis négatifs.
- **Ni la longueur du texte ni la langue ne mesurent quoi que ce soit** (×1,00 à ×1,13 sur
  toutes les tranches). L'étude BigQuery arrive au même constat.
- **Le pic est entre 7 et 13 jours**, pas au dépôt : 0-6 jours ×0,44 par rapport à cette tranche.
- **Test 2 tient** : ×1,46 et ×1,76 sur le stock de plus d'un an, selon la part du stock récent
  perdue. Survit au retrait des fiches attaquées. La tranche « 10 % et plus » est **non
  exploitable** — couverture des strates à 21 %, à ne pas citer.
- **Analyse A** : home_services ×3,94, États-Unis ×1,40, wellness_fitness ×1,68 mais fragile.
  Son second modèle, l'ampleur de la purge, n'est pas exploitable.

## À faire

- [ ] **Relire les paragraphes de récit des scripts.** Les tableaux sont régénérés, les phrases
      autour portent encore des chiffres écrits en dur d'un passage antérieur. Un seul est
      marqué, dans `age_a_la_suppression.py`. Les quatorze autres scripts ne sont pas audités.
- [ ] **Les 4 avis d'écart** entre DuckDB (4 747) et BigQuery (4 737) restent inexpliqués. Six
      des dix le sont : convention de comptage des jours.
- [ ] **Balayage systématique des attaques par avis négatifs.** La nouvelle règle en trouve 4
      là où on en connaissait 2, dont une petite attaque sur une fiche de 9 545 avis qu'aucun
      seuil en pourcentage ne pouvait voir.

Synthèse des résultats du jour : `documentations/2026-09-08-synthese-de-la-journee.md`.
Écueils à ne pas répéter : `../BONNES-ET-MAUVAISES-PRATIQUES.md`.

### Les cinq défauts — diagnostic posé le 2026-09-06

Les chiffres de cette section sont ceux du comptage fautif : c'est le constat qui a mené à la
correction, conservé tel quel comme trace du diagnostic.

1. **509 des 5 230 suppressions concernent un avis qui revient** (9,7 %). Sur le périmètre de
   l'étude : 124 sur 2 853. Le README de l'export annonçait 617 résurrections ; le filtre n'a
   jamais été posé.

2. **Sept entreprises n'ont rien perdu.** Le robot a lu une page de listing au lieu de deux le
   12 août. 162 avis marqués supprimés, 162 revenus au passage suivant, compteur public de
   Google inchangé. Ces sept figurent parmi les 24 fiches « massivement purgées » qui servent
   de référence à tous les contrôles.

3. **Le périmètre « avis récents » contient 819 avis anciens**, dont 588 de plus d'un an, jusqu'à
   13 ans. Sa définition retenait tout avis vu pour la première fois pendant le suivi. Ces
   819 avis portent 154 des 2 853 suppressions et ont un taux de suppression de 18,8 % contre
   2,5 % pour les vrais avis récents.

4. **Une réponse de propriétaire retirée est indétectable.** L'export ne versionne que la note
   et le texte. Le résultat « répondre protège » ne peut pas être vérifié contre ce cas.

5. **Le passage de 5 314 à 2 853 n'était écrit nulle part.** 5 314 lignes marquées supprimées,
   moins 84 lignes d'historique d'édition = 5 230 avis ; moins 2 525 avis de plus de 30 jours
   = 2 705 ; plus 148 dus au défaut n° 3 = 2 853.

### Ce qui manquait

Aucune étape de qualification des suppressions n'a été faite avant de modéliser. La question
« qu'est-ce qu'une suppression dans ces données, et est-ce que ce que je compte existe
vraiment » n'a jamais été posée.

---

## En cours : construction de la table v2

Dossier `v2/`. Objectif : une table propre pour une régression logistique.

- [~] **`v2/build_panel.py` — écrit, jamais exécuté.** Le fichier existe mais il a été écrit
  avant que les caractéristiques soient décidées. À reprendre avec les décisions ci-dessous.

### Décisions prises avec Romain le 2026-09-06

| Sujet | Décision |
|---|---|
| Unité d'une ligne | un avis, un passage du robot |
| Suppression | l'avis est absent au dernier passage **et** n'est jamais revenu |
| Note et texte | recalculés à la date de chaque passage, avec l'historique de l'export |
| Caractéristiques d'auteur figées | gardées, avec réserve écrite |
| Activité de la fiche | avis reçus le jour même, sur 7 jours, sur 30 jours |
| Échantillonnage | tous les avis supprimés + 1 avis sur 20 parmi les autres |
| Tirage | porte sur les avis, jamais sur les lignes |
| Fiches touchées | tous leurs avis conservés, pas de tirage |

### Colonnes retenues

**L'avis à ce passage** : âge en jours, note du jour, présence et longueur du texte, nombre de
photos, langue, modifié ou non.

**Réponse du patron à ce passage** : existait-elle déjà, délai en jours après l'avis, ancienneté
de la réponse.

**Activité de la fiche à ce passage** : avis reçus le jour même, sur 7 jours, sur 30 jours ; ces
trois chiffres rapportés au stock total ; avis de la même note reçus sur 7 jours.

**La fiche** : note moyenne du jour et son évolution, écart entre la note de l'avis et cette
moyenne, nombre total d'avis, pays, secteur, taille du groupe.

**L'auteur** : niveau Local Guide, nombre d'avis déclaré, nombre de photos déclaré, nombre
d'avis dans le panel, nombre de fiches dans le panel, plusieurs avis le même jour, ancienneté.

**Qualité de collecte à ce passage** : listing tronqué, compteur Google stable, passage
incomplet.

**Le passage** : numéro de vague.

### Reste à trancher avant de construire

- [ ] Que faire des 43 comptes qui perdent leur niveau Local Guide pendant le suivi. CSV de
  vérification manuelle prêt : `data/verif_niveaux_perdus.csv`.
- [ ] Traiter « aucun niveau Local Guide » comme valeur inconnue et non comme un niveau zéro,
  à confirmer.

---

## Vérifications faites le 2026-09-06

- [x] **Contenu textuel des avis supprimés.** `scripts/verif_texte.py`. Onze contrôles par
  expression régulière. **94 % des avis récents supprimés ne déclenchent aucun contrôle.**
  Insultes : 1,02 % des suppressions. Zéro suppression parmi les avis contenant un lien web ou
  une adresse e-mail. Aucun charabia. 30 % des supprimés n'ont aucun texte.
  Résultat à recalculer après correction du comptage, sans attendre qu'il change beaucoup.

- [x] **Les 7 vitrines endormies expliquées.** Défaut de collecte, voir défaut n° 2 ci-dessus.
  Deux hypothèses écartées en chemin : campagne d'avis ancienne (les avis s'étalent de 2016 à
  2026, un auteur différent à chaque fois) et comptes bannis (ces 210 auteurs ont 19 avis
  ailleurs dans le panel, aucun touché).

- [x] **Les salles de sport expliquées.** Deux fiches espagnoles, deux paquets distincts d'avis
  d'une étoile les 1er et 2 août 2026 : 219 avis sur la fiche A (28 % de ses 781 avis) et 111
  sur la fiche B (17 % de ses 668). Un auteur distinct par avis, deux tiers sans texte, un seul
  avis contenant une insulte. Google a supprimé 229 avis sur A et 135 sur B ; aucun n'est revenu.
  Ces 364 avis expliquent pourquoi « 1 étoile » et « sport et bien-être » sortaient si forts.
  Chiffres et contrôles : `documentations/2026-09-08-cas-attaque-salles-de-sport.md`.

- [x] **Réponse du patron, ordre des événements.** `scripts/verif_reponse_proprietaire.py`.
  Délai médian de 1 jour entre l'avis et la réponse, 93 % sous 7 jours. Sur les 1 406 avis
  supprimés qui avaient une réponse, les 1 406 l'avaient reçue avant la suppression.
  Réserve maintenue : une réponse retirée reste indétectable.

- [x] **Dérive des caractéristiques d'auteur.** Mesurée sur les 602 avis disparus puis revenus,
  seule population observée deux fois. Nombre d'avis de l'auteur : 85 % ne bougent pas ou
  bougent de 1-2. Niveau Local Guide : 82 % ne bougent pas, 43 comptes perdent leur niveau.
  Les 43 sont tous hors des 7 fiches au listing tronqué et dispersés sur 43 fiches différentes.
  Cette population n'a rien d'ordinaire : la mesure ne vaut pas pour les 4,88 M autres avis.

---

## Fait le 2026-09-08 : âge des avis supprimés

Deux notes, un module partagé, un compte rendu de méthode.

| Fichier | Contenu |
|---|---|
| `documentations/2026-09-08-age-a-la-suppression.md` | Suppressions par âge en jours (1 à 30), et par journée du suivi. La référence. |
| `documentations/2026-09-08-histogramme-age-des-suppressions.md` | Les mêmes suppressions en tranches larges (moins d'un mois, 1-3 mois, 3-6, 6-12, plus d'un an), pour le mail à Axel. |
| `documentations/2026-09-08-note-de-methodo.md` | Ce qui a été fait, dans quel ordre, ce qui a été jeté et pourquoi. |
| `scripts/suppressions_corrigees.py` | Module partagé : définition corrigée d'une suppression, en DuckDB. Seule copie hors BigQuery. |

### Résultats

- **Pic à 7 jours de vie : 449 suppressions**, contre 279 à 6 jours, 134 à 9 jours, 118 à
  8 jours, 43 à 5 jours. Le nombre d'avis observés est quasi constant d'un âge à l'autre
  (environ 32 000 par âge de 2 à 30 jours), donc les nombres bruts se comparent sans
  pondération.
- **Répartition en tranches larges** : 51,6 % des suppressions frappent un avis de moins d'un
  mois, 30,3 % un avis de plus d'un an. Le poids du vieux stock vient de son volume, pas de son
  risque (0,0027 % par jour contre 0,2699 % pour un avis de moins d'un mois).
- **7,65 % des avis neufs sont supprimés dans leurs 30 premiers jours** (risque cumulé).
- **Concentration recalculée sur le comptage corrigé** : 85,4 % des établissements sans aucune
  suppression, 14,4 % du total porté par 24 fiches. Les chiffres « 84 % / 39 fiches / 19,5 % »
  de la note du 2026-09-06 sont d'avant la correction et ne valent plus.
- **Volume par journée du suivi** : de 153 le 14/08 à 760 le 17/08, un facteur 5. Chaque journée
  se répartit sur 129 à 275 établissements. Une exception, le 16/08, où un seul établissement
  porte 26 % des suppressions du jour.

### Contrôles faits, à ne pas refaire

- **Rythme hebdomadaire : écarté.** Les bosses à 14, 21 et 28 jours ne survivent pas au retrait
  de l'âge 7 et sont portées par les 16 et 23 août. `created_at` est un horodatage réel (courbe
  horaire plausible, 60 secondes distinctes), pas une date reconstruite depuis un libellé
  « il y a une semaine ».
- **Fiches massivement purgées : la répartition tient sans elles** (moins d'un mois 47,7 %,
  plus d'un an 33,4 %).
- **Censure à droite : la hiérarchie tient** sur la seule cohorte présente à la vague 1
  (2,29 % des avis de moins d'un mois supprimés contre 0,034 % des avis de plus d'un an).

### À faire

- Croiser le pic à 7 jours avec les facteurs de l'analyse B : qui sont les avis qui tombent à
  7 jours, et diffèrent-ils des autres ? C'est le candidat direct pour l'angle faux positifs.

## Programmes

| Programme | Ce qu'il fait | Commande |
|---|---|---|
| `scripts/build_tables.py` | Construit les tables v1. **Comptage faux, à corriger.** | `uv run scripts/build_tables.py` |
| `scripts/level1_bivariate.py` | Facteur par facteur, à âge comparable | `uv run scripts/level1_bivariate.py` |
| `scripts/analysis_a.py` | Quelle entreprise est touchée | `nice -n 19 uv run scripts/analysis_a.py` |
| `scripts/analysis_b.py` | Quel avis tombe dans une fiche touchée | `nice -n 19 uv run scripts/analysis_b.py --marges-rapides` |
| `scripts/controle_robustesse.py` | Rejoue A et B sans les fiches purgées | `nice -n 19 uv run scripts/controle_robustesse.py` |
| `scripts/verif_texte.py` | Contenu des avis supprimés | `uv run scripts/verif_texte.py` |
| `scripts/test2_debordement.py` | Mortalité du vieux stock | `uv run scripts/test2_debordement.py` |
| `scripts/verif_reponse_proprietaire.py` | Ordre réponse / suppression | `uv run scripts/verif_reponse_proprietaire.py` |
| `scripts/query.py` | Interroger les tables en SQL | `uv run scripts/query.py --exemples` |
| `scripts/suppressions_corrigees.py` | Module partagé : définition corrigée d'une suppression | (importé) |
| `scripts/histogramme_age_suppressions.py` | Âge des avis supprimés, comptage corrigé | `nice -n 19 .venv/bin/python etude-exploratoire/scripts/histogramme_age_suppressions.py` |
| `scripts/cas_attaque_salles_de_sport.py` | Le cas des deux salles de sport, fiche par fiche | `nice -n 19 .venv/bin/python etude-exploratoire/scripts/cas_attaque_salles_de_sport.py` |
| `scripts/age_a_la_suppression.py` | Âge à la suppression, jour par jour | `nice -n 19 .venv/bin/python etude-exploratoire/scripts/age_a_la_suppression.py` |
| `v2/build_panel.py` | Table v2. **Écrit, jamais exécuté.** | — |
| `scripts/machine_learning.py` | Contrôle par apprentissage. **Jamais relancé.** | — |

Règles de lancement : un seul cœur et priorité basse (`nice -n 19`) pour tout ce qui dépasse
deux minutes, sinon WSL coupe la connexion VSCode. Vérifier `free -m` avant. Deux calculs lourds
au maximum en même temps.

---

## Suspendu

- [!] Test 3, vérification de la visite sur les services à domicile.
- [!] Contrôle par apprentissage automatique.
- [!] Mention d'un employé par reconnaissance de noms.
- [!] Argument Local Guide du livrable : faux sur les avis récents, à réécrire ou retirer.

---

## Réserves à porter au livrable

- Fenêtre de 14 jours : les suppressions rapides sont visibles, pas les révisions à 6 mois.
- Le filtrage avant publication est invisible. Zéro suppression parmi les avis contenant un lien
  alors qu'il en existe dans le panel : ce filtrage a lieu avant la mise en ligne.
- Vrais faux avis et erreurs de modération sont indistinguables par collecte automatique.
- Le listing public de Google sert parfois des réponses incomplètes sans le signaler. Toute
  mesure de suppression par collecte doit filtrer les avis qui reviennent.
- Le panel ne couvre pas les groupes de 2-3 ni de 11-19 sites.
- 41 pays dont un seul hors Europe.
- Royaume-Uni hors panel.
- Le dictionnaire d'insultes couvre 7 langues sur 41 pays.
