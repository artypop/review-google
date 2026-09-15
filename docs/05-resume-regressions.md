# Les régressions logistiques : ce qui a été mis dans le modèle, ce qui a été lancé, ce qui en sort

Dernière mise à jour : 2026-09-15.

Document d'accueil pour qui rejoint l'étude et veut savoir ce qui a été calculé. Il ne crée
aucun chiffre : chaque valeur vient de [03-resultats.md](03-resultats.md) et des notes de
`logistic-regression-study/output-study/`, citées à côté. En cas d'écart, ce sont les CSV de
`output-study/` qui font foi.

---

## 1. Les caractéristiques mises dans le modèle

Modèle principal : `logistic-regression-study/python/07_regression_panel.py`, sur 225 757 avis
publiés du 13 mai au 16 août 2026, 8 205 fiches, une ligne par avis, 2 595 suppressions
(1,15 %).

**L'avis**
- la note, de 1 à 5 étoiles, la référence étant 5 étoiles ;
- la longueur du texte en quatre tranches : sans texte, 1 à 50, 51 à 200, plus de 200
  caractères ;
- la présence d'une photo ;
- une réponse du commerçant arrivée avant le début du suivi.

**L'auteur**
- le nombre total d'avis qu'il a déposés, en logarithme ;
- son profil Local Guide en trois cas : guide établi comme référence, compte sans niveau,
  niveau affiché sans avis déclaré ;
- le nombre d'avis qu'il a déposés le même jour, appelé « rafale ».

**La langue**
- un avis écrit dans une langue inhabituelle pour la fiche.

**L'établissement**
- le secteur, sept en tout ;
- la région, États-Unis ou Europe ;
- la taille du groupe : une fiche, de 4 à 10, de 20 à 50.

**L'afflux**
- le rapport entre les avis reçus par la fiche ce jour-là et son rythme habituel.

**Le contrôle**
- l'âge de l'avis à la première observation, en logarithme. Il sert à lire les autres
  caractéristiques à âge comparable. Son coefficient ne se cite pas.

### Trois caractéristiques écartées en cours de route

| Écartée | Motif |
|---|---|
| langue étrangère au pays | en Europe elle mesure le tourisme : 92,8 % des avis croates y sont « étrangers » |
| langue inconnue | recouvre « sans texte » à 97,7 % ; le modèle ne peut pas départager deux colonnes identiques |
| rythme de fiche inconnu | 12 avis concernés, dont 5 américains |

### Cinq colonnes interdites en entrée

Elles ne sont connues qu'une fois l'histoire finie, et les mettre dans le modèle reviendrait à
prédire la suppression avec la suppression : âge à la suppression, délai de réponse, réponse
relevée au dernier passage du robot, réponse arrivée pendant la période de risque, et la cible
elle-même.

---

## 2. Ce qui a été lancé

### Le modèle sur le panel, cinq passages

Sorties dans `output-study/2026-09-14-sorties-07/`, sauf le sixième passage, lancé le
2026-09-15 et rangé dans `output-study/2026-09-15-sorties-07/`.

| Passage | Avis | Suppressions | Taux |
|---|---:|---:|---:|
| tous | 225 757 | 2 595 | 1,15 % |
| tous, sans les six enseignes | 210 670 | 1 576 | 0,75 % |
| États-Unis | 127 813 | 1 851 | 1,45 % |
| Europe | 97 944 | 744 | 0,76 % |
| Europe, sans les six enseignes | 97 497 | 417 | 0,43 % |
| États-Unis, sans les six enseignes | 113 173 | 1 159 | 1,02 % |

Les six enseignes signalées sont quatre chaînes américaines de traitement antiparasitaire et
deux salles de sport espagnoles. Elles portent 1 019 des 2 595 suppressions du panel, soit
39,3 %. C'est pourquoi chaque effet est lu deux fois.

Pour régénérer, depuis `logistic-regression-study/` :

```bash
python python/07_regression_panel.py
python python/07_regression_panel.py --sans-enseignes-signalees
python python/07_regression_panel.py --region US
python python/07_regression_panel.py --region Europe
python python/07_regression_panel.py --region Europe --sans-enseignes-signalees
python python/07_regression_panel.py --region US --sans-enseignes-signalees
```

### L'effet de répondre vite, huit passages

Sorties dans `output-study/2026-09-14-sorties-08/`, produites par
`python/08_effet_reponse_commercant.py`.

Population : les 15 248 avis publiés du 11 au 16 août, les seuls dont on a vu les premiers
jours de vie. 55 ont disparu avant le jalon, il en reste 15 193.

