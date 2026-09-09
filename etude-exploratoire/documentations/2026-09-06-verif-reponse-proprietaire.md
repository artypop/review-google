---
date: 2026-09-06
projet: reviewflowz-analyse-google
titre: "La réponse du patron protège-t-elle vraiment ?"
statut: résultats
---

# La réponse du patron protège-t-elle vraiment ?

> ## MIXTE — vérifié le 2026-09-08
>
> **Méthode, décisions et questions ouvertes : toujours valables.**
> **Chiffres de résultat : périmés**, calculés avant la correction du comptage. Dans ce
> document : 1 406 avis avec réponse, et tous les dénominateurs du périmètre 2 853.
>
> Comptage de référence aujourd'hui : **4 747 suppressions** sur 5 230 disparitions brutes.
> Résultats à jour : `2026-09-08-synthese-de-la-journee.md`. Inventaire : `INDEX.md`.

Produit par `scripts/verif_reponse_proprietaire.py`.

## Pourquoi cette vérification est indispensable

L'analyse B donne « avis avec réponse du propriétaire : 3,7 fois moins supprimé ». C'est le seul
levier que le client puisse actionner lui-même, donc le résultat le plus directement
exploitable de l'étude. Il faut être sûr avant de le recommander.

L'explication concurrente à écarter : dans les tables, la présence d'une réponse est enregistrée
telle qu'elle est au dernier passage du robot, puis recopiée sur tous les passages précédents.
Un avis supprimé au troisième jour n'a pas eu le temps de recevoir une réponse. Un avis qui
survit trois semaines en reçoit une. Si c'est le mécanisme dominant, « avoir une réponse » est
une conséquence de la survie et non une protection, et la recommandation est fausse.

## Résultats

<!-- genere:reponse — regenere par scripts/verif_reponse_proprietaire.py, ne pas editer a la main -->

### 1. Quand le patron répond-il ?

- 54 768 avis récents ont reçu une réponse.
- Délai médian entre l'avis et la réponse : **1 jours** (moitié des cas entre 0 et 2 jours).
- **78.1 %** des réponses arrivent dans les 2 jours, **93.0 %** dans les 7 jours.

Plus les réponses sont tardives, plus le risque que « avoir une réponse » signifie surtout « avoir survécu » est grand.

### 2. Chez les avis supprimés, la réponse est-elle arrivée avant ?

- 1 406 avis récents supprimés avaient une réponse.
- **1 406** l'avaient reçue **avant** la suppression.
- 0 l'ont reçue après la date de suppression détectée.

### 3. L'effet tient-il quand on date la réponse ?

| Façon de compter la réponse | Avis suivis | Disparitions | Sur 10 000 passages | Effet |
|---|---:|---:|---:|---:|
| réponse figée à l'état final (méthode actuelle) — **avec** réponse | 618 142 | 1 406 | 23.14 | ×0.86 |
| réponse figée à l'état final (méthode actuelle) — **sans** réponse | 519 134 | 1 447 | 26.89 | référence |
| réponse datée, comptée seulement une fois publiée — **avec** réponse | 601 363 | 1 406 | 24.08 | ×0.94 |
| réponse datée, comptée seulement une fois publiée — **sans** réponse | 535 913 | 1 447 | 25.69 | référence |

L'effet passe de ×0.86 à ×0.94 quand on ne compte la réponse qu'à partir du moment où elle existe réellement, soit un déplacement de +9 %.

<!-- /genere:reponse -->
