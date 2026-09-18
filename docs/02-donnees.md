# Les données : d'où elles viennent, ce qu'elles disent, ce qu'elles cachent

Dernière mise à jour : 2026-09-14.

---

## 1. Pourquoi le même chiffre a parfois deux valeurs

C'est la première chose à comprendre avant de lire un résultat de ce projet, et c'est ce qui
a rendu le dossier illisible pendant une semaine.

**La plupart des désaccords entre deux chiffres viennent de deux questions différentes qui
portent le même nom.** Les calculs sont justes des deux côtés. Trois exemples réels, pris dans
ce projet.

### « Combien d'avis ont plusieurs enregistrements ? » — 617 ou 602

Le robot passe une fois par jour et note tous les avis qu'il voit. Normalement, un avis donne
une ligne dans le fichier. Mais certains avis disparaissent puis reviennent : ils donnent alors
deux lignes, parfois trois.

Le fichier contient 4 878 151 lignes pour 4 877 534 avis différents.

- **617**, c'est le nombre de **lignes en trop** : 4 878 151 moins 4 877 534.
- **602**, c'est le nombre d'**avis concernés**. Certains ont trois lignes, d'où
  l'écart entre les deux comptes.

Les deux sont justes. L'un compte des lignes, l'autre compte des avis. Écrire « 617 avis » est
faux, et c'était écrit dans le fichier d'instructions du projet jusqu'au 2026-09-14.

Détail utile : ces 602 avis se répartissent en 578 qui ont disparu puis sont revenus, et 24 qui
sont des bugs d'enregistrement (voir § 3).

### « Combien de suppressions sur les deux salles de sport espagnoles ? » — 327 ou 364

Deux salles de sport en Espagne ont perdu beaucoup d'avis d'un coup, tous à une étoile.

- **364**, c'est tout ce qu'elles ont perdu pendant les quatorze jours de suivi, quelle que soit
  la date de publication de l'avis.
- **327**, c'est ce qu'elles ont perdu **parmi les avis qui entrent dans l'étude de régression**,
  laquelle ne retient que les avis publiés dans les 90 jours avant le 11 août.

Un avis supprimé le 18 août mais publié il y a deux ans entre dans le premier compte. Il est
absent du second. Les deux sont justes ; il faut dire lequel on cite.

### « Une rafale d'auteur, ça multiplie le risque par combien ? » — ×3,9, ×5,09, ×9,54, ×49,30

Une rafale, c'est le même auteur qui publie plusieurs avis le même jour.

Quatre chiffres circulent parce que quatre calculs différents ont été faits : sur tout le
corpus, sur les seuls avis récents, sur le panel de la régression, sur les seuls établissements
américains. Chacun a sa réponse. **Aucun n'est le bon dans l'absolu.**

### La règle qui en découle

**Un chiffre ne se cite jamais seul.** Il vient avec ce qu'il compte (des lignes ? des avis ?
des établissements ?) et sur quelle population. C'est la seule protection contre ce genre de
confusion, et elle a coûté assez cher pour qu'on la tienne.

---

## 2. D'où viennent les données

**9 048 entreprises suivies, un relevé par jour du 11 au 24 août 2026, 4,88 millions d'avis.**

À chaque passage, le robot recense la totalité des avis de chaque fiche Google. Quatorze
passages, donc treize intervalles pendant lesquels un avis peut disparaître.

**Un avis qui n'apparaît plus à un passage est considéré comme supprimé.** C'est une déduction
de notre part, à partir de ce que le robot voit. Google ne signale jamais rien. Toute la section
suivante existe parce que cette déduction est parfois fausse.

Les fichiers d'origine sont dans `data/exports/exports/`. Ils ne sont pas dans le dépôt : ils
pèsent 838 Mo et contiennent des données personnelles — nom de l'auteur, lien vers son profil,
texte de l'avis. Le fichier de licence de l'export interdit leur rediffusion.

Le panel ne couvre pas tout : 41 pays dont un seul hors d'Europe, le Royaume-Uni n'y est pas, et
les groupes de 2 à 3 sites et de 11 à 19 sites sont absents.

---

## 3. Ce qu'on appelle une suppression

Le fichier contient une colonne qui dit à quelle date le robot n'a plus retrouvé un avis. Cette
colonne ne veut **pas** dire « Google a supprimé cet avis ». Elle veut dire « le robot ne l'a pas
vu ce jour-là ». Deux situations rendent la déduction fausse, et sont retirées avant tout
comptage.

**Le bug d'enregistrement — 24 avis.** Même auteur, même note, même date de publication, mais un
texte entièrement différent d'une ligne à l'autre. C'est l'auteur qui a réécrit son avis et le
robot qui l'a mal enregistré. Ces 24 avis sont écartés quelle que soit la durée de leur
absence.

