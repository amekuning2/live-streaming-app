import streamlit as st
import os
import subprocess
import signal
import base64
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC

# Set halaman ke mode centered agar ramping di desktop & pas di HP
st.set_page_config(page_title="YouTube Live Control", layout="centered")

# --- PATH CONFIGURATION ---
VIDEO_DIR = "/home/amekuning2/web_panel/video"
AUDIO_DIR = "/home/amekuning2/web_panel/audio"
PID_FILE = "/home/amekuning2/web_panel/stream.pid"
STREAM_KEY_FILE = "/home/amekuning2/web_panel/stream_key.txt"

os.makedirs(VIDEO_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)

# --- MODERN BASE64 SVG THUMBNAIL PLACEHOLDERS (Anti-Broken Link) ---
# Play icon aesthetic placeholder for video
DEFAULT_COVER = "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAxMDAgMTAwIj48cmVjdCB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgcng9IjEyIiBmaWxsPSIjMjIyIi8+PHBvbHlnb24gcG9pbnRzPSI0MCwzNSA3MCw1MCA0MCw2NSIgZmlsbD0iI0ZGMDAwMCIvPjwvc3ZnPg=="
# Music note aesthetic placeholder for audio tracks without album art
DEFAULT_MUSIC_COVER = "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAxMDAgMTAwIj48cmVjdCB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgcng9IjEyIiBmaWxsPSIjMjIyIi8+PHBhdGggZD0iTTM1LDc1IEE4LDggMCAxLDEgMzUsNjAgTDY1LDMwIEw2NSw0NSBMMzUsNzUgWiBNNjUsMzAgTDY1LDE1IEw4NSwyNSBMODUsNDAgWiIgZmlsbD0iIzg4OCIvPjwvc3ZnPg=="

# --- INJECT CUSTOM CSS FOR PREMIUM DARK THEME ---
st.markdown(f"""
    <style>
    /* Mengubah background utama ke Ultra-Dark */
    .stApp {{
        background-color: #0f0f0f !important;
        color: #f1f1f1 !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }}
    
    /* Menyembunyikan element Streamlit default */
    [data-testid="stSidebar"] {{
        display: none !important;
    }}
    header {{
        visibility: hidden !important;
        height: 0px !important;
    }}
    footer {{
        visibility: hidden !important;
    }}
    
    /* Global Card/Container Dark styling */
    .custom-card {{
        background-color: #161616;
        border: 1px solid #282828;
        border-radius: 12px;
        padding: 22px;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4);
    }}
    
    /* Item row styling */
    .item-row {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 12px 0;
        border-bottom: 1px solid #222222;
    }}
    .item-row:last-child {{
        border-bottom: none;
    }}
    
    .item-left {{
        display: flex;
        align-items: center;
        gap: 16px;
        min-width: 0;
        flex-grow: 1;
    }}
    
    .item-thumb {{
        width: 54px;
        height: 54px;
        border-radius: 8px;
        object-fit: cover;
        background-color: #242424;
        flex-shrink: 0;
        border: 1px solid #333333;
    }}
    
    .item-info {{
        display: flex;
        flex-direction: column;
        min-width: 0;
    }}
    
    .item-title {{
        font-weight: 600;
        font-size: 14.5px;
        color: #ffffff;
        margin: 0;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }}
    
    .item-subtitle {{
        font-size: 12px;
        color: #888888;
        margin: 2px 0 0 0;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }}
    
    .item-duration {{
        font-size: 13px;
        color: #aaaaaa;
        font-family: monospace;
        margin-right: 15px;
        flex-shrink: 0;
    }}
    
    /* Customization form inputs */
    div[data-baseweb="input"] {{
        background-color: #1f1f1f !important;
        border: 1px solid #333333 !important;
        border-radius: 8px !important;
    }}
    input {{
        color: #ffffff !important;
        font-size: 15px !important;
    }}
    
    /* Label styling */
    label {{
        color: #aaaaaa !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        margin-bottom: 6px !important;
    }}
    
    /* Custom play/stop buttons container */
    .control-container {{
        margin-top: 25px;
        text-align: center;
    }}
    </style>
""", unsafe_allow_html=True)

# --- HELPER FUNCTIONS ---
def get_stream_status():
    if os.path.exists(PID_FILE):
        with open(PID_FILE, "r") as f:
            pid = f.read().strip()
        if pid:
            try:
                os.kill(int(pid), 0)
                return True, int(pid)
            except OSError:
                return False, None
    return False, None

def get_audio_duration(file_path):
    try:
        audio = MP3(file_path)
        return audio.info.length  # dalam detik
    except:
        return 0

