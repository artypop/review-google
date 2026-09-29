# 2.2 Les deux phénomènes enregistrés par le corpus

| Commande | CSV |
|---|---|
| `uv run python consolidation/2_2_deux_phenomenes.py` | `2_2_resume.csv`, `2_2a_calendrier.csv`, `2_2b_delai.csv`, `2_2c_auteurs.csv` |

Chiffres du 2026-09-29. Base : `reviews_doublons_cleaned`, toutes dates de publication.
Suppressions constatées du 12 au 24 août 2026.

---

## Les 4 chaînes antiparasitaires américaines

### Combien (`2_2_resume.csv`)

- 93 fiches, 231 325 avis dans la base, 872 supprimés pendant le suivi.
- Ces chaînes portent 4,9 % des avis de la base et 22 % de ses 4 035 suppressions.
- 827 des 872 avis supprimés portent 5 étoiles (95 %). 19 portent 4 étoiles, 24 portent 1 étoile.

| Enseigne | Fiches | Avis | Supprimés | dont 5 étoiles |
|---|---:|---:|---:|---:|
| EcoShield Pest Solutions | 27 | 118 179 | 323 | 299 |
| Insight Pest Solutions | 21 | 22 012 | 273 | 261 |
| Pointe Pest Control | 20 | 53 868 | 171 | 163 |
| Bulwark Exterminating | 25 | 37 266 | 105 | 104 |

### Quand (`2_2a_calendrier.csv`, `2_2b_delai.csv`)

Deux mouvements distincts (`2_2_par_jour.csv`) :
- 467 avis publiés depuis le 4 août, supprimés au fil des jours, surtout 6 ou 7 jours après leur
  publication ;
- 405 avis publiés avant le 4 août, dont 215 supprimés en deux jours : 106 le 12 août, 109 le
  17 août.

Délai entre publication et suppression, sur les 872 :

| Délai | Avis supprimés |
|---|---:|
| 1 à 5 jours | 30 |
| 6 ou 7 jours | 290 |
| 8 à 30 jours | 322 |
| plus de 30 jours | 230 |

- Le 7e jour seul compte 187 suppressions, le 6e 103.
- « Supprimés au bout d'une semaine » décrit 290 avis sur 872 (33 %).

### Qui les a écrits (`2_2c_auteurs.csv`)

Avis publiés de J-30 à J+13 sur les 4 chaînes : 653 supprimés, 5 762 conservés.

| Profil de l'auteur | Supprimés | Conservés |
|---|---:|---:|
| Local Guide niveau 1 à 3 | 77 % | 79 % |
| Local Guide niveau 4 et plus | 15 % | 16 % |
| sans niveau Local Guide | 8 % | 5 % |
| aucune photo sur son profil | 77 % | 74 % |
| un seul avis déclaré | 28 % | 27 % |
| 4 avis ou plus le même jour sur le panel | 8 % (52 avis) | 0,3 % (16 avis) |

- Les auteurs supprimés ressemblent aux auteurs conservés, sauf les 52 avis publiés par des
  auteurs à 4 avis ou plus dans la journée.
- Sur les autres fiches américaines, les supprimés s'écartent davantage des conservés : 13 % sans
  niveau Local Guide contre 5 %, 36 % à un seul avis déclaré contre 25 %.
- Au dernier passage où l'avis est vu, 56 % des supprimés des chaînes ont une réponse du
  propriétaire, contre 36 % des conservés.

---

## Les 2 salles de sport espagnoles

### Combien (`2_2_resume.csv`)

- 2 fiches, 1 399 avis dans la base, 329 supprimés : 24 % de leurs avis.
- 317 à 1 étoile, 10 à 2 étoiles, 2 à 5 étoiles.
- Elles portent 0,03 % des avis de la base et 8 % de ses suppressions.

### Quand (`2_2a_calendrier.csv`, `2_2b_delai.csv`)

- 295 des avis supprimés ont été publiés en deux jours : 160 le 1er août, 135 le 2 août
  (`2_2_par_jour.csv`, colonne `supprimes_publies_ce_jour`).
- Suppressions en trois vagues : 74 le 12 août, 151 le 16 août, 83 les 22 et 23 août
  (`2_2_par_jour.csv`, colonne `supprimes_ce_jour`).
- 327 suppressions tombent entre 9 et 22 jours après la publication. Aucune avant le 9e jour.

### Qui les a écrits (`2_2c_auteurs.csv`)

Les 327 avis supprimés publiés de J-30 à J+13, comparés aux avis conservés des autres fiches
européennes :

| Profil de l'auteur | Supprimés des salles | Conservés, autres fiches Europe |
|---|---:|---:|
| un seul avis déclaré | 73 % | 24 % |
| sans niveau Local Guide | 24 % | 4 % |
| aucune photo sur son profil | 83 % | 51 % |

- Au dernier passage où l'avis est vu, 224 des 327 (69 %) ont une réponse du propriétaire.

---

## Réserves

- Le secteur, au chapitre 1 : les services à domicile américains passent de 28,6 à 21,3
  suppressions pour 10 000 avis sans les 4 chaînes, le sport européen de 17,1 à 6,5 sans les
  2 salles (`1c_suppressions_secteur_region.csv`). Les deux groupes expliquent une partie du
  classement des secteurs.
- La réponse du propriétaire est lue au dernier passage où l'avis est vu. Une réponse retirée
  est invisible.
- Les données ne disent pas qui a demandé les suppressions. Pour les salles, la demande du
  propriétaire reste une hypothèse.
- La base écarte les avis modifiés plus d'un an après leur publication (chapitre 1). 322 avis
  supprimés des 4 chaînes, dont 316 à 5 étoiles, sortent ainsi du décompte : avec eux, les
  chaînes perdraient 1 194 avis. Le décompte actuel en retient 872
  (`1b_retires_365_jours_par_fiche.csv`, fiches où `enseigne_signalee` vaut vrai).
- Les 4 chaînes sont repérées sur leur nom exact : une dizaine de succursales au nom suivi d'une
  ville restent hors du groupe.
