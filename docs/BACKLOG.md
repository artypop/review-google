# Backlog — historique et reste à faire

**C'est le seul fichier du projet qui porte l'historique.** Les choix en vigueur sont dans
[01-etude.md](01-etude.md), [02-donnees.md](02-donnees.md) et [03-resultats.md](03-resultats.md) ;
ils n'ont pas à être répétés ici.

Il remplace, depuis le 2026-09-14 : `etude-exploratoire/BACKLOG.md`,
`etude-exploratoire/PASSATION.md`, `logistic-regression-study/BACKLOG.md` et
`logistic-regression-study/PASSATION.md`.

---

# Ce qui reste à faire

## À faire, par ordre d'intérêt

1. **Comprendre les quatre chaînes américaines de traitement antiparasitaire.** Elles portent
   692 des 2 595 suppressions du panel, presque toutes sur des avis 4 et 5 étoiles. Vérifié le
   2026-09-17 : aucun afflux soudain d'avis, la hausse d'EcoShield est durable et commence en
   avril (`sql/controle_E_afflux_chaines_antiparasitaires.bqsql`). Deux pistes ouvertes : leurs
   textes nomment très souvent un technicien — compter la répétition d'un même prénom sur les
   avis d'une fiche — et 44 de leurs avis viennent d'auteurs ayant publié 4 avis ou plus le même
   jour sur leurs succursales, tous supprimés, contre 34 avis américains hors chaînes dans le
   même cas dont aucun supprimé.
2. **Chercher les attaques par avis négatifs dans tout le panel.** Deux ont été trouvées par
   hasard. Le balayage systématique n'a jamais été fait, et c'est ce qui permettrait de dire si
   le phénomène est marginal.
3. **Croiser le pic au septième jour avec ce qui fait tomber un avis.** Qui sont les avis qui
   sautent à 7 jours ? C'est le motif le plus net de l'étude et il n'a pas d'explication.
4. **Comprendre pourquoi la réponse du propriétaire joue en sens opposés** selon l'habitude de
   réponse de la fiche : ×0,40 sur les fiches qui répondent à plus de 75 % de leurs avis, ×2,0
   sur celles qui répondent à 25 à 75 %. Il faudrait le contenu des réponses ou les
   signalements, que les données ne portent pas.
5. **Construire le modèle des suppressions tardives**, après le 8e jour de l'avis. Le modèle A
   couvre les 8 premiers jours ; rien ne couvre la suite.
6. **Remonter dans `sql/03` les transformations restées en Python** — les tranches de texte, le
   logarithme des rafales, le regroupement des secteurs rares, les tranches d'habitude de
   réponse. Elles sont définies à deux endroits, ce qui est le défaut corrigé partout ailleurs.
7. **Passer le 07 au repérage des enseignes par `biz_surveillance`.** Il utilise encore le nom
   d'enseigne pour les salles de sport, ce qui écarte 90 avis de plus, sans aucune suppression
   parmi eux.
8. **Mettre `docs/03-resultats.md` et `docs/05-resume-regressions.md` à jour** des passages du
   2026-09-17.

## Questions de méthode jamais refermées

Quatre décisions ont été soulevées puis laissées en suspens. Aucune n'est bloquante, toutes
reviendront.

- **Le niveau Local Guide** : tranché le 2026-09-17. Trois paliers — sans niveau, 1 à 3, 4 et
  plus — dans `sql/03_adding_features.bqsql`. Reste ouvert : le palier 4 et plus ne protège pas
  une fois les photos et le nombre d'avis de l'auteur pris en compte, et personne n'explique
  pourquoi.
- **Le recalcul à âge comparable** : remplacé le 2026-09-17 par un indicateur oui / non, le 8e
  jour de l'avis tombe-t-il pendant le suivi. Reste ouvert : tous les avis publiés avant le
  3 août sont rangés ensemble, qu'ils aient 9 ou 90 jours.
- **Les marges d'erreur de l'analyse B** : sont-elles toutes calculées par la méthode lente, ou
  certaines sont-elles restées sur la méthode rapide sans que ce soit écrit ? La méthode rapide
  surestime la rafale d'auteur.
