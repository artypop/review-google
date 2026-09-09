---
id: reviewflowz-analyse-google
nom: "ReviewFlowz — Analyse suppression reviews Google"
type: client
statut: actif
client: ReviewFlowz
debut: null
fin_prevue: 2026-09-30
cadence: null
jalons:
  - date: 2026-09-15
    libelle: Rédaction livrable
---

# ReviewFlowz — Analyse suppression reviews Google

> ## MIXTE — vérifié le 2026-09-08
>
> **Méthode, décisions et questions ouvertes : toujours valables.**
> **Chiffres de résultat : périmés**, calculés avant la correction du comptage. Dans ce
> document : 5 230 suppressions, le taux de 0,11 %, 617 résurrections.
>
> Comptage de référence aujourd'hui : **4 747 suppressions** sur 5 230 disparitions brutes.
> Résultats à jour : `2026-09-08-synthese-de-la-journee.md`. Inventaire : `INDEX.md`.

<!-- orga:auto — régénéré par les scripts, ne pas éditer à la main -->
**Dernière activité** : 2026-08-31 · **Prochain jalon** : Rédaction livrable, 2026-09-15 (dans 11 j)
**Fait en [[2026-W36]]** : Téléchargement des parquets · Init ML
<!-- /orga:auto -->

## Où on en est
Étude quantitative sur les caractéristiques d'un avis Google associées à sa suppression, avec
l'angle des faux positifs — aucune étude indépendante évaluée par les pairs n'existe sur le
sujet, ce qui est l'argument de positionnement. La collecte est faite : 14 vagues quotidiennes
du 11 au 24 août 2026 sur 9 048 établissements, 4,88 M d'avis, 5 230 suppressions, soit un taux
de 0,11 %. Les premiers bivariés sont posés — le statut Local Guide est l'effet le plus fort à
ce stade, la note a un effet non monotone, et le « 73 % de suppressions sur des 5 étoiles » du
marché s'explique par la composition de la base ; reste la régression logistique, les
interactions et le livrable du 15 septembre.

## Prochaines étapes

### Cadrage des données
Le périmètre est arrêté par la collecte : tous les avis de chaque établissement du panel, pas
un échantillon récent. Les caractéristiques d'avis et d'auteur listées au cadrage sont toutes
disponibles, plus le niveau de Local Guide (1-10) qui n'était pas prévu.

Ce qui n'est pas dans l'export et devra être renoncé ou recollecté : l'adresse, le téléphone et
la complétion de la fiche d'établissement. La note moyenne, elle, se reconstruit depuis
`histograms` (répartition 1-5 étoiles par vague), qui donne en prime la trajectoire de la note
sur les 14 vagues.

### Choix de modélisation
Arrêter la liste des caractéristiques à tester, en privilégiant celles sur lesquelles le client
peut agir. Définir les interactions à tester, soit par expertise métier, soit pour infirmer ou
confirmer les croyances du marché, après les résultats du niveau bivarié.

Trois arbitrages statistiques à rendre : la correction de la dépendance (erreurs-types groupées
sur l'identifiant le plus englobant disponible, ou modèle multiniveau si les variables
d'établissement deviennent un objet d'analyse) ; le traitement du déséquilibre entre gros
groupes et mono-enseignes (vérification a posteriori sans les plus gros, ou pondération) ; et le
plafonnement ou non du nombre d'avis par établissement.

### Validation
Identifier les caractéristiques réellement actionnables par le client. Vérifier sur un
échantillon réel l'hypothèse selon laquelle Google filtre les insultes avant publication — si
elle tient, la caractéristique est absente de l'échantillon et n'a pas à être retenue. Piloter
et valider les choix de modélisation avant le passage à l'échelle.

### Après l'analyse
Diffusion et promotion du résultat : l'angle à mettre en avant reste à choisir. Piste évoquée :
le rapprochement avec le SEO et ce que les suppressions révèlent des éléments de scoring de
l'algorithme.

## Interlocuteurs
- Axel — directeur de ReviewFlowz — commanditaire de l'étude

## Points de vigilance
- **Le taux de suppression observé est de 0,11 %** : 5 230 suppressions sur 4 878 151 avis en
  ligne de base. Le nombre d'événements suffit largement à la régression logistique — ce qui est
  contraint, c'est le détail. Les 19 cellules secteur × taille vont de 63 à 1 557 événements,
  donc quatre cellules `mono` sont sous 100 : les interactions et les effets par sous-groupe y
  seront mal estimés. Trois conséquences pratiques : sous-échantillonner les négatifs pour le
  coût de calcul (les odds ratios sont inchangés, seule la constante est à corriger si on veut
  des probabilités absolues) ; présenter les résultats en risque relatif et non en probabilité,
  qui vaudra toujours ~0,1 % ; et ne jamais évaluer un modèle sur l'exactitude, puisque prédire
  « jamais supprimé » donne 99,89 %. Le random forest du niveau 3 est bien plus exposé à cette
  rareté que la régression.
