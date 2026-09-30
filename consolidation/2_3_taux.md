# 2.3 Taux de suppression par caractéristique

| Commande | CSV |
|---|---|
| `uv run python consolidation/2_3_taux.py` | `2_3_<caractéristique>.csv`, 11 fichiers |

Chiffres du 2026-09-29. Table : `reviews_panel_features_03B`, les 35 751 avis publiés du 4 au
17 août 2026 (J-7 à J+6), dont 1 355 disparus du 12 au 24 août. Un calcul direct : pour chaque
modalité, les avis et ceux qui ont disparu.

Lecture d'une case : « aux États-Unis, sur 10 000 avis 1 étoile du panel, 842 ont disparu ».

Chaque case ci-dessous donne deux nombres : tous / sans enseignes. Ce sont des suppressions pour
10 000 avis.

---

## Le panel

| | Avis | Supprimés | Pour 10 000 |
|---|---:|---:|---:|
| US | 19 928 | 1 050 | 527 |
| US, sans enseignes | 17 625 | 598 | 339 |
| Europe | 15 823 | 305 | 193 |
| Europe, sans enseignes | 15 799 | 282 | 178 |

## Résultats

### Note (`2_3_note.csv`)

| Note | US | Europe |
|---|---:|---:|
| 1 étoile | 842 / 807 | 631 / 514 |
| 2 étoiles | 444 / 421 | 324 / 207 |
| 3 étoiles | 164 / 142 | 72 / 72 |
| 4 étoiles | 288 / 166 | 88 / 88 |
| 5 étoiles | 529 / 320 | 163 / 163 |

- Aux États-Unis, l'avis 5 étoiles disparaît plus souvent que l'avis 3 ou 4 étoiles, avec ou
  sans les chaînes.
- Des deux côtés, l'avis 1 étoile est le plus touché.

### Niveau Local Guide (`2_3_local_guide.csv`)

Paliers décidés le 2026-09-29, appliqués ici le 2026-09-30 : sans niveau / 1 à 4 / 5 et plus.

| | US | Europe |
|---|---:|---:|
| sans niveau | 777 / 634 | 601 / 551 |
| niveau 1 à 4 | 570 / 350 | 192 / 177 |
| niveau 5 et plus | 198 / 139 | 97 / 93 |

- Sans niveau, l'avis disparaît 1,8 fois plus qu'au niveau 1 à 4 aux États-Unis (sans
  enseignes), 3,1 fois plus en Europe.
- Au niveau 5 et plus, l'avis disparaît 2,5 fois moins qu'au niveau 1 à 4 aux États-Unis (sans
  enseignes), 1,9 fois moins en Europe.

### Photo jointe à l'avis (`2_3_photo_jointe.csv`)

| | US | Europe |
|---|---:|---:|
| avec photo | 280 / 265 | 186 / 186 |
| sans photo | 547 / 346 | 194 / 178 |

### Texte (`2_3_texte.csv`, `2_3_longueur_texte.csv`)

| | US | Europe |
|---|---:|---:|
| avec texte | 514 / 348 | 216 / 211 |
| sans texte | 568 / 311 | 140 / 106 |
| 1 à 50 caractères | 517 / 329 | 185 / 175 |
| 51 à 200 caractères | 502 / 317 | 204 / 197 |
| plus de 200 caractères | 531 / 403 | 240 / 238 |

- En Europe, un avis avec texte disparaît 2 fois plus qu'un avis sans texte (sans enseignes).

### Photos publiées par l'auteur sur son profil (`2_3_photos_auteur.csv`)

| | US | Europe |
|---|---:|---:|
| 0 photo | 611 / 397 | 233 / 211 |
| 1 à 5 | 497 / 304 | 221 / 212 |
| 6 à 20 | 374 / 272 | 130 / 125 |
| 21 à 100 | 65 / 68 | 89 / 83 |
| plus de 100 | 98 / 72 | 69 / 69 |

