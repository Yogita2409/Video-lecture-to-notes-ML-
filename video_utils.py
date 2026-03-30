import subprocess
import os

def extract_audio(video_path):
    audio_path = video_path.replace(".mp4", ".wav")

    command = [
        r"C:\Users\yogita\Downloads\ffmpeg-8.1-essentials_build\ffmpeg-8.1-essentials_build\bin\ffmpeg.exe",
        "-i", video_path,
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        audio_path
    ]

    try:
        result = subprocess.run(command, capture_output=True, text=True)
        print(result.stderr)   # 👈 IMPORTANT: will show error
        return audio_path if os.path.exists(audio_path) else None
    except Exception as e:
        print("ERROR:", e)
        return None