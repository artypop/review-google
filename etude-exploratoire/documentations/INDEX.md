# Index de la documentation — étude exploratoire

Établi le 2026-09-08, après la correction du comptage des suppressions.

**Comptage de référence : 5 230 lignes de disparition, portées par 5 109 avis distincts,
-> 4 747 suppressions retenues en DuckDB (4 737 en BigQuery, voir `CLAUDE.md` point 4).**
Le 5 230 compte des événements, le 4 747 des avis : deux unités, à ne pas mettre de part et
d'autre d'une flèche sans le dire. Définition
dans [`../scripts/suppressions_corrigees.py`](../scripts/suppressions_corrigees.py), qui
réimplémente en DuckDB la logique de
[`../../logistic-regression-study/sql/01_build_avis_deleted_panel.sql`](../../logistic-regression-study/sql/01_build_avis_deleted_panel.sql).

Trois statuts :

| Statut | Ce que ça veut dire |
|---|---|
| **À jour** | Aucun chiffre périmé. Citable tel quel. |
| **Mixte** | Méthode, décisions et questions ouvertes valables. Chiffres de résultat périmés, nommés dans le bandeau du document. |
| **Périmé** | Déplacé dans `legacy/`. Corps généré sur le comptage fautif, verdicts dépendants. Aucun chiffre à citer. |

---

## À jour — résultats du 2026-09-08

| Document | Objet | Régénéré par |
|---|---|---|
| [2026-09-08-age-a-la-suppression.md](2026-09-08-age-a-la-suppression.md) | **La référence sur l'âge.** Suppressions par âge en jours (1 à 30), par journée du suivi, contrôles du pic à 7 jours, réconciliation des trois comptages d'avis récents. | [`age_a_la_suppression.py`](../scripts/age_a_la_suppression.py) |
| [2026-09-08-histogramme-age-des-suppressions.md](2026-09-08-histogramme-age-des-suppressions.md) | Les mêmes suppressions en tranches larges (moins d'un mois, 1-3, 3-6, 6-12, plus d'un an), risque par tranche, projections annuelles. Version pour le mail à Axel. | [`histogramme_age_suppressions.py`](../scripts/histogramme_age_suppressions.py) |
| [2026-09-08-cas-attaque-salles-de-sport.md](2026-09-08-cas-attaque-salles-de-sport.md) | Les deux fiches espagnoles attaquées, traitées séparément, avec le tableau des correctifs par rapport au 2026-09-06. | [`cas_attaque_salles_de_sport.py`](../scripts/cas_attaque_salles_de_sport.py) |
| [2026-09-08-note-de-methodo.md](2026-09-08-note-de-methodo.md) | Compte rendu de méthode de la session : définition corrigée d'une suppression, contrôles faits, constructions jetées. | — |
| [2026-09-08-synthese-de-la-journee.md](2026-09-08-synthese-de-la-journee.md) | Résultats validés du 2026-09-08, avec la commande qui régénère chacun. | — |

## À jour — résultats du 2026-09-09, relancés après correction

Régénérés sur le comptage corrigé **et** après dédoublonnage de la table maîtresse. Ils
remplacent les versions de `legacy/`, dont les copies périmées ont été retirées.

| Document | Objet | Régénéré par |
|---|---|---|
| [2026-09-06-analyse-b-quel-avis-tombe.md](2026-09-06-analyse-b-quel-avis-tombe.md) | **Le résultat le plus solide de l'étude.** Quel avis tombe dans une fiche touchée. Ses 26 effets tiennent tous au contrôle de robustesse. | [`analysis_b.py`](../scripts/analysis_b.py) |
| [2026-09-06-test2-debordement-organique.md](2026-09-06-test2-debordement-organique.md) | Test 2, l'angle du livrable. Le stock de plus d'un an meurt davantage dans les fiches à fort afflux récent : ×1,46 et ×1,76. Tient sans les fiches attaquées. La tranche « 10 % et plus » sort non exploitable. | [`test2_debordement.py`](../scripts/test2_debordement.py) |
| [2026-09-06-controle-robustesse.md](2026-09-06-controle-robustesse.md) | Rejeu de A et B sans les fiches attaquées, verdict sur 68 effets : 49 tiennent, 8 non-effets stables, 5 fragiles, 6 ne tiennent pas — les 6 sont tous dans le modèle d'ampleur de A. | [`controle_robustesse.py`](../scripts/controle_robustesse.py) |
| [2026-09-06-analyse-a-quel-etablissement.md](2026-09-06-analyse-a-quel-etablissement.md) | Modèle établissement. **Le premier modèle, « être touché », tient. Le second, l'ampleur de la purge, n'est pas exploitable** : 396 fiches, 6 effets qui changent de sens quand on en retire 4. | [`analysis_a.py`](../scripts/analysis_a.py) |
| [2026-09-06-premiers-resultats-facteur-par-facteur.md](2026-09-06-premiers-resultats-facteur-par-facteur.md) | Tableaux facteur par facteur sur les avis récents, à âge comparable. Seuil « trop peu pour conclure » à 20 disparitions. | [`level1_bivariate.py`](../scripts/level1_bivariate.py) |

