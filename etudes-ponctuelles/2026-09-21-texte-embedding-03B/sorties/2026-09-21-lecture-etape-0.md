# Etape 0 : ce que porte le texte du panel 03B

Date : 2026-09-21. Produit par `00_effectifs.py`, sur la copie locale de
`client-divers.reviewflowz.03B_reviews_panel_filtered_08_04_to_08_26`.
Regenerable par : `.venv/Scripts/python.exe etudes-ponctuelles/2026-09-21-texte-embedding-03B/00_effectifs.py`

Aucun embedding lance. Ce document dimensionne l'etape suivante.

---

## 1. Combien d'avis entrent dans l'etude texte

Fichier `2026-09-21-A1-effectifs-textes.csv`.

| | avis du panel | dont avec texte | part |
|---|---|---|---|
| restes en ligne | 34 396 | 25 147 | 73,1 % |
| supprimes | 1 355 | 1 021 | 75,4 % |
| **total** | **35 751** | **26 168** | **73,2 %** |

Sans les deux salles de sport et les quatre chaines antiparasitaires :

| | avis du panel | dont avec texte | part |
|---|---|---|---|
| restes en ligne | 32 211 | 23 600 | 73,3 % |
| supprimes | 871 | 698 | 80,1 % |
| **total** | **33 082** | **24 298** | **73,4 %** |

Les 26 168 avis avec texte se repartissent sur 4 971 fiches et 26 058 auteurs.
Un auteur depose donc au plus un ou deux avis dans ce panel : la mise de cote
par auteur, pour la route C, ne coutera presque rien.

## 2. Les avis supprimes ne sont pas plus souvent sans texte

Sur ce panel, 24,6 % des avis supprimes n'ont pas de texte, contre 26,9 % des
avis restes en ligne. Une fois les six enseignes retirees, l'ecart se creuse
dans le meme sens : 19,9 % des supprimes sans texte, contre 26,7 % des autres.

La ligne L5 du backlog, « pourquoi 30 % des avis supprimes n'ont aucun texte »,
porte sur le panel `02` et `03`, qui compte 225 757 avis publies dans les
90 jours avant le 11 aout. Elle ne se transpose pas ici. Sur le panel `03B`,
un avis supprime porte un texte un peu plus souvent que la moyenne.

## 3. Le poids des six enseignes dans la population texte

Fichier `2026-09-21-A5-enseignes.csv`.

| groupe | fiches | avis | avec texte | supprimes | part supprimee sur les textes |
|---|---|---|---|---|---|
| reste du panel | 5 470 | 33 082 | 24 298 | 871 | 2,87 % |
| chaines antiparasitaires US | 94 | 2 645 | 1 863 | 461 | 17,02 % |
| salles de sport attaquees | 2 | 24 | 7 | 23 | 85,71 % |

Deux conclusions pour la suite.

**Les chaines antiparasitaires portent 461 des 1 355 suppressions du panel,
soit une sur trois, pour 7,1 % des avis qui ont un texte.** Elles vont
dominer tout regroupement. Chaque route doit sortir en deux versions.

**Les salles de sport attaquees ne comptent pas dans cette etude.** Elles
portent 24 avis, dont 7 avec texte. Les retirer ou les garder ne changera
aucun chiffre de l'analyse texte.

Le drapeau du projet repere sur le nom exact et attrape 85 fiches. Il laisse
passer 10 succursales nommees « EcoShield Pest Solutions Houston », « Bulwark
Exterminating Corporate » et ainsi de suite, qui portent 342 avis et
9 suppressions. Pour cette etude, le repere se fait sur le debut du nom et
attrape les 95 fiches ; le drapeau du projet n'est pas modifie. 66 autres
fiches de traitement antiparasitaire, hors de ces quatre enseignes, restent
en dehors.

## 4. Les cases exploitables pour une comparaison a note fixee

Fichier `2026-09-21-A6-cases-note-langue.csv`. Comptage des avis supprimes qui
portent un texte, dans chaque case note x langue, hors les six enseignes.

