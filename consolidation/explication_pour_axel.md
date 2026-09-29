# Suppressions d'avis : sur quels avis on mesure, et comment se lit une régression

Pour Axel. Chiffres du 2026-09-29. Commande qui les régénère :
`uv run python consolidation/axel_comparaison_perimetres.py`, sortie
`consolidation/sorties/axel_comparaison_perimetres.csv`.

---

## En bref

- **Décrire les avis supprimés** (leur note, leur secteur, leur auteur) se fait sur toutes les
  suppressions. C'est déjà le cas : les 4 035 avis disparus pendant le suivi, quelle que soit leur
  date de publication, sont décrits aux points 1, 2.1 et 2.2 de l'étude.
- **Mesurer ce qui fait supprimer un avis** oblige à comparer des avis supprimés à des avis restés
  en ligne, publiés à la même période. On le fait sur les 35 751 avis publiés du 4 au 17 août,
  dont 1 355 ont disparu.
- Une table qui réunirait « les avis publiés de J-7 à J+7 » et « toutes les suppressions »
  donnerait des taux faux. Sur nos propres données, elle efface par exemple l'effet des comptes
  sans niveau Local Guide.

---

## 1. Deux questions, deux tables

**Première question : à quoi ressemble un avis supprimé ?** On regarde les avis supprimés, et eux
seuls. Toutes les suppressions comptent, y compris celles d'avis publiés il y a des années.
C'est ce que font les points 1c, 2.1 et 2.2 de l'étude, sur les 4 035 suppressions de la base.

**Seconde question : qu'est-ce qui fait qu'un avis est supprimé ?** Il faut un taux : sur
10 000 avis 1 étoile, combien disparaissent ? Et sur 10 000 avis 5 étoiles ? Un taux demande de
connaître aussi les avis **restés en ligne**. On prend donc tous les avis publiés du 4 au 17 août
(J-7 à J+6), supprimés ou non : 35 751 avis, dont 1 355 supprimés.

---

## 2. Pourquoi la table « J-7 à J+7 + toutes les suppressions » ne mesure pas les causes

Cette table contiendrait :
- 38 319 avis publiés du 4 au 18 août, supprimés ou non ;
- plus 2 617 avis publiés en dehors de cette période, **tous supprimés** : 2 536 publiés avant
  le 4 août, 81 publiés après le 18 août.

Un avis de 2019 n'y entre que s'il a disparu. Les centaines de milliers d'avis de 2019 restés en
ligne n'y sont pas. Les 2 536 avis anciens gonflent donc le nombre de suppressions sans qu'aucun
avis ancien conservé ne les équilibre.

**Le même calcul sur les deux tables** (suppressions pour 10 000 avis) :

| | Notre panel (4 au 17 août) | Table « J-7 à J+7 + toutes les suppressions » |
|---|---:|---:|
| **Tous les avis** | **379** | **986** |
| 5 étoiles | 385 | 887 |
| 4 étoiles | 156 | 476 |
| 3 étoiles | 101 | 704 |
| 2 étoiles | 364 | 1 078 |
| 1 étoile | 732 | 2 546 |
| Auteur sans niveau Local Guide | 711 | 1 142 |
| Auteur de niveau 1 à 4 | 416 | 1 098 |
| Auteur de niveau 5 et plus | 139 | 568 |
| Auteur sans photo publiée | 464 | 1 149 |
| Auteur à plus de 20 photos | 80 | 392 |

**Ce que la seconde table fait dire à tort :**
- **Un avis sur dix serait supprimé** (986 pour 10 000). Sur l'ensemble de la base, il en
  disparaît 8,5 pour 10 000 pendant les 14 jours de suivi.
- **Le compte sans niveau Local Guide ne se distinguerait plus.** Dans notre panel, il perd
  1,7 fois plus d'avis qu'un auteur de niveau 1 à 4 (711 contre 416). Dans l'autre table, 1 142
  contre 1 098 : presque autant. Les auteurs des avis anciens ont eu des années pour obtenir un
  niveau, et leurs avis supprimés noient le signal des comptes neufs.
