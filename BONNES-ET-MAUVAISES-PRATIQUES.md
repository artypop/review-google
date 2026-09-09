# Bonnes et mauvaises pratiques

Écrit le 2026-09-08 après une session où la plupart des sorties ont dû être corrigées. Chaque
écueil listé ici s'est produit dans ce projet. Le but est de ne pas y retomber.

À lire avant de produire un chiffre. Les règles de fonctionnement (plan approuvé, relecture par
un sous-agent) sont dans [CLAUDE.md](CLAUDE.md) ; ce document donne les défauts concrets à
chercher.

---

# Partie 1 — Les écueils rencontrés

## 1. Un pourcentage sans son dénominateur

**Ce qui a été écrit** : « 361 avis d'une étoile publiés en deux jours sur une fiche notée 4,95,
soit 24 % de son listing ».

**Le défaut** : le 24 % rapportait le paquet des **deux** fiches (361 avis, comptage périmé) au
listing des **deux** fiches (1 484 avis, comptage périmé), puis présentait le résultat comme la
part du listing d'**une seule** — « de son listing ». Numérateur et dénominateur portaient sur
deux établissements, la phrase sur un.

**Valeurs correctes, chacune sur son propre listing** : 219 avis sur 781, soit 28,0 % pour la
fiche A ; 111 sur 668, soit 16,6 % pour la fiche B.

**Le contrôle** : écrire le dénominateur dans la phrase. « 219 avis sur les 781 de cette fiche,
soit 28 % » n'aurait pas pu passer. Un pourcentage seul cache son erreur ; un pourcentage suivi
de « de ses N avis » l'expose.

## 2. Une part d'un sous-périmètre présentée comme une part du corpus

**Ce qui a été écrit** : « la vague 6 du 16 août porte 35 % des suppressions ».

**Le défaut** : ces 35 % étaient la part du 16 août dans un groupe que j'avais moi-même
construit, pas dans les 4 747 suppressions du corpus. Sur le corpus, le 16 août fait
706 suppressions et le 17 août en fait 760 : il n'y a pas de journée dominante. Les effectifs de
ce groupe ne sont plus reproductibles, le script ayant été supprimé.

**Le contrôle** : avant d'annoncer une part, nommer le dénominateur à voix haute. « 35 % de
quoi ? » Si la réponse est « du groupe que j'ai construit », le chiffre ne peut pas être présenté
comme un résultat sur les données.

## 3. Deux faits sans rapport collés par « soit »

**Ce qui a été écrit** : « sur une fiche notée 4,95 — soit 24 % de son listing ».

**Le défaut** : la note moyenne et la part du listing n'ont aucun lien. Le « soit » laisse
croire que l'un découle de l'autre. Le 4,95 était en plus la note des avis **restés en ligne**,
pas celle affichée par la fiche, qui valait 3,81.

**Le contrôle** : relire chaque « soit », « donc » et chaque tiret. Si les deux membres ne sont
pas la même grandeur exprimée autrement, couper la phrase en deux.

## 4. Un chiffre issu d'un comptage périmé

**Ce qui a été écrit** : 399 suppressions, 264 sur 816, taux de 0,107 %, et le trio
« 84 % des établissements / 39 fiches / 19,5 % » — ce dernier venant de `CLAUDE.md`, la note du
2026-09-06 écrivant « 20 % ».

**Le défaut** : tous ces chiffres viennent du comptage d'avant le retrait des résurrections et
des bugs d'édition. Ils circulaient encore dans sept fichiers le lendemain de la correction.

**Le contrôle** : une seule définition, dans un seul fichier
([`etude-exploratoire/scripts/suppressions_corrigees.py`](etude-exploratoire/scripts/suppressions_corrigees.py)),
importée par tous les scripts. Et un balayage `grep` des anciennes valeurs après chaque
correction de définition, pour poser un bandeau là où elles subsistent.

## 5. Un même mot pour deux choses

**Ce qui a été écrit** : « cohorte » désignait dans la même note le groupe d'avis suivi et les
avis publiés le même jour.

**Le défaut** : le lecteur ne peut plus savoir de quoi on parle, et le rédacteur non plus.

**Le contrôle** : un terme, un concept, sur tout le document. En cas de doute, remplacer le mot
savant par sa définition : « les avis publiés le 10 août » plutôt que « la cohorte du 10 août ».

