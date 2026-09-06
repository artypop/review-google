# Etude des avis supprimes par Google : synthese des decisions

Date : 3 juillet 2026. Etat : phases 1 et 2 quasi terminees (exploration Overture, mapping categories, clustering), pilote de resolution Google valide sur 10 lignes. Reste : echantillonnage stratifie (phase 3), pilote 200 lignes + resolution complete (phase 4), QA et livraison (phase 5).

## 1. Objectif et design du panel

Construire un panel representatif de 10 000 etablissements Google Maps et mesurer les avis supprimes par Google au fil du temps.

- 5 000 US + 5 000 Europe (UK exclu)
- 7 industries x 2 regions x 3 buckets de taille = 42 cellules d'environ 238 etablissements
- Industries : Travel (tour operators), Hospitality (hotels), Food & Beverage, Home services, Healthcare, Automotive, Wellness & Fitness

Decisions verrouillees :

1. L'unite d'echantillonnage est la marque / le groupe, pris en entier. Un groupe selectionne apporte TOUTES ses locations au panel.
2. Buckets par nombre de locations US+EU (decision du 3 juillet : comptage sur le perimetre du panel, pas mondial). Mono = exactement 1, petit groupe = 4 a 10, grand groupe = 2 0 a 50. Les groupes de 2-3 et 11-19 sont exclus pour garder des buckets propres. Les groupes de plus de 50 locations sont exclus entierement (jamais d'echantillonnage partiel d'un groupe).
3. Le bucket mesure le nombre de locations operees par le business, pas sa taille economique.
4. Gate d'avis 100 a 10 000 : appliquee a une location "seed" par groupe, au moment de la resolution Google (Overture n'a pas de compte d'avis). Un groupe accepte garde tous ses membres meme hors plage.
5. Matching Google strict : distance < 100 m ET similarite de nom > 0.8 ET business_status OPERATIONAL. Tout le reste est rejete et remplace, jamais rattrape a la main.
6. Franchises : marque = groupe, avec un flag is_franchise best effort.
7. Faible diversite de marques dans les cellules grands groupes acceptee (5 a 8 marques par cellule).
8. Starvation acceptee sur travel grands groupes : les tour operators n'operent presque jamais 20 a 50 locations, c'est representatif du secteur.
9. Repartition equilibree entre sous-categories a l'interieur de chaque cellule : cible = 238 / nombre de sous-categories. Un manque sur une sous-categorie est redistribue equitablement aux autres sous-categories de la meme cellule et documente dans le rapport QA. Verification faite : seulement 8 combinaisons sous-categorie x cellule en manque, dont 6 dans les cellules travel deja en starvation (les 2 autres : landscaping EU grand groupe, bnb US grand groupe).

## 2. Source de donnees et mapping des categories

Source : Overture Maps, release 2026-06-17.0 (figee pour reproductibilite). 75,6 M de lieux monde, extrait local US + Europe hors UK de 34,06 M de lignes. Filtre de depart : confidence > 0.6.

Mapping de 316 categories Overture vers les 7 industries, par sous-arbres de taxonomie (ex : tout le sous-arbre restaurant couvre les 163 feuilles de cuisines) plus listes de feuilles choisies. Arbitrages valides :

- Inclus apres revue : veterinaires (healthcare), car wash (automotive), locations de vacances et campings (hospitality)
- Exclus apres revue : travel agents, boulangeries, wineries / breweries, hopitaux, feuilles fourre-tout generiques (travel_service, automotive_service, etc.)

Volumes par industrie a confidence > 0.6 (nombre de lieux) :

| Industrie | US | EU hors UK |
| --- | --- | --- |
| Automotive | 487 k | 416 k |
| Food & Beverage | 1 068 k | 1 425 k |
| Healthcare | 639 k | 331 k |
| Home services | 488 k | 247 k |
| Hospitality | 221 k | 583 k |
| Travel | 9,7 k | 18,2 k |
| Wellness & Fitness | 313 k | 244 k |

Travel est deux ordres de grandeur plus petit que le reste : assume.

## 3. Clustering en groupes (sans Google, valide empiriquement)

Cle de cluster : coalesce(brand.wikidata, domaine eTLD+1 du site web, nom normalise). Couverture site web de 73 a 95 % selon l'industrie, donc la cle repose surtout sur les domaines.

Regles issues des tests :

- Domaines agregateurs detectes par les donnees (pas seulement une blacklist statique) : un vrai reseau a un token de nom dominant partage par ses membres (starbucks a 100 %, crossfit a 99 %), un agregateur non (business.site a 5 %, gelbeseiten.de a 10 %). Seuil de coherence : 0.5.
- Domaines incoherents de 4 membres ou plus : lieux exclus, motif aggregator_domain (438 k lieux).
- Cles nom seul avec plusieurs membres : indecidable (Pizzeria Roma x48 dans 11 pays), exclues des buckets groupes, motif ambiguous_name (264 k lieux). Nom seul unique = candidat mono uniquement.
- Univers eligible restant : 5,79 M de lieux.

