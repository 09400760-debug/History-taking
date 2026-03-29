import json
import random
import re
import urllib.parse
import uuid
from datetime import datetime

import requests
import streamlit as st
from openai import OpenAI

from dynamic_rubric import (
    choose_case,
    build_history_taking_system_prompt,
    build_assessor_system_prompt,
    build_assessor_schema,
)

st.set_page_config(
    page_title="History-taking practice bot",
    page_icon="🩺",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    :root {
        color-scheme: light !important;
    }

    html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"], .main {
        background: #ffffff !important;
        color: #111111 !important;
    }

    [data-testid="stHeader"] {
        background: #ffffff !important;
    }

    [data-testid="stToolbar"] {
        right: 0.5rem;
    }

    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 2rem;
        max-width: 820px;
        background: #ffffff !important;
    }

    p, div, label, span, h1, h2, h3, h4, h5 {
        color: #111111 !important;
    }

    [data-testid="stChatMessageContent"] {
        color: #111111 !important;
    }

    [data-testid="stMarkdownContainer"] {
        color: #111111 !important;
    }

    input, textarea {
        background: #ffffff !important;
        color: #111111 !important;
    }

    section[data-testid="stSidebar"] {
        background: #ffffff !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

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
APP_TITLE = "🩺 History-taking practice bot"
WELCOME_TEXT = (
    "This space gives you opportunities to practise paediatric history taking. "
    "The aim is to assess how well you build a diagnosis through a thorough relevant history. "
    "This is not a management station."
)

TEXT_PRECEPTOR_INVITE = "Would you like to move to preceptor mode?"
TEXT_SUMMARY_QUESTION = "Please summarise the case briefly in one or two sentences."
TEXT_DIAGNOSIS_QUESTION = "What is your most likely diagnosis?"
TEXT_DIFFERENTIALS_QUESTION = "What are your main differential diagnoses?"
TEXT_END_CONFIRM = "Are you finished and ready for feedback?"
TEXT_FINAL_LINE = "Thank you. I will now generate your feedback."

NON_CUSTOMIZED_FEEDBACK_QUESTION = "Would you like any feedback?"

VOICE_COMPLETION_HINTS = [
    "thank you i will now generate your feedback",
]

VISIBLE_INTERACTION_MODES = [
    "Text only",
    "Realtime voice",
]

VISIBLE_AGE_OPTIONS = [
    "Random",
    "Neonate",
    "Infant",
    "1-5 years",
    "6-10 years",
    "11-19 years",
]

VISIBLE_SYSTEM_OPTIONS = [
    "Random",
    "Cardiovascular",
    "Gastrointestinal",
    "Musculoskeletal",
    "Neurological",
    "Renal",
    "Respiratory",
]

RANDOM_AGE_POOL = [
    "Neonate",
    "Infant",
    "1-5 years",
    "6-10 years",
    "11-19 years",
]

RANDOM_SYSTEM_POOL = [
    "Cardiovascular",
    "Gastrointestinal",
    "Musculoskeletal",
    "Neurological",
    "Renal",
    "Respiratory",
]

STUDY_NUMBERS_PER_ARM = 126
STUDY_NUMBER_OPTIONS = ["Please select study number"] + [
    f"1-{i:03d}" for i in range(1, STUDY_NUMBERS_PER_ARM + 1)
] + [
    f"2-{i:03d}" for i in range(1, STUDY_NUMBERS_PER_ARM + 1)
]

GRADE_LABELS = {
    1: "Early Development",
    2: "Emerging Competence",
    3: "Competent",
    4: "Highly Competent",
    5: "Exceptional Competence",
}

CUSTOMIZED_GROUP = "customized"
NON_CUSTOMIZED_GROUP = "non_customized"

# =========================
# Helpers
# =========================
def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", str(text).strip().lower())


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def parse_iso(value: str | None):
    if not value:
        return None
    try:
        cleaned = str(value).strip()
        if cleaned.endswith("Z"):
            cleaned = cleaned[:-1] + "+00:00"
        return datetime.fromisoformat(cleaned)
    except Exception:
        return None


def format_hhmm(value: str | None) -> str:
    dt = parse_iso(value)
    return dt.strftime("%H:%M") if dt else "Not recorded"


def format_duration(started_at: str | None, ended_at: str | None) -> str:
    start_dt = parse_iso(started_at)
    end_dt = parse_iso(ended_at)
    if not start_dt or not end_dt:
        return "Not recorded"
    mins = max(0, int(round((end_dt - start_dt).total_seconds() / 60)))
    return f"{mins} mins"


def is_yes(text: str) -> bool:
    t = normalize_text(text)
    yes_values = {
        "yes", "y", "yeah", "yep", "okay", "ok", "sure", "please do",
        "go ahead", "continue", "yes please", "okay yes", "ok yes"
    }
    return t in yes_values or t.startswith("yes ")


def is_no(text: str) -> bool:
    t = normalize_text(text)
    no_values = {"no", "n", "nope", "not now", "later", "no thanks", "not yet"}
    return t in no_values or t.startswith("no ")


def looks_like_finished_history(text: str) -> bool:
    t = normalize_text(text)
    phrases = [
        "finished with history",
        "i am finished",
        "im finished",
        "i'm finished",
        "i am done",
        "im done",
        "i'm done",
        "that's all",
        "thats all",
        "done with history",
        "finished",
        "no further questions",
        "i have no further questions",
        "end history",
        "that is all",
        "history complete",
        "we are done",
        "can we move to preceptor",
        "move to preceptor",
        "switch to preceptor",
    ]
    return any(p in t for p in phrases)


def looks_like_voice_session_complete(messages):
    if not messages:
        return False

    assistant_lines = [
        normalize_text(m.get("content", ""))
        for m in messages
        if m.get("role") == "assistant"
    ]

    for line in reversed(assistant_lines[-12:]):
        if any(hint in line for hint in VOICE_COMPLETION_HINTS):
            return True
    return False


def looks_like_greeting_only(text: str) -> bool:
    return normalize_text(text) in {
        "hello", "hi", "hey", "good morning", "good afternoon", "good evening",
        "hello there", "hi there"
    }


def resolve_random_selection(selected_age: str, selected_system: str):
    resolved_age = selected_age if selected_age != "Random" else random.choice(RANDOM_AGE_POOL)
    resolved_system = selected_system if selected_system != "Random" else random.choice(RANDOM_SYSTEM_POOL)
    return resolved_age, resolved_system


def transcript_from_messages(messages):
    return "\n".join([f'{m["role"]}: {m["content"]}' for m in messages])


def get_student_messages(messages):
    return [
        str(m.get("content", "")).strip()
        for m in messages
        if m.get("role") == "user" and str(m.get("content", "")).strip()
    ]


def is_meaningful_student_text(text: str) -> bool:
    t = normalize_text(text)
    trivial = {
        "", "hello", "hi", "hey", "good morning", "good afternoon", "good evening",
        "okay", "ok", "yes", "no", "sure", "thanks", "thank you"
    }
    if t in trivial:
        return False
    word_count = len([w for w in re.split(r"\s+", t) if w])
    return word_count >= 4


def has_meaningful_interaction(messages) -> bool:
    student_messages = get_student_messages(messages)
    meaningful_turns = [msg for msg in student_messages if is_meaningful_student_text(msg)]
    total_student_words = sum(
        len([w for w in re.split(r"\s+", msg.strip()) if w])
        for msg in student_messages
    )
    return len(meaningful_turns) >= 2 or total_student_words >= 12


def make_json_safe(obj):
    if isinstance(obj, dict):
        return {str(k): make_json_safe(v) for k, v in obj.items()}
    if isinstance(obj, set):
        return sorted([make_json_safe(v) for v in obj])
    if isinstance(obj, list):
        return [make_json_safe(v) for v in obj]
    if isinstance(obj, tuple):
        return [make_json_safe(v) for v in obj]
    return obj


def score_to_grade(score):
    try:
        s = float(score)
    except Exception:
        return 1

    if s < 20:
        return 1
    if s < 40:
        return 2
    if s < 60:
        return 3
    if s < 80:
        return 4
    return 5


def coerce_grade(value):
    try:
        g = int(value)
    except Exception:
        return None
    if g < 1:
        return 1
    if g > 5:
        return 5
    return g


def looks_like_history_question(text: str) -> bool:
    t = normalize_text(text)
    question_starters = [
        "how old", "when did", "when was", "what happened", "what brought",
        "why did", "how long", "has she", "has he", "did she", "did he",
        "is she", "is he", "does she", "does he", "was she", "was he",
        "can you tell me", "tell me about", "any", "who lives", "what is her",
        "what is his", "what are", "has there been", "do you know", "was there"
    ]
    if "?" in text:
        return True
    return any(t.startswith(p) for p in question_starters)


def looks_like_summary_response(text: str) -> bool:
    t = normalize_text(text)
    if looks_like_history_question(text):
        return False
    if len(t.split()) < 5:
        return False
    summary_markers = [
        "this is", "this child", "this patient", "a child with", "a 6-year-old",
        "a 2-year-old", "a 4-year-old", "a 9-year-old", "child with", "presentation of",
        "likely", "with", "who has"
    ]
    return any(marker in t for marker in summary_markers)


def looks_like_diagnosis_response(text: str) -> bool:
    t = normalize_text(text)
    if looks_like_history_question(text):
        return False
    if len(t.split()) > 20:
        return False
    diagnosis_markers = [
        "pyelonephritis", "uti", "urinary tract infection", "epilepsy", "meningitis",
        "pneumonia", "bronchiolitis", "asthma", "tuberculosis", "tb", "appendicitis",
        "gastroenteritis", "dehydration", "sepsis", "nephrotic syndrome", "nephritic syndrome",
        "reflux", "cerebral palsy", "migraine", "febrile seizure", "pertussis",
        "croup", "foreign body aspiration", "congenital heart disease", "malnutrition",
        "hepatitis", "dysentery", "constipation", "rickets", "congenital syphilis"
    ]
    return any(marker in t for marker in diagnosis_markers)


def looks_like_differentials_response(text: str) -> bool:
    t = normalize_text(text)
    if looks_like_history_question(text):
        return False
    differential_markers = [
        ",", ";", "or", "also", "another", "differential", "possibility", "could be"
    ]
    if len(t.split()) < 2:
        return False
    return any(marker in t for marker in differential_markers)


def get_study_group(study_number: str | None) -> str:
    if not study_number:
        return CUSTOMIZED_GROUP

    cleaned = str(study_number).strip()
    prefix = cleaned.split("-")[0]

    if prefix == "1":
        return CUSTOMIZED_GROUP
    if prefix == "2":
        return NON_CUSTOMIZED_GROUP

    return CUSTOMIZED_GROUP


def build_non_customized_caregiver_prompt(case_data: dict, optional_instruction: str = "") -> str:
    prompt = f"""
You are role-playing a realistic caregiver in a paediatric history-taking practice conversation.

This is a standard non-customized practice chatbot.
Do not behave like an assessor, tutor, examiner, or preceptor.

KNOWN FACTS:
- Caregiver name: {case_data.get("caregiver_name")}
- Caregiver role: {case_data.get("caregiver_role")}
- Caregiver occupation: {case_data.get("caregiver_occupation")}
- Child name: {case_data.get("child_name")}
- Child age: {case_data.get("child_age")}
- Child sex: {case_data.get("child_sex")}
- Presenting complaint: {case_data.get("presenting_complaint")}
- Siblings: {case_data.get("siblings")}
- Residence: {case_data.get("residence")}
- Birth place: {case_data.get("birth_place")}
- Household structure: {case_data.get("household_structure")}
- School/daycare: {case_data.get("school_or_daycare")}
- Hidden case summary: {case_data.get("case_summary")}

RULES:
- Stay in caregiver role only.
- Start naturally with this opening line:
  "{case_data.get("opening_line")}"
- Do not repeat the full opening line later unless directly asked who you are.
- Do not ask the student any questions.
- Do not guide the student.
- Do not provide feedback unless explicitly asked to give feedback at the end.
- Do not mention rubrics, scoring, grades, diagnosis, or differentials unless the student directly asks what you were told.
- Answer naturally, briefly, and realistically.
- Do not volunteer the whole history at once.
- Only reveal information when asked.
- Use simple caregiver language, not textbook language.
- Keep answers internally consistent with the hidden case summary.
- If the student's wording is vague or unclear, ask briefly for clarification.
- Do not move into preceptor mode.
- If the student says they are done, ask:
  "{NON_CUSTOMIZED_FEEDBACK_QUESTION}"
- If they say yes, give brief general feedback on the interaction like a normal helpful chatbot.
- If they say no, end politely.
""".strip()

    if optional_instruction.strip():
        prompt += f"\n\nAdditional student instruction:\n{optional_instruction.strip()}"

    return prompt


def caregiver_reply_from_messages(messages, caregiver_system_prompt):
    response = client.responses.create(
        model="gpt-4.1-mini",
        instructions=caregiver_system_prompt,
        input=messages,
    )
    return response.output_text.strip()


def generate_generic_feedback(messages):
    transcript = transcript_from_messages(messages)

    prompt = f"""
You are a helpful clinical tutor.

Give brief general feedback on this paediatric history-taking interaction.

Focus on:
- two or three strengths
- two or three areas for improvement

Do NOT use any rubric.
Do NOT score.
Do NOT grade.
Keep it concise, practical, and supportive.

Transcript:
{transcript}
"""

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt,
    )
    return response.output_text.strip()


