# Le projet en une lecture

Document à transmettre à quelqu'un qui arrive. Il se suffit à lui-même. Les renvois vers les
autres fichiers permettent d'approfondir un point précis.

Écrit le 2026-09-14.

---

## 1. Ce qu'on cherche

Google supprime des avis sur les fiches Google Maps. Certains sont faux, et les retirer est le
but recherché. D'autres sont de vrais avis écrits par de vrais clients, et leur suppression est
une erreur.

**On cherche quelles caractéristiques banales d'un avis font qu'il a plus de chances d'être
supprimé.** L'objectif est de repérer les avis honnêtes qui sautent. La question symétrique,
« comment détecter un faux avis », sort du sujet.

Commanditaire : Axel, dirigeant de ReviewFlowz, un outil de gestion d'avis clients. Il veut
pouvoir dire à ses clients ce qui fait disparaître un avis légitime.

---

## 2. Les données

Un robot a suivi **9 048 établissements Google Maps pendant quatorze jours**, du 11 au 24 août
2026. Chaque jour, il relève la totalité des avis de chaque fiche. Au total **4,88 millions
d'avis**.

**Un avis qui n'apparaît plus à un passage est considéré comme supprimé.** Retenez cette phrase :
c'est une déduction de notre part. Google ne nous signale rien. Toute la section 4
existe parce que cette déduction est parfois fausse.

Le panel n'a pas été tiré au hasard. Il couvre sept secteurs, deux régions (États-Unis et Europe
hors Royaume-Uni) et trois tailles d'entreprise. **L'unité tirée au sort est le groupe** : quand un groupe est retenu, tous ses établissements
entrent. Deux fiches
d'une même enseigne ne sont donc pas deux informations indépendantes, et les calculs en tiennent
compte.

Les fichiers font 838 Mo et contiennent des données personnelles — nom de l'auteur, lien vers son
profil, texte de l'avis. Ils ne sont pas dans le dépôt. **Ne jamais en copier dans un fichier
versionné.**

---

## 3. Les deux études, et pourquoi il y en a eu deux

C'est la partie qui déroute quand on arrive. Le dépôt contient deux dossiers d'analyse. Un seul
est vivant.

### L'étude exploratoire — du 4 au 9 septembre, aujourd'hui gelée

**Pourquoi elle a existé.** On venait de recevoir l'export et personne ne savait ce qu'il y avait
dedans. Avant de modéliser quoi que ce soit, il fallait regarder les données, comprendre ce que
le robot voit et ce qu'il rate. Le travail s'est fait en local, avec DuckDB, directement sur les
fichiers.

**Ce qu'elle a apporté, et c'est considérable :**

1. **La découverte que le comptage de base était faux.** « L'avis a disparu » ne veut pas dire
   « Google l'a supprimé ». Sur 5 230 disparitions constatées, 483 n'en sont pas — voir la
   section 4. Sans cette correction, tous les résultats suivants auraient été décalés de 9 %.
2. **Les pièges du jeu de données**, listés en section 5. Chacun a produit une erreur réelle
   avant d'être compris.
3. **Des résultats qui tiennent encore**, repris en section 6 : le pic de suppression au septième
   jour, le lien entre afflux récent et mortalité des vieux avis, ce qui fait qu'un avis tombe
   plutôt qu'un autre.

**Pourquoi elle est gelée.** Quand la régression a démarré, elle a construit son propre corpus
dans BigQuery, avec ses propres règles. Pendant quelques jours, deux définitions d'une
suppression et deux jeux de chiffres ont coexisté. Le projet est devenu impossible à expliquer :
le même effet circulait avec quatre valeurs différentes, sans que rien ne dise laquelle
répondait à quelle question.

Le dossier reste sur le disque parce que ses notes portent le raisonnement qui a mené aux
décisions actuelles. **Mais on n'y écrit plus, on n'y relance rien, et on ne cite aucun de ses
chiffres directement.** Ce qui en reste valable a été remonté dans `docs/`.

