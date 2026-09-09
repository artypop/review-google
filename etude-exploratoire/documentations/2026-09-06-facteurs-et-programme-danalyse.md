---
date: 2026-09-06
projet: reviewflowz-analyse-google
titre: "Ce qu'on a trouvé dans les données, et comment on va analyser"
statut: à jour au 2026-09-06, décisions prises
---

# Ce qu'on a trouvé dans les données, et comment on va analyser

> ## MIXTE — vérifié le 2026-09-08
>
> **Méthode, décisions et questions ouvertes : toujours valables.**
> **Chiffres de résultat : périmés**, calculés avant la correction du comptage. Dans ce
> document : 84 % / 39 fiches / 20 %, 106 761, 2 853, 2,67 %, 0,107 %, 264 avis sur 816, 1 399 établissements touchés.
>
> Comptage de référence aujourd'hui : **4 747 suppressions** sur 5 230 disparitions brutes.
> Résultats à jour : `2026-09-08-synthese-de-la-journee.md`. Inventaire : `INDEX.md`.

Cette note fait deux choses : elle raconte les cinq découvertes qui ont changé le cadrage de
l'étude, et elle décrit le programme d'analyse qui en découle.

Tous les chiffres viennent de requêtes sur les fichiers de l'export, reproductibles.

---

## En bref

1. **Google supprime les avis récents, presque jamais les vieux.** Le risque culmine une à deux
   semaines après la publication, puis s'effondre. Entre un avis d'une semaine et un avis de
   trois ans, le rapport est de 1 à 163.

2. **Du coup, les premiers chiffres du 4 septembre étaient faussés.** Ils comparaient des avis
   d'âges différents. Une fois corrigés, quatre d'entre eux changent de sens.

3. **Ce ne sont pas des avis isolés qui sautent, ce sont des fiches entières qui se font
   nettoyer.** 84 % des établissements n'ont perdu aucun avis. 39 fiches concentrent 20 % de
   toutes les suppressions.

4. **On analyse donc deux questions séparément** : quelle entreprise se fait taper, puis, dans
   une entreprise qui se fait taper, quel avis tombe.

5. **On se concentre sur les avis de moins de 30 jours.** C'est là que tout se joue, et le taux
   de suppression y est de 2,7 % au lieu de 0,1 % — des chiffres enfin exploitables.

---

## 1. Les cinq découvertes

### 1.1 Google modère dans les deux premières semaines, puis oublie

C'est le fait le plus important de l'étude, et il n'était dans aucun document de cadrage.

Pour chaque avis et chaque passage du robot, on a regardé : est-il encore là ? Cela donne le
**risque quotidien** — sur 1 000 avis en ligne, combien disparaissent d'un passage à l'autre.

| Âge de l'avis | Risque quotidien | Sur 10 000 avis, il en disparaît |
|---|---:|---:|
| 0 à 2 jours | 0,363 % | 36 |
| 3 à 6 jours | 0,403 % | 40 |
| **7 à 13 jours** | **0,500 %** | **50** |
| 14 à 20 jours | 0,252 % | 25 |
| 21 à 29 jours | 0,089 % | 9 |
| 30 à 59 jours | 0,034 % | 3 |
| 2 à 6 mois | 0,011 % | 1 |
| 6 à 12 mois | 0,006 % | moins de 1 |
| 1 an et plus | 0,0032 % | moins de 1 |

**Le pic est à 7-13 jours, puis c'est fini.** À un mois, le risque a été divisé par 15. À un an,
par 156. Un avis qui a passé son premier mois est tranquille.

Cette lecture est fiable parce qu'elle tient compte de deux difficultés :

- les avis publiés pendant les 14 jours de collecte ont été observés moins longtemps que les
  autres — on ne peut pas comparer leurs taux bruts ;
- un avis ancien qu'on observe aujourd'hui est, par définition, un avis qui a survécu à sa
  période dangereuse. Le compter comme « peu supprimé » sans le dire serait trompeur.

Le calcul par passage règle les deux : chaque avis ne compte que pour les jours où on l'a
réellement observé.

### 1.2 Pourquoi ça invalide les premiers chiffres

Quand on compare deux groupes d'avis sans regarder leur âge, une bonne partie de l'écart ne
mesure que le fait qu'un groupe est plus jeune que l'autre.

