from moviepy.editor import VideoFileClip
import os

def extract_audio(video_path):
    try:
        audio_path = "audio.wav"

        video = VideoFileClip(video_path)

        # 🔥 Important fix
        if video.audio is None:
            print("No audio track found!")
            return None

        video.audio.write_audiofile(audio_path, codec='pcm_s16le')

        return os.path.abspath(audio_path)

    except Exception as e:
        print("Error in audio extraction:", e)
        return None
    