Si vous devez quand même l'ouvrir : commencez par `etude-exploratoire/documentations/INDEX.md`,
qui dit quelle note porte des chiffres encore valables et laquelle porte des chiffres d'avant la
correction. Sans lui, rien ne les distingue.

**Une réserve à connaître** : les cinq notes régénérées le 9 septembre ont des tableaux à jour,
mais les paragraphes de commentaire écrits en dur dans les programmes n'ont jamais été relus.
Vérifier toute phrase chiffrée contre le tableau qui la précède.

### L'étude de régression — en cours, c'est là qu'on travaille

Elle construit une table dans BigQuery, une ligne par avis, et cherche ce qui fait varier le
risque de suppression. **225 757 avis** publiés entre le 13 mai et le 16 août, sur 8 205 fiches,
dont **2 595 supprimés** — 1,15 %.

Trois étapes, dans cet ordre :

| | Fichier | Produit |
|---|---|---|
| 1 | `logistic-regression-study/sql/01_selection_panel.sql` | le corpus, 225 757 avis |
| 2 | `logistic-regression-study/sql/02_adding_features.sql` | les 42 caractéristiques |
| 3 | `logistic-regression-study/python/07_regression_panel.py` | les résultats |

**Tout se passe dans BigQuery**, sauf la modélisation. Pas de version parallèle en local : c'est
en dupliquant des définitions que l'étude précédente a fini par se contredire elle-même.

**`sql/02_adding_features.sql` ne se modifie pas sans l'accord de Romain.** Le changer oblige à
reconstruire la table et à relancer tous les modèles.

---

## 4. Ce qu'on appelle une suppression

Le fichier contient une colonne qui dit à quelle date le robot n'a plus retrouvé un avis. Deux
situations rendent la déduction fausse.

**Le bug d'enregistrement — 24 avis.** Même auteur, même note, même date de publication, mais un
texte entièrement différent d'une ligne à l'autre. C'est l'auteur qui a réécrit son avis et le
robot qui l'a mal enregistré.

**Le raté de collecte.** L'avis est absent un seul jour, puis revient identique. Sur les avis qui
disparaissent puis reviennent, 71 % sont absents une seule journée. Un vrai retrait contesté puis
annulé par Google prend plusieurs jours.

**La règle : une absence de deux jours ou plus est une vraie suppression.** Elle est datée du jour
de la première disparition.

Résultat : **5 230 disparitions constatées, portées par 5 109 avis différents, dont 4 747
retenues comme de vraies suppressions.**

---

## 5. Avant de toucher à un chiffre

### Un chiffre ne se cite jamais seul

C'est la règle la plus importante du projet, et elle vient d'une douzaine de désaccords entre nos
propres fichiers. Presque aucun n'était une erreur de calcul : c'étaient **des questions
différentes qui portaient le même nom**.

Un exemple réel. « Combien d'avis ont plusieurs enregistrements ? » a eu deux réponses, 617 et
602, et les deux sont justes :

- **617** est le nombre de **lignes** en trop dans le fichier ;
- **602** est le nombre d'**avis** concernés — certains ont trois lignes.

Écrire « 617 avis » est faux, et c'était écrit dans le fichier d'instructions du projet.

**Donc : toujours dire ce que le chiffre compte — des lignes, des avis, des établissements ? — et
sur quelle population.**

### L'âge de l'avis écrase tout le reste

Le risque de suppression est **divisé par 21** entre un avis du jour et un avis de trois mois.

Une comparaison qui ne tient pas compte de l'âge mesure surtout une différence d'âge. C'est ce
qui faisait croire que répondre à un avis le protégeait : les avis anciens ont eu le temps de
recevoir une réponse, et ils ne risquent presque plus rien. Les deux choses bougent ensemble sans
que l'une cause l'autre.

### Ne jamais prédire avec une information qu'on n'a qu'après coup

Le temps écoulé avant la suppression n'est connu que pour les avis déjà supprimés. S'en servir
comme caractéristique reviendrait à deviner un événement avec une information obtenue après qu'il
s'est produit. Même piège pour « l'avis a une réponse » quand on le mesure à la fin.