def get_audio_thumbnail_b64(file_path):
    try:
        audio = ID3(file_path)
        for tag in audio.values():
            if isinstance(tag, APIC):
                # Convert cover art bytes to base64 string
                b64_data = base64.b64encode(tag.data).decode("utf-8")
                return f"data:{tag.mime};base64,{b64_data}"
    except:
        pass
    return DEFAULT_MUSIC_COVER

# Save stream key persistently
def save_stream_key(key):
    with open(STREAM_KEY_FILE, "w") as f:
        f.write(key)

def load_stream_key():
    if os.path.exists(STREAM_KEY_FILE):
        with open(STREAM_KEY_FILE, "r") as f:
            return f.read().strip()
    return ""

# Initialize session state for music add toggle
if "show_add_music" not in st.session_state:
    st.session_state.show_add_music = False

is_running, run_pid = get_stream_status()

# --- 1. YOUTUBE HEADER BANNER ---
st.markdown("""
    <div style="background-color: #FF0000; display: flex; justify-content: center; align-items: center; height: 110px; border-radius: 6px; margin-bottom: 20px;">
        <svg viewBox="0 0 200 60" width="200" height="60">
            <path fill="#FFFFFF" d="M37.3,10.3c-4.4-0.3-15.6-0.3-20.1,0C12.4,10.6,8.7,11.3,6.2,13.8c-3,3-3.2,8.8-3.2,16.2s0.2,13.2,3.2,16.2 c2.5,2.5,6.2,3.2,11.1,3.5c4.5,0.3,15.7,0.3,20.1,0c4.9-0.3,8.6-1.1,11.1-3.5c3-3,3.2-8.8,3.2-16.2s-0.2-13.2-3.2-16.2 C51.8,11.3,48.1,10.6,47.3,10.3z M22,41.5V18.5l15,11.5L22,41.5z"/>
            <text x="62" y="41" fill="#FFFFFF" font-family="'Arial Black', Gadget, sans-serif" font-size="28" font-weight="900" letter-spacing="-1">YouTube</text>
        </svg>
    </div>
    <h2 style="text-align: center; color: white; margin-top: -5px; margin-bottom: 5px; font-weight: 700; letter-spacing: -0.5px;">🚀 YouTube Live Streaming</h2>
    <h3 style="text-align: center; color: white; margin-top: -4px; margin-bottom: 20px; font-weight: 500; font-size: 16px;">Dashboard v2.5 - Stream Control</h3>
""", unsafe_allow_html=True)

# --- 2. STREAM KEY INPUT ---
saved_key = load_stream_key()
stream_key = st.text_input("Youtube Stream Key", type="password", value=saved_key or "xxxx")
if stream_key != saved_key:
    save_stream_key(stream_key)

st.write("")

# --- 3. VIDEO LIST CARD (READ-ONLY & CASE-INSENSITIVE) ---
st.markdown('<div class="custom-card">', unsafe_allow_html=True)
st.markdown("<h3 style='margin:0; font-size:18px; font-weight:600; color:white;'>Video List</h3>", unsafe_allow_html=True)