Exemple concret. On avait annoncé le 4 septembre que les Local Guides voyaient leurs avis
supprimés 2,9 fois moins souvent. En réalité les Local Guides ont surtout beaucoup d'avis
anciens, et les avis anciens ne sautent jamais. À âge comparable, l'écart tombe entre 1,6 et 2,5.

L'inverse existe aussi : l'effet de la note était **sous-estimé**. Sur les avis de 7 à 30 jours,
un avis 1 étoile est supprimé 24 fois plus qu'un 4 étoiles, pas 9 fois.

**Règle appliquée partout depuis** : aucune comparaison n'est publiée sans avoir été recalculée à
âge comparable. Et quand deux populations diffèrent par autre chose que l'âge — le secteur, par
exemple — on recalcule aussi à composition comparable. Voir 3.3.

### 1.3 Les suppressions sont concentrées sur très peu de fiches

| Ce que la fiche a perdu | Nombre de fiches | Suppressions | Part du total |
|---|---:|---:|---:|
| Rien | 7 598 | 0 | 0 % |
| Moins de 1 % de ses avis | 1 235 | 2 890 | 55,3 % |
| 1 à 5 % | 125 | 1 318 | 25,2 % |
| 5 à 20 % | 21 | 382 | 7,3 % |
| 20 % et plus | 18 | 640 | 12,2 % |

**84 % des établissements n'ont rien perdu du tout.** À l'autre bout, 39 fiches — moins d'une
sur deux cents — portent 20 % des suppressions. Le cas extrême est une salle de sport espagnole
qui a perdu 264 avis sur 816, soit un tiers de sa fiche, en quatorze jours.

Deux phénomènes différents sont donc mélangés :

- **la purge de fiche** : Google repère quelque chose au niveau de l'établissement et efface en
  masse. Rare, spectaculaire, et responsable de la moitié du volume ;
- **la suppression à l'unité** : un avis isolé tombe sur une fiche par ailleurs intacte.

Si on lance un seul modèle sur l'ensemble, il apprendra surtout à reconnaître ces 39 fiches — des
salles de sport espagnoles, des services à domicile américains — au lieu d'apprendre ce qui
distingue un avis d'un autre. D'où les deux analyses séparées, décrites en 3.2.

### 1.4 Le « Local Guide oui/non » est une mauvaise variable

Dans les données, deux colonnes coexistent : `local_guide` (oui/non) et `local_guide_level`
(un chiffre de 1 à 10). Le oui/non n'est rien d'autre que « niveau supérieur ou égal à 4 ».

Or le niveau, lui, a une progression nette :

| Niveau | Avis | Taux de suppression |
|---:|---:|---:|
| 1 | 301 554 | 0,145 % |
| 2 | 958 717 | 0,146 % |
| 3 | 1 103 852 | 0,141 % |
| 4 | 575 746 | 0,110 % |
| 5 | 846 528 | 0,051 % |
| 6 | 693 732 | 0,029 % |
| 7 | 286 682 | 0,028 % |
| 8 et plus | 96 117 | 0,040 % |

Plat de 1 à 3, chute franche de 4 à 6, plat ensuite. **La vraie frontière est entre 5 et 6, pas
à 4.** Le niveau 4, qui porte pourtant le badge Local Guide, est presque aussi exposé qu'un
niveau 1.

On garde donc le niveau, en trois paliers (1-3 / 4-5 / 6 et plus), et on abandonne le oui/non.

### 1.5 Deux champs vides qui signifient « compte tout neuf »

Deux anomalies nous ont occupés, et **la vérification manuelle de Romain les a résolues**.

**Le niveau Local Guide absent** — 15 223 avis, supprimés 16 à 19 fois plus que les autres à âge
comparable. Deux vérifications sur des profils réels :

- *Sur les avis anciens* (45 profils ouverts) : les comptes sont vivants et actifs — médiane de
  52 avis, certains remontent à 2012 — et ils n'affichent aucun niveau, encore aujourd'hui.
  Lecture retenue : **ces gens ne sont pas inscrits au programme Local Guides**, qui fonctionne
  sur adhésion volontaire. On peut publier des centaines d'avis sans y souscrire.
- *Sur les avis récents* (30 profils ouverts) : tout autre chose. 19 profils sur 20 affichent
  aujourd'hui un niveau 1 ou 2, et un compteur à 1 avis — celui qu'on a collecté. Au moment du
  passage du robot, **le compte venait de publier son tout premier avis** et Google ne lui avait
  pas encore attribué de niveau.

