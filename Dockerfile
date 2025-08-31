# ---- Base Python 3.10, légère
FROM python:3.10-slim

# Pour Coqui TTS / soundfile / ffmpeg
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg libsndfile1 espeak-ng && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copie des deps en premier pour tirer parti du cache Docker
COPY requirements.txt ./requirements.txt

# PyTorch CPU (versions compatibles avec TTS==0.22.0)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu \
        torch==2.1.0 torchaudio==2.1.0

# Copie du code
COPY . .

# (Optionnel) pré-télécharger le modèle pour accélérer le 1er démarrage
# Si tu veux pré-charger pendant le build (prolonge le build et ajoute du poids) décommente :
# RUN python -c "from TTS.api import TTS; TTS('tts_models/fr/css10/vits')"

# Port FastAPI
EXPOSE 8000

# Variables utiles dans ton app.py si besoin
ENV PYTHONUNBUFFERED=1 \
    UVICORN_HOST=0.0.0.0 \
    UVICORN_PORT=8000

# Lancement du serveur
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