### Six enseignes portent 39 % des suppressions

Quatre chaînes américaines de traitement antiparasitaire et deux salles de sport espagnoles.
**Tout résultat doit être produit deux fois, avec et sans elles.** Les scripts ont une option
pour ça.

### Ce que l'export ne dit pas

- Les caractéristiques d'un avis sont son état **au dernier passage où on l'a vu**. L'export ne
  garde pas leur valeur à chaque passage.
- **Une réponse de commerçant retirée est invisible.**
- **Le filtrage avant publication est invisible** : aucun avis contenant un lien n'a été supprimé
  pendant le suivi, alors qu'il en existe. Ces avis-là sont bloqués avant d'être mis en ligne. On
  ne voit donc qu'une partie de la modération.

---

## 6. Ce qu'on sait aujourd'hui

**Comment lire.** « ×2 » veut dire : deux fois plus supprimé qu'un avis identique par ailleurs.
Les crochets donnent la marge d'incertitude ; quand elle contient 1, on ne voit pas d'écart.

### Le résultat principal : deux comportements opposés

Sur 10 000 avis de chaque groupe, combien ont disparu :

| Note | États-Unis | Europe |
|---|---:|---:|
| 1 étoile | 262 | 585 |
| 3 étoiles | 65 | 24 |
| 4 étoiles | 61 | 24 |
| **5 étoiles** | **145** | **36** |

**Aux États-Unis, l'avis 5 étoiles est supprimé plus souvent que l'avis 3 ou 4 étoiles.** En
Europe, c'est l'inverse. Les additionner revient à faire la moyenne de deux choses sans rapport.

Sur l'ensemble du panel, **71 % des suppressions portent sur un avis 5 étoiles**. C'est le sujet
du livrable : Google retire ici des avis que rien ne désigne comme faux.

### Ce qui fait qu'un avis récent saute

À âge comparable, sur les 225 757 avis du corpus :

| | Risque relatif | Sans les six enseignes |
|---|---:|---:|
| Compte d'auteur sans niveau Local Guide | ×2,30 | ×2,51 |
| Secteur des services à domicile | ×5,73 | ×3,16 |
| Établissement américain | ×1,99 | ×2,14 |
| Avis 1 étoile | ×6,34 | ×3,56 |

### Répondre vite protège

**Hors des quatre chaînes antiparasitaires, répondre dans les deux jours divise le risque par
1,8 : ×0,56 [0,37 – 0,85].** Sur le corpus complet, l'effet n'est plus visible — ces chaînes
portent 37 % des suppressions de cette population et l'effacent.

**Annoncer le ×0,56 sans dire qu'il exclut ces quatre chaînes serait faux.**

Deux chiffres ne sont plus citables : « ×0,30 » et « répondre protège 3,7 fois ». Ils comptaient
la réponse à la fin de l'histoire, ce qui mesurait en partie « avoir survécu assez longtemps pour
en recevoir une ».

### Les acquis de l'étude exploratoire

**Le pic au septième jour de vie de l'avis.** 449 avis supprimés à cet âge exactement, soit 1,4 %
des 32 609 avis observés à 7 jours. Trois à dix fois le risque des âges voisins. Vérifié comme un
effet d'âge : il est étalé sur 12 des 13 journées de suivi et sur 144
établissements. **Ce qui se joue à 7 jours n'est pas expliqué.**

**Les vieux avis meurent davantage là où il y a eu un afflux récent.** Sur les avis de plus d'un
an, à marché comparable : quand une fiche a reçu récemment un afflux valant 1 à 3 % de son stock,
ses vieux avis disparaissent 1,46 fois plus. Entre 3 et 10 %, 1,76 fois plus. C'est le seul
chiffrage direct de l'erreur de modération.

**La modération ne porte pas sur des fautes visibles.** Onze marqueurs cherchés dans les textes
supprimés — insultes, spam, charabia. Les avis supprimés ne sont pas majoritairement des textes
fautifs. C'est ce qui fonde l'angle du livrable.