**Le compteur d'avis à 0** — 236 846 avis, soit 4,9 % du corpus. Ce n'est pas un compte sans
avis : 3 656 auteurs annoncés à 0 ont entre 2 et 12 avis dans notre propre panel. Là aussi il
s'agit d'un compte que Google n'a pas encore comptabilisé.

Trois conséquences pratiques :

1. **Ces deux champs sont des états transitoires, pas des catégories.** Un pipeline qui
   remplacerait le compteur vide par un zéro ferait dire au modèle « cet auteur n'a jamais écrit
   d'avis », ce qui est faux sur 4,9 % des lignes.
2. **Sur les avis récents, les deux vides ensemble forment une signature nette** : premier avis
   d'un compte créé de la veille. C'est un facteur légitime, connu au moment de la publication.
3. **Ce sont deux populations différentes selon l'ancienneté de l'avis**, et elles n'entrent pas
   ensemble dans le modèle.

### 1.6 On peut suivre un auteur d'une fiche à l'autre

Le lien de chaque avis contient l'identifiant du contributeur. Il est stable et s'extrait sans
collecte supplémentaire. Le panel compte 4 570 502 auteurs distincts, dont 255 618 apparaissent
sur plusieurs fiches suivies.

| Avis de l'auteur dans le panel | Auteurs | Taux de suppression |
|---|---:|---:|
| 1 | 4 314 882 | 0,089 % |
| 2 | 217 236 | 0,249 % |
| 3 à 5 | 37 398 | 0,248 % |
| 6 à 20 | 984 | 0,290 % |

Un auteur présent sur plusieurs fiches du panel voit ses avis supprimés 2,8 fois plus. Le taux
est calculé par avis, il n'y a donc pas d'effet mécanique du type « plus il en écrit, plus il en
perd ».

Ce déblocage rend gratuites deux mesures que la méthodologie donnait pour coûteuses : les
répétitions d'un même auteur, et sa zone géographique reconstruite depuis les pays des fiches
qu'il a notées.

---

## 2. Les facteurs retenus

La colonne « actionnable » répond à la question laissée ouverte au §4 du plan de travail : sur
quoi le client peut-il réellement agir.

### Sur l'avis lui-même

| Facteur | Comment on le mesure | Actionnable |
|---|---|---|
| Âge au moment du passage | En jours | Non, mais structure tout |
| Note | 1 à 5, en catégories séparées, jamais en droite | Non |
| Présence et longueur du texte | Nombre de caractères, en paliers | Oui |
| Photos | Nombre, pas seulement présence | Oui |
| Réponse du propriétaire | Présence d'une réponse | **Oui, directement** |
| Langue différente de celle de la fiche | Comparaison à la langue dominante de la fiche | Non |
| Avis modifié depuis publication | Date de modification postérieure à la création | Oui |

**La réponse du propriétaire est le seul levier direct du client.** Elle est donc prioritaire à
valider. Attention au sens de la causalité : il faudra vérifier que la réponse précède bien la
disparition, et pas l'inverse.

### Sur l'auteur

| Facteur | Comment on le mesure |
|---|---|
| Niveau Local Guide | Paliers 1-3 / 4-5 / 6 et plus |
| Compte tout neuf | Niveau absent **et** compteur à 0 |
| Nombre d'avis de l'auteur | En paliers, le 0 traité comme « inconnu » et non comme zéro |
| Nombre de photos de l'auteur | Idem |
| Présence sur plusieurs fiches du panel | Comptage par identifiant de contributeur |
| Rafale : plusieurs avis le même jour | Écart entre premier et dernier avis inférieur à un jour |

### Sur l'établissement

| Facteur | Comment on le mesure | Effet mesuré |
|---|---|---|
| Vitesse de collecte des avis | Avis des 30 derniers jours rapportés au stock | **×26** |
| Secteur et taille du groupe | Les 7 secteurs, les 3 paliers de taille | ×10 |
| Région | États-Unis ou Europe | ×1,7 |
| Note moyenne et son évolution | Reconstruites depuis les histogrammes des 14 passages | à mesurer |
| Volume d'avis | Nombre total | à mesurer |

La vitesse de collecte est le signal d'établissement le plus fort :

