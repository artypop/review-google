Sélection des listings

Plan de travail — étude suppressions d'avis Google

**Deleted Reviews Study, Panel Summary**

# Analyse de suppression d'un avis : note de méthode

## 1. Objectif

Identifier, parmi les éléments connus au moment où un avis est publié, ceux qui prédisent sa suppression ultérieure par Google, et distinguer les facteurs qui agissent seuls de ceux qui ne pèsent qu'en combinaison.

## 2. Choix du périmètre

Proposition d’une étude générale qui récolte tous les avis d’un panel d’entreprises à T et qui observe lesquels disparaissent au relevé suivant (T+1) (passage d'un filtre, re-scan, signalement). 

Deux fils directeurs sont retenus pour orienter l’étude qui cherchent à rétro-concevoir les signaux que Google utilise, à partir de ce qui survit comparé à ce qui meurt :

1. **Vérification de la visite réelle** : Google contrôle-t-il, d'une manière ou d'une autre, que l'auteur s'est effectivement rendu sur place (ou est-ce que l’avis est plausible compte tenu de la zone desservie) ?
2. **Détection des politiques incitatives** : Google repère-t-il les avis issus d'une sollicitation interdite (QR code en salle, jeu-concours,  avis qui sautent ensemble sur plusieurs fiches d'une même enseigne après une campagne sur l’ensemble des franchisés.) ?

## 3. Le corpus et les hypothèses

Le corpus est l'ensemble des avis présents sur les fiches suivies, comparés entre deux relevés successifs espacés d'un intervalle adapté (hebdomadaire, par exemple) : un premier relevé noté T, un second noté T+1.

*Attention : La cadence (un avis compté comme supprimé dès une absence en T+1, ou seulement après confirmation sur T+1 et T+2) est à déterminer, après avoir mesuré la part d'avis disparus qui réapparaissent au relevé suivant : négligeable, T+1 suffit ; sinon, on exige la confirmation.*

Les fiches sont celles de clients de ReviewFlowz, le choix géographique est à déterminer (États-Unis et/ou Europe du Sud).

Proposition de répartition en quatre segments choisis pour tester les hypothèses :

- **r~~éseaux franchisés** (restaurants, hôtels) : le client, local ou touriste, vient sur place, il peut noter a posteriori ou sur place (potentiellement source de campagne ou d’incitation) ;~~
- Petits groupes de restaurants et hôtels.
- **tour-opérateurs et organisateurs d'activités** : le client est généralement un touriste qui va noter à distance ;
- **services à domicile** : l'adresse Google est un bureau où personne ne se rend (exemples : plombier, déménageur) ;
- **sociétés de proximité** : l'adresse correspond au lieu de service, la clientèle est locale ; sert de référence pour les trois autres segments (exemple : avocats)

Faire catégories homogènes pour construire le dataset et définir plus finement les catégories de google.

Définir un protocole pour construire la liste.

France / UK ?

500 et 5000 review

Répartition gaussienne des 

**Hypothèses principales**

1. **Vitesse de collecte** : une fiche qui reçoit beaucoup d'avis d'un coup en perd-elle davantage ?
2. **Solidité du compte de l'auteur** : les avis de comptes faibles (récents, sans photo, sans historique, hors Local Guide) sautent-ils plus que ceux de comptes établis ?
3. **Adresse et provenance** : les fiches dont l'adresse ne correspond pas au lieu de service, avec clientèle non locale, perdent-elles plus d'avis ?
4. **Contenu et format** : qu'est-ce qui survit le mieux (texte + photo, avis court, note seule) ? Un avis citant le nom d'un employé saute-t-il plus ?
5. J’ajoute le volume de reviews de base (au début du test) – Qui nous permettra de justifier de pas bleed trop sur le scraping (pas besoin de scrap que des profils qui ont 10K reviews).

