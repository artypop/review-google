# Les données suffisent-elles pour mesurer ce qui fait supprimer un avis ?

Note du 2026-09-17, pour Axel. Tous les chiffres viennent des sorties du jour, dans
`logistic-regression-study/output-study/2026-09-17-sorties-07`, `-sorties-08` et `-sorties-10`.

---

## 1. Ce qu'il faut compter

Pour comparer les avis supprimés aux avis restés en ligne, ce sont **les avis supprimés** qui
fixent la précision. Les millions d'avis restés en ligne ne coûtent rien et n'apportent presque
rien une fois qu'on en a beaucoup plus que d'avis supprimés.

Un exemple simple. Pour savoir si les avis 1 étoile disparaissent plus souvent, on regarde la
composition des avis supprimés. Avec 10 avis supprimés, on ne distingue rien. Avec 1 000, on
mesure une différence de 30 %. Le nombre d'avis restés en ligne, 10 000 ou 200 000, ne change
presque rien à cette précision.

---

## 2. Ce qu'on a

| Population étudiée | Avis | Avis supprimés |
|---|---:|---:|
| Panel entier | 225 757 | 2 595 |
| États-Unis, sans les chaînes antiparasitaires | 113 173 | 1 159 |
| Europe, sans les salles de sport | 97 497 | 417 |
| Les 8 premiers jours de l'avis, États-Unis sans les chaînes | 8 800 | 293 |
| Les 8 premiers jours, Europe | 7 731 | 152 |
| Effet d'une réponse du propriétaire | 16 467 | 381 |

Le modèle principal compare une vingtaine de caractéristiques à la fois. Avec 1 159 avis
supprimés aux États-Unis, chaque caractéristique s'appuie sur plusieurs dizaines de cas.

---

## 3. Ce que ces nombres donnent, en clair

Chaque résultat sort avec une fourchette : la plus petite et la plus grande valeur compatibles
avec les données.

| Résultat | Valeur | Fourchette |
|---|---|---|
| Avis 1 étoile, États-Unis | supprimé 3,5 fois plus qu'un avis 5 étoiles | de 2,3 à 5,3 fois |
| Avis 1 étoile, Europe | 4,1 fois plus | de 2,5 à 6,8 fois |
| Auteur sans niveau Local Guide, États-Unis | 2,3 fois plus | de 1,7 à 3,1 fois |
| Auteur sans niveau Local Guide, Europe | 3,0 fois plus | de 2,0 à 4,5 fois |
| Auteur à 100 photos, États-Unis | 2,4 fois moins | de 1,7 à 3,5 fois moins |

Ces fourchettes ne contiennent pas « aucune différence ». L'écart existe, et son ampleur est
connue à peu près au double près. C'est assez pour dire ce qui pèse et dans quel ordre.

**Ce que ces chiffres ne disent pas.** « 3,5 fois plus » compare deux avis identiques par
ailleurs : 259 suppressions pour 10 000 avis 1 étoile, contre 97 pour 10 000 avis 5 étoiles. La
composition des avis supprimés est autre chose : aux États-Unis, hors chaînes, 80 % des avis
supprimés portent 5 étoiles et 14 % portent 1 étoile, parce que les avis 5 étoiles sont 85 % du
corpus.

---

## 4. Trois vérifications qui concordent

**1. Deux calculs indépendants donnent le même résultat.** Le modèle sur tout le panel et le
modèle limité aux avis publiés du 10 au 16 août ne partagent ni le même corpus ni la même
méthode :

| | Tout le panel | Les 8 premiers jours |
|---|---|---|
| Avis 1 étoile, États-Unis | ×3,5 | ×3,2 |
| Avis 1 étoile, Europe | ×4,1 | ×3,0 |
| Auteur sans niveau Local Guide, États-Unis | ×2,3 | ×2,2 |
| Auteur sans niveau Local Guide, Europe | ×3,0 | ×2,9 |

**2. Le modèle annonce le bon nombre de suppressions sur des établissements qu'il n'a jamais
vus.** Les fiches sont réparties en cinq groupes ; chaque groupe est noté par un modèle ajusté
sur les quatre autres.

| | Suppressions annoncées | Suppressions constatées |
|---|---:|---:|
| États-Unis sans les chaînes | 1 151 | 1 134 |
| Europe sans les salles | 409 | 409 |
| Les 8 premiers jours, États-Unis | 288 | 283 |

**3. L'effet d'une réponse tient à six moments de mesure différents.** Sur les fiches qui
répondent à plus de 75 % de leurs avis, l'avis déjà répondu est supprimé 2 à 3 fois moins, que
l'on regarde la réponse au 1er, 2e, 3e, 4e, 5e ou 6e jour : de ×0,32 à ×0,47.

---

## 5. Là où les nombres ne suffisent pas, on le dit

L'étude annonce aussi ce qu'elle ne peut pas mesurer :

- **Les avis 3 étoiles dans les 8 premiers jours** : 3 suppressions par région. Aucun chiffre
  n'est produit.
- **Plusieurs avis publiés le même jour par un même auteur, sur cette même période** : 55 avis
  aux États-Unis et 72 en Europe. Le sens est net, l'ampleur reste inconnue.
- **Les fiches qui répondent à moins de 25 % de leurs avis** : 149 avis répondus et 3
  suppressions. Rien n'en est tiré.
- **L'effet d'une réponse sur les fiches qui répondent de temps en temps** : 30 suppressions
  d'avis répondus, et une fourchette qui va de ×1,04 à ×4,0. On donne le sens et on écrit que
  l'ampleur est floue.

Le modèle de la réponse dit aussi quel écart il était capable de repérer, sur son passage sans
l'habitude de la fiche : une protection d'au moins 45 %, ou une aggravation d'au moins 82 %. En dessous, il n'aurait rien vu, et il est écrit
qu'il n'aurait rien vu.

---

## 6. Ce qu'on peut dire, et ce qu'on ne dira pas

**On peut dire** quelles caractéristiques augmentent ou diminuent le risque, de combien, et dans
quel ordre : la note, le profil de l'auteur, sa production de photos et d'avis, le fait de
publier plusieurs avis le même jour, le secteur, la région, la date de publication.

**On ne dira pas** la cause d'une suppression : traitement automatique, signalement du
propriétaire ou contestation d'un tiers. Les données ne contiennent rien là-dessus, et aucun
volume supplémentaire n'y changerait quelque chose.

**On ne dira pas non plus** qu'un avis précis va disparaître. Les 10 % d'avis jugés les plus
risqués contiennent 22 à 31 % des suppressions, contre 10 % pour un tirage au hasard. Le modèle
sert à comprendre ce qui pèse, sans deviner cas par cas.