## 6. Construire pour contourner un problème qui n'existe pas

**Ce qui s'est passé** : trois constructions successives — cohorte des avis nés pendant le
suivi, matrice vague × âge sur un groupe fixe, exposition par âge — toutes destinées à rendre
comparables des âges dont les dénominateurs différaient.

**Le défaut** : le corpus contient environ 32 000 observations à **chaque** âge de 2 à 30 jours.
Le dénominateur était plat. Une requête `GROUP BY age` de trois lignes répondait à la question.

**Le contrôle** : avant de construire quoi que ce soit pour corriger une comparaison, sortir la
colonne des effectifs et la regarder. Si elle est plate, il n'y a rien à corriger.

## 7. Annoncer une conclusion avant son contrôle

**Ce qui a été écrit** : « le pic est un effet d'âge, pas une purge », puis plus tard « le
16 août est une journée à part », deux affirmations posées avant vérification. La seconde était
fausse.

**Le contrôle** : une conclusion sur la cause d'un motif demande au minimum de vérifier son
étalement dans le temps et sur les unités. Pour le pic à 7 jours : 12 des 13 journées,
144 établissements, et survie au retrait des deux journées les plus chargées. Ces trois chiffres
d'abord, la conclusion ensuite.

## 8. Empiler les contrôles dans la note de résultat

**Ce qui s'est passé** : une note a atteint six sections de contrôles pour trois lignes de
résultat. Le commanditaire n'a pas pu la lire.

**Le contrôle** : le résultat d'abord, en clair. Les contrôles dans un tableau à part, une ligne
par contrôle, verdict en un mot. Ce qui a été jeté dans une note de méthode séparée.

## 9. Expliquer la géométrie d'un tableau au lieu de sa lecture

**Ce qui a été écrit** : « les lignes se comparent entre elles, les colonnes ne se comparent pas,
voir le § 3 ». Le lecteur ne savait toujours pas ce que contenait une case.

**Le défaut** : décrire les propriétés d'un tableau n'apprend pas à le lire. Et l'affirmation
était fausse : les **cases** d'une colonne se comparaient très bien, seuls les **totaux** de
colonnes ne se comparaient pas.

**Le contrôle** : commencer par une case précise, en disant ce qu'elle contient et sur quoi elle
se rapporte, avant d'expliquer les sens de lecture. Une phrase de la forme « cette case vaut N,
ces N avis ont tous été publiés le jour J, où M avis sont parus, donc N/M de cette journée »
apprend à lire tout le tableau. (Les chiffres de l'exemple d'origine venaient d'une construction
depuis supprimée, ils ne sont pas repris ici.)

## 10. Enchaîner les analyses sans repasser par le commanditaire

**Ce qui s'est passé** : quatre analyses lancées d'affilée, chacune parce que la précédente
soulevait une question. Trois ont été jetées.

**Le contrôle** : terminer ce qui est approuvé, énoncer la question nouvelle, attendre. La règle
est dans [CLAUDE.md](CLAUDE.md), étape A.

## 11. Ajouter une correction là où il n'y a rien à corriger

**Ce qui s'est passé** : un retour sur un mail contenait une section « ce que je te conseille de
ne pas mettre » sur un argument qui n'était pas dans le mail. C'était en réalité une
rétractation d'un conseil donné la veille.

**Le contrôle** : une rétractation se présente comme telle — « je t'ai dit X hier, c'était
faux » — et non comme un conseil sur le document en cours.

## 12. Répéter un conseil que le commanditaire a déjà écarté

**Ce qui s'est passé** : la même remarque sur le traitement des salles de sport, formulée deux
fois à deux tours d'écart.

**Le contrôle** : une remarque non retenue est une décision. Ne la reformuler que si un élément
nouveau la change, et le dire.

## 13. Chemins relatifs après un `cd`

**Ce qui s'est passé** : un `cd etude-exploratoire/documentations` dans un appel, puis des
chemins relatifs dans l'appel suivant. Le script a échoué sur `FileNotFoundError` après avoir
déjà modifié des fichiers.

**Le contrôle** : chemins absolus dans les scripts qui écrivent, et une assertion sur le nombre
de fichiers trouvés avant de boucler.

