# Index de la documentation — étude exploratoire

Établi le 2026-09-08, après la correction du comptage des suppressions.

**Comptage de référence : 5 230 disparitions brutes -> 4 747 suppressions retenues.** Définition
dans [`../scripts/suppressions_corrigees.py`](../scripts/suppressions_corrigees.py), qui
réimplémente en DuckDB la logique de
[`../../logistic-regression-study/sql/01_build_avis_deleted_panel.sql`](../../logistic-regression-study/sql/01_build_avis_deleted_panel.sql).

Trois statuts :

| Statut | Ce que ça veut dire |
|---|---|
| **À jour** | Aucun chiffre périmé. Citable tel quel. |
| **Mixte** | Méthode, décisions et questions ouvertes valables. Chiffres de résultat périmés, nommés dans le bandeau du document. |
| **Périmé** | Déplacé dans `to-update/`. Corps généré sur le comptage fautif, verdicts dépendants. Aucun chiffre à citer. |

---

## À jour — résultats du 2026-09-08

| Document | Objet | Régénéré par |
|---|---|---|
| [2026-09-08-age-a-la-suppression.md](2026-09-08-age-a-la-suppression.md) | **La référence sur l'âge.** Suppressions par âge en jours (1 à 30), par journée du suivi, contrôles du pic à 7 jours, réconciliation des trois comptages d'avis récents. | [`age_a_la_suppression.py`](../scripts/age_a_la_suppression.py) |
| [2026-09-08-histogramme-age-des-suppressions.md](2026-09-08-histogramme-age-des-suppressions.md) | Les mêmes suppressions en tranches larges (moins d'un mois, 1-3, 3-6, 6-12, plus d'un an), risque par tranche, projections annuelles. Version pour le mail à Axel. | [`histogramme_age_suppressions.py`](../scripts/histogramme_age_suppressions.py) |
| [2026-09-08-cas-attaque-salles-de-sport.md](2026-09-08-cas-attaque-salles-de-sport.md) | Les deux fiches espagnoles attaquées, traitées séparément, avec le tableau des correctifs par rapport au 2026-09-06. | [`cas_attaque_salles_de_sport.py`](../scripts/cas_attaque_salles_de_sport.py) |
| [2026-09-08-note-de-methodo.md](2026-09-08-note-de-methodo.md) | Compte rendu de méthode de la session : définition corrigée d'une suppression, contrôles faits, constructions jetées. | — |
| [2026-09-08-synthese-de-la-journee.md](2026-09-08-synthese-de-la-journee.md) | Résultats validés du 2026-09-08, avec la commande qui régénère chacun. | — |

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

## Périmé — dans `to-update/`

Résultats à relancer sur le comptage corrigé. Chaque document garde sa méthode et ses pièges
documentés ; seuls ses chiffres tombent.

| Document | Objet | À relancer avec |
|---|---|---|
| [to-update/2026-09-06-analyse-a-quel-etablissement.md](to-update/2026-09-06-analyse-a-quel-etablissement.md) | Modèle établissement : qui est touché, et quelle ampleur de purge une fois touché. Piège central documenté : la vitesse de collecte mesurait une exposition, pas une sanction. | [`analysis_a.py`](../scripts/analysis_a.py) |
| [to-update/2026-09-06-analyse-b-quel-avis-tombe.md](to-update/2026-09-06-analyse-b-quel-avis-tombe.md) | Modèle intra-fiche : quel avis tombe dans un établissement touché, à fiche et jour identiques. | [`analysis_b.py`](../scripts/analysis_b.py) |
| [to-update/2026-09-06-controle-robustesse.md](to-update/2026-09-06-controle-robustesse.md) | Rejeu de A et B sans les fiches massivement purgées, verdict sur 68 effets. Le critère de verdict, fixé avant de regarder les chiffres, reste utilisable. | [`controle_robustesse.py`](../scripts/controle_robustesse.py) |
| [to-update/2026-09-06-premiers-resultats-facteur-par-facteur.md](to-update/2026-09-06-premiers-resultats-facteur-par-facteur.md) | Tableaux facteur par facteur sur les avis récents, à âge comparable. Grille de lecture toujours bonne : seuil « trop peu pour conclure » à 20 disparitions. | [`level1_bivariate.py`](../scripts/level1_bivariate.py) |
| [to-update/2026-09-06-test2-debordement-organique.md](to-update/2026-09-06-test2-debordement-organique.md) | Test 2 : le vieux stock meurt-il davantage dans les fiches à fort afflux récent. **Portait l'angle du livrable, à refaire en priorité.** | [`test2_debordement.py`](../scripts/test2_debordement.py) |
| [to-update/2026-09-06-enquete-fiches-purgees-et-plan.md](to-update/2026-09-06-enquete-fiches-purgees-et-plan.md) | Enquête sur les fiches les plus touchées : 7 artefacts de collecte démasqués par triple preuve, 2 salles de sport attaquées. C'est ce raisonnement qui a fondé la correction. | — |
| [to-update/2026-09-06-synthese-etat-et-resultats.md](to-update/2026-09-06-synthese-etat-et-resultats.md) | Ancienne synthèse générale. Garde la liste « ce qu'il ne faut pas dire à Axel » comme garde-fou de communication. | — |
| [to-update/2026-09-04-reviewflowz-analyse-google-premieres-observations-sur-l-export-vagues-1-14.md](to-update/2026-09-04-reviewflowz-analyse-google-premieres-observations-sur-l-export-vagues-1-14.md) | Premiers comptages bivariés, remplacés dès le 2026-09-06 parce que confondus par l'âge. Garde les quatre pièges du dataset. | — |

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

- `to-update/synthese-etat-et-resultats` et `trouvailles-et-loups` couvrent les mêmes résultats
  avec deux découpages différents.
- `to-update/enquete-fiches-purgees-et-plan` et `reprise-qualification-des-suppressions`
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

1. **Relancer le Test 2** sur le comptage corrigé. Il portait l'angle du livrable et c'est le
   résultat le plus exposé à l'erreur, puisqu'il mesure la mortalité des vieux avis.
2. **Combien d'attaques par avis négatifs dans le panel.** Deux repérées par hasard, le
   balayage systématique n'est pas fait.
3. **Ce qui se joue à 7 jours** : cycle de traitement automatique ou réaction à un signalement.
   Rien ne le tranche dans les données.
4. **Croiser le pic à 7 jours avec les facteurs de l'analyse B** : qui sont les avis qui tombent
   à 7 jours. Candidat direct pour l'angle faux positifs.
