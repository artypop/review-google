# Passation — analyse des suppressions d'avis Google

Document destiné à qui reprend le projet, humain ou assistant.
Écrit le 2026-09-06, chiffres mis à jour le 2026-09-08.

> Point d'entrée pour la reprise : `documentations/INDEX.md` (inventaire de tous les documents
> avec leur statut), puis `documentations/2026-09-08-synthese-de-la-journee.md` (résultats
> valides) et `../BONNES-ET-MAUVAISES-PRATIQUES.md` (écueils à ne pas répéter).

---

# 1. Consignes de rédaction — à lire avant d'écrire une ligne

Ces consignes viennent de Romain. Elles ne sont pas négociables et elles s'appliquent aux
réponses comme aux documents produits.

**Franc, sans fioriture, sans faire le malin. Aucune phrase parasite.**

## Interdits

**Les méta-phrases qui annoncent l'intention ou la posture.**
« Pour être franc », « pour être clair », « soyons honnêtes », « en toute transparence ».

**Les phrases-bilan qui commentent l'effet de ce qui vient d'être dit.**
« Ça transforme X en Y », « ça évite que… », « c'est là que ça devient intéressant ».

**Les images et métaphores.**
« Se tirer une balle dans le pied », « jeter le bébé avec l'eau du bain ».

**Toute liaison qui n'apporte pas d'information** et sert seulement de transition ou d'effet.

**Toute litanie** qui rappelle le contexte, redonne des éléments déjà vus, ou allonge la sauce.

**Les tournures d'insistance.** Écrire « trois choses » et non « trois choses, pas une ».

**Les phrases couperet en fin de paragraphe.** Ne pas clore par une formule définitive.
Écrire « tu souhaites les garder, mais… » et non « On les garde, c'est ta décision. »

## Interdiction absolue

**Aucune phrase qui ressemble à un titre de post LinkedIn.**

Exemples relevés par Romain dans ce projet :

- « C'est la fenêtre pour porter l'argumentaire tant qu'il est frais »
- « Le risque n'est pas le désordre, c'est la version »
- « Revoir l'atelier de données : à faire avant de poser les créneaux, pas après »
- « La frontière à poser tient en une seule règle à suivre »
- « C'est un faux positif, et c'est chiffré »

## Vocabulaire

Aucun mot de statistique. Bannis : rapport de risque, standardisé, effets fixes, logistique
conditionnelle, bootstrap, quantile, censure à droite, strate, significatif.

Dire la conséquence concrète, pas la méthode. « Sur 10 000 avis en ligne, il en disparaît 50 »
et non « risque par vague de 0,50 % ».

## Niveau d'explication

Méthode Feynman. Expliquer ce qu'on fait, ce qu'on produit et toute réponse à une question
comme à quelqu'un qui découvre le sujet, avec des mots ordinaires et un exemple concret tiré de
ses propres données.

Quand Romain dit qu'il n'a pas compris, redire la même chose autrement ne sert à rien. Changer
d'angle et dérouler un cas réel, chiffre par chiffre.

## Erreurs à ne pas répéter

Romain a relevé ces comportements pendant la session du 2026-09-06 :

- **Partir bille en tête.** Construire ou lancer avant qu'il ait validé la méthode. Il l'a dit
  trois fois. Ne rien construire tant que la question posée n'est pas tranchée avec lui.
- **Lancer des calculs lourds.** Un calcul qui prend tous les cœurs pendant des heures coupe
  sa connexion VSCode sous WSL. Tout ce qui dépasse deux minutes se lance avec
  `nice -n 19` et un seul cœur, et lui appartient : il décide quand.
- **Oublier ce qui a été dit.** Il a dû rappeler lui-même que les 602 avis observés deux fois
  étaient les avis disparus puis revenus, après dix minutes d'échange dessus.
- **Ne pas vérifier avant d'affirmer.** L'origine de toute cette session est là.

---

