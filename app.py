import streamlit as st
import random
import requests

# ================= PAGE CONFIG =================
st.set_page_config(page_title="Pronunciation Trainer", layout="centered")

# ================= DICTIONARY API =================
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

# ================= INIT STATE =================
def init_state():
    defaults = {
        "mode": "home",
        "words": [],
        "weak_words": [],

        "study_i": 0,
        "practice_i": 0,
        "test_i": 0,

        "practice_words": [],
        "test_words": [],

        "score": 0
    }

    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ================= RESET ENGINE =================
def reset_progress():
    st.session_state.study_i = 0
    st.session_state.practice_i = 0
    st.session_state.test_i = 0
    st.session_state.score = 0
    st.session_state.practice_words = []
    st.session_state.test_words = []

# ================= SIDEBAR NAV =================
st.sidebar.title("Navigation")

if st.sidebar.button("Home"):
    st.session_state.mode = "home"

if st.sidebar.button("Study"):
    reset_progress()
    st.session_state.mode = "study"

if st.sidebar.button("Practice"):
    reset_progress()
    st.session_state.mode = "practice"

if st.sidebar.button("Test"):
    reset_progress()
    st.session_state.mode = "test"

if st.sidebar.button("Result"):
    st.session_state.mode = "result"

# ================= HOME =================
if st.session_state.mode == "home":

    st.title("Pronunciation Trainer")
    st.write("Learn commonly mispronounced English words through Study → Practice → Test.")

    st.subheader("Word Set")

    text = st.text_area("Enter words (one per line)")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Add words"):
            new_words = [w.strip() for w in text.split("\n") if w.strip()]
            st.session_state.words.extend(new_words)
            st.success("Words added")

    with col2:
        if st.button("Clear words"):
            st.session_state.words = []
            st.session_state.weak_words = []
            reset_progress()

    st.markdown("### Current words")
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
        st.write("Meaning:", definition)

        if audio:
            st.audio(audio)

        col1, col2 = st.columns(2)

        if col1.button("I know"):
            st.session_state.study_i += 1
            st.rerun()

        if col2.button("I don’t know"):
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
        st.warning("No words added")
        st.stop()

    if not st.session_state.practice_words:
        st.session_state.practice_words = words.copy()
        random.shuffle(st.session_state.practice_words)

    pw = st.session_state.practice_words

    if st.session_state.practice_i < len(pw):

        w = pw[st.session_state.practice_i]
        ipa, definition, audio = get_word_data(w)

        st.write("Listen → Type")

        if audio:
            st.audio(audio)

        ans = st.text_input("Your answer", key=f"practice_{st.session_state.practice_i}")

        if st.button("Submit"):

            if ans.strip().lower() == w.lower():
                st.success("Correct")
            else:
                st.error(f"Incorrect → {w}")
                st.session_state.weak_words.append(w)

            st.session_state.practice_i += 1
            st.rerun()

    else:
        st.success("Practice completed")

# ================= TEST =================
elif st.session_state.mode == "test":

    st.header("Test Mode")

    words = st.session_state.words

    if not words:
        st.warning("No words added")
        st.stop()

    if not st.session_state.test_words:
        st.session_state.test_words = random.sample(words, min(12, len(words)))

    tw = st.session_state.test_words

    if st.session_state.test_i < len(tw):

        w = tw[st.session_state.test_i]

        ans = st.text_input("Type word", key=f"test_{st.session_state.test_i}")

        if st.button("Submit"):

            if ans.strip().lower() == w.lower():
                st.session_state.score += 1
                st.success("Correct")
            else:
                st.error(f"Incorrect → {w}")
                st.session_state.weak_words.append(w)

            st.session_state.test_i += 1
            st.rerun()

    else:
        st.success("Test completed")

# ================= RESULT =================
elif st.session_state.mode == "result":

    st.header("Results")

    total = len(st.session_state.test_words)
    score = st.session_state.score

    percent = int((score / total) * 100) if total else 0

    if percent >= 90:
        grade = "A"
    elif percent >= 80:
        grade = "B"
    elif percent >= 70:
        grade = "C"
    elif percent >= 60:
        grade = "D"
    elif percent >= 50:
        grade = "E"
    else:
        grade = "F"

    st.subheader(f"Grade: {grade}")
    st.write(f"Score: {percent}%")
    st.write(f"{score} / {total}")

    st.markdown("### All words")
    st.write(", ".join(st.session_state.words))

    st.markdown("### Weak words")
    st.write(", ".join(set(st.session_state.weak_words)))

    if st.button("Restart everything"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()
