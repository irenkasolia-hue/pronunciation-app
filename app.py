import streamlit as st
import random

# ---------------- STATE ----------------
if "mode" not in st.session_state:
    st.session_state.mode = "home"

if "words" not in st.session_state:
    st.session_state.words = []

if "weak_words" not in st.session_state:
    st.session_state.weak_words = []

if "study_i" not in st.session_state:
    st.session_state.study_i = 0

if "practice_i" not in st.session_state:
    st.session_state.practice_i = 0

if "test_i" not in st.session_state:
    st.session_state.test_i = 0

if "test_words" not in st.session_state:
    st.session_state.test_words = []

if "score" not in st.session_state:
    st.session_state.score = 0

# ---------------- HOME ----------------
if st.session_state.mode == "home":

    st.title("🧠 Pronunciation Trainer")

    text = st.text_area("Enter words (one per line)")

    if st.button("Start"):
        st.session_state.words = [w.strip() for w in text.split("\n") if w.strip()]
        st.session_state.mode = "study"

    st.stop()

# ---------------- STUDY ----------------
if st.session_state.mode == "study":

    st.header("📘 STUDY MODE")

    words = st.session_state.words

    if st.session_state.study_i < len(words):

        w = words[st.session_state.study_i]

        st.subheader(w)

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

        if st.button("Go to Practice"):
            st.session_state.mode = "practice"
            st.rerun()

    st.stop()

# ---------------- PRACTICE ----------------
if st.session_state.mode == "practice":

    st.header("🎧 PRACTICE MODE")

    if st.session_state.practice_i == 0:
        st.session_state.practice_words = st.session_state.words.copy()
        random.shuffle(st.session_state.practice_words)

    words = st.session_state.practice_words

    if st.session_state.practice_i < len(words):

        w = words[st.session_state.practice_i]

        st.write("Listen → Type")

        ans = st.text_input("Your answer")

        if st.button("Submit"):
            if ans.strip().lower() == w.lower():
                st.success("✔ Correct")
            else:
                st.error(f"✖ Correct: {w}")
                st.session_state.weak_words.append(w)

            st.session_state.practice_i += 1
            st.rerun()

    else:
        st.success("Practice completed")

        if st.button("Go to Test"):
            st.session_state.mode = "test"
            st.rerun()

    st.stop()

# ---------------- TEST ----------------
if st.session_state.mode == "test":

    st.header("🟥 TEST MODE")

    if st.session_state.test_i == 0:
        st.session_state.test_words = random.sample(
            st.session_state.words,
            min(12, len(st.session_state.words))
        )

    words = st.session_state.test_words

    if st.session_state.test_i < len(words):

        w = words[st.session_state.test_i]

        ans = st.text_input("Type word")

        if st.button("Submit"):
            if ans.strip().lower() == w.lower():
                st.session_state.score += 1
            else:
                st.session_state.weak_words.append(w)

            st.session_state.test_i += 1
            st.rerun()

    else:
        st.session_state.mode = "result"
        st.rerun()

    st.stop()

# ---------------- RESULT ----------------
if st.session_state.mode == "result":

    st.header("📊 RESULT")

    total = len(st.session_state.test_words)
    score = st.session_state.score

    percent = int((score / total) * 100) if total > 0 else 0

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

    st.markdown("### 📚 All words")
    st.write(", ".join(st.session_state.words))

    st.markdown("### 🧠 Weak words")
    st.write(", ".join(set(st.session_state.weak_words)))

    if st.button("Restart"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()

# ---------------- TEACHER ----------------
if st.sidebar.button("👩‍🏫 Teacher view"):

    st.session_state.mode = "teacher"
    st.rerun()

if st.session_state.mode == "teacher":

    st.header("👩‍🏫 Teacher Dashboard")

    st.write("Total words:", len(st.session_state.words))
    st.write("Weak words:", len(set(st.session_state.weak_words)))

    st.subheader("Weak Words")
    st.write(", ".join(set(st.session_state.weak_words)))

    if st.button("Back"):
        st.session_state.mode = "home"
        st.rerun()
