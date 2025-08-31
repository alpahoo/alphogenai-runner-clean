# app.py
import os
import uuid
import requests
from TTS.api import TTS
import ffmpeg
import boto3
from dotenv import load_dotenv

# Charger les variables d’environnement
load_dotenv()

def generate_voice_french(text, output_file="narration.wav"):
    print("🔊 Génération de la voix en français...")
    tts = TTS(model_name="tts_models/fr/mai/mai", progress_bar=True, gpu=True)
    tts.tts_to_file(text=text, file_path=output_file)
    print(f"✅ Voix générée : {output_file}")
    return output_file

def create_video_with_audio(video_file, audio_file, output_file="final.mp4"):
    print("🎬 Montage vidéo + audio...")
    input_video = ffmpeg.input(video_file)
    input_audio = ffmpeg.input(audio_file)
    try:
        ffmpeg.output(
            input_video, 
            input_audio, 
            output_file,
            vcodec='h264', 
            acodec='aac'
        ).run(overwrite_output=True)
        print(f"✅ Vidéo finale créée : {output_file}")
        return output_file
    except ffmpeg.Error as e:
        print("❌ Erreur FFmpeg :", e.stderr.decode())
        raise

def upload_to_r2(file_path, r2_key):
    print("☁️ Upload vers R2...")
    client = boto3.client(
        's3',
        endpoint_url=os.getenv('R2_ENDPOINT'),
        aws_access_key_id=os.getenv('R2_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('R2_SECRET_ACCESS_KEY')
    )
    client.upload_file(file_path, os.getenv('R2_BUCKET'), r2_key)
    print(f"✅ Upload terminé : https://{os.getenv('R2_BUCKET')}.r2.cloudflarestorage.com/{r2_key}")
    return f"https://{os.getenv('R2_BUCKET')}.r2.cloudflarestorage.com/{r2_key}"

def send_webhook(job_id, status, r2_url=None, error=None):
    print(f"📨 Webhook → {os.getenv('CLOUDFLARE_WORKER_WEBHOOK')}")
    payload = {"job_id": job_id, "status": status}
    if r2_url: payload["asset_r2_key"] = r2_url
    if error: payload["error_msg"] = error
    try:
        requests.post(os.getenv('CLOUDFLARE_WORKER_WEBHOOK'), json=payload)
        print("✅ Webhook envoyé")
    except Exception as e:
        print("❌ Échec du webhook :", str(e))

def process_job(prompt):
    job_id = str(uuid.uuid4())
    send_webhook(job_id, "running", progress=10)
    try:
        # 1. Générer la voix
        audio_file = generate_voice_french(prompt)
        send_webhook(job_id, "running", progress=40)
        # 2. Générer une vidéo (simulée)
        print("🎥 Génération de la vidéo (simulée)...")
        os.system("ffmpeg -f lavfi -i color=c=black:s=1280x720:d=10 -c:v libx264 temp_video.mp4 -y")
        send_webhook(job_id, "running", progress=70)
        # 3. Monter vidéo + audio
        final_video = create_video_with_audio("temp_video.mp4", audio_file, f"{job_id}.mp4")
        send_webhook(job_id, "running", progress=90)
        # 4. Upload vers R2
        r2_key = f"output/{job_id}.mp4"
        r2_url = upload_to_r2(final_video, r2_key)
        # 5. Webhook "done"
        send_webhook(job_id, "done", r2_url=r2_url)
    except Exception as e:
        send_webhook(job_id, "error", error=str(e))

if __name__ == "__main__":
    prompt = "Un dauphin guide un bateau perdu vers le rivage."
    process_job(prompt)