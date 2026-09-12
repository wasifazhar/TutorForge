# TutorForge

A Streamlit app that generates quizzes and revision guides for your Preply students, powered by Groq's free/fast LLM API.

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Get a free Groq API key at https://console.groq.com/keys

3. Run the app:
   ```
   streamlit run app.py
   ```

4. Paste your Groq API key into the sidebar (stored only for the session).

   Alternatively, set it as an environment variable before running so you don't need to paste it each time:
   ```
   export GROQ_API_KEY=your_key_here
   streamlit run app.py
   ```

## Features

- **Quiz Generator**: pick a subject (Python, C++, JS, OOP, DSA, SQL, GCSE/IB/AP CS), a topic, difficulty, and question type (MCQ or short-answer/coding). Generates an interactive quiz with scoring and per-question explanations.
- **Revision Guide**: generates a structured Markdown revision guide (overview, key concepts, worked example, common mistakes) for any topic — downloadable as `.md`.

## Notes

- Uses `llama-3.3-70b-versatile` on Groq by default — fast and free-tier friendly. Swap `GROQ_MODEL` in `app.py` if you want a different model.
- All quiz/guide generation calls the LLM live, so keep an eye on your Groq free-tier rate limits if you're using it during live tutoring sessions.
