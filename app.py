import streamlit as st
import streamlit.components.v1 as components

WORDS = ["genre","receipt","queue","colonel","psychology","ballet","chaos"]

st.title("🎤 FREE Pronunciation Trainer (No API)")

word = st.selectbox("Choose word", WORDS)

st.write("Click mic and speak 👇")

components.html(f"""
<html>
<body>
<button onclick="start()">🎤 Start speaking</button>
<p id="result">...</p>

<script>
function start() {{
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    recognition.lang = 'en-US';

    recognition.onresult = function(event) {{
        document.getElementById("result").innerText =
        "You said: " + event.results[0][0].transcript;
    }}

    recognition.start();
}}
</script>

</body>
</html>
""", height=200)

st.info("No API. Fully free browser speech recognition.")
