# /home/amekuning2/web_panel/core_stream.py
import os
import sys
import re
import subprocess
import time

RESTART_INTERVAL = 2700  # Restart FFmpeg setiap 45 menit (dalam detik)

def natural_sort_key(s):
    return [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', s)]

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
        raw = [f for f in os.listdir(audio_dir) if f.lower().endswith('.mp3')]
        raw.sort(key=natural_sort_key)
        audio_files = [os.path.join(audio_dir, f) for f in raw]

    return video_files[0] if video_files else None, audio_files

def get_audio_duration(filepath):
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
             '-of', 'default=noprint_wrappers=1:nokey=1', filepath],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10
        )
        return float(result.stdout.strip())
    except:
        return 0

def build_playlist(audio_files, total_loops, playlist_path):
    with open(playlist_path, "w") as f:
        for _ in range(total_loops):
            for audio in audio_files:
                escaped = audio.replace("'", "\\'")
                f.write(f"file '{escaped}'\n")

def run_ffmpeg(video_file, playlist_path, rtmp_url, duration_limit=None):
    """Jalankan FFmpeg, return process object."""
    cmd = [
        'ffmpeg', '-y',
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
        '-preset', 'ultrafast',
        '-tune', 'zerolatency',
        '-b:v', '2500k',
        '-maxrate', '2500k',
        '-bufsize', '5000k',
        '-g', '48',
        '-c:a', 'aac',
        '-b:a', '128k',
        '-ar', '44100',
        '-ac', '2',
        '-af', 'aresample=async=1',
    ]

    if duration_limit:
        cmd += ['-t', str(duration_limit)]

    cmd += ['-shortest', '-f', 'flv', rtmp_url]

    return subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 core_stream.py <STREAM_KEY> <TOTAL_LOOPS>")
        sys.exit(1)

    STREAM_KEY  = sys.argv[1]
    TOTAL_LOOPS = int(sys.argv[2])
    RTMP_URL    = f"rtmp://a.rtmp.youtube.com/live2/{STREAM_KEY}"
    LOG_PATH    = "/home/amekuning2/web_panel/stream.log"
    PLAYLIST    = "/home/amekuning2/web_panel/audio_playlist.txt"

    video_file, audio_files = get_stream_files()

    if not video_file or not audio_files:
        print("Error: Video atau Audio tidak ditemukan!")
        sys.exit(1)

    print(f"Video   : {video_file}")
    print(f"Audio   : {len(audio_files)} file, Loop: {TOTAL_LOOPS}x")

    # Hitung total durasi playlist
    total_audio_sec = sum(get_audio_duration(f) for f in audio_files) * TOTAL_LOOPS
    print(f"Estimasi durasi total: {total_audio_sec/3600:.2f} jam")

    # Build playlist lengkap
    build_playlist(audio_files, TOTAL_LOOPS, PLAYLIST)

    stream_start = time.time()
    elapsed_audio = 0  # Detik audio yang sudah diputar

    log_file = open(LOG_PATH, "w")

    try:
        while True:
            remaining = total_audio_sec - elapsed_audio
            if remaining <= 0:
                print("Semua loop selesai. Stream dihentikan.")
                break

            # Limit per segment = min(RESTART_INTERVAL, sisa durasi)
            segment_dur = min(RESTART_INTERVAL, remaining)

            print(f"[{time.strftime('%H:%M:%S')}] Segment baru, durasi: {segment_dur:.0f}s, sisa: {remaining:.0f}s")
            log_file.write(f"\n=== Segment baru | {time.strftime('%Y-%m-%d %H:%M:%S')} | durasi: {segment_dur:.0f}s ===\n")
            log_file.flush()

            seg_start = time.time()
            process = run_ffmpeg(video_file, PLAYLIST, RTMP_URL, duration_limit=segment_dur)

            # Stream log ke file
            for line in process.stdout:
                log_file.write(line)
                log_file.flush()

            process.wait()
            seg_elapsed = time.time() - seg_start
            elapsed_audio += seg_elapsed

            rc = process.returncode
            print(f"[{time.strftime('%H:%M:%S')}] FFmpeg selesai (rc={rc}), elapsed: {seg_elapsed:.0f}s")

            # Kalau FFmpeg exit bukan karena -t habis (rc != 0) dan masih ada sisa → restart
            if rc != 0 and elapsed_audio < total_audio_sec:
                print("FFmpeg error, restart dalam 3 detik...")
                time.sleep(3)
                continue

            # Kalau segment selesai normal tapi masih ada sisa audio → loop ke segment berikutnya
            if elapsed_audio < total_audio_sec - 5:
                print("Segment selesai, lanjut segment berikutnya...")
                time.sleep(1)
                continue

            # Semua selesai
            break

    finally:
        log_file.close()
        print("Streaming selesai.")

if __name__ == "__main__":
    main()