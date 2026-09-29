# 5. Réponse du propriétaire, une ligne par avis et par jour

| Commande | CSV |
|---|---|
| `uv run python consolidation/5_reponse_jour_par_jour.py` (environ 20 secondes) | `5_effectifs.csv`, `5_effets.csv`, `5_fiches_par_case.csv` |

Chiffres du 2026-09-29. Panel 03B : avis publiés du 4 au 17 août 2026, sur les fiches dont
l'habitude de réponse est connue. 35 095 avis (18 860 mono + small, 16 235 large), suivis jour
par jour : 379 961 avis-jours, 1 349 suppressions sur 1 355 (`5_effectifs.csv`, lignes « total du
passage »).

## Le montage

- Chaque avis compte une ligne par jour où il pouvait disparaître, du lendemain de sa première
  observation jusqu'à sa disparition ou au 24 août.
- La réponse compte à partir du lendemain du jour où elle arrive. Exemple : un avis publié le
  12 août et répondu le 15 compte « sans réponse » les 13, 14 et 15 août, puis « réponse à
  3 jours » à partir du 16.
- Il n'y a plus de jalon : les avis supprimés avant le 3e jour restent dans le calcul, et les
  réponses à 3 jours et plus se mesurent.
- Chaque effet compare l'avis déjà répondu à l'avis du même âge encore sans réponse ce jour-là,
  sur des fiches de même habitude, à note et région égales.
- Règle de citation (`commun.py`) : au moins 20 suppressions, sur au moins 10 fiches, sans qu'une
  fiche en porte plus du quart.

---

## Résultats

### Fiches qui répondent à plus de 75 % : l'avis répondu disparaît 3 à 4 fois moins

| Réponse | Mono + small | Large, sans enseignes |
|---|---:|---:|
| le jour même | ×0,36 [0,20 à 0,63] — 2 772 avis, 80 suppressions, 36 fiches | ×0,24 [0,12 à 0,48] — 2 811 avis, 43 suppressions, 19 fiches |
| le lendemain | ×0,33 [0,18 à 0,60] — 1 972 avis, 44 suppressions, 22 fiches | ×0,23 [0,13 à 0,41] — 2 572 avis, 37 suppressions, 16 fiches |
| référence : pas encore de réponse | 3 026 avis, 137 suppressions, 56 fiches | 2 480 avis, 74 suppressions, 38 fiches |
| à 2 jours | ×0,23, 10 suppressions, non citable | ×0,24, 14 suppressions, non citable |
| à 3 jours et plus | ×0,11, 9 suppressions, non citable | ×0,22, 14 suppressions, non citable |

- Un avis répondu au 3e jour compte d'abord dans « pas encore de réponse », puis dans sa case de
  réponse : les avis d'une ligne à l'autre ne s'additionnent pas.
- Le jalon du 3b donnait ×0,41 et ×0,46 sur mono + small. Le calcul jour par jour donne ×0,36 et
  ×0,33 : même sens, même ordre de grandeur.
- Les réponses à 2 jours et à 3 jours et plus vont dans le même sens, sur trop peu de
  suppressions pour être citées.
- Sur les `large` avec les 4 chaînes, la réponse du jour même donne ×0,84 [0,50 à 1,40]. Les
  chaînes répondent le jour même et perdent beaucoup d'avis : 258 suppressions sur 49 fiches, dont
  215 sur les chaînes.
- **Contrôle mono seul, small seul** :
  - les small donnent ×0,26 (jour même) et ×0,27 (lendemain), citables ;
  - les mono donnent ×0,67 et ×0,46 sur 17 et 8 suppressions, non citables.
  - Le résultat mono + small vient des small.

### Fiches qui répondent à 75 % ou moins : aucun effet citable

- Mono + small, réponse le jour même : ×2,26 [0,75 à 6,84], sur 24 suppressions portées par
  6 fiches. Cedar Park Overhead Doors (cid `10505273405281271038`) en porte 18
  (`5_fiches_par_case.csv`).
- Small seul, réponse le jour même : ×3,76 [1,47 à 9,58], sur 22 suppressions portées par
  4 fiches, dont 18 pour Cedar Park.
- Dans la même fiche (4b), l'avis répondu de ces fiches ne disparaît pas plus : ×0,41 avec les
  enseignes, ×0,56 sans (non citable).
- **Hypothèse de Romain** : « la réponse d'un propriétaire qui ne répond pas régulièrement ne
  protège pas le score, voire augmente les risques de suppression ».
  - « Augmente les risques » : non établi. L'écart observé vient de Cedar Park.
  - « Ne protège pas » : non établi non plus. Aucun effet de la réponse n'est citable sur ces
    fiches au 5. Dans la même fiche (4b), l'avis répondu tombe moins : ×0,41 avec les enseignes,
    citable ; ×0,56 sans les enseignes, non citable.

### L'avis resté sans réponse sur une fiche qui répond à tout

- Sur une fiche qui répond à plus de 75 %, un avis encore sans réponse disparaît 2,5 fois plus
  que sur une fiche qui répond moins : ×2,53 [1,41 à 4,54] (mono + small). En large sans
  enseignes : ×2,19 [1,25 à 3,83].
- Au 3b, le même écart valait ×2,02.

### Les autres colonnes, pour mémoire (mono + small)

- Note 1 ou 2 étoiles : ×2,05 [1,32 à 3,17] face aux 5 étoiles.
- Fiche aux États-Unis : ×2,14 [1,26 à 3,64].
- Avis de 7 jours : ×7,39 [5,50 à 9,94] face aux avis de 9 à 13 jours.

---

## Réserves

- Une réponse retirée par le propriétaire est invisible : l'avis compte « sans réponse ».
- La réponse compte à partir du lendemain de sa date. Ce décalage d'un jour empêche qu'une réponse
  arrivée après la disparition compte comme une protection.
- L'habitude de la fiche est calculée sur ses seuls avis survivants de l'année précédente.
- Le sens de la cause reste ouvert : sur une fiche qui répond à tout, l'absence de réponse peut
  marquer un avis que le propriétaire conteste ou signale. Les données ne montrent pas les
  signalements.
- Les 95 fiches signalées sont toutes `large` : pour mono + small, « tous » et « sans enseignes »
  sont identiques.
- Le calcul a occupé plusieurs cœurs pendant 18 secondes. Au-delà de deux minutes, le lancer avec
  `nice -n 19`.