# 2. Le projet en dix lignes

Étude quantitative pour ReviewFlowz (commanditaire : Axel) : quelles caractéristiques d'un avis
Google sont associées à sa suppression. L'angle du livrable porte sur les erreurs de modération.

Les données : 9 048 entreprises suivies, un relevé par jour du 11 au 24 août 2026, 4,88 millions
d'avis. À chaque passage le robot recense la totalité des avis de chaque fiche. Un avis qui
n'apparaît plus est compté comme supprimé.

Les fichiers d'origine sont dans `data/exports/exports/`. Ils ne sont pas dans le dépôt : 872 Mo
et des données personnelles. Le README de l'export interdit leur rediffusion.

---

# 3. Où en est le projet

**Les résultats chiffrés produits jusqu'au 2026-09-06 sont invalidés.**

Le comptage des suppressions est faux. Cinq défauts, détaillés dans `BACKLOG.md` et dans
`documentations/2026-09-06-reprise-qualification-des-suppressions.md`.

Le plus grave : 509 des 5 230 disparitions concernent un avis qui réapparaît ensuite. Le README
de l'export l'annonçait dès le départ. Le filtre n'a jamais été posé.

Le deuxième : sept entreprises figurant parmi les 24 « massivement purgées » n'ont jamais rien
perdu. Le robot a lu une page de listing au lieu de deux le 12 août, et 162 avis ont été comptés
comme supprimés. Ils sont tous revenus au passage suivant, et le compteur public de Google n'a
jamais bougé.

**Ce qui reste utilisable** : les programmes, les tables intermédiaires, les méthodes de calcul.
Une fois le comptage corrigé, tout se recalcule en une quinzaine de minutes.

---

# 4. Ce qui a été décidé et qu'il ne faut pas rouvrir

Ces points ont été tranchés avec Romain le 2026-09-06.

| Sujet | Décision |
|---|---|
| Unité d'une ligne de la table | un avis, un passage du robot |
| Définition d'une suppression | absent au dernier passage **et** jamais revenu |
| Note et texte | recalculés à la date de chaque passage |
| Caractéristiques d'auteur figées | gardées, avec réserve écrite |
| Activité de la fiche | avis reçus le jour même, sur 7 jours, sur 30 jours |
| Échantillonnage | tous les supprimés + 1 avis sur 20 parmi les autres |
| Ce que le tirage sélectionne | des avis entiers, jamais des lignes |
| Fiches ayant perdu au moins un avis | tous leurs avis conservés |

La liste complète des colonnes retenues est dans `BACKLOG.md`.

---

# 5. La prochaine étape

Construire la table v2, dans le dossier `v2/`.

Le fichier `v2/build_panel.py` existe déjà mais il a été écrit avant que les caractéristiques
soient décidées. Il est incomplet et n'a jamais été exécuté.

Deux points restent à trancher avec Romain avant de le reprendre :

1. Que faire des 43 comptes qui perdent leur niveau Local Guide pendant le suivi. Le CSV de
   vérification manuelle est prêt : `data/verif_niveaux_perdus.csv`.
2. Confirmer que « aucun niveau Local Guide » sera traité comme une valeur inconnue et jamais
   comme un niveau zéro.

---

# 6. Les pièges du jeu de données

Ils sont réels et ils ont tous causé une erreur dans ce projet.

**Un avis supprimé peut revenir.** 509 cas sur 5 230 disparitions brutes ; c'est ce qui ramène
le compte à 4 747 suppressions réelles. Ne jamais compter une suppression sans
vérifier que l'avis ne réapparaît pas plus tard sur la même fiche.

**Le robot lit parfois une page de listing au lieu de deux.** Le contrôle de complétude du
collecteur ne le détecte pas. Deux signes : le nombre de pages lues chute pour une fiche, et le
compteur public de Google ne baisse pas alors que le listing perd des avis.

