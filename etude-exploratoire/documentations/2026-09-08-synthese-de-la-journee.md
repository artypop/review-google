# Synthèse du 2026-09-08 — résultats validés

Ce document ne contient que des résultats vérifiés, avec pour chacun la commande qui le
régénère. Inventaire complet de la documentation : [INDEX.md](INDEX.md). Méthode et écueils :
[2026-09-08-note-de-methodo.md](2026-09-08-note-de-methodo.md) et
[../../BONNES-ET-MAUVAISES-PRATIQUES.md](../../BONNES-ET-MAUVAISES-PRATIQUES.md).

---

## Le socle : ce qu'on compte

**5 230 disparitions brutes -> 4 747 suppressions retenues.**

`deleted_detected_at` dans l'export signifie seulement que le robot ne retrouve plus l'avis à un
passage. Deux situations rendent cette déduction fausse et sont retirées :

- **bug d'édition** (24 avis) : même auteur, même note, même date de dépôt, texte réécrit ;
- **raté de collecte** : avis absent un seul jour puis revenu à l'identique.

Un avis absent 2 jours ou plus avant de revenir reste compté comme supprimé, à la date de sa
première disparition.

Cette définition existe en **un seul endroit** hors BigQuery :
[`../scripts/suppressions_corrigees.py`](../scripts/suppressions_corrigees.py). La référence est
[`01_build_avis_deleted_panel.sql`](../../logistic-regression-study/sql/01_build_avis_deleted_panel.sql).
Si la définition change en BigQuery, ce fichier est à reprendre, et lui seul.

---

## Résultat 1 — L'âge à la suppression, jour par jour

```
nice -n 19 .venv/bin/python etude-exploratoire/scripts/age_a_la_suppression.py
```

Note produite : [2026-09-08-age-a-la-suppression.md](2026-09-08-age-a-la-suppression.md)

| Âge de l'avis | Supprimés | Avis observés à cet âge |
|---:|---:|---:|
| 5 jours | 43 | 32 713 |
| 6 jours | 279 | 32 823 |
| **7 jours** | **449** | 32 609 |
| 8 jours | 118 | 32 339 |
| 9 jours | 134 | 32 711 |

**Le nombre d'avis observés est quasi constant d'un âge à l'autre** — environ 32 000 par âge, de
2 à 30 jours. Les nombres bruts se comparent donc directement, sans pondération ni exposition.
Seul l'âge 1 jour est sous-observé (3 700), un avis n'entrant dans le calcul qu'au passage
suivant celui qui l'a découvert.

Le pic à 7 jours vaut 3,8 fois le niveau de 8 jours et 10 fois celui de 5 jours.

## Résultat 2 — Le pic à 7 jours est un effet d'âge, pas une purge

Trois contrôles, dans la même note :

| Contrôle | Ce qu'on verrait si c'était une purge | Ce qu'on observe |
|---|---|---|
| Étalement dans le temps | 1 ou 2 journées | **12 des 13 journées** du suivi |
| Étalement sur les fiches | quelques listings | **144 établissements** ; le plus touché en porte 27, soit 6 % des 449 |
| Retrait des 2 journées les plus chargées | le pic disparaît | **il reste** : 381 à 7 j, 200 à 6 j, 75 à 8 j |

Le pic est même plus net après ce retrait : le rapport 7 j / 8 j passe de 3,8 à 5,1.

**Écarté par la même note : le rythme hebdomadaire.** Les bosses à 14, 21 et 28 jours ne
survivent pas au retrait de l'âge 7 (l'écart passe de ×2,6 à ×1,5) et ne tiennent que dans
5 vagues sur 13, portées par les 16 et 23 août. `created_at` a été vérifié comme un horodatage
réel : courbe horaire plausible et 60 valeurs de secondes présentes. Les multiples de 7 ne
viennent donc pas d'une date reconstruite depuis un libellé « il y a une semaine ». Ce contrôle
a été fait par requête ponctuelle, non versionnée dans un script ; son détail est dans
[2026-09-08-note-de-methodo.md](2026-09-08-note-de-methodo.md).

## Résultat 3 — La répartition en tranches larges

```
nice -n 19 .venv/bin/python etude-exploratoire/scripts/histogramme_age_suppressions.py
```

Note produite : [2026-09-08-histogramme-age-des-suppressions.md](2026-09-08-histogramme-age-des-suppressions.md)

