# L'étude : la question posée, sur quoi, avec quelles règles

Dernière mise à jour : 2026-09-14.

---

## 1. La question

Google supprime des avis. Certains sont de faux avis, et les retirer est le but recherché.
D'autres sont de vrais avis, écrits par de vrais clients, et leur suppression est une erreur.

**L'étude cherche quelles caractéristiques banales d'un avis font qu'il a plus de chances d'être
supprimé.** L'intérêt du commanditaire porte sur le second cas : les avis honnêtes qui sautent.

Commanditaire : Axel, dirigeant de ReviewFlowz. Interlocuteur et validateur : Romain.

---

## 2. Sur quelles fiches

**9 048 établissements Google Maps**, suivis un jour par jour du 11 au 24 août 2026.

Le panel n'a pas été tiré au hasard. Il a été construit pour couvrir sept secteurs, deux
régions et trois tailles d'entreprise :

- **Sept secteurs** : voyage, hôtellerie, restauration, services à domicile, santé, automobile,
  sport et bien-être.
- **Deux régions** : États-Unis et Europe hors Royaume-Uni.
- **Trois tailles**, comptées en nombre d'établissements du même groupe : un seul, de 4 à 10,
  de 20 à 50.

Trois décisions de construction ont des conséquences qu'il faut connaître avant de lire un
résultat :

1. **L'unité tirée au sort est le groupe, pas l'établissement.** Quand un groupe est retenu,
   tous ses établissements entrent dans le panel. Deux établissements d'une même enseigne ne
   sont donc pas deux informations indépendantes, et les calculs en tiennent compte.
2. **Les groupes de 2 à 3 et de 11 à 19 établissements sont absents**, pour garder des tailles
   nettes. Les groupes de plus de 50 établissements aussi.
3. **Seules les fiches ayant entre 100 et 10 000 avis** ont servi à sélectionner un groupe.

Le panel couvre 41 pays, dont un seul hors d'Europe. Le Royaume-Uni n'y est pas.

---

## 3. Sur quels avis : le corpus de la régression

Le suivi porte sur 4,88 millions d'avis. La régression n'en retient pas autant.

**225 757 avis, publiés entre le 2026-05-13 et le 2026-08-16**, sur 8 205 fiches. Parmi eux,
2 595 ont été supprimés, soit 1,15 %.

Les deux bornes :

- **Borne basse, le 13 mai** : 90 jours avant le premier passage du robot. Au-delà, le risque de
  suppression devient si faible qu'un avis ancien n'apporte plus d'information — il est cent
  fois moins exposé qu'un avis récent.
- **Borne haute, le 16 août** : le sixième passage. Un avis publié ce jour-là est encore observé
  pendant huit jours avant la fin du suivi. Accepter des avis plus récents reviendrait à faire
  entrer des avis qu'on n'a presque pas eu le temps de regarder.

**Deux populations cohabitent dans ce corpus, et il ne faut pas les confondre :**

| | Avis | Supprimés |
|---|---:|---:|
| Déjà en ligne au premier passage, âgés de 1 à 90 jours | 210 509 | 0,95 % |
| Publiés pendant le suivi, du 11 au 16 août | 15 248 | 3,92 % |

Les seconds sont les seuls dont on a vu les premiers jours de vie. C'est sur eux, et eux seuls,
que repose l'étude sur l'effet de répondre vite à un avis.

**731 avis sont exclus du corpus** parce qu'ils ont plusieurs enregistrements dans le fichier.
Cette exclusion n'est pas neutre : elle retire 0,3 % des avis mais environ 3 % des suppressions.
Elle est assumée, et ses conséquences sont écrites dans [02-donnees.md](02-donnees.md) § 3.

---

## 4. Les choix de modélisation arrêtés

**L'âge de l'avis est une variable de contrôle, jamais un critère de découpage.** Le risque est
divisé par 21 entre un avis du jour et un avis de trois mois. Il entre dans le modèle pour que
les autres caractéristiques se lisent à âge comparable. **Son propre coefficient n'est pas un
résultat à citer.** Sans lui, « avoir une réponse du commerçant » ressort protecteur alors que
c'est l'âge déguisé.

**Il entre sous forme de logarithme**, parce que la chute du risque est brutale au début puis
plate. Un coefficient sur une échelle droite donnerait la même baisse entre le premier et le
deuxième jour qu'entre le quatre-vingtième et le quatre-vingt-unième.

**Les résultats se lisent en risque relatif**, jamais en probabilité brute. « Deux fois plus
supprimé qu'un avis identique par ailleurs » et non « 3 % de chances d'être supprimé ».

**La qualité du modèle se juge sur sa capacité à classer et sur la justesse de ses prévisions**,
jamais sur le pourcentage de bonnes réponses : avec 1 % de suppressions, un modèle qui répond
toujours « pas supprimé » a 99 % de bonnes réponses et ne sert à rien.

**Le jeu d'essai est mis de côté par établissement et par auteur**, jamais ligne par ligne. Sans
cela, le modèle retrouverait en test des fiches et des auteurs qu'il a déjà vus à
l'entraînement.

**Tout résultat est produit deux fois : avec et sans les six enseignes signalées** — quatre
chaînes américaines de traitement antiparasitaire et deux salles de sport espagnoles. Elles
portent 39,3 % des suppressions du panel à elles seules.

**L'outil est `statsmodels`**, parce qu'on cherche des coefficients et des marges d'incertitude
pour expliquer, pas un modèle qui prédit. `scikit-learn` n'est pas interdit, il n'est simplement
pas l'outil de cette question.

---

## 5. Ce qui est écarté, et qu'il ne faut pas proposer

- un score de détection de texte écrit par une IA : les détecteurs ne sont pas fiables ;
- la recherche de textes identiques à l'intérieur d'un même établissement ;
- l'usage des champs vides (adresse, téléphone) comme signal ;
- toute expérience consistant à publier des avis pour voir ce qui se passe.

---

## 6. La chaîne de traitement

Trois étapes, dans cet ordre. Tout se passe dans BigQuery, sauf la modélisation.

| Étape | Fichier | Produit |
|---|---|---|
| 1. Le corpus | `sql/01_selection_panel.sql` | la table `reviews_panel_selection`, 225 757 avis, une ligne par avis |
| 2. Les caractéristiques | `sql/02_adding_features.sql` | la table `reviews_panel_features`, les mêmes avis, 42 colonnes |
| 3. Les modèles | `python/07_regression_panel.py` et `python/08_effet_reponse_commercant.py` | les dossiers datés de `output-study/` |

**La table est construite et interrogée uniquement dans BigQuery.** Aucune version en parallèle
ailleurs : c'est en dupliquant des définitions que l'étude précédente a fini par se contredire
elle-même.

Avant de lancer `08`, lancer `sql/controle_C_reponses_au_jalon.sql`, qui vérifie qu'il y a de
quoi calculer.

---

## 7. L'étude qui a précédé

Un premier travail d'exploration a eu lieu du 4 au 9 septembre 2026, dans
`etude-exploratoire/`. Il a servi à comprendre les données, à repérer les défauts de comptage et
à produire les premiers résultats.

**Ce dossier est gelé depuis le 2026-09-14.** Ses résultats qui tiennent encore sont repris dans
[03-resultats.md](03-resultats.md), ses définitions dans [02-donnees.md](02-donnees.md). On ne
relance rien dedans et on n'y écrit plus. Voir `etude-exploratoire/README.md`.
