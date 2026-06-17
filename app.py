import streamlit as st
import random
import requests
import tempfile
import base64
import openai

st.set_page_config(page_title="Pronunciation Trainer", layout="centered")

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
        return "N/A", "No definition found", ""

# ================= STATE =================
def init(k, v):
    if k not in st.session_state:
        st.session_state[k] = v

init("mode", "home")
init("words", [])
init("weak", [])

init("study_i", 0)

init("practice_i", 0)
init("practice_words", [])

init("test_i", 0)
init("test_words", [])
init("score", 0)

init("mic_audio", None)

# ================= RESET HELP =================
def reset_practice():
    st.session_state.practice_i = 0
    st.session_state.practice_words = []

def reset_test():
    st.session_state.test_i = 0
    st.session_state.test_words = []
    st.session_state.score = 0

# ================= NAVIGATION =================
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

if st.sidebar.button("Result"):
    st.session_state.mode = "result"

# ================= HOME =================
if st.session_state.mode == "home":

    st.title("🧠 Pronunciation Trainer")

    text = st.text_area("Enter words (one per line)")

    if st.button("Add words"):
        new_words = [w.strip() for w in text.split("\n") if w.strip()]
        st.session_state.words.extend(new_words)

    st.write("Current words:")
    st.write(st.session_state.words)

# ================= STUDY =================
elif st.session_state.mode == "study":

    st.header("📚 Study Mode")

    words = st.session_state.words

    if not words:
        st.warning("No words added")
        st.stop()

    col1, col2 = st.columns(2)

    if col1.button("⬅ Prev"):
        st.session_state.study_i = max(0, st.session_state.study_i - 1)

    if col2.button("Next ➡"):
        st.session_state.study_i = min(len(words) - 1, st.session_state.study_i + 1)

    w = words[st.session_state.study_i]

    ipa, definition, audio = get_word_data(w)

    st.subheader(w)
    st.write("IPA:", ipa)

    if audio:
        st.audio(audio)

    st.info(definition)

    st.write(f"Card {st.session_state.study_i + 1} / {len(words)}")

# ================= PRACTICE =================
elif st.session_state.mode == "practice":

    st.header("🎧 Practice Mode")

    words = st.session_state.words

    if not words:
        st.warning("No words")
        st.stop()

    if not st.session_state.practice_words:
        st.session_state.practice_words = words.copy()
        random.shuffle(st.session_state.practice_words)

    w = st.session_state.practice_words[st.session_state.practice_i]

    ipa, definition, audio = get_word_data(w)

    mode = st.radio("Mode", ["Listen → Type", "See → Speak"])

    st.write(f"Word #{st.session_state.practice_i + 1}")

    # ================= LISTEN =================
    if mode == "Listen → Type":

        if audio:
            st.audio(audio)

        ans = st.text_input("Type word")

        col1, col2, col3 = st.columns(3)

        if col1.button("Submit"):
            if ans.lower().strip() == w.lower():
                st.success("Correct")
            else:
                st.error(f"Correct answer: {w}")
                st.session_state.weak.append(w)

            st.session_state.practice_i += 1
            st.rerun()

        if col2.button("🔊 Replay"):
            if audio:
                st.audio(audio)

        if col3.button("⏭ Skip"):
            st.session_state.practice_i += 1
            st.rerun()

    # ================= SPEAK =================
    else:

        st.write("Say:", w)

        spoken = st.text_input("What did you say?")

        col1, col2 = st.columns(2)

        if col1.button("Submit"):
            if spoken.lower().strip() == w.lower():
                st.success("Correct pronunciation")
            else:
                st.error(f"Check word: {w}")
                st.session_state.weak.append(w)

            st.session_state.practice_i += 1
            st.rerun()

        if col2.button("🔁 Try again"):
            st.rerun()

# ================= TEST =================
elif st.session_state.mode == "test":

    st.header("🟥 Test Mode")

    words = st.session_state.words

    if not words:
        st.warning("No words")
        st.stop()

    if not st.session_state.test_words:
        st.session_state.test_words = random.sample(words, min(10, len(words)))

    w = st.session_state.test_words[st.session_state.test_i]

    ans = st.text_input("Type word")

    if st.button("Submit"):

        if ans.lower().strip() == w.lower():
            st.session_state.score += 1
            st.success("Correct")
        else:
            st.error(f"Wrong: {w}")
            st.session_state.weak.append(w)

        st.session_state.test_i += 1
        st.rerun()

# ================= RESULT =================
elif st.session_state.mode == "result":

    st.header("📊 Results")

    total = len(st.session_state.test_words)
    score = st.session_state.score

    percent = int((score / total) * 100) if total else 0

    grade = "A" if percent >= 90 else "B" if percent >= 80 else "C" if percent >= 70 else "D" if percent >= 60 else "E" if percent >= 50 else "F"

    st.subheader(f"Grade: {grade}")
    st.write(f"{percent}% ({score}/{total})")

    st.markdown("### Weak words")
    st.write(set(st.session_state.weak))

# ================= SPEECH LAB =================
elif st.session_state.mode == "speech_lab":

    st.header("🎤 Speech Lab")

    st.write("Record or upload audio for pronunciation analysis")

    uploaded_audio = st.file_uploader("Upload audio (mp3/wav/webm)", type=["mp3", "wav", "webm"])

    audio_source = None

    if st.session_state.mic_audio:
        audio_source = ("mic", st.session_state.mic_audio)

    elif uploaded_audio:
        audio_source = ("upload", uploaded_audio)

    transcript = ""

    # ================= TRANSCRIPTION =================
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

    # ================= ANALYSIS =================
    def highlight(text, targets):
        words = text.split()
        t = set(targets)

        out = []
        for w in words:
            clean = w.strip(".,!?;:").lower()

            if clean in t:
                out.append(f"🟢 {w}")
            else:
                out.append(f"⚪ {w}")

        return " ".join(out)

    if st.button("Analyze speech"):

        if not transcript:
            st.warning("No speech detected")
            st.stop()

        st.markdown("### Highlighted transcript")
        st.write(highlight(transcript, st.session_state.words))

        spoken = set([w.strip(".,!?;:").lower() for w in transcript.split()])
        targets = set(st.session_state.words)

        missing = targets - spoken

        st.markdown("### Missing / mispronounced words")

        if missing:
            st.error(", ".join(missing))
        else:
            st.success("All target words detected 🎉")