| Âge à la suppression | Suppressions | Part des 4 747 | Avis distincts dans la tranche | Risque par jour |
|---|---:|---:|---:|---:|
| moins de 1 mois | 2 450 | 51,6 % | 101 392 | 0,2699 % |
| 1 à 3 mois | 453 | 9,5 % | 168 325 | 0,0249 % |
| 3 à 6 mois | 183 | 3,9 % | 205 046 | 0,0078 % |
| 6 à 12 mois | 223 | 4,7 % | 361 092 | 0,0051 % |
| plus de 1 an | 1 438 | 30,3 % | 4 147 161 | 0,0027 % |

**Le vieux stock pèse 30 % des 4 747 suppressions par son volume, pas par son risque.** Il
compte 4,1 millions d'avis contre 101 000 à moins d'un mois, soit 41 fois plus d'avis. Son
risque par jour, lui, est 100 fois plus faible.

**7,65 % des avis neufs sont supprimés dans leurs 30 premiers jours** (risque cumulé, jours
d'âge 1 à 29). Réserve attachée à ce chiffre : il enchaîne des risques quotidiens mesurés sur
13 jours d'observation pour couvrir 30 jours d'âge, et il est sensible au pic de 7 à 13 jours.
Si ce pic est un accident de la fenêtre observée, le cumul baisse d'autant.

Contrôle : la répartition tient sans les 24 fiches massivement purgées. Sur les 4 065
suppressions restantes après retrait de leurs 682, la tranche « moins d'un mois » fait 47,7 % et
« plus d'un an » 33,4 %.

Contrôle de censure : sur les seuls avis déjà présents à la vague 1, donc suivis les 14 jours
complets, la hiérarchie tient — 2,29 % des avis de moins d'un mois supprimés contre 0,034 % des
avis de plus d'un an.

## Résultat 4 — Trois comptages d'« avis récents supprimés », réconciliés

| Code | Définition | Suppressions | Usage |
|---|---|---:|---|
| **D1** | âge à la suppression strictement inférieur à 30 jours | 2 450 | la tranche « moins de 1 mois » du tableau ci-dessus |
| **D2** | âge à la suppression de 30 jours ou moins | 2 462 | le périmètre de modélisation, filtre `age_days <= 30` |
| **D3** | avis âgé de 30 jours ou moins au 11 août, supprimé à n'importe quel moment | 2 540 | une cohorte figée au départ de l'étude |

Les écarts s'expliquent entièrement : **D2 − D1 = 12** avis supprimés à exactement 30 jours,
**D3 − D2 = 78** avis qui avaient moins de 30 jours au 11 août mais ont franchi leur trentième
jour avant d'être supprimés. À citer avec son code, pas avec le seul chiffre.

## Résultat 5 — Le volume varie d'un facteur 5 selon la journée du suivi

De **153 suppressions le 14/08 à 760 le 17/08**. Chaque journée se répartit sur 129 à 275
établissements, donc aucune n'est une purge de quelques listings — à une exception, le 16/08, où
un seul établissement porte 26 % des suppressions du jour et où le total passe de 706 à 486 en
écartant les fiches purgées à plus de 5 %.

## Résultat 6 — La concentration, recalculée

```
nice -n 19 .venv/bin/python etude-exploratoire/scripts/histogramme_age_suppressions.py
```

**85,4 % des établissements n'ont aucune suppression.** Les 24 fiches ayant perdu plus de 5 % de
leurs avis portent **14,4 %** des 4 747 suppressions.

Les chiffres « 84 % / 39 fiches / 19,5 % » de `CLAUDE.md` et « 84 % / 39 fiches / 20 % » de la
note du 2026-09-06 sont d'avant la correction et ne valent plus.

## Résultat 7 — Le cas des deux salles de sport espagnoles

```
nice -n 19 .venv/bin/python etude-exploratoire/scripts/cas_attaque_salles_de_sport.py
```

Note produite : [2026-09-08-cas-attaque-salles-de-sport.md](2026-09-08-cas-attaque-salles-de-sport.md)

Les deux seules fiches du panel à dépasser 100 suppressions. **Chaque part est rapportée au
listing de sa propre fiche.**

| | Fiche A | Fiche B |
|---|---:|---:|
| Avis au listing | 781 | 668 |
| Publiés les 1er et 2 août | 219 (28,0 % de ses avis) | 111 (16,6 % de ses avis) |
| Avis supprimés | 229, soit 29,3 % de ses 781 avis | 135, soit 20,2 % de ses 668 avis |
| Note affichée par Google au 11/08 | 3,81 | 4,67 |
| Note affichée par Google au 24/08 | **4,95** | **4,96** |
| Délai de suppression dominant | 14-15 jours | 10-11 jours |

Un auteur distinct par avis ou presque, deux tiers sans aucun texte. Le signal était le rythme
et l'écart à la note habituelle de la fiche, pas le contenu.

**Ces 364 suppressions représentent 15 % des 2 450 suppressions de la tranche D1 « moins de
1 mois ».** Choisir le périmètre des avis récents ne dilue pas ce cas, il le concentre — d'où la
nécessité de le traiter à part explicitement dans les modèles.

362 des 364 portent sur des avis publiés entre le 28 juillet et le 5 août, la fenêtre couverte
par les tableaux de la note ; les 2 restantes portent sur des avis publiés avant le 28 juillet.

Ce qui a déclenché le retrait n'est pas dans les données. L'export ne contient rien sur les
signalements. Le gérant ayant répondu à une partie de ces avis, un signalement de sa part est
l'hypothèse la plus simple, mais rien ne la confirme.

---

## Conséquence pour la régression logistique

**Périmètre retenu : les avis de 30 jours ou moins.** Le nombre de suppressions dépend de la
définition d'âge retenue — voir les codes D1, D2, D3 du Résultat 4. Deux façons de le chiffrer, à ne pas
mélanger.

**Au niveau de l'avis, cohorte D3** (avis âgé de 30 jours ou moins au 11 août) :

| | Cohorte D3 | Corpus complet |
|---|---:|---:|
| Avis | 107 821 | 4 877 534 |
| Suppressions | 2 540, soit 53,5 % des 4 747 du corpus | 4 747 |
| Part de la cohorte supprimée | 2,36 % de ses 107 821 avis | 0,097 % de 4 877 534 |

**Au niveau de l'observation** (un avis × un passage du robot), tranche D1 « moins de 1 mois » :

| | Tranche D1 | Corpus complet |
|---|---:|---:|
| Observations | 907 588 | 63 148 624 |
| Suppressions | 2 450, soit 51,6 % des 4 747 | 4 747 |

Passer de la tranche D1 au corpus complet multiplie les observations par 70 et les événements
par 1,9. À 2,36 % d'avis supprimés le problème d'événement rare disparaît ; à 0,097 % les
coefficients deviennent instables.

Les chiffres au niveau de l'observation viennent de
`histogramme_age_suppressions.py` ; ceux au niveau de l'avis d'une requête ponctuelle, non
encore versionnée dans un script.

Le périmètre restreint sur **l'âge de l'avis, pas sur son sort** : tous les avis frais sont
gardés, supprimés et non supprimés. Le stock ancien reste dans la table BigQuery, le filtre se
pose à l'analyse.

**Ce qui n'est pas établi** : que les mécanismes diffèrent réellement entre frais et vieux
stock. Des taux bruts non stratifiés suggèrent une inversion de signe sur le texte et sur la
réponse du propriétaire, mais ce test n'a pas été refait à âge comparable et il contredit les
analyses existantes sur au moins un facteur. **Ne pas s'appuyer sur cet argument tant qu'il n'est
pas repris.**

## Ce qui reste à faire

1. **Relancer le Test 2** sur le comptage corrigé. Il portait l'angle du livrable et c'est le
   résultat le plus exposé, puisqu'il mesure la mortalité des vieux avis — exactement là où se
   trouvaient les fausses suppressions.
2. **Relancer les analyses A, B et le contrôle de robustesse** sur le comptage corrigé.
3. **Compter les attaques par avis négatifs dans le panel.** Deux repérées par hasard, le
   balayage systématique n'est pas fait, donc aucun chiffre n'existe.
4. **Croiser le pic à 7 jours avec les facteurs de l'analyse B** : qui sont les avis qui tombent
   à 7 jours, et diffèrent-ils des autres. Candidat direct pour l'angle faux positifs.
5. **Refaire le test frais / vieux stock à âge comparable**, pour établir ou écarter la
   différence de mécanismes.

## Limites qui ne se lèveront pas

- **14 jours d'observation.** Les suppressions rapides sont visibles ; une révision de
  modération à six mois ne l'est pas. Toute projection annuelle suppose que ces 14 jours sont
  représentatifs, ce que rien ne garantit.
- **Le jour de vie 0** est hors de portée d'une collecte quotidienne.
- **Le filtrage avant publication est invisible.** Un avis que Google refuse de publier
  n'apparaît nulle part dans les données.
- **Vrais faux avis et erreurs de modération sont indistinguables** par collecte automatique.
