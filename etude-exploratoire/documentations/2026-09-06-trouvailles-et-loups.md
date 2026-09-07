---
date: 2026-09-06
projet: reviewflowz-analyse-google
titre: "Toutes les trouvailles, tous les points à vérifier"
statut: document de référence
---

# Toutes les trouvailles, tous les points à vérifier

Deux parties. Ce qui a été trouvé, avec son degré de fiabilité. Ce qui reste à vérifier, avec ce
qu'il faut faire pour chaque point.

Un mot revient dans la colonne « fiabilité » :

- **solide** : ne dépend pas du comptage des suppressions, ou l'erreur de comptage ne peut pas
  le renverser ;
- **à recalculer** : le résultat vient probablement tenir, mais il compte des suppressions qui
  n'en sont pas ;
- **invalidé** : le résultat repose entièrement sur le comptage faux.

---

# Partie 1 — Les trouvailles

## Sur le fonctionnement de Google

### 1. Google supprime les avis récents, presque jamais les vieux
**Fiabilité : à recalculer.**

Sur 10 000 avis en ligne, combien disparaissent d'un jour sur l'autre :

| Âge de l'avis | Disparitions pour 10 000 |
|---|---:|
| 0 à 2 jours | 36 |
| 3 à 6 jours | 40 |
| 7 à 13 jours | 50 |
| 14 à 20 jours | 25 |
| 21 à 29 jours | 9 |
| 1 à 2 mois | 3 |
| plus d'un an | moins de 1 |

Un avis qui a passé son premier mois ne risque presque plus rien.

### 2. Les avis supprimés ne contiennent rien de répréhensible
**Fiabilité : solide.**

Sur 100 avis récents supprimés, 94 ne déclenchent aucun des onze contrôles automatiques.
Les insultes concernent 1,02 % des suppressions. 30 % des avis supprimés n'ont aucun texte.

### 3. La publicité est bloquée avant publication
**Fiabilité : solide.**

Zéro suppression parmi les avis contenant un lien internet. Zéro parmi ceux contenant une
adresse e-mail. Ces avis existent dans le panel et restent en ligne. Google filtre donc ce type
de contenu au moment de la publication, hors de portée de cette collecte.

### 4. Aucun charabia dans les données
**Fiabilité : solide.**

Aucun avis sans voyelle sur douze caractères ou plus, ni parmi les supprimés ni parmi les autres.

### 5. Les suppressions sont concentrées sur peu d'entreprises
**Fiabilité : à recalculer.**

84 % des entreprises n'ont perdu aucun avis en quatorze jours. Vingt-quatre entreprises portaient
18 % des suppressions — sept d'entre elles sortent de cette liste, voir le point 12.

### 6. Google ne sanctionne pas une entreprise parce qu'elle reçoit beaucoup d'avis
**Fiabilité : à recalculer.**

Sans correction, une entreprise à fort afflux paraît 26 fois plus touchée. En tenant compte du
fait qu'elle a simplement plus d'avis récents à perdre, l'effet disparaît et s'inverse.

### 7. Ce qui distingue un avis supprimé d'un autre, dans la même entreprise le même jour
**Fiabilité : invalidé.**

| | Effet | Fourchette |
|---|---:|---:|
| Auteur ayant publié plusieurs avis le même jour | 19 à 26 fois plus | 18 à 40 |
| Avis noté 1 étoile | 3,3 fois plus | 2,2 à 5,1 |
| Avis noté 2 étoiles | 2,1 fois plus | 1,2 à 3,5 |
| Avis modifié après publication | 2,0 fois plus | 1,6 à 2,5 |
| Auteur sans niveau Local Guide | 1,7 fois plus | 1,3 à 2,1 |
| Réponse du patron sous l'avis | 3,7 fois moins | 2,6 à 5,1 |

Sans effet démontré : la longueur du texte, les photos, la langue, le fait d'écrire sur
plusieurs entreprises, être Local Guide niveau 6 ou plus.

### 8. Les vieux avis meurent plus dans les entreprises à fort afflux récent
**Fiabilité : invalidé, à refaire en priorité.**

Un avis de plus d'un an disparaissait 1,5 à 1,7 fois plus dans une entreprise recevant un afflux
récent que dans une entreprise comparable sans afflux. Le résultat tenait sur les avis de plus de
trois ans.

Ce résultat portait l'angle du livrable. Il est aussi le plus exposé : il mesure la mortalité des
vieux avis, et c'est exactement là que se trouvent les fausses suppressions.

### 9. Répondre à un avis : l'ordre des événements est vérifié
**Fiabilité : solide sur l'ordre, invalidé sur l'ampleur.**

Le patron répond vite : délai médian d'un jour, 93 % des réponses en moins de sept jours.
Sur les 1 406 avis supprimés qui avaient une réponse, les 1 406 l'avaient reçue avant leur
suppression. Aucune exception.

L'ampleur de la protection reste à établir : quand on ne compte la réponse qu'à partir du jour
où elle existe vraiment, l'écart brut se réduit de 0,86 à 0,94.

## Sur deux cas particuliers du panel

