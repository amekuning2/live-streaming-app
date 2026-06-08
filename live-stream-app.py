import streamlit as st
import os
import re
import subprocess
import time

st.set_page_config(page_title="Live Stream Control Panel", page_icon="🚀", layout="centered")

st.title("🚀 Control Panel Live Stream")
st.write("Kontrol & Pantau Progress Download GDrive Langsung dari Sini")

stream_key = st.text_input("Stream Key YouTube:", placeholder="Masukkan Stream Key YouTube lo...")
gdrive_link = st.text_input("Link Google Drive Video:", placeholder="https://drive.google.com/file/d/...")
tipe_stream = st.selectbox("Format Video / Tipe Stream:", ["Horizontal Standard (16:9)", "Vertikal / Shorts (9:16)"])

def extract_gdrive_id(url):
    match = re.search(r'(?:id=|/d/|/file/d/)([\w-]+)', url)
    return match.group(1) if match else None

col1, col2 = st.columns(2)

with col1:
    if st.button("🚀 MULAI LIVE STREAMING", type="primary", use_container_width=True):
        if not stream_key or not gdrive_link:
            st.error("Isi data Stream Key dan Link GDrive dulu, bro!")
        else:
            file_id = extract_gdrive_id(gdrive_link)
            if not file_id:
                st.error("ID Google Drive tidak valid!")
            else:
                st.info("Membuang sisa stream lama & membersihkan sisa file...")
                os.system("pkill -f ffmpeg")
                os.system("pkill -f yt-dlp")
                os.system("rm -f video.mp4")

                st.warning("Menghubungkan ke Google Drive... Mohon tunggu sebentar.")
                
                cmd_download = f"yt-dlp --no-check-certificate \"https://drive.google.com/file/d/{file_id}/view\" -o video.mp4"
                process = subprocess.Popen(cmd_download, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

                progress_bar = st.progress(0)
                status_text = st.empty()
                meta_text = st.empty()

                for line in iter(process.stdout.readline, ''):
                    if "[download]" in line and "%" in line:
                        match_percent = re.search(r'(\d+\.\d+)%', line)
                        match_speed = re.search(r'at\s+([^\s]+)', line)
                        match_eta = re.search(r'ETA\s+([^\s]+)', line)
                        
                        if match_percent:
                            persen_float = float(match_percent.group(1))
                            persen_int = int(persen_float)
                            progress_bar.progress(persen_int / 100.0)
                            status_text.text(f"📥 Sedang Mendownload Video: {persen_int}%")
                        
                        speed_str = match_speed.group(1) if match_speed else "0 MiB/s"
                        eta_str = match_eta.group(0) if match_eta else "ETA --:--"
                        meta_text.caption(f"⚡ Kecepatan: {speed_str} | ⏳ {eta_str}")

                process.stdout.close()
                process.wait()

                if process.returncode != 0:
                    st.error("❌ Download Gagal! Periksa kuota VPS atau link GDrive lo.")
                else:
                    progress_bar.progress(1.0)
                    status_text.text("📥 Download Selesai 100%!")
                    st.info("🎬 Mengirim semburan live stream ke YouTube...")

                    if "Vertikal" in tipe_stream:
                        video_filter = "-vf \"scale=ih*16/9:ih:force_original_aspect_ratio=decrease,crop=1080:1920,setsar=1\""
                    else:
                        video_filter = "-vf \"scale=1280:720,setsar=1\""

                    cmd_ffmpeg = (
                        f"ffmpeg -re -stream_loop -1 -i video.mp4 "
                        f"{video_filter} -c:v libx264 -preset ultrafast -b:v 2500k "
                        f"-g 60 -c:a aac -b:a 128k -ar 44100 "
                        f"-f flv \"rtmp://a.rtmp.youtube.com/live2/{stream_key}\""
                    )

                    subprocess.Popen(cmd_ffmpeg, shell=True)
                    st.success("✅ [SUKSES] FFmpeg Berjalan! Live lo sudah ON di YouTube.")

with col2:
    if st.button("🛑 MATIKAN LIVE STREAMING", type="secondary", use_container_width=True):
        os.system("pkill -f ffmpeg")
        os.system("pkill -f yt-dlp")
        os.system("rm -f video.mp4")
        st.success("🛑 Streaming di VPS berhasil dimatikan total!")