**Autres pistes** : suppressions synchronisées sur plusieurs fiches d'un réseau après une campagne ? ; avis sincère, mais dont la rédaction ressemble (ou a été amélioré) par IA ? ; fragilité accrue juste après modification de la fiche de l’entreprise (nom, adresse, catégorie)…

**Cible à prédire.** Chaque ligne du corpus est un avis présent en T. La cible, notée **Y** : `0` si l'avis est toujours là en T+1, `1` s'il a disparu entre les deux.

**Exclusions, traitées en amont du jeu de données :**

- on retire les avis disparus parce que la fiche de l'entreprise a été supprimée entre T et T+1 (autre cause de disparition, sans rapport avec l'avis) ;
- on retire les avis disparus parce que le compte de l'auteur est tombé (quarantaine, purge massive de faux comptes) (autre mécanisme, qui demande un protocole différent (analyser l'ensemble des avis d'un compte pour repérer le motif)).
- on retire les avis qui sont apparus entre T et T+1.

Conséquence : Y ne capture que les suppressions d'avis « à la pièce », celles qui nous intéressent. C'est aussi pourquoi le taux de suppression attendu dans le corpus devrait être inférieur aux chiffres bruts communiqués par Google (25 %).

Liens : https://transparencyreport.google.com/maps-content/enforcement

https://transparencyreport.google.com/maps-content/protections

https://transparencyreport.google.com/maps-content/overview?lu=page&page=of1:2025&hl=fr

## 4. La méthodologie

Le problème est posé comme une prédiction : à partir des caractéristiques connues d'un avis  en T, prédire s'il aura disparu en T+1.

### Étape 1 : Construire le jeu de données

*Fonction : transformer les deux relevés en un tableau exploitable par le modèle.*

On dresse un dataframe où une ligne = un avis présent en T, une colonne = une caractéristique (les features de la partie 5), et une dernière colonne = la cible Y.

Produit de l'étape : le couple X (le tableau des features) + Y (la cible).

### Étape 2 : Mesurer chaque facteur isolément

*Fonction : repérer vite si un facteur, pris seul, déplace le taux de suppression et sur combien d'avis.*

Avant tout modèle, on regarde les facteurs un par un. Pour chacun, deux chiffres :

- le taux de suppression quand il est présent : la part d'avis supprimés dans le sous-ensemble concerné, noté `P(Y | facteur)` ;
- la couverture : combien d'avis ce facteur concerne, noté `P(facteur)`.

Chaque résultat se dit en une phrase avec un nombre.

Exemple illustratif :

| Sous-ensemble | Taux de suppression | Lecture |
| --- | --- | --- |
| Ensemble du corpus | ~20% | référence |
| Avis 1 étoile | ~25 % | au-dessus de la base |
| Avis 2-3-4 étoiles | ~10 % | sous la base |
| Avis 5 étoiles | ~17 % | proche de la base |
| Segment tour-opérateur | ~40 % | ≈ ×2 vs base |
| Pays de l'auteur ≠ pays de l'établissement | ~26 % | au-dessus de la base |
| Avis contenant une insulte | ~90 % | très fort, mais sur très faibles nombres d’avis (0,01% du corpus) |

