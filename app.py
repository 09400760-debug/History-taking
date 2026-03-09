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
TEXT_PRECEPTOR_INVITE = "Would you like to move to preceptor mode?"
TEXT_PRECEPTOR_QUESTION = "Based on the history, what is your assessment? What are your differential diagnoses?"
TEXT_FEEDBACK_QUESTION = "Would you like to get your assessment and feedback now?"
TEXT_FINAL_YES = "Generating your feedback and score now."
TEXT_FINAL_NO = "Okay. You can generate feedback later by clicking the button below."

VOICE_COMPLETION_HINTS = [
    "would you like to get your assessment and feedback now",
    "thank you please click stop session now",
    "okay please click stop session now",
]

# =========================
# Rubric summary
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

Output format:
- Strengths
- Areas for improvement
- Missed opportunities
- Domain-based scoring comments
- Overall score out of 100
- Overall comment
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
- opening_line must be a brief natural caregiver greeting that introduces the caregiver and child

Example format:
{
  "caregiver_name": "Lindiwe",
  "child_name": "Aya",
  "presenting_complaint": "cough and difficulty breathing",
  "case_summary": "An 8-month-old with 2 days of cough, fast breathing, poor feeding, mild fever, and no seizures.",
  "opening_line": "Hello doctor, I'm Lindiwe. My child's name is Aya."
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
# Helpers
# =========================
def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", str(text).strip().lower())


def is_yes(text: str) -> bool:
    t = normalize_text(text)
    yes_values = {
        "yes", "y", "yeah", "yep", "okay", "ok", "sure", "please do",
        "go ahead", "continue", "yes please", "okay yes", "ok yes"
    }
    return t in yes_values or t.startswith("yes ")


def is_no(text: str) -> bool:
    t = normalize_text(text)
    no_values = {
        "no", "n", "nope", "not now", "later", "no thanks", "not yet"
    }
    return t in no_values or t.startswith("no ")


def looks_like_finished_history(text: str) -> bool:
    t = normalize_text(text)
    phrases = [
        "finished with history",
        "i am finished",
        "im finished",
        "that's all",
        "thats all",
        "done with history",
        "finished",
        "no further questions",
        "i have no further questions",
        "end history",
        "i'm done",
        "im done",
    ]
    return any(p in t for p in phrases)


def looks_like_voice_session_complete(messages) -> bool:
    if not messages:
        return False

    assistant_lines = [
        normalize_text(m.get("content", ""))
        for m in messages
        if m.get("role") == "assistant"
    ]

    if not assistant_lines:
        return False

    for line in reversed(assistant_lines[-5:]):
        if any(hint in line for hint in VOICE_COMPLETION_HINTS):
            return True

    return False


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


def build_caregiver_history_instructions(case_data):
    return f"""
You are simulating a realistic caregiver in a paediatric history-taking station.

Hidden case summary:
{case_data["case_summary"]}

Caregiver name: {case_data["caregiver_name"]}
Child name: {case_data["child_name"]}
Presenting complaint: {case_data["presenting_complaint"]}

Rules:
- Stay fully in caregiver role.
- Use English only.
- Use simple, natural, non-medical language.
- Give only the information asked for.
- Do not volunteer extra details unless directly asked.
- Do not coach the learner.
- Do not ask doctor-like questions.
- If the learner opens with "hello", "hi", "good morning", "good afternoon", or introduces themselves, greet them back naturally, introduce yourself by name, and include your child's name.
- Do not immediately give the whole story on a simple greeting alone.
- If the learner asks broad opening clinical questions like "What brought you in?", "What seems to be the problem?", "Tell me about your child", or "What is the problem with your child?", answer with the main complaint naturally.
- If the learner asks something unclear, ask briefly for clarification.
- Keep your answers internally consistent with the hidden case summary.
"""


def transcript_from_messages(messages):
    return "\n".join([f'{m["role"]}: {m["content"]}' for m in messages])


def call_assessment(messages):
    transcript = transcript_from_messages(messages)

    instructions = f"""
You are a strict paediatric preceptor and examiner giving combined feedback and scoring on a student history-taking station.

Use this rubric summary:
{RUBRIC_TEXT}

Rules:
- Be strict.
- Do not be generous.
- Base everything only on transcript evidence.
- Do not assume missing history was asked.
- Keep the feedback concise but specific and useful.
"""

    prompt = f"""
Transcript:
{transcript}

Provide:
1. Strengths
2. Areas for improvement
3. Missed opportunities
4. Domain-based scoring comments
5. Overall score out of 100
6. Overall comment
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
    query = {
        "age_group": age_group,
        "system": system,
        "caregiver_name": case_data["caregiver_name"],
        "child_name": case_data["child_name"],
        "presenting_complaint": case_data["presenting_complaint"],
        "case_summary": case_data["case_summary"],
        "opening_line": case_data["opening_line"],
        "session_id": session_id,
        "return_url": STREAMLIT_APP_URL,
    }
    return f"{VOICE_SERVER_BASE_URL}/?{urllib.parse.urlencode(query)}"


def get_query_param(name: str, default=""):
    try:
        return st.query_params.get(name, default)
    except Exception:
        return default


def clear_return_query_params():
    for key in ["import_voice", "session_id", "auto_feedback"]:
        try:
            if key in st.query_params:
                del st.query_params[key]
        except Exception:
            pass


def set_status(level: str, message: str):
    st.session_state.last_voice_import_status = {"level": level, "message": message}


def reset_case_state():
    st.session_state.messages = []
    st.session_state.case_data = None
    st.session_state.current_session_id = None
    st.session_state.presentation_done = False
    st.session_state.assessment_generated = None
    st.session_state.mode = "caregiver"
    st.session_state.last_voice_import_status = None
    st.session_state.text_phase = "caregiver"


def apply_imported_messages(imported_messages, session_id=None, status_message="Voice transcript imported automatically."):
    st.session_state.messages = imported_messages
    st.session_state.assessment_generated = None
    st.session_state.presentation_done = looks_like_voice_session_complete(imported_messages)
    st.session_state.mode = "post_presentation" if st.session_state.presentation_done else "caregiver"
    st.session_state.text_phase = "post_presentation" if st.session_state.presentation_done else "caregiver"
    if session_id:
        st.session_state.current_session_id = session_id
    set_status("success", status_message)


def run_text_state_machine(user_text: str):
    phase = st.session_state.text_phase
    case_data = st.session_state.case_data

    if phase == "caregiver":
        if looks_like_finished_history(user_text):
            st.session_state.text_phase = "await_preceptor_choice"
            return TEXT_PRECEPTOR_INVITE

        response = client.responses.create(
            model="gpt-4.1-mini",
            instructions=build_caregiver_history_instructions(case_data),
            input=st.session_state.messages,
        )
        return response.output_text.strip()

    if phase == "await_preceptor_choice":
        if is_yes(user_text):
            st.session_state.text_phase = "await_preceptor_answer"
            return TEXT_PRECEPTOR_QUESTION
        if is_no(user_text):
            st.session_state.text_phase = "caregiver"
            response = client.responses.create(
                model="gpt-4.1-mini",
                instructions=build_caregiver_history_instructions(case_data),
                input=[
                    {"role": "system", "content": "The learner chose not to move to preceptor mode. Continue in caregiver role."},
                    *st.session_state.messages,
                ],
            )
            return response.output_text.strip()
        return "Please answer yes or no."

    if phase == "await_preceptor_answer":
        st.session_state.text_phase = "await_feedback_choice"
        return TEXT_FEEDBACK_QUESTION

    if phase == "await_feedback_choice":
        if is_yes(user_text):
            st.session_state.text_phase = "post_presentation"
            st.session_state.presentation_done = True
            st.session_state.mode = "post_presentation"
            return TEXT_FINAL_YES
        if is_no(user_text):
            st.session_state.text_phase = "post_presentation"
            st.session_state.presentation_done = True
            st.session_state.mode = "post_presentation"
            return TEXT_FINAL_NO
        return "Please answer yes or no."

    return "Conversation complete."


# =========================
# Session state init
# =========================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "case_data" not in st.session_state:
    st.session_state.case_data = None

if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = None

if "presentation_done" not in st.session_state:
    st.session_state.presentation_done = False

if "assessment_generated" not in st.session_state:
    st.session_state.assessment_generated = None

if "mode" not in st.session_state:
    st.session_state.mode = "caregiver"

if "text_phase" not in st.session_state:
    st.session_state.text_phase = "caregiver"

if "selected_age" not in st.session_state:
    st.session_state.selected_age = AGE_OPTIONS[0]

if "selected_system" not in st.session_state:
    st.session_state.selected_system = SYSTEM_OPTIONS[0]

if "last_voice_import_status" not in st.session_state:
    st.session_state.last_voice_import_status = None

# =========================
# Recover query params
# =========================
query_session_id = str(get_query_param("session_id", "")).strip()
if query_session_id:
    st.session_state.current_session_id = query_session_id

import_voice_flag = str(get_query_param("import_voice", "0")).strip()
auto_feedback_flag = str(get_query_param("auto_feedback", "0")).strip()

# =========================
# Auto-import when returning from voice page
# =========================
if import_voice_flag == "1":
    imported_messages, import_error = import_voice_transcript(st.session_state.current_session_id)

    if import_error:
        set_status("warning", import_error)
    else:
        apply_imported_messages(
            imported_messages,
            session_id=st.session_state.current_session_id,
            status_message="Voice transcript imported automatically.",
        )

        if auto_feedback_flag == "1":
            with st.spinner("Generating feedback..."):
                st.session_state.assessment_generated = call_assessment(imported_messages)
                st.session_state.presentation_done = True
                st.session_state.mode = "post_presentation"
                st.session_state.text_phase = "post_presentation"

    clear_return_query_params()
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

if st.button("Start new case", use_container_width=True):
    if not valid_selection:
        st.warning("Please select both an age group and a system first.")
    else:
        try:
            case_data = generate_case(selected_age, selected_system)
            session_id = str(uuid.uuid4())

            reset_case_state()
            st.session_state.case_data = case_data
            st.session_state.current_session_id = session_id
            st.rerun()
        except Exception as e:
            st.error(f"Could not generate case: {e}")

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
elif st.session_state.current_session_id:
    st.info("Voice session detected. If the student completed the session, the transcript can still import automatically on return.")
else:
    st.info("Start a case first, then open the voice page.")

st.caption(
    "The voice case opens in a new tab. After the session ends and the student clicks Stop Session, the app should return here and import the transcript automatically."
)

# =========================
# Show status
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
# Conversation display
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

        assistant_text = run_text_state_machine(prompt)
        st.session_state.messages.append({"role": "assistant", "content": assistant_text})

        if normalize_text(assistant_text) == normalize_text(TEXT_FINAL_YES):
            with st.spinner("Generating feedback..."):
                st.session_state.assessment_generated = call_assessment(st.session_state.messages)

        st.rerun()

elif not st.session_state.case_data and not st.session_state.messages and not st.session_state.current_session_id:
    st.info("Start a case to begin.")
elif st.session_state.mode == "post_presentation":
    st.info("Conversation complete.")
elif st.session_state.messages and not st.session_state.case_data:
    st.info("Imported voice transcript loaded.")

# =========================
# Feedback section
# =========================
if st.session_state.presentation_done and not st.session_state.assessment_generated:
    st.markdown("### Feedback")
    if st.button("Give me Feedback", use_container_width=True):
        with st.spinner("Generating feedback..."):
            st.session_state.assessment_generated = call_assessment(st.session_state.messages)
            st.rerun()

if st.session_state.assessment_generated:
    st.markdown("### Feedback and score")
    st.write(st.session_state.assessment_generated)
