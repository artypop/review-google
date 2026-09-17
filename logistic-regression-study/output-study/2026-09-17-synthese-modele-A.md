# Ce qui fait supprimer un avis Google dans ses 8 premiers jours

Synthèse du 2026-09-17. Pour Axel et Romain. À valider par Romain avant diffusion.

**Population** : avis publiés du 10 au 16 août 2026 sur les fiches suivies.

| | Avis | Supprimés dans leurs 8 premiers jours |
|---|---|---|
| États-Unis, sans les quatre chaînes antiparasitaires | 8 800 | 293 |
| Europe | 7 731 | 152 |

Les deux salles de sport espagnoles n'ont aucun avis sur cette période. Les 56 avis supprimés après leur 8e jour sont retirés du calcul.

**Lecture des chiffres** : chaque effet compare deux avis identiques sur tout le reste, qui ne diffèrent que par la caractéristique citée.

Table : `reviews_panel_features_03`.
Commande : `nice -n 19 .venv/bin/python logistic-regression-study/python/10_modele_A_8_premiers_jours.py`.
Fichiers : `output-study/2026-09-17-sorties-10/`.

---

## Résultats

**1. Un avis 1 étoile est supprimé environ trois fois plus souvent qu'un avis 5 étoiles.**
- États-Unis : ×3,2 (entre ×1,9 et ×5,4). En chiffres bruts, 966 suppressions pour 10 000 avis 1 étoile, contre 295 pour 10 000 avis 5 étoiles.
- Europe : ×3,0 (entre ×1,6 et ×5,4). En chiffres bruts, 513 contre 179 pour 10 000 avis.

**La composition des suppressions est tout autre**, puisque les avis 5 étoiles sont les plus nombreux : aux États-Unis, 54 des 293 suppressions portent sur des avis 1 étoile (18 %) et 220 sur des avis 5 étoiles (75 %) ; en Europe, 32 des 152 (21 %) et 96 (63 %).

Ligne `etoiles_1` de `10_effets_US_sans_enseignes.csv` et `10_effets_Europe.csv` ; lignes `etoiles` des croisements.

**2. Un auteur sans niveau Local Guide voit ses avis supprimés deux à trois fois plus souvent qu'un guide de niveau 1 à 3.**
- États-Unis : ×2,2 (entre ×1,5 et ×3,2).
- Europe : ×2,9 (entre ×1,7 et ×5,1).
- En chiffres bruts, aux États-Unis : 705 suppressions pour 10 000 avis d'auteurs sans niveau, 325 pour les niveaux 1 à 3.

Ligne `guide_sans_niveau` ; lignes `profil` de `10_croisements_*.csv`.

**3. En Europe, un avis avec du texte est supprimé plus de deux fois plus souvent qu'un avis sans texte.**
- De 1 à 50 caractères : ×2,2 (entre ×1,1 et ×4,5).
- De 51 à 200 caractères : ×2,5 (entre ×1,2 et ×5,3).
- Plus de 200 caractères : ×2,2 (entre ×1,3 et ×3,8).
- En chiffres bruts : 93 suppressions pour 10 000 avis sans texte, 219 à 248 avec texte.
- Aux États-Unis, la longueur du texte ne joue pas.

Lignes `texte_*`.

**4. Aux États-Unis, un avis publié un jour où la fiche reçoit beaucoup d'avis est moins souvent supprimé.**
- Un jour à 5 fois le rythme habituel de la fiche, contre un jour normal : ×0,74.
- En Europe, la tendance va en sens inverse, mais l'écart est trop faible pour conclure.

Ligne `log_ratio_pic_journalier_fiche`.

**Ce que vaut le modèle.** Chaque fiche est notée par un modèle qui ne l'a jamais vue :

| | 10 % des avis jugés les plus risqués contiennent | Suppressions annoncées / constatées |
|---|---|---|
| États-Unis sans les chaînes | 23 % des suppressions | 288 / 283 |
| Europe | 26 % des suppressions | 147 / 146 |

- Le modèle annonce le bon nombre total de suppressions, mais il repère mal les avis à risque.
- Aux États-Unis, les deux dixièmes d'avis qu'il juge les moins risqués contiennent 50 suppressions, là où il en annonce 21.
- Ces huit caractéristiques n'expliquent qu'une petite partie des suppressions des premiers jours.

Fichiers : `10_ciblage_*.png`, `10_justesse_*.csv`.

---

## Réserves

- **Les photos de l'auteur vont dans le sens attendu, sans que l'effet soit net une fois le reste pris en compte.**
  - En chiffres bruts, les avis d'auteurs à plus de 100 photos sont peu supprimés : 89 pour 10 000 aux États-Unis contre 372 sans photo ; en Europe, 2 suppressions sur 579 avis.
  - Dans le modèle, l'effet reste en limite : ×0,89 (entre ×0,77 et ×1,02) aux États-Unis, ×0,85 (entre ×0,71 et ×1,00) en Europe, pour chaque multiplication par 2,7 du nombre de photos plus un.
  - Les photos et le nombre d'avis de l'auteur mesurent la même activité. Depuis l'ajout des photos, le nombre d'avis n'a plus d'effet net aux États-Unis, alors qu'il en avait un dans la version précédente de cette synthèse.
- **Le palier Local Guide 4 et plus ne protège pas.**
  - En chiffres bruts, ces auteurs sont moins supprimés en Europe : 146 pour 10 000 contre 179 pour les niveaux 1 à 3.
  - À photos et nombre d'avis égaux, ils le sont plus : ×1,8 (entre ×1,02 et ×3,1). La limite basse touche presque 1.
- **Plusieurs avis publiés le même jour par le même auteur** sont plus souvent supprimés, mais cela ne concerne que 55 avis aux États-Unis et 72 en Europe. L'ampleur de l'effet ne se mesure pas.
- **Les quatre chaînes antiparasitaires américaines changent les résultats.** Avec elles :
  - l'avis 1 étoile passe à ×2,0 ;
  - les photos de l'auteur deviennent nettes (×0,82, entre ×0,73 et ×0,91) ;
  - le repérage des avis à risque tombe à 13 %.
- **Les avis 3 étoiles ne sont pas mesurés** : 3 suppressions dans chaque région.
- **La période est courte**, 7 jours de publication. Les avis publiés du 7 au 9 août sont écartés : la moitié des suppressions de ceux du 7 août tombent après leur 8e jour.
- **La réponse du propriétaire n'est pas dans ce modèle.** Un avis supprimé le lendemain n'a pas eu le temps d'en recevoir une. Elle est traitée à part : répondre dans les 2 jours divise le risque par 1,8, hors des quatre chaînes (`docs/03-resultats.md` § 3).
- **Le niveau, les photos et le nombre d'avis de l'auteur** sont relevés au dernier passage du robot, jusqu'à 14 jours après la publication.
- **Les données ne disent pas pourquoi un avis est supprimé.** Google ne signale rien.
