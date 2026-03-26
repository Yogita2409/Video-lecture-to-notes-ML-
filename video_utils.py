import os
import shutil
import subprocess

# ✅ ADD THIS HERE (TOP PE)
if not shutil.which("ffmpeg"):
    print("❌ FFmpeg NOT found")
else:
    print("✅ FFmpeg found")

# (optional but recommended)
os.environ["PATH"] += os.pathsep + "/usr/bin"


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

        result = subprocess.run(command, capture_output=True, text=True)

        print("STDERR:", result.stderr)

        if result.returncode != 0:
            print("❌ FFmpeg failed")
            return None

        if os.path.exists(audio_path):
            return os.path.abspath(audio_path)
        else:
            return None

    except Exception as e:
        print("Error:", e)
        return None
    
    