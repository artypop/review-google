# Contrôle par apprentissage automatique (XGBoost) et caractéristiques textuelles

Date : 2026-09-16.
Ce document consigne les résultats du contrôle L15 du backlog, exécuté par `python/10_xgboost_controle.py`.

---

## 1. Ce que le test apporte au projet

Le modèle d'arbres de décision (XGBoost) avec caractéristiques textuelles a été entraîné sur le panel de 225 757 avis et évalué sur un quart des établissements mis de côté (environ 52 000 avis de test, auteurs partagés retirés).

### A. La capacité à classer valide la régression logistique

| Périmètre | AUC Régression logistique | AUC XGBoost (avec texte) | Écart |
|---|---:|---:|---:|
| Ensemble du panel | 0,860 | 0,866 | +0,006 |
| Sans les six enseignes signalées | 0,800 | 0,800 | 0,000 |
| États-Unis | 0,860 | 0,858 | −0,002 |
| États-Unis sans les enseignes | 0,810 | 0,820 | +0,010 |
| Europe | — | 0,844 | — |
| Europe sans les enseignes | — | 0,807 | — |

L'AUC de XGBoost est pratiquement identique à celle de la régression logistique. Ce résultat démontre que la régression logistique ne passe à côté d'aucun mécanisme non linéaire majeur sur les données du panel.

### B. Les mêmes facteurs dominent

Les variables qui réduisent le plus l'erreur dans les arbres sont identiques à celles qui portent les plus forts coefficients dans la régression logistique :
1. **L'âge de l'avis** (`log_age_vague1` et `age_a_la_vague1_j`) totalise 13,6 % du gain global.
2. **Le secteur des services à domicile** (`secteur_home_services`) apporte 5,0 % du gain.
3. **La région** (`region_US`) représente 4,7 % du gain.
4. **La note de l'avis** (`star` et `etoiles_5`) apporte 4,8 % du gain.
5. **Le profil de l'auteur** (`profil_guide_etabli`) contribue pour 2,4 % du gain.

### C. La contribution des caractéristiques textuelles

L'intégration du texte brut apporte des signaux complémentaires :
- Aux États-Unis, le mot `excellent` entre dans le top 10 des variables (1,6 % du gain), ce qui reflète la surreprésentation des avis élogieux 5 étoiles parmi les suppressions américaines.
- Les points d'interrogation (`texte_pts_interrogation`), le nombre de mots (`texte_mots`) et la longueur en caractères (`texte_chars`) apportent chacun entre 0,8 % et 1,0 % du gain.
- Les caractéristiques textuelles affinent les prédictions individuelles sans modifier la hiérarchie principale dominée par l'âge, le secteur et la note.

### D. Les interactions détectées

Les successions de divisions dans les arbres mettent en évidence deux interactions principales :
1. **Secteur des services à domicile × Note** : l'effet de la note est amplifié dans les services à domicile (gain d'interaction : 86 826).
2. **Région × Note** : la note 5 étoiles pèse lourdement aux États-Unis, tandis que la note 1 étoile pèse en Europe (gain d'interaction : 44 573).

---

## 2. Les réserves méthodologiques

1. **La part dominante de l'âge** : plus de la moitié de la capacité de classement est portée par l'âge de l'avis au premier passage du robot.
2. **Le déséquilibre de classe** : 2 595 suppressions sur 225 757 avis (1,15 %). La pondération inverse des classes permet au modèle de classer correctement, mais les probabilités prédites doivent être lues avec la courbe de calibration.
3. **Le vocabulaire restreint** : le TF-IDF porte sur 50 termes discriminants. Il isole les mots les plus fréquents sans couvrir la totalité du lexique spécialisé de chaque secteur.
