import streamlit as st
import openai
import json
import os
from audio_recorder_streamlit import audio_recorder

# ---------------- CONFIG ----------------
openai.api_key = st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY"))

WORDS = [
    "psalm","admirable","infamous","receipt","recipe","coup","ballet","debut",
    "flour","ingenuity","indigenous","itinerary","suite","aisle","bouquet",
    "psychic","psychology","photograph","photography","economy","economic",
    "entrepreneur","queue","choir","colonel","sword","drawer","forehead",
    "salmon","genre","hierarchy","hyperbole","hypothesis","ubiquitous","yacht"
]

DATA_FILE = "data.json"

# ---------------- STORAGE ----------------
def load_data():
    if os.path.exists(DATA_FILE):
        return json.load(open(DATA_FILE))
    return []

def save_data(data):
    json.dump(data, open(DATA_FILE, "w"), indent=2)

data = load_data()

# ---------------- AI ----------------
def transcribe(audio_bytes):
    with open("temp.wav", "wb") as f:
        f.write(audio_bytes)

    with open("temp.wav", "rb") as f:
        result = openai.audio.transcriptions.create(
            model="gpt-4o-mini-transcribe",
            file=f
        )
    return result.text


def analyze(word, transcript, prev=None):
    prompt = f"""
You are a pronunciation coach.

Target word: {word}
Student speech: {transcript}

Previous attempt: {prev if prev else "none"}

Provide:
1. Score (1–5)
2. Main pronunciation error
3. Key problematic sound (/θ/, /ʒ/, /ə/, /tʃ/, /dʒ/)
4. Correct pronunciation explanation
5. One micro-drill
6. If second attempt: compare improvement
"""

    res = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return res.choices[0].message.content

# ---------------- UI ----------------
st.title("🎤 AI Pronunciation Trainer (Live Mic)")

word = st.selectbox("Choose word", WORDS)
attempt = st.radio("Attempt", [1, 2])

st.write("Press record and speak 👇")

audio = audio_recorder()

if audio:
    st.audio(audio, format="audio/wav")

    if st.button("Analyze pronunciation"):
        transcript = transcribe(audio)

        st.subheader("Transcript")
        st.write(transcript)

        prev = None
        if attempt == 2:
            for d in reversed(data):
                if d["word"] == word:
                    prev = d["transcript"]
                    break

        feedback = analyze(word, transcript, prev)

        st.subheader("AI Feedback")
        st.write(feedback)

        data.append({
            "word": word,
            "attempt": attempt,
            "transcript": transcript,
            "feedback": feedback
        })

        save_data(data)

# ---------------- PROGRESS ----------------
st.sidebar.header("Progress")

if data:
    st.sidebar.write(f"Attempts: {len(data)}")
    st.sidebar.write(f"Words practiced: {len(set(d['word'] for d in data))}")
