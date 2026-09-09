# Décisions — ReviewFlowz — Analyse suppression reviews Google

> ## MIXTE — vérifié le 2026-09-08
>
> **Méthode, décisions et questions ouvertes : toujours valables.**
> **Chiffres de résultat : périmés**, calculés avant la correction du comptage. Dans ce
> document : le taux de 0,11 %.
>
> Comptage de référence aujourd'hui : **4 747 suppressions** sur 5 230 disparitions brutes.
> Résultats à jour : `2026-09-08-synthese-de-la-journee.md`. Inventaire : `INDEX.md`.

_Append-only. L'entrée la plus récente se place juste sous ce titre._

<!-- Gabarit d'une entrée, à recopier. Une entrée = une décision.

## AAAA-MM-JJ — Titre de la décision
**Contexte** : ce qui a amené la question.
**Décision** : ce qui est tranché, dans les termes où ça a été dit.
**Qui décide** : la personne ou l'instance.
**Conséquence** : ce que ça change pour la suite du projet.
**Source** : lien vers le document d'origine, s'il vit hors du dépôt (CR, mail, Drive).

Le champ Source est un pointeur, jamais une copie : le document reste unique là où il est.
La date est celle de la décision, pas celle de la saisie. Une action à mener n'est pas une
décision : elle va dans la note de semaine.
-->

## 2026-09-04 — Plan d'analyse en trois niveaux
**Contexte** : les caractéristiques accessibles par scraping sont arrêtées et la cible est
binaire (avis supprimé ou en ligne).
**Décision** : l'analyse se fait en trois niveaux — bivarié par caractéristique, régression
logistique pour isoler les effets propres, random forest en complément optionnel pour les
interactions non prévues et les non-linéarités.
**Qui décide** : Romain.
**Conséquence** : le random forest est un contrôle, pas le modèle de référence. Il est aussi le
plus exposé à la rareté de la cible (0,11 %).
**Source** : dossier de cadrage Notion, ReviewFlowz v2.

## 2026-09-04 — L'export de données prévaut sur le protocole de cadrage
**Contexte** : le dossier de cadrage décrit deux dispositifs — un panel hebdomadaire
FR/DE/UK/US avec appariement franchisés / indépendants et courbes de survie à deux ans, et un
dispositif resserré sur US et Europe. L'export livré (14 vagues quotidiennes du 11 au 24 août
2026, 9 048 établissements, US et Europe hors Royaume-Uni) correspond au second.
**Décision** : en cas de divergence entre le protocole écrit et les données de l'export, les
données prévalent. Le protocole est mis à jour pour refléter ce qui a été collecté, jamais
l'inverse.
**Qui décide** : Romain.
**Conséquence** : le Royaume-Uni sort du périmètre, donc la comparaison des régimes juridiques
se fait sans le pays du DMCC Act. L'appariement franchisé / indépendant un-pour-un n'existe pas
et se substitue par une comparaison des paliers `mono` / `small` / `large` à secteur et pays
comparables. Les courbes de survie à deux ans sont hors de portée : la fenêtre est de 14 jours.
**Source** : `local/exports.zip`, fichier `exports/README.md` (hors dépôt, gitignoré).