- Au-delà de 20 photos, l'avis disparaît 5,5 à 6 fois moins qu'un avis d'auteur sans photo
  aux États-Unis, 2,5 à 3 fois moins en Europe (sans enseignes).

### Nombre d'avis déclarés par l'auteur (`2_3_avis_auteur.csv`)

| | US | Europe |
|---|---:|---:|
| 1 avis | 608 / 441 | 323 / 287 |
| 2 à 5 | 533 / 329 | 169 / 161 |
| 6 à 20 | 607 / 349 | 149 / 144 |
| 21 à 100 | 247 / 164 | 119 / 112 |
| plus de 100 | 152 / 128 | 91 / 91 |

### Secteur (`2_3_secteur.csv`)

| | US | Europe |
|---|---:|---:|
| Services à domicile | 1 175 / 600 | 396 / 396 |
| Sport et bien-être | 532 / 532 | 293 / 193 |
| Santé | 421 / 421 | 68 / 68 |
| Voyage | 322 / 322 | 208 / 208 |
| Automobile | 272 / 272 | 216 / 216 |
| Restauration | 163 / 163 | 143 / 143 |
| Hôtellerie | 124 / 124 | 165 / 165 |

### Taille de l'entreprise (`2_3_taille.csv`)

| | US | Europe |
|---|---:|---:|
| mono (1 établissement) | 235 / 235 | 201 / 201 |
| small (4 à 10) | 529 / 529 | 166 / 166 |
| large (20 à 50) | 646 / 259 | 212 / 176 |

- Les 95 fiches signalées sont toutes `large` : mono et small ne changent pas sans elles.

### Habitude de réponse de la fiche (`2_3_habitude_reponse_fiche.csv`)

Part des avis de la fiche, publiés du 11/08/2025 au 03/08/2026, qui avaient une réponse avant le
11 août.

| | US | Europe |
|---|---:|---:|
| répond à 25 % ou moins | 637 / 398 | 185 / 185 |
| répond à 25-75 % | 430 / 408 | 190 / 133 |
| répond à plus de 75 % | 499 / 305 | 210 / 210 |
| moins de 10 avis d'historique | 187 / 150 | 27 / 27 |

### Avis publiés sur la fiche le même jour (`2_3_avis_sur_la_fiche_le_meme_jour.csv`)

| | US | Europe |
|---|---:|---:|
| seul avis du jour | 311 / 227 | 140 / 137 |
| 2 à 4 avis ce jour-là | 618 / 419 | 150 / 150 |
| 5 à 9 | 793 / 496 | 362 / 335 |
| 10 et plus | 482 / 262 | 444 / 297 |

- Une grosse fiche reçoit plus d'avis par jour : cette colonne suit aussi la taille de la fiche.

---

## Réserves

- **Un taux direct compte tout ce qui accompagne la caractéristique.** Aux États-Unis, 529 avis
  5 étoiles sur 10 000 disparaissent, et 320 une fois les 4 chaînes retirées. Les chaînes ont
  beaucoup d'avis 5 étoiles et en perdent beaucoup : le taux « 5 étoiles » mesure en partie
  « être chez une des chaînes ». Le même mélange existe entre toutes les caractéristiques : si
  les avis 1 étoile viennent plus souvent d'auteurs sans niveau Local Guide, le taux « sans
  niveau » contient une partie de l'effet « 1 étoile ». La régression séparera les deux.
- Chaque CSV donne les « fiches touchées » : le nombre de fiches différentes qui portent les
  suppressions d'une case. Quelques cases reposent sur moins de 10 suppressions, par exemple les
  3 étoiles (5 et 6) ou la santé en Europe (9).
- Les caractéristiques de l'auteur sont celles lues par le robot au dernier passage où l'avis
  est vu.
- En attente : la mention d'un prénom dans le texte, quand la liste de prénoms sera prête.
