# Legacy — documents périmés de l'étude exploratoire

**Aucun chiffre de résultat de ce dossier ne doit être cité.** Ni dans un livrable, ni dans un
mail, ni dans une conversation avec Axel. Ces documents sont conservés pour leur méthode, leurs
pièges documentés et la trace du raisonnement, pas pour leurs nombres.

Ce dossier s'appelait `to-update/` jusqu'au 2026-09-09. Renommé parce que cinq de ses huit
documents ont été relancés ce jour-là : leurs versions à jour sont dans `documentations/`, et
les copies restées ici ne sont plus qu'un état antérieur.

## Pourquoi ces documents sont périmés

Deux corrections successives ont invalidé leurs chiffres.

**Le comptage des suppressions, corrigé le 2026-09-08.** `deleted_detected_at` seul ne dit pas
qu'un avis a été supprimé, seulement que le robot ne l'a plus retrouvé à un passage. Un avis
absent un seul jour est un raté de collecte. 24 avis au texte réécrit sont des bugs d'édition.
Définition retenue dans `../../scripts/suppressions_corrigees.py`.

**Le dédoublonnage de la table maîtresse, le 2026-09-09.** `WHERE NOT is_update` ne rend pas une
ligne par avis : 617 avis, ceux qui ont disparu puis sont revenus, ont plusieurs enregistrements
de base. Ce doublon gonflait la caractéristique « rafale d'auteur », qui lisait donc en partie la
suppression qu'on lui demandait de prédire.

Ces documents ont été produits avant l'une ou l'autre de ces corrections.

## Ce que chacun garde d'utile

| Document | Ce qui reste bon |
|---|---|
| `2026-09-06-enquete-fiches-purgees-et-plan.md` | Le raisonnement qui a fondé la correction du comptage : 7 artefacts de collecte démasqués par triple preuve, 2 salles de sport attaquées. |
| `2026-09-06-synthese-etat-et-resultats.md` | La liste « ce qu'il ne faut pas dire à Axel », garde-fou de communication. |
| `2026-09-04-...-premieres-observations-...md` | Les quatre pièges du jeu de données. |
| `2026-09-06-analyse-a-quel-etablissement.md` | Le piège central documenté : la vitesse de collecte mesurait une exposition, pas une sanction. **Version à jour dans `../`.** |
| `2026-09-06-analyse-b-quel-avis-tombe.md` | La méthode de comparaison intra-fiche, à fiche et jour identiques. **Version à jour dans `../`.** |
| `2026-09-06-controle-robustesse.md` | Le critère de verdict, fixé avant de regarder les chiffres. **Version à jour dans `../`.** |
| `2026-09-06-premiers-resultats-facteur-par-facteur.md` | Le seuil « trop peu pour conclure » à 20 disparitions. **Version à jour dans `../`.** |
| `2026-09-06-test2-debordement-organique.md` | Le protocole du Test 2. **Version à jour dans `../`.** |

Les trois premiers n'ont pas de script pour les régénérer : ils resteront périmés.
