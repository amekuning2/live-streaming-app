import streamlit as st
import os
import subprocess

st.set_page_config(
    page_title="YouTube Live Control",
    page_icon="📺",
    layout="centered"
)

PID_FILE = "shuffle.pid"

st.title("🎥 YouTube Live Streaming VPS")

stream_key = st.text_input(
    "YouTube Stream Key",
    type="password"
)

col1, col2 = st.columns(2)

with col1:

    if st.button(
        "▶️ START",
        use_container_width=True,
        type="primary"
    ):

        if not stream_key:
            st.error("Masukkan Stream Key")
        else:

            os.system("pkill -f ffmpeg")
            os.system("pkill -f shuffle-live.py")

            cmd = f"nohup python3 shuffle-live.py '{stream_key}' > shuffle.log 2>&1 & echo $! > {PID_FILE}"

            subprocess.Popen(
                cmd,
                shell=True
            )

            st.success("Streaming Started")

with col2:

    if st.button(
        "⛔ STOP",
        use_container_width=True
    ):

        os.system("pkill -f ffmpeg")
        os.system("pkill -f shuffle-live.py")

        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)

        st.success("Streaming Stopped")

st.divider()

st.subheader("Log")

if os.path.exists("shuffle.log"):

    try:

        with open(
            "shuffle.log",
            "r"
        ) as f:

            logs = f.read()

        st.code(logs[-10000:])

    except:
        pass

else:

    st.info("Belum ada log")