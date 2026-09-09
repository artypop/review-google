# Note de méthode — session du 2026-09-08

Objet : ce qui a été fait pour mesurer l'âge des avis supprimés, dans quel ordre, ce qui a été
jeté et pourquoi. Écrite pour que personne ne refasse les détours ni les contrôles déjà faits.

---

## Ce qui reste, et à quoi ça sert

| Fichier | À utiliser pour |
|---|---|
| `2026-09-08-age-a-la-suppression.md` | La référence. Suppressions par âge en jours (1 à 30) et par journée du suivi. |
| `2026-09-08-histogramme-age-des-suppressions.md` | Le mail à Axel. Les mêmes suppressions en tranches larges. |
| `../scripts/suppressions_corrigees.py` | Importer la définition corrigée d'une suppression dans un nouveau script. |
| `../scripts/age_a_la_suppression.py` | Régénérer la note de référence. `--age-max` règle le dernier âge du tableau. |
| `../scripts/histogramme_age_suppressions.py` | Régénérer la note en tranches larges. |
| `2026-09-08-cas-attaque-salles-de-sport.md` | Le cas des deux salles de sport espagnoles, fiche par fiche. Remplace les chiffres du 2026-09-06. |
| `../scripts/cas_attaque_salles_de_sport.py` | Régénérer ce cas. |

## Le socle : ce qu'on appelle une suppression

`deleted_detected_at` dans l'export brut veut seulement dire que le robot ne retrouve plus
l'avis à un passage. Deux situations rendent cette déduction fausse, et il faut les retirer
avant tout comptage :

1. **Bug d'édition** (24 avis) : même auteur, même note, même date de dépôt, texte réécrit d'une
   ligne à l'autre. Une modification mal enregistrée par le robot.
2. **Raté de collecte** : l'avis est absent un seul jour puis revient à l'identique. Un vrai
   retrait revu par Google prend plusieurs jours, pas vingt-quatre heures.

Les avis absents 2 jours ou plus avant de revenir restent comptés comme supprimés, à la date de
leur première disparition.

**5 230 disparitions brutes -> 4 747 suppressions retenues.**

La référence de cette logique est `logistic-regression-study/sql/01_build_avis_deleted_panel.sql`,
en BigQuery. `../scripts/suppressions_corrigees.py` la réimplémente en DuckDB pour les scripts
locaux. **C'est la seule copie hors BigQuery** : si la définition change là-bas, ce fichier est à
reprendre, et lui seul.

## Comment l'âge est mesuré

`age_days = date_diff('day', created_at, wave.started_at)`.

- `created_at` est la date de publication donnée par Google. Vérifié comme étant un vrai
  horodatage, pas une date reconstruite : la répartition horaire suit une courbe de journée
  plausible (creux à 4h, pic à 17h), les 60 valeurs de secondes sont présentes, et 945 avis sur
  58 107 seulement tombent sur la seconde zéro. Le point valait d'être vérifié parce qu'une date
  reconstruite depuis un libellé « il y a une semaine » aurait fabriqué des âges multiples de 7.
- Une observation = un avis encore en ligne à un passage du robot. On part de la vague 2, la
  vague 1 étant le recensement initial. Un avis n'entre qu'au passage suivant celui qui l'a
  découvert, ce qui rend l'âge 1 jour peu observé (3 700 observations contre ~32 000 aux autres
  âges) et l'âge 0 jour inobservable.

## Le fait qui rend tout simple

**Le corpus contient à peu près autant d'avis de chaque âge** : environ 32 000 observations par
âge, de 2 jours à 30 jours. Donc les nombres bruts de suppressions se comparent directement d'un
âge à l'autre, sans dénominateur, sans pondération, sans exposition.

Ce fait n'a été constaté qu'à la fin de la session, après trois constructions destinées à
contourner un problème de dénominateur qui n'existait pas. Le vérifier en premier est le bon
réflexe : une colonne « observations » plate dispense de tout le reste.

## Résultats

**Par âge en jours.** 449 suppressions à 7 jours de vie, contre 279 à 6 jours, 134 à 9 jours,
118 à 8 jours, 43 à 5 jours. Pic net et isolé : 3,8 fois le niveau de 8 jours, 10 fois celui de
5 jours. Vérifié comme étant un effet d'âge et non une purge, voir le tableau des contrôles.

**En tranches larges.** 51,6 % des suppressions frappent un avis de moins d'un mois, 30,3 % un
avis de plus d'un an. Le poids du vieux stock vient de son volume et non de son risque :
0,0027 % de risque par jour contre 0,2699 % pour un avis de moins d'un mois.