### 10. Une attaque par avis négatifs, nettoyée par Google
**Fiabilité : solide.**

Deux salles de sport espagnoles. 361 avis d'une étoile publiés les 1er et 2 août 2026, sur une
fiche notée 4,95, par 363 comptes différents. 270 des 399 avis supprimés n'avaient aucun texte.
Un seul contenait une insulte. Google les a effacés dix à quatorze jours plus tard. Aucun n'est
revenu.

Ces 399 avis pèsent 14 % des suppressions du périmètre de l'étude. Ils expliquent pourquoi
« 1 étoile » et « sport et bien-être » ressortaient si forts avant contrôle.

### 11. Une vraie purge de vieux avis, inexpliquée
**Fiabilité : solide sur le constat, aucune explication.**

Bischoff Touristik, autocariste allemand. 48 avis supprimés, étalés de 2018 à 2026, un auteur
différent à chaque fois. Le compteur public de Google passe de 157 à 112, donc la baisse est
réelle. Le robot a lu ses huit pages à chaque passage, donc ce n'est pas un défaut de collecte.
Deux avis seulement sont revenus.

Aucune hypothèse ne tient pour l'instant.

## Sur la qualité des données

### 12. Sept entreprises n'ont jamais rien perdu
**Fiabilité : solide.**

Le 12 août, le robot a lu une page de listing au lieu de deux sur sept fiches. 162 avis ont été
comptés comme supprimés. Les 162 sont revenus au passage suivant. Le compteur public de Google
n'a jamais bougé.

Deux hypothèses ont été écartées en chemin. Ce n'est pas une vieille campagne d'avis rattrapée :
les avis s'étalent de 2016 à 2026, un auteur différent à chaque fois. Ce ne sont pas des comptes
bannis : ces 210 auteurs ont 19 avis ailleurs dans le panel, aucun supprimé.

### 13. Un avis supprimé sur dix revient
**Fiabilité : solide.**

509 des 5 230 suppressions concernent un avis qui réapparaît vivant sur la même fiche. Sur le
périmètre de l'étude : 124 sur 2 853.

Le taux de retour est le plus fort les premiers jours — 29 % le 12 août, 35 % le 14 août — puis
tombe à 3-4 %.

### 14. Le périmètre « avis récents » contenait des avis de treize ans
**Fiabilité : solide.**

Sa définition retenait tout avis vu pour la première fois pendant le suivi. 819 avis de plus de
30 jours y sont entrés, dont 588 de plus d'un an. Ils portent 154 des 2 853 suppressions et ont
un taux de suppression de 18,8 %, contre 2,5 % pour les vrais avis récents.

### 15. Une réponse de propriétaire retirée est indétectable
**Fiabilité : solide.**

L'export garde l'historique de la note et du texte, jamais celui de la réponse. Sur les 2 012
lignes d'historique, aucune ne concerne une réponse.

### 16. Les caractéristiques de l'auteur sont écrasées à chaque passage
**Fiabilité : solide sur le principe, mesure fragile.**

Le fichier ne contient que la dernière valeur observée. Un compte affiché à 0 avis le 12 août
peut afficher 5 avis le 24 : c'est 5 qui figure dans le fichier, y compris sur la ligne du
12 août.

La seule mesure possible porte sur les 602 avis disparus puis revenus, observés deux fois.
Nombre d'avis de l'auteur : 85 % ne bougent pas ou bougent de 1 ou 2. Niveau Local Guide : 82 %
ne bougent pas, 43 comptes perdent leur niveau, dont un niveau 8.

Ces 602 avis ne sont pas une population ordinaire. La mesure ne vaut pas pour les 4,88 millions
d'autres.

### 17. D'où viennent les chiffres 5 314, 5 230 et 2 853
**Fiabilité : solide.**

| | |
|---|---:|
| Lignes marquées supprimées dans l'export | 5 314 |
| dont lignes d'historique d'édition, pas des avis | −84 |
| Avis supprimés | 5 230 |
| dont avis de plus de 30 jours | −2 525 |
| Avis récents supprimés | 2 705 |
| ajouts dus au défaut du point 14 | +148 |
| chiffre utilisé dans toute l'étude | 2 853 |

### 18. L'argument Local Guide du livrable est faux sur les avis récents
**Fiabilité : solide.**

Sur le périmètre récent, 96 % des auteurs sans niveau Local Guide ont aussi un compteur d'avis à
zéro. Ce sont des comptes créés la veille, pas des personnes non inscrites au programme. La
vérification manuelle de 30 profils le confirme : 19 sur 20 affichent aujourd'hui un niveau 1
ou 2.

| Avis récents | Nombre | Supprimés |
|---|---:|---:|
| Auteur avec un niveau et des avis | 93 184 | 2,2 % |
| Auteur avec un niveau, compteur à zéro | 8 397 | 4,3 % |
| Auteur sans niveau, compteur à zéro | 4 966 | 7,5 % |

La formule « ne pas être inscrit multiplie par 16 le risque » ne vaut que pour les vieux avis.

---

# Partie 2 — Les points à vérifier