Le montage évite le piège qui a faussé les mesures précédentes. On fixe un jalon, on relève à
ce moment-là qui porte déjà une réponse, puis on compte qui disparaît jusqu'au huitième jour.
Une réponse arrivée après la suppression ne peut donc pas être comptée, et tous les avis ont le
même âge au jalon.

Quatre jalons — fin du premier, du deuxième, du troisième et du quatrième jour — chacun sur le
corpus complet et sans les quatre chaînes antiparasitaires, soit huit passages.

Les caractéristiques sont celles du modèle sur le panel, sans l'âge et sans l'afflux, plus
« une réponse est présente au jalon ».

Avant de lancer : `sql/controle_C_reponses_au_jalon.sql`, en lecture seule, qui vérifie qu'il y
a de quoi calculer.

```bash
python python/08_effet_reponse_commercant.py
python python/08_effet_reponse_commercant.py --sans-enseignes-signalees
python python/08_effet_reponse_commercant.py --jalon-jours 3 --fenetre-jours 5 --sans-enseignes-signalees
```

---

## 3. Les résultats

### Deux comportements opposés selon la région

Taux de suppression avant tout modèle, sur 10 000 avis de chaque groupe :

| Note | États-Unis | Europe |
|---|---:|---:|
| 1 étoile | 262 | 585 |
| 3 étoiles | 65 | 24 |
| 4 étoiles | 61 | 24 |
| 5 étoiles | **145** | 36 |

Aux États-Unis, l'avis 5 étoiles disparaît plus souvent que l'avis 3 ou 4 étoiles. En Europe,
les suppressions suivent les avis négatifs. Sur l'ensemble du panel, 1 850 des 2 595
suppressions portent sur un avis 5 étoiles, soit 71 %.

### Le phénomène américain ne vient pas des quatre chaînes

Passage lancé le 2026-09-15, `output-study/2026-09-15-sorties-07/07_croisements_US_sans_enseignes.csv`.
Taux de suppression sur 10 000 avis américains, une fois les six enseignes retirées :

| Note | États-Unis | États-Unis sans les enseignes |
|---|---:|---:|
| 1 étoile | 262 | 259 |
| 3 étoiles | 65 | 63 |
| 4 étoiles | 61 | 40 |
| **5 étoiles** | **145** | **97** |

L'avis 5 étoiles reste supprimé plus souvent que l'avis 3 ou 4 étoiles. Il porte 933 des 1 159
suppressions américaines restantes, soit 80 %. Le constat qui fonde le livrable tient donc sans
les enseignes signalées.

### Quatre effets qui tiennent dans tous les passages

| Ce qu'on regarde | Risque relatif | Sans les six enseignes |
|---|---:|---:|
| Avis 1 étoile, contre un avis 5 étoiles | ×6,34 | ×3,56 |
| Secteur des services à domicile | ×5,73 | ×3,16 |
| Compte d'auteur sans niveau Local Guide | ×2,30 | ×2,51 |
| Établissement américain | ×1,99 | ×2,14 |

Le profil d'auteur est le seul qui se renforce quand on retire les six enseignes, ce qui montre
qu'il ne vient pas d'elles. Le ×6,34 du 1 étoile porte sur une minorité des suppressions ; il
se cite avec sa part de volume à côté.

### Trois effets qui changent de sens selon le découpage

Aucun ne se cite sans dire sur quel groupe il est lu.

| | Tous | Sans enseignes | États-Unis | Europe |
|---|---:|---:|---:|---:|
| Rafale d'auteur | ×9,54 | ×5,28 | ×49,30 | ×0,90 |
| Afflux d'avis sur la fiche ce jour-là | ×1,40 | ×0,87 | ×0,84 | ×2,17 |
| Texte de plus de 200 caractères | ×0,66 | ×1,38 | ×1,10 | ×0,51 |

La rafale repose sur très peu de cas. Le gros du signal tient à 100 avis déposés à quatre le
même jour, dont 44 supprimés, et ces 44 sont entièrement dans les enseignes signalées. Le
passage américain sans les enseignes le confirme : le ×49,30 y tombe à ×5,19 [1,87 – 14,41].

Le texte long est le seul effet du panel dont le signe s'inverse nettement des deux côtés. Il
demande un examen à part avant toute publication.

### Ce que le passage américain sans les enseignes déplace

`output-study/2026-09-15-sorties-07/07_coefficients_US_sans_enseignes.csv`, sur 113 173 avis et
1 159 suppressions.

