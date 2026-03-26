import streamlit as st
import whisper
from video_utils import extract_audio
import yt_dlp
import time
import os
import html
import shutil

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# ===================== PAGE =====================
st.set_page_config(page_title="Video Lecture to Notes", layout="wide")
st.title("🎥 Video Lecture to Notes Converter")

# ===================== FFmpeg CHECK =====================
if not shutil.which("ffmpeg"):
    st.warning("⚠️ FFmpeg not found. Audio extraction may fail.")
else:
    st.success("✅ FFmpeg detected")

# ===================== MODEL =====================
@st.cache_resource
def load_model():
    return whisper.load_model("base")

# ===================== DOWNLOAD =====================
def download_youtube_video(url):
    try:
        filename = f"video_{int(time.time())}.mp4"

        ydl_opts = {
            'format': 'best',  # IMPORTANT FIX
            'outtmpl': filename,
            'quiet': True,
            'nocheckcertificate': True,
            'ignoreerrors': True,
            'no_warnings': True,
            'noplaylist': True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        return filename

    except Exception as e:
        st.error(f"❌ Download Error: {str(e)}")
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

# ===================== INPUT UI =====================
st.markdown("### 📌 Choose Input Method")

option = st.radio(
    "Select one:",
    ["Upload Video", "YouTube Link"]
)

video_file = None
youtube_url = None

if option == "Upload Video":
    video_file = st.file_uploader("📂 Upload your video", type=["mp4", "mov", "avi"])

elif option == "YouTube Link":
    st.warning("⚠️ YouTube may fail on cloud. Prefer upload.")
    youtube_url = st.text_input("🔗 Enter YouTube URL")

# ===================== PROCESS =====================
if video_file is not None or (youtube_url and youtube_url.strip() != ""):

    progress = st.progress(0)
    status = st.empty()

    # Show video
    if video_file is not None:
        st.video(video_file)
    else:
        st.video(youtube_url)

    status.info("📥 Loading video...")

    # Save video
    if video_file is not None:
        vid = f"upload_{int(time.time())}.mp4"
        with open(vid, "wb") as f:
            f.write(video_file.read())
    else:
        vid = download_youtube_video(youtube_url)
        if not vid:
            st.stop()

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
    result = model.transcribe(audio)

    progress.progress(90)

    # Notes
    notes = format_notes(result["segments"])

    st.subheader("📜 Notes")
    for n in notes[:100]:
        st.write(n)

    # Topic
    st.subheader("🎯 Predicted Topic")
    topic = predict_topic(result["text"][:2000])
    st.success(topic)

    progress.progress(100)
    status.success("✅ Done!")

    # PDF
    pdf = create_pdf(notes)
    with open(pdf, "rb") as f:
        st.download_button("📥 Download PDF", f, file_name="Lecture_Notes.pdf")

    # Cleanup
    try:
        os.remove(vid)
        os.remove(audio)
    except:
        pass
    