Classés par ordre d'importance.

## À faire avant tout le reste

### L1. Combien de suppressions sont réelles

509 avis revenus sont ce qu'on peut prouver. Le chiffre est un minimum, pour deux raisons :

- 224 avis ont disparu au dernier passage du panel. S'ils devaient revenir, on ne peut pas le
  voir.
- Un avis disparu et jamais recollecté reste compté comme supprimé.

**À faire** : reconstruire le comptage en excluant les avis qui reviennent, puis mesurer combien
de suppressions restent.

### L2. L'ampleur réelle du défaut de collecte

Jamais mesuré. Une première mesure donne 9 717 passages sur 126 672 où le robot a lu moins de
pages que son maximum sur cette fiche, touchant 1 340 fiches.

Ce chiffre est un majorant : une fiche qui perd légitimement des avis a moins de pages à lire.
Il faut le croiser avec le compteur public de Google pour séparer les deux cas.

**À faire** : un programme qui, pour chaque fiche et chaque passage, compare le nombre de pages
lues à l'habitude de la fiche et l'évolution du compteur Google. En sortie, la liste des passages
à exclure.

### L3. Le Test 2 après correction

Le résultat qui porte le livrable. Les fausses suppressions portent sur des vieux avis dans des
entreprises sans activité récente, donc dans le groupe de comparaison du test. Les retirer
devrait renforcer le résultat.

Le sens de l'erreur reste inconnu tant que le calcul n'est pas refait. Ne rien annoncer avant.

### L4. Les 43 comptes qui perdent leur niveau Local Guide

Un niveau Local Guide monte, il ne redescend pas. Ces 43 comptes ont perdu le leur pendant les
quatorze jours, dont un niveau 8. Ils sont tous hors des sept fiches au listing tronqué, et
dispersés sur 43 fiches différentes.

Deux explications possibles : Google a suspendu ces comptes, ou la page du profil n'a rien
renvoyé ce jour-là.

**À faire** : ouvrir les profils. Le fichier est prêt : `data/verif_niveaux_perdus.csv`, avec le
lien, le niveau avant, le niveau après et les deux dates. S'ils affichent tous un niveau
aujourd'hui, « aucun niveau » dans le fichier ne veut rien dire de fiable.

## Questions ouvertes sur les résultats

### L5. Pourquoi 30 % des avis supprimés n'ont aucun texte

Une note seule, sans commentaire. C'est le plus gros groupe parmi les avis supprimés et personne
ne sait pourquoi Google les vise.

Trois pistes : ils viennent de comptes neufs, ils font partie de salves, ou une note sans texte
est en soi un signal pour Google.

### L6. Bischoff Touristik

Voir le point 11. Vraie perte de 48 avis étalés sur huit ans, sans explication.

**À faire** : regarder si les auteurs concernés ont perdu des avis ailleurs, et si la fiche a
changé (fusion, déménagement, changement de nom).

### L7. Combien d'attaques par avis négatifs dans le panel

Deux ont été repérées par hasard, sur les deux salles de sport. Personne n'a cherché les autres.

**À faire** : repérer les épisodes du type « beaucoup d'avis de même note en peu de jours sur une
fiche ». Les compter, mesurer combien Google en a nettoyé et en combien de temps. Ces cas doivent
sortir des résultats principaux.

### L8. L'effet réel de la réponse du patron

Voir le point 9. L'ordre des événements est vérifié. L'ampleur de la protection n'a jamais été
recalculée en datant la réponse.

**À faire** : refaire le calcul en ne comptant la réponse qu'à partir du jour où elle existe.

### L9. La note au moment du passage

L'export contient 2 012 lignes d'historique qui gardent l'ancienne note et l'ancien texte quand
une personne modifie son avis. Cette information n'a jamais été exploitée. Elle permet de
connaître la note à chaque passage, et non seulement la note finale.

## Contrôles jamais faits

### L10. Les 15 passages incomplets

Le README de l'export les mentionne, en disant qu'il s'agit surtout de fiches retirées par
Google. Personne ne les a regardés.

### L11. Les 84 lignes d'historique marquées supprimées

Ce sont des lignes d'historique d'édition portant une date de suppression. Leur signification
n'a pas été établie.

### L12. Le compteur public de Google comme source de vérité

Il a permis de démasquer les sept fiches. Il n'a jamais été utilisé de façon systématique pour
valider les suppressions, alors qu'il donne un contrôle indépendant du listing.

### L13. Comment est calculée la langue dominante d'une fiche

La comparaison « langue de l'avis contre langue de la fiche » entre dans les modèles. La façon de
déterminer la langue dominante n'a jamais été vérifiée.

## Analyses prévues et jamais faites

### L14. La vérification de la visite

Dans les services à domicile, personne ne se rend à l'adresse. Un client géographiquement
éloigné est-il plus supprimé qu'un client proche ? L'information n'existe que pour 5 % des avis
et se déduit au pays près.

### L15. Le contrôle par apprentissage automatique

Reste-t-il un signal que les analyses n'auraient pas vu ? Jamais lancé. Le programme existe.