## 14. Une hypothèse habillée en fait

**Ce qui a été écrit** : « Google intervient quand le signal est massif », proposé pour
remplacer « probablement à la demande de l'établissement ».

**Le défaut** : les deux sont des hypothèses. Remplacer l'une par l'autre ne rend rien plus
solide, ça déplace juste la conjecture.

**Le contrôle** : nommer l'inférence comme telle et dire sur quoi elle s'appuie. « Ce qui a
déclenché le retrait n'est pas dans les données ; le gérant ayant répondu à une partie de ces
avis, un signalement de sa part est l'hypothèse la plus simple. »

## 15. Corriger la documentation en oubliant le fichier le plus lu

**Ce qui s'est produit** : après la correction du comptage, un bandeau a été posé sur les quinze
documents concernés de `etude-exploratoire/`. `CLAUDE.md`, chargé à chaque session, portait
toujours « 39 fiches concentrent 19,5 % », « 2,67 % » et « 0,107 % » sans avertissement.

**Le défaut** : le fichier d'instructions est le premier lu et le dernier vérifié. Il
recontamine toutes les sessions suivantes.

**Le contrôle** : le balayage des anciennes valeurs commence par `CLAUDE.md` et le `README.md`,
pas par les notes.

---

# Partie 2 — Les bonnes pratiques à garder

## Sur les chiffres

- **Une seule définition, un seul fichier.** La définition d'une suppression vit dans
  `suppressions_corrigees.py` et nulle part ailleurs hors BigQuery. Toute copie finit par
  diverger — c'est le défaut qui a rendu `etude-exploratoire` peu fiable.
- **Le dénominateur dans la phrase**, à chaque pourcentage, sans exception.
- **Un code par définition concurrente.** Trois comptages d'« avis récents supprimés »
  coexistent (2 450, 2 462, 2 540) et sont tous justes. Ils portent maintenant les codes D1, D2,
  D3, avec l'écart entre eux expliqué. Se citent par leur code.
- **Regarder la colonne des effectifs avant de construire.** Elle dit souvent que la
  construction est inutile.
- **Chaque affirmation chiffrée est régénérable** par une commande écrite à côté d'elle.

## Sur les contrôles

- **Trois questions pour distinguer un effet d'un accident** : sur combien de journées ? sur
  combien d'unités ? survit-il au retrait des cas extrêmes ?
- **Vérifier la nature de la donnée avant d'interpréter son motif.** Des pics aux multiples de 7
  auraient pu venir d'une date reconstruite depuis « il y a une semaine ». La répartition horaire
  de `created_at` a écarté cette hypothèse en une requête.
- **Consigner les contrôles avec leur verdict**, pour que personne ne les refasse. Tableau à
  part, une ligne, un mot.
- **Consigner aussi ce qui a été jeté**, sinon la même construction sera reproposée comme neuve.

## Sur la restitution

- **Le résultat d'abord, les réserves ensuite**, jamais mélangés.
- **Commencer par un cas concret** quand on présente un tableau : une case, ce qu'elle contient,
  ce qu'elle vaut.
- **Une analogie de la vie quotidienne** pour un mécanisme abstrait, à condition qu'elle porte
  le mécanisme et pas seulement l'ambiance.
- **Nommer ce que la relecture a rattrapé.** Le commanditaire voit ainsi que l'étape sert, sans
  avoir à la contrôler lui-même.
- **Corriger en une phrase, sans commentaire sur l'erreur.** Pas de bilan, pas d'excuse répétée.

## Sur la conduite de la mission

- **Le plan avant le calcul**, et le tour de parole s'arrête sur le plan.
- **Une question nouvelle ne se traite pas dans la foulée.** Elle s'énonce et elle attend.
- **`nice -n 19` pour tout calcul dépassant deux minutes**, sinon WSL coupe la connexion. Vérifier
  `free -m` avant. Deux calculs lourds au maximum en même temps.
- **Une limite de mémoire explicite dans DuckDB**, et agréger en SQL plutôt que charger en
  pandas. `reviews.parquet` fait 834 Mo.
- **Jamais de nom d'auteur, de lien d'avis ou de texte d'avis dans un document versionné.**
  `data/` est gitignoré et le reste.
