# Passation — étude régression logistique

Écrit le 2026-09-09, pour reprendre le travail sur une autre machine.
Destiné à qui reprend le dossier, humain ou assistant.

> **Mise à jour du 2026-09-09 au soir. Les sections 3 et 4 ci-dessous sont périmées.**
> Ce qu'elles annoncent comme « pas construit » l'est depuis :
> `age_days` est dans le panel, `sql/04_avis_features-v3.sql` et `sql/05_panel_final-v3.sql`
> sont écrits et exécutés, et le programme statsmodels est
> `06_statsmodels_analysis_review_claude.py`, qui tourne et produit ses sorties dans
> `sorties/`. Deux défauts de construction ont été trouvés et corrigés dans l'intervalle —
> 766 suppressions comptées deux fois, et une fuite de données du futur sur la rafale
> d'auteur. Le détail et les résultats sont dans `BACKLOG.md`, section « Fait le 2026-09-09 ».
> La règle du test de robustesse a changé : voir `../CLAUDE.md`, Conventions de Restitution
> point 5.

> Ordre de lecture : cette note, puis `BACKLOG.md` (état d'avancement détaillé et liste des
> caractéristiques retenues), puis `../CLAUDE.md` (instructions du projet, périmètre, pièges).
> Les consignes de rédaction à respecter sont dans `../etude-exploratoire/PASSATION.md`,
> section 1. Elles s'appliquent aussi à ce dossier.

---

## 1. À quoi sert ce dossier

Construire le modèle qui répond à la question d'Axel : quelles caractéristiques anodines d'un
avis Google sont associées à sa suppression. Le dossier `../etude-exploratoire/` a servi à
comprendre les données et à repérer les défauts de comptage ; ses chiffres sont à reprendre, sa
méthode reste la référence.

Règle d'environnement, à ne pas contourner : la table de panel est construite, corrigée et
interrogée **uniquement en BigQuery** (`client-divers.reviewflowz.*`). Aucune version en DuckDB
ni en pandas. Un seul endroit où corriger, sinon les versions divergent avec le temps — c'est
exactement ce qui a rendu l'étude exploratoire peu fiable.

---

## 2. Ce qui est construit

**La table de panel : `client-divers.reviewflowz.avis_deleted_panel`.**

Une ligne = un avis, à une vague où il est encore en ligne. La colonne `deleted` vaut 1 la seule
vague où l'avis disparaît pour de bon, 0 avant, et l'avis n'a plus aucune ligne après. Construite
par `sql/01_build_avis_deleted_panel.sql`, qui applique les deux corrections de comptage :

- les 24 bugs d'édition (même auteur, même note, même date de dépôt, texte différent) ne sont
  jamais comptés comme une suppression ;
- un avis absent un seul jour est un raté de collecte, jamais une suppression ; absent 2 jours
  ou plus, c'est une vraie suppression, datée de sa première disparition.

Comptage de référence : **5 230 lignes de disparition, portées par 5 109 avis distincts, →
4 747 suppressions retenues en DuckDB, 4 737 en BigQuery.** Le 5 230 compte des événements, les
deux autres comptent des avis. Écart entre moteurs expliqué dans `../CLAUDE.md` point 4.

**Colonnes présentes dans la table :** `review_id`, `cid`, `wave`, `deleted`,
`jours_en_ligne_avant_suppression`, `jours_sous_surveillance_avant_suppression`.

**Les deux requêtes de contrôle**, qui lisent la table sans la modifier :

| Fichier | Ce qu'il fait |
|---|---|
| `sql/02_verification_totaux.sql` | Totaux du panel, à comparer aux valeurs attendues (~4 875 000 avis, ~4 740 supprimés) |
| `sql/03_concentration_par_magasin.sql` | Les fiches qui concentrent les suppressions, pour vérifier qu'aucune n'écrase le modèle |

**Tables et vues BigQuery connues comme existantes :** `reviews`, `waves`, `businesses`,
`avis_deleted_panel`, et la vue `ressuscites` (créée depuis `sql/dbeaver/scripts_divers.sql`).

**Doublon repéré, pas encore supprimé :** `sql/dbeaver/requete_creation_avis_deleted_panel.sql`
fait exactement la même chose que `sql/01_build_avis_deleted_panel.sql` — même logique, mêmes
colonnes de sortie. C'est le brouillon de travail DBeaver, écrit avant que la version commentée
soit rangée dans `sql/`. Romain doit dire s'il le supprime ; rien n'a été touché.

