import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.api as sm
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

# Configurer matplotlib pour un rendu headless
import matplotlib
matplotlib.use('Agg')

# ==========================================
# 1. GÉNÉRATION DE DONNÉES SYNTHÉTIQUES
# ==========================================
# Nous simulons les données d'utilisateurs d'une plateforme (DataSciencester)
# Variables : Expérience (années), Salaire ($) et Compte Payant Premium (0 ou 1)
np.random.seed(42)
n_samples = 200

# Caractéristiques
experience = np.random.uniform(0, 10, n_samples)
salary = np.random.uniform(20000, 110000, n_samples)

# Probabilité théorique de souscription (Log-odds linéaire + bruit)
# Le coefficient du salaire est faible car l'échelle est grande (ex: 80 000 vs 5 ans d'exp)
logit_p = -3.5 + 0.8 * experience - 0.000025 * (salary - 60000) + np.random.normal(0, 0.5, n_samples)
p = 1 / (1 + np.exp(-logit_p))
paid_account = np.random.binomial(1, p)

# Création du DataFrame
df = pd.DataFrame({
    'experience': experience,
    'salary': salary,
    'paid_account': paid_account
})

# Séparation des features (X) et de la cible (y)
X = df[['experience', 'salary']]
y = df['paid_account']

# Train/Test Split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

# ==========================================
# 2. APPROCHE STATSMODELS (Inférence & Explication)
# ==========================================
print("\n=== [STATSMODELS] Entraînement du modèle ===")
# Statsmodels n'ajoute pas d'intercept (constante) par défaut, il faut le faire manuellement !
X_train_sm = sm.add_constant(X_train)
X_test_sm = sm.add_constant(X_test)

# Ajustement du modèle par maximum de vraisemblance (sans régularisation par défaut)
sm_model = sm.Logit(y_train, X_train_sm).fit()

# Affichage du rapport statistique complet
print(sm_model.summary())

# ==========================================
# 3. APPROCHE SCIKIT-LEARN (Prédiction & Production)
# ==========================================
print("\n=== [SCIKIT-LEARN] Entraînement du modèle ===")
# Scikit-learn applique par défaut une régularisation L2 (Ridge).
# Pour désactiver la régularisation (comparaison équitable avec Statsmodels), 
# la méthode la plus robuste toutes versions confondues consiste à mettre un très grand paramètre C (ex: C=1e10).
# De plus, scikit-learn bénéficie grandement de la mise à l'échelle (scaling) pour converger rapidement.
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Modèle sans régularisation (C très grand pour simuler aucun effet régularisant)
sk_model_unreg = LogisticRegression(C=1e10, solver='lbfgs')
sk_model_unreg.fit(X_train, y_train) # sans scaling pour comparer les coefficients bruts

# Modèle avec régularisation L2 standard (C=1.0, conseillé en machine learning)
sk_model_reg = LogisticRegression(C=1.0, solver='lbfgs')
sk_model_reg.fit(X_train_scaled, y_train)

print("Coefficients Scikit-Learn (Non régularisé - échelle d'origine) :")
print(f"Intercept : {sk_model_unreg.intercept_[0]:.4f}")
print(f"Coefficients : {sk_model_unreg.coef_[0]}")

print("\nCoefficients Statsmodels (échelle d'origine) :")
print(sm_model.params)

# Évaluation sur le jeu de test
y_pred_sm = (sm_model.predict(X_test_sm) >= 0.5).astype(int)
y_pred_sk = sk_model_unreg.predict(X_test)

print(f"\nPrécision Statsmodels sur le jeu de test : {accuracy_score(y_test, y_pred_sm):.2%}")
print(f"Précision Scikit-Learn sur le jeu de test : {accuracy_score(y_test, y_pred_sk):.2%}")

# ==========================================
# 4. CRÉATION ET ENREGISTREMENT DE LA VISUALISATION
# ==========================================
plt.figure(figsize=(12, 6))

# Subplot 1 : Répartition des données d'origine et frontière de décision de Statsmodels
plt.subplot(1, 2, 1)
# Points de données (Payant vs Non Payant)
plt.scatter(df[df['paid_account'] == 1]['experience'], df[df['paid_account'] == 1]['salary'], 
            color='darkblue', marker='o', label='Premium (Réel)', alpha=0.7)
plt.scatter(df[df['paid_account'] == 0]['experience'], df[df['paid_account'] == 0]['salary'], 
            color='darkorange', marker='x', label='Gratuit (Réel)', alpha=0.7)

# Tracer la frontière de décision (z = 0 => const + b1*exp + b2*salary = 0)
# => salary = -(const + b1*exp) / b2
b0, b1, b2 = sm_model.params
exp_vals = np.linspace(0, 10, 100)
salary_boundary_sm = -(b0 + b1 * exp_vals) / b2

# On filtre pour rester dans des valeurs de salaire réalistes
valid_mask = (salary_boundary_sm >= 20000) & (salary_boundary_sm <= 110000)
plt.plot(exp_vals[valid_mask], salary_boundary_sm[valid_mask], color='red', linestyle='--', linewidth=2,
         label='Frontière Statsmodels')

plt.title("Statsmodels - Frontière de décision brute", fontsize=12)
plt.xlabel("Années d'expérience", fontsize=10)
plt.ylabel("Salaire annuel ($)", fontsize=10)
plt.xlim(-0.5, 10.5)
plt.ylim(15000, 115000)
plt.grid(True, linestyle=':', alpha=0.6)
plt.legend()

# Subplot 2 : Comparaison des probabilités prédites (Sigmoïde)
plt.subplot(1, 2, 2)
# Trier par probabilité pour un joli tracé de courbe sigmoïde
probs_sm = sm_model.predict(X_test_sm)
sorted_idx = np.argsort(probs_sm)

plt.scatter(range(len(y_test)), y_test.iloc[sorted_idx], color='gray', marker='|', label='Réalité (0 ou 1)')
plt.plot(range(len(y_test)), probs_sm.iloc[sorted_idx], color='blue', label='Probabilité Statsmodels', linewidth=2)

# Prédiction probabilités Scikit-Learn (Non régularisé)
probs_sk = sk_model_unreg.predict_proba(X_test)[:, 1]
plt.plot(range(len(y_test)), probs_sk[sorted_idx], color='green', linestyle=':', label='Probabilité Scikit-Learn', linewidth=2)

plt.title("Comparaison des probabilités prédites", fontsize=12)
plt.xlabel("Observations du jeu de test (triées)", fontsize=10)
plt.ylabel("Probabilité d'être Premium (Y=1)", fontsize=10)
plt.ylim(-0.05, 1.05)
plt.grid(True, linestyle=':', alpha=0.6)
plt.legend()

plt.tight_layout()
plt.savefig('/workspace/scratch/regression_decision_boundary.png', dpi=150, bbox_inches='tight')
plt.close()

print("\nVisualisation enregistrée avec succès.")

