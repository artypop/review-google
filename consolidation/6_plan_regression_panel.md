# Plan pour le 2026-09-30 — refaire la régression du panel (07B / 07C)

Écrit le 2026-09-29 au soir. Rien n'est lancé : ce document liste ce qu'il faut décider avant.

---

## 1. Ce qu'on cherche

La question de l'étude : **quelles caractéristiques d'un avis font qu'il est supprimé, toutes les
autres étant égales ?**

Les chiffres consolidés aujourd'hui y répondent en partie seulement :
- **2.3** donne des taux bruts. Aux États-Unis, 529 avis 5 étoiles sur 10 000 disparaissent, et
  320 sans les 4 chaînes. Le taux « 5 étoiles » compte donc en partie « être chez une des
  chaînes ».
- **4a** ne mesure que la fiche : secteur, taille, région, afflux.
- **4b** compare les avis d'une même fiche, seulement dans les 314 fiches qui ont perdu au moins
  un avis. Il ne peut rien dire du secteur ni de la région.
- **La régression du panel** mesure l'effet de chaque caractéristique sur les 35 751 avis de 03B,
  à note, auteur, secteur et âge égaux. C'est elle que cite le rapport (section 5, tableau 7,
  figure 6).

---

## 2. Ce qui existe déjà

| Script | Date | Ce qu'il fait | Pourquoi il ne suffit plus |
|---|---|---|---|
| `logistic-regression-study/python/07B_regression_panel.py` | 21/09 | modèle complet, une vingtaine de colonnes, une ligne par avis | paliers Local Guide 1-3 / 4+ ; rafale et langue inhabituelle incluses ; enseignes repérées sur le nom |
| `logistic-regression-study/python/07C_regression_reduite.py` | 28/09 (Matthieu) | modèle réduit à 7 caractéristiques, 6 passages (US, Europe, ensemble × complet, sans retraits) | réponse lue au dernier passage du robot (voir question 3) ; « sans retraits » retire tout l'antiparasitaire US |

Les deux lisent `reviews_panel_features_03B` et ajoutent trois colonnes de contrôle d'exposition :
- `age_a_la_premiere_observation_j` ;
- `fenetre_observation_j` ;
- `vu_tardivement`.

Sorties du 07C : `logistic-regression-study/output-study/2026-09-28-sorties-07C/`.

---

## 3. Ce qui est déjà décidé et ne se rediscute pas

- Panel 03B : 35 751 avis publiés du 4 au 17 août 2026, 1 355 suppressions, 5 566 fiches.
- Paliers Local Guide : sans niveau / 1 à 4 / 5 et plus.
- Hors du modèle : la langue inhabituelle pour la fiche, l'avis modifié par son auteur.
- Règle de citation : au moins 20 suppressions, sur au moins 10 fiches, aucune fiche au-delà du
  quart, pour la case et pour sa référence. Chaque effet porte une colonne `citable`.
- Toute fiche citée porte son cid, ses dates et le CSV qui la contient.
- Outil : `statsmodels`. Tout le comptage dans BigQuery. Sorties dans `consolidation/`,
  préfixe **6**.

---

## 4. Les questions à trancher demain

### Question 0 — Sur quels avis ? (posée le 29/09 au soir, à trancher en premier)

**Ce que contient 03B.** Les 35 751 avis publiés du 4 au 17 août (J-7 à J+6), et parmi eux les
1 355 qui ont disparu. Les suppressions d'avis plus anciens n'y sont pas : sur les 4 035
suppressions de la base, 2 680 portent sur des avis publiés hors du 4-17 août.

**Ce qu'Axel voulait**, selon Romain : les avis publiés de J-7 à J+7, plus **toutes** les
suppressions vues pendant les 14 jours, même celles d'avis anciens.

**Le problème de cette table telle quelle.** Un avis de 2019 n'y entrerait que s'il a disparu.
Ses centaines de milliers de voisins de 2019 restés en ligne n'y seraient pas. Tout calcul de
taux ou de régression y verrait « avis de 2019 : 100 % supprimés », et toute caractéristique
fréquente chez les avis anciens paraîtrait liée à la suppression.

