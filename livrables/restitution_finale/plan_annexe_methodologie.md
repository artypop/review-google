# Plan de l'annexe : corpus, méthode, phénomènes

Rédigé le 2026-10-02 (vendredi), à reprendre le lundi 2026-10-05.

D'après la 2e réunion avec Axel, cette partie va **à la fin du document**, en annexe : les
insights passent en premier.

---

## Avant de produire : fixer les règles communes

Deux définitions de la suppression coexistent dans les figures existantes :

- règle des 2 jours d'absence (03C) : courbe du 7e jour, flux du 1er octobre ;
- `deleted_detected_at` renseigné : flux 4-5 étoiles, longueur du texte, Local Guide, matrice
  secteur × taille (toutes produites le 2026-10-02).

Elles donnent des chiffres qui ne se recoupent pas (flux : 3,81 % d'un côté, 3,24 % de l'autre).
À fixer une fois, et à écrire en tête de la méthodologie :

1. le corpus : `reviews_doublons_cleaned_all` ;
2. la définition de la suppression ;
3. le sort des 232 disparitions notées le 24 août : un seul jour d'absence, faute de relevé le
   lendemain, donc peut-être des clignotements ;
4. 4-5 étoiles ou toutes les notes ;
5. toutes les fiches ou sans les enseignes.

---

## 1. Description du corpus

**Contenu**
- 9 048 fiches, 7 secteurs, 2 régions (États-Unis, Europe), 3 tailles, 41 pays, sans le
  Royaume-Uni.
- 4 876 933 avis dans `reviews_doublons_cleaned_all`.
- Part des avis avec texte : 65 % sur toute la base.

**Visuels**
- Tableau des fiches et des avis par secteur × région, avec une colonne taille. Il fait
  apparaître que Voyage n'a que des entreprises mono (480 fiches).
- Option : barres des avis par secteur.

**À produire** : requête sur `businesses` et le corpus.

---

## 2. Méthodologie de sélection des entreprises

**Contenu** (déjà écrit dans `docs/01-etude.md` § 2)
- L'unité tirée est le groupe : tous ses établissements entrent dans le panel.
- 3 tailles nettes : 1, 4 à 10, 20 à 50 établissements. Les groupes de 2-3, 11-19 et plus de 50
  sont absents.
- Seules des fiches de 100 à 10 000 avis ont servi à sélectionner un groupe.
- Pas de tirage au hasard sur tout Google Maps : les résultats décrivent ce panel.

**Visuels**
- Schéma en entonnoir, ou tableau du plan de sélection : secteur × taille × région, en
  nombre de fiches.

**Question ouverte** : pourquoi Voyage n'a-t-il que des mono ? À demander à celui qui a construit
le panel.

---

## 3. Méthodologie de récolte des avis

**Contenu**
- Un passage du robot par jour du 11 au 24 août 2026, soit 14 passages ; chaque passage relève
  tous les avis de chaque fiche.
- Champs relevés : note, texte, dates, niveau Local Guide, photos, réponse.
- Ce que la récolte ne voit pas :
  - un avis supprimé avant le 11 août ;
  - un avis filtré avant même sa publication : aucun avis contenant un lien n'a disparu, ils
    sont filtrés en amont ;
  - une réponse retirée ;
  - les caractéristiques au moment de l'écriture : on a leur état au dernier passage.
- 3 fiches ne sont plus relevées à partir du 17, du 18 ou du 22 août.

**Visuels**
- Frise du 11 au 24 août avec les passages. Elle resservira pour l'âge de l'avis et pour J+7.
- Option : fiches relevées et avis vus à chaque passage (table `waves`), pour montrer la
  stabilité de la collecte.

---

## 4. Doublons et clignotements (exclus)

**Contenu**
- Doublon : un même avis enregistré plusieurs fois, par exemple quand le texte a été réécrit. Le
  bug d'enregistrement touche 24 avis.
- Clignotement : avis absent un seul jour, qui revient identique. 71 % des avis qui reviennent
  n'ont été absents qu'un jour.

**Visuels**
- Tableau en entonnoir : lignes brutes de `reviews` (4 880 163) → avis distincts → doublons
  retirés → clignotements retirés → `reviews_doublons_cleaned_all` (4 876 933).
