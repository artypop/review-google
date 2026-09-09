---
date: 2026-09-06
projet: reviewflowz-analyse-google
titre: "Le texte des avis supprimés a-t-il une cause visible ?"
statut: résultats
---

# Le texte des avis supprimés a-t-il une cause visible ?

> ## MIXTE — vérifié le 2026-09-08
>
> **Méthode, décisions et questions ouvertes : toujours valables.**
> **Chiffres de résultat : périmés**, calculés avant la correction du comptage. Dans ce
> document : 2 853 avis frais supprimés comme dénominateur, et les 845 (29,6 %) sans texte qui en découlent.
>
> Comptage de référence aujourd'hui : **4 747 suppressions** sur 5 230 disparitions brutes.
> Résultats à jour : `2026-09-08-synthese-de-la-journee.md`. Inventaire : `INDEX.md`.

Produit par `scripts/verif_texte.py`.

## Pourquoi cette vérification passe avant les modèles

Toute l'étude repose sur une hypothèse non vérifiée jusqu'ici : que les avis supprimés par
Google ne sont pas, dans leur masse, des insultes, du spam ou du charabia. Si c'était le cas,
il n'y aurait pas de faux positifs à mesurer — juste une modération qui fonctionne.

Onze marqueurs, calculés par expression régulière, sans modèle et sans apprentissage. Chacun
est un motif de suppression légitime et évident.

## Ce que la mesure ne dit pas

- Le lexique d'obscénités couvre EN, FR, DE, ES, IT, NL, PT. Le panel compte 41 pays : le grec
  et le polonais notamment ne sont pas couverts. Le taux affiché est un **plancher**.
- Un marqueur n'est pas une preuve de faute. Un avis contenant un numéro de téléphone peut être
  parfaitement légitime.
- L'inverse est plus important : **l'absence de marqueur n'est pas une preuve d'innocence.** Un
  faux avis bien écrit n'en porte aucun. Ce test borne la part des suppressions qui ont une
  explication évidente ; il ne prouve pas que le reste est un faux positif.

## Protection des données

Le script lit `text` mais n'en écrit jamais rien : `data/build/text_flags.parquet` ne contient
que l'identifiant de ligne et des booléens.

## Résultats

<!-- genere:veriftexte — regenere par scripts/verif_texte.py, ne pas editer a la main -->

### Combien d'avis supprimés portent un marqueur visible

Sur **2 853 avis frais supprimés** :

- **6.3 %** portent au moins un des onze marqueurs ;
- contre **5.0 %** des avis frais survivants ;
- 845 (29.6 %) n'ont aucun texte du tout : une note seule, sur laquelle aucun marqueur ne peut se prononcer.

### Marqueur par marqueur

| Marqueur | Part des supprimés | Part des survivants | Risque ×, à âge comparable | Sans les 24 fiches purgées |
|---|---:|---:|---:|---:|
| Insulte ou obscénité (lexique 7 langues) | 1.02 % | 0.59 % | ×1.75 | ×2.19 |
| Contient un lien web | 0.00 % | 0.05 % | aucune suppression | aucune suppression |
| Contient une adresse e-mail | 0.00 % | 0.00 % | aucune suppression | aucune suppression |
| Contient un numéro de téléphone | 0.04 % | 0.01 % | ×3.52 | ×4.53 |
| Écrit intégralement en majuscules (plus de 15 caractères) | 0.11 % | 0.09 % | ×1.25 | ×1.15 |
| Ponctuation excessive (!!! ou ???) | 3.26 % | 2.62 % | ×1.27 | ×1.49 |
| Caractère répété cinq fois ou plus | 0.18 % | 0.09 % | ×1.83 | ×1.87 |
| Texte présent mais de moins de 10 caractères | 1.23 % | 0.89 % | ×1.38 | ×1.32 |
| Aucune voyelle sur au moins 12 caractères (charabia) | 0.00 % | 0.00 % | — | — |
| Moins d'un tiers de lettres (émojis, symboles, chiffres) | 0.63 % | 0.66 % | ×1.00 | ×0.89 |
| Vocabulaire promotionnel ou de sollicitation | 0.18 % | 0.16 % | ×1.10 | ×1.45 |
| Au moins un marqueur | 6.31 % | 4.96 % | ×1.31 | ×1.45 |

« Part des supprimés » = parmi les avis frais supprimés, combien portent ce marqueur. « Risque × » = combien de fois plus un avis porteur disparaît à chaque passage, à âge comparable, qu'un avis non porteur.

<!-- /genere:veriftexte -->

## Ce qu'il faut en retenir

**93,7 % des avis frais supprimés ne portent aucun marqueur visible de faute.** C'est le
chiffre à mettre au livrable. La modération de Google, sur ce panel, ne s'exerce pas
majoritairement sur des insultes, du spam ou du charabia.

Le détail conforte cette lecture plutôt qu'il ne la nuance :

- **L'obscénité concerne 1,02 % des avis supprimés.** Le risque est bien plus élevé pour un avis
  qui en contient (×1,75, et ×2,19 hors fiches purgées) — donc Google y réagit, ce qui valide
  au passage que le marqueur mesure quelque chose de réel. Mais l'effectif est dérisoire :
  cette réaction n'explique presque rien du volume supprimé.
- **Le spam publicitaire est absent.** Zéro suppression parmi les avis contenant un lien web,
  zéro parmi ceux contenant une adresse e-mail, alors que ces avis existent dans le panel. Si
  Google filtre ce type de contenu, il le fait avant publication — hors de portée de ce panel,
  comme la réserve du livrable l'indique déjà.
- **Le charabia n'existe pas** dans les données : aucun avis sans voyelle sur douze caractères
  ou plus, ni supprimé ni survivant.
- **Le seul effectif notable est ailleurs** : 29,6 % des avis supprimés n'ont pas de texte du
  tout. Ce sont des notes seules, sur lesquelles aucune faute textuelle ne peut être reprochée.

Le marqueur composite « au moins un marqueur » passe de ×1,31 à ×1,45 quand on retire les
24 fiches massivement purgées : l'écart n'est donc pas un artefact de ces fiches.

**Réserve à porter au livrable.** Ce test borne la part des suppressions ayant une explication
textuelle **évidente**. Il ne prouve pas que les 93,7 % restants sont des faux positifs : un
faux avis bien rédigé ne porte aucun marqueur. Ce qu'il établit, c'est que l'hypothèse
« Google supprime surtout des avis manifestement fautifs » est fausse sur ce panel, et que
l'étude a donc un sujet.
