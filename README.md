# ReviewFlowz — analyse des suppressions d'avis Google

Étude quantitative : quelles caractéristiques d'un avis Google sont associées à sa suppression.
Angle du livrable : les faux positifs.

Le projet a deux volets, dans deux dossiers séparés :

- **`etude-exploratoire/`** — l'étude d'origine, en DuckDB sur les fichiers parquet en local. Ce
  README la décrit en détail ci-dessous.
- **`logistic-regression-study/`** — la table de panel pour la régression logistique, construite
  en BigQuery. Voir `logistic-regression-study/sql/` et `logistic-regression-study/BACKLOG.md`.

## État au 2026-09-09

Le comptage des suppressions a été corrigé le 2026-09-08, puis la table maîtresse dédoublonnée
le 2026-09-09 : **5 230 lignes de disparition, portées par 5 109 avis distincts, -> 4 747
suppressions retenues en DuckDB** (4 737 en BigQuery, voir `CLAUDE.md` point 4), après retrait
des ratés de collecte et de 24 bugs d'édition. Le 5 230 compte des événements, le 4 747 compte
des avis.
Définition dans
[`etude-exploratoire/scripts/suppressions_corrigees.py`](etude-exploratoire/scripts/suppressions_corrigees.py),
seule copie hors BigQuery.

**Les analyses A et B, le contrôle de robustesse, le Test 2 et le facteur par facteur ont été
relancés le 2026-09-09** sur le comptage corrigé et la table dédoublonnée. Leurs notes sont
revenues dans `etude-exploratoire/documentations/`. Trois documents restent périmés dans
`legacy/`, ceux qui n'ont pas de script pour les régénérer : aucun de leurs chiffres de
résultat ne doit être cité.

Réserve sur les cinq notes relancées : leurs tableaux sont régénérés, mais les paragraphes de
récit écrits en dur dans les scripts n'ont pas été relus. Vérifier une phrase chiffrée dans le
tableau au-dessus d'elle avant de la citer.

**Trois points d'entrée, dans cet ordre :**

1. [`etude-exploratoire/documentations/INDEX.md`](etude-exploratoire/documentations/INDEX.md) —
   inventaire des 24 documents, chacun avec son statut : à jour, mixte, périmé.
2. [`etude-exploratoire/documentations/2026-09-08-synthese-de-la-journee.md`](etude-exploratoire/documentations/2026-09-08-synthese-de-la-journee.md) —
   les résultats valides, avec la commande qui régénère chacun.
3. [`BONNES-ET-MAUVAISES-PRATIQUES.md`](BONNES-ET-MAUVAISES-PRATIQUES.md) — les écueils déjà
   rencontrés et le contrôle qui aurait évité chacun. À lire avant de produire un chiffre.

État d'avancement et prochaines étapes :
[`etude-exploratoire/BACKLOG.md`](etude-exploratoire/BACKLOG.md).

---

## Démarrer

