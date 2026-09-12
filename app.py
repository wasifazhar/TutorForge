import streamlit as st
from groq import Groq
import json
import re
import os

st.set_page_config(page_title="TutorForge", page_icon=":material/school:", layout="centered")

MODEL_OPTIONS = {
    "GPT-OSS 120B (higher quality)": "openai/gpt-oss-120b",
    "GPT-OSS 20B (faster)": "openai/gpt-oss-20b",
}

SUBJECTS = [
    "Python", "C++", "JavaScript", "Object-Oriented Programming",
    "Data Structures & Algorithms", "SQL", "GCSE Computer Science",
    "IB Computer Science", "AP Computer Science", "Custom..."
]

DIFFICULTIES = ["Beginner", "Intermediate", "Advanced"]


def subject_picker(key_prefix):
    subject_choice = st.selectbox("Subject", SUBJECTS, key=f"{key_prefix}_subject")
    if subject_choice == "Custom...":
        return st.text_input("Enter custom subject", key=f"{key_prefix}_subject_custom")
    return subject_choice


def get_client():
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        try:
            api_key = st.secrets.get("GROQ_API_KEY")
        except Exception:
            api_key = None
    if not api_key:
        return None
    return Groq(api_key=api_key)


def extract_json(text):
    text = text.strip()
    text = re.sub(r"^```(json)?", "", text)
    text = re.sub(r"```$", "", text)
    text = text.strip()
    match = re.search(r"\[.*\]|\{.*\}", text, re.DOTALL)
    if match:
        text = match.group(0)
    return json.loads(text)


def generate_quiz(client, model, subject, topic, difficulty, num_questions, q_type):
    system_prompt = (
        "You are an expert computer science tutor who writes precise, exam-quality quiz "
        "questions. Always respond with valid JSON only, no commentary, no markdown fences."
    )
    if q_type == "Multiple Choice":
        format_instruction = (
            'Return a JSON array of objects, each with keys: '
            '"question" (string), "options" (array of exactly 4 strings), '
            '"correct_index" (integer 0-3), "explanation" (string, 1-2 sentences).'
        )
    else:
        format_instruction = (
            'Return a JSON array of objects, each with keys: '
            '"question" (string, a short-answer or coding question), '
            '"answer" (string, the ideal answer or code), '
            '"explanation" (string, 1-2 sentences).'
        )

    user_prompt = (
        f"Create {num_questions} {difficulty.lower()}-level {q_type.lower()} questions "
        f"on the subject '{subject}', focused on the topic: '{topic}'. "
        f"{format_instruction}"
    )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.6,
    )
    return extract_json(response.choices[0].message.content)


def generate_revision_guide(client, model, subject, topic, difficulty):
    system_prompt = (
        "You are an expert computer science tutor. Produce clear, well-structured "
        "revision notes in Markdown, using headers, bullet points, and short code "
        "blocks where useful. No filler, no preamble."
    )
    user_prompt = (
        f"Write a {difficulty.lower()}-level revision guide for the topic "
        f"'{topic}' within the subject '{subject}'. Include: a short overview, "
        f"key concepts as bullet points, one worked example, and common mistakes "
        f"students make."
    )
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.5,
    )
    return response.choices[0].message.content


def reset_quiz_state():
    for key in ["quiz_data", "active_quiz_type", "current_q", "score", "answers", "submitted"]:
        st.session_state.pop(key, None)


def quiz_tab(client, model):
    st.subheader(":material/quiz: Generate a Quiz")
    col1, col2 = st.columns(2)
    with col1:
        subject = subject_picker("quiz")
        difficulty = st.selectbox("Difficulty", DIFFICULTIES, key="quiz_difficulty")
    with col2:
        q_type = st.selectbox("Question Type", ["Multiple Choice", "Short Answer / Coding"], key="quiz_type_select")
        num_questions = st.slider("Number of Questions", 3, 15, 5, key="quiz_num")

    topic = st.text_input("Specific Topic (e.g. 'recursion', 'JOINs', 'binary search trees')", key="quiz_topic")

    if st.button("Generate Quiz", type="primary", icon=":material/bolt:"):
        if not client:
            st.error("Groq API key not configured. See the setup instructions in the README.")
        elif not subject.strip():
            st.warning("Please enter a subject.")
        elif not topic.strip():
            st.warning("Please enter a topic.")
        else:
            with st.spinner("Generating questions..."):
                try:
                    quiz_data = generate_quiz(client, model, subject, topic, difficulty, num_questions, q_type)
                    reset_quiz_state()
                    st.session_state.update({
                        "quiz_data": quiz_data,
                        "active_quiz_type": q_type,
                        "current_q": 0,
                        "score": 0,
                        "answers": {},
                        "submitted": False,
                    })
                except Exception as e:
                    st.error(f"Failed to generate quiz: {e}")

    if st.session_state.get("quiz_data"):
        st.divider()
        render_quiz()


