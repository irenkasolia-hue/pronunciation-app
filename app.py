import streamlit as st
import random
import requests
import tempfile
import base64
import openai
from streamlit.components.v1 import html as components_html

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

    st.title("🎧 Pronunciation Trainer")

    text = st.text_area("Enter words (one per line)")

    if st.button("Add words"):
        new_words = [w.strip() for w in text.split("\n") if w.strip()]
        st.session_state.words += new_words

    st.write("📦 Word bank:")

    for w in list(st.session_state.words):
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

    # "I don't know" button to mark weak words and advance
    if col3.button("✖ I don't know"):
        if w not in st.session_state.weak:
            st.session_state.weak.append(w)
        st.session_state.study_i = min(len(words)-1, st.session_state.study_i + 1)
        st.rerun()

# ================= PRACTICE =================
elif st.session_state.mode == "practice":

    st.header("🎧 Practice (Listen→Type / Speak→Auto)")

    words = st.session_state.practice_words
    if not words:
        st.warning("Go to Home first")
        st.stop()

    # wrap index to avoid crash
    if st.session_state.practice_i >= len(words):
        st.success("Practice complete")
        st.stop()

    w = st.session_state.practice_words[st.session_state.practice_i]

    mode = st.radio("Task type", ["Listen → Type", "Speak → Auto (free)"])

    ipa, definition, audio = get_word_data(w)

    if mode == "Listen → Type":

        if audio:
            st.audio(audio)

        ans_key = f"practice_input_{st.session_state.practice_i}"
        ans = st.text_input("Type word", key=ans_key)

        col1, col2, col3 = st.columns(3)

        if col1.button("Submit", key=f"submit_pr_{st.session_state.practice_i}"):
            if ans.lower().strip() == w.lower():
                st.success("✔ Correct")
            else:
                st.error(f"✖ Wrong — correct: {w}")
                if w not in st.session_state.weak:
                    st.session_state.weak.append(w)

            st.session_state.practice_i += 1
            st.rerun()

        if col2.button("🔊 Replay", key=f"replay_pr_{st.session_state.practice_i}"):
            if audio:
                st.audio(audio)

        if col3.button("⏭ Skip", key=f"skip_pr_{st.session_state.practice_i}"):
            st.session_state.practice_i += 1
            st.rerun()

    else:
        st.subheader(f"Speak now: {w}")
        st.markdown("_This uses your browser's free speech recognition (Chrome/Edge recommended)._")

        # components.html will return the transcript (if browser supports postMessage)
        js = f"""
        <div>
          <button id="start">🎙 Start</button>
          <button id="retry" style="margin-left:8px;">🔁 Retry</button>
          <p id="status">Press Start and speak the word once.</p>
        </div>
        <script>
        const startBtn = document.getElementById('start');
        const retryBtn = document.getElementById('retry');
        const status = document.getElementById('status');
        function send(value) {{
            // post message back to Streamlit
            window.parent.postMessage({{isStreamlitMessage: true, value: value}}, '*');
        }}
        function startRec() {{
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            if(!SpeechRecognition){{
                status.innerText = 'SpeechRecognition not supported in this browser.';
                send('');
                return;
            }}
            const recognition = new SpeechRecognition();
            recognition.lang = 'en-US';
            recognition.interimResults = false;
            recognition.maxAlternatives = 1;
            status.innerText = 'Listening...';
            recognition.onresult = function(event) {{
                const t = event.results[0][0].transcript;
                status.innerText = 'Heard: ' + t;
                send(t);
            }};
            recognition.onerror = function(e) {{
                status.innerText = 'Error: ' + e.error;
                send('');
            }};
            recognition.onend = function() {{
                // do nothing
            }};
            recognition.start();
        }}
        startBtn.onclick = startRec;
        retryBtn.onclick = startRec;
        </script>
        """

        transcript = components_html(js, height=160)

        # transcript will be None until the iframe posts a message; show instructions
        if transcript is None:
            st.info("Click Start and speak. After speaking, wait a moment for the result to appear below.")
        else:
            st.subheader("Detected:")
            st.write(transcript)

            # allow manual correction before submit
            corr = st.text_input("If needed, edit the detected text", value=transcript)

            col1, col2 = st.columns([1,1])
            if col1.button("Submit pronunciation", key=f"submit_speak_pr_{st.session_state.practice_i}"):
                if corr.lower().strip() == w.lower():
                    st.success("✔ Correct pronunciation")
                else:
                    st.error(f"✖ Check pronunciation — expected: {w}")
                    if w not in st.session_state.weak:
                        st.session_state.weak.append(w)

                st.session_state.practice_i += 1
                st.rerun()

            if col2.button("Retry", key=f"retry_speak_pr_{st.session_state.practice_i}"):
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

    task = st.radio("Task", ["Listen → Type", "Speak → Auto (free)"])

    ipa, definition, audio = get_word_data(w)

    if task == "Listen → Type":

        if audio:
            st.audio(audio)

        ans_key = f"test_input_{st.session_state.test_i}"
        ans = st.text_input("Type word", key=ans_key)

        if st.button("Submit", key=f"submit_test_lt_{st.session_state.test_i}"):
            if ans.lower().strip() == w.lower():
                st.session_state.score += 1
                st.success("✔ Correct")
            else:
                st.error(f"✖ Wrong — correct: {w}")
                if w not in st.session_state.weak:
                    st.session_state.weak.append(w)

            st.session_state.test_i += 1
            st.rerun()

    else:
        st.subheader(f"Speak now: {w}")
        st.markdown("_This uses your browser's free speech recognition (Chrome/Edge recommended)._")

        js2 = f"""
        <div>
          <button id="start2">🎙 Start</button>
          <button id="retry2" style="margin-left:8px;">🔁 Retry</button>
          <p id="status2">Press Start and speak the word once.</p>
        </div>
        <script>
        const startBtn2 = document.getElementById('start2');
        const retryBtn2 = document.getElementById('retry2');
        const status2 = document.getElementById('status2');
        function send2(value) {{
            window.parent.postMessage({{isStreamlitMessage: true, value: value}}, '*');
        }}
        function startRec2() {{
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            if(!SpeechRecognition){{
                status2.innerText = 'SpeechRecognition not supported in this browser.';
                send2('');
                return;
            }}
            const recognition = new SpeechRecognition();
            recognition.lang = 'en-US';
            recognition.interimResults = false;
            recognition.maxAlternatives = 1;
            status2.innerText = 'Listening...';
            recognition.onresult = function(event) {{
                const t = event.results[0][0].transcript;
                status2.innerText = 'Heard: ' + t;
                send2(t);
            }};
            recognition.onerror = function(e) {{
                status2.innerText = 'Error: ' + e.error;
                send2('');
            }};
            recognition.start();
        }}
        startBtn2.onclick = startRec2;
        retryBtn2.onclick = startRec2;
        </script>
        """

        transcript2 = components_html(js2, height=160)

        if transcript2 is None:
            st.info("Click Start and speak. After speaking, wait a moment for the result to appear below.")
        else:
            st.subheader("Detected:")
            st.write(transcript2)

            corr2 = st.text_input("If needed, edit the detected text", value=transcript2)

            col1, col2 = st.columns([1,1])
            if col1.button("Submit", key=f"submit_test_sp_{st.session_state.test_i}"):
                if corr2.lower().strip() == w.lower():
                    st.session_state.score += 1
                    st.success("✔ Correct")
                else:
                    st.error(f"✖ Wrong pronunciation — expected: {w}")
                    if w not in st.session_state.weak:
                        st.session_state.weak.append(w)

                st.session_state.test_i += 1
                st.rerun()

            if col2.button("Retry", key=f"retry_test_sp_{st.session_state.test_i}"):
                st.rerun()

# ================= FALLBACK / END =================
else:
    st.write("Mode not implemented")