- Option : figure 1 de l'ancien rapport, jour de disparition des avis revenus.

**À régler avant d'écrire**
- La règle qui a construit `reviews_doublons_cleaned` n'est écrite nulle part dans le dépôt. La
  récupérer auprès de celui qui l'a construite dans BigQuery : sans elle, cette partie ne peut
  pas être rédigée.
- Les 232 disparitions du 24 août : voir les règles communes, point 3.

---

## 5. Le pic au 7e jour (remplace la courbe de survie)

**Contenu**
- Entre la moitié et deux tiers des suppressions tombent aux 6e et 7e jours de vie de l'avis.
- Au-delà du 8e jour, il n'en reste presque plus sur les 12 jours observés.
- Le pic se répète chaque jour du 18 au 23 août, sur 13 à 29 fiches à chaque fois : ce n'est pas
  une purge à une date donnée.

Chiffres mesurés avec la règle des 2 jours, toutes notes (`survie_par_jour.csv`) :

| Jours d'existence | Tous les avis | Sans les 6 enseignes |
|---|---|---|
| 1 à 5 | 26 % des suppressions | 34 % |
| 6 et 7 | 60 % | 48 % |
| 8 à 12 | 15 % | 18 % |

**Visuel** : barres des suppressions par jour d'existence, avec un titre qui affirme le
résultat (note de `livrables/restitution/avis_restit.md`).

**À refaire** : avec la définition finale de la suppression, et sur les 4-5 étoiles si c'est
la règle du document. Source actuelle :
`etudes-ponctuelles/2026-09-30-courbe-de-vie/`.

**Option** (`avis_restit.md`) : étendre l'axe à 30 jours d'âge en prenant tous les avis, y
compris ceux publiés avant le 11 août. Chaque jour d'âge ne compte que les avis observés à
cet âge-là.

---

## 6. Les phénomènes bizarres

Garder ceux qui sont vérifiés ; les autres vont dans un encadré « non expliqués ».

**Vérifiés**
- **Les 4 chaînes antiparasitaires** (102 fiches) : elles perdent 1 nouvel avis 4-5 étoiles sur
  6 dans la semaine (16,7 %, 206 / 1 231). La hausse est durable depuis avril, sans afflux
  soudain. Visuel : graphique de distribution par jour depuis juillet, montré à la 2e réunion.
- **Les 2 salles espagnoles** : une vague d'avis 1 étoile presque entièrement supprimée (20 sur
  21 pour The Boxer Club, publiés les 12 et 13 août). Visuel : tableau 18 de l'ancien rapport.
- **La concentration** : 17 fiches portent le quart des suppressions, 54 la moitié. Visuel :
  courbe de concentration corrigée
  (`etudes-ponctuelles/2026-09-28-secteurs-et-concentration/`).
- **Les avis vus tardivement** : 283 avis vus 8 jours ou plus après leur publication. Ils sont
  longs et plutôt négatifs, probablement mis en attente par Google. Visuel : tableau 20 de
  l'ancien rapport.

**Non expliqués**
- **Local Guide sans niveau** : 256 suppressions sur 12 651 avis 4-5 étoiles, soit 2,0 %,
  environ 20 fois les autres. Je n'ai pas vérifié si ce sont des comptes fermés.
- **Les journées du 16 et 17 août** : 657 et 750 disparitions notées, contre environ 260 les
  autres jours. Ce pic n'a jamais été contrôlé (BACKLOG).

---

## Ordre de travail

1. Fixer les règles communes (en haut de ce fichier).
2. Récupérer la règle de nettoyage des doublons et clignotements.
3. Produire les tableaux et graphiques des parties 1, 3, 4 et 5 : uniquement des requêtes.
4. Rédiger la partie 6 en dernier : elle dépend des chiffres finaux.

---

## En attente depuis le 2026-10-02

**Régression logistique** (US, Europe, tous ; corpus `03C_7_17_aout`, 4-5 étoiles). Rien n'est
lancé ; deux réponses attendues :
- **Prénom** : aucun code de détection dans le dépôt. Les tableaux 16 et 17 de l'ancien rapport
  (`extracted_full.md`) viennent d'un code absent. Soit on récupère ce code ou sa liste de
  prénoms, soit on construit la détection : une liste publique de prénoms, un mot à majuscule
  présent dans la liste, les prénoms qui sont aussi des mots courants retirés. L'Europe sera
  moins fiable.