- **Les trois contrôles « effet ou accident »** — sur combien de journées, sur combien d'unités,
  survit-il au retrait des cas extrêmes ? Faut-il les passer systématiquement ? Le pic du 16 août
  ne leur a toujours pas été soumis.

## Vérifications listées le 2026-09-06 et jamais faites

Quinze avaient été recensées. Trois sont faites depuis. Les douze autres, dans l'ordre du
document d'origine :

| | Sujet | État |
|---|---|---|
| L1 | Combien de suppressions sont réelles | **fait** le 2026-09-08 : 4 747 sur 5 230 |
| L2 | L'ampleur réelle du défaut de collecte, page par page | à faire |
| L3 | Le Test 2 après correction du comptage | **fait** le 2026-09-09, il tient |
| L4 | Les 43 comptes qui perdent leur niveau Local Guide | à faire — le fichier d'échantillon est prêt |
| L5 | Pourquoi 30 % des avis supprimés n'ont aucun texte | à faire |
| L6 | Bischoff Touristik : un retrait obtenu sur demande ? | à faire |
| L7 | Combien d'attaques par avis négatifs dans le panel | à faire — voir le point 2 ci-dessus |
| L8 | L'effet réel de la réponse du commerçant | **fait** le 2026-09-14, complété le 2026-09-17 : l'effet se sépare selon l'habitude de réponse de la fiche |
| L9 | La note de la fiche au moment de chaque passage | à faire |
| L10 | Les 15 passages incomplets | à faire |
| L11 | Les 84 lignes d'historique marquées supprimées | à faire |
| L12 | Le compteur public de Google comme source de vérité | à faire |
| L13 | Comment est calculée la langue dominante d'une fiche | à faire |
| L14 | La vérification de la visite | à faire |
| L15 | Le contrôle par apprentissage automatique | à faire — jamais relancé |

## Écarté, et à ne pas reproposer sans élément nouveau

- **Le drapeau qui repère les salles de sport attaquées dans `sql/02`** se fonde sur le nom
  d'enseigne et marque 13 fiches quand 2 sont attaquées. Les 11 autres portent 90 avis et zéro
  suppression. Décision de Romain, 2026-09-14. Depuis le 2026-09-17, les scripts 08 et 10
  passent par la table `biz_surveillance` ; le 07 utilise encore le nom.
- **Le script `09_simplified_reg.py`** : modèle à cinq caractéristiques écrit le 2026-09-17, qui
  utilise `a_une_reponse`, l'état de la réponse au dernier passage du robot. Cette colonne
  mesure en partie la survie de l'avis. Ses sorties, dans `output-study/2026-09-17-sorties-09/`,
  ne sont pas à citer.
- **Enrichir un corpus court avec des avis plus anciens jamais supprimés** : ces avis ont déjà
  franchi le filtre des premiers jours, et les effets en sortiraient gonflés. Écarté le
  2026-09-17.
- **Compter comme restés en ligne les avis supprimés après la fenêtre d'observation** : la durée
  d'observation varie selon la date de publication. Ils sont retirés du corpus depuis le
  2026-09-17, dans le modèle A et dans le 08.
- **Les avis contenant un lien** : zéro suppression dans le panel, ils sont filtrés avant
  publication.
- **L'effet « avis modifié »** : non mesurable sur le panel actuel, qui exclut les avis à
  plusieurs enregistrements.
- **Les caractéristiques de campagne d'auteur** : 99,3 % des compteurs valent zéro, le corpus ne
  couvrant que 9 048 commerces.
- **Le score de détection de texte écrit par une IA**, la recherche de textes identiques, l'usage
  des champs vides, et toute expérience consistant à publier des avis.

---

# L'historique

## 2026-09-17 — paliers d'auteur, mesure de qualité, réponse par type de fiche

**Nouvelle table de caractéristiques, `reviews_panel_features_03`** (`sql/03_adding_features.bqsql`),
même corpus que la 02 : 225 757 avis, 2 595 suppressions. Trois changements de colonnes — palier
Local Guide en trois valeurs, photos de l'auteur, habitude de réponse de la fiche.

