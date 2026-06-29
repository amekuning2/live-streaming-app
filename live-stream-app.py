# /home/amekuning2/web_panel/live-stream-app.py
import streamlit as st
import os
import re
import subprocess
import base64
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC

st.set_page_config(page_title="YouTube Live Control", layout="centered")

# --- PATH CONFIGURATION ---
VIDEO_DIR       = "/home/amekuning2/web_panel/video"
AUDIO_DIR       = "/home/amekuning2/web_panel/audio"
PID_FILE        = "/home/amekuning2/web_panel/stream.pid"
STREAM_KEY_FILE = "/home/amekuning2/web_panel/stream_key.txt"
LOG_PATH        = "/home/amekuning2/web_panel/stream.log"

os.makedirs(VIDEO_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)

# --- SVG PLACEHOLDERS ---
DEFAULT_COVER = "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAxMDAgMTAwIj48cmVjdCB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgcng9IjEyIiBmaWxsPSIjMjIyIi8+PHBvbHlnb24gcG9pbnRzPSI0MCwzNSA3MCw1MCA0MCw2NSIgZmlsbD0iI0ZGMDAwMCIvPjwvc3ZnPg=="
DEFAULT_MUSIC_COVER = "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAxMDAgMTAwIj48cmVjdCB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgcng9IjEyIiBmaWxsPSIjMjIyIi8+PHBhdGggZD0iTTM1LDc1IEE4LDggMCAxLDEgMzUsNjAgTDY1LDMwIEw2NSw0NSBMMzUsNzUgWiBNNjUsMzAgTDY1LDE1IEw4NSwyNSBMODUsNDAgWiIgZmlsbD0iIzg4OCIvPjwvc3ZnPg=="

# --- CSS ---
st.markdown("""
<style>
.stApp { background-color:#0f0f0f !important; color:#f1f1f1 !important; font-family:'Inter',-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif; }
[data-testid="stSidebar"] { display:none !important; }
header { visibility:hidden !important; height:0px !important; }
footer { visibility:hidden !important; }
.custom-card { background-color:#161616; border:1px solid #282828; border-radius:12px; padding:22px; margin-bottom:20px; box-shadow:0 4px 15px rgba(0,0,0,0.4); }
.item-row { display:flex; align-items:center; justify-content:space-between; padding:12px 0; border-bottom:1px solid #222222; }
.item-row:last-child { border-bottom:none; }
.item-left { display:flex; align-items:center; gap:16px; min-width:0; flex-grow:1; }
.item-thumb { width:54px; height:54px; border-radius:8px; object-fit:cover; background-color:#242424; flex-shrink:0; border:1px solid #333333; }
.item-info { display:flex; flex-direction:column; min-width:0; }
.item-title { font-weight:600; font-size:14.5px; color:#ffffff; margin:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.item-subtitle { font-size:12px; color:#888888; margin:2px 0 0 0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.item-duration { font-size:13px; color:#aaaaaa; font-family:monospace; margin-right:15px; flex-shrink:0; }
div[data-baseweb="input"] { background-color:#1f1f1f !important; border:1px solid #333333 !important; border-radius:8px !important; }
input { color:#ffffff !important; font-size:15px !important; }
label { color:#aaaaaa !important; font-size:13px !important; font-weight:500 !important; margin-bottom:6px !important; }
</style>
""", unsafe_allow_html=True)

# --- NATURAL SORT (FIX MASALAH 1: urutan berantakan) ---
def natural_sort_key(s):
    """Sort string dengan angka secara natural: 01,02,...,09,10,11 bukan 01,10,11,02"""
    return [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', s)]

# --- HELPER FUNCTIONS ---
def get_stream_status():
    if os.path.exists(PID_FILE):
        with open(PID_FILE, "r") as f:
            pid_str = f.read().strip()
        if pid_str:
            try:
                pid = int(pid_str)
                os.kill(pid, 0)
                return True, pid
            except (OSError, ValueError):
                pass
    return False, None

def get_audio_duration(file_path):
    try:
        audio = MP3(file_path)
        return audio.info.length
    except:
        return 0

def get_audio_thumbnail_b64(file_path):
    try:
        audio = ID3(file_path)
        for tag in audio.values():
            if isinstance(tag, APIC):
                b64_data = base64.b64encode(tag.data).decode("utf-8")
                return f"data:{tag.mime};base64,{b64_data}"
    except:
        pass
    return DEFAULT_MUSIC_COVER

def save_stream_key(key):
    with open(STREAM_KEY_FILE, "w") as f:
        f.write(key)

def load_stream_key():
    if os.path.exists(STREAM_KEY_FILE):
        with open(STREAM_KEY_FILE, "r") as f:
            return f.read().strip()
    return ""

def start_stream(stream_key, loop_count):
    stop_stream()
    # FIX MASALAH 3: pakai setsid biar proses benar-benar independent dari Streamlit
    cmd = (
        f"setsid nohup python3 /home/amekuning2/web_panel/core_stream.py "
        f"'{stream_key}' {loop_count} "
        f"> {LOG_PATH} 2>&1 & echo $!"
    )
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, text=True)
    pid = result.stdout.strip()
    if pid:
        with open(PID_FILE, "w") as f:
            f.write(pid)
        return True
    return False