def normalize_assessment_payload(data: dict, case_data: dict | None = None) -> dict:
    if not isinstance(data, dict):
        data = {"overall_feedback": str(data)}

    grade = coerce_grade(data.get("grade"))
    if grade is None:
        grade = score_to_grade(data.get("final_score_out_of_100", 0))

    grade_label = str(data.get("grade_label", "")).strip() or GRADE_LABELS.get(grade, "Competent")

    diagnosis = (
        data.get("diagnosis")
        or data.get("true_case_diagnosis")
        or (case_data.get("expected_diagnosis") if case_data else None)
    )

    differentials = data.get("important_expected_differentials")
    if not isinstance(differentials, list):
        differentials = case_data.get("expected_differentials", []) if case_data else []

    strengths = data.get("strengths", [])
    if not isinstance(strengths, list):
        strengths = [str(strengths)]

    missed = data.get("missed_opportunities", [])
    if not isinstance(missed, list):
        missed = [str(missed)]

    missed_history = data.get("key_missed_history_questions", [])
    if not isinstance(missed_history, list):
        missed_history = [str(missed_history)]

    section_feedback = data.get("section_feedback", [])
    if not isinstance(section_feedback, list):
        section_feedback = []

    return {
        "grade": grade,
        "grade_label": grade_label,
        "diagnosis": diagnosis,
        "important_expected_differentials": differentials,
        "key_missed_history_questions": missed_history,
        "strengths": strengths,
        "missed_opportunities": missed,
        "overall_feedback": data.get("overall_feedback", ""),
        "case_summary": data.get("case_summary", ""),
        "section_feedback": section_feedback,
        "scores": data.get("scores", {}),
    }


