from moviepy.editor import VideoFileClip
import os

def extract_audio(video_path):
    try:
        video = VideoFileClip(video_path)
        audio_path = "audio.wav"
        
        video.audio.write_audiofile(audio_path)
        
        return os.path.abspath(audio_path)

    except Exception as e:
        print("Error in audio extraction:", e)
        return None