| Ce qu'on regarde | États-Unis | Sans les enseignes |
|---|---:|---:|
| Rafale d'auteur | ×49,30 | ×5,19 [1,87 – 14,41] |
| Secteur des services à domicile | ×4,79 | ×3,42 [1,84 – 6,38] |
| Avis 1 étoile | ×2,41 | ×3,47 [2,30 – 5,22] |
| Compte d'auteur sans niveau Local Guide | ×1,83 | ×2,27 [1,68 – 3,07] |
| Texte de plus de 200 caractères | ×1,10 | ×1,37 [1,02 – 1,85] |
| Afflux d'avis sur la fiche ce jour-là | ×0,84 | ×0,72 [0,58 – 0,89] |

Le profil d'auteur et le 1 étoile se renforcent sans les enseignes. Le texte long passe au-dessus
de 1, comme sur le corpus entier. L'afflux, qui restait incertain aux États-Unis, devient
protecteur. Le modèle classe correctement dans 81 % des cas sur des établissements jamais vus.

### Répondre au commerçant : trois chiffres pour trois questions

| Chiffre | Ce qu'il répond |
|---|---|
| ×1,02 [0,75 – 1,38] | un avis qui porte déjà une réponse depuis longtemps est-il mieux protégé ? Non. |
| ×0,56 [0,37 – 0,85] | répondre dans les deux jours à un avis qui vient de tomber sert-il à quelque chose ? Oui, hors des quatre chaînes antiparasitaires. |
| ×0,79 [0,53 – 1,16] | le même calcul sur tout le monde : l'effet n'est plus mesurable. |

Les quatre chaînes pèsent 1 021 avis sur 15 193, soit 6,7 % de cette population, et portent 189
des 505 suppressions, soit 37,4 %. Elles tirent l'effet moyen vers 1. Annoncer le ×0,56 sans
dire qu'il les exclut serait faux.

Le résultat ne dépend pas du jalon choisi : ×0,59 à la fin du premier jour, ×0,56 au deuxième,
×0,46 au troisième, ×0,48 au quatrième, toujours hors les quatre chaînes.

Deux chiffres anciens ne sont plus citables : « ×0,30 » et « répondre protège 3,7 fois ». Ils
comptaient la réponse dans l'état où elle se trouvait au dernier passage du robot.

### Ce que vaut le modèle

Présenté avec un avis supprimé et un avis resté en ligne tirés au hasard, sur des
établissements qu'il n'a jamais vus, il donne le score le plus élevé au bon dans 86 % des cas.
Sans l'âge, ce chiffre tombe à 72 %. C'est le second qui mesure ce que les caractéristiques de
l'avis apportent réellement.

---

## 4. Les réserves à porter avec les chiffres

- **Les probabilités du modèle européen ne s'utilisent pas.** Le sous-ensemble tiré pour le
  test est tombé sur des fiches 2,3 fois moins touchées que le corpus dont il sort. Les
  coefficients européens restent lisibles en risque relatif. La correction proposée est une
  validation croisée par établissement, non faite à ce jour.
- **On ne voit que quatorze jours**, et seulement la modération après publication. Le filtrage
  avant mise en ligne est invisible : aucun avis contenant un lien n'a été supprimé pendant le
  suivi, alors qu'il en existe dans le panel.
- **Le sens de la causalité sur la réponse du commerçant n'est pas établi.** Celui qui répond
  en deux jours est aussi celui qui surveille sa fiche et signale les avis qu'il juge
  illégitimes. Le modèle tient compte du secteur, du pays, de la taille de la fiche, de la note
  et du profil de l'auteur, sans mesurer cette attention.
- **731 avis sont écartés du corpus** : 0,3 % des avis et environ 3 % des suppressions. Les
  avis déposés en rafale sont 52 % des écartés.
- **Un avis compté « non supprimé » peut l'être le lendemain du dernier relevé.**

---

## 5. Où lire la suite

| Pour | Lire |
|---|---|
| le projet entier en une lecture | [00-brief-equipe.md](00-brief-equipe.md) |
| la question, le corpus, les choix de modélisation | [01-etude.md](01-etude.md) |
| les définitions et pourquoi les chiffres divergent | [02-donnees.md](02-donnees.md) |
| tous les résultats et leurs limites | [03-resultats.md](03-resultats.md) |
| les erreurs déjà commises | [04-enseignements.md](04-enseignements.md) |
| le détail de chaque passage | `logistic-regression-study/output-study/2026-09-14-interpretation-panel.md` et `2026-09-14-effet-reponse-commercant.md` |
