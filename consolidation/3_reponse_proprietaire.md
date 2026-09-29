# 3. Réponse rapide du propriétaire

| Commande | CSV |
|---|---|
| `uv run python consolidation/3a_jour_par_jour.py` | `3_population.csv`, `3a_jour_par_jour.csv` |
| `uv run python consolidation/3b_regression_reponse.py` | `3b_effectifs.csv`, `3b_effets.csv` |

Chiffres du 2026-09-29. Table : `reviews_panel_features_03B`.

Refait le même jour de deux autres façons : une ligne par avis et par jour, sans jalon
(`5_reponse_jour_par_jour.md`), et en comparant les avis d'une même fiche (`4_quelle_fiche_quel_avis.md`,
partie 4b). Les trois vont dans le même sens pour les fiches qui répondent à plus de 75 %.

---

## Le montage

Un avis supprimé au 3e jour ne peut plus recevoir de réponse au 5e. On fixe donc un jalon :
- on prend les avis encore en ligne au passage du robot du 2e jour ;
- on lit à cette date si le propriétaire a répondu : le jour même, le lendemain, à 2 jours, ou pas
  encore ;
- on compte ceux qui disparaissent du 3e au 8e jour.

Deux types de fiches, selon la part de leurs avis de l'année précédente qui avaient une réponse
avant le 11 août : **plus de 75 %** (la fiche répond à presque tout), **75 % ou moins**.

La population (`3_population.csv`), identique à celle du 08B :

| Étape | Avis | Disparus du 3e au 8e jour |
|---|---:|---:|
| vus le jour de leur publication ou le lendemain | 19 874 | 684 |
| publiés du 10 au 16 août, suivis jusqu'à leur 8e jour | 17 473 | 596 |
| encore en ligne au 2e jour | 17 408 | 596 |
| fiche avec au moins 10 avis d'historique | 17 121 | 593 |

Les 95 fiches signalées sont toutes des `large`. Pour mono + small, « tous » et « sans
enseignes » donnent donc les mêmes chiffres.

---

## Résultats

### Fiches qui répondent à plus de 75 % : répondre vite va avec moins de suppressions

**Mono + small** (`3b_effectifs.csv`, `3b_effets.csv`) :

| Réponse au 2e jour | Avis | Disparus du 3e au 8e jour | Pour 10 000 | Risque, à note et région égales |
|---|---:|---:|---:|---:|
| le jour même | 1 435 | 37 (24 fiches) | 258 | ×0,41 [0,22 à 0,79] |
| le lendemain | 923 | 22 (16 fiches) | 238 | ×0,46 [0,23 à 0,92] |
| pas de réponse | 1 459 | 77 (27 fiches) | 528 | référence |

- Un avis qui a reçu sa réponse le jour même disparaît 2,4 fois moins qu'un avis sans réponse de
  la même sorte de fiche. Les deux fourchettes restent sous 1.

**Large, sans enseignes** :

| Réponse au 2e jour | Avis | Disparus du 3e au 8e jour | Pour 10 000 | Risque, à note et région égales |
|---|---:|---:|---:|---:|
| le jour même | 1 268 | 13 (9 fiches) | 103 | ×0,44 [0,18 à 1,07] |
| le lendemain | 1 244 | 12 (8 fiches) | 96 | ×0,41 [0,20 à 0,86] |
| pas de réponse | 1 150 | 25 (14 fiches) | 217 | référence |

- Même sens que pour mono + small, sur 25 suppressions d'avis répondus.

Jour par jour (`3a_jour_par_jour.csv`), sur 10 000 avis en ligne au 2e jour, encore en ligne au
8e jour :

| | Répondu au 2e jour | Pas de réponse |
|---|---:|---:|
| mono + small | 9 763 | 9 472 |
| large, sans enseignes | 9 913 | 9 783 |

- L'écart apparaît surtout aux 6e et 7e jours, les jours où les suppressions sont les plus nombreuses
  (`sorties/figures/3a_jour_par_jour.png`).

### Fiches qui répondent à 75 % ou moins : le sens s'inverse, sans que les données tranchent

**Mono + small** :

| Réponse au 2e jour | Avis | Disparus du 3e au 8e jour | Pour 10 000 | Risque, à note et région égales |
|---|---:|---:|---:|---:|
| le jour même | 223 | 14 (5 fiches) | 628 | ×2,45 [0,93 à 6,46] |
| le lendemain | 202 | 10 (5 fiches) | 495 | ×2,17 [0,70 à 6,77] |
| pas de réponse | 4 693 | 113 (43 fiches) | 241 | référence |

