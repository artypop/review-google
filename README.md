# ReviewFlowz — analyse des suppressions d'avis Google

Étude quantitative : quelles caractéristiques d'un avis Google sont associées à sa suppression.
Angle du livrable : les faux positifs.

Le projet a deux volets, dans deux dossiers séparés :

- **`etude-exploratoire/`** — l'étude d'origine, en DuckDB sur les fichiers parquet en local. Ce
  README la décrit en détail ci-dessous. Ses résultats chiffrés sont invalidés (voir son
  `BACKLOG.md`) ; sa méthodologie reste une référence.
- **`logistic-regression-study/`** — la table de panel pour la régression logistique, construite
  en BigQuery. Voir `logistic-regression-study/sql/` et `logistic-regression-study/BACKLOG.md`.

**Pour comprendre les résultats de l'étude d'origine, lire d'abord** [`etude-exploratoire/documentations/2026-09-06-facteurs-et-programme-danalyse.md`](etude-exploratoire/documentations/2026-09-06-facteurs-et-programme-danalyse.md).
**Pour son état d'avancement**, [`etude-exploratoire/BACKLOG.md`](etude-exploratoire/BACKLOG.md).

---

## Démarrer

Prérequis : [uv](https://docs.astral.sh/uv/). Rien d'autre à installer, `uv` s'occupe de Python
et des dépendances à la première commande.

Les données ne sont pas dans le dépôt (872 Mo et données personnelles). Il faut
`data/exports/exports/*.parquet` en place — voir « Les données » plus bas.

```bash
uv run etude-exploratoire/scripts/build_tables.py      # ~20 s, construit les tables d'analyse
uv run etude-exploratoire/scripts/level1_bivariate.py  # ~5 s, produit les résultats facteur par facteur
uv run etude-exploratoire/scripts/query.py --tables    # vérifier que tout est là
```

---

## Regarder les données soi-même

Deux façons, selon qu'on veut une réponse chiffrée ou explorer visuellement.

**Pour une question précise : `etude-exploratoire/scripts/query.py`.** Il ouvre les tables et exécute du SQL, sans
rien installer ni écrire de code.

**Pour explorer à la souris : `etude-exploratoire/explore.py`**, à la racine de ce dossier. Ouvrir le fichier dans VS Code,
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

### Les trois tables

| Nom | Lignes | Une ligne = |
|---|---:|---|
| `avis` | 4 878 151 | un avis. **Corpus entier**, colonne `is_fresh` pour les avis de moins de 30 jours |
| `etablissements` | 9 048 | un établissement, avec vélocité, intensité de purge, note et trajectoire |
| `suivi` | 1 137 276 | un avis **frais** observé à un passage du robot. `died` = il a disparu à ce passage |

Les fichiers d'origine restent accessibles sous `reviews_brut`, `businesses_brut`,
`histograms_brut`, `waves_brut`, si besoin de revenir à la source.

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

## Les résultats déjà produits

| Fichier | Contenu |
|---|---|
| [`etude-exploratoire/documentations/2026-09-06-premiers-resultats-facteur-par-facteur.md`](etude-exploratoire/documentations/2026-09-06-premiers-resultats-facteur-par-facteur.md) | Les 15 facteurs, avec le mode d'emploi des chiffres |
| [`etude-exploratoire/documentations/2026-09-06-analyse-a-quel-etablissement.md`](etude-exploratoire/documentations/2026-09-06-analyse-a-quel-etablissement.md) | Quel établissement subit une intervention |
| [`etude-exploratoire/documentations/2026-09-06-analyse-b-quel-avis-tombe.md`](etude-exploratoire/documentations/2026-09-06-analyse-b-quel-avis-tombe.md) | Dans une fiche touchée, quel avis tombe |
| [`etude-exploratoire/documentations/2026-09-06-controle-robustesse.md`](etude-exploratoire/documentations/2026-09-06-controle-robustesse.md) | A et B rejouées sans les 24 fiches purgées |
| [`etude-exploratoire/documentations/2026-09-06-verif-contenu-textuel.md`](etude-exploratoire/documentations/2026-09-06-verif-contenu-textuel.md) | **93,7 % des avis supprimés ne portent aucune faute visible** |
| [`etude-exploratoire/documentations/2026-09-06-test2-debordement-organique.md`](etude-exploratoire/documentations/2026-09-06-test2-debordement-organique.md) | **Le chiffre du livrable** : le stock ancien meurt 1,5 à 1,7× plus dans les fiches à fort afflux |
| `data/resultats/*.csv` | Les mêmes chiffres, pour Excel |

Le CSV contient, pour chaque facteur et chaque modalité : le nombre d'observations, le nombre de
disparitions, le risque brut et le risque à âge comparable. C'est cette dernière colonne qu'il
faut lire — voir l'explication dans la note.

---

## Les scripts

Tous dans `etude-exploratoire/scripts/`.

| Script | Ce qu'il fait | Sortie | Durée |
|---|---|---|---|
| `build_tables.py` | Lit l'export d'origine, calcule les caractéristiques, écrit les trois tables. Dix contrôles de cohérence en fin d'exécution. | `data/build/*.parquet` | 20 s |
| `level1_bivariate.py` | Risque de suppression facteur par facteur, à âge comparable, avec et sans les fiches purgées. | Note + CSV | 10 s |
| `analysis_b.py` | Compare les avis d'une même fiche le même jour. `--bootstrap N` pour les marges d'erreur. | Note + CSV | 2 min ; **compter ~2 min par tirage de bootstrap** (30 tirages ≈ 1 h, 200 ≈ 7 h) |
| `controle_robustesse.py` | Rejoue A et B sans les 24 fiches massivement purgées et met les coefficients côte à côte. | Note + CSV | ~7 min |
| `verif_texte.py` | Onze marqueurs textuels (insultes, spam, charabia…) : la suppression a-t-elle une cause visible ? | Note + CSV | ~2 min |
| `test2_debordement.py` | Le stock ancien meurt-il plus dans les fiches à fort afflux récent ? | Note + CSV | ~1 min |
| `machine_learning.py` | Contrôle par forêt aléatoire et gradient boosting : reste-t-il un signal non repéré ? | Note + CSV | ~15 min |
| `query.py` | Interroge les tables en SQL. Ne modifie rien. | Écran ou CSV | immédiat |

Tous sont **rejouables sans risque** : ils réécrivent leurs sorties à chaque exécution.

Les scripts qui écrivent une note ne réécrivent que la partie comprise entre des marqueurs
`<!-- genere:... -->`. Le texte d'analyse rédigé autour survit à une régénération.

### Les calculs longs

`analysis_b.py --bootstrap` et `machine_learning.py` prennent du temps. Les lancer détachés du
terminal, pour qu'un plantage de l'éditeur ne les emporte pas :

```bash
setsid nohup uv run etude-exploratoire/scripts/analysis_b.py --bootstrap 30 \
  > data/resultats/analyse_b_run.log 2>&1 < /dev/null &
```

**Attention à la mémoire** : la machine de travail est passée de 7 à 16 Go le 2026-09-06. Le
noyau avait tué un lancement du machine learning sous l'ancienne configuration. Le plafond
DuckDB reste posé à 1-2 Go dans chaque script, et la règle tient : pas plus de deux calculs
lourds en même temps, `free -m` avant de lancer.

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

Trois termes reviennent partout.

**Avis frais** — publié depuis moins de 30 jours. C'est le périmètre de l'analyse, parce que le
risque de suppression s'effondre au-delà : divisé par 15 à un mois, par 156 à un an.

**Risque par passage** — sur 1 000 avis en ligne, combien ont disparu au passage suivant du
robot. Ce n'est pas la probabilité qu'un avis finisse supprimé, qui s'accumule sur plusieurs
jours et est bien plus élevée.

**À âge comparable** — un chiffre recalculé tranche d'âge par tranche d'âge, puis recombiné comme
si tous les groupes comparés avaient la même répartition d'âge. Indispensable ici : l'âge pèse
plus que tout le reste, et une comparaison qui l'ignore mesure surtout une différence d'âge.
