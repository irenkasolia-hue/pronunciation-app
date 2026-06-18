import streamlit as st
import random
import tempfile
import base64
import openai
import streamlit.components.v1 as components

st.set_page_config(page_title="Pronunciation Trainer", layout="centered")

# ================= SAFE INIT =================
def init(key, value):
    if key not in st.session_state:
        st.session_state[key] = value

init("mode", "home")
init("words", [])
init("weak", [])

init("study_i", 0)

init("practice_words", [])
init("practice_i", 0)

init("test_words", [])
init("test_i", 0)
init("score", 0)

init("answered", False)

# ================= DICTIONARY =================
def get_word_data(word):
    try:
        url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
        res = requests.get(url, timeout=5).json()

        ipa = res[0].get("phonetic", "N/A")
        definition = res[0]["meanings"][0]["definitions"][0]["definition"]

        audio = ""
        for p in res[0].get("phonetics", []):
            if p.get("audio"):
                audio = p["audio"]
                break

        return ipa, definition, audio
    except:
        return "N/A", "No definition available", ""

# ================= MIC COMPONENT =================
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

# ================= RESET HELPERS =================
def reset_practice():
    st.session_state.practice_words = st.session_state.words.copy()
    random.shuffle(st.session_state.practice_words)
    st.session_state.practice_i = 0
    st.session_state.answered = False

def reset_test():
    st.session_state.test_words = random.sample(
        st.session_state.words,
        min(10, len(st.session_state.words))
    )
    st.session_state.test_i = 0
    st.session_state.score = 0
    st.session_state.answered = False

# ================= NAV =================
st.sidebar.title("Navigation")

if st.sidebar.button("Home"):
    st.session_state.mode = "home"

if st.sidebar.button("Study"):
    st.session_state.mode = "study"

if st.sidebar.button("Practice"):
    reset_practice()
    st.session_state.mode = "practice"

if st.sidebar.button("Test"):
    reset_test()
    st.session_state.mode = "test"

if st.sidebar.button("Speech Lab"):
    st.session_state.mode = "speech_lab"

# ================= HOME =================
if st.session_state.mode == "home":

    st.title("🧠 Pronunciation Trainer")

    text = st.text_area("Enter words (one per line)")

    if st.button("Add words"):
        new_words = [w.strip() for w in text.split("\n") if w.strip()]
        st.session_state.words += new_words

    st.write("Word bank:")
    for w in st.session_state.words:
        col1, col2 = st.columns([4,1])
        col1.write(w)
        if col2.button("❌", key=w):
            st.session_state.words.remove(w)
            st.rerun()

# ================= STUDY =================
elif st.session_state.mode == "study":

    st.header("📚 Study Mode")

    if not st.session_state.words:
        st.warning("No words added")
        st.stop()

    st.session_state.study_i %= len(st.session_state.words)
    w = st.session_state.words[st.session_state.study_i]

    ipa, definition, audio = get_word_data(w)

    st.subheader(w)
    st.write("IPA:", ipa)
    st.info(definition)

    if audio:
        st.audio(audio)

    col1, col2 = st.columns(2)

    if col1.button("⬅"):
        st.session_state.study_i -= 1
        st.rerun()

    if col2.button("➡"):
        st.session_state.study_i += 1
        st.rerun()

# ================= PRACTICE =================
elif st.session_state.mode == "practice":

    st.header("🎧 Practice Mode")

    words = st.session_state.practice_words
    if not words:
        st.warning("No words available")
        st.stop()

    st.session_state.practice_i %= len(words)
    w = words[st.session_state.practice_i]

    st.subheader(f"Say: {w}")

    audio_data = mic_recorder()

    col1, col2 = st.columns(2)

    if audio_data and isinstance(audio_data, str) and "," in audio_data:

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

        if not st.session_state.answered:
            if transcript == w.lower():
                st.success("✔ Correct")
            else:
                st.error(f"✖ Incorrect → {w}")
                st.session_state.weak.append(w)
            st.session_state.answered = True

    if col1.button("Next"):
        st.session_state.practice_i += 1
        st.session_state.answered = False
        st.rerun()

# ================= TEST =================
elif st.session_state.mode == "test":

    st.header("🟥 Test Mode")

    words = st.session_state.test_words

    if not words:
        st.warning("No test words")
        st.stop()

    if st.session_state.test_i >= len(words):
        st.success(f"Finished ✔ Score: {st.session_state.score}/{len(words)}")
        st.stop()

    w = words[st.session_state.test_i]

    st.subheader(f"Question {st.session_state.test_i+1}/{len(words)}")
    st.write(f"Say: {w}")

    audio_data = mic_recorder()

    col1, col2 = st.columns(2)

    if audio_data and isinstance(audio_data, str) and "," in audio_data:

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

        if not st.session_state.answered:
            if transcript == w.lower():
                st.success("✔ Correct")
                st.session_state.score += 1
            else:
                st.error(f"✖ Incorrect → {w}")
                st.session_state.weak.append(w)
            st.session_state.answered = True

    if col1.button("Next"):
        st.session_state.test_i += 1
        st.session_state.answered = False
        st.rerun()

# ================= SPEECH LAB =================
elif st.session_state.mode == "speech_lab":

    st.header("🎤 Speech Lab")

    uploaded = st.file_uploader("Upload audio", type=["mp3","wav","webm"])

    if uploaded:

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(uploaded.read())
            path = tmp.name

        with open(path, "rb") as f:
            transcript = openai.audio.transcriptions.create(
                model="gpt-4o-mini-transcribe",
                file=f
            ).text

        st.subheader("Transcript")
        st.write(transcript)