def stop_stream():
    os.system("pkill -f core_stream.py")
    os.system("pkill -f ffmpeg")
    if os.path.exists(PID_FILE):
        os.remove(PID_FILE)

# --- SESSION STATE ---
if "show_add_music" not in st.session_state:
    st.session_state.show_add_music = False

is_running, run_pid = get_stream_status()

# --- HEADER ---
st.markdown("""
<div style="background-color:#FF0000;display:flex;justify-content:center;align-items:center;height:110px;border-radius:6px;margin-bottom:20px;">
    <svg viewBox="0 0 200 60" width="200" height="60">
        <path fill="#FFFFFF" d="M37.3,10.3c-4.4-0.3-15.6-0.3-20.1,0C12.4,10.6,8.7,11.3,6.2,13.8c-3,3-3.2,8.8-3.2,16.2s0.2,13.2,3.2,16.2 c2.5,2.5,6.2,3.2,11.1,3.5c4.5,0.3,15.7,0.3,20.1,0c4.9-0.3,8.6-1.1,11.1-3.5c3-3,3.2-8.8,3.2-16.2s-0.2-13.2-3.2-16.2 C51.8,11.3,48.1,10.6,47.3,10.3z M22,41.5V18.5l15,11.5L22,41.5z"/>
        <text x="62" y="41" fill="#FFFFFF" font-family="'Arial Black',Gadget,sans-serif" font-size="28" font-weight="900" letter-spacing="-1">YouTube</text>
    </svg>
</div>
<h2 style="text-align:center;color:white;margin-top:-5px;margin-bottom:5px;font-weight:700;letter-spacing:-0.5px;">🚀 YouTube Live Streaming</h2>
<h3 style="text-align:center;color:white;margin-top:-4px;margin-bottom:20px;font-weight:500;font-size:16px;">Dashboard v3.5 - Stream Control</h3>
""", unsafe_allow_html=True)

# --- STREAM KEY ---
saved_key = load_stream_key()
stream_key = st.text_input("Youtube Stream Key", type="password", value=saved_key or "")
if stream_key and stream_key != saved_key:
    save_stream_key(stream_key)

st.write("")

# --- VIDEO LIST ---
st.markdown('<div class="custom-card">', unsafe_allow_html=True)
st.markdown("<h3 style='margin:0;font-size:18px;font-weight:600;color:white;'>Video List</h3>", unsafe_allow_html=True)

video_files = []
if os.path.exists(VIDEO_DIR):
    video_files = [
        os.path.join(VIDEO_DIR, f) for f in os.listdir(VIDEO_DIR)
        if f.lower().endswith('.mp4')
    ]