| note | langue | supprimes avec texte | restes avec texte |
|---|---|---|---|
| 5 | anglais | 373 | 11 669 |
| 1 | anglais | 89 | 1 025 |
| 5 | francais | 41 | 2 155 |
| 5 | allemand | 37 | 1 511 |
| 5 | espagnol | 27 | 959 |
| 1 | francais | 24 | 298 |
| 4 | anglais | 15 | 723 |
| toutes les autres cases | | moins de 13 | |

**Deux cases seulement portent assez d'avis supprimes pour une comparaison
solide** : 5 etoiles en anglais, et 1 etoile en anglais. Sur le panel complet,
elles montent a 668 et 101 supprimes.

Une troisieme case est possible en rassemblant les avis 5 etoiles qui ne sont
pas en anglais : 127 supprimes contre 6 567 restes. Le modele choisi aligne
les langues dans le meme espace, donc ce regroupement se defend. Il demande
de verifier que la composition par langue est la meme des deux cotes, sans
quoi on mesurerait la langue.

Les notes 2 et 3 sortent du champ : 23 et 9 avis supprimes en tout.

## 5. La longueur des textes

Fichier `2026-09-21-A4-longueurs.csv`, hors les six enseignes.

| | restes en ligne | supprimes |
|---|---|---|
| moyenne | 267 caracteres, 46 mots | 322 caracteres, 56 mots |
| mediane | 138 caracteres, 24 mots | 157 caracteres, 27 mots |
| 9 avis sur 10 sous | 619 caracteres, 108 mots | 763 caracteres, 133 mots |
| le plus long | 4 085 caracteres, 771 mots | 3 351 caracteres, 587 mots |

**Les textes supprimes sont plus longs.** L'ecart est visible sur les quatre
mesures et n'a besoin d'aucun embedding pour etre constate. Il devient une
reserve pour la suite : un modele de texte separe naturellement un texte long
d'un texte court, donc une partie de ce qu'il trouvera sera cette difference
de longueur. La longueur doit figurer dans la lecture de chaque groupe.

Consequence sur le parametrage : un avis median tient en 24 mots, environ
40 fragments pour un modele multilingue. Un avis sur dix depasse 108 mots,
environ 170 fragments. Couper a 256 fragments tronquerait environ trois avis
sur cent, et plus souvent du cote des supprimes, qui sont plus longs. Garder
la longueur maximale du modele, 512 fragments, evite d'introduire cette
difference de traitement. Le cout est faible : les lots sont constitues par
longueur croissante, donc les textes courts ne sont pas payes au prix des
longs.

## 6. Les langues

Fichier `2026-09-21-A3-par-langue.csv`. Sur les 26 168 avis avec texte :
anglais 16 407, francais 3 143, allemand 2 229, espagnol 1 457, italien 843,
neerlandais 676, polonais 314. Les 31 autres langues totalisent moins de
1 100 avis.

**37 % des textes ne sont pas en anglais.** Un modele anglophone est exclu.

---

## Ce qui est confirme pour l'etape 1

- population a encoder : 26 168 textes, dont 24 298 hors les six enseignes
- modele multilingue obligatoire
- comparaison note par note, sur les deux cases anglaises et la case des
  5 etoiles non anglaises
- longueur maximale a 512 fragments
- deux versions de chaque sortie, avec et sans les six enseignes

## Ce qui a ete tranche le 2026-09-21

1. **Route C reportee.** Le modele nourri des seuls vecteurs repose sur
   698 avis supprimes hors enseignes, mis de cote par fiche et par auteur,
   soit environ 140 avis supprimes au jeu d'essai. La marge serait large.
   Decrite dans la rubrique « pour aller plus loin » du document Word.
2. **Route D reportee.** La recherche de textes proches figure dans la liste
   « ecarte, a ne pas reproposer sans element nouveau » du backlog, sous le
   nom « recherche de textes identiques ». L'element nouveau a soumettre a
   Romain est que les chaines antiparasitaires portent une suppression sur
   trois du panel. Decrite elle aussi dans « pour aller plus loin ».
3. **Reperage des chaines elargi pour cette etude.** Le repere se fait sur le
   debut du nom, ce qui attrape 95 fiches au lieu de 85. L'ecart porte
   342 avis et 9 suppressions. Le drapeau du projet reste inchange.

Restent donc au programme les routes A, le regroupement des textes, et B, la
comparaison des deux populations a note egale.
