---
date: 2026-09-15
projet: reviewflowz-analyse-google
titre: "Le passage américain sans les six enseignes signalées"
statut: résultats
---

# Le passage américain sans les six enseignes signalées

Sixième passage de `python/07_regression_panel.py`, lancé le 2026-09-15, sorties dans
`2026-09-15-sorties-07/`. Il manquait : quatre des six enseignes signalées sont américaines,
donc c'est sur ce découpage que leur retrait pèse le plus, et la convention du projet demande
chaque résultat en double.

```bash
python python/07_regression_panel.py --region US --sans-enseignes-signalees
```

## Le corpus

| Passage | Avis | Suppressions | Taux |
|---|---:|---:|---:|
| US | 127 813 | 1 851 | 1,45 % |
| US sans les enseignes | 113 173 | 1 159 | 1,02 % |

Le retrait enlève 14 640 avis et 692 suppressions, soit 37,4 % des suppressions américaines
pour 11,5 % des avis.

Tous les risques relatifs qui suivent sont à âge comparable. Le coefficient de
`log_age_vague1` n'est pas un résultat et n'est pas cité.

---

## 1. Le constat qui fonde le livrable tient

Taux de suppression avant tout modèle, sur 10 000 avis de chaque groupe
(`07_croisements_US_sans_enseignes.csv`) :

| Note | US | US sans les enseignes |
|---|---:|---:|
| 1 étoile | 262,0 | 259,4 |
| 2 étoiles | 96,5 | 94,9 |
| 3 étoiles | 65,3 | 63,1 |
| 4 étoiles | 60,5 | 40,1 |
| **5 étoiles** | **145,1** | **97,0** |

L'avis 5 étoiles reste supprimé plus souvent que l'avis 3 ou 4 étoiles. En volume, 933 des
1 159 suppressions restantes frappent un avis 5 étoiles, soit **80,5 %**, contre 85,9 % sur le
passage américain entier.

Le niveau baisse d'un tiers, la forme de la colonne ne bouge pas. Les quatre chaînes
antiparasitaires amplifiaient le phénomène sans le créer.

---

## 2. Les coefficients, au complet

`07_coefficients_US_sans_enseignes.csv`. Référence des notes : 5 étoiles. Référence des
profils : guide établi. Référence des tranches de texte : sans texte. Référence des tailles :
une fiche unique.

| Variable | Risque relatif | Fourchette | p |
|---|---:|---|---:|
| etoiles_1 | ×3,47 | [2,30 – 5,22] | 0,000 |
| etoiles_2 | ×1,53 | [0,84 – 2,78] | 0,163 |
| etoiles_3 | ×1,10 | [0,61 – 1,97] | 0,760 |
| etoiles_4 | ×0,62 | [0,39 – 0,96] | 0,033 |
| profil_aucun_niveau | ×2,27 | [1,68 – 3,07] | 0,000 |
| profil_niveau_sans_avis_declare | ×1,28 | [0,89 – 1,85] | 0,189 |
| texte_1_50 | ×1,31 | [0,93 – 1,85] | 0,126 |
| texte_51_200 | ×1,22 | [0,88 – 1,70] | 0,231 |
| texte_201p | ×1,37 | [1,02 – 1,85] | 0,037 |
| secteur_home_services | ×3,42 | [1,84 – 6,38] | 0,000 |
| secteur_wellness_fitness | ×2,01 | [0,93 – 4,35] | 0,074 |
| secteur_travel | ×2,08 | [0,68 – 6,41] | 0,200 |
| secteur_healthcare | ×1,63 | [0,87 – 3,07] | 0,129 |
| secteur_hospitality | ×0,73 | [0,32 – 1,65] | 0,446 |
| secteur_food_beverage | ×0,55 | [0,19 – 1,60] | 0,274 |
| taille_small | ×1,54 | [0,83 – 2,87] | 0,172 |
| taille_large | ×0,78 | [0,41 – 1,46] | 0,430 |
| log_burst | ×5,19 | [1,87 – 14,41] | 0,002 |
| log_ratio_pic_journalier_fiche | ×0,72 | [0,58 – 0,89] | 0,002 |
| log_rc | ×0,92 | [0,83 – 1,01] | 0,073 |
| has_photo | ×0,84 | [0,60 – 1,18] | 0,321 |
| reponse_avant_surveillance | ×0,84 | [0,57 – 1,23] | 0,364 |
| langue_minoritaire_sur_la_fiche | ×0,66 | [0,27 – 1,63] | 0,372 |

---

## 3. Ce que le retrait déplace

