import streamlit as st
import whisper
from video_utils import extract_audio
import yt_dlp
import time
import sqlite3
import os
import html

# 🔥 FFmpeg PATH
os.environ["PATH"] += os.pathsep + r"C:\Users\yogita\Downloads\ffmpeg-8.1-essentials_build\ffmpeg-8.1-essentials_build\bin"

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# ===================== SESSION TIMER INIT =====================
if "start_time" not in st.session_state:
    st.session_state["start_time"] = time.time()

# ===================== DATABASE =====================
conn = sqlite3.connect("users.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password TEXT,
    total_time INTEGER DEFAULT 0
)
""")
conn.commit()

# ===================== PAGE =====================
st.set_page_config(page_title="Video Lecture to Notes", layout="wide")

# ===================== GREEN PROGRESS =====================
st.markdown("""
<style>
.stProgress > div > div > div > div {
    background-color: #00ff00;
}
</style>
""", unsafe_allow_html=True)

st.title("🎥 Video Lecture to Notes Converter")

# ===================== AUTH =====================
st.sidebar.title("🔐 Login / Signup")

mode = st.sidebar.radio("Select", ["Login", "Signup"])
user = st.sidebar.text_input("Username")
pwd = st.sidebar.text_input("Password", type="password")

if st.sidebar.button("Submit"):
    if mode == "Signup":
        try:
            c.execute("INSERT INTO users VALUES (?, ?, 0)", (user, pwd))
            conn.commit()
            st.sidebar.success("Account created")
        except:
            st.sidebar.error("User exists")
    else:
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (user, pwd))
        if c.fetchone():
            st.session_state["user"] = user
            st.sidebar.success("Logged in")
        else:
            st.sidebar.error("Wrong credentials")

# ===================== LOGIN CHECK =====================
if "user" not in st.session_state:
    st.warning("⚠️ Please login from sidebar to use the app")
    st.stop()

# ===================== TIME SAVE =====================
now = time.time()
start_time = st.session_state.get("start_time", now)
spent = int(now - start_time)

if spent > 3:
    c.execute(
        "UPDATE users SET total_time = total_time + ? WHERE username=?",
        (spent, st.session_state["user"])
    )
    conn.commit()
    st.session_state["start_time"] = now

# ===================== DASHBOARD =====================
c.execute("SELECT total_time FROM users WHERE username=?", (st.session_state["user"],))
time_spent = c.fetchone()[0] or 0

minutes = time_spent // 60
seconds = time_spent % 60

xp = time_spent // 5
level = xp // 50
progress_val = (xp % 50) / 50

st.sidebar.markdown("## 🧠 Your Dashboard")
st.sidebar.markdown(f"👤 {st.session_state['user']}")
st.sidebar.metric("⏱ Time Used", f"{minutes}m {seconds}s")
st.sidebar.markdown(f"💎 XP: {xp}")
st.sidebar.markdown(f"🎮 Level: {level}")
st.sidebar.progress(progress_val)
st.sidebar.caption(f"{int(progress_val*100)}% to next level")

# ===================== MODEL =====================
@st.cache_resource
def load_model():
    return whisper.load_model("tiny")

# ===================== DOWNLOAD =====================
def download_youtube_video(url):
    try:
        filename = f"video_{int(time.time())}.mp4"
        ydl_opts = {
            'format': 'best[ext=mp4]',
            'outtmpl': filename,
            'quiet': True,
            'noplaylist': True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return filename
    except Exception as e:
        st.error(f"Download Error: {str(e)}")
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
        if len(clean_line) > 500:
            clean_line = clean_line[:500] + "..."

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
file = st.file_uploader("Upload Video")
url = st.text_input("YouTube link")

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
        with open(vid,"wb") as f:
            f.write(file.read())
    else:
        vid = download_youtube_video(url)
        if not vid:
            st.stop()

    progress.progress(30)

    status.info("🎧 Extracting audio...")
    audio = extract_audio(vid)

    progress.progress(60)

    model = load_model()

    status.info("📝 Transcribing...")
    result = model.transcribe(audio)

    progress.progress(90)

    notes = format_notes(result["segments"])

    st.subheader("📜 Notes")
    for n in notes[:100]:
        st.write(n)

    # 🎯 PREDICTED TOPIC
    st.subheader("🎯 Predicted Topic")
    topic = predict_topic(result["text"][:2000])
    st.success(topic)

    progress.progress(100)
    status.success("✅ Done!")

    st.balloons()

    pdf = create_pdf(notes)
    with open(pdf, "rb") as f:
        st.download_button("📥 Download PDF", f, file_name="Lecture_Notes.pdf")