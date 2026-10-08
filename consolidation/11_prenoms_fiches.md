# 11. Part de prénoms, vélocité et suppressions : fiches touchées en masse et fiches ordinaires

| Commande | CSV |
|---|---|
| `uv run python consolidation/11_prenoms_fiches.py` | `11_fiches.csv`, `11a_taux.csv`, `11a_croise.csv`, `11a_effets.csv`, `11b_reel_attendu.csv`, `11b_effets.csv`, `11c_effets.csv` |

Chiffres du 2026-10-08. Suite du point 10 et du mail d'Axel du 2026-10-07 : ne pas traiter de la même
façon les fiches touchées en masse (plus de 10 suppressions en 14 jours) et les autres.

- **Base :** `reviews_doublons_cleaned_all`, base complète nettoyée, 4 590 suppressions.
- **Prénoms :** marquage d'Axel, `reviews_name_enriched` (avis 4 et 5 étoiles avec texte), joint par
  `review_id` : 2 675 178 avis retrouvés dans notre base sur 2 675 519. L'état supprimé est le nôtre.
- **Fiches retenues :** au moins 20 avis 4 et 5 étoiles avec texte, comme chez Axel : 8 430 fiches,
  dont 97 touchées en masse (63 sans les chaînes ni les salles).
- **Part de prénoms :** part de ces avis qui citent un nom ; tranches d'Axel.
- **Vélocité :** avis publiés du 11 août 2025 au 10 août 2026, divisés par 12. Dans les modèles, elle
  entre en continu, effet lu pour 2 fois plus d'avis par mois.

Chiffres cités sans les chaînes ni les salles sauf mention ; les trois périmètres sont dans les CSV.

---

## A. Qui est touché en masse ? (`11a_taux.csv`, `11a_effets.csv`, `figures/11a_masse.png`)

Part des fiches touchées en masse, comptée directement, toutes les fiches :

| Part de prénoms | Fiches | Touchées en masse | % |
|---|---:|---:|---:|
| moins de 10 % | 3 808 | 6 | 0,2 % |
| 10 à 25 % | 2 006 | 6 | 0,3 % |
| 25 à 50 % | 1 410 | 23 | 1,6 % |
| 50 % et plus | 1 206 | 62 | 5,1 % |

| Vélocité, avis par mois | Fiches | Touchées en masse | % |
|---|---:|---:|---:|
| moins de 3 | 4 460 | 1 | 0,0 % |
| 3 à 7 | 1 821 | 4 | 0,2 % |
| 7 à 15 | 1 200 | 14 | 1,2 % |
| 15 et plus | 949 | 78 | 8,2 % |

À secteur, région, taille, nombre d'avis, habitude de réponse et part d'avis 1-2 étoiles égaux :

| | Sans la vélocité | Avec la vélocité |
|---|---|---|
| 25 à 50 % de prénoms, face à moins de 10 % | ×7,25 [1,83 à 28,7] | ×3,02 [0,77 à 11,9] |
| 50 % et plus de prénoms | ×8,06 [1,91 à 34,1] | ×2,84 [0,66 à 12,3] |
| 2 fois plus d'avis par mois | | ×2,56 [1,95 à 3,35] |

- Une fiche qui reçoit 2 fois plus d'avis par mois a 2,6 fois plus de chances d'être touchée en masse.
- Une fois la vélocité tenue égale, l'écart des fiches à 50 % de prénoms tombe de ×8 à ×3, et sa
  fourchette contient 1. Ce chiffre unique cache le croisement ci-dessous.

Croisement, sans les chaînes ni les salles (`11a_croise.csv`) : fiches touchées en masse / fiches.

| Part de prénoms | moins de 3 avis par mois | 3 à 7 | 7 à 15 | 15 et plus |
|---|---|---|---|---|
| moins de 10 % | 0 / 2 262 | 1 / 810 | 3 / 469 | 2 / 267 (0,7 %) |
| 10 à 25 % | 0 / 1 037 | 1 / 417 | 0 / 322 | 5 / 230 (2,2 %) |
| 25 à 50 % | 1 / 674 | 0 / 324 | 6 / 221 | 14 / 188 (7,4 %) |
| 50 % et plus | 0 / 482 | 1 / 267 | 3 / 173 | 26 / 194 (13,4 %) |

