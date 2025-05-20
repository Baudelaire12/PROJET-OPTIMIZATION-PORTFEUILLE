FROM python:3.9-slim

WORKDIR /app

# Installer les dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code source
COPY . .

# Exposer le port pour Streamlit
EXPOSE 8501

# Commande par défaut pour lancer l'application Streamlit
CMD ["streamlit", "run", "app/app.py"]