**La mesure de qualité passe en cinq tours par établissement**, ce qui referme le point mis en
pause le 2026-09-14. Le niveau annoncé par le modèle redevient juste en Europe : 409 suppressions
annoncées pour 409 constatées, contre 3,72 % annoncés pour 1,47 % observés sur le dernier décile
de l'ancien tirage.

**L'âge au 11 août est remplacé par un indicateur oui / non** : le 8e jour de l'avis tombe-t-il
pendant le suivi ? L'ancienne variable valait 0 pour les 15 248 avis publiés pendant le suivi,
quelle que soit leur durée d'observation.

**Le graphique de calibration est remplacé par une courbe de ciblage**, qui dit quelle part des
suppressions tombe dans les 10 % d'avis jugés les plus risqués. Lue par période de publication,
elle vaut 22 à 31 %, contre 41 à 51 % quand la date de publication aide le modèle.

**Nouveau modèle A** (`python/10_modele_A_8_premiers_jours.py`) : les avis publiés du 10 au
16 août, suivis jusqu'à leur 8e jour, avec les suppressions comptées dès le lendemain de la
publication. La note et le profil de l'auteur y donnent les mêmes effets que sur tout le panel.

**Le 08 est refait avec l'habitude de réponse de la fiche.** L'effet d'une réponse se sépare en
deux : ×0,40 sur les fiches qui répondent à plus de 75 % de leurs avis, ×2,0 sur celles qui
répondent à 25 à 75 %. L'effet moyen, ×0,59, mélange les deux.

**Deux contrôles écrits** : `controle_D_delai_suppression_enseignes.bqsql`, qui montre que les
suppressions des deux salles de sport tombent 9 à 22 jours après la publication, et
`controle_E_afflux_chaines_antiparasitaires.bqsql`, qui écarte l'hypothèse d'un afflux soudain
sur les chaînes.

**Les synthèses du jour** sont dans `logistic-regression-study/output-study/` :
`2026-09-17-synthese-generale.md`, `-synthese-07.md`, `-synthese-modele-A.md`, `-synthese-08.md`
et `-argumentaire-effectifs.md`. Le brief d'équipe est mis à jour, et ses exemples de lignes sont
anonymisés.

## 2026-09-14 — interprétation, effet de la réponse, remise en ordre

Les résultats des quatre passages du modèle sont enfin lus et écrits. Le résultat central : aux
États-Unis l'avis 5 étoiles est supprimé plus souvent que l'avis 3 ou 4 étoiles, en Europe
l'inverse. 71 % des suppressions du panel portent sur un avis 5 étoiles.

**La divergence sur la réponse du commerçant est refermée.** L'analyse B lisait la réponse dans
l'état où elle se trouvait au dernier passage du robot, recopié sur tous les précédents. Datée,
elle donne ×0,40 quand l'ancienne façon de compter donnait ×0,30 ; seul ce facteur bouge, les
autres se déplacent de 1 à 5 %.

**Le montage à jalon fixe répond à la question du client d'Axel** : répondre dans les deux jours
divise le risque par 1,8 hors des quatre chaînes antiparasitaires. L'effet tient sur quatre
moments d'observation différents.

**Des chiffres qui ne correspondaient à aucun fichier de sortie ont été corrigés** : le tableau
des quatre passages, un « ×0,93, p = 0,649 » qui n'existait nulle part, un « 50,0 % contre
35,0 % » non régénérable, et une affirmation fausse du README sur le comptage des tables locales.

**La qualité du modèle européen s'est révélée non mesurable** telle qu'elle est calculée
aujourd'hui — voir « en pause » ci-dessus.

Le dossier a été réorganisé en `sql/`, `python/`, `output-study/` et `legacy/`, puis le projet
entier remis à plat : cette documentation, et la mise au gel de l'étude exploratoire.

## 2026-09-13 — le panel change de forme