- L'avis répondu disparaît plus souvent. Les fourchettes contiennent 1, et chaque résultat repose
  sur 5 fiches.
- Sur 10 000 avis en ligne au 2e jour, 9 501 répondus et 9 759 non répondus sont encore en ligne
  au 8e jour.

**Large** : 1 à 4 suppressions par case, aucune mesure possible.

### Ce que disent les autres colonnes du modèle (`3b_effets.csv`, mono + small)

- Sur une fiche qui répond à plus de 75 %, un avis resté sans réponse disparaît 2 fois plus que
  sur les autres fiches : ×2,02 [1,00 à 4,10] ; 528 pour 10 000 contre 241.
- Avis 1 ou 2 étoiles : ×1,89 [1,05 à 3,38] face aux 5 étoiles. En large sans enseignes : ×4,41.
- Fiche aux États-Unis : ×2,24 [1,17 à 4,28].

### Contrôle : mono seul, small seul (`3b_effectifs.csv`, `3b_effets.csv`)

Le résultat de mono + small vient des fiches small. Les fiches mono ont trop peu de suppressions
pour le confirmer ou le contredire.

| Réponse au 2e jour, fiche qui répond à plus de 75 % | Mono | Small |
|---|---:|---:|
| le jour même | ×0,60 [0,16 à 2,21], 6 suppressions | ×0,34 [0,16 à 0,71], 31 suppressions |
| le lendemain | ×0,90 [0,26 à 3,09], 5 suppressions | ×0,36 [0,16 à 0,83], 17 suppressions |

| Réponse au 2e jour, fiche qui répond à 75 % ou moins | Mono | Small |
|---|---:|---:|
| le jour même | 1 suppression : aucune mesure | ×3,82 [1,59 à 9,17], 13 suppressions sur 4 fiches |
| le lendemain | 1 suppression : aucune mesure | ×3,41 [0,92 à 12,7], 9 suppressions sur 4 fiches |

- Mono : 3 504 avis, 73 suppressions du 3e au 8e jour, sur toutes les fiches mono réunies.
- Small : 5 268 avis, 198 suppressions.
- Chez les small qui répondent à 75 % ou moins, la réponse du jour même va avec 3,8 fois plus de
  suppressions, et la fourchette reste au-dessus de 1. 9 des 13 suppressions viennent d'une seule
  fiche : Cedar Park Overhead Doors (US, services à domicile, cid `10505273405281271038`),
  46 avis publiés du 10 au 16 août, 9 disparus les 16, 17, 19, 21 et 22 août
  (`3b_fiches_par_case.csv`).

---

## Réserves

- Les « ×0,41 » se lisent : à note et région égales, sur des fiches de même habitude, l'avis
  répondu disparaît 0,41 fois autant que l'avis sans réponse. La fourchette donne les valeurs
  compatibles avec les données ; quand elle contient 1, les données ne tranchent pas.
- L'hypothèse « répondre sur une fiche qui répond peu augmente le risque » repose sur 24
  suppressions d'avis répondus, portées par 5 fiches par case. Sur les small seuls, la
  fourchette du jour même passe au-dessus de 1. 9 de ses 13 suppressions viennent de Cedar Park
  Overhead Doors, qui a répondu le jour même à 46 avis. Sans elle, il en reste 4, trop peu pour
  mesurer. Les fiches derrière chaque case : `3b_fiches_par_case.csv`.
- Avec les 4 chaînes, la réponse du jour même sur les fiches `large` qui répondent à plus de
  75 % donne ×2,36 [1,13 à 4,94]. Les chaînes répondent à presque tout le jour même : elles
  apportent 389 de ces 1 657 avis et 112 de leurs 125 suppressions.
- Les réponses à 2 jours sont écartées partout : 1 à 4 suppressions par case.
- Délais en jours civils, heure UTC : « le jour même » va jusqu'à 24 heures, « le lendemain »
  jusqu'à 48 heures.
- Une réponse retirée par le propriétaire est invisible. Les données ne disent pas qui a signalé
  un avis : sur une fiche qui répond à tout, l'absence de réponse peut marquer un avis que le
  propriétaire conteste. Hypothèse, non vérifiable ici.
- Dans les passages mono seul et small seul, les cases écartées ne sont pas les mêmes que dans
  mono + small : 3 504 et 5 268 avis ne font donc pas les 8 935 de mono + small.