**Le raté de collecte.** L'avis est absent un seul jour, puis revient identique. Sur les avis qui
disparaissent puis reviennent, 71 % sont absents une seule journée. Un vrai retrait contesté puis
annulé par Google prend plusieurs jours.

**La règle retenue : une absence de deux jours ou plus est une vraie suppression.** Elle est
datée du jour de la première disparition. Une absence d'un seul jour est un raté du robot.

Le décompte qui en sort : **5 230 disparitions constatées, portées par 5 109 avis différents,
dont 4 747 sont retenues comme de vraies suppressions.**

Encore une fois deux unités : le 5 230 compte des **événements** — un même avis peut disparaître
deux fois —, le 5 109 et le 4 747 comptent des **avis**. Ne jamais les mettre de part et d'autre
d'une flèche sans dire lequel est lequel.

### Deux définitions cohabitent, et c'est voulu

| | Sur tout le corpus | Sur le panel de la régression |
|---|---|---|
| Combien d'avis | 4,88 millions | 225 757 |
| La règle | absence de 2 jours ou plus, bugs d'édition retirés | les avis à plusieurs enregistrements sont **exclus du corpus**, puis toute disparition compte |
| Combien de suppressions | 4 747 | 2 595 |
| Où c'est écrit | `etude-exploratoire/scripts/suppressions_corrigees.py` | `sql/01_selection_panel.bqsql` et `sql/02_adding_features.bqsql` |

Les deux règles se complètent. Sur le panel, la question du retour ne se pose plus : les 731
avis qui ont plusieurs enregistrements ont été sortis du corpus dès le départ, donc il ne reste
aucun avis revenu à trier.

**Cette exclusion n'est pas neutre et elle est assumée.** Elle retire 0,3 % des avis mais environ
3 % des suppressions. Conséquences directes : l'effet « avis modifié » n'est pas mesurable sur ce
panel, et les avis publiés en rafale sont la moitié des avis écartés, ce qui fait sous-estimer
l'effet des rafales.

### Un écart de 10 jamais expliqué

Le même calcul donne **4 747** suppressions avec l'outil local et **4 737** avec BigQuery, à
partir des mêmes 5 230 disparitions et des mêmes 5 109 avis.

L'écart vient de la façon de mesurer une durée d'absence. L'un compte les passages de minuit,
l'autre compte les heures réellement écoulées. Six avis absents entre 45 et 46 heures valent
« deux jours » pour l'un et « un jour » pour l'autre, et basculent donc de côté.

**Six avis sur dix sont expliqués. Les quatre autres ne le sont pas.** Citer le total avec l'outil
qui l'a produit.

---

## 4. Ce qu'on appelle une fiche attaquée

Certaines fiches ne perdent pas des avis un par un : elles en perdent des dizaines d'un coup,
tous négatifs, tous récents. Ce sont des attaques, et il faut pouvoir refaire les calculs sans
elles pour vérifier qu'elles ne portent pas les résultats à elles seules.

**Une fiche est dite attaquée quand les quatre conditions sont réunies :**

1. au moins 10 suppressions ;
2. au moins 80 % de ces suppressions sur des avis à une étoile ;
3. au moins 80 % sur des avis publiés moins de 30 jours avant leur suppression ;
4. *(décidée le 2026-09-10, encore absente du code)* au moins 10 avis supprimés publiés
   le même jour.

### Pourquoi le critère précédent a été abandonné

Jusqu'au 2026-09-09, une fiche était dite attaquée quand elle perdait plus de 5 % de ses avis.
Les 24 fiches que ce critère retenait ont été examinées une par une :

- **2** étaient réellement attaquées ;
- **1** est un autocariste allemand qui perd 48 avis négatifs écrits sur huit ans, le plus récent
  datant de trois ans. C'est un retrait obtenu sur demande ;
- **15** ne perdent que des avis 4 et 5 étoiles, surtout des artisans américains. **C'est le
  phénomène même que l'étude documente** : les écarter reviendrait à retirer le sujet du corpus ;
- **6** ont moins de 25 avis, dont une à 2 avis qui atteignait le seuil avec une seule
  suppression.

Le critère en pourcentage rate aussi les petites attaques sur les grosses fiches : 10
suppressions sur 9 545 avis font 0,10 % du stock, et passent inaperçues.

### Une réserve sur le code actuel

Le repérage des salles de sport attaquées se fait sur le **nom** de l'enseigne. L'identifiant de
la fiche n'entre pas dans le calcul. Résultat : 13 fiches sont marquées alors que 2 sont attaquées. Les 11
autres portent le même nom d'enseigne, totalisent 90 avis et **aucune suppression**. Les retirer
d'un calcul ne change donc aucun résultat, mais le compte de fiches est faux si on le cite tel
quel.

