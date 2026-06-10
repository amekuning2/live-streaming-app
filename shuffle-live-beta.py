import os
import random
import subprocess
import sys
import time

VIDEO_DIR = "/home/amekuning2/web_panel/video"
AUDIO_DIR = "/home/amekuning2/web_panel/audio"

STREAM_KEY = sys.argv[1]

RTMP_URL = f"rtmp://a.rtmp.youtube.com/live2/{STREAM_KEY}"


def random_video():

    files = [
        os.path.join(VIDEO_DIR, f)
        for f in os.listdir(VIDEO_DIR)
        if f.lower().endswith(".mp4")
    ]

    if len(files) == 0:
        raise Exception("NO VIDEO FOUND")

    return random.choice(files)


def random_audio():

    files = [
        os.path.join(AUDIO_DIR, f)
        for f in os.listdir(AUDIO_DIR)
        if f.lower().endswith(".mp3")
    ]

    if len(files) == 0:
        raise Exception("NO AUDIO FOUND")

    return random.choice(files)


while True:

    try:

        video_file = random_video()
        audio_file = random_audio()

        print("=" * 60)
        print("VIDEO :", video_file)
        print("AUDIO :", audio_file)
        print("=" * 60)

        cmd = [
            "ffmpeg",
            "-re",
            "-stream_loop",
            "-1",
            "-i",
            video_file,
            "-stream_loop",
            "-1",
            "-i",
            audio_file,
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-ar",
            "44100",
            "-b:v",
            "2500k",
            "-maxrate",
            "2500k",
            "-bufsize",
            "5000k",
            "-g",
            "60",
            "-f",
            "flv",
            RTMP_URL
        ]

        process = subprocess.Popen(cmd)

        process.wait()

        print("FFMPEG EXIT")
        time.sleep(5)

    except Exception as e:

        print("ERROR:", str(e))
        time.sleep(10)