- **Réponse du propriétaire** : « répondu au plus tard au 7e jour » fait croire que la réponse
  protège l'avis, car un avis supprimé tôt n'a pas eu le temps d'en recevoir une. Proposition :
  un jalon à la fin du 2e jour (répondu au plus tard au 2e jour, suppression comptée du 3e au
  7e jour, avis disparus avant le jalon retirés), comme le 08.

**Choix proposés par défaut pour la régression**
- Suppression au plus tard 7 jours après la publication.
- Pic compté sur les 4-5 étoiles : au moins 3 avis le jour de publication, avis étudié compris,
  et au moins 4 fois la moyenne journalière des 365 jours avant le 11 août.
- Marges d'incertitude calculées par fiche ; 3 fiches plus relevées écartées.

---

## Produits le 2026-10-02

| Sujet | Graphique ou tableau | Données | Script |
|---|---|---|---|
| Flux 4-5 étoiles par secteur | — | `etudes-ponctuelles/2026-10-02-flux-4-5-etoiles/sorties/flux-4-5-etoiles.csv` | même dossier, `calcul.py` |
| Longueur du texte | `graphiques/longueur_texte_quintiles.png` | `donnees/longueur_texte_quintiles.csv` | `etudes-ponctuelles/2026-10-02-longueur-texte-quintiles/calcul.py` |
| Niveau Local Guide | `graphiques/local_guide_niveaux.png` | `donnees/local_guide_niveaux.csv` | `etudes-ponctuelles/2026-10-02-local-guide-niveaux/calcul.py` |
| Pertes / nouveaux, secteur × taille | `graphiques/pertes_secteur_taille.png` | `donnees/pertes_secteur_taille.csv` | `etudes-ponctuelles/2026-10-02-pertes-secteur-taille/calcul.py` |

Titre proposé pour la matrice (graphique 3) : « Avis 4 et 5 étoiles supprimés pour 100 publiés
en deux semaines, par secteur et taille d'entreprise ».

Commande commune, depuis `review-google/` :
`PYTHONPATH=".venv/Lib/site-packages;outils" <python uv> <script>`

---

## Produits le 2026-10-05

| Sujet | Graphique | Données | Script |
|---|---|---|---|
| Régression logistique 03C (prénom, photo, réponse, pic), US / Europe / les deux | `graphiques/regression_03C_prenom.png` | `donnees/regression_03C_prenom_{rapports_de_cotes,effectifs,controles}.csv` | `logistic-regression-study/python/07F_regression_03C_prenom.py` |
| Même régression sur tout le suivi, jour par jour, à secteur et taille égaux (version recommandée) | `graphiques/regression_03C_suivi_complet.png` | `donnees/regression_03C_suivi_complet_{rapports_de_cotes,effectifs,controles}.csv` | `logistic-regression-study/python/07G_regression_03C_jour_par_jour.py` |

- Corpus : 03C, avis 4-5 étoiles. Un avis disparu compte comme supprimé, sans la règle des 2 jours (les doublons sont déjà retirés). Suppression au plus tard au 7e jour.
- Prénom : annotation d'Axel, ajoutée par `03C_ajout_prenom.py`.
- Réponse au 7e jour : biaisée, car un avis supprimé plus tôt a eu moins de temps pour recevoir une réponse. Calculée jour par jour mais sans contrôles, elle n'a pas d'effet significatif (0,73 [0,49–1,09]). Avec les contrôles du 07G, elle devient significative (voir ci-dessous).
- Version 07G : 903 suppressions au lieu de 631. Le secteur et la taille sont en contrôle, la région aussi pour « les deux », sans être affichés. Le jour d'âge n'est pas dans le modèle, par choix de Matthieu : l'ajouter change les résultats de 0,02 au plus. Les conclusions : pas d'effet du prénom, un pic qui augmente le risque, une réponse reçue qui le diminue, une photo qui ne protège qu'aux États-Unis.