| Part du stock reçue en 30 jours | Fiches | Taux de suppression |
|---|---:|---:|
| Moins de 1 % | 2 594 | 0,040 % |
| 1 à 3 % | 2 761 | 0,078 % |
| 3 à 10 % | 1 466 | 0,192 % |
| 10 % et plus | 166 | **1,047 %** |

C'est la signature d'une campagne d'avis. **Réserve importante** : une fiche qui reçoit beaucoup
d'avis d'un coup a mécaniquement un stock plus jeune, et l'âge pèse ×163. Une bonne part de cet
écart est peut-être de l'âge déguisé. C'est l'objet du Test 1 (voir 3.4).

Attention aussi à la taille : les groupes de 2-3 sites et de 11-19 sites ont été volontairement
exclus du panel. La taille se lit donc comme **trois paliers**, jamais comme une courbe. On ne
peut pas écrire « plus le groupe est gros, plus il perd d'avis ».

---

## 3. Le programme d'analyse

### 3.1 Le périmètre : les avis de moins de 30 jours

Décidé au vu de la courbe de risque : la frontière des 30 jours est exactement là où la chute se
termine.

| | Corpus entier | Avis de moins de 30 jours |
|---|---:|---:|
| Avis | 4 878 151 | 106 761 |
| Suppressions | 5 230 | 2 853 |
| Taux | 0,107 % | **2,67 %** |

On garde 55 % des suppressions en ne gardant que 2 % des lignes. Le taux est multiplié par 25,
ce qui change trois choses : les probabilités redeviennent présentables au client, les
précautions liées aux événements très rares deviennent inutiles, et tout tourne en quelques
secondes.

**Le stock ancien n'est pas jeté.** Il reste dans les données et sert : au Test 2, où les avis
anciens sont précisément la grandeur mesurée ; aux caractéristiques d'établissement ; et à toute
comparaison ancien / récent. Ce qu'on ne cherche pas à faire, c'est expliquer ce qui fait
supprimer un avis *ancien* — sauf si un résultat intéressant apparaît en chemin.

### 3.2 Deux analyses séparées

**Analyse A — quelle entreprise se fait taper.**
Une ligne par établissement : 9 048 au total, 1 399 touchés. On cherche ce qui distingue les
fiches où Google intervient. C'est là qu'on mesure l'effet du secteur, de la taille, de la
région et de la vitesse de collecte.

**Analyse B — dans une fiche touchée, quel avis tombe.**
Une ligne par avis, uniquement dans les 1 399 fiches touchées. Le principe : **on ne compare que
des avis d'une même fiche entre eux.**

Concrètement, au lieu de demander « les avis 1 étoile sautent-ils plus que les 5 étoiles ? » sur
l'ensemble du panel, on demande « dans cette salle de sport précise qui a perdu des avis, est-ce
les 1 étoile ou les 5 étoiles qui sont tombés ? », et on additionne la réponse sur les 1 399
fiches. Tout ce qui est propre à la fiche — son secteur, son pays, sa clientèle, sa politique de
modération — sort de l'équation, puisque c'est identique pour tous les avis comparés.

Deux avantages décisifs :

- plus besoin de corriger pour le secteur, le pays ou la taille : c'est automatique ;
- une fiche entièrement purgée, où tous les avis sont tombés, n'apporte aucune comparaison utile
  et se retire d'elle-même du calcul. Les 39 fiches qui écrasaient tout cessent de peser.

**Conséquence à retenir** : secteur, taille et région ne peuvent pas être des variables de
l'analyse B, puisqu'ils sont identiques dans une fiche donnée. Ils n'y apparaissent que sous
forme de croisements — « l'effet de la note est-il le même aux États-Unis et en Europe ? ».

### 3.3 Deux règles de calcul appliquées partout

**Toujours recalculer à âge comparable.** Démontré en 1.1 et 1.2.

**Toujours recalculer à composition comparable quand on compare deux groupes hétérogènes.**
Exemple vécu : les États-Unis semblaient supprimer les 5 étoiles récentes 3,3 fois plus que
l'Europe. Mais 29 % des 5 étoiles récentes américaines sont dans les services à domicile — le
secteur le plus supprimé — contre 8 % en Europe. À composition sectorielle identique, l'écart
tombe à 2,4. **38 % de l'écart n'était que de la composition.** Et il n'est pas général : sur
l'automobile, la restauration et l'hôtellerie, les deux régions sont identiques.

