# /home/amekuning2/web_panel/live-stream-app.py
import streamlit as st
import os
import glob
import subprocess
import signal
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC

st.set_page_config(page_title="CPM Control Panel 24/7", layout="wide")

VIDEO_DIR = "/home/amekuning2/web_panel/video"
AUDIO_DIR = "/home/amekuning2/web_panel/audio"
PID_FILE = "/home/amekuning2/web_panel/stream.pid"

os.makedirs(VIDEO_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)

# --- HELPER FUNCTIONS ---
def get_stream_status():
    if os.path.exists(PID_FILE):
        with open(PID_FILE, "r") as f:
            pid = f.read().strip()
        if pid:
            # Cek apakah PID benar-benar berjalan
            try:
                os.kill(int(pid), 0)
                return True, int(pid)
            except OSError:
                return False, None
    return False, None

def get_audio_duration(file_path):
    try:
        audio = MP3(file_path)
        return audio.info.length # dalam detik
    except:
        return 0

def get_audio_thumbnail(file_path):
    try:
        audio = ID3(file_path)
        for tag in audio.values():
            if isinstance(tag, APIC):
                return tag.data # Return bytes gambar
    except:
        pass
    return None

# --- UI HEADER ---
st.title("🎙️ CPM - Cerita Podcast Misteri 24/7 Engine")
st.subheader("Control Panel v2.0 (1 Video Loop + Sequential Audio)")
st.write("---")

# Cek Status Running
is_running, run_pid = get_stream_status()

# --- SIDEBAR: KONTROL STREAM ---
st.sidebar.header("🎛️ Live Stream Controller")
stream_key = st.sidebar.text_input("YouTube Stream Key", type="password", value="xxxx-xxxx-xxxx-xxxx")
loop_count = st.sidebar.number_input("Jumlah Loop Audio", min_value=1, value=5, step=1)

if is_running:
    st.sidebar.success(f"🟢 Status: LIVE (PID: {run_pid})")
    if st.sidebar.button("🔴 STOP STREAM", use_container_width=True):
        os.kill(run_pid, signal.SIGTERM)
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
        st.rerun()
else:
    st.sidebar.error("🔴 Status: OFFLINE")
    if st.sidebar.button("🚀 START STREAM", use_container_width=True):
        if not stream_key:
            st.sidebar.warning("Isi Stream Key dulu!")
        else:
            # Jalankan core_stream.py di background menggunakan nohup / popen
            p = subprocess.Popen(["python3", "/home/amekuning2/web_panel/core_stream.py", stream_key, str(loop_count)])
            with open(PID_FILE, "w") as f:
                f.write(str(p.pid))
            st.rerun()

# --- MAIN CONTENT: ASSET MANAGEMENT ---
tab1, tab2 = st.tabs(["🎥 Video Background (Max 1)", "🎵 Audio Playlist"])

# --- TAB 1: VIDEO ---
with tab1:
    st.header("Video Background")
    video_files = glob.glob(os.path.join(VIDEO_DIR, "*.mp4"))
    
    if video_files:
        st.info(f"Video aktif saat ini: `{os.path.basename(video_files[0])}`")
        if st.button("🗑️ Hapus Video Lama untuk Ganti baru"):
            os.remove(video_files[0])
            st.rerun()
    else:
        uploaded_video = st.file_uploader("Upload Video Background (720p .mp4)", type=["mp4"])
        if uploaded_video is not None:
            with open(os.path.join(VIDEO_DIR, uploaded_video.name), "wb") as f:
                f.write(uploaded_video.getbuffer())
            st.success("Video berhasil diupload!")
            st.rerun()

# --- TAB 2: AUDIO ---
with tab2:
    st.header("Audio Playlist & Estimasi")
    
    # Upload Item Baru
    uploaded_audio = st.file_uploader("➕ Add Item (Upload MP3 Baru)", type=["mp3"])
    if uploaded_audio is not None:
        with open(os.path.join(AUDIO_DIR, uploaded_audio.name), "wb") as f:
            f.write(uploaded_audio.getbuffer())
        st.success(f"Berhasil menambah file: {uploaded_audio.name}")
        st.rerun()
        
    st.write("---")
    
    # List & Urutan Audio
    audio_files = sorted(glob.glob(os.path.join(AUDIO_DIR, "*.mp3")))
    
    if not audio_files:
        st.warning("Belum ada file audio di folder `audio/`")
    else:
        total_duration_sec = 0
        st.write("💡 *Tips: Ubah nama file (Rename) dengan awalan angka (misal: 01_lagu.mp3) untuk mengatur urutan putar.*")
        
        # Tampilkan List Audio dalam bentuk Grid/Table rapi
        for idx, audio_path in enumerate(audio_files):
            filename = os.path.basename(audio_path)
            duration = get_audio_duration(audio_path)
            total_duration_sec += duration
            
            minutes, seconds = divmod(int(duration), 60)
            img_data = get_audio_thumbnail(audio_path)
            
            col1, col2, col3, col4 = st.columns([1, 4, 2, 2])
            
            with col1:
                if img_data:
                    st.image(img_data, width=60)
                else:
                    st.image("https://placehold.co/60x60?text=MP3", width=60) # Placeholder jika ga ada metadata gambar
                    
            with col2:
                st.write(f"**{idx+1}. {filename}**")
                
            with col3:
                st.write(f"⏱️ {minutes:02d}:{seconds:02d}")
                
            with col4:
                # Fitur Rename & Delete
                new_name = st.text_input("Rename", value=filename, key=f"ren_{idx}", label_visibility="collapsed")
                if new_name != filename:
                    os.rename(audio_path, os.path.join(AUDIO_DIR, new_name))
                    st.rerun()
                    
                if st.button("🗑️ Delete", key=f"del_{idx}"):
                    os.remove(audio_path)
                    st.rerun()
            st.write("---")
            
        # --- KALKULASI LOOP & ESTIMASI AUTO STOP ---
        total_min = total_duration_sec / 60
        grand_total_min = total_min * loop_count
        hours, mins = divmod(int(grand_total_min), 60)
        
        st.subheader("📊 Estimasi Durasi Live Stream")
        c1, c2, c3 = st.columns(3)
        c1.metric("Durasi 1 Sesi Playlist", f"{int(total_min)} Menit")
        c2.metric("Setting Target Loop", f"{loop_count}x Loop")
        c3.metric("Total Durasi Live (Auto-Stop)", f"{hours} Jam {mins} Menit")