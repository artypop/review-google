# Ce qu'on sait, et ce qu'on ne peut pas dire

Dernière mise à jour : 2026-09-14.

Ce document donne les résultats. Le détail de chaque calcul et sa méthode sont dans les notes
de `logistic-regression-study/output-study/`, citées à chaque fois.

**Comment lire un risque relatif.** « ×2 » veut dire : deux fois plus supprimé qu'un avis
identique par ailleurs. La fourchette entre crochets donne la marge d'incertitude. Quand elle
contient 1, le modèle ne voit pas d'écart.

---

## 1. Le résultat principal : deux phénomènes opposés dans le même corpus

Sur 10 000 avis de chaque groupe, voici combien ont disparu :

| Note de l'avis | États-Unis | Europe |
|---|---:|---:|
| 1 étoile | 262 | 585 |
| 3 étoiles | 65 | 24 |
| 4 étoiles | 61 | 24 |
| **5 étoiles** | **145** | **36** |

**Aux États-Unis, l'avis 5 étoiles est supprimé plus souvent que l'avis 3 ou 4 étoiles.** En
Europe, il l'est seize fois moins que l'avis 1 étoile. Ce sont deux comportements opposés, et
les additionner revient à faire la moyenne de deux choses qui n'ont rien à voir.

En volume : sur les 1 851 suppressions américaines, **1 590 frappent un avis 5 étoiles**, soit
86 %. Sur les 744 suppressions européennes, 422 frappent un avis 1 étoile, soit 57 %.

**Sur l'ensemble du panel, 1 850 des 2 595 suppressions portent sur un avis 5 étoiles, soit
71 %.** C'est le sujet du livrable : Google retire ici des avis que rien ne désigne comme faux.

Source : `output-study/2026-09-14-interpretation-panel.md`.

---

## 2. Ce qui fait qu'un avis récent saute

Mesuré sur les 225 757 avis publiés du 13 mai au 16 août, à âge comparable.

| Ce qu'on regarde | Risque relatif | Sans les six enseignes |
|---|---:|---:|
| Compte d'auteur sans niveau Local Guide | ×2,30 | ×2,51 |
| Secteur des services à domicile | ×5,73 | ×3,16 |
| Établissement américain | ×1,99 | ×2,14 |
| Avis 1 étoile (contre 5 étoiles) | ×6,34 | ×3,56 |

**Ces quatre effets vont dans le même sens partout**, y compris quand on retire les six
enseignes qui portent 39 % des suppressions. Le profil d'auteur est même le seul qui se
renforce sans elles, ce qui veut dire qu'il ne vient pas d'elles.

Attention au 1 étoile : il multiplie le risque par six, mais il ne concerne qu'une minorité des
suppressions. C'est un effet fort sur un petit volume.

### Trois effets qui changent de sens selon le découpage

Aucun ne doit être cité sans préciser sur quel groupe il est lu.

| | Tout | Sans les enseignes | États-Unis | Europe |
|---|---:|---:|---:|---:|
| Rafale d'auteur | ×9,54 | ×5,28 | ×49,30 | ×0,90 |
| Afflux d'avis sur la fiche ce jour-là | ×1,40 | ×0,87 | ×0,84 | ×2,17 |
| Texte de plus de 200 caractères | ×0,66 | ×1,38 | ×1,10 | ×0,51 |

La **rafale d'auteur** repose sur très peu de cas : 1 681 avis sur 225 757 ont deux dépôts ou
plus le même jour. Le gros du signal tient à une seule cellule, 100 avis à quatre dépôts le
même jour dont 44 supprimés — et ces 44 sont **entièrement** dans les enseignes signalées. Une
fois celles-ci retirées, la cellule compte 56 avis et zéro suppression.

Le **texte long** est le seul effet dont le sens s'inverse nettement : protecteur sur le corpus
entier, aggravant sans les enseignes. À examiner avant toute publication.

---

## 3. Répondre vite à un avis le protège-t-il ?

C'est la question du client d'Axel, et elle a une réponse.

