"""
Point d'entrée pour Streamlit Cloud.
Ce fichier collecte des données réelles via Yahoo Finance avant de lancer l'application.
"""
import streamlit as st

# Configuration de la page - DOIT être appelé en premier
st.set_page_config(
    page_title="Optimisation de Portefeuille",
    page_icon="📈",
    layout="wide"
)

import sys
import os
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import time

# Créer les répertoires nécessaires
os.makedirs('data/raw', exist_ok=True)
os.makedirs('data/processed', exist_ok=True)
os.makedirs('data/logs', exist_ok=True)

# Fonction pour collecter des données réelles
def collect_real_data():
    st.sidebar.title("Collecte de données")

    with st.sidebar.expander("⚙️ Paramètres de collecte", expanded=True):
        # Paramètres de collecte
        start_date = st.date_input(
            "Date de début",
            datetime.now() - timedelta(days=365*5)  # 5 ans par défaut
        )

        end_date = st.date_input(
            "Date de fin",
            datetime.now()
        )

        # Liste des tickers par défaut
        default_tickers = [
            # Indices majeurs
            '^GSPC',  # S&P 500
            '^DJI',   # Dow Jones
            '^IXIC',  # NASDAQ
            # Grandes capitalisations technologiques
            'AAPL',   # Apple
            'MSFT',   # Microsoft
            'GOOGL',  # Alphabet (Google)
            'AMZN',   # Amazon
            'META',   # Meta (Facebook)
            'TSLA',   # Tesla
            'NVDA',   # NVIDIA
            # Grandes capitalisations financières et autres secteurs
            'JPM',    # JPMorgan Chase
            'V',      # Visa
            'PG',     # Procter & Gamble
            'JNJ',    # Johnson & Johnson
            'WMT',    # Walmart
            'XOM',    # Exxon Mobil
            'BAC',    # Bank of America
            'KO',     # Coca-Cola
            'DIS',    # Disney
            'NFLX'    # Netflix
        ]

        # Sélection des tickers
        selected_tickers = st.multiselect(
            "Sélectionner les actifs",
            options=default_tickers,
            default=default_tickers[:10]  # 10 premiers tickers par défaut
        )

        if st.button("Collecter les données"):
            if not selected_tickers:
                st.error("Veuillez sélectionner au moins un actif.")
                return False

            # Afficher un message de chargement
            with st.spinner("Collecte des données en cours..."):
                # Récupérer les données pour chaque ticker
                all_data = pd.DataFrame()

                for ticker in selected_tickers:
                    try:
                        # Récupérer les données via yfinance
                        stock = yf.Ticker(ticker)
                        data = stock.history(start=start_date, end=end_date)

                        if data.empty:
                            st.warning(f"Aucune donnée trouvée pour {ticker}")
                            continue

                        # Ajouter une colonne pour identifier le ticker
                        data['Ticker'] = ticker

                        # Ajouter au DataFrame principal
                        all_data = pd.concat([all_data, data])

                        st.success(f"Données récupérées pour {ticker}: {len(data)} entrées")

                    except Exception as e:
                        st.error(f"Erreur lors de la récupération des données pour {ticker}: {e}")

                if all_data.empty:
                    st.error("Aucune donnée n'a été récupérée.")
                    return False

                # Sauvegarder les données brutes
                all_data_reset = all_data.reset_index()
                all_data_reset.to_csv('data/raw/stock_data.csv', index=False)

                # Prétraiter les données
                # Créer un DataFrame pivot manuellement
                # Réinitialiser l'index pour avoir Date comme colonne
                if 'Date' not in all_data.columns and isinstance(all_data.index, pd.DatetimeIndex):
                    all_data = all_data.reset_index()

                # Créer un dictionnaire pour stocker les séries de prix par ticker
                prices_dict = {}

                # Parcourir les tickers uniques
                for ticker in all_data['Ticker'].unique():
                    # Filtrer les données pour ce ticker
                    ticker_data = all_data[all_data['Ticker'] == ticker]
                    # Créer une série avec Date comme index et Close comme valeurs
                    prices_dict[ticker] = pd.Series(ticker_data['Close'].values, index=ticker_data['Date'])

                # Créer un DataFrame à partir du dictionnaire
                pivot_data = pd.DataFrame(prices_dict)

                # Calculer les rendements journaliers
                returns = pivot_data.pct_change().dropna()

                # Supprimer les valeurs aberrantes (rendements > 50% ou < -50%)
                returns = returns.mask((returns > 0.5) | (returns < -0.5), np.nan)

                # Remplir les valeurs manquantes avec la moyenne des rendements
                returns = returns.fillna(returns.mean())

                # Sauvegarder les rendements
                returns.to_csv('data/processed/returns.csv')

                st.success(f"Prétraitement terminé: {len(returns)} jours de rendements pour {len(returns.columns)} actions")
                return True

    return True  # Par défaut, continuer avec les données existantes ou simulées

# Collecter des données réelles
data_ready = collect_real_data()

if data_ready:
    # Ajouter le répertoire de l'application au chemin
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'app')))

    # Importer et exécuter l'application principale
    import dashboard
else:
    st.error("Impossible de continuer sans données. Veuillez réessayer la collecte de données.")
