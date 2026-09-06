# 1. Objet et périmètre

**Question : quelles caractéristiques d'un avis sont associées à sa suppression par Google, et lesquelles ne le sont pas.**
Angle : les faux positifs (suppressions d'avis potentiellement légitimes).
Périmètre : on étudie les suppressions en général, sans distinguer vrais faux avis et faux positifs (indistinguables par scraping). Argument : si une caractéristique anodine prédit fortement la suppression, c'est un indice indirect de faux positifs.
Données : ~10 000 enseignes, ≥100 avis chacune, suivies 10 jours. Classées par taille (mono / petit groupe 5-10 / gros groupe 10+) et secteur.
Limite assumée : on capte les suppressions rapides (10 jours), pas les révisions de stock à 6 mois.

# 2. Variable cible et caractéristiques directement accessibles par scrapping

Cible :

- avis supprimé (1)
- toujours en ligne (0)

Caractéristiques disponibles :

- Note de 1 à 5
- Date & heure de publication ( ! Dernière mise à jour )
- Texte (contenu)
- Présence de photo
- Nombre de photos
- Caractéristiques de l’auteur accessible :
    - nom
    - prénom
    - local guide
    - nombre de reviews
    - nombre de photos
- Autres ?

Caractéristiques de l’établissement :

- Nombre total de review
- date de dernière mise à jour
- Adresse
- Téléphone
- Note moyenne de l’établissement
- Complétion de la fiche
- Autres infos ?

C.F. Doc

# 3. Analyses

**Niveau 1 — bivarié (proportions)**
Pour chaque caractéristique prise seule, comparer sa fréquence chez les supprimés vs les live. Grosse différence → critère candidat ; pas de différence → pas un critère. Sortie descriptive et communicable. À définir de notre côté : la liste des caractéristiques à inclure (voir §4).

**Niveau 2 — régression logistique**
Mesure l'effet de chaque caractéristique une fois retiré l'effet des autres (effet « à note égale, à photo égale »). Corrige les corrélations trompeuses du bivarié et donne des effets chiffrés et directionnels, interprétables. À définir de notre côté : la liste des caractéristiques à inclure (qui découlent de 1), et les interactions à tester (voir §4).

**Niveau 3 — random forest (optionnel).**
Modèle à base d'arbres, utile pour aller plus loin. Il capte seul des effets que la régression logistique ignore par défaut : interactions non prévues et relations non linéaires (ex. un effet qui n'apparaît qu'aux notes extrêmes). À utiliser en complément, pour vérifier qu'on n'a pas manqué d'effet.

# 4. Sélection caractéristiques et interactions

Caractéristiques à inclure pour le Niveau 1 :

- Note 1  à 5
- Texte (contenu)
    - **Présence ou non de contenu (longueur > 0 ou 0)**
    - **longueur par segment** de xxx caractères ou x mots (à définir par rapport à la moyenne ou la médiane ?)
    - Présence d’insulte O/N (à voir si pertinent)
    - **Présence d’un prénom d’un employé O/N – Librairie python**
    - Présence d’un nom complet VS prénom
    - Qualité du contenu (hors-sujet) (classificateur, à voir si pertinent) – Attention au coût d’évaluation
    - Langue ( % business )
- Photos :
    - **Oui / Non**
    - **Nombre de photos**
- Auteur :
    - **local guide O/N**
    - **nombre de reviews**
    - photo de l’auteur
- Fréquence de publication pour l’enseigne au moment de la publication de l’avis
    - **Vélocité (# reviews / période de temps – Ex: 30d)**
    - **Écart à la Moyennes mobile**
        - 90 jours

Variables de contexte (cf §5) :

- **la taille**
- **le secteur**

Caractéristiques à inclure pour le Niveau 2 :

- Choix en gras au-dessus

**Interactions à tester :**

- à définir par expertise métier ou à définir par rapport aux croyances pour les infirmer / confirmer (post analyse niveau 1)
    - Exemple :
        - Nbre de reviews X longueur du segment
        - Local Guide X Qualité du contenu
        - Photo X Note
        - etc.
- Question à résoudre : quels sont les caractéristiques à traiter qui peuvent être actionnables par le client ?

## 5. Choix d'architecture à trancher

**Architecture proposée** : un modèle unique, la taille et le secteur en variable de contexte, deux études géographiques (US et Europe).

### 5.1 Périmètre : combien d'avis et d'enseignes on prend

Deux décisions d'échantillonnage de même nature (tout prendre ou plafonner).

- **Enseignes par groupe** : toutes les enseignes de chaque groupe (proposé). On ne plafonne pas, puisque la taille est une variable du modèle.
- **Avis par établissement** : prendre tous les avis récents par établissement. Proposition : on se fixe une date ou X reviews. Récupéré l’historique si besoin (rythme de publication, voir §2). Reste à fixer la frontière « récent », de préférence en ancienneté.

### 5.2 Dépendance : corriger le fait que les avis liés se ressemblent

La dépendance existe à deux étages, même mécanisme :

- **établissement** : tous les avis d'un établissement partagent ses variables d'établissement (note moyenne, complétion de la fiche d’établissement, nombre de review…) à garder en tête si on veut mesurer des effets dessus ;
- **groupe** : les établissements d'un même groupe partagent une politique de modération commune.

Correction :

- **Erreurs-types groupées** (recommandé au départ). Les effets ne changent pas (photo, prénom… gardent leur valeur) ; seule change la marge d'incertitude annoncée. Comme les avis liés apportent moins d'informations indépendantes que leur nombre ne le suggère, la correction fait compter les entités indépendantes plutôt que les avis, d'où des p-values plus honnêtes. **Point clé** : regrouper au bon niveau = l'identifiant le plus englobant disponible (le groupe si l'enseigne est en groupe, l'établissement sinon), pour couvrir les deux étages d'un coup et ne pas oublier les mono-enseignes.
- **Modèle multiniveau** (plus lourd). Distingue explicitement les étages (avis / établissement / groupe) et estime la part de suppression propre à chaque niveau. Pertinent seulement si les variables d'établissement deviennent un objet d'analyse central.

### 5.3 Déséquilibre : éviter que les gros dominent

Deux déséquilibres de même nature (non réglés par 5.2) :

- **gros groupes** (50 établissements vs une mono-enseigne) ;
- **gros établissements** (10 000 avis vs 50) — seulement si « tous les avis » retenu en 5.1 ; disparaît si on plafonne.

Traitement commun :

- vérification a posteriori : relancer sans les plus gros et vérifier que les conclusions tiennent ;
- ou pondération : donner à chaque groupe/établissement un poids choisi plutôt que son nombre brut.

## 6. Points à valider

- Insultes : hypothèse que Google filtre les insultes avant publication, donc absentes de l'échantillon. À vérifier sur un échantillon réel avant de décider de garder ou non cette caractéristique.

## 7. Next Steps

**Cadrage des données**

- Lister toutes les caractéristiques accessibles sans coût (fiche établissement + avis).
- Trancher le périmètre d'avis : X récent ou tout à partir de DATE.

**Choix de modélisation**

- Définir les caractéristiques à tester (réfléchir à ce sur quoi on peut agir).
- Définir les interactions à tester (expertise métier / croyances à infirmer-confirmer).
- Trancher les arbitrages du §5 : correction de la dépendance, traitement du déséquilibre.

**Validation**

- Identifier les caractéristiques actionnables par le client.
- Vérifier l'hypothèse insultes (§6) sur un échantillon réel.
- Pilote et validation des solutions choisies.

Partie 1 : l’analyse une fois les résultats obtenus.

Partie 2 : Diffusion et promotion du résultat. Quel angle mettre en avant ?

Regarder SEO / fuite des éléments du scoring de l’algo.