if video_files:
    v_path = video_files[0]
    v_filename = os.path.basename(v_path)
    v_display_title = os.path.splitext(v_filename)[0].replace("-", " ").replace("_", " ").title()
    st.markdown(f"""
        <div class="item-row" style="margin-top:15px;">
            <div class="item-left">
                <img class="item-thumb" src="{DEFAULT_COVER}" alt="thumb">
                <div class="item-info">
                    <div class="item-title">{v_display_title}</div>
                    <div class="item-subtitle">{v_filename}</div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("<div style='color:#666;font-size:14px;margin-top:15px;font-style:italic;'>Tidak ada video. Upload via WinSCP ke folder /video.</div>", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# --- MUSIC LIST ---
st.markdown('<div class="custom-card">', unsafe_allow_html=True)
col_m_title, col_m_btn = st.columns([5, 1])
with col_m_title:
    st.markdown("<h3 style='margin:0;font-size:18px;font-weight:600;color:white;'>Music list</h3>", unsafe_allow_html=True)
with col_m_btn:
    if st.button("➕ Add", key="add_m_trigger", use_container_width=True):
        st.session_state.show_add_music = not st.session_state.show_add_music

if st.session_state.show_add_music:
    st.markdown("<div style='margin-top:15px;padding:15px;background:#1f1f1f;border-radius:8px;'>", unsafe_allow_html=True)
    uploaded_audio = st.file_uploader("Upload audio track baru (.mp3)", type=["mp3"])
    if uploaded_audio is not None:
        save_path = os.path.join(AUDIO_DIR, uploaded_audio.name)
        with open(save_path, "wb") as f:
            f.write(uploaded_audio.getbuffer())
        st.success(f"✅ Berhasil menambahkan: {uploaded_audio.name}")
        st.session_state.show_add_music = False
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# FIX MASALAH 1: Natural sort biar 01,02,...,09,10,11 urut bener
audio_files = []
if os.path.exists(AUDIO_DIR):
    raw = [f for f in os.listdir(AUDIO_DIR) if f.lower().endswith('.mp3')]
    raw.sort(key=natural_sort_key)
    audio_files = [os.path.join(AUDIO_DIR, f) for f in raw]

total_duration_sec = 0

if audio_files:
    st.markdown("<div style='margin-top:10px;'>", unsafe_allow_html=True)
    for idx, audio_path in enumerate(audio_files):
        filename = os.path.basename(audio_path)
        duration = get_audio_duration(audio_path)
        total_duration_sec += duration

        minutes, seconds = divmod(int(duration), 60)
        formatted_duration = f"{minutes:02d}:{seconds:02d}"
        cover_src = get_audio_thumbnail_b64(audio_path)

        # Bersihkan judul: buang prefix angka (01_, 02- dll)
        clean_title = os.path.splitext(filename)[0]
        clean_title = re.sub(r'^\d+[-_.\s]+', '', clean_title)
        clean_title = clean_title.replace("-", " ").replace("_", " ").title()

        st.markdown(f"""
            <div class="item-row">
                <div class="item-left">
                    <img class="item-thumb" src="{cover_src}" alt="Cover">
                    <div class="item-info">
                        <div class="item-title">{clean_title}</div>
                        <div class="item-subtitle">{filename}</div>
                    </div>
                </div>
                <div class="item-duration">{formatted_duration}</div>
            </div>
        """, unsafe_allow_html=True)

        col_dummy, col_pop = st.columns([5, 1])
        with col_pop:
            with st.popover("⋮", key=f"pop_{idx}"):
                new_name = st.text_input("Rename", value=filename, key=f"ren_{idx}")
                if st.button("✅ Simpan Nama", key=f"save_ren_{idx}"):
                    if new_name != filename:
                        os.rename(audio_path, os.path.join(AUDIO_DIR, new_name))
                        st.rerun()
                if st.button("🗑️ Delete", key=f"del_{idx}", use_container_width=True):
                    os.remove(audio_path)
                    st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)
else:
    st.markdown("<div style='color:#666;font-size:14px;margin-top:15px;font-style:italic;'>Playlist kosong. Upload file MP3.</div>", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# --- NUMBER LOOP & ESTIMASI ---
loop_count = st.number_input("Number Loop", min_value=1, value=5, step=1)

total_min = total_duration_sec / 60
grand_total_min = total_min * loop_count
hours, mins = divmod(int(grand_total_min), 60)

if total_duration_sec > 0:
    st.markdown(f"""
        <div style="background-color:#161616;padding:15px;border-radius:10px;border:1px solid #222;margin-top:15px;font-size:13.5px;color:#aaa;">
            📊 <b>Estimasi Live:</b> {int(total_min)} menit/playlist × {int(loop_count)} Loop = <b>{hours} Jam {mins} Menit</b>
        </div>
    """, unsafe_allow_html=True)

st.write("")

# --- PLAY / STOP BUTTON ---
if is_running:
    st.markdown(f"""
        <div style="text-align:center;color:#2ecc71;font-weight:600;font-size:14px;margin-bottom:12px;">
            🟢 LIVE STREAM SEDANG BERJALAN (PID: {run_pid})
        </div>
    """, unsafe_allow_html=True)
    if st.button("🟥 Stop Live", key="stop_live_btn", use_container_width=True):
        stop_stream()
        st.rerun()
else:
    st.markdown("""
        <div style="text-align:center;color:#e74c3c;font-weight:600;font-size:14px;margin-bottom:12px;">
            🔴 STATUS: OFFLINE
        </div>
    """, unsafe_allow_html=True)
    if st.button("▶️ Play Live", key="play_live_btn", use_container_width=True):
        if not stream_key:
            st.error("Masukkan Youtube Stream Key dulu!")
        elif not video_files:
            st.error("Upload video background dulu via WinSCP!")
        elif not audio_files:
            st.error("Upload minimal 1 lagu di Playlist dulu!")
        else:
            ok = start_stream(stream_key, int(loop_count))
            if ok:
                st.success("✅ Streaming dimulai!")
                st.rerun()
            else:
                st.error("Gagal start stream. Cek log.")

st.write("")

# --- DOWNLOAD LOG ---
if os.path.exists(LOG_PATH):
    with open(LOG_PATH, "rb") as f:
        log_data = f.read()
    st.download_button(
        label="⬇️ Download Log",
        data=log_data,
        file_name="stream_log.txt",
        mime="text/plain",
        use_container_width=True
    )