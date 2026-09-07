# Backlog — Analyse suppressions d'avis Google

Dernière mise à jour : 2026-09-06.

Légende : `[ ]` à faire · `[~]` en cours · `[x]` fait · `[!]` bloqué

---

## État du projet : les résultats chiffrés sont invalidés

Le 2026-09-06, une vérification a montré que le comptage des suppressions est faux. Tous les
chiffres produits jusqu'ici en dépendent. Les programmes, les tables et les méthodes restent
utilisables ; ce sont les résultats qui tombent.

Détail complet : `documentations/2026-09-06-reprise-qualification-des-suppressions.md`.

### Les cinq défauts

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

- [x] **Les salles de sport expliquées.** 361 avis d'une étoile publiés les 1er et 2 août 2026
  sur une fiche notée 4,95, par 363 comptes différents. 270 des 399 avis supprimés n'avaient
  aucun texte. Un seul contenait une insulte. Aucune de ces suppressions n'est revenue.
  Google a nettoyé une attaque. Ces 399 avis pèsent 14 % des suppressions du périmètre de
  l'étude et expliquent pourquoi « 1 étoile » et « sport et bien-être » sortaient si forts.

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