**Réserve commune à ces cinq documents.** Leurs tableaux sont régénérés, mais les paragraphes de
récit écrits en dur dans les scripts n'ont pas été relus. Un est marqué dans
`age_a_la_suppression.py` ; les autres n'ont pas été audités. Vérifier une phrase chiffrée dans
le tableau au-dessus d'elle avant de la citer.

## À jour — cadrage et construction du panel

Ces documents ne portent aucun chiffre de résultat, donc la correction du comptage ne les touche
pas.

| Document | Objet |
|---|---|
| [selection-listing.md](selection-listing.md) | Décisions de construction du panel : sources, clustering par groupe, résolution Google, budgets, design du crawl adaptatif. Daté du 3 juillet 2026. |
| [panel-summary.md](panel-summary.md) | Description du panel obtenu : 9 048 fiches, 38 cellules, distribution du nombre d'avis. En anglais. |
| [methodologie.md](methodologie.md) | Note de cadrage : objectif, corpus, hypothèses, features à tester, protocoles des Tests 2 et 3. |
| [plan-de-travail.md](plan-de-travail.md) | Plan d'analyse en trois niveaux, liste des caractéristiques et interactions, arbitrages sur la dépendance et le déséquilibre. |

## Mixte — méthode valable, chiffres périmés

| Document | Ce qui reste utile | Chiffres périmés dedans |
|---|---|---|
| [2026-09-06-trouvailles-et-loups.md](2026-09-06-trouvailles-et-loups.md) | **La seule liste consolidée des 15 vérifications non faites** (L1 à L15), et une colonne de fiabilité qui dit résultat par résultat ce que la correction peut renverser. | 84 % / 24 entreprises / 18 %, 509 sur 5 230, 124 sur 2 853 |
| [2026-09-06-facteurs-et-programme-danalyse.md](2026-09-06-facteurs-et-programme-danalyse.md) | Les décisions de méthode qui tiennent : périmètre à 30 jours, recalcul à âge comparable, niveau Local Guide en trois paliers, liste de ce qui est écarté. | 84 % / 39 fiches, 106 761, 2 853, 2,67 %, 264 sur 816 |
| [2026-09-06-reprise-qualification-des-suppressions.md](2026-09-06-reprise-qualification-des-suppressions.md) | Les sept questions Q1 à Q7 de qualification d'une suppression. Q4, Q5 et Q7 ne sont toujours pas traitées. | 509 sur 5 230, 617 résurrections, cascade 5 314 / 2 705 / 2 853 |
| [2026-09-06-verif-contenu-textuel.md](2026-09-06-verif-contenu-textuel.md) | Le résultat de fond tient : la modération ne porte pas majoritairement sur des fautes visibles. Réserve : le lexique ne couvre que 7 langues sur 41 pays. | dénominateur 2 853, et les 845 sans texte qui en découlent |
| [2026-09-06-verif-reponse-proprietaire.md](2026-09-06-verif-reponse-proprietaire.md) | Le raisonnement qui écarte l'inversion causale : aucune réponse n'est postérieure à la suppression de l'avis. Les délais qui l'étayent (médiane 1 jour, 93 % sous 7 jours) sont calculés sur le périmètre périmé et sont à recalculer. | 1 406 avis avec réponse, dénominateurs du périmètre 2 853 |
| [reviewflowz-analyse-google.md](reviewflowz-analyse-google.md) | Les 13 points de vigilance, dont ceux qui ne bougent pas avec le comptage : filtrage pré-publication invisible, détecteurs IA non fiables, paliers de taille non continus. | 5 230 suppressions, taux 0,11 %, 617 résurrections |
| [reviewflowz-analyse-google-decisions.md](reviewflowz-analyse-google-decisions.md) | Le journal des décisions, et celle qui structure tout : en cas de divergence entre le protocole de cadrage et l'export, les données prévalent. | taux 0,11 % |

