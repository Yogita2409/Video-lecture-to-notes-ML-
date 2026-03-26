import streamlit as st
import whisper
from video_utils import extract_audio
import yt_dlp
import time
import os
import html

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# ===================== PAGE =====================
st.set_page_config(page_title="Video Lecture to Notes", layout="wide")
st.title("🎥 Video Lecture to Notes Converter")

# ===================== MODEL =====================
@st.cache_resource
def load_model():
    return whisper.load_model("base")

# ===================== DOWNLOAD =====================
def download_youtube_video(url):
    try:
        filename = f"video_{int(time.time())}.mp4"

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': filename,
            'quiet': True,
            'nocheckcertificate': True,
            'ignoreerrors': True,
            'no_warnings': True,
            'noplaylist': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0'
            }
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

# ===================== INPUT =====================
st.markdown("### 📌 Choose Input Method")
option = st.radio("", ["Upload Video (Recommended)", "YouTube Link (May fail)"])

file = None
url = None

if option == "Upload Video (Recommended)":
    file = st.file_uploader("Upload Video", type=["mp4"])
else:
    st.warning("⚠️ YouTube videos may not work due to server restrictions")
    url = st.text_input("Enter YouTube link")

# ===================== PROCESS =====================
if file or url:

    progress = st.progress(0)
    status = st.empty()

    if file:
        st.video(file)
    elif url:
        st.video(url)

    status.info("📥 Loading video...")

    if file:
        vid = f"upload_{time.time()}.mp4"
        with open(vid, "wb") as f:
            f.write(file.read())
    else:
        vid = download_youtube_video(url)
        if not vid:
            st.stop()

    progress.progress(30)

    status.info("🎧 Extracting audio...")
    audio = extract_audio(vid)

    if not audio:
        st.error("❌ Audio extraction failed")
        st.stop()

    progress.progress(60)

    model = load_model()

    status.info("📝 Transcribing...")
    result = model.transcribe(audio)

    progress.progress(90)

    notes = format_notes(result["segments"])

    st.subheader("📜 Notes")
    for n in notes[:100]:
        st.write(n)

    st.subheader("🎯 Predicted Topic")
    topic = predict_topic(result["text"][:2000])
    st.success(topic)

    progress.progress(100)
    status.success("✅ Done!")

    pdf = create_pdf(notes)
    with open(pdf, "rb") as f:
        st.download_button("📥 Download PDF", f, file_name="Lecture_Notes.pdf")

    # cleanup
    try:
        os.remove(vid)
        os.remove(audio)
    except:
        pass

    