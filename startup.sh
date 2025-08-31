#!/bin/bash

# startup.sh

echo "🚀 Démarrage du runner AlphoGenAI..."

# 1. Aller dans /app
cd /app

# 2. Cloner le dépôt GitHub
git clone https://github.com/alpahoo/alphogenai-runner.git .

# 3. Installer les dépendances Python
pip install -r requirements.txt

# 4. Lancer le script principal
python app.py