## Périmé — dans `legacy/`

**Aucun chiffre de résultat de ce dossier ne doit être cité.** Ces trois documents n'ont pas de
script pour les régénérer : ils resteront périmés. Chacun garde sa méthode et ses pièges
documentés, pas ses nombres. Le dossier contient aussi les copies d'avant correction des cinq
documents relancés le 2026-09-09 ; voir [legacy/README.md](legacy/README.md).

| Document | Ce qui reste utilisable | Régénérable ? |
|---|---|---|
| [legacy/2026-09-06-enquete-fiches-purgees-et-plan.md](legacy/2026-09-06-enquete-fiches-purgees-et-plan.md) | Enquête sur les fiches les plus touchées : 7 artefacts de collecte démasqués par triple preuve, 2 salles de sport attaquées. C'est ce raisonnement qui a fondé la correction. | — |
| [legacy/2026-09-06-synthese-etat-et-resultats.md](legacy/2026-09-06-synthese-etat-et-resultats.md) | Ancienne synthèse générale. Garde la liste « ce qu'il ne faut pas dire à Axel » comme garde-fou de communication. | — |
| [legacy/2026-09-04-reviewflowz-analyse-google-premieres-observations-sur-l-export-vagues-1-14.md](legacy/2026-09-04-reviewflowz-analyse-google-premieres-observations-sur-l-export-vagues-1-14.md) | Premiers comptages bivariés, remplacés dès le 2026-09-06 parce que confondus par l'âge. Garde les quatre pièges du dataset. | — |

## Hors documentation

| Fichier | Objet |
|---|---|
| [../../CLAUDE.md](../../CLAUDE.md) | Instructions de travail : flux plan / relecture, architecture, méthodologie. **Chiffres corrigés le 2026-09-09** : concentration, taux du périmètre frais, codes D1/D2/D3, comptage de référence. Aucune valeur périmée restante. |
| [../../README.md](../../README.md) | Présentation du dépôt, commandes, tables, scripts, vocabulaire. **Réécrit le 2026-09-09** : liens réparés, résultats valides séparés des résultats à relancer, durées non mesurées retirées. |
| [../BACKLOG.md](../BACKLOG.md) | État d'avancement, décisions, table des programmes, réserves à porter au livrable. |
| [../PASSATION.md](../PASSATION.md) | Document de reprise : consignes de rédaction, décisions verrouillées, pièges du jeu de données. |
| [../../BONNES-ET-MAUVAISES-PRATIQUES.md](../../BONNES-ET-MAUVAISES-PRATIQUES.md) | Bonnes pratiques et écueils rencontrés, avec le contrôle qui aurait évité chacun. |

## Doublons connus

Signalés pour qu'on ne les traite pas comme des sources indépendantes :

- `legacy/synthese-etat-et-resultats` et `trouvailles-et-loups` couvrent les mêmes résultats
  avec deux découpages différents.
- `legacy/enquete-fiches-purgees-et-plan` et `reprise-qualification-des-suppressions`
  décrivent les mêmes défauts de comptage.
- `panel-summary` et `selection-listing` décrivent le même panel ; `selection-listing` est plus
  complet et daté.
- `methodologie`, `plan-de-travail` et `reviewflowz-analyse-google` se recouvrent sur les
  features et les prochaines étapes.
- `2026-09-08-age-a-la-suppression` et `2026-09-08-histogramme-age-des-suppressions` portent les
  mêmes suppressions à deux granularités. Le premier fait référence.

## Questions ouvertes

La liste consolidée est dans [2026-09-06-trouvailles-et-loups.md](2026-09-06-trouvailles-et-loups.md),
partie 2 (L1 à L15). Les quatre qui bloquent la reprise :

1. ~~Relancer le Test 2 sur le comptage corrigé.~~ **Fait le 2026-09-09.** Il tient : ×1,46 pour
   les fiches ayant perdu 1 à 3 % de leur stock récent, ×1,76 pour 3 à 10 %, et les deux
   survivent au retrait des fiches attaquées.
2. **Combien d'attaques par avis négatifs dans le panel.** Deux repérées par hasard, le
   balayage systématique n'est pas fait.
3. **Ce qui se joue à 7 jours** : cycle de traitement automatique ou réaction à un signalement.
   Rien ne le tranche dans les données.
4. **Croiser le pic à 7 jours avec les facteurs de l'analyse B** : qui sont les avis qui tombent
   à 7 jours. Candidat direct pour l'angle faux positifs.
