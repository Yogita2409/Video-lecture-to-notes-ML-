import subprocess
import os

def extract_audio(video_path):
    try:
        audio_path = "audio.wav"

        command = [
            "ffmpeg",
            "-i", video_path,
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", "44100",
            "-ac", "2",
            audio_path
        ]

        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if os.path.exists(audio_path):
            return os.path.abspath(audio_path)
        else:
            print("FFmpeg failed:", result.stderr.decode())
            return None

    except Exception as e:
        print("Error:", e)
        return None
    
    