## 4. Grille de faisabilite (nombre de groupes par industrie x region x bucket)

| Industrie | US mono | US petit | US grand | EU mono | EU petit | EU grand |
| --- | --- | --- | --- | --- | --- | --- |
| Automotive | 271 078 | 3 719 | 252 | 217 858 | 2 207 | 287 |
| Food & Beverage | 496 990 | 10 605 | 811 | 895 170 | 5 501 | 430 |
| Healthcare | 301 553 | 7 221 | 438 | 241 634 | 1 265 | 100 |
| Home services | 342 735 | 2 507 | 187 | 200 268 | 743 | 78 |
| Hospitality | 105 708 | 1 234 | 111 | 394 250 | 2 678 | 202 |
| Travel | 7 636 | 51 | 1 | 14 733 | 56 | 2 |
| Wellness & Fitness | 184 935 | 1 882 | 120 | 172 138 | 1 162 | 107 |

Lecture faisabilite (238 locations par cellule) :

- Cellules mono : besoin d'environ 476 groupes avec oversampling, toutes les industries passent largement.
- Cellules petits groupes : besoin d'environ 80 groupes, tout passe sauf travel (51 US, 56 EU) : remplissable mais sans marge.
- Cellules grands groupes : besoin d'environ 16 groupes, tout passe sauf travel (1 US, 2 EU) : starvation assumee.

Decision ouverte : redistribuer les ~476 slots des cellules travel grand groupe vers travel mono / petit, ou accepter un panel legerement sous 10 000.

## 5. Resolution vers Google Places et pilote

Pipeline : Text Search avec textQuery = nom + adresse + code postal + ville, locationBias cercle de 2 km autour des coordonnees Overture. Verification stricte sur les 3 premiers candidats : distance < 100 m, similarite de nom token-set > 0.8, statut OPERATIONAL. Corroboration gratuite dans la meme reponse : match du domaine web, et telephone (a ajouter au prochain extrait Overture). Chaque reponse est cachee sur disque, les re-runs sont gratuits.

Pilote reel sur 10 lieux tires au hasard : 5 acceptes, 5 rejetes.

| Cas | Verdict | Enseignement |
| --- | --- | --- |
| 3 fermes ou disparus (CLOSED_PERMANENTLY, etc.) | rejet correct | le filtre anti obsolescence Overture fonctionne |
| 2 renvois d'un autre business proche | rejet correct | Text Search repond toujours quelque chose, les gates protegent |
| 1 vrai faux negatif (nom pollue + coordonnees a 1,4 km) | rejet strict assume | recuperable en partie via une cascade de requetes de secours |
| Taux d'acceptation net | 5/10 | l'oversampling est indispensable |

Constat cle : sur les 5 acceptes, seuls 2 passent la gate d'avis 100 a 10 000 (97, 38 et 91 avis echouent). Acceptation seed de bout en bout d'environ 20 % sur ce mini pilote. Consequence : l'oversampling fixe x2 est probablement insuffisant, recommandation de passer le sampler en mode pull-until-filled (on tire des candidats jusqu'a remplir chaque cellule). A confirmer sur le pilote 200 lignes.

Ameliorations retenues pour le resolveur final :

1. Cascade de requetes en cas de rejet : nom nettoye (tronque a la premiere ponctuation), puis requete par domaine du site.
2. Ajout des telephones Overture a l'extrait pour corroboration quasi deterministe.
3. Les gates restent strictes : un mauvais place_id empoisonne silencieusement la mesure, un rejet remplace ne coute rien.

## 6. Cout Google Places API

Le field mask (userRatingCount, rating, websiteUri) declenche le SKU Text Search Enterprise : 35 dollars les 1 000 appels sur le palier 1 000 a 100 000 (verifie sur la page de pricing Google). Les champs de matching seuls seraient en Pro a 32 dollars, l'ecart est negligeable : on reste en Enterprise en un seul appel.

Modele d'appels (pull-until-filled, taux d'acceptation seed 20 a 30 % issus du pilote) :

| Poste | Appels |
| --- | --- |
| Cellules mono (14 x 238 locations) | 11 100 a 16 700 |
| Cellules petits groupes (seeds + ~5 membres par groupe accepte) | 4 600 a 5 500 |
| Cellules grands groupes (seeds + ~29 membres par groupe accepte) | 3 600 a 3 800 |
| Total | 19 000 a 26 000 |

Cout estime : 670 a 900 dollars pour la construction du panel. Budget de securite : 1 000 dollars. Variante deux etapes possible (Text Search IDs only gratuit + un Place Details Enterprise a 20 dollars les 1 000 sur le premier candidat) qui ramene a 420 a 580 dollars, decision apres le pilote 200 lignes.

