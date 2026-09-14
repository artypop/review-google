# Étude exploratoire — dossier gelé le 2026-09-14

**Ne rien relancer ici. Ne rien y écrire. Ne citer aucun chiffre de ce dossier sans passer par
`../docs/`.**

Si vous arrivez sur le projet, lisez d'abord [`../docs/00-brief-equipe.md`](../docs/00-brief-equipe.md),
dont la section 3 explique ce que ce dossier a été et pourquoi il est gelé.

---

## Ce que ce dossier a été

Le premier travail du projet, du 4 au 9 septembre 2026. Il a servi à trois choses :

1. **comprendre les données** — ce que le robot voit, ce qu'il rate, ce que Google cache ;
2. **trouver les défauts de comptage** — c'est ici qu'on a découvert que « l'avis a disparu » ne
   veut pas dire « Google l'a supprimé », et que 483 des 5 230 disparitions constatées n'en sont
   pas ;
3. **produire les premiers résultats**, dont plusieurs tiennent encore.

Techniquement : DuckDB en lecture directe sur les fichiers d'origine, en local. L'étude qui lui
succède travaille dans BigQuery.

## Pourquoi il est gelé

Le projet s'organise maintenant autour d'une seule étude vivante, la régression logistique. Deux
études en parallèle, avec deux définitions d'une suppression et deux jeux de chiffres, ont rendu
le dossier impossible à expliquer à quelqu'un qui arrive.

Le dossier reste sur le disque parce que ses notes portent le raisonnement qui a mené aux
décisions actuelles. Il ne bouge plus.

## Où sont passés ses résultats

| Ce qu'il portait | Où le lire maintenant |
|---|---|
| Le pic de suppression au septième jour de vie de l'avis | `../docs/03-resultats.md` § 4 |
| Le lien entre afflux récent et mortalité des vieux avis | `../docs/03-resultats.md` § 4 |
| Quel avis tombe dans une fiche qui perd des avis | `../docs/03-resultats.md` § 4 |
| Les réserves à porter au livrable | `../docs/03-resultats.md` § 5 |
| La définition d'une suppression et ses seuils | `../docs/02-donnees.md` § 3 |
| Le critère de fiche attaquée et pourquoi l'ancien a été abandonné | `../docs/02-donnees.md` § 4 |
| Les pièges du jeu de données | `../docs/02-donnees.md` § 5 |
| Les vérifications jamais faites, L1 à L15 | `../docs/BACKLOG.md` |

## Si vous devez quand même ouvrir ce dossier

**Commencez par `documentations/INDEX.md`.** Il donne le statut de chacune des 22 notes : à jour,
chiffres périmés, ou entièrement périmée. Sans lui, rien ne distingue un chiffre encore valable
d'un chiffre d'avant la correction du comptage du 2026-09-08.

`audit-methode.md` décrit, note par note, comment chaque analyse a été calculée. C'est le seul
endroit où l'on peut savoir ce que fait une analyse sans lire son programme.

**Une réserve qui vaut pour les cinq notes régénérées le 2026-09-09** : leurs tableaux sont à
jour, mais les paragraphes de commentaire écrits en dur dans les programmes n'ont jamais été
relus. Vérifier toute phrase chiffrée contre le tableau qui la précède avant de la citer.

## Ce qui a été retiré de ce dossier

`v2/build_panel.py`, une table de panel écrite et jamais exécutée, remplacée par la chaîne
BigQuery. Ses six avertissements sur le jeu de données ont été récupérés et vivent dans
`../docs/02-donnees.md` § 5.

`BACKLOG.md` et `PASSATION.md` : leur contenu est réparti dans `../docs/`. Le détail de ce qui
est allé où est à la fin de `../docs/BACKLOG.md`.