---

## 3. Ce qui n'est pas construit

**`age_days` n'existe pas dans la table de panel.** C'est le facteur dominant du modèle, et il
manque. À ajouter directement dans `sql/01_build_avis_deleted_panel.sql`, dans le SELECT final :
`TIMESTAMP_DIFF(w.started_at, r.created_at, DAY) AS age_days`. La valeur change d'une ligne à
l'autre pour un même avis (vague 2 : 3 jours, vague 3 : 4 jours…), ce qui est le comportement
voulu : le modèle a besoin de l'âge de l'avis au moment de chaque vague. Même logique que la
colonne `age_days` de `fresh_hazard.parquet`, côté DuckDB
(`../etude-exploratoire/scripts/build_tables.py:231`).

**Aucune caractéristique d'avis n'existe côté BigQuery.** Elles sont toutes déjà écrites en
DuckDB dans `../etude-exploratoire/scripts/build_tables.py:130-183` (table `reviews_features`).
Le travail consiste à porter cette logique en SQL BigQuery, pas à la réinventer : `star`,
`has_text`, `text_chars`, `n_photos`, `has_photo`, `has_reply`, `reviewer_review_count`,
`log_rc`, `rc_zero`, `local_guide_level`, `lg_level_missing`, `new_account`, `language`,
`author_key` (hash extrait de `review_link`), `author_same_day_burst`, plus secteur / pays /
taille par jointure sur `businesses`.