- Sous 7 avis par mois : 5 fiches touchées sur 8 273, quelle que soit la part de prénoms.
- À 15 avis par mois et plus : 0,7 % des fiches à moins de 10 % de prénoms, 13,4 % des fiches à 50 % et
  plus. Leur vélocité médiane est proche, 21 et 28 avis par mois.
- La vélocité est la condition : sans elle, presque aucune fiche n'est touchée. Parmi les fiches
  rapides, la part de prénoms sépare nettement les fiches touchées des autres.
- Seuil relatif (au moins 5 suppressions et plus de 5 % des avis récents, 87 fiches) : 50 % et plus
  de prénoms ×2,45 [0,83 à 7,23], vélocité ×2,04 [1,62 à 2,57]. Même lecture.

## B. Chez les fiches ordinaires (0 à 10 suppressions) (`11b_reel_attendu.csv`, `11b_effets.csv`, `figures/11b_ordinaires.png`)

Suppressions réelles face aux suppressions attendues si chaque avis avait le risque moyen de sa tranche
d'âge (publié pendant le suivi, moins de 30 jours, 30 à 90, 90 à 365, 1 à 3 ans, plus de 3 ans) :

| Part de prénoms | Fiches | Suppressions | Attendues | Réel / attendu |
|---|---:|---:|---:|---:|
| moins de 10 % | 3 802 | 594 | 762 | 0,78 |
| 10 à 25 % | 2 000 | 441 | 410 | 1,08 |
| 25 à 50 % | 1 386 | 345 | 290 | 1,19 |
| 50 % et plus | 1 086 | 390 | 308 | 1,27 |

| Vélocité, avis par mois | Réel / attendu |
|---|---:|
| moins de 3 | 1,15 |
| 3 à 7 | 1,13 |
| 7 à 15 | 0,90 |
| 15 et plus | 0,95 |

À secteur, région et taille égaux, 50 % et plus de prénoms face à moins de 10 % : ×1,47 [1,14 à 1,91]
sans la vélocité, ×1,68 [1,29 à 2,19] avec. 2 fois plus d'avis par mois : ×0,92 [0,89 à 0,95].

- Une fois l'âge des avis pris en compte, la vélocité ne fait pas perdre plus : les fiches rapides
  perdent même un peu moins que l'attendu.
- La part de prénoms garde un écart d'environ ×1,5, que la vélocité n'explique pas.

## C. Dans les fiches touchées en masse (`11c_effets.csv`, `figures/11c_avis_masse.png`)

Avis 4-5 étoiles avec texte : un avis qui cite un nom face à un avis sans nom, même fiche, même
tranche d'âge.

| Périmètre | Fiches | Avis avec nom (supprimés) | Avis sans nom (supprimés) | Écart brut | Même fiche, même âge |
|---|---:|---:|---:|---:|---|
| toutes les fiches | 97 | 107 516 (1 099) | 57 514 (676) | ×0,87 | ×1,01 [0,89 à 1,14] |
| sans les chaînes ni les salles | 63 | 36 261 (517) | 37 013 (459) | ×1,15 | ×1,05 [0,90 à 1,22] |

- Les suppressions en masse emportent les avis avec et sans nom au même rythme.

---

## Lecture d'ensemble

- **Être touché en masse** demande une forte vélocité : sous 7 avis par mois, presque aucune fiche ne
  l'est. Parmi les fiches à 15 avis par mois et plus, celles à 50 % de prénoms le sont 18 fois plus
  souvent que celles à moins de 10 % (13,4 % contre 0,7 %).
- **Chez les fiches ordinaires**, la vélocité n'explique rien une fois l'âge des avis pris en compte.
  La part de prénoms garde un écart d'environ ×1,5.
- **Au niveau de l'avis**, citer un nom ne change rien, y compris dans les fiches touchées en masse.

## Réserves

- Le seuil coupe les fiches selon le résultat : une fiche ordinaire ne peut pas dépasser 10
  suppressions. L'étape B mesure des écarts bornés par construction.
- 63 fiches touchées en masse hors chaînes et salles : les fourchettes de l'étape A sont larges.
- La vélocité et le stock d'avis récents sont comptés sur les avis encore en ligne au 11 août.
- Le marquage des prénoms est celui d'Axel : environ 7 % de noms manqués, 0,7 % de faux positifs
  selon son test.
- « Sans les chaînes » et « sans les chaînes ni les salles » sont identiques à l'étape B : les 2 salles
  sont touchées en masse et sortent des fiches ordinaires.