**Une ligne par avis**, là où il y en avait une par avis et par passage. Une observation, un
sort, aucune dépendance entre les lignes d'un même avis.

Quatre corrections de fond dans le calcul des caractéristiques, toutes sur le même principe :
une caractéristique ne doit jamais être mesurée après le moment qu'elle prétend prédire.

- la réponse du commerçant est datée ;
- le passé d'un auteur est arrêté à la veille de l'avis examiné ;
- le rythme habituel d'une fiche est gelé sur les douze mois précédant le suivi — il était
  calculé sur une fenêtre contenant le pic lui-même, ce qui divisait son propre effet par deux ;
- la mesure de langue étrangère comparait un code de langue à un code de pays, ce qui marquait
  71 % des avis américains comme étrangers parce que `en` n'est pas `us`.

**Décision assumée** : les avis ayant plusieurs enregistrements sont exclus du corpus. 731 avis,
soit 0,3 % des avis mais 3 % des suppressions.

## 2026-09-10 — le critère de fiche attaquée

Le seuil « plus de 5 % des avis perdus » est abandonné après examen fiche par fiche des 24 qu'il
retenait. Remplacé par une signature à trois conditions, plus une quatrième décidée ce jour-là
et jamais écrite dans le code.

## 2026-09-09 — le comptage est corrigé, tout est relancé

Trois défauts trouvés et corrigés le même jour :

- le programme qui construit les tables n'appliquait pas la définition corrigée d'une
  suppression ;
- la table maîtresse comptait deux fois les avis disparus puis revenus — 5 503 lignes pour
  4 737 suppressions réelles ;
- la caractéristique « rafale d'auteur » comptait l'enregistrement de disparition comme un
  second avis du même auteur le même jour. Elle lisait donc en partie la suppression qu'on lui
  demandait de prédire. Corriger cette fuite a fait passer son effet de ×7,2 à ×3,9.

Les cinq analyses ont été relancées sur le comptage corrigé.

## 2026-09-08 — ce qu'est une suppression

La colonne qui dit qu'un avis a disparu ne veut pas dire que Google l'a supprimé. Deux
situations sont retirées : le raté de collecte d'une journée, et 24 bugs d'enregistrement.
**Une absence de deux jours ou plus est une vraie suppression.**

Le comptage passe de 5 230 disparitions constatées à 4 747 suppressions retenues.

Le pic au septième jour de vie de l'avis est mesuré et vérifié comme un effet d'âge.

## 2026-09-06 et avant — les premiers travaux

Construction du panel, premières analyses facteur par facteur, repérage des deux salles de sport
espagnoles attaquées. Les résultats de cette période ont été refaits après la correction du
comptage ; ceux qui n'ont pas pu l'être ne sont plus cités.

---

# Où est passé l'ancien contenu

| Fichier | Ce qu'il portait | Où c'est maintenant |
|---|---|---|
| `etude-exploratoire/PASSATION.md` § 1 | les consignes de rédaction | `../CLAUDE.md` § 2 |
| `etude-exploratoire/PASSATION.md` § 6 | les pièges du jeu de données | [02-donnees.md](02-donnees.md) § 5 |
| `etude-exploratoire/BACKLOG.md` | les réserves à porter au livrable | [03-resultats.md](03-resultats.md) § 5 |
| `logistic-regression-study/PASSATION.md` § 5 | les deux mesures de langue | [02-donnees.md](02-donnees.md) § 6 |
| `logistic-regression-study/BACKLOG.md` | les résultats des passages | [03-resultats.md](03-resultats.md) § 2 |
| `audit-process.md` | l'audit de méthode des 20 notes exploratoires | **déplacé** en `../etude-exploratoire/audit-methode.md` : il décrit des notes de ce dossier, il reste avec elles |
| `BONNES-ET-MAUVAISES-PRATIQUES.md` | les 15 écueils | [04-enseignements.md](04-enseignements.md), partie 1 |

Les fichiers eux-mêmes sont supprimés du dépôt. `git log --diff-filter=D --name-only` les
retrouve, et `git show <commit>^:<chemin>` en rend une copie.
