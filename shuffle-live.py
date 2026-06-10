import os
import random
import subprocess
import sys
import time

VIDEO_DIR = "/home/amekuning2/web_panel/video"
AUDIO_DIR = "/home/amekuning2/web_panel/audio"

STREAM_KEY = sys.argv[1]
RTMP_URL = f"rtmp://a.rtmp.youtube.com/live2/{STREAM_KEY}"


def get_files(folder, ext):
    return [
        os.path.join(folder, f)
        for f in os.listdir(folder)
        if f.lower().endswith(ext)
    ]


def get_duration(filepath):
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", filepath],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10
        )
        return float(result.stdout.strip())
    except:
        return 0


while True:
    try:
        videos = get_files(VIDEO_DIR, ".mp4")
        audios = get_files(AUDIO_DIR, ".mp3")

        if not videos:
            print("ERROR: Tidak ada file .mp4 di folder video")
            time.sleep(10)
            continue

        if not audios:
            print("ERROR: Tidak ada file .mp3 di folder audio")
            time.sleep(10)
            continue

        video_file = random.choice(videos)
        audio_file = random.choice(audios)

        dur_aud = get_duration(audio_file)
        seg_dur = dur_aud if dur_aud > 0 else 300

        print("=" * 60)
        print(f"VIDEO : {os.path.basename(video_file)}")
        print(f"AUDIO : {os.path.basename(audio_file)}")
        print(f"DURASI: {seg_dur:.0f} detik")
        print("=" * 60)

        cmd = [
            "ffmpeg",
            "-re",
            "-stream_loop", "-1",   # loop video
            "-i", video_file,
            "-i", audio_file,       # audio tidak di-loop
            "-map", "0:v:0",        # ambil video dari file pertama
            "-map", "1:a:0",        # ambil audio dari file kedua
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-tune", "zerolatency",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "128k",
            "-ar", "44100",
            "-b:v", "2500k",
            "-maxrate", "2500k",
            "-bufsize", "5000k",
            "-g", "60",
            "-t", str(seg_dur),     # stop setelah audio habis
            "-f", "flv",
            RTMP_URL
        ]

        process = subprocess.Popen(cmd)
        process.wait()

        print("Selesai, next lagu...")
        time.sleep(2)

    except Exception as e:
        print("ERROR:", str(e))
        time.sleep(10)