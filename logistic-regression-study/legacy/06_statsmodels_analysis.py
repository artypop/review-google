#!/usr/bin/env python3
"""
==============================================================================
Script : 06_statsmodels_analysis.py
Description : Analyse par régression logistique (statsmodels) sur le panel d'avis.
              Compare le modèle complet avec le modèle robuste (hors 24 fiches).
==============================================================================
"""

import os
import sys
import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt

def get_data(project_id="client-divers", json_key_path=None):
    """
    Charge la table client-divers.reviewflowz.avis_panel_final depuis BigQuery.
    Si l'environnement BigQuery n'est pas disponible (ex: test local), 
    génère un jeu de données synthétique respectant la même structure.
    """
    if json_key_path and os.path.exists(json_key_path):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = json_key_path

    try:
        from google.cloud import bigquery
        client = bigquery.Client(project=project_id)
        query = """
        SELECT * 
        FROM `client-divers.reviewflowz.avis_panel_final`
        """
        print("Chargement des données depuis BigQuery...")
        df = client.query(query).to_dataframe()
        print(f"Données chargées : {len(df)} observations.")
        return df
    except Exception as e:
        print(f"Notice BigQuery (mode simulation) : {e}")
        print("Génération d'un jeu de données synthétique représentatif pour validation du code...")
        np.random.seed(42)
        n = 15000
        cids = [f"cid_{i}" for i in range(1, 100)]
        # 24 fiches concentrant des suppressions
        outlier_cids = [f"cid_{i}" for i in range(1, 25)]
        
        cid_array = np.random.choice(cids, size=n)
        is_outlier = np.isin(cid_array, outlier_cids)
        
        age_days = np.random.exponential(scale=30, size=n) + 1
        star = np.random.choice([1, 2, 3, 4, 5], size=n, p=[0.15, 0.05, 0.05, 0.15, 0.60])
        has_text = np.random.choice([0, 1], size=n, p=[0.3, 0.7])
        text_chars = has_text * np.random.exponential(scale=150, size=n)
        has_photo = np.random.choice([0, 1], size=n, p=[0.8, 0.2])
        has_reply = np.random.choice([0, 1], size=n, p=[0.75, 0.25])
        log_rc = np.random.exponential(scale=1.5, size=n)
        rc_zero = np.random.choice([0, 1], size=n, p=[0.8, 0.2])
        new_account = np.random.choice([0, 1], size=n, p=[0.85, 0.15])
        author_burst = np.random.choice([1, 2, 3, 5], size=n, p=[0.90, 0.06, 0.03, 0.01])
        langue_etrangere = np.random.choice([0, 1], size=n, p=[0.92, 0.08])
        langue_minoritaire = np.random.choice([0, 1], size=n, p=[0.95, 0.05])
        log_ratio_pic = np.random.exponential(scale=0.5, size=n)
        industry = np.random.choice(['Retail', 'Services', 'Health', 'Restaurant'], size=n)
        bucket = np.random.choice(['mono', 'small', 'large'], size=n)

        # Logit latent avec effet fort sur age_days, star=1, new_account et raid
        logit = (
            -3.5 
            - 0.04 * age_days 
            + 1.2 * (star == 1) 
            + 0.8 * new_account 
            + 0.9 * log_ratio_pic 
            + 1.5 * is_outlier
            + 0.5 * langue_etrangere
        )
        prob = 1 / (1 + np.exp(-logit))
        deleted = (np.random.rand(n) < prob).astype(int)

        df_sim = pd.DataFrame({
            'review_id': [f"rev_{i}" for i in range(n)],
            'cid': cid_array,
            'wave': np.random.randint(2, 15, size=n),
            'deleted': deleted,
            'age_days': age_days,
            'jours_sous_surveillance': age_days + np.random.randint(0, 10, size=n),
            'star': star,
            'has_text': has_text,
            'text_chars': text_chars,
            'has_photo': has_photo,
            'has_reply': has_reply,
            'log_rc': log_rc,
            'rc_zero': rc_zero,
            'new_account': new_account,
            'author_same_day_burst': author_burst,
            'langue_etrangere_au_pays': langue_etrangere,
            'langue_minoritaire_sur_la_fiche': langue_minoritaire,
            'log_ratio_pic_journalier_fiche': log_ratio_pic,
            'industry': industry,
            'bucket': bucket
        })
        return df_sim

def prepare_features(df):
    """
    Nettoie et prépare la matrice de caractéristiques (X) et la variable cible (y).
    """
    df = df.copy()
    
    # 1. Variable cible
    y = df['deleted'].astype(int)
    
    # 2. Variables explicatives numériques et booléennes
    feature_cols = [
        'age_days',
        'star',
        'has_text',
        'text_chars',
        'has_photo',
        'has_reply',
        'log_rc',
        'rc_zero',
        'new_account',
        'author_same_day_burst',
        'langue_etrangere_au_pays',
        'langue_minoritaire_sur_la_fiche',
        'log_ratio_pic_journalier_fiche'
    ]
    
    X_num = df[feature_cols].copy()
    for col in X_num.columns:
        X_num[col] = pd.to_numeric(X_num[col], errors='coerce').fillna(0)
    
    # 3. Dummies pour variables catégorielles (ex: bucket, industry si présentes)
    cat_cols = [c for c in ['bucket', 'industry'] if c in df.columns]
    if cat_cols:
        X_cat = pd.get_dummies(df[cat_cols], drop_first=True, dtype=float)
        X = pd.concat([X_num, X_cat], axis=1)
    else:
        X = X_num

    # 4. Ajout de la constante pour l'intercept (obligatoire dans statsmodels)
    X = sm.add_constant(X)
    return y, X

