import streamlit as st
import random
import requests
import tempfile
import openai

# ================= PAGE =================
st.set_page_config(page_title="Pronunciation Trainer", layout="centered")

# ================= API =================
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

# ================= STATE INIT =================
def init(key, value):
    if key not in st.session_state:
        st.session_state[key] = value

init("mode", "home")
init("words", [])
init("weak_words", [])

init("study_i", 0)
init("practice_i", 0)
init("test_i", 0)

init("practice_words", [])
init("test_words", [])
init("score", 0)

# ================= RESET =================
def reset_all():
    st.session_state.study_i = 0
    st.session_state.practice_i = 0
    st.session_state.test_i = 0
    st.session_state.score = 0
    st.session_state.practice_words = []
    st.session_state.test_words = []

# ================= NAV =================
st.sidebar.title("Navigation")

if st.sidebar.button("Home"):
    st.session_state.mode = "home"

if st.sidebar.button("Study"):
    reset_all()
    st.session_state.mode = "study"

if st.sidebar.button("Practice"):
    reset_all()
    st.session_state.mode = "practice"

if st.sidebar.button("Test"):
    reset_all()
    st.session_state.mode = "test"

if st.sidebar.button("Speech Lab"):
    st.session_state.mode = "speech_lab"

if st.sidebar.button("Result"):
    st.session_state.mode = "result"

# ================= HOME =================
if st.session_state.mode == "home":

    st.title("Pronunciation Trainer")

    st.write("Enter commonly mispronounced words (one per line).")

    text = st.text_area("Words")

    if st.button("Add words"):
        new_words = [w.strip() for w in text.split("\n") if w.strip()]
        st.session_state.words.extend(new_words)
        st.success("Words added")

    st.write("Current words:")
    st.write(", ".join(st.session_state.words))

# ================= STUDY =================
elif st.session_state.mode == "study":

    st.header("Study Mode")

    words = st.session_state.words

    if not words:
        st.warning("No words added")
        st.stop()

    if st.session_state.study_i < len(words):

        w = words[st.session_state.study_i]
        ipa, definition, audio = get_word_data(w)

        st.subheader(w)
        st.write("IPA:", ipa)

        if st.button("Show meaning"):
            st.info(definition)

        if audio:
            st.audio(audio)

        col1, col2 = st.columns(2)

        if col1.button("✔ I know"):
            st.session_state.study_i += 1
            st.rerun()

        if col2.button("✖ I don’t know"):
            st.session_state.weak_words.append(w)
            st.session_state.study_i += 1
            st.rerun()

    else:
        st.success("Study completed")

# ================= PRACTICE =================
elif st.session_state.mode == "practice":

    st.header("Practice Mode")

    words = st.session_state.words

    if not words:
        st.warning("No words")
        st.stop()

    if not st.session_state.practice_words:
        st.session_state.practice_words = words.copy()
        random.shuffle(st.session_state.practice_words)

    pw = st.session_state.practice_words
    w = pw[st.session_state.practice_i]

    ipa, definition, audio = get_word_data(w)

    st.markdown("### 🎧 Listen → Type")

    if audio:
        st.audio(audio)

    ans = st.text_input("Type word", key=f"p{st.session_state.practice_i}")

    if st.button("Submit typing"):
        if ans.strip().lower() == w.lower():
            st.success("Correct")
        else:
            st.error(f"Wrong → {w}")
            st.session_state.weak_words.append(w)

        st.session_state.practice_i += 1
        st.rerun()

    st.markdown("---")

    st.markdown("### 🎤 See → Speak")

    st.write(f"Say: **{w}**")

    spoken = st.text_input("What did you say?", key=f"s{st.session_state.practice_i}")

    if st.button("Submit speaking"):
        if spoken.strip().lower() == w.lower():
            st.success("Correct pronunciation")
        else:
            st.error(f"Check pronunciation → {w}")
            st.session_state.weak_words.append(w)

        st.session_state.practice_i += 1
        st.rerun()

# ================= TEST =================
elif st.session_state.mode == "test":

    st.header("Test Mode")

    words = st.session_state.words

    if not words:
        st.warning("No words")
        st.stop()

    if not st.session_state.test_words:
        st.session_state.test_words = random.sample(words, min(12, len(words)))

    tw = st.session_state.test_words

    w = tw[st.session_state.test_i]

    ans = st.text_input("Type word", key=f"t{st.session_state.test_i}")

    if st.button("Submit"):
        if ans.strip().lower() == w.lower():
            st.session_state.score += 1
            st.success("Correct")
        else:
            st.error(f"Wrong → {w}")
            st.session_state.weak_words.append(w)

        st.session_state.test_i += 1
        st.rerun()

# ================= RESULT =================
elif st.session_state.mode == "result":

    st.header("Results")

    total = len(st.session_state.test_words)
    score = st.session_state.score

    percent = int((score / total) * 100) if total else 0

    grade = "A" if percent >= 90 else "B" if percent >= 80 else "C" if percent >= 70 else "D" if percent >= 60 else "E" if percent >= 50 else "F"

    st.subheader(f"Grade: {grade}")
    st.write(f"{percent}% ({score}/{total})")

    st.markdown("### Weak words")
    st.write(", ".join(set(st.session_state.weak_words)))

# ================= SPEECH LAB =================
elif st.session_state.mode == "speech_lab":

    st.header("🎤 Speech Lab")

    st.write("Upload speech or paste transcript for analysis.")

    audio_file = st.file_uploader("Upload audio (mp3/wav)", type=["mp3", "wav"])
    text_input = st.text_area("OR paste text")

    transcript = ""

    if audio_file:

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(audio_file.read())
            path = tmp.name

        with open(path, "rb") as f:
            transcript = openai.audio.transcriptions.create(
                model="gpt-4o-mini-transcribe",
                file=f
            ).text

        st.subheader("Transcript")
        st.write(transcript)

    elif text_input:
        transcript = text_input

    if st.button("Analyze speech"):

        if not transcript:
            st.warning("No input")
            st.stop()

        spoken_words = [w.strip(".,!?;:").lower() for w in transcript.split()]
        target_words = set(st.session_state.words)

        found = [w for w in spoken_words if w in target_words]
        missing = [w for w in target_words if w not in spoken_words]

        st.markdown("### Detected target words")
        st.write(", ".join(found) if found else "None")

        st.markdown("### Words to review")
        st.write(", ".join(missing) if missing else "None")

        if missing:
            st.error("Likely mispronounced or skipped: " + ", ".join(missing))
        else:
            st.success("Good pronunciation coverage")
