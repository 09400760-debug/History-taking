import json
import re
import urllib.parse

import requests
import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="History-taking practice bot", page_icon="🩺")

st.title("🩺 History-taking practice bot")

# =========================
# OpenAI client
# =========================
api_key = st.secrets["OPENAI_API_KEY"]
client = OpenAI(api_key=api_key)

# =========================
# Hosted voice backend
# =========================
VOICE_SERVER_BASE_URL = "https://history-taking-voice.onrender.com"

# =========================
# Rubric summary for feedback/scoring
# =========================
RUBRIC_TEXT = """
Wits Paediatrics history-taking rubric (strict marking approach)

Assess the student strictly on:
1. Main complaint and development of symptoms
2. Danger signs
3. Involved system focused history
4. Other systems enquiry
5. Birth history
6. Immunisation
7. Nutrition
8. Past medical / surgical / medication / allergy history
9. Family history
10. Social history where relevant
11. Communication and logical flow
12. Preceptor stage: assessment and differential diagnoses

Important strict principles:
- Do not mark generously.
- Reward specificity and follow-up questions.
- Broad vague questions should score lower unless followed by detail.
- Do not assume a question was asked if it is not clearly present in the transcript.
- If the learner misses important lines of enquiry, count that against them.
- If the learner asks closed questions only, note the weakness.
- Use transcript evidence only.

Feedback format:
- Strengths
- Areas for improvement
- Missed opportunities
- Overall comment

Scoring format:
- Score each major domain briefly
- Give an overall score out of 100
- Use a strict marker standard
- Give a short rationale
"""

# =========================
# Case generator prompt
# =========================
CASE_GENERATOR_PROMPT = """
You are generating a paediatric practice case for a 5th-year medical student.

Return ONLY valid JSON with these keys:
- caregiver_name
- child_name
- presenting_complaint
- case_summary
- opening_line

Rules:
- South African paediatric context
- realistic caregiver language
- common paediatric problem
- keep case_summary hidden and concise but clinically useful
- opening_line must sound like a caregiver speaking
"""

# =========================
# Helpers
# =========================
def generate_case(age_group: str, system: str):
    prompt = f"""
Generate one case for:
Age group: {age_group}
System: {system}
"""
    response = client.responses.create(
        model="gpt-4.1-mini",
        instructions=CASE_GENERATOR_PROMPT,
        input=prompt,
    )

    text = response.output_text.strip()

    try:
        data = json.loads(text)
    except Exception:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise ValueError("Could not parse generated case JSON.")
        data = json.loads(match.group(0))

    required = [
        "caregiver_name",
        "child_name",
        "presenting_complaint",
        "case_summary",
        "opening_line",
    ]
    for key in required:
        if key not in data:
            raise ValueError(f"Generated case missing key: {key}")

    return data


def build_text_mode_instructions(case_data):
    return f"""
You are simulating a realistic caregiver in a paediatric history-taking station.

Hidden case summary:
{case_data["case_summary"]}

Caregiver name: {case_data["caregiver_name"]}
Child name: {case_data["child_name"]}
Presenting complaint: {case_data["presenting_complaint"]}

Rules:
- Stay in caregiver role unless the learner clearly indicates they are finished.
- Use English only.
- Use simple, natural, non-medical language.
- Give only the information asked for.
- Do not volunteer extra details.
- Do not coach the learner.
- Do not ask doctor-like questions.
- If the learner only introduces themselves, acknowledge briefly and wait.
- If the learner asks broad opening questions like "What brought you in?" answer with the main complaint directly.
- If the learner clearly says they are done, respond only:
  "Would you like to move to preceptor mode?"
- If the learner says yes to preceptor mode, ask only:
  "Based on the history, what is your assessment? What are your differential diagnoses?"
- After the learner answers in preceptor mode, respond only:
  "Thank you. You can now use the feedback and scoring buttons."
"""


def transcript_from_messages(messages):
    return "\n".join([f'{m["role"]}: {m["content"]}' for m in messages])


def call_feedback(messages):
    transcript = transcript_from_messages(messages)

    instructions = f"""
You are a strict paediatric preceptor giving feedback on a student history-taking station.

Use this rubric summary:
{RUBRIC_TEXT}

Give concise but useful feedback.
Do not be generous.
Base everything on transcript evidence only.
"""

    prompt = f"""
Transcript:
{transcript}

Provide:
1. Strengths
2. Areas for improvement
3. Missed opportunities
4. Overall comment
"""

    response = client.responses.create(
        model="gpt-4.1-mini",
        instructions=instructions,
        input=prompt,
    )
    return response.output_text.strip()


def call_scoring(messages):
    transcript = transcript_from_messages(messages)

    instructions = f"""
You are a strict paediatric examiner scoring a history-taking performance.

Use this rubric summary:
{RUBRIC_TEXT}

Mark strictly.
Do not be generous.
Base everything on transcript evidence only.
Give an overall score out of 100.
"""

    prompt = f"""
Transcript:
{transcript}

Provide:
- Brief domain-based scoring comments
- Overall score out of 100
- Short rationale for the mark
"""

    response = client.responses.create(
        model="gpt-4.1-mini",
        instructions=instructions,
        input=prompt,
    )
    return response.output_text.strip()