---

## 7. Ce qu'on ne peut pas dire

À porter dans le livrable, sans exception.

- **On ne peut pas distinguer un faux avis d'une erreur de modération** par collecte automatique.
  On montre que beaucoup d'avis supprimés n'ont aucune faute visible ; on ne prouve pas qu'ils
  sont authentiques.
- **On ne voit que quatorze jours.** Les suppressions rapides sont visibles, les révisions à six
  mois ne le sont pas.
- **On ne sait pas pourquoi Google supprime.** Rien ne dit si une suppression vient d'un
  traitement automatique, d'un signalement du commerçant ou d'une contestation de l'auteur. Toute
  phrase sur la cause est une hypothèse et doit être écrite comme telle.
- **Pour la réponse du commerçant, le sens de la cause n'est pas établi.** Celui qui répond en
  deux jours est aussi celui qui surveille sa fiche et signale les avis qu'il juge illégitimes.
- **Le panel ne couvre pas tout** : 41 pays dont un seul hors d'Europe. Le Royaume-Uni en est
  absent.

---

## 8. Par où vous pouvez commencer

Les sujets ouverts, du plus utile au moins urgent.

1. **Comprendre les quatre chaînes américaines de traitement antiparasitaire.** Elles portent
   27 % des suppressions du panel, presque toutes sur des avis 4 et 5 étoiles, et **aucune
   caractéristique disponible ne les explique** : les auteurs sont ordinaires, les textes tous
   différents, il n'y a pas de pic d'afflux. Deux pistes : leurs avis supprimés ont plus souvent
   une réponse du commerçant, et leurs textes nomment très souvent un technicien par son prénom.
2. **Chercher les attaques par avis négatifs dans tout le panel.** Deux ont été trouvées par
   hasard. Le balayage systématique n'a jamais été fait.
3. **Croiser le pic au septième jour avec ce qui fait tomber un avis.** Qui sont les avis qui
   sautent à 7 jours ? C'est le candidat le plus direct pour l'angle du livrable.
4. **Revoir la façon dont on mesure la qualité du modèle.** Aujourd'hui un quart des
   établissements est mis de côté une seule fois, au hasard. En Europe ce tirage est tombé sur
   des fiches 2,3 fois moins touchées que la moyenne, ce qui rend les niveaux de risque annoncés
   inutilisables. Une correction est écrite, en attente.

---

## 9. Comment travailler

**Ne rien lancer avant d'avoir posé la méthode avec Romain.** La règle vient d'une session où
quatre analyses ont été enchaînées et trois jetées. On écrit ce qu'on va calculer, sur quoi, avec
quel dénominateur, puis on lance.

**Précautions machine.** La machine de travail a 7,7 Go de mémoire et tourne sous WSL. Un calcul
qui prend tous les cœurs coupe la connexion de l'éditeur. Au-delà de deux minutes : `nice -n 19`,
`free -m` avant de lancer, deux calculs lourds au maximum en même temps.

**Jamais de nom d'auteur, de lien d'avis ou de texte d'avis dans un fichier versionné.**

### Où trouver quoi

| | |
|---|---|
| `docs/01-etude.md` | la question, le panel, les choix de modélisation |
| `docs/02-donnees.md` | les définitions, les pièges, pourquoi les chiffres divergent |
| `docs/03-resultats.md` | tous les résultats, avec leurs réserves |
| `docs/04-enseignements.md` | les erreurs déjà commises, et ce qui a été construit puis jeté |
| `docs/BACKLOG.md` | l'historique et le reste à faire |
| `logistic-regression-study/output-study/` | les sorties chiffrées et les notes qui les commentent |

**Lisez `docs/04-enseignements.md` avant de produire un chiffre.** Il liste quinze erreurs déjà
commises sur ce projet, avec le texte fautif exact et le contrôle qui aurait évité chacune. Elles
se reproduisent facilement.