- **L'ordre des notes change.** Dans notre panel, l'avis 3 étoiles est le moins supprimé
  (101 pour 10 000). Dans l'autre table, il passe à 704, au-dessus du 4 étoiles (476).
- **L'écart lié aux photos de l'auteur est divisé par deux.** Dans notre panel, un auteur sans
  photo perd 5,8 fois plus d'avis qu'un auteur à plus de 20 photos. Dans l'autre table, 2,9 fois.

Ajouter l'âge de l'avis au calcul ne répare rien : pour un avis de 2019, la table ne contient que
des supprimés, et aucun conservé du même âge auquel le comparer.

---

## 3. La régression, expliquée simplement

### Le problème qu'elle règle

Deux caractéristiques vont souvent ensemble. Un exemple tiré de nos données : aux États-Unis,
529 avis 5 étoiles sur 10 000 disparaissent. Sans les 4 chaînes de traitement antiparasitaire,
ce taux tombe à 320. Ces chaînes reçoivent beaucoup d'avis 5 étoiles et en perdent beaucoup. Le
taux « 5 étoiles » compte donc en partie « être chez une de ces chaînes ».

Un simple taux mélange les deux. La régression les sépare.

### Ce qu'elle fait

Elle compare des avis qui ne diffèrent que par une seule caractéristique, toutes les autres
étant égales : même secteur, même région, même âge, même profil d'auteur. Pour chaque
caractéristique, elle donne un chiffre de la forme « ×2 » :
- **×2** : l'avis disparaît deux fois plus souvent qu'un avis identique par ailleurs ;
- **×0,5** : deux fois moins souvent ;
- **×1** : aucune différence.

Exemple de l'étude. En comparant les avis d'une même fiche le même jour, un avis 1 étoile
disparaît 5 fois plus souvent qu'un avis 5 étoiles (×5,13, sans les enseignes signalées). La
fiche, son secteur et son pays sont les mêmes pour les deux avis : l'écart vient de la note.

Comme la question est « supprimé ou non », on utilise la variante de la régression faite pour
les réponses oui / non, dite logistique. Elle se lit de la même façon.

### La fourchette

Chaque chiffre vient avec une fourchette, par exemple ×0,36 [0,20 à 0,63]. Ce sont les valeurs
compatibles avec les données. Quand la fourchette contient 1, par exemple [0,75 à 6,84], les
données ne permettent pas de dire si l'effet existe.

### La règle qu'on s'est fixée avant de citer un chiffre

Un effet se cite s'il repose sur au moins 20 suppressions, réparties sur au moins 10 fiches,
sans qu'une seule fiche en porte plus du quart.

Pourquoi : sur les fiches qui répondent peu à leurs avis, répondre le jour même semblait
multiplier le risque par 2,3. Sur les 24 suppressions derrière ce chiffre, 18 venaient d'une
seule fiche, Cedar Park Overhead Doors. Le chiffre décrivait cette fiche.

### Ce qu'elle ne dit pas

Une régression montre ce qui va avec la suppression. Elle ne prouve pas la cause. Exemple : sur
les fiches qui répondent à presque tous leurs avis, un avis déjà répondu disparaît environ trois
fois moins (×0,36). Deux lectures restent possibles :
- la réponse protège l'avis ;
- le propriétaire s'abstient de répondre aux avis qu'il signale à Google.

Les données ne montrent pas les signalements et ne permettent pas de trancher.

---

## Sources

| Chiffre | Fichier |
|---|---|
| Comparaison des deux tables | `consolidation/sorties/axel_comparaison_perimetres.csv` |
| 4 035 suppressions, 8,5 pour 10 000 | `consolidation/sorties/1a_tables.csv`, `1c_suppressions_secteur_region.csv` |
| 5 étoiles aux États-Unis : 529 et 320 | `consolidation/sorties/2_3_note.csv` |
| 1 étoile ×5,13 dans la même fiche | `consolidation/sorties/4b_effets.csv` |
| Réponse ×0,36, Cedar Park | `consolidation/sorties/5_effets.csv`, `5_fiches_par_case.csv` |