| Option | Avis | Suppressions couvertes | Ce qu'il faut savoir |
|---|---|---:|---|
| A. 03B tel quel | publiés du 4 au 17 août | 1 355 | déjà prêt ; ne couvre que les avis récents |
| B. 03B étendu au 18 août (J+7) | + 2 568 avis | un peu plus | les avis du 18 août ne sont suivis que 6 jours |
| C. toute la base, une ligne par avis et par jour ; chaque avis entre à son âge du 11 août | 4 751 680 | 4 035 | couvre toutes les suppressions avec le bon dénominateur ; environ 60 millions de lignes : le modèle doit tourner sur des comptes regroupés dans BigQuery ; les caractéristiques des fiches sont à recalculer hors de 03B |
| D. la table d'Axel à la lettre | J-7 à J+7 + tous les supprimés | 4 035 | inutilisable pour des taux ou une régression (voir plus haut) |
| E. proposition de Romain : tous les avis publiés sur un an (11/08/2025 au 24/08/2026), une ligne par avis et par jour | 487 045 avis de 2026, plus ceux d'août à décembre 2025 | au moins 3 067, au plus 3 400 (`2_1a_par_annee.csv`) | plusieurs millions de lignes, à regrouper dans BigQuery ; l'habitude de réponse de la fiche est à calculer sur l'année d'avant (août 2024 à août 2025), sinon l'avis entre dans sa propre habitude ; mêle la routine du 7e jour et des retraits en bloc d'avis anciens |
| F. 90 jours avant J jusqu'à J+13 (13 mai au 24 août), comme l'ancien 07 | 243 901 (table `02_reviews_panel_…`) | à compter | le choix documenté dans `docs/01-etude.md` § 3 : au-delà de 90 jours, un avis ne risque presque plus rien ; environ 3 millions de lignes jour par jour |

Pour mémoire, la fenêtre du 2.1b (J-30 à J+13) compte 107 644 avis et 2 467 suppressions, soit
61 % des 4 035 (`2_1b_resume.csv`).

**Le biais des 14 jours**, commun à E, F et C : tous les avis sont regardés pendant les mêmes
14 jours, donc les comparaisons entre eux tiennent. Ce qu'on ne voit pas, c'est ce qui arrive
après le 24 août, et ce qui a été supprimé avant le 11. Un avis ancien du panel est un avis
qui a survécu jusqu'au 11 août : les effets se lisent « parmi les avis encore en ligne le
11 août ».

**Recommandation : F.** Au 30e jour, il disparaît environ 4 avis par jour sur 10 000 en ligne
(2.1b), et moins encore ensuite : entre 90 jours et un an, on ajoute des centaines de milliers
d'avis pour peu de suppressions. Une partie de ces suppressions tardives arrive en bloc : les
chaînes les 12 et 17 août, les avis anciens réécrits les 16 et 17 août. Elles se décrivent à
part, comme au 2.2. E reste possible : il faudra alors lire les effets séparément pour les avis
de moins de 90 jours et pour les autres.

### Question 1 — Une ligne par avis, ou une ligne par avis et par jour ?

**Le problème.** Dans 03B, les avis ne sont pas regardés aussi longtemps :
- un avis publié le 17 août est suivi 7 jours ;
- un avis publié le 11 août est suivi 13 jours ;
- un avis publié le 4 août n'est vu qu'à partir du 11 : on ne sait rien de ses 7 premiers jours.

Avec une ligne par avis (07B, 07C), il faut trois colonnes de contrôle pour corriger ces écarts.
Le rapport a dû les expliquer au tableau 10.

Avec une ligne par avis et par jour (format des points 4b et 5), chaque ligne pose une seule
question : « cet avis disparaît-il aujourd'hui, sachant qu'il était là hier ? ». Un avis suivi
7 jours fait 7 lignes, un avis suivi 13 jours en fait 13. Les trois contrôles deviennent inutiles.
L'âge du jour entre comme une colonne de contrôle, jour par jour jusqu'au 8e.

| Option | Pour | Contre |
|---|---|---|
| A. une ligne par avis (comme 07B, 07C) | comparable aux chiffres du rapport actuel | trois contrôles à expliquer ; la réponse du propriétaire ne peut pas être datée |
| B. une ligne par avis et par jour | même format que 4b et 5 ; plus de contrôles d'exposition ; la réponse peut être datée | chiffres non comparables un à un avec le rapport actuel |

