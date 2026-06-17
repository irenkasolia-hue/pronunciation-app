# Pronunciation App

Simple Streamlit app for pronunciation checks using OpenAI.

How to run locally:
1. Create a virtualenv and install dependencies:
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt

2. Set your OpenAI key. Either:
   - Create file `.streamlit/secrets.toml` with:
     OPENAI_API_KEY = "sk-..."
   - Or set env var `OPENAI_API_KEY`.

3. Run:
   streamlit run app.py

Notes:
- This app saves attempt data to `data.json` locally.
- Make sure your OpenAI plan / model access supports the models used.
