import streamlit as st
import os
import subprocess

st.set_page_config(
    page_title="YouTube Live Control",
    page_icon="🚀",
    layout="centered"
)

PID_FILE = "shuffle.pid"
LOG_FILE = "shuffle.log"


def is_running():
    result = subprocess.run("pgrep -f shuffle-live.py", shell=True, stdout=subprocess.PIPE)
    return result.returncode == 0


st.title("🚀 YouTube Live Streaming")
st.divider()

stream_key = st.text_input("YouTube Stream Key", type="password", placeholder="xxxx-xxxx-xxxx-xxxx")

col1, col2 = st.columns(2)

with col1:
    if st.button("▶ START", use_container_width=True, type="primary"):
        if not stream_key:
            st.error("Masukkan Stream Key dulu!")
        else:
            os.system("pkill -f ffmpeg")
            os.system("pkill -f shuffle-live.py")
            os.system(f"rm -f {LOG_FILE}")
            cmd = f"nohup python3 /home/amekuning2/web_panel/shuffle-live.py '{stream_key}' > {LOG_FILE} 2>&1 & echo $! > {PID_FILE}"
            subprocess.Popen(cmd, shell=True)
            import time; time.sleep(2)
            if is_running():
                st.success("✅ Streaming Started!")
            else:
                st.warning("⚠️ Cek log untuk detail.")

with col2:
    if st.button("⏹ STOP", use_container_width=True):
        os.system("pkill -f ffmpeg")
        os.system("pkill -f shuffle-live.py")
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
        st.success("🛑 Streaming Stopped!")

st.divider()

# Download log
if os.path.exists(LOG_FILE):
    with open(LOG_FILE, "rb") as f:
        log_data = f.read()
    st.download_button(
        label="⬇️ Download Log",
        data=log_data,
        file_name="stream_log.txt",
        mime="text/plain",
        use_container_width=True
    )
else:
    st.info("Belum ada log.")