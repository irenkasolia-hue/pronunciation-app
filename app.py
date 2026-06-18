import streamlit as st
import random
import tempfile
import base64
import openai
import streamlit.components.v1 as components

st.set_page_config(page_title="Pronunciation Trainer", layout="centered")

# ================= STATE =================
def init(k, v):
    if k not in st.session_state:
        st.session_state[k] = v

init("words", [])
init("mode", "home")

init("practice_i", 0)
init("practice_words", [])

init("test_i", 0)
init("test_words", [])
init("score", 0)

init("mic_audio", None)

# ================= MIC RECORDER =================
def mic_recorder():
    return components.html("""
    <button onclick="startRec()">🎤 Record</button>
    <button onclick="stopRec()">⏹ Stop</button>
    <p id="status"></p>

    <script>
    let recorder;
    let chunks = [];

    async function startRec() {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

        recorder = new MediaRecorder(stream);
        chunks = [];

        recorder.ondataavailable = e => chunks.push(e.data);

        recorder.onstop = async () => {
            const blob = new Blob(chunks, { type: "audio/webm" });

            const reader = new FileReader();
            reader.readAsDataURL(blob);

            reader.onloadend = () => {
                window.parent.postMessage({
                    type: "streamlit:setComponentValue",
                    value: reader.result
                }, "*");
            };
        };

        recorder.start();
        document.getElementById("status").innerText = "Recording...";
    }

    function stopRec() {
        recorder.stop();
        document.getElementById("status").innerText = "Processing...";
    }
    </script>
    """, height=120)

# ================= NAV =================
st.sidebar.title("Menu")

if st.sidebar.button("Home"):
    st.session_state.mode = "home"

if st.sidebar.button("Practice"):
    st.session_state.mode = "practice"

if st.sidebar.button("Test"):
    st.session_state.mode = "test"
    st.session_state.test_words = random.sample(st.session_state.words, min(10, len(st.session_state.words)))
    st.session_state.test_i = 0
    st.session_state.score = 0

# ================= HOME =================
if st.session_state.mode == "home":

    st.title("🧠 Pronunciation Trainer")

    text = st.text_area("Enter words (one per line)")

    if st.button("Add"):
        new_words = [w.strip() for w in text.split("\n") if w.strip()]
        st.session_state.words += new_words

    st.write(st.session_state.words)

# ================= PRACTICE (REAL MIC) =================
elif st.session_state.mode == "practice":

    st.header("🎧 Practice (Speak Mode)")

    if not st.session_state.practice_words:
        st.session_state.practice_words = st.session_state.words.copy()
        random.shuffle(st.session_state.practice_words)

    words = st.session_state.practice_words
    w = words[st.session_state.practice_i]

    st.subheader(f"Say: {w}")

    audio_data = mic_recorder()

    result_box = st.empty()

    if audio_data:

        audio_b64 = audio_data.split(",")[1]
        audio_bytes = base64.b64decode(audio_b64)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
            tmp.write(audio_bytes)
            path = tmp.name

        with open(path, "rb") as f:
            transcript = openai.audio.transcriptions.create(
                model="gpt-4o-mini-transcribe",
                file=f
            ).text.lower().strip()

        st.write("You said:", transcript)

        if transcript == w.lower():
            result_box.success("✔ Correct pronunciation")
        else:
            result_box.error(f"✖ Wrong → expected: {w}")

    if st.button("Next"):
        st.session_state.practice_i += 1
        st.rerun()

# ================= TEST (REAL MIC + SCORE) =================
elif st.session_state.mode == "test":

    st.header("🟥 Test (10 words)")

    words = st.session_state.test_words

    if not words:
        st.warning("No words")
        st.stop()

    if st.session_state.test_i >= len(words):
        st.success(f"Finished ✔ Score: {st.session_state.score}/{len(words)}")
        st.stop()

    w = words[st.session_state.test_i]

    st.write(f"Question {st.session_state.test_i + 1} / {len(words)}")

    st.subheader(f"Say: {w}")

    audio_data = mic_recorder()

    if audio_data:

        audio_b64 = audio_data.split(",")[1]
        audio_bytes = base64.b64decode(audio_b64)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
            tmp.write(audio_bytes)
            path = tmp.name

        with open(path, "rb") as f:
            transcript = openai.audio.transcriptions.create(
                model="gpt-4o-mini-transcribe",
                file=f
            ).text.lower().strip()

        st.write("You said:", transcript)

        if transcript == w.lower():
            st.success("✔ Correct")
            st.session_state.score += 1
        else:
            st.error(f"✖ Wrong → {w}")

    if st.button("Next"):
        st.session_state.test_i += 1
        st.rerun()