**Le programme `statsmodels` n'est pas écrit.** Lecture de la table depuis BigQuery via
`google.cloud.bigquery` vers pandas, puis modélisation avec `statsmodels` (pas `scikit-learn`,
pour obtenir directement les coefficients et leurs marges d'incertitude).

**La caractéristique « le texte contient un prénom » n'est pas construite.** À documenter comme
imparfaite, au même titre que le dictionnaire d'insultes de l'étude exploratoire (7 langues
couvertes sur 41 pays).

---

## 4. Ordre de travail — validé et exécuté le 2026-09-09

Les six points ci-dessous sont faits, sauf le point 5 (tableau croisé stratifié par âge), qui
est produit par le script sous la forme de `sorties/06_croisements_par_age.csv`.

1. Ajouter `age_days` au panel (modification de `sql/01`, table à reconstruire).
2. Écrire `sql/04_avis_features.sql` : une ligne par `review_id`, portage des caractéristiques
   ci-dessus depuis `build_tables.py`. Jointure au panel sur `(review_id, cid)`.
3. Comparer les totaux de cette nouvelle table BigQuery à `reviews_features.parquet` (DuckDB)
   sur les mêmes avis, pour vérifier que le portage d'un moteur SQL à l'autre ne dérive pas.
4. Écrire le programme `statsmodels`.
5. Avant le modèle complet : un tableau croisé par caractéristique, stratifié par âge, comme
   dans l'étude exploratoire. Objectif : écarter tout de suite une caractéristique qui ne montre
   rien, et comprendre celles qui montrent quelque chose avant de les combiner.
6. Chercher les effets cumulés seulement après l'étape 5.

Le point 4 peut s'écrire en parallèle des points 1 à 3, sans attendre la validation du périmètre
par Axel.

---

## 5. Décisions prises le 2026-09-09

**La langue devient deux variables distinctes, pas une.** Axel et Romain veulent mesurer si
écrire dans une langue qui n'est pas celle du pays joue un rôle. L'étude exploratoire mesurait
autre chose : l'écart à la langue majoritaire de la fiche. Les deux axes sont conservés, sous des
noms qui disent lequel est lequel :

| Ce qu'elle mesure | Nom retenu | Remplace |
|---|---|---|
| L'avis est dans une langue qui n'est pas une langue du pays du commerce | `langue_etrangere_au_pays` | rien, à construire |
| L'avis est dans une langue inhabituelle pour ce commerce précis | `langue_minoritaire_sur_la_fiche` | `lang_off_modal` |

`lang_off_modal` est abandonné comme nom : « modal » ne dit pas ce qui est mesuré.

**Pourquoi les deux axes ne se confondent pas.** En Espagne, 40 des 550 fiches du panel ont
l'anglais comme langue majoritaire de leurs avis ; la plus grosse en compte 1 335 rédigés en
anglais. Même situation en Grèce (21 fiches sur 116) et au Portugal (16 sur 94). Sur ces fiches,
un avis en anglais est étranger au pays mais parfaitement habituel pour le commerce. Une seule
variable ne peut pas distinguer les deux cas.

Le croisement des deux donne quatre situations, et c'est le croisement qui permet de savoir à
quoi réagit le filtre de Google :

- étranger au pays **et** inhabituel sur la fiche : l'avis qui détonne complètement ;
- étranger au pays mais habituel sur la fiche : l'hôtel touristique espagnol anglophone ;
- langue du pays mais inhabituel sur la fiche : l'avis en espagnol sur ce même hôtel ;
- habituel sur les deux : le cas de référence.

Si Google réagit à « l'avis détonne », seule la première situation ressort. S'il réagit à
« l'auteur n'est pas du pays », les deux premières ressortent.

**Chiffres ci-dessus reproductibles** avec cette requête, sur l'export local
(`data/exports/exports/`, environnement exploratoire) :

```sql
CREATE VIEW base AS
SELECT r.cid, r.language, b.country
FROM 'reviews.parquet' r JOIN 'businesses.parquet' b USING (cid)
WHERE NOT r.is_update AND r.language IS NOT NULL;

CREATE TABLE modal AS
SELECT cid, country, language AS modal_language, n FROM (
  SELECT cid, country, language, count(*) AS n,
         row_number() OVER (PARTITION BY cid ORDER BY count(*) DESC, language) AS rn
  FROM base GROUP BY cid, country, language
) WHERE rn = 1;

SELECT country, count(*) AS n_fiches, count(*) FILTER (modal_language = 'en') AS modal_en,
       max(n) FILTER (modal_language = 'en') AS max_avis_en
FROM modal GROUP BY country ORDER BY n_fiches DESC;
```

**Ce que `langue_etrangere_au_pays` demande de construire.** Une table pays → langues
officielles, qui n'existe pas dans les données brutes (seul le pays y figure). Elle doit associer
à chaque pays un **ensemble** de langues, pas une seule : la Belgique en a trois officielles
(français, néerlandais, allemand), la Suisse quatre. Avec une règle « BE → français », un avis en
néerlandais à Anvers serait compté comme étranger, ce qui n'est pas ce qu'on cherche à mesurer.
La variable devient donc « la langue de l'avis n'est dans aucune des langues officielles du
pays ». Le panel contient 41 pays à renseigner et 146 langues d'avis distinctes ; les codes sont
au format court (`en`, `fr`, `de`, `ca`).

---

## 6. Questions ouvertes

**Pour Axel** (Romain s'en charge) :

1. **Le périmètre.** L'étude exploratoire avait tranché sur les avis frais (30 jours ou moins) :
   107 821 avis, dont 2 540 supprimés, soit 2,36 % de ces 107 821. À comparer au corpus entier,
   0,097 % (4 747 sur 4 877 534). Ce cadrage reste à confirmer pour la régression. Les outils se
   construisent quel que soit le choix ; seul le périmètre des lignes analysées en dépend.
   Attention en citant un chiffre d'« avis récents supprimés » : trois comptages coexistent, tous
   justes, à citer avec leur code (**D1** = 2 450, **D2** = 2 462, **D3** = 2 540). Détail dans
   `../etude-exploratoire/documentations/2026-09-08-age-a-la-suppression.md`.
2. **Laquelle des deux vélocités mettre en avant dans le rapport.** Les deux colonnes existent
   déjà. `jours_en_ligne_avant_suppression` part de la vraie date de publication donnée par
   Google : c'est la durée réelle en ligne. `jours_sous_surveillance_avant_suppression` part du
   premier passage de notre robot : identique pour un avis posté pendant le suivi, plus courte
   pour un avis déjà en ligne avant le 11 août, puisqu'on ne prétend rien sur ce qu'on n'a pas
   vu. Rien à construire, seulement à choisir.

**À trancher avec Romain :**

3. **La langue des noms de colonnes.** Le panel BigQuery est en français
   (`jours_en_ligne_avant_suppression`), l'étude exploratoire en anglais (`has_text`,
   `lang_off_modal`). À décider une fois pour toutes les caractéristiques du point 2 de
   l'ordre de travail, pas colonne par colonne.
4. **Le statut Local Guide.** `BACKLOG.md` liste `local_guide` et `local_guide_level`. Vérifier
   s'ils portent bien deux informations différentes avant de les lire séparément : le niveau
   n'est peut-être qu'une autre mesure du nombre d'avis du critique. L'étude exploratoire
   n'utilisait que `local_guide_level`, avec `lg_level_missing` pour marquer les manquants.

**À vérifier sur l'autre machine :**

5. La table BigQuery `reviews` doit porter les colonnes dont les caractéristiques ont besoin :
   `review_link`, `reviewer_review_count`, `reviewer_photo_count`, `local_guide_level`,
   `n_photos`, `reply_text`, `reply_date`, `language`, `updated_at`. `sql/01` n'en lit que huit,
   donc rien ne confirme aujourd'hui que les autres ont bien été chargées. À contrôler avant
   d'écrire `sql/04`.

---

## 7. Pièges à ne pas rouvrir

**`review_id` n'est pas unique.** Toujours filtrer `NOT is_update` sur la table `reviews`.

**`deleted_detected_at` seul surcompte les suppressions.** Il veut seulement dire que le robot
n'a pas retrouvé l'avis à une vague. La correction est déjà appliquée dans `sql/01` ; ne jamais
compter une suppression depuis la colonne brute.

**Les deux colonnes de vélocité ne sont jamais des variables d'entrée du modèle.** On ne les
connaît que pour un avis déjà supprimé : les utiliser reviendrait à prédire un événement avec une
information qu'on n'a qu'après qu'il s'est produit. Elles servent à décrire les avis supprimés
dans le rapport. Dans le modèle, la variable de temps est `age_days`, connue à l'avance quelle
que soit l'issue.

**L'âge de l'avis pèse plus que tout le reste.** Toute comparaison qui ne tient pas compte de
l'âge mesure surtout une différence d'âge. Exemple concret : si les avis avec photo se trouvent
être plus souvent des avis récents, on croira que la photo fait supprimer alors qu'on aura
seulement comparé des avis jeunes à des avis vieux.

**Les suppressions sont concentrées.** 85,4 % des 9 048 établissements n'ont aucune suppression.
**Périmé depuis le 2026-09-09 :** le critère des 5 % est abandonné, voir `../CLAUDE.md`.
Pour mémoire, il retenait 24 fiches portant 14,4 % des 4 747 suppressions, dont
deux salles de sport espagnoles attaquées qui en portent 364 à elles deux. Tout modèle se
relance sans ces 24 fiches pour vérifier que les conclusions tiennent.

**Les caractéristiques d'auteur sont figées à la dernière valeur vue.** Un compte affiché à
0 avis le 12 août peut en afficher 5 le 24, et c'est 5 qui figure dans l'export. Réserve à écrire
dans le rapport, pas un motif d'exclusion.

**Une réponse de propriétaire retirée est indétectable.** L'export ne versionne que la note et le
texte de l'avis. Réserve connue sur `has_reply`.

**Ne pas lancer de calcul lourd sans le dire.** La machine de Romain est sous WSL avec VSCode
connecté ; un calcul qui prend tous les cœurs coupe sa connexion. Au-delà de deux minutes :
`nice -n 19`, un seul cœur, et c'est lui qui décide quand.

---

## 8. Où trouver quoi

| Fichier | Contenu |
|---|---|
| `BACKLOG.md` | État d'avancement, décisions du 2026-09-07, liste des caractéristiques retenues |
| `sql/01_build_avis_deleted_panel.sql` | Construction du panel, avec les corrections de comptage commentées |
| `sql/02_verification_totaux.sql` | Contrôle des totaux après reconstruction |
| `sql/03_concentration_par_magasin.sql` | Fiches concentrant les suppressions |
| `sql/dbeaver/` | Brouillons DBeaver, dont un doublon de `01` (voir section 2) |
| `../CLAUDE.md` | Instructions du projet : périmètre, pièges, conventions de restitution |
| `../etude-exploratoire/PASSATION.md` | Consignes de rédaction (section 1), pièges du jeu de données |
| `../etude-exploratoire/scripts/build_tables.py` | Les caractéristiques déjà écrites, à porter en BigQuery |
| `../etude-exploratoire/documentations/INDEX.md` | Inventaire des 24 documents avec leur statut |
| `../etude-exploratoire/documentations/legacy/` | **Chiffres d'avant correction. Aucun à citer.** |
| `../BONNES-ET-MAUVAISES-PRATIQUES.md` | Écueils rencontrés, à ne pas répéter |

Données personnelles : `data/` est dans le `.gitignore`. Ne jamais committer d'extrait de
données. Ne jamais faire figurer de nom d'auteur ni de lien d'avis dans un document.
