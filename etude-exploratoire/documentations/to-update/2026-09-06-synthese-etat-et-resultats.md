---
date: 2026-09-06
projet: reviewflowz-analyse-google
titre: "Synthèse — ce qui a été fait, comment le relancer, ce que ça donne"
statut: à jour au 2026-09-06
---

# Synthèse de l'étude au 2026-09-06

> ## PÉRIMÉ — déplacé le 2026-09-08
>
> Les résultats chiffrés de ce document sont calculés sur le comptage d'avant la correction des
> suppressions (résurrections et bugs d'édition non retirés). Ses verdicts en dépendent, donc
> **aucun de ses chiffres ne doit être cité ni communiqué**.
>
> Comptage de référence aujourd'hui : **4 747 suppressions** sur 5 230 disparitions brutes.
> Définition : `../../scripts/suppressions_corrigees.py`.
> Résultats à jour : `../2026-09-08-synthese-de-la-journee.md` et `../INDEX.md`.
>
> Le document est conservé pour sa méthode, ses pièges documentés et ses questions ouvertes.

Jalon livrable : 2026-09-15.

---

# Partie A — Ce qui a été fait, et comment le relancer

Tous les programmes sont dans `scripts/`. Ils se lancent depuis la racine du projet.
Ils réécrivent leurs sorties à chaque exécution : les relancer ne casse rien.

## Préparation des données

| Programme | Ce qu'il fait | Commande | Durée |
|---|---|---|---|
| `build_tables.py` | Lit l'export Google d'origine et construit les trois tables de travail. À lancer en premier, tout le reste en dépend. | `uv run scripts/build_tables.py` | 20 s |

Il produit trois fichiers dans `data/build/` :

- **`reviews_features.parquet`** — 4 878 151 lignes, un avis par ligne. Tous les avis, anciens compris.
- **`business_features.parquet`** — 9 048 lignes, une entreprise par ligne.
- **`fresh_hazard.parquet`** — 1 137 276 lignes. Un avis récent, observé à un passage du robot.
  Sert à mesurer les disparitions jour par jour.

Aucun de ces fichiers ne contient de nom d'auteur, de lien d'avis ni de texte.

## Les analyses

| Programme | La question à laquelle il répond | Commande | Durée |
|---|---|---|---|
| `level1_bivariate.py` | Facteur par facteur, lesquels sont liés à la suppression ? | `uv run scripts/level1_bivariate.py` | 10 s |
| `analysis_a.py` | Quelle entreprise Google vient nettoyer ? | `uv run scripts/analysis_a.py` | 2 min |
| `analysis_b.py` | Dans une entreprise nettoyée, quel avis tombe ? | `uv run scripts/analysis_b.py` | 2 min |
| `controle_robustesse.py` | Les résultats tiennent-ils sans les 24 entreprises massacrées ? | `uv run scripts/controle_robustesse.py` | 7 min |

## Les vérifications

| Programme | La question | Commande | Durée |
|---|---|---|---|
| `verif_texte.py` | Les avis supprimés contiennent-ils des insultes, de la pub, du charabia ? | `uv run scripts/verif_texte.py` | 2 min |
| `test2_debordement.py` | Google emporte-t-il des vieux avis qui n'ont rien à voir ? | `uv run scripts/test2_debordement.py` | 1 min |

## Consulter les données soi-même

| Programme | Ce qu'il fait | Commande |
|---|---|---|
| `query.py` | Poser une question en SQL sans écrire de code | `uv run scripts/query.py --exemples` |
| `explore.py` | Explorer à la souris dans VS Code (cellules `# %%`) | ouvrir le fichier |

## Le calcul long

Un seul programme est lent : la marge d'erreur de l'analyse B.

```bash
setsid nohup uv run scripts/analysis_b.py --bootstrap 30 \
  > data/resultats/analyse_b_run.log 2>&1 < /dev/null &
```

- Compter **environ 2 minutes par tirage** : 30 tirages ≈ 1 h, 200 tirages ≈ 7 h.
- Le lancer détaché comme ci-dessus, sinon il meurt avec la session.
- Suivre l'avancement : `tail -f data/resultats/analyse_b_run.log`.
- Il met la note et le tableau à jour tout seul en finissant.

**À quoi ça sert.** Sans lui, on a un chiffre mais pas sa précision. On sait que les avis publiés
en rafale disparaissent 18 fois plus, mais pas si la vraie valeur est 12 ou 28. Le calcul refait
l'analyse 30 fois sur des tirages au sort d'entreprises et regarde à quel point le résultat bouge.
**Tant qu'il n'a pas tourné, la note affiche « non calculé » et aucun chiffre de l'analyse B ne
doit être présenté comme acquis.**

## Suspendu

| Programme | État |
|---|---|
| `machine_learning.py` | Jamais relancé. Il saturait la machine quand elle avait 7 Go ; elle en a 16 depuis le 2026-09-06. Sert de contrôle : reste-t-il un signal que les analyses A et B auraient manqué ? Optionnel. |

## Règles de lancement

- Un calcul se fait dans un programme de `scripts/`, jamais ailleurs. Tout chiffre présenté doit
  pouvoir être régénéré par une des commandes ci-dessus.
- Deux calculs lourds au maximum en même temps. Vérifier avec `free -m` avant de lancer.
- Les longs se lancent détachés (`setsid nohup … &`).

---

# Partie B — Les résultats

## Le jeu de données

- 9 048 entreprises suivies, 7 secteurs, États-Unis et Europe hors Royaume-Uni.
- 14 relevés quotidiens, du 11 au 24 août 2026. Le robot recense la totalité des avis à chaque passage.
- 4 878 151 avis. 5 230 ont disparu pendant les 14 jours.

## 1. Google supprime les avis récents, et presque uniquement eux

C'est le fait qui structure toute l'étude.

| Âge de l'avis | Sur 10 000 avis en ligne, combien disparaissent d'un jour sur l'autre |
|---|---:|
| 0 à 2 jours | 36 |
| 3 à 6 jours | 40 |
| **7 à 13 jours** | **50** |
| 14 à 20 jours | 25 |
| 21 à 29 jours | 9 |
| 1 mois à 2 mois | 3 |
| 2 à 6 mois | 1 |
| plus d'un an | moins de 1 |

Le danger culmine une à deux semaines après la publication, puis s'effondre. **Un avis qui a
passé son premier mois ne risque pratiquement plus rien.**

Conséquence pratique : toute comparaison entre deux groupes d'avis doit tenir compte de leur âge.
Sinon on mesure surtout qu'un groupe est plus jeune que l'autre. Quatre conclusions des premiers
chiffres du 4 septembre se sont révélées fausses pour cette raison.

L'étude se concentre donc sur les avis de moins de 30 jours : 106 761 avis, 2 853 suppressions.

## 2. Ce ne sont pas des avis isolés, ce sont des vitrines entières

- **84 % des entreprises n'ont perdu aucun avis** en 14 jours.
- 24 entreprises concentrent **958 suppressions, soit 18 % du total**.
- Le cas le plus extrême : une salle de sport espagnole a perdu 264 avis sur 816, un tiers de sa
  vitrine, en quatorze jours.

La liste complète est dans `data/resultats/fiches_massivement_purgees.csv`.

**Deux situations très différentes y coexistent.**

*Des opérations détectées* — 4 entreprises. Beaucoup d'avis reçus récemment, note qui grimpe
(+1,1 étoile pour l'une), et ce sont les avis récents qui sautent. Google attrape quelque chose.

*Des vitrines endormies vidées de leurs vieux avis* — ce sont **les 7 entreprises les plus
touchées du panel**, plus une neuvième (Bischoff). Seule une salle de sport espagnole s'intercale
en 8e position :

| Entreprise | Pays | Avis perdus | Part de la vitrine | Avis reçus le mois précédent | Avis récents perdus |
|---|---|---:|---:|---:|---:|
| Mikel Coffee Company | GR | 35 | 47 % | 1,3 % | **0** |
| Fair Doctors Duisburg | DE | 34 | 46 % | 5,4 % | **0** |
| REDDY Küchen Eislingen | DE | 23 | 45 % | 0 % | **0** |
| Occasions Cavallari | FR | 23 | 44 % | 0 % | **0** |
| JET Waschstraße | DE | 18 | 44 % | 0 % | **0** |
| DetailCar La Concha | ES | 18 | 44 % | 0 % | **0** |
| MEGA Malereinkaufsgen. | DE | 11 | 39 % | 3,6 % | **0** |
| Bischoff Touristik *(9e)* | DE | 48 | 30 % | 0 % | **0** |

Cinq des huit n'avaient reçu aucun avis le mois précédent, les trois autres très peu.
**Aucune des huit n'a perdu un seul avis récent** : la totalité des suppressions porte sur le
vieux stock. Google a effacé entre 30 et 47 % d'une vitrine, sans toucher à ce qui venait
d'arriver. Ce ne sont pas des tricheurs pris sur le fait.

## 3. Les avis supprimés ne sont pas des insultes

Vérification faite avec `verif_texte.py`. Onze contrôles automatiques sur le texte : insultes en
7 langues, liens, adresses e-mail, numéros de téléphone, majuscules, ponctuation excessive,
caractères répétés, texte trop court, charabia, symboles, vocabulaire publicitaire.

Sur 100 avis récents supprimés :

- **94 ne déclenchent aucun contrôle.** Rien à leur reprocher dans le texte.
- 1 contient une insulte.
- 30 n'ont aucun texte du tout — ce sont des notes seules, sans commentaire.

**Aucun avis contenant un lien internet n'a été supprimé.** Ni aucun contenant une adresse
e-mail. Alors qu'il en existe dans le panel. La pub est donc bloquée avant publication, et ce
panel ne peut pas la voir.

Aucun charabia dans les données, ni parmi les supprimés ni parmi les autres.

Google réagit bien aux insultes quand il y en a : un avis qui en contient disparaît 1,75 fois
plus. Mais ça ne concerne que 1 % des suppressions. **Ça n'explique pas le volume.**

*Limites.* Le dictionnaire d'insultes couvre 7 langues sur 41 pays — le grec et le polonais n'y
sont pas. Le chiffre de 94 % est donc un maximum. Et surtout : ne rien avoir à se reprocher dans
le texte ne prouve pas qu'un avis est authentique. Un faux avis bien écrit ne déclenche aucun
contrôle. Ce test montre que l'hypothèse « Google supprime surtout des avis manifestement
fautifs » est fausse. Il ne prouve pas que les 94 % sont des erreurs.

## 4. Google emporte des vieux avis qui n'ont rien à voir — le chiffre du livrable

Vérification faite avec `test2_debordement.py`.

**La question.** Un avis écrit il y a plus d'un an n'a aucun rapport avec une opération lancée
le mois dernier. Disparaît-il quand même davantage dans les entreprises qui reçoivent un afflux
récent ?

**La réponse : oui.** À secteur, pays, taille et volume d'avis comparables :

| Avis reçus le mois précédent | Disparitions de vieux avis, comparé au groupe calme |
|---|---:|
| moins de 1 % de la vitrine | référence |
| 1 à 3 % | **1,7 fois plus** |
| 3 à 10 % | **1,8 fois plus** |

Trois raisons de tenir ce résultat pour solide :

1. Il tient sans les 24 entreprises massacrées : 1,5 et 1,7 fois plus.
2. Il tient sur les avis de **plus de trois ans**, encore plus éloignés de toute opération
   récente : 1,5 et 1,7 fois plus.
3. Il repose sur beaucoup de cas : 683 et 702 disparitions, sur plus de 3,7 millions de vieux avis.

**Le palier « plus de 10 % » ne doit pas être communiqué.** Il n'y a que 9 disparitions dedans,
et les entreprises comparables manquent. Le chiffre affiché est du bruit. C'est une limite du
panel : une entreprise qui reçoit énormément d'avis a peu de vieux stock.

**Pourquoi c'est l'argument central.** L'analyse A montre que Google ne punit pas une entreprise
parce qu'elle reçoit beaucoup d'avis. Mais le ménage déclenché par ce flux emporte au passage
des avis anciens sans rapport. **C'est la définition d'une erreur de modération, et c'est mesuré.**

*Limite.* La comparaison corrige ce qu'on connaît des entreprises — pays, secteur, taille,
volume. Si les entreprises à fort afflux se distinguent par autre chose qu'on ne mesure pas,
l'écart pourrait venir de là. Le panel ne permet pas de l'exclure.

## 5. Quelle entreprise Google vient nettoyer

Analyse A, `analysis_a.py`, sur 2 529 entreprises ayant au moins 10 avis récents, dont 455 touchées.
Résultats vérifiés sans les 24 entreprises massacrées : **ce modèle-là tient entièrement.**

**Ce qui compte :**

| | Effet | Tient sans les 24 |
|---|---:|---|
| Services à domicile (plomberie, dératisation, jardinage) | 3,0 fois plus touchées | oui, 2,9 |
| États-Unis contre Europe | 1,4 fois plus | oui, 1,4 |
| Sport et bien-être | 1,5 fois plus | oui, 1,4 |
| Beaucoup d'avis récents (plus de 150) | 6,3 fois plus | oui, 6,1 |

**Ce qui ne compte pas :** la vitesse à laquelle une entreprise reçoit des avis.

C'est le résultat le plus contre-intuitif de l'étude. Sans correction, une entreprise qui reçoit
beaucoup d'avis semble 26 fois plus touchée. Une fois qu'on tient compte du simple fait qu'elle
a **plus d'avis récents à perdre**, l'effet disparaît complètement — et s'inverse même (0,50, et
0,40 sans les 24). **Google ne sanctionne pas une entreprise parce qu'elle reçoit un afflux d'avis.**

**Attention sur un point.** Le second modèle de l'analyse A, celui qui dit *combien* une
entreprise perd une fois touchée, est beaucoup moins stable. Retirer les 24 entreprises fait
changer de sens six de ses résultats, et « sport et bien-être » s'effondre de 3,6 à 1,3 — les
deux salles de sport espagnoles portaient tout. **Ne pas communiquer l'ampleur des purges par
secteur.** Le modèle « qui est touché » est fiable, celui de « combien » ne l'est pas.

## 6. Dans une entreprise touchée, quel avis tombe

Analyse B, `analysis_b.py`. 584 entreprises, 2 828 disparitions.

Le principe : on ne compare que des avis d'une **même** vitrine, un **même** jour. Tout ce qui
tient à l'entreprise — son secteur, son pays, sa clientèle — disparaît automatiquement de la
comparaison. Il ne reste que ce qui distingue un avis d'un autre au même endroit.

Les marges d'erreur ont été calculées. La fourchette dit entre quelles valeurs se situe la
vérité. **Quand la fourchette contient 1, il n'y a pas d'effet** : le chiffre seul est trompeur.

**Ce qui augmente le risque — établi :**

| | Effet | Fourchette |
|---|---:|---:|
| Auteur ayant publié plusieurs avis le même jour | 26 fois plus | 18 à 40 |
| Avis noté 1 étoile | 3,3 fois plus | 2,2 à 5,1 |
| Avis noté 2 étoiles | 2,1 fois plus | 1,2 à 3,5 |
| Avis modifié après publication | 2,0 fois plus | 1,6 à 2,5 |
| Auteur sans niveau Local Guide | 1,7 fois plus | 1,3 à 2,1 |

Le chiffre de la rafale est à manier avec précaution : la méthode rapide utilisée pour les
fourchettes le surestime. **La valeur de référence est 18,8, pas 26.** La fourchette, elle,
reste valable : l'effet est massif et certain.

**Ce qui protège — établi :**

| | Effet | Fourchette |
|---|---:|---:|
| **Réponse du patron sous l'avis** | **3,7 fois moins supprimé** | 2,6 à 5,1 |
| Auteur ayant écrit 21 à 100 avis | 1,4 fois moins | 1,1 à 1,8 |

**Ce qui ne joue pas** — la fourchette contient 1, donc aucun effet démontré :

- la longueur du texte, et le fait d'avoir un texte ou non ;
- **les photos** (0,77, fourchette 0,57 à 1,04) ;
- la langue de l'avis ;
- **être Local Guide niveau 6 ou plus** (0,71, fourchette 0,43 à 1,15) ;
- avoir un compteur d'avis à zéro ;
- écrire sur plusieurs entreprises du panel ;
- les notes 3 et 5 étoiles.

### La réponse du patron a été vérifiée

C'est le seul levier actionnable par le client, donc le résultat le plus exposé. L'objection à
écarter : peut-être que le patron répond seulement aux avis qui ont survécu assez longtemps, et
alors la réponse serait une conséquence de la survie, pas une protection.

Vérification faite avec `verif_reponse_proprietaire.py` :

- **Le patron répond vite.** Délai médian de 1 jour. 78 % des réponses arrivent dans les 2 jours,
  93 % dans les 7 jours.
- **Sur les 1 406 avis supprimés qui avaient une réponse, les 1 406 l'avaient reçue avant leur
  suppression.** Aucune exception.

L'inversion est donc écartée. Il reste une réserve : quand on ne compte la réponse qu'à partir
du jour où elle existe vraiment, l'écart brut se réduit de 0,86 à 0,94. Il faut refaire
l'analyse B avec la réponse datée avant de donner un chiffre définitif au client.

Le contrôle sans les 24 entreprises massacrées ne déplace aucun de ces résultats. **L'analyse B
est la partie la plus solide de l'étude.**

## 7. Un argument du livrable est à réécrire

Il circulait cette formule : « ne pas être inscrit au programme Local Guides de Google multiplie
par 16 le risque de suppression ».

**Elle est fausse sur les avis récents**, qui sont pourtant le cœur de l'étude.

Sur les avis récents, 96 % des auteurs « sans niveau Local Guide » ont aussi un compteur d'avis à
zéro. Ta vérification manuelle sur 30 profils l'a confirmé : 19 sur 20 affichent aujourd'hui un
niveau 1 ou 2 et un seul avis à leur actif. **Ce ne sont pas des non-inscrits, ce sont des comptes
créés la veille.** Google n'avait pas encore eu le temps de leur attribuer un niveau.

Et se méfier d'un compte créé la veille, ce n'est pas une erreur de modération. C'est normal.

| Avis récents | Nombre | Supprimés |
|---|---:|---:|
| Auteur avec un niveau et des avis | 93 184 | 2,2 % |
| Auteur avec un niveau, compteur à zéro | 8 397 | 4,3 % |
| **Auteur sans niveau, compteur à zéro (compte neuf)** | **4 966** | **7,5 %** |

La formule ne vaut que pour les **vieux** avis. Là, la vérification sur 45 profils montre de
vrais comptes actifs — 52 avis en moyenne, certains remontant à 2012 — qui ne se sont jamais
inscrits au programme. **Deux populations, deux arguments, à ne jamais mélanger.**

---

# Partie C — Ce qui reste avant le 15 septembre

## À finir

1. ~~La marge d'erreur de l'analyse B.~~ Fait.
2. ~~Vérifier la réponse du patron.~~ Fait : l'inversion est écartée, les 1 406 réponses
   précèdent la suppression. **Reste à refaire l'analyse B avec la réponse datée** pour donner
   un chiffre définitif : l'écart brut se réduit de 0,86 à 0,94 quand on date la réponse.
3. **Réécrire l'argument Local Guide** en le rattachant aux vieux avis, ou le retirer.

## Décisions qui t'appartiennent

4. **Comment faire entrer l'âge dans les modèles** : courbe continue (plus juste) ou tranches
   (plus facile à expliquer). Recommandation : courbe pour calculer, tranches pour présenter.
5. **Enquêter ou non sur les 8 vitrines endormies vidées.** Ce n'est pas au programme initial,
   c'est le phénomène le plus étrange du jeu de données, et il colle exactement à l'angle du
   livrable. Coût : quelques heures.

## Optionnel

6. **Test 3** — dans les services à domicile, un client géographiquement éloigné est-il plus
   supprimé ? Ne concerne que 5 % des avis, donnera probablement une réponse floue.
7. **Le contrôle par machine learning** — vérifier qu'aucun signal n'a été manqué.

---

# Ce qu'il ne faut pas dire à Axel en l'état

- ❌ « Les entreprises à fort afflux d'avis sont 5 fois plus touchées sur leur vieux stock. »
  → 9 cas seulement, c'est du bruit.
- ❌ « Ne pas être inscrit au programme Local Guides multiplie par 16 le risque. »
  → Vrai sur les vieux avis, faux sur les récents.
- ❌ « Le secteur sport et bien-être perd 3,6 fois plus d'avis. »
  → Deux salles de sport espagnoles portaient tout le résultat.
- ❌ « Les photos protègent un avis. » ❌ « Être Local Guide niveau 6 protège. »
  → Les deux fourchettes contiennent 1 : aucun effet démontré.
- ❌ « La rafale multiplie le risque par 26. »
  → La valeur de référence est 18,8. Le 26 vient de la méthode rapide, qui la surestime.
- ⚠ « Répondre aux avis protège 3,7 fois. »
  → L'inversion causale est écartée, mais le chiffre doit être recalculé avec la réponse datée
  avant d'être donné au client.
- ✅ « Sur 100 avis supprimés, 94 n'ont rien de répréhensible dans leur texte. »
- ✅ « Les avis de plus d'un an disparaissent 1,5 à 1,7 fois plus dans les vitrines où Google
  fait le ménage, alors qu'ils n'ont aucun rapport avec ce ménage. »
- ✅ « Google ne sanctionne pas une entreprise parce qu'elle reçoit beaucoup d'avis. »
- ✅ « 84 % des entreprises n'ont rien perdu ; 24 en concentrent 18 %. »
