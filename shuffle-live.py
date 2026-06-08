import os
import sys
import subprocess
import random

# Fungsi untuk mengambil semua ID file dari folder GDrive Public
def get_files_from_folder(folder_id):
    cmd = f"yt-dlp --flat-playlist --get-id \"https://drive.google.com/drive/folders/{folder_id}\""
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode == 0:
        return [f_id.strip() for f_id in result.stdout.split('\n') if f_id.strip()]
    return []

def main():
    if len(sys.argv) < 4:
        print("Error: Argumen kurang! Butuh stream_key, video_folder_id, audio_folder_id")
        sys.exit(1)
        
    stream_key = sys.argv[1]
    video_folder_id = sys.argv[2]
    audio_folder_id = sys.argv[3]
    
    print("🧹 Membersihkan sisa file lama...")
    os.system("rm -f vid_temp.mp4 aud_temp.mp3")
    
    print("🔍 Mengambil list file dari Google Drive...")
    list_video = get_files_from_folder(video_folder_id)
    list_audio = get_files_from_folder(audio_folder_id)
    
    if not list_video or not list_audio:
        print("❌ Gagal membaca folder GDrive! Pastikan folder di-set PUBLIC.")
        sys.exit(1)
        
    print(f"✅ Terdeteksi {len(list_video)} Video dan {len(list_audio)} Musik. Memulai Shuffle Stream...")
    
    while True:
        id_video_acak = random.choice(list_video)
        id_audio_acak = random.choice(list_audio)
        
        print(f"📥 Downloading: Video ID {id_video_acak} & Audio ID {id_audio_acak}")
        
        cmd_dl_vid = f"yt-dlp --no-check-certificate \"https://drive.google.com/file/d/{id_video_acak}/view\" -o vid_temp.mp4"
        cmd_dl_aud = f"yt-dlp --no-check-certificate \"https://drive.google.com/file/d/{id_audio_acak}/view\" -o aud_temp.mp3"
        
        subprocess.run(cmd_dl_vid, shell=True)
        subprocess.run(cmd_dl_aud, shell=True)
        
        print("📺 Broadcasting live stream dengan Audio Spectrum...")
        
        # Perintah FFmpeg + Audio Spectrum Irit CPU (Preset Ultrafast)
        cmd_ffmpeg = (
            f"ffmpeg -re -i vid_temp.mp4 -i aud_temp.mp3 "
            f"-filter_complex \"[1:a]showwaves=s=300x100:mode=p2p:r=25:colors=white[spectrum];"
            f"[0:v][spectrum]overlay=x=20:y=main_h-overlay_h-20[outv]\" "
            f"-map \"[outv]\" -map 1:a -c:v libx264 -preset ultrafast -b:v 2500k "
            f"-g 60 -c:a aac -b:a 128k -ar 44100 -f flv \"rtmp://a.rtmp.youtube.com/live2/{stream_key}\""
        )
        
        process = subprocess.Popen(cmd_ffmpeg, shell=True)
        process.wait()
        
        # Hapus file biar storage VPS ga bengkak
        os.system("rm -f vid_temp.mp4 aud_temp.mp3")

if __name__ == "__main__":
    main()