Prérequis : [uv](https://docs.astral.sh/uv/). Rien d'autre à installer, `uv` s'occupe de Python
et des dépendances à la première commande.

Les données ne sont pas dans le dépôt (838 Mo d'export, dont 834 Mo pour `reviews.parquet` seul, et données personnelles). Il faut
`data/exports/exports/*.parquet` en place — voir « Les données » plus bas.

Les scripts qui tournent sur le comptage corrigé n'ont besoin d'aucune table intermédiaire, ils
lisent les parquet directement :

```bash
nice -n 19 .venv/bin/python etude-exploratoire/scripts/age_a_la_suppression.py
nice -n 19 .venv/bin/python etude-exploratoire/scripts/histogramme_age_suppressions.py
nice -n 19 .venv/bin/python etude-exploratoire/scripts/cas_attaque_salles_de_sport.py
```

Les scripts de l'étude d'origine passent par trois tables intermédiaires, construites par
`build_tables.py`. **Ces tables reposent sur le comptage d'avant correction** : elles restent
utilisables pour explorer, pas pour produire un résultat.

```bash
uv run etude-exploratoire/scripts/build_tables.py      # ~20 s, construit les tables d'analyse
uv run etude-exploratoire/scripts/query.py --tables    # vérifier que tout est là
```

---

## Regarder les données soi-même

Deux façons, selon qu'on veut une réponse chiffrée ou explorer visuellement.

**Pour une question précise : `etude-exploratoire/scripts/query.py`.** Il ouvre les tables et exécute du SQL, sans
rien installer ni écrire de code.

**Pour explorer à la souris : `etude-exploratoire/explore.py`.** Ouvrir le fichier dans VS Code,
exécuter les cellules `# %%` avec `Shift+Entrée`, puis cliquer sur l'icône Data Wrangler à côté
du DataFrame dans le panneau Variables. Les cellules chargent des extraits ciblés — Data
Wrangler ne suit pas sur les 4,88 millions de lignes du corpus complet.

```bash
# qu'est-ce qui existe
uv run etude-exploratoire/scripts/query.py --tables
uv run etude-exploratoire/scripts/query.py --colonnes avis

# des questions déjà écrites, pour démarrer
uv run etude-exploratoire/scripts/query.py --exemples
uv run etude-exploratoire/scripts/query.py --exemple age
uv run etude-exploratoire/scripts/query.py --exemple rafale

# sa propre question
uv run etude-exploratoire/scripts/query.py "SELECT star, count(*) FROM avis WHERE is_fresh GROUP BY 1 ORDER BY 1"

# sortir un CSV ouvrable dans Excel (séparateur ; et virgule décimale)
uv run etude-exploratoire/scripts/query.py "SELECT ..." --csv data/resultats/ma_question.csv

# console : on tape du SQL ligne à ligne, « quit » pour sortir
uv run etude-exploratoire/scripts/query.py
```

Le champ `deleted` de ces tables vient du comptage d'avant correction. Pour compter des
suppressions, importer `suppressions_corrigees.py` plutôt qu'utiliser ce champ.

### Les trois tables

| Nom | Lignes | Une ligne = |
|---|---:|---|
| `avis` | 4 878 151 | une ligne de base de l'export. **Corpus entier**, colonne `is_fresh` pour les avis de moins de 30 jours. `review_id` n'y est pas unique : 4 878 151 lignes pour 4 877 534 avis distincts, l'écart venant des avis disparus puis revenus |
| `etablissements` | 9 048 | un établissement, avec vélocité, intensité de purge, note et trajectoire |
| `suivi` | 1 137 276 | un avis **frais** observé à un passage du robot. `died` = il a disparu à ce passage |

Les fichiers d'origine restent accessibles sous `reviews_brut`, `businesses_brut`,
`histograms_brut`, `waves_brut`, si besoin de revenir à la source.

Réserve sur `suivi` : son périmètre « frais » retenait tout avis vu pour la première fois pendant
le suivi, ce qui y a fait entrer 819 avis de plus de 30 jours, dont 588 de plus d'un an.

### Pourquoi trois tables et pas une

- `avis` répond aux questions du type « combien d'avis 5 étoiles, et combien ont sauté ».
- `etablissements` sert à l'analyse A : quelle entreprise se fait taper.
- `suivi` sert à l'analyse B et à tout ce qui touche au temps. Un avis publié la veille du dernier
  passage n'a été observé qu'une fois ; un avis présent depuis le début l'a été treize fois.
  Compter les deux pareil fausse tout. Dans `suivi`, chaque avis compte pour le nombre de fois où
  il a réellement été vérifié.

**Règle pratique** : pour un simple comptage, utiliser `avis`. Dès qu'on parle de risque ou de
délai, utiliser `suivi`.

---

## Les résultats valides

Tous calculés sur le comptage corrigé. Détail et contrôles dans
[la synthèse](etude-exploratoire/documentations/2026-09-08-synthese-de-la-journee.md).

| Fichier | Contenu |
|---|---|
| [`2026-09-08-age-a-la-suppression.md`](etude-exploratoire/documentations/2026-09-08-age-a-la-suppression.md) | **La référence sur l'âge.** Suppressions par âge en jours et par journée du suivi, contrôles du pic, réconciliation des trois comptages d'avis récents |
| [`2026-09-08-histogramme-age-des-suppressions.md`](etude-exploratoire/documentations/2026-09-08-histogramme-age-des-suppressions.md) | Les mêmes suppressions en tranches larges, risque par tranche, projections annuelles |
| [`2026-09-08-cas-attaque-salles-de-sport.md`](etude-exploratoire/documentations/2026-09-08-cas-attaque-salles-de-sport.md) | Les deux fiches espagnoles attaquées, traitées séparément |
| [`2026-09-08-note-de-methodo.md`](etude-exploratoire/documentations/2026-09-08-note-de-methodo.md) | Ce qui a été fait, ce qui a été jeté, les contrôles à ne pas refaire |
| `data/resultats/*.csv` | Les mêmes chiffres, pour Excel |

Les deux résultats les plus nets :

- **Le pic de suppression tombe au septième jour de vie de l'avis** : 449 suppressions à
  7 jours, contre 279 à 6 jours et 118 à 8 jours. Ces nombres bruts se comparent directement
  parce que l'exposition est quasi identique — environ 32 000 avis observés à chaque âge de 2 à
  30 jours. Vérifié comme un effet d'âge et non une purge : étalé sur 12 des 13 journées du
  suivi et sur 144 établissements, et il survit au retrait des deux journées les plus chargées.
- **51,6 % des 4 747 suppressions frappent un avis de moins d'un mois, 30,3 % un avis de plus
  d'un an.** Le vieux stock pèse par son volume : 4,1 millions d'avis, contre 101 000 à moins
  d'un mois. Son risque par passage est cent fois plus faible — 0,0027 % sur 53 708 075
  observations d'avis de plus d'un an, contre 0,2699 % sur 907 588 observations d'avis de moins
  d'un mois.

## Les résultats relancés le 2026-09-09

Régénérés sur le comptage corrigé et la table dédoublonnée. Revenus dans
`etude-exploratoire/documentations/`.

| Fichier | Contenu | Régénéré par |
|---|---|---|
| [`2026-09-06-analyse-b-quel-avis-tombe.md`](etude-exploratoire/documentations/2026-09-06-analyse-b-quel-avis-tombe.md) | **Le résultat le plus solide.** Quel avis tombe dans une fiche touchée. Ses 26 effets tiennent tous au contrôle de robustesse | `analysis_b.py` |
| [`2026-09-06-test2-debordement-organique.md`](etude-exploratoire/documentations/2026-09-06-test2-debordement-organique.md) | **L'angle du livrable.** Le stock de plus d'un an meurt davantage dans les fiches à fort afflux récent : ×1,46 et ×1,76 | `test2_debordement.py` |
| [`2026-09-06-controle-robustesse.md`](etude-exploratoire/documentations/2026-09-06-controle-robustesse.md) | A et B rejouées sans les fiches attaquées. 49 effets tiennent sur 68 ; les 6 qui ne tiennent pas sont tous dans le modèle d'ampleur de A | `controle_robustesse.py` |
| [`2026-09-06-analyse-a-quel-etablissement.md`](etude-exploratoire/documentations/2026-09-06-analyse-a-quel-etablissement.md) | Quel établissement subit une intervention. **Son second modèle, l'ampleur de la purge, n'est pas exploitable** | `analysis_a.py` |
| [`2026-09-06-premiers-resultats-facteur-par-facteur.md`](etude-exploratoire/documentations/2026-09-06-premiers-resultats-facteur-par-facteur.md) | Les 15 facteurs, avec le mode d'emploi des chiffres | `level1_bivariate.py` |

## Les résultats encore périmés

`legacy/` garde trois documents sans script associé : l'enquête sur les fiches purgées —
c'est le raisonnement qui a fondé la correction du comptage —, l'ancienne synthèse générale, qui
garde la liste « ce qu'il ne faut pas dire à Axel », et les premières observations du
2026-09-04. Voir
[`INDEX.md`](etude-exploratoire/documentations/INDEX.md).

Le CSV de `level1_bivariate.py` contient, pour chaque facteur et chaque modalité : le nombre
d'observations, le nombre de disparitions, le risque brut et le risque à âge comparable. C'est
cette dernière colonne qu'il faut lire — voir l'explication dans la note.

Un résultat reste à recalculer sans être déplacé :
[`2026-09-06-verif-contenu-textuel.md`](etude-exploratoire/documentations/2026-09-06-verif-contenu-textuel.md)
conclut que la modération ne porte pas majoritairement sur des fautes visibles. La conclusion
tient, ses pourcentages sont calculés sur l'ancien dénominateur.

---

## Les scripts

Tous dans `etude-exploratoire/scripts/`.

### Sur le comptage corrigé

| Script | Ce qu'il fait | Sortie | Durée |
|---|---|---|---|
| `suppressions_corrigees.py` | Module partagé : la définition d'une suppression, la vue `avis` (une ligne par avis, `death_at` corrigé) et ses vues intermédiaires. `vue_panel()` ajoute la vue d'exposition `panel` à la demande. Importé par les autres, ne se lance pas seul. | — | — |
| `age_a_la_suppression.py` | Suppressions par âge en jours et par journée du suivi, contrôles du pic. `--age-max` règle le dernier âge. | Note + CSV | — |
| `histogramme_age_suppressions.py` | Les mêmes en tranches larges, risque par tranche, projections. | Note + CSV | — |
| `cas_attaque_salles_de_sport.py` | Le cas des deux fiches espagnoles, fiche par fiche. | Note | — |

### De l'étude d'origine

Ces scripts tournent, mais sur le comptage d'avant correction. Ils sont à reprendre pour
importer `suppressions_corrigees.py`.

| Script | Ce qu'il fait | Sortie | Durée |
|---|---|---|---|
| `build_tables.py` | Lit l'export, calcule les caractéristiques, écrit les trois tables. Dix contrôles de cohérence en fin d'exécution. | `data/build/*.parquet` | 20 s |
| `level1_bivariate.py` | Risque de suppression facteur par facteur, à âge comparable, avec et sans les fiches purgées. | Note + CSV | 10 s |
| `analysis_a.py` | Quel établissement subit une intervention, et de quelle ampleur. | Note + CSV | 2 min |
| `analysis_b.py` | Compare les avis d'une même fiche le même jour. `--bootstrap N` pour les marges d'erreur. | Note + CSV | 2 min ; **compter ~2 min par tirage de bootstrap** (30 tirages ≈ 1 h, 200 ≈ 7 h) |
| `controle_robustesse.py` | Rejoue A et B sans les fiches massivement purgées et met les coefficients côte à côte. | Note + CSV | ~7 min |
| `verif_texte.py` | Onze marqueurs textuels (insultes, spam, charabia…) : la suppression a-t-elle une cause visible ? | Note + CSV | ~2 min |
| `verif_reponse_proprietaire.py` | Ordre entre la réponse du propriétaire et la suppression. | Note + CSV | — |
| `test2_debordement.py` | Le stock ancien meurt-il plus dans les fiches à fort afflux récent ? | Note + CSV | ~1 min |
| `machine_learning.py` | Contrôle par forêt aléatoire et gradient boosting : reste-t-il un signal non repéré ? | Note + CSV | — (jamais relancé depuis le passage à 16 Go) |
| `fiches_urls.py` | Produit les URL Google des fiches à inspecter à la main. | CSV | immédiat |
| `query.py` | Interroge les tables en SQL. Ne modifie rien. | Écran ou CSV | immédiat |

Les scripts réécrivent leurs sorties à chaque exécution, sans effet de bord.

**Les scripts de l'étude d'origine se lancent depuis `etude-exploratoire/`, pas depuis la
racine.** Ils écrivent dans `documentations/<nom>.md` et lisent dans `data/`, deux chemins
relatifs au répertoire courant. Comme `data/` est à la racine du dépôt, il faut un lien :
`ln -sfn ../data etude-exploratoire/data`, puis lancer depuis `etude-exploratoire/`. Sans ce
lien, les calculs tournent depuis la racine mais l'écriture de la note échoue.

Ces huit scripts ne réécrivent que la partie de leur note comprise entre des marqueurs
`<!-- genere:... -->`, donc le texte d'analyse rédigé autour survit à une régénération. Les trois
scripts du 2026-09-08 réécrivent leur note entière : tout leur texte est dans le script.

### Les calculs longs

`analysis_b.py --bootstrap` et `machine_learning.py` prennent du temps. Les lancer détachés du
terminal, pour qu'un plantage de l'éditeur ne les emporte pas :

```bash
setsid nohup uv run etude-exploratoire/scripts/analysis_b.py --bootstrap 30 \
  > data/resultats/analyse_b_run.log 2>&1 < /dev/null &
```

**Attention à la mémoire.** La machine de travail est passée de 7 à 16 Go le 2026-09-06 ;
`machine_learning.py` saturait la machine quand elle en avait 7.

Le plafond DuckDB vaut 1 Go dans `analysis_a`, `analysis_b`, `level1_bivariate` et
`machine_learning`, 2 Go dans `query`, `test2_debordement`, `verif_texte` et
`verif_reponse_proprietaire`, et 6 Go dans `suppressions_corrigees` — donc dans les trois
scripts du 2026-09-08. **`build_tables.py` et `fiches_urls.py` n'en posent aucun, à corriger.**

Règles de lancement : pas plus de deux calculs lourds en même temps, `free -m` avant de lancer,
`nice -n 19` au-delà de deux minutes.

---

## Les données

Non versionnées, `data/` est dans le `.gitignore`. Le README de l'export interdit la
rediffusion : `reviewer_name`, `review_link` et `text` identifient des personnes.

```
data/
  exports/exports/*.parquet   l'export d'origine, 14 passages du 11 au 24 août 2026
  build/*.parquet             les tables d'analyse, régénérables
  resultats/*.csv             les sorties chiffrées
  verif_*.csv                 les échantillons de vérification manuelle
```

Les tables construites ne contiennent **ni nom, ni lien, ni texte d'avis** : l'auteur y est
réduit à un identifiant anonymisé, le texte à sa longueur. Elles sont donc manipulables sans
précaution particulière. Ce n'est pas le cas des fichiers `reviews_brut`.

---

## Vocabulaire

**Avis frais** — publié depuis moins de 30 jours. C'est le périmètre de la modélisation, parce
que le risque de suppression s'effondre au-delà : 0,2699 % par passage sur 907 588 observations
d'avis de moins d'un mois, contre 0,0027 % sur 53 708 075 observations d'avis de plus d'un an,
soit cent fois moins.

**Trois comptages d'avis récents supprimés coexistent**, tous justes, parce que l'âge peut se
compter à trois moments différents. À citer avec leur code, jamais avec le seul chiffre :

| Code | Définition | Suppressions |
|---|---|---:|
| **D1** | âge à la suppression strictement inférieur à 30 jours | 2 450 |
| **D2** | âge à la suppression de 30 jours ou moins | 2 462 |
| **D3** | avis de 30 jours ou moins au 11 août, supprimé à n'importe quel moment | 2 540 |

**Risque par passage** — sur 1 000 avis en ligne, combien ont disparu au passage suivant du
robot. Les passages étant quotidiens, un risque par passage est un risque par jour ; ce README
n'emploie que « par passage ». Ce n'est pas la probabilité qu'un avis finisse supprimé, qui
s'accumule sur plusieurs jours et est bien plus élevée.

**Observation** — un avis constaté en ligne à un passage du robot. C'est l'unité de la table
`suivi` et de la vue `panel` de `suppressions_corrigees.py` : le même objet sous deux noms selon
le script.

**À âge comparable** — un chiffre recalculé tranche d'âge par tranche d'âge, puis recombiné comme
si tous les groupes comparés avaient la même répartition d'âge. Indispensable ici : l'âge pèse
plus que tout le reste, et une comparaison qui l'ignore mesure surtout une différence d'âge.