def insufficient_interaction_feedback_json(case_data):
    diagnosis = case_data.get("expected_diagnosis") if case_data else None
    differentials = case_data.get("expected_differentials", []) if case_data else []

    return {
        "grade": 1,
        "grade_label": GRADE_LABELS[1],
        "diagnosis": diagnosis,
        "important_expected_differentials": differentials,
        "key_missed_history_questions": [],
        "strengths": [
            "No assessable strengths could be identified because there was insufficient student interaction."
        ],
        "missed_opportunities": [
            "Complete the history-taking interaction before requesting assessment."
        ],
        "overall_feedback": (
            "No valid assessment was possible because there was insufficient interaction to judge the "
            "student's history-taking or diagnostic reasoning."
        ),
        "case_summary": "Insufficient interaction to generate a valid assessment.",
        "section_feedback": [],
    }


def call_assessment(messages, detailed: bool = False):
    case_data = st.session_state.case_data

    if st.session_state.study_group == NON_CUSTOMIZED_GROUP:
        return {
            "grade": None,
            "grade_label": "",
            "diagnosis": None,
            "important_expected_differentials": [],
            "key_missed_history_questions": [],
            "strengths": [],
            "missed_opportunities": [],
            "overall_feedback": "This study arm does not include automated rubric-based feedback.",
            "case_summary": "",
            "section_feedback": [],
        }

    if not case_data:
        return {
            "grade": 1,
            "grade_label": GRADE_LABELS[1],
            "diagnosis": None,
            "important_expected_differentials": [],
            "key_missed_history_questions": [],
            "strengths": [],
            "missed_opportunities": [
                "The session metadata was incomplete, so the app could not reconstruct the case for assessment."
            ],
            "overall_feedback": "Assessment could not run because the case metadata was missing after import.",
            "case_summary": "The transcript was imported, but the hidden case data could not be restored for assessment.",
            "section_feedback": [],
        }

    if not has_meaningful_interaction(messages):
        return insufficient_interaction_feedback_json(case_data)

    transcript = transcript_from_messages(messages)
    assessment_prompt = build_assessor_system_prompt(case_data, detailed=detailed)

    prompt = f"""
Assess this paediatric history-taking transcript.

Transcript:
{transcript}
"""

    response = client.responses.create(
        model="gpt-4.1-mini",
        instructions=assessment_prompt,
        input=prompt,
    )

    text = response.output_text.strip()

    try:
        parsed = json.loads(text)
        return normalize_assessment_payload(parsed, case_data)
    except Exception:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                parsed = json.loads(match.group(0))
                return normalize_assessment_payload(parsed, case_data)
            except Exception:
                pass

    return normalize_assessment_payload(
        {
            "grade": 1,
            "grade_label": GRADE_LABELS[1],
            "diagnosis": case_data.get("expected_diagnosis"),
            "important_expected_differentials": case_data.get("expected_differentials", []),
            "key_missed_history_questions": [],
            "strengths": [],
            "missed_opportunities": [],
            "overall_feedback": text,
            "case_summary": "Assessment could not be parsed cleanly, but feedback was generated.",
        },
        case_data,
    )


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

    return {"messages": messages, "raw_payload": data}, None


