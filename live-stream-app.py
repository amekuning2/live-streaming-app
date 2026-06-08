import streamlit as st
import os
import re
import subprocess

st.set_page_config(page_title="Live Stream Control Panel", page_icon="🚀", layout="centered")

st.title("🚀 Control Panel Live Stream (Shuffle Mode)")
st.write("Sistem otomatis acak Video & Musik dari Folder Google Drive + Audio Spectrum")

stream_key = st.text_input("Stream Key YouTube:", placeholder="Masukkan Stream Key YouTube lo...")
folder_video_link = st.text_input("Link Folder GDrive VIDEO (Mute):", placeholder="https://drive.google.com/drive/folders/...")
folder_audio_link = st.text_input("Link Folder GDrive MUSIK (MP3):", placeholder="https://drive.google.com/drive/folders/...")

def extract_gdrive_id(url):
    match = re.search(r'(?:id=|/folders/|/d/|/file/d/)([\w-]+)', url)
    return match.group(1) if match else None

col1, col2 = st.columns(2)

with col1:
    if st.button("🚀 MULAI LIVE STREAMING", type="primary", use_container_width=True):
        if not stream_key or not folder_video_link or not folder_audio_link:
            st.error("Isi semua data dulu, bro!")
        else:
            video_folder_id = extract_gdrive_id(folder_video_link)
            audio_folder_id = extract_gdrive_id(folder_audio_link)
            
            if not video_folder_id or not audio_folder_id:
                st.error("ID Folder Google Drive tidak valid!")
            else:
                st.info("🧹 Membersihkan sisa live stream lama...")
                os.system("pkill -f ffmpeg")
                os.system("pkill -f yt-dlp")
                os.system("pkill -f core_shuffle.py")
                os.system("rm -f vid_temp.mp4 aud_temp.mp3")
                
                st.success("🎬 Menjalankan Mesin Shuffle Live Stream di Background VPS...")
                
                # Memanggil core_shuffle.py secara independen di background agar Streamlit tidak freeze/loading terus
                cmd_background = f"python3 core_shuffle.py {stream_key} {video_folder_id} {audio_folder_id} > shuffle.log 2>&1 &"
                subprocess.Popen(cmd_background, shell=True)
                
                st.balloons()
                st.info("ℹ️ Live Stream sudah ON. Halaman Wix ini boleh lo tutup, live bakal tetep jalan nonstop!")

with col2:
    if st.button("🛑 MATIKAN LIVE STREAMING", type="secondary", use_container_width=True):
        os.system("pkill -f ffmpeg")
        os.system("pkill -f yt-dlp")
        os.system("pkill -f core_shuffle.py")
        os.system("rm -f vid_temp.mp4 aud_temp.mp3")
        st.success("🛑 Streaming berhasil dimatikan total!")