"""
Application Streamlit pour l'optimisation de portefeuille.
"""
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
import sys
import os

# Ajouter le répertoire parent au chemin pour pouvoir importer les modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from simple_portfolio import (
    calculate_returns,
    calculate_portfolio_metrics,
    optimize_portfolio
)

# Configuration de la page
st.set_page_config(
    page_title="Optimisation de Portefeuille",
    page_icon="📈",
    layout="wide"
)

# Titre et description
st.title("📊 Optimisation de Portefeuille d'Investissement")
st.markdown("""
Cette application vous permet d'optimiser votre portefeuille d'investissement en utilisant la théorie moderne du portefeuille (MPT) et des modèles d'apprentissage automatique.
""")

# Afficher des informations sur les données
with st.expander("ℹ️ Informations sur les données"):
    st.markdown("""
    ### Source des données
    Les données utilisées dans cette application sont récupérées via Yahoo Finance. Elles incluent les prix historiques des actions et sont utilisées pour calculer les rendements journaliers.

    ### Prétraitement
    Les données brutes sont prétraitées pour :
    - Calculer les rendements journaliers
    - Supprimer les valeurs aberrantes
    - Gérer les valeurs manquantes

    ### Mise à jour des données
    Pour mettre à jour les données avec les dernières informations du marché, exécutez :
    ```bash
    python collect_real_data.py
    ```
    """)

# Sidebar pour les paramètres
st.sidebar.header("Paramètres")

# Sélection des actifs
default_tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'JPM', 'V', 'PG']
selected_tickers = st.sidebar.multiselect(
    "Sélectionner les actifs",
    options=default_tickers,
    default=default_tickers[:5]
)

# Paramètres d'optimisation
st.sidebar.subheader("Paramètres d'optimisation")
risk_free_rate = st.sidebar.slider("Taux sans risque (%)", 0.0, 5.0, 1.0) / 100
n_portfolios = st.sidebar.slider("Nombre de portefeuilles à simuler", 1000, 10000, 5000)

# Chargement des données
@st.cache_data
def load_data():
    try:
        # Essayer de charger les données réelles
        prices = pd.read_csv('data/raw/stock_prices.csv', index_col=0, parse_dates=True)
        returns = pd.read_csv('data/processed/returns.csv', index_col=0, parse_dates=True)
        return prices, returns
    except FileNotFoundError:
        st.warning("Données réelles non trouvées. Génération de données simulées pour la démonstration...")

        # Générer des données simulées
        np.random.seed(42)

        # Créer des dates
        dates = pd.date_range(start='2020-01-01', end='2023-12-31', freq='B')

        # Liste des tickers
        tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'JPM', 'V', 'PG']

        # Générer des prix simulés
        prices_data = {}
        for ticker in tickers:
            # Prix initial aléatoire entre 50 et 500
            initial_price = np.random.uniform(50, 500)

            # Générer des rendements journaliers avec une tendance haussière
            daily_returns = np.random.normal(0.0005, 0.015, size=len(dates))

            # Calculer les prix cumulatifs
            price_series = initial_price * (1 + daily_returns).cumprod()

            prices_data[ticker] = price_series

        # Créer un DataFrame de prix
        prices = pd.DataFrame(prices_data, index=dates)

        # Calculer les rendements
        returns = prices.pct_change().dropna()

        # Créer les répertoires si nécessaires
        os.makedirs('data/raw', exist_ok=True)
        os.makedirs('data/processed', exist_ok=True)

        # Sauvegarder les données simulées
        prices.to_csv('data/raw/stock_prices.csv')
        returns.to_csv('data/processed/returns.csv')

        st.success("Données simulées générées avec succès pour la démonstration!")
        return prices, returns

prices, returns = load_data()