## 7. Monitoring ScrapingBee : crawl adaptatif

Parametres : 15 credits par appel, 20 avis par appel, soit 0,75 credit par avis. 7 vagues sur 14 jours (une toutes les 48 h).

Crawl brut de tous les avis a chaque vague : 5,25 x (total des avis du panel), soit environ 26 M de credits pour une moyenne de 500 avis par etablissement. Trop cher.

Design retenu : crawl adaptatif par comptage exact.

1. Page 1 triee par plus recent (1 appel) : donne les nouveaux avis et le compte total.
2. Reconciliation exacte : suppressions = compte precedent + nouveaux avis - compte actuel. Les comptes Google sont fiables (constat terrain Reviewflowz), ce n'est pas une approximation.
3. Si zero suppression : stop a 1 ou 2 appels au lieu de ~25.
4. Si d suppressions : pagination en profondeur, on connait l'ID et le timestamp de chaque avis connu, donc on identifie chaque avis manquant des qu'on a depasse sa position temporelle. Stop des que les d manquants sont identifies.
5. Avis edites : matching par ID globalement, jamais par position. Un ID connu qui remonte en tete n'est pas un nouvel avis.
6. Le crawl a profondeur fixe (ex : 200 derniers avis) est rejete : aveugle aux suppressions d'avis anciens, qui sont precisement une cible connue des purges Google.

Budget credits (moyenne 500 avis par etablissement) :

| Poste | Credits |
| --- | --- |
| Vague 1 : baseline complete (etat ID + timestamp obligatoire) | ~3,75 M |
| Vagues 2 a 7 : etablissements sans suppression (~90 %) | ~1,6 M |
| Vagues 2 a 7 : scans profonds declenches (~10 %) | ~1,4 M |
| Sous-total etude | ~6,75 M |
| Optionnel : vague 7 en crawl complet d'audit | +3,75 M |

Plan SPB Enterprise 1 : 999 dollars pour 14 M de credits et 200 requetes concurrentes. Le coeur de l'etude consomme environ la moitie du plan, l'audit inclus environ 10,5 M. Fallback si l'endpoint avis ne renvoie pas le compte total : un appel SPB supplementaire sur la page du lieu par etablissement et par vague, +0,9 M de credits, negligeable.

A valider avant lancement (sur les ~2 M de credits stockes qui expirent le 7 juillet) : presence du compte total dans la reponse SPB, comportement de la pagination profonde, dry run du crawler adaptatif sur quelques centaines d'etablissements.

## 8. Duree des vagues, parallelisme, pools

Vague complete : 10 000 etablissements x ~20 appels = 200 000 appels a ~3 s.

| Threads paralleles | Duree de la vague |
| --- | --- |
| 1 | ~7 jours (impossible) |
| 10 | 16,7 h |
| 20 | 8,3 h |
| 50 | 3,3 h |
| 100 | 1,7 h |
| 200 (plafond du plan) | ~50 min |
- La pagination est sequentielle par etablissement (le curseur de la page N+1 vient de la page N) : un etablissement de 10 000 avis = 500 pages = ~25 min incompressibles. Le parallelisme se fait entre etablissements.
- Prevoir 10 a 15 % de temps en plus pour les retries (les echecs ne consomment pas de credits mais consomment du planning).
- Zone de confort : 50 a 100 threads. Les vagues adaptatives 2 a 7 (~30 k appels) tombent a ~30 min a 50 threads.

Dimensionnement du pool de cookies + headers : taille du pool = (appels par seconde) x (delai minimal de reutilisation d'une identite).

| Threads | Appels/s | Reutilisation 10 s | Reutilisation 30 s |
| --- | --- | --- | --- |
| 50 | ~17 | 170 identites | 500 |
| 100 | ~33 | 330 identites | 1 000 |

Quelques centaines d'identites suffisent pour le setup 50 threads. Sur les vagues adaptatives, la pression par identite est divisee par ~7 a pool egal.

## 9. Budget global previsionnel

| Poste | Cout |
| --- | --- |
| Google Places (construction du panel) | 670 a 900 dollars (variante deux etapes : 420 a 580) |
| ScrapingBee (7 vagues, crawl adaptatif) | ~6,75 M credits, dans le plan a 999 dollars, audit optionnel inclus ~10,5 M |
| Validation pre lancement | ~0 (credits expirant le 7 juillet) |

## 10. Decisions ouvertes

1. Redistribution des slots des cellules travel grand groupe (vers mono / petit) ou panel sous 10 000 : a trancher avant la phase 3.
2. Sampler pull-until-filled plutot que multiplicateur fixe x2 : recommande, a confirmer.
3. Resolution en un appel Enterprise (simple) ou deux etapes (moins chere) : decision apres le pilote 200 lignes et verification des SKU factures dans la console Google.
4. Cadence et implementation du monitoring : vivent dans le repo reviewflowz, design adaptatif acte ici.