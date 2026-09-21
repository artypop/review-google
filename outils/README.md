# Travailler sur une copie locale des tables

Ce dossier tire les tables de BigQuery vers `data/bigquery/` et les ouvre dans
DuckDB. Le SQL se fait alors en local, sans appel facturé et sans attente.

**La règle du projet ne change pas** : le panel se construit dans BigQuery, par
`sql/01_selection_panel.sql` et `sql/02_adding_features.sql`. Ce dossier
descend le résultat tel quel. Aucune caractéristique n'est recalculée ici.

---

## Mise en route

Prérequis, une seule fois :

```bash
gcloud auth application-default login
gcloud auth application-default set-quota-project client-divers
uv sync
```

Le compte a besoin de lire le dataset : `roles/bigquery.jobUser` sur le projet
et `roles/bigquery.dataViewer` sur `reviewflowz`. La lecture suffit, les
scripts n'écrivent rien dans BigQuery.

```bash
python outils/tirer_tables.py reviews_panel_features businesses
python outils/controle_copie_locale.py
```

Le contrôle doit finir sur « Copie locale fidèle ». Sinon, aucun chiffre local
ne vaut tant que l'écart n'est pas expliqué.

---

## Les trois fichiers

| | |
|---|---|
| `local.py` | ouvre DuckDB sur les copies, expose chaque parquet comme une vue |
| `tirer_tables.py` | descend une table de BigQuery en parquet, en flux |
| `controle_copie_locale.py` | vérifie que la copie dit la même chose que BigQuery |

`python outils/local.py` liste ce qui est descendu.

---

## Le fuseau horaire

**C'est le piège du travail en local, et il est silencieux.** BigQuery convertit
un TIMESTAMP en date sur UTC. DuckDB utilise le fuseau de la session,
Europe/Paris sur nos machines. Un avis déposé le 12 mai à 23 h UTC devient un
avis du 13 mai en heure de Paris, et entre dans un corpus borné au 13 mai.

Mesuré le 2026-09-15 en rejouant `sql/01` sur la copie de `reviews` :

| | Avis | Suppressions |
|---|---:|---:|
| sans `SET TimeZone='UTC'` | 225 807 | 2 589 |
| avec | 225 757 | 2 595 |

202 avis entraient par la borne basse, 152 sortaient par la borne haute. Les
deux résultats paraissent corrects et un seul l'est.

`connexion()` pose le fuseau. Toute connexion DuckDB ouverte ailleurs le perd.

---

## Ce qui est tirable

| Table | Lignes | Parquet | Données personnelles |
|---|---:|---:|---|
| `reviews` | 4 880 163 | 1 025 Mo | oui — texte, nom d'auteur, lien de profil |
| `avis_features` | 4 877 534 | 166 Mo | non |
| `reviews_panel_features` | 225 757 | 15 Mo | non |
| `reviews_panel_selection` | 225 757 | — | oui |
| `businesses` | 9 048 | 0,5 Mo | non |
| `avis_panel_final` | 63 148 730 | — | oui — ancien panel, abandonné le 2026-09-13 |

`data/` est couvert par `.gitignore`. Le texte des avis, les noms d'auteurs et
les liens de profil ne doivent jamais entrer dans un fichier versionné.

Le tirage de `reviews` prend 19 minutes et coûte environ 0,003 $. Une fois
descendue, une requête dessus ne coûte plus rien.