- Le dispositif ne capte que les suppressions rapides — 14 jours de suivi — pas les révisions
  de stock à six mois, alors que le réentraînement rétroactif des modèles est le mécanisme qui
  produit les vagues observées en 2025. La limite est assumée, elle doit être écrite dans le
  livrable.
- `review_id` n'est pas une clé unique dans `reviews` : 2 012 lignes de version après édition
  (`is_update`) et 617 résurrections d'avis supprimés puis réapparus. L'état vivant du panel
  s'obtient avec `NOT is_update AND deleted_detected_at IS NULL`. Toute analyse qui compte les
  lignes brutes est fausse.
- Les URL de photos sont resignées à chaque collecte : elles ne sont pas un signal de
  changement. L'histogramme Google se met à jour avant la liste d'avis, donc un avis peut avoir
  disparu du décompte tout en étant encore servi — la liste est la source de vérité.
- Le panel ne couvre pas toutes les tailles de groupe : `mono` est une enseigne à établissement
  unique, `small` va de 4 à 10 sites, `large` de 20 à 50, et au-delà de 50 les groupes sont
  exclus. Les groupes de 2 à 3 sites et ceux de 11 à 19 n'ont aucun représentant — l'effet de
  taille ne s'interprète que sur les trois paliers observés, pas comme une courbe continue.
- Le panel est déséquilibré par construction : 1 428 établissements pour chacun des six premiers
  secteurs mais 480 pour `travel`, et 41 codes pays dont un seul hors Europe (US). Une analyse
  géographique par pays est hors de portée ; par région, elle tient.
- `reviewer_name`, `reviewer_avatar`, `review_link` et `text` identifient des personnes. Le
  README impose de ne pas rediffuser et de retirer les colonnes auteur si l'analyse s'en passe.
  L'archive reste dans `local/`, qui est gitignoré.
- Le filtrage pré-publication est invisible par construction : aucune mesure externe ne
  l'atteint. Toute conclusion porte sur les avis publiés puis supprimés, jamais sur ceux qui
  n'ont jamais paru.
- Vrais faux avis et faux positifs sont indistinguables par scraping, et le périmètre retenu ne
  les sépare pas. L'argument tient sur une inférence indirecte : si une caractéristique anodine
  prédit fortement la suppression, c'est un indice de faux positifs — pas une mesure.
- Les seules données à fréquence fine viennent d'acteurs du reputation management (GMBapi,
  Localo), commercialement intéressés et sur panels non représentatifs. À citer comme
  hypothèses à tester, pas comme résultats.
- Les scores de génération par IA reposent sur des détecteurs dont la non-fiabilité est
  documentée (Liang et al., Patterns 2023 : plus de la moitié des textes de non-natifs classés
  à tort comme IA). Toute caractéristique construite là-dessus hérite de ce biais.
- Les expérimentations contrôlées — poster des avis tests — sont exclues : conditions
  d'utilisation, et illégales au Royaume-Uni depuis le DMCC Act.
- Le dossier de cadrage décrit deux dispositifs — un panel hebdomadaire FR/DE/UK/US avec
  appariement franchisés / indépendants et courbes de survie à deux ans, et un dispositif
  resserré sur US et Europe. C'est le second qui a été exécuté, en quotidien sur 14 jours.
  Le Royaume-Uni est hors panel, l'appariement franchisé / indépendant n'existe pas dans
  l'export : il se reconstruit via `bucket`, à secteur et pays comparables.

## Liens
- [Dossier de cadrage — ReviewFlowz v2](https://app.notion.com/p/cartelis/ReviewFlowz-v2-38894a0a1bb1803fa8c2f3e177bd47c6?source=copy_link) — Notion, document de référence de l'étude
- [Rapport de transparence Google Maps](https://transparencyreport.google.com/maps-content/overview) — volumes publiés et supprimés, ventilation par motif, comptes et fiches
- [Enforcement, séries par période](https://transparencyreport.google.com/maps-content/enforcement) — détail des mesures
- [Reviewing War, arXiv 2023](https://arxiv.org/pdf/2302.00598) — précédent méthodologique direct : mesure des suppressions Google Maps par crawling
- [Règlement UGC Google Maps](https://support.google.com/contributionpolicy/answer/7422880) et [contenus interdits](https://support.google.com/contributionpolicy/answer/7400114) — les motifs opposables
- [Aveu des faux positifs et recours](https://support.google.com/business/answer/4596773) — Google reconnaît supprimer des avis légitimes
- [GMBapi, panel de 60 000 fiches](https://gmbapi.com/news/google-reviews-deleted-ai-legal-takedowns/) et [Localo, 335 520 avis supprimés](https://localo.com/blog/review-velocity-study) — données d'industrie, conflit d'intérêts à signaler
- [Liang et al., Patterns 2023](https://arxiv.org/abs/2304.02819) — non-fiabilité des détecteurs de texte IA