**Hors des quatre chaînes américaines de traitement antiparasitaire, répondre dans les deux
jours divise le risque par 1,8 : ×0,56, fourchette [0,37 – 0,85].** Mesuré sur 14 170 avis
encore en ligne à la fin de leur deuxième jour, dont 316 supprimés entre le 3e et le 8e jour.

**Sur le corpus complet, l'effet n'est pas mesurable : ×0,79, fourchette [0,53 – 1,16].** Ces
quatre chaînes portent 37 % des suppressions de cette population et effacent l'effet moyen.

Comment le dire : « répondre dans les deux jours divise à peu près par deux le risque qu'un avis
récent soit supprimé, sauf sur quatre chaînes américaines de traitement antiparasitaire où
Google supprime des avis pour une raison qu'on n'a pas identifiée ». **Annoncer le ×0,56 sans
dire qu'il exclut ces quatre chaînes serait faux.**

L'effet tient quand on déplace le moment où l'on regarde : ×0,59 au premier jour, ×0,56 au
deuxième, ×0,46 au troisième, ×0,48 au quatrième.

Source : `output-study/2026-09-14-effet-reponse-commercant.md`.

### Trois chiffres cohabitent sur la réponse du commerçant

| Chiffre | Ce qu'il mesure |
|---|---|
| **×1,02** [0,75 – 1,38] | une réponse arrivée **avant le 11 août**, sur les avis de 0 à 90 jours. Aucun effet. |
| **×0,40** | une réponse présente au passage précédent, sur les avis de moins de 30 jours des fiches touchées |
| **×0,56** [0,37 – 0,85] | une réponse arrivée dans les **deux premiers jours**, hors les quatre chaînes |

Ils ne se contredisent pas. Le premier répond à « un avis qui porte déjà une réponse depuis
longtemps est-il mieux protégé ? » — non. Le troisième répond à « répondre vite à un avis qui
vient de tomber sert-il à quelque chose ? » — oui.

**Deux chiffres ne sont plus citables : « ×0,30 » et « répondre protège 3,7 fois ».** Ils
comptaient la réponse dans l'état où elle se trouvait au dernier passage du robot, ce qui
mesurait en partie « avoir survécu assez longtemps pour en recevoir une ».

---

## 4. Les résultats de l'étude exploratoire qui tiennent encore

Produits entre le 4 et le 9 septembre 2026, sur l'ensemble des 4,88 millions d'avis. **Le
dossier est gelé : ces chiffres ne sont plus régénérables sans le rouvrir.**

### Le pic au septième jour de vie de l'avis

**449 avis supprimés à l'âge de 7 jours exactement**, soit 1,377 % des 32 609 avis observés à cet
âge. Trois à dix fois le risque des âges voisins : 0,099 % à 4 jours, 0,131 % à 5 jours, 0,365 %
à 8 jours.

Ces nombres bruts se comparent directement parce qu'environ 32 000 avis sont observés à chaque
âge de 2 à 30 jours. Vérifié comme un effet d'âge : il est étalé sur 12 des 13
journées de suivi et sur 144 établissements, il survit au retrait des deux journées les plus
chargées.

**Ce qui se joue à 7 jours n'est pas expliqué.** Cycle de traitement automatique, ou délai de
réaction à un signalement ? Rien dans les données ne tranche.

### Où tombent les suppressions selon l'âge

Sur les 4 747 suppressions du corpus entier : **51,6 % frappent un avis de moins d'un mois,
30,3 % un avis de plus d'un an.**

Le vieux stock pèse par son volume : 4,1 millions d'avis contre 101 000 de moins d'un mois. Son
risque par passage reste cent fois plus faible.

### Les vieux avis meurent davantage là où il y a eu un afflux récent

C'est le seul chiffrage direct de l'erreur de modération.

Sur les avis de plus d'un an, à marché comparable : quand une fiche a reçu récemment un afflux
représentant 1 à 3 % de son stock, ses vieux avis disparaissent **1,46 fois plus**. Entre 3 et
10 %, **1,76 fois plus**. Les deux tiennent quand on retire les fiches attaquées.