if prices is not None and returns is not None:
    # Filtrer les données pour les actifs sélectionnés
    if selected_tickers:
        returns_filtered = returns[selected_tickers]
    else:
        st.warning("Veuillez sélectionner au moins un actif.")
        returns_filtered = returns[default_tickers[:5]]

    # Calculer les métriques du portefeuille
    expected_returns, cov_matrix = calculate_portfolio_metrics(returns_filtered)

    # Optimisation du portefeuille
    with st.spinner("Optimisation du portefeuille en cours..."):
        frontier, optimal_weights = optimize_portfolio(expected_returns, cov_matrix, n_portfolios)

    # Afficher les résultats dans deux colonnes
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Frontière Efficiente")

        # Créer un graphique interactif avec Plotly
        fig = px.scatter(
            frontier, x='Volatility', y='Return',
            color='Sharpe', color_continuous_scale='viridis',
            title='Frontière Efficiente',
            labels={'Volatility': 'Volatilité (Risque)', 'Return': 'Rendement Attendu', 'Sharpe': 'Ratio de Sharpe'}
        )

        # Ajouter le portefeuille optimal
        max_sharpe_idx = frontier['Sharpe'].idxmax()
        fig.add_trace(go.Scatter(
            x=[frontier.loc[max_sharpe_idx, 'Volatility']],
            y=[frontier.loc[max_sharpe_idx, 'Return']],
            mode='markers',
            marker=dict(size=15, color='red'),
            name='Portefeuille Optimal'
        ))

        # Ajouter la ligne du taux sans risque
        max_vol = frontier['Volatility'].max()
        max_ret = frontier.loc[max_sharpe_idx, 'Return']
        fig.add_trace(go.Scatter(
            x=[0, max_vol * 1.2],
            y=[risk_free_rate, risk_free_rate + (max_ret - risk_free_rate) * 1.2],
            mode='lines',
            line=dict(color='red', dash='dash'),
            name='Ligne du Marché des Capitaux'
        ))

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Allocation du Portefeuille Optimal")

        # Créer un DataFrame pour l'allocation
        allocation = pd.DataFrame({
            'Actif': returns_filtered.columns,
            'Poids': optimal_weights
        })
        allocation = allocation.sort_values('Poids', ascending=False)

        # Créer un graphique interactif avec Plotly
        fig = px.bar(
            allocation, x='Actif', y='Poids',
            title='Allocation du Portefeuille Optimal',
            labels={'Actif': 'Actif', 'Poids': 'Poids dans le Portefeuille'},
            color='Poids', color_continuous_scale='viridis'
        )

        st.plotly_chart(fig, use_container_width=True)

    # Afficher les métriques du portefeuille optimal
    st.subheader("Métriques du Portefeuille Optimal")

    # Calculer les métriques
    optimal_return = frontier.loc[max_sharpe_idx, 'Return']
    optimal_volatility = frontier.loc[max_sharpe_idx, 'Volatility']
    optimal_sharpe = frontier.loc[max_sharpe_idx, 'Sharpe']

    # Afficher les métriques dans trois colonnes
    metric_col1, metric_col2, metric_col3 = st.columns(3)

    with metric_col1:
        st.metric(
            label="Rendement Annuel Attendu",
            value=f"{optimal_return:.2%}"
        )

    with metric_col2:
        st.metric(
            label="Volatilité Annuelle",
            value=f"{optimal_volatility:.2%}"
        )

    with metric_col3:
        st.metric(
            label="Ratio de Sharpe",
            value=f"{optimal_sharpe:.2f}"
        )

    # Afficher le tableau des poids
    st.subheader("Poids du Portefeuille Optimal")

    # Formater les poids en pourcentage
    allocation['Poids (%)'] = allocation['Poids'] * 100
    st.dataframe(allocation[['Actif', 'Poids (%)']], use_container_width=True)

    # Analyse des rendements historiques
    st.subheader("Analyse des Rendements Historiques")

    # Convertir l'index en datetime si ce n'est pas déjà fait
    if not isinstance(returns.index, pd.DatetimeIndex):
        returns.index = pd.to_datetime(returns.index, utc=True)

    # Convertir en UTC pour éviter les problèmes de fuseau horaire
    if returns.index.tz is not None:
        returns.index = returns.index.tz_convert('UTC').tz_localize(None)

    # Extraire les dates min et max
    min_date = returns.index.min()
    max_date = returns.index.max()

    # Convertir en date (pas datetime)
    if hasattr(min_date, 'date'):
        min_date = min_date.date()
        max_date = max_date.date()

    # Sélectionner la période
    date_range = st.slider(
        "Sélectionner la période",
        min_value=min_date,
        max_value=max_date,
        value=(min_date, max_date)
    )

    # Convertir les dates sélectionnées en datetime pour le filtrage
    start_date = pd.Timestamp(date_range[0])
    end_date = pd.Timestamp(date_range[1])

    # Filtrer les données par période
    mask = (returns.index >= start_date) & (returns.index <= end_date)
    returns_period = returns.loc[mask]

    # Calculer les rendements cumulés
    cumulative_returns = (1 + returns_period[selected_tickers]).cumprod() - 1

    # Créer un graphique interactif avec Plotly
    fig = px.line(
        cumulative_returns, x=cumulative_returns.index, y=cumulative_returns.columns,
        title='Rendements Cumulés',
        labels={'value': 'Rendement Cumulé', 'variable': 'Actif'}
    )

    st.plotly_chart(fig, use_container_width=True)

    # Téléchargement des résultats
    st.subheader("Télécharger les Résultats")

    # Créer un DataFrame pour les résultats
    results = pd.DataFrame({
        'Actif': allocation['Actif'],
        'Poids (%)': allocation['Poids (%)'],
        'Rendement Attendu (%)': [expected_returns[ticker] * 100 for ticker in allocation['Actif']],
        'Volatilité (%)': [np.sqrt(cov_matrix.loc[ticker, ticker]) * 100 for ticker in allocation['Actif']]
    })

    # Convertir en CSV pour le téléchargement
    csv = results.to_csv(index=False)
    st.download_button(
        label="Télécharger les résultats (CSV)",
        data=csv,
        file_name="portfolio_optimization_results.csv",
        mime="text/csv"
    )

else:
    st.error("Impossible de charger ou de générer les données. Veuillez vérifier les permissions d'écriture dans le répertoire 'data'.")
