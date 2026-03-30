import streamlit as st
import whisper
import time
import os
import html
import subprocess

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# ===================== FIX FFMPEG PATH =====================
os.environ["PATH"] = r"C:\Users\yogita\Downloads\ffmpeg-8.1-essentials_build\ffmpeg-8.1-essentials_build\bin;" + os.environ["PATH"]
os.environ["FFMPEG_BINARY"] = r"C:\Users\yogita\Downloads\ffmpeg-8.1-essentials_build\ffmpeg-8.1-essentials_build\bin\ffmpeg.exe"

FFMPEG_PATH = r"C:\Users\yogita\Downloads\ffmpeg-8.1-essentials_build\ffmpeg-8.1-essentials_build\bin\ffmpeg.exe"

# ===================== PAGE =====================
st.set_page_config(page_title="Video Lecture to Notes", layout="wide")
st.title("🎥 Video Lecture to Notes Converter")

# ===================== MODEL =====================
@st.cache_resource
def load_model():
    return whisper.load_model("base")

# ===================== AUDIO EXTRACTION =====================
def extract_audio(video_path):
    audio_path = video_path.rsplit(".", 1)[0] + ".wav"

    command = [
        FFMPEG_PATH,
        "-i", video_path,
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        audio_path
    ]

    try:
        result = subprocess.run(command, capture_output=True, text=True)

        if result.returncode != 0:
            st.error("FFmpeg Error:\n" + result.stderr)
            return None

        return audio_path if os.path.exists(audio_path) else None

    except Exception as e:
        st.error(f"Error: {e}")
        return None

# ===================== PDF =====================
def create_pdf(lines):
    file = f"notes_{int(time.time())}.pdf"
    doc = SimpleDocTemplate(file)
    styles = getSampleStyleSheet()

    content = []
    content.append(Paragraph("Lecture Notes", styles["Title"]))
    content.append(Spacer(1, 12))

    for line in lines:
        clean_line = html.escape(line)
        content.append(Paragraph(f"• {clean_line}", styles["Normal"]))
        content.append(Spacer(1, 6))

    doc.build(content)
    return file

# ===================== NOTES =====================
def format_notes(seg):
    return [f"[{round(s['start'],1)}s] {s['text']}" for s in seg if len(s['text']) > 5]

# ===================== TOPIC =====================
def predict_topic(text):
    topics = {
        "Machine Learning": ["model","training","neural","regression","classification"],
        "Programming": ["python","code","function","loop"],
        "Database": ["sql","database","query","table"],
        "Statistics": ["mean","median","probability","variance"],
        "Web Development": ["html","css","javascript"],
        "Physics": ["force","energy","velocity"]
    }

    text = text.lower()
    scores = {t: sum(text.count(k) for k in kws) for t, kws in topics.items()}
    best = max(scores, key=scores.get)

    return best if scores[best] > 0 else "General"

# ===================== INPUT =====================
st.markdown("### 📂 Upload Your Video")

video_file = st.file_uploader(
    "Upload lecture video (MP4 recommended)",
    type=["mp4", "mov", "avi"]
)

# ===================== PROCESS =====================
if video_file is not None:

    progress = st.progress(0)
    status = st.empty()

    st.video(video_file)

    status.info("📥 Saving video...")

    vid = f"upload_{int(time.time())}.mp4"
    with open(vid, "wb") as f:
        f.write(video_file.getbuffer())

    progress.progress(30)

    # Extract audio
    status.info("🎧 Extracting audio...")
    audio = extract_audio(vid)

    if not audio:
        st.error("❌ Audio extraction failed")
        st.stop()

    progress.progress(60)

    # Transcribe
    model = load_model()

    status.info("📝 Transcribing...")
    result = model.transcribe(audio, fp16=False)

    progress.progress(90)

    # Notes
    notes = format_notes(result["segments"])

    st.subheader("📜 Generated Notes")
    for n in notes[:100]:
        st.write(n)

    # Topic
    st.subheader("🎯 Predicted Topic")
    topic = predict_topic(result["text"][:2000])
    st.success(topic)

    progress.progress(100)
    status.success("✅ Processing Complete!")

    # PDF download
    pdf = create_pdf(notes)
    with open(pdf, "rb") as f:
        st.download_button(
            "📥 Download Notes as PDF",
            f,
            file_name="Lecture_Notes.pdf"
        )

    # Cleanup
    try:
        os.remove(vid)
        os.remove(audio)
    except:
        pass