**La tranche « 10 % et plus » n'est pas exploitable** : 9 disparitions seulement. Ne pas la
communiquer.

### Dans une fiche qui perd des avis, lequel tombe

Comparaison entre avis d'une même fiche, un même jour : 514 établissements, 61 202 observations,
2 623 disparitions. **Les 26 effets mesurés tiennent tous au contrôle de robustesse.**

Les plus forts : rafale d'auteur ×5,09, avis 1 étoile ×3,61, avis modifié depuis sa publication
×1,95, réponse du commerçant ×0,40.

Et un résultat qui va dans le sens du livrable : **un avis 5 étoiles est plus supprimé qu'un avis
4 étoiles** (×1,24). Le tri ne vise pas que les avis négatifs.

### Ce qui n'a pas tenu

Sur 68 effets rejoués sans les fiches attaquées, **49 tiennent, 8 sont des absences d'effet
stables, 5 sont fragiles, 6 ne tiennent pas.** Les six qui tombent sont tous dans le modèle qui
cherche quel établissement se fait toucher.

**Le modèle qui cherche l'ampleur d'une purge n'est pas exploitable** : il tourne sur 396 fiches
et six de ses effets changent de sens quand on en retire quatre.

**La vitesse à laquelle une fiche collecte des avis n'a aucun effet propre** sur son risque
d'être touchée.

### La modération ne porte pas sur des fautes visibles

Onze marqueurs cherchés dans les textes supprimés — insultes, spam, charabia. **Le résultat de
fond tient : les avis supprimés ne sont pas majoritairement des textes fautifs.** C'est ce qui
fonde l'angle du livrable.

Réserve : le dictionnaire couvre 7 langues sur 41 pays. C'est un plancher.

---

## 5. Ce qu'on ne peut pas dire

À porter dans le livrable, sans exception.

**On ne voit qu'une partie de la modération.** Le filtrage avant publication est invisible :
aucun avis contenant un lien n'a été supprimé pendant le suivi, alors qu'il en existe dans le
panel. Ces avis-là sont bloqués avant d'être mis en ligne.

**On ne peut pas distinguer un faux avis d'une erreur de modération** par collecte automatique.
L'étude montre que beaucoup d'avis supprimés n'ont aucune faute visible ; elle ne prouve pas
qu'ils sont authentiques.

**On ne voit que quatorze jours.** Les suppressions rapides sont visibles, les révisions à six
mois ne le sont pas.

**On ne connaît pas le sens de la causalité pour la réponse du commerçant.** Celui qui répond en
deux jours est aussi celui qui surveille sa fiche et signale les avis qu'il juge illégitimes. Le
modèle tient compte du secteur, du pays, de la taille de la fiche, de la note et du profil de
l'auteur — pas de l'attention portée à la fiche.

**« Aucune réponse n'est arrivée après la suppression » ne prouve rien.** Une réponse arrivée
après une suppression ne peut pas être observée, l'avis n'étant plus là. C'est un effet de la
collecte.

**Une réponse retirée est invisible.** Un avis dont la réponse a été effacée est compté « sans
réponse ».

**Le panel ne couvre pas tout** : 41 pays dont un seul hors d'Europe. Le Royaume-Uni en est
absent, ainsi que les groupes de 2-3 et de 11-19 établissements.

**Les probabilités produites par le modèle européen ne sont pas utilisables.** Il classe
correctement, mais le niveau de risque qu'il annonce est faux — voir
`output-study/2026-09-14-interpretation-panel.md` § 5.

---

## 6. Ce que vaut le modèle

Présenté avec un avis supprimé et un avis resté en ligne tirés au hasard, le modèle donne le
score le plus élevé au bon dans **86 % des cas**, sur des établissements qu'il n'a jamais vus.

**Une réserve importante : ce 86 % vient surtout de l'âge**, qui est une variable de contrôle et
pas un résultat. Sans l'âge, il tombe à 72 %. C'est ce second chiffre qui mesure ce que les
caractéristiques de l'avis apportent réellement.
