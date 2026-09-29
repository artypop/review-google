# 2.1 Google supprime peu une fois l'avis publié

| Commande | CSV |
|---|---|
| `uv run python consolidation/2_1_peu_de_suppressions.py` | `2_1a_par_annee.csv`, `2_1b_par_age.csv`, `2_1b_resume.csv` |

Chiffres du 2026-09-29. Base : `reviews_doublons_cleaned`.

---

## Résultats

### Sur toute la base (`2_1a_par_annee.csv`)

- 4 035 avis disparaissent pendant les 14 jours de suivi, sur 4 751 680 : 8,5 pour 10 000, soit
  0,085 %.
- 3 067 de ces 4 035 suppressions portent sur des avis publiés en 2026 (76 %) : 63 pour 10 000
  avis de 2026.
- Les avis plus anciens ne disparaissent presque plus :

| Année de publication | Suppressions pour 10 000 avis | Sans enseignes |
|---|---:|---:|
| 2026 | 63,0 | 42,9 |
| 2025 | 4,7 | 4,2 |
| 2024 | 2,6 | 2,6 |
| 2023 | 2,2 | 2,1 |
| 2016 à 2022 | de 0,9 à 1,9 | de 0,9 à 1,9 |
| 2014 et 2015 | 1,7 et 2,8 (5 suppressions) | 1,9 et 3,0 |
| avant 2014 | 0 | 0 |

### Sur les avis publiés de J-30 à J+13 (`2_1b_resume.csv`, `2_1b_par_age.csv`)

Avis publiés du 12 juillet au 24 août 2026.

- 107 644 avis, 2 467 supprimés : 229 pour 10 000, soit 2,3 %.
- Sans enseignes : 100 896 avis, 1 487 supprimés : 147 pour 10 000, soit 1,5 %.

Le rythme des suppressions selon l'âge de l'avis, en suppressions par jour pour 10 000 avis en
ligne :

| Âge de l'avis | Tous | Sans enseignes |
|---|---:|---:|
| 1 à 8 jours | 48,5 | 35,1 |
| 9 jours et plus | 14,5 | 8,3 |
| le 7e jour seul | 136,6 | 84,3 |
| le 30e jour seul | 3,7 | 3,9 |

- Après le 8e jour, le rythme quotidien est divisé par 3,3 (par 4,2 sans enseignes).
- Encore en ligne sur 10 000 avis publiés :

| | au 8e jour | au 15e jour | au 30e jour | au 43e jour |
|---|---:|---:|---:|---:|
| tous | 9 623 | 9 395 | 9 250 | 9 213 |
| sans enseignes | 9 715 | 9 605 | 9 505 | 9 470 |

---

## Ce qui diffère de la formulation du plan

- « Moins de 1 % » : vrai sur la base entière (0,085 %). Sur les avis de J-30 à J+13, 2,3 %
  disparaissent (1,5 % sans enseignes).
- « Au-delà de 8 jours, quasi plus de suppressions » : le rythme quotidien baisse, mais il dure.
  Sans enseignes, sur 10 000 avis, 285 disparaissent pendant les 8 premiers jours, puis 210 du
  9e au 30e jour. Avec les enseignes : 377, puis 373.
- Deux reprises après le 8e jour, sans enseignes :
  - États-Unis, 13e et 14e jours : 36 et 30 suppressions pour 10 000 avis en ligne ;
  - Europe, du 19e au 21e jour : de 10 à 14 pour 10 000.
- Dès le 22e jour, le rythme passe sous 10 pour 10 000 par jour. Il est de 4 au 30e jour.

---

## Réserves

- Un avis publié le 12 juillet n'est vu qu'à partir du 11 août, à 30 jours. Les âges de 9 à
  43 jours reposent donc surtout sur des avis publiés avant l'arrivée du robot. Les âges de 1 à
  8 jours reposent sur des avis publiés à partir du 4 août.
- Les 4 chaînes ont perdu en deux jours, le 12 et le 17 août, 215 avis publiés avant le 4 août
  (`2_2_par_jour.csv`, colonne `dont_publies_avant_le_4_aout`). Elles gonflent les âges au-delà du 8e jour dans la version « tous ».
- La réserve sur les 14 jours de suivi est écrite au chapitre 1.