**Décision de Romain du 2026-09-14 : le repérage se fait sur le `cid`.** Les deux fiches
attaquées sont `3163466139043001754`, qui porte 206 avis du panel et 192 suppressions dont
99,5 % à une étoile, et `10346942689164695031`, qui porte 151 avis et 135 suppressions dont
93,3 % à une étoile. Leurs 327 suppressions redonnent le chiffre du § 1. Les 11 fiches en trop
que retenait le nom portent 296 avis du panel et aucune suppression.

Le flag `salle_de_sport_attaquee` de `sql/02_adding_features.bqsql` marque toujours sur le nom :
le corriger oblige à reconstruire la table et à relancer tous les modèles, ce qui est une
décision à part. Toute nouvelle requête exclut sur ces deux `cid`. Première application :
`etudes-ponctuelles/2026-09-15-part-supprimee-par-note/`.

Le repérage par nom des quatre chaînes américaines reste en place, pour la raison donnée
ci-dessous.

Le même repérage pour les quatre chaînes américaines de traitement antiparasitaire est correct :
là, on veut bien toutes les succursales (26, 19, 19 et 24 fiches).

---

## 5. Les pièges du jeu de données

Chacun a produit une erreur réelle dans ce projet.

**L'identifiant d'un avis n'est pas unique.** Voir le § 1. Toute table qui compte des avis doit
regrouper explicitement, en gardant la première observation.

**L'âge de l'avis écrase tout le reste.** Le risque de suppression est divisé par 21 entre un
avis du jour et un avis de trois mois. Une comparaison qui ne tient pas compte de l'âge mesure
surtout une différence d'âge. C'est ce qui faisait croire que répondre à un avis le protégeait.

**Le temps écoulé avant la suppression ne peut pas servir à prédire la suppression.** On ne le
connaît que pour les avis déjà supprimés. S'en servir reviendrait à deviner un événement avec
une information qu'on n'obtient qu'après qu'il s'est produit.

**Les caractéristiques d'un avis sont son état au dernier passage où on l'a vu.** L'export ne
garde l'historique que de la note et du texte.

**Une réponse de commerçant retirée est invisible.** Le champ qui liste ce qui a changé ne
mentionne jamais les réponses. Un avis dont la réponse a été effacée est donc compté « sans
réponse », sans qu'on puisse le savoir.

**Le filtrage avant publication est invisible.** Aucun avis contenant un lien n'a été supprimé
pendant le suivi, alors qu'il en existe dans le panel : ces avis-là sont filtrés avant même
d'être mis en ligne. On ne voit donc qu'une partie de la modération de Google.

**Le renouvellement des adresses de photos n'est pas un signal.** Elles changent sans que l'avis
bouge.

**L'histogramme des notes se met à jour avant le listing.** En cas de désaccord entre les deux,
le listing fait foi.

---

## 6. Les deux façons de mesurer la langue

Une seule variable de langue ne suffit pas, et les confondre a produit un résultat faux.

| Ce qu'on veut mesurer | Nom de la variable |
|---|---|
| L'avis est dans une langue qui n'est pas parlée officiellement dans le pays du commerce | `langue_etrangere_au_pays` |
| L'avis est dans une langue inhabituelle **pour ce commerce précis** | `langue_minoritaire_sur_la_fiche` |

**Pourquoi les deux ne se confondent pas.** En Espagne, 40 des 550 fiches du panel ont l'anglais
comme langue principale de leurs avis ; la plus grosse en compte 1 335 en anglais. Même situation
en Grèce (21 fiches sur 116) et au Portugal (16 sur 94). Sur ces fiches, un avis en anglais est
étranger au pays mais parfaitement habituel pour le commerce.

**Ce qui a été mesuré le 2026-09-14 :** `langue_etrangere_au_pays` mesure en réalité le tourisme.
92,8 % des avis croates y sont comptés étrangers, dont 44,7 % en allemand contre 7,2 % en croate.
67 % en Norvège, 70 % au Portugal, 62 % en Grèce. Aux États-Unis, 2 %. **Cette variable ne doit
pas être citée** ; `langue_minoritaire_sur_la_fiche` la remplace dans le modèle, et ne souffre
pas de ce défaut.

Construire `langue_etrangere_au_pays` correctement demande une table associant chaque pays à
**toutes** ses langues officielles — la Belgique en a trois, la Suisse quatre. Avec une règle
« Belgique → français », un avis en néerlandais à Anvers serait compté étranger, ce qui n'est pas
la question posée.

---

## 7. Où sont écrites ces règles dans le code

| Règle | Fichier |
|---|---|
| Le corpus de la régression | `sql/01_selection_panel.bqsql` |
| Les 42 caractéristiques, dont la cible | `sql/02_adding_features.bqsql` |
| La définition d'une suppression sur tout le corpus | `etude-exploratoire/scripts/suppressions_corrigees.py` — **dossier gelé, voir son README** |

`sql/02_adding_features.bqsql` ne se modifie pas sans accord préalable de l'équipe, même quand
les modifications sont acceptées automatiquement : le changer oblige à reconstruire la table et à
relancer tous les modèles.