| Ce qu'on regarde | US | US sans les enseignes |
|---|---:|---:|
| Rafale d'auteur | ×49,30 | ×5,19 |
| Secteur des services à domicile | ×4,79 | ×3,42 |
| Avis 1 étoile | ×2,41 | ×3,47 |
| Compte d'auteur sans niveau Local Guide | ×1,83 | ×2,27 |
| Texte de plus de 200 caractères | ×1,10 | ×1,37 |
| Afflux d'avis sur la fiche ce jour-là | ×0,84 | ×0,72 |

### La rafale d'auteur était portée par les chaînes

Le ×49,30 tombe à ×5,19. Ce qui reste repose sur presque rien
(`07_croisements_US_sans_enseignes.csv`) :

| Avis déposés le même jour | Avis | Suppressions |
|---|---:|---:|
| 1 | 112 553 | 1 142 |
| 2 | 535 | 14 |
| 3 | 51 | 3 |
| 4 | 28 | 0 |
| 6 | 6 | 0 |

17 suppressions au-delà d'un dépôt par jour, sur 1 159. La cellule à quatre dépôts, qui portait
44 suppressions sur le passage américain entier, en compte zéro. **Ce coefficient ne se cite
pas sans ce tableau à côté.**

### Le texte long : l'inversion est américaine

Taux bruts par tranche de texte, sur 10 000 avis :

| Tranche | US | US sans les enseignes |
|---|---:|---:|
| Sans texte | 142,0 | 81,1 |
| 1 à 50 car. | 148,3 | 99,3 |
| 51 à 200 car. | 141,1 | 100,2 |
| Plus de 200 car. | 150,9 | **127,3** |

La colonne américaine entière est plate. Sans les enseignes, elle devient croissante, et le
modèle suit : ×1,10 [0,85 – 1,42] puis ×1,37 [1,02 – 1,85]. C'est le même mouvement que sur le
corpus entier, où le coefficient passe de ×0,66 à ×1,38. **L'inversion du texte long se situe
donc du côté américain**, et non dans un mélange entre les deux régions.

### L'afflux devient protecteur

×0,84 [0,69 – 1,02] sur le passage américain entier, ×0,72 [0,58 – 0,89] sans les enseignes. La
fourchette exclut maintenant 1. Une fiche américaine qui reçoit dix fois son rythme habituel un
jour donné voit les avis de ce jour disparaître moins souvent. C'est l'inverse de l'Europe, où
le même indicateur donne ×2,17.

### Le profil d'auteur et le 1 étoile se renforcent

Comme sur le corpus entier, ces deux effets grossissent une fois les enseignes retirées, ce qui
montre qu'ils ne viennent pas d'elles. Le compte sans niveau Local Guide pèse 2 142 avis sur
113 173 et porte 122 des 1 159 suppressions : 569,6 suppressions pour 10 000 avis de ce groupe,
contre 89,2 pour un guide établi.

---

## 4. Ce que vaut ce passage

AUC 0,812 sur des établissements jamais vus, auteurs chevauchants retirés du test : 1 002
établissements mis de côté, 315 avis retirés, entraînement 87 049 avis contre 26 124 en test.

**La calibration est bonne sur les dix déciles** (`07_calibration_US_sans_enseignes.csv`). Le
dernier décile annonce 4,42 % de suppression et on en observe 4,71 %. Le défaut qui rend le
passage européen inexploitable n'apparaît pas ici : le taux de suppression du test suit celui du
corpus, parce que le risque américain est réparti sur beaucoup de fiches.

Réserve inchangée : cette AUC est portée en grande partie par l'âge, variable de contrôle.

---

## 5. Réserves de lecture

- Les 731 avis écartés du corpus valent aussi pour ce passage. Les avis déposés en rafale sont
  52 % des écartés, ce qui affaiblit encore un `log_burst` déjà mince.
- Le retrait des enseignes s'appuie sur `chaine_antiparasitaire_us`, dont les comptes par fiche
  (26, 19, 19, 24) sont vérifiés. Le drapeau des salles de sport espagnoles marque 11 fiches de
  trop, sans suppression, donc sans effet sur les coefficients américains.
- Les avis encore en ligne au dernier passage n'ont pas fini leur histoire.

---

## 6. Ce qui reste à faire

Le passage européen et sa version sans les enseignes restent mal calibrés. Leurs coefficients se
lisent en risque relatif ; les probabilités qu'ils produisent ne se citent pas. La correction
proposée est une validation croisée par établissement en cinq plis, décrite dans
`2026-09-14-interpretation-panel.md` § 5. Elle n'est pas faite.
