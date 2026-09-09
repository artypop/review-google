# Le cas des deux salles de sport espagnoles

Script : `etude-exploratoire/scripts/cas_attaque_salles_de_sport.py`. Date : 2026-09-08.

Une attaque par avis négatifs, nettoyée par Google. Les deux seules fiches du panel à dépasser
100 suppressions, toutes deux du secteur `wellness_fitness` en Espagne.

**Les deux fiches sont traitées séparément, et chaque part est rapportée au listing de sa propre
fiche.** Les versions précédentes de ce cas additionnaient les deux fiches puis rapportaient le
total à l'une d'elles, ce qui donnait des parts fausses. Correctifs au bas de cette note.


### Fiche A

| | |
|---|---:|
| Avis au listing | 781 |
| Note affichée par Google, au 11/08 | 3,81 sur 778 avis |
| Note affichée par Google, au 24/08 | **4,95** sur 552 avis |
| Avis publiés les 1er et 2 août | 219, soit **28,0 % de ses 781 avis** |
| Avis supprimés | 229, soit **29,3 % de ses 781 avis** |
| Note moyenne des supprimés | 1,04 |
| Note moyenne des restants | 4,95 |
| Part de 1 étoile parmi les supprimés | 98 % |
| Part de 5 étoiles parmi les restants | 98 % |
| Sans aucun texte, supprimés / restants | 67 % / 25 % |
| Auteur sans niveau Local Guide, parmi les supprimés | 25 % |
| Âge médian des supprimés | 9 jours |
| Âge médian des restants | 3,2 ans |
| Délai de suppression le plus fréquent | **14 à 15 jours** (183 avis) |

### Fiche B

| | |
|---|---:|
| Avis au listing | 668 |
| Note affichée par Google, au 11/08 | 4,67 sur 575 avis |
| Note affichée par Google, au 24/08 | **4,96** sur 533 avis |
| Avis publiés les 1er et 2 août | 111, soit **16,6 % de ses 668 avis** |
| Avis supprimés | 135, soit **20,2 % de ses 668 avis** |
| Note moyenne des supprimés | 1,07 |
| Note moyenne des restants | 4,96 |
| Part de 1 étoile parmi les supprimés | 93 % |
| Part de 5 étoiles parmi les restants | 98 % |
| Sans aucun texte, supprimés / restants | 71 % / 29 % |
| Auteur sans niveau Local Guide, parmi les supprimés | 21 % |
| Âge médian des supprimés | 9 jours |
| Âge médian des restants | 2,8 ans |
| Délai de suppression le plus fréquent | **10 à 11 jours** (70 avis) |

## Le paquet, jour par jour

| Fiche | Publié le | Avis publiés | Dont supprimés | Note moyenne | Auteurs distincts | Sans texte |
|---|---|---:|---:|---:|---:|---:|
| A | 28/07 | 1 | 1 | 1,00 | 1 | 100 % |
| A | 29/07 | 1 | 0 | 5,00 | 1 | 100 % |
| A | 31/07 | 1 | 1 | 1,00 | 1 | 0 % |
| B | 01/08 | 54 | 54 | 1,02 | 54 | 61 % |
| A | 01/08 | 107 | 107 | 1,00 | 107 | 72 % |
| B | 02/08 | 57 | 55 | 1,02 | 57 | 79 % |
| A | 02/08 | 112 | 112 | 1,01 | 111 | 63 % |
| B | 03/08 | 5 | 5 | 1,00 | 5 | 60 % |
| A | 03/08 | 3 | 3 | 1,00 | 3 | 100 % |
| B | 04/08 | 16 | 15 | 1,25 | 15 | 81 % |
| A | 04/08 | 2 | 2 | 1,50 | 2 | 50 % |
| B | 05/08 | 6 | 6 | 1,50 | 6 | 33 % |
| A | 05/08 | 1 | 1 | 1,00 | 1 | 100 % |

Un auteur distinct par avis, ou presque. Le signal n'est pas dans le texte — la majorité de ces
avis n'en ont aucun — il est dans le rythme et dans l'écart à la note habituelle de la fiche.

## Délai entre publication et suppression

| Fiche | Jours | Avis |
|---|---:|---:|
| B | 9 | 9 |
| B | 10 | 37 |
| B | 11 | 33 |
| B | 13 | 1 |
| B | 14 | 2 |
| B | 15 | 2 |
| B | 16 | 4 |
| B | 17 | 3 |
| B | 18 | 7 |
| B | 19 | 4 |
| B | 20 | 10 |
| B | 21 | 12 |
| B | 22 | 11 |
| A | 10 | 2 |
| A | 11 | 2 |
| A | 13 | 1 |
| A | 14 | 94 |
| A | 15 | 89 |
| A | 16 | 1 |
| A | 17 | 1 |
| A | 18 | 1 |
| A | 19 | 1 |
| A | 20 | 2 |
| A | 21 | 20 |
| A | 22 | 13 |

Les deux fiches n'ont pas été nettoyées à la même vitesse, alors que l'attaque est simultanée.

## Ce que ça veut dire

Ce n'est pas un faux positif. Une entreprise s'est fait attaquer, Google a nettoyé. Deux
conséquences pour le livrable :

1. Le dire, sinon l'étude paraît à charge. Google fait son travail quand le signal est massif.
2. Ces 364 avis faussent tout résultat où ils entrent. Ils expliquent à eux
   seuls pourquoi « 1 étoile » et « secteur sport et bien-être » sortaient si forts avant le
   contrôle de robustesse.

## Correctifs par rapport aux notes du 2026-09-06

| Chiffre publié le 2026-09-06 | Ce qui est vrai | Cause de l'erreur |
|---|---|---|
| 399 avis supprimés | 364 : 229 sur A + 135 sur B | Comptage d'avant la correction des résurrections et des bugs d'édition |
| 264 avis sur 816 | 229 sur 781 pour la fiche A | Idem |
| « 361 avis en deux jours » | 330 : 219 sur A, 111 sur B | Deux fiches, deux paquets, jamais un seul |
| « 24 % de son listing » | 28,0 % sur A, 16,6 % sur B | Paquet d'une fiche divisé par le total des deux |
| « sur une fiche notée 4,95 » | Google affichait 3,81 sur A et 4,67 sur B au 11/08, remontées à 4,95 et 4,96 au 24/08 | 4,95 était la note moyenne des avis restés en ligne, jamais celle affichée par la fiche |
| « effacés 10 à 14 jours plus tard » | voir le tableau des délais : deux vitesses distinctes | Les deux fiches étaient confondues |

Le compte des contrôles textuels (« 1 seul avis contenait une insulte ») vient de
`scripts/verif_texte.py`, sur le périmètre d'avant la correction. Non recalculé ici.