def import_latest_voice_transcript():
    try:
        response = requests.get(f"{VOICE_SERVER_BASE_URL}/latest_transcript", timeout=20)
    except Exception as e:
        return None, f"Could not contact voice server: {e}"

    if response.status_code != 200:
        return None, "No saved voice transcript found yet on the voice server."

    payload = response.json()
    data = payload.get("data", {})
    transcript_lines = data.get("transcript_lines", [])

    if not transcript_lines:
        return None, "Saved voice transcript is empty."

    messages = []
    for line in transcript_lines:
        speaker = line.get("speaker", "").strip()
        text = line.get("text", "").strip()
        if not text:
            continue

        if speaker == "Student":
            messages.append({"role": "user", "content": text})
        elif speaker == "Bot":
            messages.append({"role": "assistant", "content": text})

    if not messages:
        return None, "Could not convert voice transcript into chat messages."

    return messages, None


def build_voice_url(age_group, system, case_data):
    query = {
        "age_group": age_group,
        "system": system,
        "case_summary": case_data["case_summary"],
        "opening_line": case_data["opening_line"],
    }
    return f"{VOICE_SERVER_BASE_URL}/?{urllib.parse.urlencode(query)}"


# =========================
# Session state
# =========================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "case_data" not in st.session_state:
    st.session_state.case_data = None

if "presentation_done" not in st.session_state:
    st.session_state.presentation_done = False

if "feedback_generated" not in st.session_state:
    st.session_state.feedback_generated = None

if "score_generated" not in st.session_state:
    st.session_state.score_generated = None

if "mode" not in st.session_state:
    st.session_state.mode = "caregiver"

# =========================
# Controls
# =========================
selected_age = st.selectbox(
    "Choose age group",
    ["Neonate", "Infant", "1-5 years", "6-10 years", "11-19 years"],
)

selected_system = st.selectbox(
    "Choose system",
    [
        "Respiratory",
        "Gastrointestinal",
        "Neurological",
        "Cardiovascular",
        "Endocrine",
        "Renal",
        "Infectious diseases",
        "Nutrition",
        "Development",
        "Neonatology",
        "Haematology and oncology",
        "Musculoskeletal",
        "Dermatology",
    ],
)

col1, col2 = st.columns(2)

with col1:
    if st.button("Start / reset case"):
        try:
            case_data = generate_case(selected_age, selected_system)
            st.session_state.case_data = case_data
            st.session_state.messages = [
                {"role": "assistant", "content": case_data["opening_line"]}
            ]
            st.session_state.presentation_done = False
            st.session_state.feedback_generated = None
            st.session_state.score_generated = None
            st.session_state.mode = "caregiver"
            st.rerun()
        except Exception as e:
            st.error(f"Could not generate case: {e}")

with col2:
    if st.button("Reset conversation"):
        st.session_state.messages = []
        st.session_state.presentation_done = False
        st.session_state.feedback_generated = None
        st.session_state.score_generated = None
        st.session_state.mode = "caregiver"
        st.rerun()

# =========================
# Voice section
# =========================
st.markdown("### Live voice mode")

if st.session_state.case_data:
    voice_url = build_voice_url(selected_age, selected_system, st.session_state.case_data)
    st.link_button("Open realtime voice case", voice_url)
else:
    st.info("Start a case first, then open the voice page.")

st.caption(
    "After you finish the voice case and click Stop Session there, come back here and import the latest voice transcript."
)

if st.button("Import latest voice transcript"):
    imported_messages, import_error = import_latest_voice_transcript()

    if import_error:
        st.warning(import_error)
    else:
        st.session_state.messages = imported_messages
        st.session_state.feedback_generated = None
        st.session_state.score_generated = None

        transcript_text = "\n".join(
            [f"{m['role']}: {m['content']}" for m in imported_messages]
        ).lower()

        if "please click stop session, then return to the main app for feedback and scoring" in transcript_text:
            st.session_state.presentation_done = True
            st.session_state.mode = "post_presentation"
        else:
            st.session_state.presentation_done = False
            st.session_state.mode = "caregiver"

        st.success("Voice transcript imported.")
        st.rerun()

# =========================
# Show current case summary to teacher only
# =========================
if st.session_state.case_data:
    with st.expander("Current hidden case summary"):
        st.write(st.session_state.case_data["case_summary"])

# =========================
# Chat display
# =========================
st.markdown("### Conversation")

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.write(m["content"])

# =========================
# Text chat mode
# =========================
if st.session_state.case_data:
    if prompt := st.chat_input("Type your response…"):
        st.session_state.messages.append({"role": "user", "content": prompt})

        response = client.responses.create(
            model="gpt-4.1-mini",
            instructions=build_text_mode_instructions(st.session_state.case_data),
            input=st.session_state.messages,
        )

        assistant_text = response.output_text.strip()
        st.session_state.messages.append({"role": "assistant", "content": assistant_text})

        lower_reply = assistant_text.lower()

        if "thank you. you can now use the feedback and scoring buttons." in lower_reply:
            st.session_state.presentation_done = True
            st.session_state.mode = "post_presentation"

        st.rerun()
else:
    st.info("Start a case to begin.")

# =========================
# Feedback and scoring
# =========================
if st.session_state.presentation_done:
    st.markdown("### Post-presentation tools")

    fcol1, fcol2 = st.columns(2)

    with fcol1:
        if st.button("Give me Feedback"):
            with st.spinner("Generating feedback..."):
                st.session_state.feedback_generated = call_feedback(st.session_state.messages)
                st.rerun()

    with fcol2:
        if st.button("Score my Performance"):
            with st.spinner("Scoring performance..."):
                st.session_state.score_generated = call_scoring(st.session_state.messages)
                st.rerun()

if st.session_state.feedback_generated:
    st.markdown("### Feedback")
    st.write(st.session_state.feedback_generated)

if st.session_state.score_generated:
    st.markdown("### Score")
    st.write(st.session_state.score_generated)

