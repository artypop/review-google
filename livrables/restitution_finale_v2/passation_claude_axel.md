# Passation : étude des suppressions d'avis Google

Pour : le Claude qui travaille avec Axel (ReviewFlowz).
Remis avec `Restitution.docx` et les données, le 12 octobre 2026, par Cartelis.
Questions : Matthieu, par Slack.

## Comment utiliser ce document

- Il décrit les fichiers transmis, leurs colonnes, les décisions prises pendant l'étude et, pour
  chaque fait de `Restitution.docx`, la population et la requête qui le redonnent.
- Les chiffres des sections 5 et 6 ont été recalculés le 12 octobre 2026 à partir des seuls
  fichiers transmis et retrouvés à l'identique. Ceux des modèles jour par jour (section 7.2) sont
  repris des sorties de l'étude.
- Les décisions de la section 4 ont été arrêtées avec Axel et Romain au fil de l'étude.
  Appliquez-les telles quelles pour que vos chiffres se comparent à ceux de la restitution.
- Les limites de la section 9 sont connues et assumées. Quand un chiffre en dépend, citez la
  limite une fois.

---

## 1. L'étude

- **Question** : quelles caractéristiques d'un avis Google vont avec sa suppression. L'étude
  porte sur les avis 4 et 5 étoiles, ceux qu'un commerçant perd.
- **Panel** : 9 048 fiches Google, 7 secteurs, 2 régions (États-Unis ; Europe, 40 pays, sans le
  Royaume-Uni), 3 tailles de groupe (un établissement ; 4 à 10 ; 20 à 50). Les fiches ont été
  choisies par groupe d'établissements : les résultats décrivent ce panel.
- **Relevé** : un passage du robot par jour, du 11 au 24 août 2026, soit 14 passages. À chaque
  passage, il relève tous les avis de chaque fiche.
- **Suppression** : un avis que le robot ne retrouve plus. `deleted_detected_at` est la date du
  premier passage où il manque ; elle vaut toujours le lendemain de `last_seen_at`, et aucun avis
  n'est revu après sa disparition.
- **Base** : 4 876 933 avis, dont 4 590 disparus pendant le relevé.

---

## 2. Les fichiers

| Fichier | Contenu | Lignes |
|---|---|---:|
| `reviews_doublons_cleaned_all.parquet` | La base. Une ligne par avis, 25 colonnes, horodatages en UTC. Copie exacte de la table BigQuery `client-divers.reviewflowz.reviews_doublons_cleaned_all`. | 4 876 933 |
| `03C_7_17_aout.parquet` | Les avis publiés du 7 au 17 août 2026, toutes notes, dates en DATE. Sous-ensemble exact de la base. | 27 828 |
| `businesses.parquet` | Les fiches : `cid`, `place_id`, `name`, `country`, `industry`, `bucket`, `review_count_at_build`. | 9 048 |
| `features_regression_reviews_doublons_cleaned_all.parquet` | La base (25 colonnes, dates en DATE), plus le prénom et les variables calculées de la section 3. | 4 876 933 |
| `features_03C_7_17_aout.parquet` | Les avis des régressions de la restitution, mêmes colonnes. | 24 191 |
| `features_regression.sql` | Reconstruit les deux fichiers de features (DuckDB), voir section 10. | |
| `enseignes_signalees.sql` | Liste les 104 fiches des six enseignes (BigQuery). | |
| `regression_secteur_taille.csv` et ses 2 PNG | Le modèle de la restitution (graphique 3.1), tous ses paramètres, contrôles compris. | |

S'y ajoute l'annotation des prénoms faite par Axel, `reviews_name_enriched.parquet`.

- `review_id` est unique dans chaque fichier transmis. `cid` relie un avis à sa fiche.
- Les fichiers d'avis contiennent le texte, le nom de l'auteur et le lien de chaque avis.

---

## 3. Les colonnes calculées

Elles suivent les 25 colonnes de la base dans les deux fichiers de features.