**Sur la durée de vie.** 7,65 % des avis neufs sont supprimés dans leurs 30 premiers jours
(risque cumulé, jours d'âge 1 à 29).

**Par journée du suivi.** De 153 suppressions le 14/08 à 760 le 17/08, un facteur 5. Chaque
journée se répartit sur 129 à 275 établissements. Une exception : le 16/08, où un seul
établissement porte 26 % des suppressions du jour, et où le total passe de 706 à 486 en écartant
les fiches purgées à plus de 5 %.

**Concentration, recalculée sur le comptage corrigé.** 85,4 % des établissements n'ont aucune
suppression ; 24 fiches ayant perdu plus de 5 % de leurs avis portent 14,4 % du total. Les
chiffres « 84 % / 39 fiches / 19,5 % » de la note du 2026-09-06 datent d'avant la correction du
comptage et ne valent plus.

> **Ajout du 2026-09-09.** Le critère « plus de 5 % des avis perdus » est abandonné. Vérification fiche par fiche des 24 qu'il retenait : 2 attaquées, 1 retrait obtenu sur demande, 15 qui ne perdent que des avis 4 et 5 étoiles — le sujet même de l'étude — et 6 fiches de moins de 25 avis. Le nouveau critère retient 4 fiches et 385 suppressions, soit 8,1 % du total. Définition dans `../../CLAUDE.md`, Conventions de Restitution point 5. Les chiffres « 24 fiches / 682 suppressions / 14,4 % » de ce document ne décrivent plus la règle en vigueur.


## Contrôles faits — ne pas les refaire

| Contrôle | Résultat |
|---|---|
| **Le pic à 7 jours est-il une purge ?** | **Non, c'est un effet d'âge.** Les 449 suppressions sont étalées sur 12 des 13 journées du suivi et sur 144 établissements (le plus touché en porte 6 %), et le pic reste après retrait des deux journées les plus chargées (381 à 7 jours contre 200 à 6 jours et 75 à 8 jours). Détail au § « Le pic à 7 jours » de `2026-09-08-age-a-la-suppression.md`. |
| Rythme hebdomadaire (bosses à 14, 21, 28 jours) | **Écarté.** L'écart entre âges multiples de 7 et autres âges tombe de ×2,6 à ×1,5 dès qu'on retire l'âge 7, et ne tient plus que dans 5 vagues sur 13, portées par les 16 et 23 août. |
| `created_at` reconstruit depuis un libellé relatif | **Écarté.** Horodatage réel, voir plus haut. |
| Fiches massivement purgées | **La répartition tient sans elles** : moins d'un mois 47,7 %, plus d'un an 33,4 %. |
| Censure à droite | **La hiérarchie tient** sur la seule cohorte présente à la vague 1 : 2,29 % des avis de moins d'un mois supprimés contre 0,034 % des avis de plus d'un an. |

## Ce qui a été construit puis jeté

Trois constructions ont été produites, puis supprimées du dépôt. Elles sont consignées ici pour
qu'on ne les repropose pas comme des idées neuves.

**1. Cohorte des avis nés pendant le suivi** (`cohorte_avis_nes_pendant_le_suivi.py`, supprimé).
Restreindre aux avis publiés à partir de la veille du premier passage, pour supprimer la
troncature à gauche. Techniquement correct, et elle situait le pic aux jours 6 et 7. Jetée parce
que le tableau par âge sur tout le corpus donne le même résultat en une ligne de SQL, et que
cette note était devenue illisible à force de contrôles empilés.

**2. Matrice vague × âge sur un groupe fixe** (`suppressions_par_vague_et_age.py`, supprimé).
Un groupe d'avis figé (les N journées de publication précédant le premier passage), croisé par
vague et par âge à la suppression. La propriété intéressante : chaque case ne contient qu'une
seule journée de publication, donc les cases se comparent entre elles alors que les totaux de
colonnes ne se comparent pas. Jetée parce que la lecture demandait trois paragraphes
d'explication pour un résultat que le tableau par âge donne directement.

**3. La conclusion « le 16 août est une journée à part, 35 % des suppressions ».** Fausse comme
formulée. Ces 35 % étaient la part du 16 août **dans le groupe de 8 jours** que j'avais choisi,
pas dans le corpus. Sur tout le corpus, le 16 août fait 706 suppressions et le 17 août en fait
760 : il n'y a pas de journée dominante, seulement une variation d'un facteur 5 sur le suivi.
Leçon à garder : une part n'a de sens qu'avec son dénominateur écrit à côté.

## Erreurs de méthode de la session, à ne pas répéter

- **Vérifier la platitude du dénominateur avant de construire quoi que ce soit.** Trois
  constructions ont servi à contourner un problème de comparabilité qui n'existait pas.
- **Écrire le dénominateur à côté de chaque pourcentage.** L'erreur du 16 août n'a pas d'autre
  cause, et celle du cas des salles de sport non plus : deux établissements additionnés puis
  rapportés à un seul donnaient « 24 % du listing » au lieu de 28 % et 17 %. Deux
  établissements ne s'additionnent pas pour produire un ratio. Voir
  `2026-09-08-cas-attaque-salles-de-sport.md`.
- **Ne pas empiler les contrôles dans la note de résultat.** Les contrôles vont dans un tableau
  à part, avec leur verdict en un mot. Le résultat reste lisible.
- **Une part et un nombre ne se mettent pas dans la même phrase sans dire de quoi.**
  « 582 suppressions puis 20,6 % » ne se lit pas.
- **Un mot ne doit désigner qu'une chose.** « Cohorte » a servi dans la même note pour le groupe
  d'avis suivi et pour les avis publiés le même jour.

## Ce qui n'est pas fait

- **Comprendre ce qui se joue à 7 jours.** Un délai reproductible ressemble à un cycle de
  traitement plutôt qu'à une réaction à un signalement, mais rien ne l'établit.
- **Croiser le pic à 7 jours avec les facteurs de l'analyse B** : qui sont les avis qui tombent
  à 7 jours, et diffèrent-ils des autres ? C'est le candidat direct pour l'angle faux positifs.
- **Le jour de vie 0** reste hors de portée d'une collecte quotidienne.
- **La fenêtre de 14 jours** ne montre pas les révisions de modération à plusieurs mois.