### 3.4 Trois tests ciblés

Ce sont eux qui portent l'angle du livrable, davantage que les modèles.

**Test 1 — la vitesse de collecte, une fois l'âge neutralisé.** Si l'écart ×26 s'effondre, alors
Google ne détecte pas les campagnes : il modère juste des avis récents, et une fiche qui en
reçoit beaucoup en perd beaucoup. S'il tient, la détection de campagne au niveau de la fiche est
démontrée.

**Test 2 — le dommage collatéral.** Dans les fiches qui reçoivent une vague d'avis, est-ce que le
vieux stock, sans rapport avec la campagne, se fait supprimer lui aussi ? On le compare à des
fiches témoins de même secteur, taille, pays et volume. **C'est la mesure de faux positifs la
plus directe que ces données permettent** — c'est l'angle de l'étude, et c'est le seul endroit où
il devient un chiffre.

**Test 3 — la vérification de visite.** Dans les services à domicile, où personne ne se rend à
l'adresse, un auteur géographiquement éloigné est-il davantage supprimé qu'un auteur proche ?
Réserve honnête : cette mesure n'existe que pour 5 % des avis et la maille est le pays. Le test
donnera probablement une fourchette large. À tenter, à ne pas promettre.

### 3.5 Règles de restitution

- **Toujours en risque relatif** (« deux fois plus »), jamais en probabilité brute.
- **Ne jamais évaluer un modèle sur son taux de bonnes réponses** : prédire « jamais supprimé »
  donne 99,89 % de réussite et ne sert à rien.
- **Séparer les jeux d'entraînement et de test par établissement et par auteur**, jamais au
  hasard : sinon le modèle reconnaît la boutique au lieu d'apprendre une règle.
- **Contrôle obligatoire** : refaire tourner sans les 39 fiches les plus purgées et vérifier que
  les conclusions tiennent.

---

## 4. Ce qu'on a écarté

- **Score de génération par IA.** Les détecteurs sont peu fiables et classent à tort les textes
  de non-anglophones (Liang et al., 2023). Construire un facteur là-dessus dans une étude qui
  dénonce les faux positifs serait indéfendable.
- **Textes identiques au sein d'une même fiche.** Sur 2,9 millions de textes, seuls 7 646 avis
  sont concernés. Le signal « avis pré-rédigé par l'entreprise » n'existe pas dans ces données.
  On le documente comme résultat négatif plutôt que de payer une détection de quasi-doublons.
- **Adresse, téléphone, complétion de la fiche.** Absents de l'export.
- **Détection des insultes.** Le test reste faisable, mais quel qu'en soit le résultat le cas
  sera trop rare pour entrer au modèle. À traiter comme une observation, pas comme un facteur.
- **Expérimentations contrôlées** (publier de faux avis pour voir). Contraires aux conditions
  d'utilisation, et illégales au Royaume-Uni depuis le DMCC Act.
- **Mention du nom d'un employé.** Faisable mais coûteux, pour un signal non mesuré. À revoir
  seulement si le temps le permet.

---

## 5. Où on en est

Fait : périmètre et architecture arrêtés, deux vérifications manuelles menées, tables d'analyse
construites, premiers résultats facteur par facteur produits (voir la note
`2026-09-06-premiers-resultats-facteur-par-facteur.md`).

Reste : les analyses A et B, puis les trois tests. Un seul arbitrage est encore ouvert, la façon
de faire entrer l'âge dans le modèle — courbe continue ou paliers. Sans conséquence sur
l'analyse A.

Le suivi détaillé est dans `BACKLOG.md`.

---

## Sources

- `documentations/methodologie.md` — hypothèses de campagne et de vérification de visite, tests
  ciblés §6.1 et §6.2, repris en 3.4.
- `documentations/plan-de-travail.md` — plan initial, arbitrages §5, points à valider §6.
- `documentations/2026-09-04-...-vagues-1-14.md` — premiers chiffres, corrigés en 1.2.
- `documentations/reviewflowz-analyse-google-decisions.md` — décisions antérieures.
- `data/exports/exports/README.md` — schéma des données et définition d'une suppression.
- `scripts/build_tables.py` et `scripts/level1_bivariate.py` — tous les chiffres de cette note.
