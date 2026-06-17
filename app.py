import streamlit as st
import openai
import json
import os

# ---------------- CONFIG ----------------
openai.api_key = st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY"))

WORDS = [
    "psalm","admirable","infamous","receipt","recipe","coup","ballet","debut",
    "flour","ingenuity","indigenous","itinerary","sour","suite","hotel","aisle",
    "bouquet","psychic","psychiatry","photograph","photography","photographer",
    "economy","economic","economical","politics","political","reservoir",
    "champagne","café","croissant","hiccough","sword","drawer","forehead",
    "plough","salmon","picturesque","extremity","miraculous","advantageous",
    "fiance","fiancee","exemplary","explanatory","diversity","albeit","anomaly",
    "apostrophe","arbitrary","archive","catastrophe","chaos","choir","colonel",
    "debris","discourse","eloquent","entrepreneur","façade","genre","hierarchy",
    "hyperbole","hypothesis","inherent","liaison","luxury","luxurious",
    "meticulous","miscellaneous","mischievous","niche","paradigm","pneumatic",
    "pseudonym","questionnaire","queue","synthesis","trajectory","ubiquitous",
    "yacht","vehement","prerequisite","repertoire","surrogate","gauge",
    "chronology","pedagogy","rhetoric"
]

# ---------------- AI ----------------
def analyze(word, text):
    prompt = f"""
You are a pronunciation coach.

Word: {word}
Student attempt transcription: {text}

Provide:
1. Score (1-5)
2. Main pronunciation issue
3. Key problematic sound (if any: /θ/ /ʒ/ /ə/ /tʃ/ /dʒ/)
4. Correct pronunciation explanation
5. One micro-drill
"""

    res = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content":prompt}]
    )

    return res.choices[0].message.content

def transcribe(file):
    t = openai.audio.transcriptions.create(
        model="gpt-4o-mini-transcribe",
        file=file
    )
    return t.text

# ---------------- UI ----------------
st.title("🧪 Pronunciation AI Checker")

word = st.selectbox("Choose word", WORDS)
attempt = st.radio("Attempt", [1,2])

audio = st.file_uploader("Upload audio", type=["mp3","wav","m4a"])

if audio:
    st.audio(audio)

    st.info("Transcribing...")

    transcript = transcribe(audio)
    st.write("Transcript:", transcript)

    if st.button("Get AI feedback"):
        feedback = analyze(word, transcript)
        st.subheader("Feedback")
        st.write(feedback)

        # save locally (simple)
        data = []
        if os.path.exists("data.json"):
            data = json.load(open("data.json"))

        data.append({
            "word": word,
            "attempt": attempt,
            "transcript": transcript,
            "feedback": feedback
        })

        json.dump(data, open("data.json","w"), indent=2)

# ---------------- PROGRESS ----------------
st.sidebar.header("Progress")

if os.path.exists("data.json"):
    data = json.load(open("data.json"))
    st.sidebar.write(f"Attempts: {len(data)}")