**Recommandation : B.** Le point 5 a montré qu'il tourne en 20 secondes sur 380 000 lignes, et
qu'il redonne les résultats du jalon (×0,36 contre ×0,41).

### Question 2 — Quelles colonnes ?

Ma proposition, colonne par colonne. « À trancher » veut dire que j'ai besoin de ta décision.

| Colonne | Découpage proposé (référence en premier) | Statut | Ce qu'on sait déjà |
|---|---|---|---|
| note | 5 étoiles ; 1, 2, 3, 4 | garder | le signal le plus fort partout |
| âge de l'avis ce jour-là | 9 à 13 jours ; puis 1 à 8 jours un par un, 14 et plus | contrôle, ne se cite pas | seulement avec l'option B |
| niveau Local Guide | 1 à 4 ; sans niveau ; 5 et plus | décidé | 4b : sans niveau ×1,56 ; 5 et plus ×0,75, non tranché |
| photos publiées par l'auteur | 0 ; 1 à 20 ; plus de 20 | garder | 4b : plus de 20 photos ×0,41 |
| avis déclarés par l'auteur | 1 ou moins ; 2 à 20 ; plus de 20 | **à trancher** | recoupe « sans niveau » : souvent le même compte neuf ; 4b : 2 à 20 avis ×0,75 |
| photo jointe à l'avis | non ; oui | **à trancher** | aucun effet en 2.3 ni en 4b |
| longueur du texte | sans texte ; 1-50 ; 51-200 ; plus de 200 caractères | **à trancher** | aucun effet en 4b ; le rapport dit déjà « la longueur ne joue pas » |
| secteur | automobile ; les 6 autres | garder | 4a : services à domicile ×2,01 sans enseignes |
| taille de l'entreprise | mono ; small ; large | **à trancher** | 4a : ne tranche pas |
| afflux d'avis sur la fiche | voir ci-dessous | **à trancher** | 4a : ×1,87 pour 1 à 2 fois le rythme habituel |
| rafale d'auteur (plusieurs avis le même jour) | 1 ; 2 et plus | **à trancher** | tu doutes de son intérêt ; 52 suppressions des chaînes viennent d'auteurs à 4 avis ou plus le même jour (2.2) |
| réponse du propriétaire | voir question 3 | **à trancher** | |
| région | voir question 5 | **à trancher** | |

**Sur l'afflux, deux formes possibles :**
- **celle du 07C** : les avis déposés sur la fiche **le jour même**, comparés à son rythme
  habituel. Une petite fiche qui reçoit un seul avis dans la journée y paraît en « pic » ;
- **celle du 4a** : les avis reçus sur **les 14 jours**, comparés à 14 jours de rythme habituel,
  en trois tranches.

Recommandation : la forme du 4a, plus lisible, et déjà mesurée.

### Question 3 — La réponse du propriétaire dans le modèle d'ensemble

**Le problème.** Le 07C utilise `a_une_reponse`, l'état de la réponse au dernier passage du robot.
- Un avis resté en ligne 13 jours a eu 13 jours pour recevoir une réponse.
- Un avis supprimé au 3e jour n'en a eu que 3.
- « Avoir une réponse » mesure donc en partie « avoir survécu ». Le 07C donne ×0,32 aux États-Unis
  sans l'antiparasitaire. Ce chiffre mélange l'effet de la réponse et ce biais.

