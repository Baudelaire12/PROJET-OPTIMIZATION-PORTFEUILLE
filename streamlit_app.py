"""
Point d'entrée pour Streamlit Cloud.
Ce fichier redirige simplement vers l'application principale.
"""
import streamlit as st
import sys
import os

# Ajouter le répertoire de l'application au chemin
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'app')))

# Importer et exécuter l'application principale
import dashboard
