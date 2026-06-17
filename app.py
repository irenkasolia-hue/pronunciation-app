import streamlit as st
import random
import requests
import tempfile
import base64
import openai

st.set_page_config(page_title="Pronunciation Trainer", layout="centered")

# ================= WORD DATA =================
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
        return "N/A", "No definition found", ""

# ================= STATE =================
def init(k, v):
    if k not in st.session_state:
        st.session_state[k] = v

init("mode", "home")
init("words", [])
init("weak", [])

init("study_i", 0)

init("practice_words", [])
init("practice_i", 0)

init("test_words", [])
init("test_i", 0)
init("score", 0)

init("mic_audio", None)

# ================= NAV =================
st.sidebar.title("Navigation")

if st.sidebar.button("Home"):
    st.session_state.mode = "home"

if st.sidebar.button("Study"):
    st.session_state.mode = "study"

if st.sidebar.button("Practice"):
    st.session_state.mode = "practice"
    st.session_state.practice_words = random.sample(st.session_state.words, len(st.session_state.words)) if st.session_state.words else []

if st.sidebar.button("Test"):
    st.session_state.mode = "test"
    st.session_state.test_words = random.sample(st.session_state.words, min(10, len(st.session_state.words)))
    st.session_state.test_i = 0
    st.session_state.score = 0

if st.sidebar.button("Speech Lab"):
    st.session_state.mode = "speech_lab"

# ================= HOME =================
if st.session_state.mode == "home":

    st.title("🧠 Pronunciation Trainer")

    text = st.text_area("Enter words (one per line)")

    if st.button("Add words"):
        new_words = [w.strip() for w in text.split("\n") if w.strip()]
        st.session_state.words += new_words

    st.write("📦 Word bank:")

    for w in st.session_state.words:
        col1, col2 = st.columns([4,1])
        col1.write(w)

        if col2.button("❌", key=f"del_{w}"):
            st.session_state.words.remove(w)
            st.rerun()

# ================= STUDY =================
elif st.session_state.mode == "study":

    st.header("📚 Study")

    words = st.session_state.words

    if not words:
        st.warning("No words")
        st.stop()

    w = words[st.session_state.study_i]

    ipa, definition, audio = get_word_data(w)

    st.subheader(w)
    st.write("IPA:", ipa)
    st.info(definition)

    if audio:
        st.audio(audio)

    col1, col2, col3 = st.columns(3)

    if col1.button("⬅"):
        st.session_state.study_i = max(0, st.session_state.study_i - 1)
        st.rerun()

    if col2.button("➡"):
        st.session_state.study_i = min(len(words)-1, st.session_state.study_i + 1)
        st.rerun()

    if col3.button("✔ I know"):
        st.session_state.study_i = min(len(words)-1, st.session_state.study_i + 1)
        st.rerun()

# ================= PRACTICE =================
elif st.session_state.mode == "practice":

    st.header("🎧 Practice (2 modes)")

    words = st.session_state.practice_words
    if not words:
        st.warning("Go to Home first")
        st.stop()

    w = st.session_state.practice_words[st.session_state.practice_i]

    mode = st.radio("Task type", ["Listen → Type", "See → Speak"])

    ipa, definition, audio = get_word_data(w)

    if mode == "Listen → Type":

        if audio:
            st.audio(audio)

        ans = st.text_input("Type word")

        if st.button("Submit"):
            if ans.lower().strip() == w.lower():
                st.success("Correct")
            else:
                st.error(f"Wrong → {w}")
                st.session_state.weak.append(w)

            st.session_state.practice_i += 1
            st.rerun()

    else:

        st.subheader(w)

        spoken = st.text_input("What did you say?")

        if st.button("Submit"):
            if spoken.lower().strip() == w.lower():
                st.success("Correct")
            else:
                st.error(f"Wrong pronunciation → {w}")
                st.session_state.weak.append(w)

            st.session_state.practice_i += 1
            st.rerun()

# ================= TEST (FIXED 10 WORDS + 2 TASK TYPES) =================
elif st.session_state.mode == "test":

    st.header("🟥 Test (10 words)")

    words = st.session_state.test_words

    if not words:
        st.warning("No test words")
        st.stop()

    if st.session_state.test_i >= len(words):
        st.success(f"Finished! Score: {st.session_state.score}/{len(words)}")
        st.stop()

    w = words[st.session_state.test_i]

    task = st.radio("Task", ["Listen → Type", "See → Speak"])

    ipa, definition, audio = get_word_data(w)

    if task == "Listen → Type":

        if audio:
            st.audio(audio)

        ans = st.text_input("Type word")

        if st.button("Submit"):
            if ans.lower().strip() == w.lower():
                st.session_state.score += 1
                st.success("Correct")
            else:
                st.error(f"Wrong → {w}")
                st.session_state.weak.append(w)

            st.session_state.test_i += 1
            st.rerun()

    else:

        st.subheader("Say the word")

        spoken = st.text_input("What did you say?")

        if st.button("Submit"):
            if spoken.lower().strip() == w.lower():
                st.session_state.score += 1
                st.success("Correct")
            else:
                st.error(f"Wrong pronunciation → {w}")
                st.session_state.weak.append(w)

            st.session_state.test_i += 1
            st.rerun()

# ================= SPEECH LAB =================
elif st.session_state.mode == "speech_lab":

    st.header("🎤 Speech Lab")

    uploaded = st.file_uploader("Upload audio", type=["mp3","wav","webm"])

    audio_source = None

    if st.session_state.mic_audio:
        audio_source = ("mic", st.session_state.mic_audio)

    elif uploaded:
        audio_source = ("upload", uploaded)

    transcript = ""

    if audio_source:

        if audio_source[0] == "upload":

            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                tmp.write(audio_source[1].read())
                path = tmp.name

        else:

            audio_b64 = audio_source[1].split(",")[1]
            audio_bytes = base64.b64decode(audio_b64)

            with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
                tmp.write(audio_bytes)
                path = tmp.name

        with open(path, "rb") as f:
            transcript = openai.audio.transcriptions.create(
                model="gpt-4o-mini-transcribe",
                file=f
            ).text

        st.subheader("Transcript")
        st.write(transcript)

        st.session_state.mic_audio = None

    def highlight(text, targets):
        t = set(targets)
        out = []

        for w in text.split():
            c = w.strip(".,!?;:").lower()
            if c in t:
                out.append(f"🟢 {w}")
            else:
                out.append(f"⚪ {w}")

        return " ".join(out)

    if st.button("Analyze"):

        if not transcript:
            st.warning("No speech detected")
            st.stop()

        st.markdown("### Highlighted")
        st.write(highlight(transcript, st.session_state.words))

        spoken = set([w.strip(".,!?;:").lower() for w in transcript.split()])
        targets = set(st.session_state.words)

        missing = targets - spoken

        st.markdown("### Missing words")

        if missing:
            st.error(", ".join(missing))
        else:
            st.success("Perfect coverage 🎉")
