import streamlit as st
import random
import requests
import tempfile
from openai import OpenAI

client = OpenAI()

st.set_page_config(page_title="Pronunciation Trainer", layout="centered")

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

init("answered", False)

# ================= WORD API =================
def get_word_data(word):
    try:
        url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
        r = requests.get(url).json()

        ipa = r[0].get("phonetic", "N/A")
        definition = r[0]["meanings"][0]["definitions"][0]["definition"]

        audio = ""
        for p in r[0].get("phonetics", []):
            if p.get("audio"):
                audio = p["audio"]
                break

        return ipa, definition, audio
    except:
        return "N/A", "No definition", ""

# ================= NAV =================
st.sidebar.title("Menu")

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

# ================= HOME =================
if st.session_state.mode == "home":

    st.title("🧠 Pronunciation Trainer")

    text = st.text_area("Enter words")

    if st.button("Add"):
        st.session_state.words += [w.strip() for w in text.split("\n") if w.strip()]

    st.write(st.session_state.words)

# ================= STUDY =================
elif st.session_state.mode == "study":

    st.header("📚 Study")

    if not st.session_state.words:
        st.warning("No words")
        st.stop()

    w = st.session_state.words[st.session_state.study_i % len(st.session_state.words)]

    ipa, definition, audio = get_word_data(w)

    st.subheader(w)
    st.write(ipa)
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

# ================= PRACTICE (SAFE MIC VERSION) =================
elif st.session_state.mode == "practice":

    st.header("🎧 Practice (SAFE MODE)")

    if not st.session_state.practice_words:
        st.session_state.practice_words = st.session_state.words.copy()

    words = st.session_state.practice_words
    if not words:
        st.stop()

    w = words[st.session_state.practice_i % len(words)]

    st.subheader(f"Say: {w}")

    audio = st.audio_input("🎤 Record your pronunciation")

    if audio and not st.session_state.answered:

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(audio.read())
            path = tmp.name

        with open(path, "rb") as f:
            result = client.audio.transcriptions.create(
                model="gpt-4o-mini-transcribe",
                file=f
            )

        text = result.text.lower().strip()

        st.write("You said:", text)

        if text == w.lower():
            st.success("✔ Correct")
        else:
            st.error(f"✖ Wrong → {w}")
            st.session_state.weak.append(w)

        st.session_state.answered = True

    if st.button("Next"):
        st.session_state.practice_i += 1
        st.session_state.answered = False
        st.rerun()

# ================= TEST =================
elif st.session_state.mode == "test":

    st.header("🟥 Test")

    words = st.session_state.test_words

    if st.session_state.test_i >= len(words):
        st.success(f"Score: {st.session_state.score}/{len(words)}")
        st.stop()

    w = words[st.session_state.test_i]

    st.subheader(f"Q{st.session_state.test_i+1}/{len(words)}")
    st.write(f"Say: {w}")

    audio = st.audio_input("🎤 Speak")

    if audio and not st.session_state.answered:

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(audio.read())
            path = tmp.name

        with open(path, "rb") as f:
            result = client.audio.transcriptions.create(
                model="gpt-4o-mini-transcribe",
                file=f
            )

        text = result.text.lower().strip()

        st.write("You said:", text)

        if text == w.lower():
            st.success("✔ Correct")
            st.session_state.score += 1
        else:
            st.error(f"✖ Wrong → {w}")

        st.session_state.answered = True

    if st.button("Next"):
        st.session_state.test_i += 1
        st.session_state.answered = False
        st.rerun()