# List Video files (Case-insensitive match)
video_files = [os.path.join(VIDEO_DIR, f) for f in os.listdir(VIDEO_DIR) if f.lower().endswith('.mp4')]
if video_files:
    v_path = video_files[0]
    v_filename = os.path.basename(v_path)
    # Simple formatting title from filename
    v_display_title = os.path.splitext(v_filename)[0].replace("-", " ").replace("_", " ").title()
    
    st.markdown(f"""
        <div class="item-row" style="margin-top: 15px;">
            <div class="item-left">
                <img class="item-thumb" src="{DEFAULT_COVER}" alt="Video thumb">
                <div class="item-info">
                    <div class="item-title">{v_display_title}</div>
                    <div class="item-subtitle">{v_filename}</div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("<div style='color:#666666; font-size:14px; margin-top:15px; font-style:italic;'>Tidak ada video aktif di folder. Silakan upload file video (.mp4) via WinSCP atau AndFTP Anda.</div>", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# --- 4. MUSIC LIST CARD (CASE-INSENSITIVE) ---
st.markdown('<div class="custom-card">', unsafe_allow_html=True)
col_m_title, col_m_btn = st.columns([5, 1])
with col_m_title:
    st.markdown("<h3 style='margin:0; font-size:18px; font-weight:600; color:white;'>Music list</h3>", unsafe_allow_html=True)
with col_m_btn:
    if st.button("➕ Add", key="add_m_trigger", use_container_width=True):
        st.session_state.show_add_music = not st.session_state.show_add_music

# Inline Music Upload form
if st.session_state.show_add_music:
    st.markdown("<div style='margin-top:15px; padding:15px; background:#1f1f1f; border-radius:8px;'>", unsafe_allow_html=True)
    uploaded_audio = st.file_uploader("Upload audio track baru (.mp3)", type=["mp3"])
    if uploaded_audio is not None:
        with open(os.path.join(AUDIO_DIR, uploaded_audio.name), "wb") as f:
            f.write(uploaded_audio.getbuffer())
        st.success(f"Berhasil menambahkan track: {uploaded_audio.name}")
        st.session_state.show_add_music = False
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# List Music files sorted alphabetically (Case-insensitive match)
audio_files = sorted([os.path.join(AUDIO_DIR, f) for f in os.listdir(AUDIO_DIR) if f.lower().endswith('.mp3')])
total_duration_sec = 0

if audio_files:
    st.markdown("<div style='margin-top:10px;'>", unsafe_allow_html=True)
    for idx, audio_path in enumerate(audio_files):
        filename = os.path.basename(audio_path)
        duration = get_audio_duration(audio_path)
        total_duration_sec += duration
        
        minutes, seconds = divmod(int(duration), 60)
        formatted_duration = f"{minutes:02d}:{seconds:02d}"
        
        # Get Album art base64 / default cover URL
        cover_src = get_audio_thumbnail_b64(audio_path)
        
        # Human friendly title
        clean_title = os.path.splitext(filename)[0]
        # Remove common numeric sorting prefixes from view
        if "_" in clean_title and clean_title.split("_")[0].isdigit():
            clean_title = clean_title.split("_", 1)[1]
        clean_title = clean_title.replace("-", " ").replace("_", " ").title()

        # HTML Row layout
        st.markdown(f"""
            <div class="item-row">
                <div class="item-left">
                    <img class="item-thumb" src="{cover_src}" alt="Audio Cover">
                    <div class="item-info">
                        <div class="item-title">{clean_title}</div>
                        <div class="item-subtitle">{filename}</div>
                    </div>
                </div>
                <div class="item-duration">{formatted_duration}</div>
            </div>
        """, unsafe_allow_html=True)
        
        # Actions columns underneath the row
        col_act_dummy, col_act_pop = st.columns([5, 1])
        with col_act_pop:
            with st.popover("⋮ Actions", key=f"pop_{idx}"):
                new_name = st.text_input("Rename File", value=filename, key=f"ren_input_{idx}")
                if new_name != filename:
                    os.rename(audio_path, os.path.join(AUDIO_DIR, new_name))
                    st.rerun()
                if st.button("🗑️ Delete", key=f"del_btn_{idx}", use_container_width=True):
                    os.remove(audio_path)
                    st.rerun()
                    
    st.markdown("</div>", unsafe_allow_html=True)
else:
    st.markdown("<div style='color:#666666; font-size:14px; margin-top:15px; font-style:italic;'>Playlist kosong. Silakan upload file MP3.</div>", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# --- 5. NUMBER LOOP INPUT ---
loop_count = st.number_input("Number Loop", min_value=1, value=5, step=1)

# Estimate total broadcast runtime
total_min = total_duration_sec / 60
grand_total_min = total_min * loop_count
hours, mins = divmod(int(grand_total_min), 60)

# Display calculations as sleek mini status indicators
if total_duration_sec > 0:
    st.markdown(f"""
        <div style="background-color:#161616; padding:15px; border-radius:10px; border: 1px solid #222222; margin-top:15px; font-size:13.5px; color:#aaaaaa;">
            📊 <b>Estimasi Live Selesai (Auto-Stop):</b> 
            {int(total_min)} menit/playlist × {loop_count} Loop = <b>{hours} Jam {mins} Menit</b>
        </div>
    """, unsafe_allow_html=True)

st.write("")

# --- 6. PLAY / STOP LIVE BUTTON ---
if is_running:
    st.markdown(f"""
        <div style="text-align: center; color: #2ecc71; font-weight: 600; font-size: 14px; margin-bottom: 12px;">
            🟢 LIVE STREAM SEDANG BERJALAN (PID: {run_pid})
        </div>
    """, unsafe_allow_html=True)
    
    if st.button("🟥 Stop Live", key="stop_live_btn", use_container_width=True):
        os.kill(run_pid, signal.SIGTERM)
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
        st.rerun()
else:
    st.markdown(f"""
        <div style="text-align: center; color: #e74c3c; font-weight: 600; font-size: 14px; margin-bottom: 12px;">
            🔴 STATUS: OFFLINE
        </div>
    """, unsafe_allow_html=True)
    
    if st.button("▶️ Play Live", key="play_live_btn", use_container_width=True):
        if not stream_key or stream_key == "paste-your-youtube-stream-key-here":
            st.error("Silakan masukkan Youtube Stream Key yang valid!")
        elif not video_files:
            st.error("Gagal memulai! Silakan upload file video background terlebih dahulu.")
        elif not audio_files:
            st.error("Gagal memulai! Silakan upload minimal 1 lagu di Playlist.")
        else:
            # Trigger engine core_stream.py di background
            p = subprocess.Popen(["python3", "/home/amekuning2/web_panel/core_stream.py", stream_key, str(loop_count)])
            with open(PID_FILE, "w") as f:
                f.write(str(p.pid))
            st.rerun()
```
eof

```python:Stream Core Engine:core_stream.py
import os
import sys
import subprocess
import time

def get_stream_files():
    video_dir = "/home/amekuning2/web_panel/video"
    audio_dir = "/home/amekuning2/web_panel/audio"
    
    # Case-insensitive file lists (using lower match logic)
    video_files = [os.path.join(video_dir, f) for f in os.listdir(video_dir) if f.lower().endswith('.mp4')]
    audio_files = sorted([os.path.join(audio_dir, f) for f in os.listdir(audio_dir) if f.lower().endswith('.mp3')]) # Urut alfabetis
    
    return video_files[0] if video_files else None, audio_files

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 core_stream.py <STREAM_KEY> <TOTAL_LOOPS>")
        sys.exit(1)
        
    STREAM_KEY = sys.argv[1]
    TOTAL_LOOPS = int(sys.argv[2])
    RTMP_URL = f"rtmp://a.rtmp.youtube.com/live2/{STREAM_KEY}"
    
    video_file, audio_files = get_stream_files()
    
    if not video_file or not audio_files:
        print("Error: Video atau Audio tidak ditemukan!")
        sys.exit(1)
        
    print(f"Menggunakan Video: {video_file}")
    print(f"Total Audio terdeteksi: {len(audio_files)} file. Target Loop: {TOTAL_LOOPS}x")
    
    # Membuat txt file untuk concat audio berdasarkan jumlah loop
    playlist_path = "/home/amekuning2/web_panel/audio_playlist.txt"
    with open(playlist_path, "w") as f:
        for _ in range(TOTAL_LOOPS):
            for audio in audio_files:
                # FFmpeg concat butuh path yang di-escape jika ada spasi
                f.write(f"file '{audio}'\n")
                
    # Command FFmpeg: 
    # -stream_loop -1 untuk melooping video tanpa batas
    # -f concat untuk memutar list audio sesuai jumlah loop sampai habis (Auto-Stop)
    ffmpeg_cmd = [
        'ffmpeg',
        '-re',
        '-stream_loop', '-1',          # Loop video selamanya sampai audio habis
        '-i', video_file,
        '-f', 'concat', '-safe', '0', '-i', playlist_path, # Audio sekuensial ber-loop
        '-c:v', 'libx264',
        '-pix_fmt', 'yuv420p',
        '-preset', 'veryfast',         # Spek e2-standard-2 kuat dan aman
        '-b:v', '2500k',               # Bitrate standar untuk 720p 24/30fps
        '-maxrate', '2500k',
        '-bufsize', '5000k',
        '-g', '48',                    # Keyframe interval (2 detik untuk 24fps)
        '-c:a', 'aac',
        '-b:a', '128k',
        '-ar', '44100',
        '-f', 'flv',
        RTMP_URL
    ]
    
    print("Mulai streaming ke YouTube...")
    process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    
    # Menulis log sederhana untuk dipantau UI jika dibutuhkan
    with open("/home/amekuning2/web_panel/stream.log", "w") as log_file:
        for line in process.stdout:
            log_file.write(line)
            log_file.flush()
            
    process.wait()
    print("Streaming selesai (Target Loop terpenuhi / dihentikan).")

if __name__ == "__main__":
    main()
```
eof

### 🛠️ Apa Saja Yang Sudah Diperbaiki?

1. **Format File Sempurna:** Sekarang kedua file di atas sudah berbentuk *pure coding syntax* yang sangat ramah disalin (bukan rich text bertumpuk lagi).
2. **Pencarian File Case-Insensitive Sempurna:** Menggunakan `os.listdir` yang digabungkan dengan `.lower().endswith()` sehingga file berakhiran `.MP3` (huruf besar) seperti **"I’m Wishing.MP3"** otomatis langsung dibaca dengan lancar oleh web panel dan juga oleh engine streaming-nya!

Coba salin ulang isinya ke dalam file masing-masing di VPS lu, lalu restart Streamlit-nya seperti biasa lewat SSH:
```bash
pkill -f streamlit
cd /home/amekuning2/web_panel/
nohup streamlit run live-stream-app.py --server.port 8501 --server.maxUploadSize=1024 &
```
Lagu **"I’m Wishing.MP3"** milik lu dijamin langsung muncul di daftar putar dengan sangat indah!