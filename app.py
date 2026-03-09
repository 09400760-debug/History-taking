import json
import re
import urllib.parse
import uuid

import requests
import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="History-taking practice bot", page_icon="🩺")
st.title("🩺 History-taking practice bot")

# =========================
# Config
# =========================
api_key = st.secrets["OPENAI_API_KEY"]
client = OpenAI(api_key=api_key)

VOICE_SERVER_BASE_URL = "https://history-taking-voice.onrender.com"
STREAMLIT_APP_URL = "https://history-takinggit-eexzk8appdm3vzfej2vtuzn.streamlit.app/"

# =========================
# Constants
# =========================
FINAL_VOICE_LINE = "Thank you. Please click stop session. You will then be taken back automatically for feedback and scoring."
FINAL_TEXT_LINE = "Thank you. You can now use the feedback and scoring buttons."

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

Return ONLY valid JSON.
Do not include markdown.
Do not include explanation text.
Do not include code fences.

Use exactly these keys:
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

Example format:
{
  "caregiver_name": "Lindiwe",
  "child_name": "Aya",
  "presenting_complaint": "cough and difficulty breathing",
  "case_summary": "An 8-month-old with 2 days of cough, fast breathing, poor feeding, mild fever, and no seizures.",
  "opening_line": "Hello, who am I speaking to?"
}
"""

# =========================
# Options
# =========================
AGE_OPTIONS = [
    "Please select age group",
    "Neonate",
    "Infant",
    "1-5 years",
    "6-10 years",
    "11-19 years",
]

SYSTEM_OPTIONS = [
    "Please select system",
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
]

# =========================
# Normalization helpers
# =========================
def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", str(text).strip().lower())


def is_final_voice_line(text: str) -> bool:
    return normalize_text(text) == normalize_text(FINAL_VOICE_LINE)


def is_final_text_line(text: str) -> bool:
    return normalize_text(text) == normalize_text(FINAL_TEXT_LINE)


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
            raise ValueError(f"Could not parse generated case JSON.\n\nModel returned:\n{text}")

        json_text = match.group(0)
        json_text = re.sub(r",\s*}", "}", json_text)
        json_text = re.sub(r",\s*]", "]", json_text)

        try:
            data = json.loads(json_text)
        except Exception as e:
            raise ValueError(
                f"Could not parse generated case JSON.\n\nModel returned:\n{text}\n\nJSON error: {e}"
            )

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


def import_voice_transcript(session_id: str | None):
    params = {}
    if session_id:
        params["session_id"] = session_id

    try:
        response = requests.get(
            f"{VOICE_SERVER_BASE_URL}/latest_transcript",
            params=params,
            timeout=20,
        )
    except Exception as e:
        return None, f"Could not contact voice server: {e}"

    if response.status_code != 200:
        return None, "No saved voice transcript found yet on the voice server."

    try:
        payload = response.json()
    except Exception as e:
        return None, f"Voice server returned invalid JSON: {e}"

    data = payload.get("data", {})
    transcript_lines = data.get("transcript_lines", [])

    if not transcript_lines:
        return None, "Saved voice transcript is empty."

    messages = []
    for line in transcript_lines:
        speaker = str(line.get("speaker", "")).strip()
        text = str(line.get("text", "")).strip()

        if not text:
            continue

        if speaker == "Student":
            messages.append({"role": "user", "content": text})
        elif speaker == "Bot":
            messages.append({"role": "assistant", "content": text})

    if not messages:
        return None, "Could not convert voice transcript into chat messages."

    return messages, None


def build_voice_url(age_group, system, case_data, session_id):
    # Deterministic voice opening to reduce the greeting problem
    voice_opening_line = f"Hello doctor, I'm {case_data['caregiver_name']}."

    query = {
        "age_group": age_group,
        "system": system,
        "caregiver_name": case_data["caregiver_name"],
        "child_name": case_data["child_name"],
        "presenting_complaint": case_data["presenting_complaint"],
        "case_summary": case_data["case_summary"],
        "opening_line": voice_opening_line,
        "session_id": session_id,
        "return_url": STREAMLIT_APP_URL,
    }
    return f"{VOICE_SERVER_BASE_URL}/?{urllib.parse.urlencode(query)}"


def clear_import_query_params():
    for key in ["import_voice", "session_id"]:
        try:
            if key in st.query_params:
                del st.query_params[key]
        except Exception:
            pass


def get_last_assistant_message(messages):
    for message in reversed(messages):
        if message.get("role") == "assistant":
            return str(message.get("content", "")).strip()
    return ""


def detect_presentation_done(messages):
    last_assistant = get_last_assistant_message(messages)
    return is_final_voice_line(last_assistant) or is_final_text_line(last_assistant)


def set_import_status(level: str, message: str):
    st.session_state.last_voice_import_status = {"level": level, "message": message}


def apply_imported_messages(imported_messages, session_id=None, status_message="Voice transcript imported automatically."):
    st.session_state.messages = imported_messages
    st.session_state.feedback_generated = None
    st.session_state.score_generated = None
    st.session_state.presentation_done = detect_presentation_done(imported_messages)
    st.session_state.mode = "post_presentation" if st.session_state.presentation_done else "caregiver"
    if session_id:
        st.session_state.current_session_id = session_id
    set_import_status("success", status_message)


def reset_case_state(reset_selections: bool = False):
    st.session_state.messages = []
    st.session_state.case_data = None
    st.session_state.current_session_id = None
    st.session_state.presentation_done = False
    st.session_state.feedback_generated = None
    st.session_state.score_generated = None
    st.session_state.mode = "caregiver"
    st.session_state.last_voice_import_status = None
    if reset_selections:
        st.session_state.selected_age = AGE_OPTIONS[0]
        st.session_state.selected_system = SYSTEM_OPTIONS[0]


# =========================
# Session state initialization
# =========================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "case_data" not in st.session_state:
    st.session_state.case_data = None

if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = None

if "presentation_done" not in st.session_state:
    st.session_state.presentation_done = False

if "feedback_generated" not in st.session_state:
    st.session_state.feedback_generated = None

if "score_generated" not in st.session_state:
    st.session_state.score_generated = None

if "mode" not in st.session_state:
    st.session_state.mode = "caregiver"

if "selected_age" not in st.session_state:
    st.session_state.selected_age = AGE_OPTIONS[0]

if "selected_system" not in st.session_state:
    st.session_state.selected_system = SYSTEM_OPTIONS[0]

if "last_voice_import_status" not in st.session_state:
    st.session_state.last_voice_import_status = None

# =========================
# Auto-import when returning from voice page
# =========================
import_voice_flag = st.query_params.get("import_voice", "0")
query_session_id = st.query_params.get("session_id", "")

if str(import_voice_flag) == "1":
    session_id_for_import = str(query_session_id).strip() or st.session_state.current_session_id
    imported_messages, import_error = import_voice_transcript(session_id_for_import)

    if import_error:
        set_import_status("warning", import_error)
    else:
        apply_imported_messages(
            imported_messages,
            session_id=session_id_for_import,
            status_message="Voice transcript imported automatically.",
        )

    clear_import_query_params()
    st.rerun()

# =========================
# Controls
# =========================
selected_age = st.selectbox(
    "Choose age group",
    AGE_OPTIONS,
    key="selected_age",
)

selected_system = st.selectbox(
    "Choose system",
    SYSTEM_OPTIONS,
    key="selected_system",
)

valid_selection = (
    selected_age != AGE_OPTIONS[0]
    and selected_system != SYSTEM_OPTIONS[0]
)

col1, col2 = st.columns(2)

with col1:
    if st.button("Start / reset case"):
        if not valid_selection:
            st.warning("Please select both an age group and a system first.")
        else:
            try:
                case_data = generate_case(selected_age, selected_system)
                session_id = str(uuid.uuid4())

                st.session_state.case_data = case_data
                st.session_state.current_session_id = session_id
                st.session_state.messages = [
                    {"role": "assistant", "content": case_data["opening_line"]}
                ]
                st.session_state.presentation_done = False
                st.session_state.feedback_generated = None
                st.session_state.score_generated = None
                st.session_state.mode = "caregiver"
                st.session_state.last_voice_import_status = None
                st.rerun()
            except Exception as e:
                st.error(f"Could not generate case: {e}")

with col2:
    if st.button("Reset conversation"):
        reset_case_state(reset_selections=True)
        st.rerun()

# =========================
# Voice section
# =========================
st.markdown("### Live voice mode")

if st.session_state.case_data and st.session_state.current_session_id:
    voice_url = build_voice_url(
        st.session_state.selected_age,
        st.session_state.selected_system,
        st.session_state.case_data,
        st.session_state.current_session_id,
    )
    st.link_button("Open realtime voice case", voice_url, use_container_width=True)
else:
    st.info("Start a case first, then open the voice page.")

st.caption(
    "The voice case opens in a new tab. After the session ends and the student clicks Stop Session, the app should return here and import the transcript automatically."
)

if st.button("Import latest voice transcript manually"):
    imported_messages, import_error = import_voice_transcript(st.session_state.current_session_id)

    if import_error:
        set_import_status("warning", import_error)
        st.warning(import_error)
    else:
        apply_imported_messages(
            imported_messages,
            session_id=st.session_state.current_session_id,
            status_message="Voice transcript imported manually.",
        )
        st.success("Voice transcript imported.")
        st.rerun()

# =========================
# Show import status
# =========================
status_value = st.session_state.last_voice_import_status
if isinstance(status_value, dict):
    level = status_value.get("level", "info")
    message = status_value.get("message", "")
    if message:
        if level == "success":
            st.success(message)
        elif level == "warning":
            st.warning(message)
        else:
            st.info(message)
elif isinstance(status_value, str) and status_value.strip():
    st.info(status_value.strip())

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
if st.session_state.case_data and st.session_state.mode != "post_presentation":
    if prompt := st.chat_input("Type your response…"):
        st.session_state.messages.append({"role": "user", "content": prompt})

        response = client.responses.create(
            model="gpt-4.1-mini",
            instructions=build_text_mode_instructions(st.session_state.case_data),
            input=st.session_state.messages,
        )

        assistant_text = response.output_text.strip()
        st.session_state.messages.append({"role": "assistant", "content": assistant_text})

        if is_final_text_line(assistant_text):
            st.session_state.presentation_done = True
            st.session_state.mode = "post_presentation"

        st.rerun()
elif not st.session_state.case_data and not st.session_state.messages:
    st.info("Start a case to begin.")
elif st.session_state.mode == "post_presentation":
    st.info("Conversation complete. Use the feedback or scoring tools below.")

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