| Option | Ce que ça donne |
|---|---|
| A. la retirer du modèle d'ensemble | la réponse reste traitée par le point 5, qui est fait pour ça |
| B. la mettre datée, comme au point 5 (seulement avec l'option B de la question 1) | une colonne « réponse déjà là la veille », sans biais de survie ; elle recoupe le point 5 |
| C. garder `a_une_reponse` comme le 07C | biais de survie ; à ne pas citer comme une protection |

**Recommandation : B si la question 1 est tranchée en B, sinon A.**

### Question 4 — Que retire la version « sans enseignes » ?

Deux définitions coexistent :

| Définition | Fiches | Avis retirés de 03B | Suppressions retirées |
|---|---:|---:|---:|
| `biz_surveillance` : les 4 chaînes au nom exact, et les 2 salles (utilisée dans toute la consolidation) | 95 dans la table | 2 327 | 475 |
| « sans retraits » du 07C et de la réunion du 28/09 : **tout** l'antiparasitaire américain repéré par mots-clés, et les 2 salles | 167 présentes dans 03B | 3 160 | 569 |

Sources : `consolidation/sorties/2_3_note.csv` (totaux sans enseignes),
`logistic-regression-study/output-study/2026-09-28-sorties-07C/07C_passages.csv`.

**Recommandation : `biz_surveillance`,** pour rester cohérent avec les points 1 à 5. La version
large peut s'ajouter en septième passage, pour voir ce que change le retrait des autres
fiches antiparasitaires américaines.

### Question 5 — La région dans le passage « ensemble »

Le 28/09, tu as dit que la localisation aux États-Unis ne doit pas être traitée comme une
caractéristique de l'avis. Le 07C la met en contrôle dans le passage « ensemble ».

| Option | Ce que ça donne |
|---|---|
| A. passages US et Europe seulement | plus de question de région ; deux résultats à lire au lieu d'un |
| B. garder le passage « ensemble », la région en contrôle non cité | comme le 07C |

**Recommandation : B.** Les résultats à citer restent ceux de US et Europe séparés. Le passage
« ensemble » sert de vue d'ensemble.

### Question 6 — Faut-il modifier la table 03B ?

`sql/03B_adding_features.bqsql` repère les chaînes sur leur nom exact et garde les paliers 1-3 /
4+. La modifier oblige à reconstruire la table.

**Recommandation : ne pas y toucher.** La table contient déjà le niveau Local Guide brut et le cid
de chaque fiche. Les paliers et le repérage par `biz_surveillance` se calculent dans la requête du
point 6, comme au 4b et au 5.

### Question 7 — La mesure « le modèle sait-il classer ? »

Le rapport (tableau 11) donne la capacité du modèle à classer les avis du plus risqué au moins
risqué : 0,724 sur le panel entier. Le 07B la calcule en cinq tours par fiche.

| Option | Ce que ça donne |
|---|---|
| A. ne pas la refaire | le tableau 11 du rapport est retiré, ou gardé avec sa date du 21/09 |
| B. la refaire | du travail en plus ; avec l'option B de la question 1, il faut d'abord définir ce qu'est « un avis jugé risqué » quand il a une ligne par jour |

**Recommandation : A.** La capacité à classer mesure si le modèle devine quels avis seront
supprimés. Cette prédiction n'est pas demandée (`CLAUDE.md`, § 3).

### Question 8 — Que remplace ce calcul dans le rapport ?

Proposition : le point 6 remplace la section 5 du rapport « propre » (tableaux 7 à 10,
figure 6). Le tableau 8 (taux par note) est remplacé par `2_3_note.csv`.

---

## 5. Le déroulé, une fois les questions tranchées

1. `consolidation/sql/6_panel.sql` : les avis de 03B, avec leurs colonnes. Avec l'option B de la
   question 1, une ligne par avis et par jour.
2. `consolidation/6_regression_panel.py` :
   - tableau des effectifs par case (avis, suppressions, fiches, enseignes, part de la première
     fiche) ;
   - modèle ;
   - effets avec fourchette et colonne `citable` ;
   - fiches derrière chaque case ;
   - graphique de contrôle.
3. **Passages** : US, Europe, ensemble × tous, sans enseignes, soit six passages.
4. **Sorties** : `6_effectifs.csv`, `6_effets.csv`, `6_fiches_par_case.csv`,
   `figures/6_effets.png`. Synthèse `6_regression_panel.md`, qui compare chaque effet au 07C et
   au 4b.
5. **Durée attendue** : moins d'une minute, d'après le point 5. Au-delà de deux minutes,
   `nice -n 19` et je te préviens.

## 6. Vérifications

- La somme des suppressions de chaque passage redonne son total : 1 355 pour « ensemble, tous ».
- Chaque passage converge ; l'état de convergence est écrit dans `6_effets.csv`.
- Les effets de la note et du niveau Local Guide se comparent à ceux du 4b. Un écart fort
  s'explique avant d'être écrit.
- Chaque graphique est regardé avant de rendre la main.

## 7. Ce que ce calcul ne dira pas

- Ce qui arrive aux avis anciens : 03B ne contient que des avis publiés du 4 au 17 août.
- La cause d'une suppression : Google, signalement du propriétaire, contestation d'un tiers.
- Les caractéristiques de l'auteur sont celles lues au dernier passage où l'avis est vu.