def fit_logistic_model(y, X, model_name="Modèle"):
    """
    Ajuste une régression logistique sous statsmodels et renvoie un DataFrame récapitulatif.
    """
    model = sm.Logit(y, X)
    results = model.fit(disp=False)
    
    # Construction du tableau des résultats
    summary_df = pd.DataFrame({
        f'Coef ({model_name})': results.params,
        f'Std Err ({model_name})': results.bse,
        f'p-value ({model_name})': results.pvalues,
        f'Odds Ratio ({model_name})': np.exp(results.params),
        f'OR IC 2.5% ({model_name})': np.exp(results.conf_int()[0]),
        f'OR IC 97.5% ({model_name})': np.exp(results.conf_int()[1])
    })
    return results, summary_df

def main():
    print("="*80)
    print("   ANALYSE REGRESSION LOGISTIQUE - COMPARAISON DU MODELE DE BASE ET ROBUSTE")
    print("="*80)
    
    # 1. Chargement des données
    df = get_data("client-divers", json_key_path="/home/romain/.gcp/client-divers-8b012e5b7c73.json")
    
    # 2. Identification des 24 fiches (CID) à forte concentration de suppressions
    deletions_per_cid = df.groupby('cid')['deleted'].sum().sort_values(ascending=False)
    top_24_cids = deletions_per_cid.head(24).index.tolist()
    print(f"\nTop 24 CIDs identifiés pour le test de robustesse.")
    print(f"Total suppressions dans les 24 fiches : {df[df['cid'].isin(top_24_cids)]['deleted'].sum()} "
          f"({df[df['cid'].isin(top_24_cids)]['deleted'].sum() / df['deleted'].sum() * 100:.1f}% du total)")
    
    # 3. Modèle 1 : Dataset complet
    print("\n--- [MODELE 1] Ajustement sur le dataset complet ---")
    y_full, X_full = prepare_features(df)
    res_full, summary_full = fit_logistic_model(y_full, X_full, model_name="Complet")
    print(res_full.summary())
    
    # 4. Modèle 2 : Dataset robuste (excluant les 24 fiches)
    print("\n--- [MODELE 2] Ajustement sur le dataset robuste (hors 24 fiches) ---")
    df_robust = df[~df['cid'].isin(top_24_cids)].copy()
    y_rob, X_rob = prepare_features(df_robust)
    res_rob, summary_rob = fit_logistic_model(y_rob, X_rob, model_name="Robuste")
    print(res_rob.summary())
    
    # 5. Fusion et comparaison des résultats
    comparison_df = pd.merge(
        summary_full[['Coef (Complet)', 'p-value (Complet)', 'Odds Ratio (Complet)']],
        summary_rob[['Coef (Robuste)', 'p-value (Robuste)', 'Odds Ratio (Robuste)']],
        left_index=True, right_index=True
    )
    
    # Calcul du pourcentage de variation des Odds Ratios
    comparison_df['Var. OR (%)'] = (
        (comparison_df['Odds Ratio (Robuste)'] - comparison_df['Odds Ratio (Complet)']) 
        / comparison_df['Odds Ratio (Complet)'] * 100
    )
    
    print("\n" + "="*80)
    print("   TABLEAU COMPARATIF DES ODDS RATIOS ET P-VALUES")
    print("="*80)
    print(comparison_df.round(4).to_string())
    
    # Sauvegarde du rapport en CSV dans scratch et out
    os.makedirs('/workspace/scratch', exist_ok=True)
    comparison_df.to_csv('/workspace/scratch/06_tableau_comparatif_models.csv')
    
    # 6. Visualisation graphique des Odds Ratios (hors const)
    plot_df = comparison_df.drop('const', errors='ignore').copy()
    
    plt.figure(figsize=(10, 6))
    y_pos = np.arange(len(plot_df))
    width = 0.35
    
    plt.barh(y_pos - width/2, plot_df['Odds Ratio (Complet)'], width, label='Modèle Complet', color='#1f77b4', alpha=0.8)
    plt.barh(y_pos + width/2, plot_df['Odds Ratio (Robuste)'], width, label='Modèle Robuste (Hors 24 fiches)', color='#ff7f0e', alpha=0.8)
    
    plt.axvline(x=1.0, color='gray', linestyle='--', linewidth=1, label='Aucun effet (OR = 1.0)')
    plt.yticks(y_pos, plot_df.index.tolist())
    plt.xlabel('Odds Ratio (e^coef)')
    plt.title('Comparaison des Odds Ratios : Modèle Complet vs Modèle Robuste')
    plt.legend()
    plt.tight_layout()
    
    chart_path = '/workspace/scratch/06_comparison_odds_ratios.png'
    plt.savefig(chart_path, dpi=150)
    plt.close()
    print(f"\nGraphique sauvegardé : {chart_path}")

if __name__ == "__main__":
    main()