def render_quiz():
    quiz_data = st.session_state.quiz_data
    q_type = st.session_state.active_quiz_type
    total = len(quiz_data)

    if st.session_state.submitted:
        st.success(f"Score: {st.session_state.score} / {total}")
        for i, q in enumerate(quiz_data):
            with st.expander(f"Q{i + 1}: {q['question']}"):
                if q_type == "Multiple Choice":
                    correct = q["options"][q["correct_index"]]
                    user_choice = st.session_state.answers.get(i)
                    st.write(f"**Your answer:** {user_choice}")
                    st.write(f"**Correct answer:** {correct}")
                else:
                    st.write(f"**Your answer:** {st.session_state.answers.get(i, '')}")
                    st.write(f"**Model answer:** {q['answer']}")
                st.info(q["explanation"])
        if st.button("Start New Quiz", icon=":material/refresh:"):
            reset_quiz_state()
            st.rerun()
        return

    st.progress((st.session_state.current_q) / total)
    idx = st.session_state.current_q
    q = quiz_data[idx]
    st.markdown(f"**Question {idx + 1} of {total}**")
    st.write(q["question"])

    if q_type == "Multiple Choice":
        choice = st.radio("Select an answer:", q["options"], key=f"choice_{idx}", index=None)
    else:
        choice = st.text_area("Your answer:", key=f"answer_{idx}")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Submit Answer", key=f"submit_{idx}", icon=":material/check:"):
            if choice is None or (isinstance(choice, str) and not choice.strip()):
                st.warning("Please provide an answer.")
            else:
                st.session_state.answers[idx] = choice
                if q_type == "Multiple Choice" and choice == q["options"][q["correct_index"]]:
                    st.session_state.score += 1
                if idx + 1 < total:
                    st.session_state.current_q += 1
                else:
                    st.session_state.submitted = True
                st.rerun()


def revision_tab(client, model):
    st.subheader(":material/menu_book: Generate a Revision Guide")
    col1, col2 = st.columns(2)
    with col1:
        subject = subject_picker("rev")
    with col2:
        difficulty = st.selectbox("Difficulty", DIFFICULTIES, key="rev_difficulty")

    topic = st.text_input("Topic (e.g. 'pointers', 'normalization', 'Big-O notation')", key="rev_topic")

    if st.button("Generate Guide", type="primary", icon=":material/auto_awesome:"):
        if not client:
            st.error("Groq API key not configured. See the setup instructions in the README.")
        elif not subject.strip():
            st.warning("Please enter a subject.")
        elif not topic.strip():
            st.warning("Please enter a topic.")
        else:
            with st.spinner("Writing revision guide..."):
                try:
                    guide = generate_revision_guide(client, model, subject, topic, difficulty)
                    st.session_state.revision_guide = guide
                except Exception as e:
                    st.error(f"Failed to generate guide: {e}")

    if st.session_state.get("revision_guide"):
        st.divider()
        st.markdown(st.session_state.revision_guide)
        st.download_button(
            "Download as Markdown",
            st.session_state.revision_guide,
            file_name=f"{topic or 'revision_guide'}.md",
            icon=":material/download:",
        )


def main():
    st.title(":material/school: TutorForge")
    st.caption("Built to generate quizzes and revision guides on demand by Wasif Azhar.")

    with st.sidebar:
        st.header(":material/settings: Settings")
        model_label = st.selectbox("Model", list(MODEL_OPTIONS.keys()))
        model = MODEL_OPTIONS[model_label]

    client = get_client()
    if not client:
        st.warning(
            "No Groq API key found. Set the `GROQ_API_KEY` environment variable "
            "(or add it to Streamlit secrets) and restart the app.",
            icon=":material/key_off:",
        )

    tab1, tab2 = st.tabs([":material/quiz: Quiz Generator", ":material/menu_book: Revision Guide"])
    with tab1:
        quiz_tab(client, model)
    with tab2:
        revision_tab(client, model)


if __name__ == "__main__":
    main()