Objectif : garder les facteurs qui ont un effet réel et un volume suffisant, écarter les anecdotiques (taux élevé mais quasi personne, comme l'insulte).

Ces taux sont descriptifs et ne corrigent pas la composition par boutique : ils servent seulement à trier les features (laquelle garder, laquelle ajuster). Un effet repéré ici est ensuite confirmé ou infirmé par le modèle et par les tests appariés, jamais présenté seul comme un résultat.

### Étape 3 : Faire tourner le modèle

*Fonction : mettre tous les facteurs en concurrence, pour répondre à deux questions hors de portée du test isolé*

*(a) l'ensemble des facteurs prédit-il réellement la suppression ?*

*(b) lesquels comptent encore une fois les autres pris en compte ?*

Proposition : Random Forest + Arbre de décision

Deux sorties à lire séparément :

- Qualité de la prédiction : la capacité du modèle à classer un avis réellement supprimé devant un avis conservé, mesurée par l'AUC (0,5 = pas mieux que le hasard, 1 = séparation parfaite). On la complète par le décompte des deux types d'erreur, fausses alertes (prédit supprimé, en réalité conservé) et oublis (prédit conservé, en réalité supprimé). C'est ce qui dit s'il existe un motif, et à quel point il est net.
- Importance des facteurs : le poids de chaque facteur une fois tous mis en concurrence (importance de Gini, fournie par le Random Forest). Ce classement diffère de celui de l'étape 2 : un facteur qui ressortait seul peut s'effacer s'il fait double emploi avec un autre, et un facteur discret peut compter en combinaison. Classement indicatif, sensible aux variables à nombreuses modalités.

Validation. On sépare les données en un jeu d'entraînement et un jeu de test, en répartissant par entreprise et par auteur : le modèle ne doit pas être testé sur une entreprise ou un auteur déjà vus à l'entraînement, sinon il reconnaît la boutique ou la personne au lieu d'apprendre une règle. La validation croisée s'appuie sur cette même clé.

Déséquilibre des classes. Les avis supprimés sont minoritaires (estimés à ~20 % du corpus). Si l'on travaille au niveau d'un segment où le taux devient trop faible, on rééquilibre en pondérant les classes : chaque avis supprimé compte alors davantage qu'un survivant, dans le rapport inverse des effectifs.

### Piste d'approfondissement : le texte brut

*Fonction : tester si le texte de l'avis apporte un signal au-delà des features construites.*

Le texte est encodé en vecteur avec un modèle de langage pour creuser d’autres hypothèses dans le texte lui-même.

## 5. Les features à tester (proposition à affiner selon les hypothèses)

Chaque groupe sert à tester les hypothèses de la partie 3. Deux de ces features, la redondance intra-auteur et la proximité auteur ↔ établissement, supposent d'aspirer l'historique de l'auteur. S’il n’est pas possible de le faire pour tous les avis, on propose d’aspirer l’historique seulement pour ceux dont un avis a été supprimé, plus un échantillon à définir de ceux dont l'avis a survécu pour la même fiche entreprise. Conséquence : ces deux features ne sont définies que sur ce sous-ensemble, elles seront donc absentes pour les autres lignes et feront l’objet d’une analyse ciblée.

**Auteur** : teste la *solidité du compte*.

| Feature | Définition / calcul |
| --- | --- |
| Activité récente | Nombre d'avis publiés sur T−1 mois, et sur T−12 mois |
| Sévérité | Note moyenne donnée par l'auteur |
| Statut Local Guide | Statut et niveau ; + indicateur « Local Guide » (seuil) |
| Position dans la distribution | Percentile du nombre d'avis : auteur prolifique vs avis isolé |

**Entreprise** : teste la *vitesse de collecte* et l'*effet secteur*.

| Feature | Définition / calcul |
| --- | --- |
| Catégorie | Catégorie de l'établissement |
| Volume d'avis | Nombre total d'avis reçus |
| Vitesse de collecte | Avis par semaine ; détection des pics |
| Note moyenne | Note moyenne de l'établissement |
| Date de modification | Date de la modification de la fiche pour la dernière fois |

**Avis (contenu & format)** : teste *ce qui survit selon le contenu et la forme*.

| Feature | Définition / calcul |
| --- | --- |
| Note | Note de l'avis |
| Longueur | Nombre de mots, nombre de caractères |
| Langue | Langue détectée |
| Format | Note seule / texte / texte + photo ou vidéo |
| Ton | Classifieur d'intention : cordial, neutre, énervé… |
| Mention d'un employé | Indicateur |
| Redondance intra-entreprise | Texte normalisé (minuscules, ponctuation retirée) puis hashé ; même hash sur plusieurs avis de la même entreprise → marqueur de campagne |
| Redondance intra-auteur | Même principe, regroupé par auteur → marqueur de copier-coller |
| Score IA | La probabilité que l’avis contienne du contenu par IA (ce score reste discutable) |
| Présence Photo | (compte photo) |
| Photo du reviewer | (URL) |
| nom du reviewer |  |

**Géographie** : teste l'*adresse et la provenance*, et alimente la question de la vérification de visite.

| Feature | Définition / calcul |
| --- | --- |
| Localisation de l'avis | Pays / région / ville (selon disponibilité) |
| Discordance de provenance | Indicateur : pays de l'auteur ≠ pays de l'établissement ou région ≠ ou ville ≠ |
| Proximité auteur ↔ établissement | Distance entre l'établissement et l'empreinte géographique de l'auteur. Le centre de gravité des autres lieux qu'il a notés (proxy de provenance, à défaut d'IP ou de GPS) |
|  |  |

**Texte brut** : piste d'approfondissement (cf. partie 4 Méthodologie).

| Feature | Définition / calcul |
| --- | --- |
| Vecteur de l'avis | Encodage de [description de l'entreprise + avis] |

### Faisceau « politique incitative »

Pour la question de la détection des politiques incitatives, on regroupe et on lit ensemble les features qui forment l'empreinte d'une sollicitation organisée. Leur importance combinée dans le modèle *est* la réponse à « sur quoi Google s'appuie pour repérer l'incitation ».

| Signal | Feature mobilisée |
| --- | --- |
| Bouffée d'avis liée à la campagne | Vitesse de collecte / détection de pics (Entreprise) |
| Avis « one-shot » | Position dans la distribution + activité récente (Auteur) |
| Mention d'un employé | Mention d'un employé (Avis). La mention nominative d'un employé est contraire au règlement Google sauf si la prestation est nominative (médecins, avocats…) |
| Texte standardisé | Redondance intra-entreprise (Avis) (avis pré rempli par l’entreprise) |
| Skew positif | Note + format de l'avis |

### Faisceau « vérification visite »

Pour la question de la vérification de la visite réelle on ne dispose ni d'IP ni d'historique de localisation : on ne crée donc pas de feature « l'auteur s'est rendu sur place », qui serait directement observable. On mobilise à la place les features de provenance déjà présentes, qui mesurent à quel point l'auteur est géographiquement crédible pour cet établissement. Leur poids combiné dans le modèle indique si Google sanctionne les avis dont la provenance est implausible, et le contraste entre segments dit *comment*.

| Signal | Feature mobilisée |
| --- | --- |
| Auteur hors de la zone desservie | Proximité auteur ↔ établissement (Géographie) |
| Avis venu d'un autre pays | Discordance de provenance (Géographie). |
| Empreinte de l'auteur incohérente | Localisation de l'avis vs centre de gravité des autres lieux notés sur la période (Géographie) |
| Contexte de l'établissement | Catégorie + segment (Entreprise) : un auteur distant est normal pour un hôtel touristique, anormal pour un commerce de quartier |

## 6. Tests ciblés possibles

La partie ML traite les questions qui se jouent au niveau de l'avis. Deux questions lui échappent par construction, soit parce qu'elles demandent une comparaison *causale* appariée, soit parce que la décision de Google se prend au niveau de la fiche et non de l'avis. Elles font l'objet de tests dédiés, menés après le modèle.

### 6.1 Débordement de la suppression des avis récupérés lors des campagnes sur les avis “sincères”

**Fonction.** Le modèle (faisceau « politique incitative ») montrera si les avis portant la signature d'une campagne (pic de collecte, comptes one-shot, texte standardisé) sont supprimés plus souvent. Mais Google peut sanctionner l'établissement s’il repère une campagne, comme une purge en profondeur et emporter au passage des avis organiques parfaitement légitimes, déposés avant, pendant ou après la campagne. Ce test sert à mesurer si la sanction déborde de l'avis incité vers le stock organique

Principe. Repérer les fiches qui ont lancé une campagne, séparer leurs avis en « campagne » et « organique », et regarder si la suppression frappe seulement les premiers ou aussi les seconds.

**Protocole.**

1. **Identifier les fiches sous campagne.** Sur la durée du suivi, on repère les établissements présentant un pic de collecte net (bouffée d'avis très au-dessus de leur rythme habituel), éventuellement renforcé par la signature du faisceau incitatif (skew 5 étoiles, comptes one-shot, redondance de texte). On peut aussi s’appuyer sur les remontées terrains (informations de campagnes connues par ReviewFlowz). Ces fiches forment le groupe d'étude.
2. **Étiqueter chaque avis de ces fiches.** Pour chaque avis, un marqueur : « campagne » (déposé pendant le pic, et/ou portant la signature) vs « organique » (déposé hors pic, compte établi, pas de signature). L'organique est le stock préexistant qu'on veut surveiller.
3. **Mesurer la suppression dans les deux groupes**, après le pic. Deux quantités : le taux de suppression des avis « campagne », et le taux de suppression des avis « organique » de ces mêmes fiches. Ce dernier comparé au taux organique d'établissements **témoins** comparables n'ayant pas subi de campagne (même période, même secteur, même taille, même note).
4. **Regarder le délai.** À quel moment, après le pic, l'organique commence-t-il à tomber (le cas échéant) ? Une suppression différée de plusieurs semaines/mois est cohérente avec un re-scan déclenché par la détection de la campagne, plutôt qu'avec une modération immédiate.

**Lecture.** Si seuls les avis « campagne » sont supprimés, la sanction est chirurgicale : pas de dommage collatéral, l'incitation est punie sans toucher l'organique. Si en revanche le taux de suppression de l'organique des fiches sous campagne dépasse nettement celui des fiches témoins, la sanction déborde : détectée au niveau de la fiche, elle emporte des avis légitimes.

### 6.2 Vérification de la visite réelle

**Fonction.** Le modèle (faisceau « vérification visite ») montrera si la proximité auteur↔établissement pèse dans la suppression, mais pas *pourquoi*. Un avis lointain peut sauter parce que Google juge la visite implausible (ce qu'on veut établir) ou parce qu’il s’agit de comptes de mauvaise qualité (fermes à avis offshore). Ce test sert à séparer ces deux explications.

**Principe.** Comparer, à l'intérieur d'une même fiche, des avis comparables sur tout sauf la provenance de l'auteur, et regarder si le lointain est supprimé plus souvent que le proche.

**Protocole.**

1. **Segment : services à domicile** (plombier, déménageur). À cette adresse, un bureau, personne ne se rend : le client légitime est forcément « lointain » par rapport au point de vente. Si Google exigeait une visite sur place, il supprimerait *tous* les avis de ces fiches. Le segment neutralise donc la question parasite « faut-il être allé au point GPS » et isole la seule vraie question : la provenance est-elle plausible au regard de la *zone desservie* ?
2. **Comparaison intra-fiche.** Rangement des avis d'une fiche en tranches selon les variables à neutraliser : note (la valeur en étoiles), longueur (court, moyen, long), langue (locale ou étrangère), solidité du compte (faible ou établi). Dans chaque tranche, on sépare les auteurs locaux des auteurs manifestement hors zone.
3. **Mesure.** Dans chaque tranche, on calcule le taux de suppression des locaux et celui des hors-zone, puis on agrège l'écart sur l'ensemble des tranches en pondérant par leur effectif. On obtient l'écart local / hors-zone à caractéristiques comparables, sans paires exactes.

**Lecture.** Si le hors-zone saute significativement plus, à compte équivalent, Google sanctionne l'implausibilité géographique, et non la faiblesse du compte.