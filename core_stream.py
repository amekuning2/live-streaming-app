# /home/amekuning2/web_panel/core_stream.py
import os
import sys
import subprocess
import glob
import time

def get_stream_files():
    video_dir = "/home/amekuning2/web_panel/video"
    audio_dir = "/home/amekuning2/web_panel/audio"
    
    video_files = glob.glob(os.path.join(video_dir, "*.mp4"))
    audio_files = sorted(glob.glob(os.path.join(audio_dir, "*.mp3"))) # Urut alfabetis
    
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
        '-map', '0:v:0',               # video dari input pertama (video file)
        '-map', '1:a:0',               # audio dari input kedua (playlist)
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