# ReviewFlowz — quels avis Google se font supprimer

Google supprime une partie des avis déposés sur les fiches Google Maps. Les commerçants le
constatent sans comprendre ce qui déclenche ces retraits.

**Cette étude cherche à déterminer quelles caractéristiques d'un avis font qu'il est supprimé** :
la note, le texte, le profil de l'auteur, le secteur du commerce, le moment du dépôt.

Commanditaire : Axel, ReviewFlowz. Suivi et validation : Romain et les personnes qui
travaillent sur l'étude.

---

## Par où commencer

| Vous voulez savoir | Lisez |
|---|---|
| **tout le projet en une lecture, si vous arrivez** | [docs/00-brief-equipe.md](docs/00-brief-equipe.md) |
| ce qu'on cherche, sur quelles données, avec quelles règles | [docs/01-etude.md](docs/01-etude.md) |
| d'où viennent les données et ce qu'elles cachent | [docs/02-donnees.md](docs/02-donnees.md) |
| **ce qu'on a trouvé** | [docs/03-resultats.md](docs/03-resultats.md) |
| ce que le travail nous a appris, et les erreurs à ne pas refaire | [docs/04-enseignements.md](docs/04-enseignements.md) |
| ce qui s'est passé quand, et ce qui reste à faire | [docs/BACKLOG.md](docs/BACKLOG.md) |

**Si vous ne lisez qu'une chose** : le § 1 de [docs/02-donnees.md](docs/02-donnees.md), qui
explique pourquoi le même chiffre a parfois deux valeurs dans ce projet. Sans lui, les résultats
paraissent se contredire.

---

## Les trois résultats à retenir

**Aux États-Unis, l'avis 5 étoiles est supprimé plus souvent que l'avis 3 ou 4 étoiles.** En
Europe, c'est l'inverse. Sur l'ensemble du panel, 71 % des suppressions portent sur un avis
5 étoiles.

**Le risque s'effondre avec l'âge de l'avis**, et culmine au septième jour de vie. Un avis de
trois mois risque vingt-et-une fois moins qu'un avis du jour.

**Répondre dans les deux jours divise le risque par 1,8**, sauf sur quatre chaînes américaines de
traitement antiparasitaire où rien de ce qu'on mesure n'explique les suppressions.

Le détail, les fourchettes et les réserves sont dans [docs/03-resultats.md](docs/03-resultats.md).

---

## Les données

9 048 établissements Google Maps, un relevé par jour du 11 au 24 août 2026, 4,88 millions
d'avis. La régression porte sur 225 757 d'entre eux, publiés entre le 13 mai et le 16 août.

Les fichiers ne sont pas dans le dépôt : 838 Mo et des données personnelles — nom de l'auteur,
lien vers son profil, texte de l'avis. Ils vivent dans `data/exports/exports/`, qui est ignoré
par git et le reste.

Le panel de travail est dans BigQuery : `client-divers.reviewflowz.reviews_panel_features`.

---

## Faire tourner les modèles

Prérequis : [uv](https://docs.astral.sh/uv/), et une clé de service Google Cloud dans
`~/.gcp/` — les scripts prennent le seul fichier `.json` qui s'y trouve.

Les deux tables BigQuery se construisent dans cet ordre, depuis un client SQL :

```sql
-- sql/01_selection_panel.bqsql    -> reviews_panel_selection, 225 757 avis
-- sql/02_adding_features.bqsql    -> reviews_panel_features, 42 colonnes
```

Puis, depuis `logistic-regression-study/` :

```bash
# Quelles caractéristiques font qu'un avis saute. Cinq passages.
python python/07_regression_panel.py
python python/07_regression_panel.py --sans-enseignes-signalees
python python/07_regression_panel.py --region US
python python/07_regression_panel.py --region Europe
python python/07_regression_panel.py --region Europe --sans-enseignes-signalees

# Répondre vite protège-t-il ? Lancer le contrôle d'abord.
# sql/controle_C_reponses_au_jalon.bqsql
python python/08_effet_reponse_commercant.py --sans-enseignes-signalees
```

Chaque passage écrit dans `output-study/{date du jour}-sorties-07/`. Relancé un autre jour, il
crée un nouveau dossier au lieu d'écraser l'ancien.

**`sql/02_adding_features.bqsql` ne se modifie pas sans accord préalable de l'équipe.** Le
changer oblige à reconstruire la table et à relancer tous les modèles.

---

## L'organisation du dépôt

```
docs/                      la documentation — commencer ici
logistic-regression-study/
  sql/                     la chaîne BigQuery et les contrôles
  python/                  les deux scripts de modélisation
  output-study/            les résultats datés et leurs notes
etude-exploratoire/        GELÉ depuis le 2026-09-14 — voir son README
data/                      les fichiers d'origine, hors dépôt
```

**`etude-exploratoire/` est gelée.** C'est le premier travail, celui qui a servi à comprendre les
données et à repérer les défauts de comptage. On n'y écrit plus et on n'y relance rien. Ses
résultats qui tiennent encore sont repris dans [docs/03-resultats.md](docs/03-resultats.md).

---

## Précautions de calcul

La machine de travail a 7,7 Go de mémoire et tourne sous WSL. Un calcul qui prend tous les cœurs
coupe la connexion de l'éditeur.

- `nice -n 19` au-delà de deux minutes ;
- `free -m` avant de lancer ;
- deux calculs lourds au maximum en même temps ;
- avec DuckDB, poser une limite de mémoire explicite et agréger en SQL avant de charger quoi
  que ce soit en mémoire — le fichier des avis fait 834 Mo.

**Jamais de nom d'auteur, de lien d'avis ou de texte d'avis dans un fichier versionné.**
