# /home/amekuning2/web_panel/core_stream.py
import os
import sys
import subprocess

def get_stream_files():
    video_dir = "/home/amekuning2/web_panel/video"
    audio_dir = "/home/amekuning2/web_panel/audio"

    video_files = []
    if os.path.exists(video_dir):
        video_files = [
            os.path.join(video_dir, f) for f in os.listdir(video_dir)
            if f.lower().endswith('.mp4')
        ]

    audio_files = []
    if os.path.exists(audio_dir):
        audio_files = [
            os.path.join(audio_dir, f) for f in os.listdir(audio_dir)
            if f.lower().endswith('.mp3')
        ]
    audio_files.sort()

    return video_files[0] if video_files else None, audio_files

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 core_stream.py <STREAM_KEY> <TOTAL_LOOPS>")
        sys.exit(1)

    STREAM_KEY = sys.argv[1]
    TOTAL_LOOPS = int(sys.argv[2])
    RTMP_URL = f"rtmp://a.rtmp.youtube.com/live2/{STREAM_KEY}"  # FIX: URL bersih

    video_file, audio_files = get_stream_files()

    if not video_file or not audio_files:
        print("Error: Video atau Audio tidak ditemukan!")
        sys.exit(1)

    print(f"Menggunakan Video: {video_file}")
    print(f"Total Audio: {len(audio_files)} file. Loop: {TOTAL_LOOPS}x")

    # Generate playlist
    playlist_path = "/home/amekuning2/web_panel/audio_playlist.txt"
    with open(playlist_path, "w") as f:
        for _ in range(TOTAL_LOOPS):
            for audio in audio_files:
                # Escape single quote di nama file
                escaped = audio.replace("'", "'\\''")
                f.write(f"file '{escaped}'\n")

    ffmpeg_cmd = [
        'ffmpeg',
        '-re',
        '-fflags', '+genpts',
        '-stream_loop', '-1',
        '-i', video_file,
        '-f', 'concat', '-safe', '0',
        '-i', playlist_path,
        '-map', '0:v:0',
        '-map', '1:a:0',
        '-c:v', 'libx264',
        '-pix_fmt', 'yuv420p',
        '-preset', 'ultrafast',       # ultrafast lebih stabil jangka panjang
        '-tune', 'zerolatency',
        '-b:v', '2500k',
        '-maxrate', '2500k',
        '-bufsize', '5000k',
        '-g', '48',
        '-c:a', 'aac',
        '-b:a', '128k',
        '-ar', '44100',
        '-ac', '2',
        '-af', 'aresample=async=1',   # sinkronisasi audio real-time
        '-shortest',                  # auto-stop saat playlist audio habis
        '-f', 'flv',
        RTMP_URL
    ]

    print("Mulai streaming ke YouTube...")
    process = subprocess.Popen(
        ffmpeg_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    with open("/home/amekuning2/web_panel/stream.log", "w") as log_file:
        for line in process.stdout:
            log_file.write(line)
            log_file.flush()

    process.wait()
    print("Streaming selesai.")

if __name__ == "__main__":
    main()