**Un avis n'est pas une ligne du fichier.** L'unité est le couple (fiche, identifiant d'avis).
602 avis ont plusieurs lignes parce qu'ils ont disparu puis sont revenus.

**Vu pour la première fois pendant le suivi ne veut pas dire publié récemment.** 819 avis de
plus de 30 jours, dont un de 13 ans, étaient classés comme récents pour cette raison.

**Les caractéristiques de l'auteur sont écrasées à chaque passage.** Le fichier ne contient que
la dernière valeur. Un compte affiché à 0 avis le 12 août peut afficher 5 avis le 24, et c'est 5
qui figure dans le fichier.

**Une réponse de propriétaire retirée est indétectable.** L'export ne versionne que la note et
le texte.

**L'âge de l'avis pèse plus que tout le reste.** Le risque de suppression culmine 7 à 13 jours
après la publication puis s'effondre. Toute comparaison qui ne tient pas compte de l'âge mesure
surtout une différence d'âge.

**Les suppressions sont concentrées.** 85,4 % des établissements n'ont rien perdu. Les
24 fiches ayant perdu plus de 5 % de leurs avis portent 14,4 % des 4 747 suppressions. Deux
salles de sport espagnoles en portent 364 à elles deux — 229 sur une fiche de 781 avis, 135 sur
une fiche de 668. Détail : `documentations/2026-09-08-cas-attaque-salles-de-sport.md`.

---

# 7. Les résultats qui survivent probablement

À recalculer après correction du comptage. Ne pas les présenter comme acquis.

**Le contenu des avis supprimés.** 94 % des avis récents supprimés ne déclenchent aucun des onze
contrôles textuels : pas d'insulte, pas de lien, pas de charabia. Les insultes concernent 1 % des
suppressions. Zéro suppression parmi les avis contenant un lien web ou une adresse e-mail.

**Les salles de sport.** Deux fiches espagnoles attaquées le même week-end. La fiche A a reçu
219 avis d'une étoile les 1er et 2 août, soit 28 % de ses 781 avis ; la fiche B en a reçu 111,
soit 17 % de ses 668. Un auteur distinct par avis, deux tiers sans aucun texte. Google a
supprimé 229 avis sur A (le plus souvent 14 à 15 jours après publication) et 135 sur B (10 à
11 jours). Aucun n'est revenu. Cette modération a fonctionné.

**La forme de la courbe d'âge.** Risque maximal à 7-13 jours, puis effondrement.

---

# 8. Environnement technique

Machine sous WSL, 16 Go de mémoire, VSCode connecté. La connexion tombe si un calcul prend tous
les cœurs longtemps.

Gestionnaire de paquets : `uv`. Rien d'autre à installer.

```bash
uv run scripts/query.py --tables      # voir les tables disponibles
uv run scripts/query.py --exemples    # questions déjà écrites
free -m                               # mémoire disponible, avant tout calcul
```

Les données ne sont pas versionnées. `data/` est dans le `.gitignore`. Ne jamais committer de
données, même un extrait. Ne jamais faire figurer de nom d'auteur ni de lien d'avis dans un
document de `documentations/`.

---

# 9. Où trouver quoi

| Fichier | Contenu |
|---|---|
| `BACKLOG.md` | État d'avancement, décisions, colonnes retenues |
| `documentations/2026-09-06-reprise-qualification-des-suppressions.md` | Les cinq défauts et le plan de reprise |
| `documentations/2026-09-06-enquete-fiches-purgees-et-plan.md` | Pourquoi ces entreprises ont perdu leurs avis |
| `documentations/2026-09-06-synthese-etat-et-resultats.md` | Synthèse des résultats. **Chiffres invalidés.** |
| `documentations/2026-09-06-facteurs-et-programme-danalyse.md` | Cadrage initial. **Périmètre à revoir.** |
| `data/exports/exports/README.md` | Schéma des données d'origine |
| `CLAUDE.md` | Instructions du projet |