| Colonne | Définition |
|---|---|
| `prenom` | Le texte cite un prénom (annotation d'Axel, `has_name`). FALSE pour un avis 4-5★ sans texte. Vide pour les 1-3★ (non annotés) et pour les 4-5★ absents de l'annotation. |
| `prenom_source` | `axel` (texte identique), `axel_texte_modifie` (texte changé entre les deux extractions), `sans_texte`, `introuvable`, `hors_annotation`. |
| `region` | `US` si `businesses.country = 'US'`, sinon `Europe`. |
| `industry`, `bucket` | Secteur et taille : `mono` (un établissement), `small` (4 à 10), `large` (20 à 50). |
| `enseigne` | La fiche fait partie des six enseignes (section 4.5). |
| `fin_suivi`, `fiche_plus_relevee` | Dernier jour où la fiche a été relevée ; TRUE si avant le 24 août. Fichier complet seulement. |
| `j_premiere_vue`, `j_reponse`, `j_suppression` | Jours entre la publication et `first_seen_at`, `reply_date`, `deleted_detected_at`. |
| `jours_de_suivi` | Jours entre `first_seen_at` et `fin_suivi`. Fichier complet seulement. |
| `n_jour` | Avis 4-5★ publiés sur la fiche le même jour, avis compris. |
| `par_jour` | Moyenne journalière des avis 4-5★ de la fiche sur les 365 jours avant le 11 août 2026. |
| `pic` | 1 si `n_jour >= 3` et `n_jour >= 4 × par_jour`. |
| `supprime` | 1 si l'avis a disparu au plus tard 7 jours après sa publication. Dans le fichier complet, rempli seulement pour les avis publiés du 7 au 17 août. |
| `disparu` | 1 si `deleted_detected_at` est renseigné. Fichier complet seulement. |
| `photo` | Au moins une photo jointe. |
| `reponse_j7`, `sans_reponse_j7` | Réponse du propriétaire au plus tard au 7e jour, et son contraire. |
| `longueur_texte`, `tranche_texte` | Caractères du texte sans les espaces de début et de fin ; `sans`, `1_40`, `41_80`, `81_130`, `131_240`, `241_plus`. |
| `tranche_guide` | `local_guide_level` en `1_3`, `4_6`, `7_10` ; vide sans niveau. |

Pour retrouver le fichier 03C dans le fichier complet :
`supprime IS NOT NULL AND star >= 4 AND prenom IS NOT NULL AND NOT fiche_plus_relevee`.

---

## 4. Les décisions prises

1. **Un avis disparu est un avis supprimé.** `deleted_detected_at` renseigné suffit. La base est
   dédoublonnée : une ligne par avis, et les 601 avis qui ont disparu puis sont revenus pendant
   le relevé en sont retirés. Une ancienne règle exigeait deux jours d'absence ; elle a été
   abandonnée avec le dédoublonnage.
2. **Avis 4 et 5 étoiles.** Les 1 à 3 étoiles restent dans les fichiers et n'entrent dans aucun
   fait, sauf le graphique A.2.
3. **Deux populations**, décrites en section 5. Un chiffre porte toujours sur l'une ou sur
   l'autre.
4. **Sept jours pour les nouveaux avis.** Un nouvel avis est supprimé s'il disparaît au plus tard
   7 jours après sa publication. Avis publiés du 7 au 17 août : le 17 août est le dernier jour qui
   laisse 7 jours avant le dernier passage, et la moitié des suppressions tombent au 6e ou au 7e
   jour (fait 1).
5. **Les six enseignes : 104 fiches au comportement à part.**
   - 4 chaînes américaines de traitement antiparasitaire, repérées par le début du nom, toutes
     succursales comprises : EcoShield Pest Solutions (35 fiches), Bulwark Exterminating (26),
     Insight Pest Solutions (21), Pointe Pest Control (20). Elles portent 1 238 des 4 590 avis
     disparus de la base, dont 1 199 à 4-5★.
   - 2 boutiques espagnoles The Boxer Club, repérées par leur `cid` (`3163466139043001754`,
     `10346942689164695031`) : une attaque par faux avis, 329 avis disparus dont 317 à une étoile.
     Le compte de six traite les deux boutiques comme deux enseignes.
   - Chaque résultat se calcule avec et sans elles. La section 6 précise, chiffre par chiffre,
     si elles sont comprises.
6. **Dates en UTC, au jour près.** Dans DuckDB, `SET TimeZone = 'UTC'` avant tout passage en
   date ; sinon une partie des avis change de jour. Les fichiers de features sont déjà en DATE.
7. **Fiches plus relevées.** 3 fiches cessent d'être relevées le 17, le 18 ou le 22 août. Elles
   sont écartées de tous les taux.
8. **Le prénom vient de l'annotation d'Axel.** Elle contient 333 `review_id` en double : on garde
   la ligne dont le texte est identique, sinon le OU des lignes. Sa colonne `deleted` compte 388
   fausses suppressions dues à ces doublons : utilisez `supprime` et `disparu`. Dans 03C, les 55
   avis 4-5★ absents de l'annotation sont écartés.
9. **Jour de pic** : la fiche reçoit au moins 3 avis 4-5★ dans la journée et au moins 4 fois sa
   moyenne journalière des 365 jours avant le 11 août. Il mesure un afflux ponctuel, distinct de
   la vitesse habituelle de collecte.
10. **Réponse** : la référence est « réponse reçue au plus tard au 7e jour », la modalité la plus
    fréquente (50,1 % des nouveaux avis). La variable affichée est donc `sans_reponse_j7`.
11. **Local Guide** : niveau au dernier relevé. Dans les données, les niveaux 1 à 3 sont des
    comptes non Local Guide, 4 et plus des Local Guides. Les avis sans niveau sont à part.
12. **Le modèle de la restitution** est volontairement simple : quatre caractéristiques
    affichées, secteur et taille en contrôle (section 7.1).

---

## 5. Les deux populations

```sql
SET TimeZone = 'UTC';
-- Nouveaux avis
CREATE VIEW n AS SELECT * FROM 'features_03C_7_17_aout.parquet';
-- Stock
CREATE VIEW s AS SELECT * FROM 'features_regression_reviews_doublons_cleaned_all.parquet'
  WHERE star >= 4 AND NOT fiche_plus_relevee;
```

**Nouveaux avis (03C), vue `n`**
- Avis 4-5★ publiés du 7 au 17 août 2026. Écartés : 55 avis sans annotation de prénom et les
  2 avis d'une fiche plus relevée.
- 24 191 avis, 4 705 fiches, 631 supprimés au plus tard au 7e jour. Sans les six enseignes :
  22 378 avis, 379 supprimés. Les boutiques espagnoles n'ont aucun avis ici.
- Mesure : part supprimée au plus tard au 7e jour.
- Un avis publié du 7 au 10 août n'est vu qu'à partir du 11 : s'il a été supprimé avant, il
  n'est pas dans la base.

**Stock, vue `s`**
- Tous les avis 4-5★ en ligne pendant le relevé, quel que soit leur âge.
- Mesure : part disparue entre le 11 et le 24 août (`disparu`), ou disparus rapportés aux
  publiés (fait 4).
- L'âge pèse plus que tout le reste : un avis récent est bien plus exposé qu'un avis ancien.
  Un écart mesuré sur le stock mélange des avis d'âges différents.

---

## 6. Les faits de la restitution

### Fait 1. Les 6e et 7e jours

- **641 des 1 272** avis 4-5★ disparus entre 1 et 13 jours après leur publication l'ont été au
  6e ou au 7e jour. Stock, avis publiés à partir du 1er juillet. Les comptes bruts se comparent
  d'un âge à l'autre : chaque âge de 2 à 13 jours est observé sur environ 28 000 avis.

  ```sql
  SELECT count(*) FILTER (j_suppression IN (6, 7)), count(*)
  FROM s
  WHERE disparu = 1 AND created_at >= DATE '2026-07-01' AND j_suppression BETWEEN 1 AND 13;
  ```

- **Graphique 1.1** est la version en taux : avis publiés à partir du 11 août, âges 1 à 12. À
  chaque âge k, il donne les avis disparus à l'âge k pour 1 000 avis en ligne et observés à cet
  âge.

### Fait 2. Répondre

- **Graphique 2.1.** Nouveaux avis, sans les six enseignes, vus et en ligne à la fin de leur
  2e jour : 17 915 avis.
  - Répondus au plus tard au 2e jour : 109 supprimés du 3e au 7e jour sur 7 642, soit 14,3 ‰.
  - Sans réponse : 223 sur 10 273, soit 21,7 ‰.
  - À secteur et taille égaux : ×0,51 [0,31–0,84]. C'est le modèle 7.1, avec `reponse_j2` à la
    place de `sans_reponse_j7` et la suppression du 3e au 7e jour comme variable expliquée.

  ```sql
  SELECT coalesce(j_reponse <= 2, FALSE) AS repondu_j2, count(*) AS avis,
         count(*) FILTER (j_suppression BETWEEN 3 AND 7) AS supprimes
  FROM n
  WHERE NOT enseigne AND j_premiere_vue <= 2 AND NOT coalesce(j_suppression <= 2, FALSE)
  GROUP BY 1;
  ```

- **Graphique 2.2.** Modèle jour par jour (section 7.2), sans les six enseignes. Chaque statut
  est comparé à un avis encore sans réponse :
  - réponse le jour même : ×0,46 ;
  - le lendemain : ×0,52 ;
  - au 2e jour : ×0,51 ;
  - au 3e jour ou après : ×0,25.

  Le taux de réponse habituel de la fiche ne joue pas. Face à 0 % : 1 à 25 %, ×1,12 ;
  25 à 75 %, ×0,91 ; 75 % et plus, ×1,04. Le graphique A.3 reprend le même modèle, six
  enseignes comprises.
- **Pourquoi un modèle jour par jour :** un avis supprimé à son 3e jour a eu moins de temps pour
  recevoir une réponse. « Répondu au 7e jour » mesure donc en partie la survie de l'avis. Dans
  le modèle jour par jour, une réponse ne compte qu'à partir du lendemain de son arrivée.

### Fait 3. Le prénom

- **×1,05 [0,80–1,38]** à secteur et taille égaux : nouveaux avis, six enseignes comprises,
  modèle 7.1, région en contrôle. C'est la ligne `tous, prenom` de `regression_secteur_taille.csv`
  et le graphique 3.1.
- **×1,01 [0,85–1,21]** à fiche égale : modèle jour par jour avec un indicateur par fiche, sur
  les 223 fiches qui ont au moins une suppression.
- **Le constat par fiche :** les fiches dont les avis positifs avec texte citent souvent un
  prénom perdent davantage d'avis, et leur vitesse de collecte ne suffit pas à l'expliquer.
  Il a été mesuré sur toute la base, avis de tous âges, avec l'ancienne règle des deux jours
  d'absence.

### Fait 4. Les services à domicile

Trois mesures, sur des populations différentes.

**a. Nouveaux avis, supprimés au plus tard au 7e jour**

| Groupe | Supprimés / avis | % |
|---|---:|---:|
| Services à domicile US, six enseignes comprises | 334 / 3 826 | 8,7 |
| Services à domicile US, sans les six enseignes | 82 / 2 013 | 4,1 |
| Idem, sans les autres entreprises antiparasitaires | 44 / 1 656 | 2,7 |
| Santé US | 70 / 2 081 | 3,4 |
| Tous secteurs et régions, sans les six enseignes | 379 / 22 378 | 1,7 |

Une « autre entreprise antiparasitaire » est une fiche dont le nom correspond à
`(?i)(pest|exterminat|termite|spidexx|mosquito|rodent|wildlife)` ou
`(?i)abc home ?(&|and) ?commercial`, hors six enseignes.

```sql
SELECT n.industry, n.enseigne,
       regexp_matches(b.name, '(?i)(pest|exterminat|termite|spidexx|mosquito|rodent|wildlife)')
         OR regexp_matches(b.name, '(?i)abc home ?(&|and) ?commercial') AS antiparasitaire,
       count(*), sum(n.supprime)
FROM n JOIN 'businesses.parquet' b USING (cid)
WHERE n.region = 'US' AND n.industry IN ('home_services', 'healthcare')
GROUP BY ALL;
```

**b. Stock : avis perdus pour 100 avis publiés, du 11 au 24 août**

Le numérateur compte les avis 4-5★ disparus du 11 au 24 août, quelle que soit leur date de
publication. Le dénominateur compte les avis 4-5★ publiés du 11 au 24 août. Le ratio mesure le
poids des pertes face au flux entrant ; un avis perdu peut être ancien.

| | Toutes fiches | Sans les six enseignes |
|---|---:|---:|
| Services à domicile | 34,7 | 22,2 |
| Santé | 12,0 | 12,0 |
| Sport et bien-être | 10,7 | 10,6 |
| Tous secteurs | 12,2 | 8,7 |
| Europe, tous secteurs | 5,4 (de 3,2 en hôtellerie à 8,1 en sport) | 5,3 |
| États-Unis, services à domicile | 38,9 | 26,5 |
| États-Unis, sport et bien-être | 15,1 | 15,1 |
| États-Unis, santé | 13,5 | 13,5 |
| États-Unis, tous secteurs | 17,1 | 11,6 |

Les chiffres que la restitution donne « sans les quatre chaînes » sont ceux de la colonne sans
les six enseignes. Les deux boutiques espagnoles, classées en sport et bien-être, expliquent
l'écart de 10,7 à 10,6.

```sql
SELECT region, industry,
       round(100.0 * sum(disparu)
             / count(*) FILTER (created_at BETWEEN DATE '2026-08-11' AND DATE '2026-08-24'), 1)
FROM s            -- ajouter WHERE NOT enseigne pour la seconde colonne
GROUP BY GROUPING SETS ((), (industry), (region), (region, industry))
ORDER BY ALL;
```

Le graphique 4.1 présente cette mesure par secteur et par taille. Les deux images qui le suivent
la présentent par région, sans les six enseignes.

**c. Le résumé « 9,8 % contre 1,0 % »** porte sur les avis 4-5★ publiés du 11 au 17 août,
toutes fiches, supprimés au plus tard au 7e jour : 9,84 % en services à domicile, 1,04 % en
restauration.

```sql
SELECT industry, round(100 * avg(coalesce(j_suppression <= 7, FALSE)::INT), 2)
FROM s WHERE created_at BETWEEN DATE '2026-08-11' AND DATE '2026-08-17'
GROUP BY 1 ORDER BY 2 DESC;
```

### Fait 5. Les jours de pic

Nouveaux avis, sans les six enseignes :
- publiés un jour de pic : 115 supprimés sur 4 974, soit 2,3 % ;
- publiés un autre jour : 264 sur 17 404, soit 1,5 %.

À secteur et taille égaux, avec le modèle 7.1 sans les six enseignes, l'écart est de ×1,78
[1,13–2,80]. Le graphique A.4 donne le détail par région : États-Unis ×1,33 [0,78–2,27], Europe
×2,75 [1,32–5,71].

```sql
SELECT pic, count(*), sum(supprime), round(100 * avg(supprime), 2)
FROM n WHERE NOT enseigne GROUP BY 1;
```

### Fait 6. États-Unis et Europe

Nouveaux avis, supprimés au plus tard au 7e jour :
- sans les six enseignes, 21,3 pour 1 000 aux États-Unis contre 11,7 en Europe ;
- avec elles, 36,5 contre 11,7.

Ce sont des écarts bruts.

```sql
SELECT region, round(1000 * avg(supprime), 1),
       round(1000 * avg(supprime) FILTER (NOT enseigne), 1)
FROM n GROUP BY 1;
```

### Fait 7. Le texte

- **Stock :** en deux semaines, 0,101 % des avis 4-5★ avec texte ont disparu, contre 0,053 %
  des avis sans texte. Par quintile de longueur, le taux va de 0,08 à 0,12 % (graphique 7.1).
- **Nouveaux avis, sans les six enseignes :**
  - plus de 80 caractères : 19,7 ‰ (201 sur 10 192) ;
  - sans texte : 13,7 ‰ (87 sur 6 335) ;
  - en Europe, 17,2 ‰ (77 sur 4 465) contre 4,6 ‰ (16 sur 3 452).
- **À secteur et taille égaux, la longueur du texte n'a pas d'effet propre.** Pour le
  vérifier, ajoutez au modèle 7.1 les indicateurs de `tranche_texte`, avec `sans` en référence.
  Le modèle ne contient pas la note de l'avis.

```sql
SELECT region, CASE WHEN longueur_texte = 0 THEN 'sans'
                    WHEN longueur_texte > 80 THEN 'plus de 80' ELSE '1 à 80' END AS texte,
       count(*), sum(supprime), round(1000 * avg(supprime), 1)
FROM n WHERE NOT enseigne
GROUP BY GROUPING SETS ((texte), (region, texte)) ORDER BY ALL;
```

### Fait 8. Les photos

×0,66 [0,40–1,08] : modèle 7.1, nouveaux avis, six enseignes comprises. L'écart est trop
incertain pour être affirmé.

### Fait 9. Les Local Guides

Stock, part des avis 4-5★ disparus en deux semaines, selon le niveau :

| Niveau | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | Sans niveau |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| % disparus | 0,105 | 0,117 | 0,122 | 0,093 | 0,032 | 0,014 | 0,014 | 0,020 | 2,02 |

- Le graphique 9.1 regroupe les niveaux 7 à 10, parce que les niveaux 8 à 10 ont trop peu de
  suppressions pour un taux à part.
- Le graphique écarte les avis sans niveau (12 651 avis) : leur barre écraserait les autres.

```sql
SELECT local_guide_level, count(*), round(100 * avg(disparu), 3)
FROM s GROUP BY 1 ORDER BY 1;
```

### Annexes de la restitution

- **905 fiches sur 8 997** ont perdu au moins un avis 4-5★ en deux semaines. 17 fiches portent
  le quart des 3 521 disparitions 4-5★. Toutes les fiches sont comptées, enseignes et fiches
  plus relevées comprises.

  ```sql
  WITH f AS (
    SELECT cid, sum(disparu) FILTER (star >= 4) AS d
    FROM 'features_regression_reviews_doublons_cleaned_all.parquet' GROUP BY cid),
  r AS (
    SELECT d, sum(d) OVER (ORDER BY d DESC ROWS UNBOUNDED PRECEDING) AS cumul,
           sum(d) OVER () AS total, row_number() OVER (ORDER BY d DESC) AS rang
    FROM f)
  SELECT (SELECT count(*) FROM f), (SELECT count(*) FROM f WHERE d > 0), max(total),
         min(rang) FILTER (cumul >= 0.25 * total)
  FROM r;
  ```

- **Graphiques A.1 et A.2.** Ils croisent la date de publication et la date de disparition.
  - A.1, les quatre chaînes : avis 4-5★, publiés à partir du 22 juillet ; les avis plus anciens
    sont regroupés.
  - A.2, les deux boutiques : avis 1★, publiés à partir du 31 juillet.
- **Les 601 avis disparus puis revenus** ont été retirés de la base et ne figurent pas dans les
  fichiers transmis. 69 % sont revenus après un seul jour d'absence.

---

## 7. Refaire les modèles

### 7.1 Le modèle de la restitution

C'est le graphique 3.1 et `regression_secteur_taille.csv`.

- **Population :** nouveaux avis. **Variable expliquée :** `supprime`.
- **Caractéristiques affichées :** `prenom`, `photo`, `sans_reponse_j7`, `pic`.
- **Contrôles, non affichés :**
  - secteur, avec l'automobile en référence ;
  - taille, avec un seul établissement en référence ;
  - région, avec l'Europe en référence, quand les deux régions sont ensemble.
- **Méthode :** régression logistique, erreurs groupées par fiche. La note n'est pas dans le
  modèle.
- **Passages :** États-Unis, Europe, les deux. Sur les deux régions ensemble :
  - prénom ×1,05 ;
  - photo ×0,66 ;
  - sans réponse au 7e jour ×1,65 [1,14–2,41] ;
  - jour de pic ×2,00 [1,35–2,95].

Ce code redonne `regression_secteur_taille.csv` (vérifié le 12 octobre 2026) :

```python
import duckdb
import pandas as pd
import statsmodels.api as sm

df = duckdb.sql("SELECT * FROM 'features_03C_7_17_aout.parquet'").df()

def ajuster(d, variables=("prenom", "photo", "sans_reponse_j7", "pic"), y="supprime"):
    X = [d[list(variables)].astype(float),
         pd.get_dummies(d["industry"], prefix="industry", dtype=float)
           .drop(columns="industry_automotive"),
         pd.get_dummies(d["bucket"], prefix="bucket", dtype=float).drop(columns="bucket_mono")]
    if d["region"].nunique() > 1:
        X.append((d["region"] == "US").astype(float).rename("region_US"))
    X = pd.concat(X, axis=1)
    X = sm.add_constant(X.loc[:, X.std() > 0], has_constant="add")
    return sm.GLM(d[y].astype(float), X, family=sm.families.Binomial()).fit(
        cov_type="cluster", cov_kwds={"groups": d["cid"].factorize()[0]})

tous = ajuster(df)
us = ajuster(df[df["region"] == "US"])
sans_enseignes = ajuster(df[~df["enseigne"]])
```

Les rapports de cotes sont `exp(params)`, leurs fourchettes `exp(conf_int())`.

### 7.2 Les modèles jour par jour

Ils produisent le graphique 2.2 et le ×1,01 du prénom.

- **Une ligne par avis et par jour** où l'avis était en ligne et observé : du lendemain de sa
  première observation jusqu'à sa suppression, ou jusqu'au 24 août. La variable expliquée vaut 1
  le jour de la suppression.
- **La réponse** compte si elle est arrivée la veille ou avant (`j_reponse <= jour - 1`).
- **Les variables** sont les mêmes qu'en 7.1, avec les mêmes contrôles et des erreurs groupées
  par fiche.
- **Graphique 2.2**, sans les six enseignes :
  - le statut de réponse remplace `sans_reponse_j7` : pas encore de réponse, réponse le jour
    même, le lendemain, au 2e jour, au 3e jour ou après ;
  - on ajoute le taux de réponse de la fiche, calculé sur ses avis 4-5★ publiés du 7 août 2025
    au 6 août 2026 : 0 %, 1 à 25 %, 25 à 75 %, 75 % et plus, et une classe à part pour les
    fiches de moins de 10 avis.
- **×1,01 du prénom :** un indicateur par fiche remplace secteur, taille et région, sur les 223
  fiches qui ont au moins une suppression.

---

## 8. Pièges techniques

- **UTC.** Sans `SET TimeZone = 'UTC'`, DuckDB passe en heure de Paris et une partie des avis
  change de jour.
- **`supprime` et `disparu`.** `supprime` ne se calcule que pour les avis publiés du 7 au
  17 août. Sur le reste de la base, seul `disparu` existe. Il se lit avec l'âge de l'avis
  (`j_premiere_vue`) et la durée de suivi (`jours_de_suivi`).
- **Les vagues.** Le passage du 12 août s'est terminé le 13 à 05:00 UTC. Une date de
  `first_seen_at` au 13 août peut donc venir du 2e ou du 3e passage.
- **L'état au dernier passage.** Niveau Local Guide, réponse et nombre d'avis de l'auteur sont
  ceux du dernier passage où l'avis a été vu.
- **L'annotation d'Axel.** Pour la suppression, utilisez nos colonnes : celle de l'annotation
  contient des doublons (section 4.8).

---

## 9. Ce que les données ne montrent pas

- **La cause d'une suppression :** filtre automatique, signalement du commerçant ou retrait par
  l'auteur.
- **Les avis filtrés avant publication.** Aucun avis contenant un lien n'a disparu pendant le
  relevé : ils sont bloqués en amont.
- **Les avis supprimés avant le 11 août**, et ceux publiés puis supprimés entre deux passages.
- **Une réponse retirée par le commerçant.** L'avis est alors compté sans réponse.
- **L'état d'un avis au moment où il a été écrit.**
- **La cause des liens observés.** Les écarts mesurés sont des liens. La réponse, par exemple,
  va avec moins de suppressions, et les données ne prouvent pas qu'elle les évite.

---

## 10. Reconstruire les fichiers

- **Les deux fichiers de features :** `features_regression.sql`, lancé dans un dossier qui
  contient `reviews_doublons_cleaned_all.parquet`, `businesses.parquet` et
  `reviews_name_enriched.parquet` : `duckdb < features_regression.sql`. Il faut quelques minutes
  et environ 6 Go de mémoire. Le résultat est identique aux fichiers transmis (vérifié le
  12 octobre 2026).
- **03C :**

  ```sql
  SET TimeZone = 'UTC';
  SELECT * REPLACE (CAST(created_at AS DATE) AS created_at, CAST(updated_at AS DATE) AS updated_at,
                    CAST(reply_date AS DATE) AS reply_date, CAST(first_seen_at AS DATE) AS first_seen_at,
                    CAST(last_seen_at AS DATE) AS last_seen_at,
                    CAST(deleted_detected_at AS DATE) AS deleted_detected_at)
  FROM 'reviews_doublons_cleaned_all.parquet'
  WHERE CAST(created_at AS DATE) BETWEEN DATE '2026-08-07' AND DATE '2026-08-17';
  ```

- **Les six enseignes :** `enseignes_signalees.sql`, sur BigQuery. Sa colonne
  `dans_biz_surveillance` compare la liste à une table interne de Cartelis. Retirez-la si la
  table n'est pas accessible.

---

## 11. Pistes ouvertes

- **Le pic des 6e et 7e jours n'a pas d'explication.**
- **Les quatre chaînes antiparasitaires.** Leurs textes sont tous différents, et on ne voit pas
  d'afflux soudain d'avis. Leurs avis citent très souvent un technicien par son prénom.
- **D'autres attaques par faux avis.** Aucune recherche systématique n'a été faite.
- **Le contenu des réponses et les signalements** ne sont pas dans les données.
- **L'effet combiné au niveau de la fiche** de la vitesse de collecte, de la part d'avis citant
  un prénom et de l'intensité de sollicitation reste à mesurer.