def build_voice_url(session_id: str):
    query = {
        "age_group": st.session_state.resolved_age,
        "system": st.session_state.resolved_system,
        "caregiver_name": st.session_state.case_data["caregiver_name"],
        "caregiver_gender": st.session_state.case_data["caregiver_gender"],
        "caregiver_role": st.session_state.case_data["caregiver_role"],
        "child_name": st.session_state.case_data["child_name"],
        "child_age": st.session_state.case_data["child_age"],
        "child_sex": st.session_state.case_data["child_sex"],
        "presenting_complaint": st.session_state.case_data["presenting_complaint"],
        "case_summary": st.session_state.case_data["case_summary"],
        "opening_line": st.session_state.case_data["opening_line"],
        "siblings": st.session_state.case_data["siblings"],
        "residence": st.session_state.case_data["residence"],
        "birth_place": st.session_state.case_data["birth_place"],
        "household_structure": st.session_state.case_data["household_structure"],
        "school_or_daycare": st.session_state.case_data["school_or_daycare"],
        "caregiver_occupation": st.session_state.case_data["caregiver_occupation"],
        "case_data_json": json.dumps(make_json_safe(st.session_state.case_data)),
        "session_id": session_id,
        "study_number": st.session_state.study_number,
        "interaction_mode": st.session_state.active_mode,
        "study_group": st.session_state.study_group,
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
    st.session_state.brief_assessment_generated = None
    st.session_state.detailed_assessment_generated = None
    st.session_state.generic_feedback = None
    st.session_state.mode = "caregiver"
    st.session_state.last_voice_import_status = None
    st.session_state.text_phase = "caregiver"
    st.session_state.case_started_at = None
    st.session_state.case_ended_at = None
    st.session_state.reflection_text = ""
    st.session_state.show_reflection_box = False
    st.session_state.raw_voice_payload = None
    st.session_state.resolved_age = None
    st.session_state.resolved_system = None
    st.session_state.transcript_download_name = None
    st.session_state.active_mode = None
    st.session_state.caregiver_system_prompt = ""
    st.session_state.assessor_schema = {}
    st.session_state.study_group = CUSTOMIZED_GROUP
    st.session_state.non_custom_instruction = ""


def apply_imported_messages(imported_obj, session_id=None, status_message="Voice transcript imported automatically."):
    imported_messages = imported_obj["messages"]
    st.session_state.messages = imported_messages
    st.session_state.raw_voice_payload = imported_obj.get("raw_payload")
    st.session_state.brief_assessment_generated = None
    st.session_state.detailed_assessment_generated = None
    st.session_state.generic_feedback = None

    raw_payload = imported_obj.get("raw_payload") or {}
    st.session_state.case_started_at = raw_payload.get("started_at") or st.session_state.case_started_at
    st.session_state.case_ended_at = raw_payload.get("ended_at") or now_iso()

    if raw_payload.get("age_group"):
        st.session_state.resolved_age = raw_payload.get("age_group")
    if raw_payload.get("system"):
        st.session_state.resolved_system = raw_payload.get("system")
    if raw_payload.get("study_number"):
        st.session_state.study_number = raw_payload.get("study_number")

    imported_group = raw_payload.get("study_group")
    if imported_group in {CUSTOMIZED_GROUP, NON_CUSTOMIZED_GROUP}:
        st.session_state.study_group = imported_group
    else:
        st.session_state.study_group = get_study_group(st.session_state.study_number)

    case_data_json = raw_payload.get("case_data_json")
    if case_data_json:
        try:
            st.session_state.case_data = json.loads(case_data_json)
            if st.session_state.study_group == CUSTOMIZED_GROUP:
                st.session_state.caregiver_system_prompt = build_history_taking_system_prompt(st.session_state.case_data)
                st.session_state.assessor_schema = build_assessor_schema(st.session_state.case_data)
            else:
                optional_instruction = st.session_state.get("non_custom_instruction", "")
                st.session_state.caregiver_system_prompt = build_non_customized_caregiver_prompt(
                    st.session_state.case_data,
                    optional_instruction=optional_instruction,
                )
                st.session_state.assessor_schema = {}
        except Exception:
            st.session_state.case_data = None

    if session_id:
        st.session_state.current_session_id = session_id

    if st.session_state.study_group == NON_CUSTOMIZED_GROUP:
        st.session_state.presentation_done = True
        st.session_state.mode = "post_presentation"
        st.session_state.text_phase = "post_presentation"
    else:
        st.session_state.presentation_done = looks_like_voice_session_complete(imported_messages)
        st.session_state.mode = "post_presentation" if st.session_state.presentation_done else "caregiver"
        st.session_state.text_phase = "post_presentation" if st.session_state.presentation_done else "caregiver"

    st.session_state.active_mode = "Realtime voice"

    set_status("success", status_message)


def build_transcript_text():
    header = [
        f"Study number: {st.session_state.study_number or 'Not recorded'}",
        f"Study group: {st.session_state.study_group or 'Not recorded'}",
        f"Start {format_hhmm(st.session_state.case_started_at)}",
        f"End {format_hhmm(st.session_state.case_ended_at)}",
        f"Duration {format_duration(st.session_state.case_started_at, st.session_state.case_ended_at)}",
        "",
        "Transcript",
        "----------",
        transcript_from_messages(st.session_state.messages),
    ]
    return "\n".join(header)


def build_reflection_text():
    lines = [
        f"Study number: {st.session_state.study_number or 'Not recorded'}",
        f"Study group: {st.session_state.study_group or 'Not recorded'}",
        f"Recorded at: {now_iso()}",
        "",
        "Reflection",
        "----------",
        st.session_state.reflection_text.strip(),
    ]
    return "\n".join(lines)


def render_assessment_json(data: dict, detailed: bool = False):
    if not isinstance(data, dict):
        st.write(data)
        return

    payload = normalize_assessment_payload(data, st.session_state.case_data)

    grade = payload.get("grade")
    grade_label = payload.get("grade_label", "")
    if grade is not None:
        st.markdown(f"**Grade:** {grade} – {grade_label}")

    diagnosis = payload.get("diagnosis")
    if diagnosis:
        st.markdown("**Diagnosis**")
        st.write(diagnosis)

    diffs = payload.get("important_expected_differentials", [])
    if diffs:
        st.markdown("**Important differential diagnoses for this case**")
        for item in diffs:
            st.write(f"- {item}")

    missed_history = payload.get("key_missed_history_questions", [])
    if missed_history:
        st.markdown("**Key missed history questions**")
        for item in missed_history:
            st.write(f"- {item}")

    case_summary = payload.get("case_summary")
    if case_summary:
        st.markdown("**Case summary**")
        st.write(case_summary)

    strengths = payload.get("strengths", [])
    if strengths:
        st.markdown("**Strengths**")
        for item in strengths:
            st.write(f"- {item}")

    missed = payload.get("missed_opportunities", [])
    if missed:
        st.markdown("**Missed opportunities**")
        for item in missed:
            st.write(f"- {item}")

    if detailed:
        section_feedback = payload.get("section_feedback", [])
        if section_feedback:
            st.markdown("**Section-by-section feedback**")
            for item in section_feedback:
                if isinstance(item, dict):
                    label = item.get("label", "Section")
                    comment = item.get("comment", "")
                    st.write(f"**{label}:** {comment}")
                else:
                    st.write(f"- {item}")

        scores = payload.get("scores", {})
        if scores:
            st.markdown("**Additional rubric comments**")
            for key, value in scores.items():
                label = key.replace("_", " ").title()
                reasoning = value.get("reasoning", "") if isinstance(value, dict) else ""
                st.write(f"**{label}:**")
                if reasoning:
                    st.write(reasoning)

    overall = payload.get("overall_feedback")
    if overall:
        st.markdown("**Overall feedback**")
        st.write(overall)


def run_text_state_machine(user_text: str):
    if st.session_state.study_group == NON_CUSTOMIZED_GROUP:
        phase = st.session_state.text_phase

        if phase == "caregiver":
            if looks_like_finished_history(user_text):
                st.session_state.text_phase = "await_non_custom_feedback_choice"
                return NON_CUSTOMIZED_FEEDBACK_QUESTION

            if looks_like_greeting_only(user_text):
                return "Hello, doctor."

            return caregiver_reply_from_messages(st.session_state.messages, st.session_state.caregiver_system_prompt)

        if phase == "await_non_custom_feedback_choice":
            if is_yes(user_text):
                st.session_state.text_phase = "post_presentation"
                st.session_state.presentation_done = True
                st.session_state.mode = "post_presentation"
                st.session_state.case_ended_at = now_iso()
                st.session_state.generic_feedback = generate_generic_feedback(st.session_state.messages)
                return "Here is some general feedback on the interaction."
            if is_no(user_text):
                st.session_state.text_phase = "post_presentation"
                st.session_state.presentation_done = True
                st.session_state.mode = "post_presentation"
                st.session_state.case_ended_at = now_iso()
                return "Okay. Session complete."
            return "Please answer yes or no."

        return "Conversation complete."

    phase = st.session_state.text_phase

    if phase == "caregiver":
        if looks_like_finished_history(user_text):
            st.session_state.text_phase = "await_preceptor_choice"
            return TEXT_PRECEPTOR_INVITE

        if looks_like_greeting_only(user_text):
            return "Good afternoon, doctor." if "afternoon" in normalize_text(user_text) else "Hello, doctor."

        return caregiver_reply_from_messages(st.session_state.messages, st.session_state.caregiver_system_prompt)

    if phase == "await_preceptor_choice":
        if is_yes(user_text):
            st.session_state.text_phase = "await_summary_answer"
            return TEXT_SUMMARY_QUESTION
        if is_no(user_text):
            st.session_state.text_phase = "caregiver"
            return "Okay, we can continue with the history."
        return "Please answer yes or no."

    if phase == "await_summary_answer":
        if looks_like_history_question(user_text):
            st.session_state.text_phase = "caregiver"
            caregiver_text = caregiver_reply_from_messages(
                st.session_state.messages,
                st.session_state.caregiver_system_prompt,
            )
            return caregiver_text

        if not looks_like_summary_response(user_text):
            return (
                "That seems more like another question or an incomplete summary. "
                "Please summarise the case briefly in one or two sentences, or continue the history first."
            )

        st.session_state.text_phase = "await_diagnosis_answer"
        return TEXT_DIAGNOSIS_QUESTION

    if phase == "await_diagnosis_answer":
        if looks_like_history_question(user_text):
            st.session_state.text_phase = "caregiver"
            caregiver_text = caregiver_reply_from_messages(
                st.session_state.messages,
                st.session_state.caregiver_system_prompt,
            )
            return caregiver_text

        if not looks_like_diagnosis_response(user_text):
            return (
                "That does not yet look like a diagnosis. "
                "Please state your single most likely diagnosis, or return to the history if you need more information."
            )

        st.session_state.text_phase = "await_differentials_answer"
        return TEXT_DIFFERENTIALS_QUESTION

    if phase == "await_differentials_answer":
        if looks_like_history_question(user_text):
            st.session_state.text_phase = "caregiver"
            caregiver_text = caregiver_reply_from_messages(
                st.session_state.messages,
                st.session_state.caregiver_system_prompt,
            )
            return caregiver_text

        if not looks_like_differentials_response(user_text):
            return (
                "Please list your main differential diagnoses, or continue the history if you need more information."
            )

        st.session_state.text_phase = "await_final_confirmation"
        return TEXT_END_CONFIRM

    if phase == "await_final_confirmation":
        if looks_like_history_question(user_text):
            st.session_state.text_phase = "caregiver"
            caregiver_text = caregiver_reply_from_messages(
                st.session_state.messages,
                st.session_state.caregiver_system_prompt,
            )
            return caregiver_text

        if is_yes(user_text):
            st.session_state.text_phase = "post_presentation"
            st.session_state.presentation_done = True
            st.session_state.mode = "post_presentation"
            st.session_state.case_ended_at = now_iso()
            return TEXT_FINAL_LINE
        if is_no(user_text):
            st.session_state.text_phase = "await_differentials_answer"
            return "Okay, please continue with your differential diagnoses."
        return "Please answer yes or no."

    return "Conversation complete."


# =========================
# Session state init
# =========================
defaults = {
    "messages": [],
    "case_data": None,
    "current_session_id": None,
    "presentation_done": False,
    "brief_assessment_generated": None,
    "detailed_assessment_generated": None,
    "generic_feedback": None,
    "mode": "caregiver",
    "text_phase": "caregiver",
    "selected_mode": "Text only",
    "selected_age": "Random",
    "selected_system": "Random",
    "selected_study_number": STUDY_NUMBER_OPTIONS[0],
    "active_mode": None,
    "study_number": None,
    "study_group": CUSTOMIZED_GROUP,
    "last_voice_import_status": None,
    "study_number_confirmed": False,
    "case_started_at": None,
    "case_ended_at": None,
    "reflection_text": "",
    "show_reflection_box": False,
    "raw_voice_payload": None,
    "resolved_age": None,
    "resolved_system": None,
    "transcript_download_name": None,
    "caregiver_system_prompt": "",
    "assessor_schema": {},
    "non_custom_instruction": "",
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# =========================
# Query params recovery
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
    imported_obj, import_error = import_voice_transcript(st.session_state.current_session_id)

    if import_error:
        set_status("warning", import_error)
    else:
        apply_imported_messages(
            imported_obj,
            session_id=st.session_state.current_session_id,
            status_message="Voice transcript imported automatically.",
        )

        if auto_feedback_flag == "1" and st.session_state.study_group == CUSTOMIZED_GROUP:
            with st.spinner("Generating brief feedback..."):
                st.session_state.brief_assessment_generated = call_assessment(imported_obj["messages"], detailed=False)
                st.session_state.presentation_done = True
                st.session_state.mode = "post_presentation"
                st.session_state.text_phase = "post_presentation"
                st.session_state.active_mode = "Realtime voice"
                if not st.session_state.case_ended_at:
                    st.session_state.case_ended_at = now_iso()

    clear_return_query_params()
    st.rerun()

# =========================
# Header
# =========================
st.title(APP_TITLE)
st.info(WELCOME_TEXT)

# =========================
# Setup section
# =========================
if not st.session_state.case_data and not st.session_state.messages:
    st.markdown("### Session setup")

    selected_study_number = st.selectbox(
        "Choose study number",
        STUDY_NUMBER_OPTIONS,
        key="selected_study_number",
    )

    study_group_preview = get_study_group(selected_study_number)

    if selected_study_number != "Please select study number":
        st.markdown(f"**Study number selected:** {selected_study_number}")
        st.markdown(
            f"**Study arm:** {'Customized bot' if study_group_preview == CUSTOMIZED_GROUP else 'Non-customized bot'}"
        )
        confirm_checkbox = st.checkbox(
            "Please confirm this is your study number",
            key="study_number_confirm_checkbox",
        )
        st.session_state.study_number_confirmed = bool(confirm_checkbox)
    else:
        st.session_state.study_number_confirmed = False

    st.markdown("**Choose interaction mode**")
    selected_mode = st.radio(
        "Choose interaction mode",
        VISIBLE_INTERACTION_MODES,
        key="selected_mode",
        label_visibility="collapsed",
    )

    if study_group_preview == CUSTOMIZED_GROUP:
        st.markdown("**Choose age group**")
        selected_age = st.radio(
            "Choose age group",
            VISIBLE_AGE_OPTIONS,
            key="selected_age",
            label_visibility="collapsed",
        )

        st.markdown("**Choose system**")
        selected_system = st.radio(
            "Choose system",
            VISIBLE_SYSTEM_OPTIONS,
            key="selected_system",
            label_visibility="collapsed",
        )

        non_custom_instruction = ""
    else:
        selected_age = "Random"
        selected_system = "Random"

        st.info("A random case will be generated for this study arm.")

        non_custom_instruction = st.text_input(
            "Optional instruction",
            value=st.session_state.non_custom_instruction,
            key="non_custom_instruction",
            help="You can ask the chatbot to switch systems or caregiver, should you wish.",
        )

        st.caption("You can ask the chatbot to switch systems or caregiver, should you wish.")

    if st.button("Start new case", use_container_width=True):
        if selected_study_number == "Please select study number":
            st.warning("Please select a study number first.")
        elif not st.session_state.study_number_confirmed:
            st.warning("Please confirm the study number before starting.")
        else:
            try:
                study_group = get_study_group(selected_study_number)

                if study_group == CUSTOMIZED_GROUP:
                    resolved_age, resolved_system = resolve_random_selection(selected_age, selected_system)
                else:
                    resolved_age, resolved_system = resolve_random_selection("Random", "Random")

                case_data = choose_case(requested_system=resolved_system)

                if study_group == CUSTOMIZED_GROUP:
                    caregiver_system_prompt = build_history_taking_system_prompt(case_data)
                    assessor_schema = build_assessor_schema(case_data)
                else:
                    caregiver_system_prompt = build_non_customized_caregiver_prompt(
                        case_data,
                        optional_instruction=non_custom_instruction,
                    )
                    assessor_schema = {}

                session_id = str(uuid.uuid4())

                reset_case_state()
                st.session_state.case_data = case_data
                st.session_state.caregiver_system_prompt = caregiver_system_prompt
                st.session_state.assessor_schema = assessor_schema
                st.session_state.current_session_id = session_id
                st.session_state.case_started_at = now_iso()
                st.session_state.study_number = selected_study_number
                st.session_state.study_group = study_group
                st.session_state.resolved_age = resolved_age
                st.session_state.resolved_system = resolved_system
                st.session_state.transcript_download_name = f"transcript_{selected_study_number}_{session_id}.txt"
                st.session_state.active_mode = selected_mode
                st.session_state.non_custom_instruction = non_custom_instruction

                if selected_mode == "Text only":
                    st.session_state.messages = [
                        {"role": "assistant", "content": case_data["opening_line"]}
                    ]

                st.rerun()
            except Exception as e:
                st.error(f"Could not generate case: {e}")

# =========================
# Voice mode
# =========================
if (
    st.session_state.case_data
    and st.session_state.active_mode == "Realtime voice"
    and not st.session_state.messages
):
    st.markdown("### Realtime voice mode")
    voice_url = build_voice_url(st.session_state.current_session_id)
    st.link_button("Open realtime voice case", voice_url, use_container_width=True)
    st.caption(
        "The voice case opens in a new tab. After the session ends and the student clicks Stop Session, "
        "the app should return here and import the transcript automatically."
    )

# =========================
# Status
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
# Study arm display
# =========================
if st.session_state.case_data:
    st.caption(
        f"Study arm: {'Customized bot' if st.session_state.study_group == CUSTOMIZED_GROUP else 'Non-customized bot'}"
    )

# =========================
# Conversation display
# =========================
show_live_transcript = (
    st.session_state.case_data
    and not st.session_state.presentation_done
    and st.session_state.active_mode == "Text only"
)

if show_live_transcript:
    st.markdown("### Conversation")
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.write(m["content"])

# =========================
# Non-customized text session end button
# =========================
if (
    st.session_state.case_data
    and st.session_state.active_mode == "Text only"
    and st.session_state.study_group == NON_CUSTOMIZED_GROUP
    and not st.session_state.presentation_done
):
    st.caption("When you are finished, type that you are done. The chatbot will then ask if you would like feedback.")

# =========================
# Text mode
# =========================
if (
    st.session_state.case_data
    and st.session_state.active_mode == "Text only"
    and st.session_state.mode != "post_presentation"
):
    if prompt := st.chat_input("Type your response…"):
        st.session_state.messages.append({"role": "user", "content": prompt})

        assistant_text = run_text_state_machine(prompt)
        st.session_state.messages.append({"role": "assistant", "content": assistant_text})

        if (
            st.session_state.study_group == CUSTOMIZED_GROUP
            and normalize_text(assistant_text) == normalize_text(TEXT_FINAL_LINE)
        ):
            with st.spinner("Generating brief feedback..."):
                st.session_state.brief_assessment_generated = call_assessment(
                    st.session_state.messages,
                    detailed=False,
                )

        st.rerun()

elif not st.session_state.case_data and not st.session_state.messages and not st.session_state.current_session_id:
    st.info("Set up and start a case to begin.")
elif st.session_state.mode == "post_presentation":
    st.info("Conversation complete.")
elif st.session_state.messages and not st.session_state.case_data:
    st.info("Imported voice transcript loaded.")

# =========================
# Feedback
# =========================
if st.session_state.presentation_done and st.session_state.study_group == CUSTOMIZED_GROUP:
    st.markdown("### Feedback")

    if not st.session_state.brief_assessment_generated:
        if st.button("Generate brief feedback", use_container_width=True):
            with st.spinner("Generating brief feedback..."):
                st.session_state.brief_assessment_generated = call_assessment(
                    st.session_state.messages,
                    detailed=False,
                )
                if not st.session_state.case_ended_at:
                    st.session_state.case_ended_at = now_iso()
                st.rerun()

    if st.session_state.brief_assessment_generated:
        render_assessment_json(st.session_state.brief_assessment_generated, detailed=False)

        if not st.session_state.detailed_assessment_generated:
            if st.button("Show detailed feedback", use_container_width=True):
                with st.spinner("Generating detailed feedback..."):
                    st.session_state.detailed_assessment_generated = call_assessment(
                        st.session_state.messages,
                        detailed=True,
                    )
                    if not st.session_state.case_ended_at:
                        st.session_state.case_ended_at = now_iso()
                    st.rerun()

        if st.session_state.detailed_assessment_generated:
            with st.expander("Detailed feedback", expanded=True):
                render_assessment_json(st.session_state.detailed_assessment_generated, detailed=True)

# =========================
# Non-customized completion note and feedback
# =========================
if st.session_state.presentation_done and st.session_state.study_group == NON_CUSTOMIZED_GROUP:
    st.markdown("### Session complete")

    if st.session_state.generic_feedback:
        st.markdown("### Feedback")
        st.write(st.session_state.generic_feedback)
    else:
        st.info("No feedback selected for this session.")

# =========================
# Transcript tools
# =========================
if st.session_state.presentation_done and st.session_state.messages:
    st.markdown("### Transcript")

    with st.expander("View transcript", expanded=False):
        for m in st.session_state.messages:
            speaker = "Student" if m["role"] == "user" else "Bot"
            st.write(f"**{speaker}:** {m['content']}")

    st.download_button(
        label="Download transcript",
        data=build_transcript_text(),
        file_name=st.session_state.transcript_download_name or "transcript.txt",
        mime="text/plain",
        use_container_width=True,
    )

# =========================
# Reflection
# =========================
if st.session_state.presentation_done:
    st.markdown("### Reflection")

    if not st.session_state.show_reflection_box:
        if st.button("Are there any reflections you'd like to record?", use_container_width=True):
            st.session_state.show_reflection_box = True
            st.rerun()

    if st.session_state.show_reflection_box:
        st.session_state.reflection_text = st.text_area(
            "Record your reflection here",
            value=st.session_state.reflection_text,
            height=180,
        )

        if st.session_state.reflection_text.strip():
            st.download_button(
                label="Download reflection",
                data=build_reflection_text(),
                file_name=f"reflection_{st.session_state.study_number}_{st.session_state.current_session_id}.txt",
                mime="text/plain",
                use_container_width=True,
            )


