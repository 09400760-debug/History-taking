import json
import random
import re
import urllib.parse
import uuid
from datetime import datetime

import requests
import streamlit as st
from openai import OpenAI

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

    [data-baseweb="select"] > div {
        background: #ffffff !important;
        color: #111111 !important;
    }

    input, textarea {
        background: #ffffff !important;
        color: #111111 !important;
    }

    section[data-testid="stSidebar"] {
        background: #ffffff !important;
    }

    @media (max-width: 768px) {
        html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"], .main {
            background: #ffffff !important;
        }

        .main .block-container {
            padding-top: 0.5rem;
            padding-left: 0.9rem;
            padding-right: 0.9rem;
            padding-bottom: 2rem;
            background: #ffffff !important;
        }
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
    "Select your study number, choose how you would like to interact, then choose an age group "
    "and system or let the bot surprise you with a random case."
)

TEXT_PRECEPTOR_INVITE = "Would you like to move to preceptor mode?"
TEXT_SUMMARY_QUESTION = "Please summarise the case briefly in one or two sentences."
TEXT_DIAGNOSIS_QUESTION = "What is your most likely diagnosis?"
TEXT_DIFFERENTIALS_QUESTION = "What are your main differential diagnoses?"
TEXT_FINAL_LINE = "Thank you. I will now generate your feedback."

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
    "Haematological",
    "Musculoskeletal",
    "Neurological",
    "Neurodevelopment",
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
    "Respiratory",
    "Cardiovascular",
    "Gastrointestinal",
    "Haematological",
    "Musculoskeletal",
    "Neurological",
    "Neurodevelopment",
    "Endocrine",
    "Renal",
    "Infectious diseases",
    "Nutrition",
    "Development",
    "Neonatology",
    "Dermatology",
    "Rheumatological",
    "Immunological",
]

STUDY_NUMBER_MAX = 126
STUDY_NUMBER_OPTIONS = ["Please select study number"] + [
    f"1-{i:03d}" for i in range(1, STUDY_NUMBER_MAX + 1)
]

FEMALE_ROLES = {"mother", "grandmother", "aunt", "female guardian", "guardian"}
MALE_ROLES = {"father", "grandfather", "uncle", "male guardian", "guardian"}

# =========================
# Rubric summaries
# =========================
BRIEF_RUBRIC_TEXT = """
Wits Paediatrics history-taking rubric (strict but constructive)

Assess the student on:
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
12. Preceptor stage: summary, diagnosis, and differential diagnoses

Important:
- Use transcript evidence only.
- Do not assume the student asked something if it is not clearly present.
- Reward specificity and logical flow.
- Keep feedback concise and focused on the highest-yield learning points.
- Give one overall performance grade from 1 to 5 using:
  1 = Needs significant development
  2 = Emerging competence
  3 = Meets expectations
  4 = Strong performance
  5 = Outstanding proficiency
"""

DETAILED_RUBRIC_TEXT = """
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
12. Preceptor stage: summary, diagnosis, and differential diagnoses

Important strict principles:
- Do not mark generously.
- Reward specificity and follow-up questions.
- Broad vague questions should score lower unless followed by detail.
- Do not assume a question was asked if it is not clearly present in the transcript.
- If the learner misses important lines of enquiry, count that against them.
- If the learner asks closed questions only, note the weakness.
- Use transcript evidence only.
- Give one overall performance grade from 1 to 5 using:
  1 = Needs significant development
  2 = Emerging competence
  3 = Meets expectations
  4 = Strong performance
  5 = Outstanding proficiency
"""

# =========================
# Case generator prompt
# =========================
CASE_GENERATOR_PROMPT = """
You are generating a paediatric practice case for a 5th-year medical student in South Africa.

Return ONLY valid JSON.
Do not include markdown.
Do not include explanation text.
Do not include code fences.

Use exactly these keys:
- caregiver_name
- caregiver_gender
- caregiver_role
- child_name
- child_age
- child_sex
- presenting_complaint
- case_summary
- opening_line
- siblings
- residence
- birth_place
- household_structure
- school_or_daycare
- caregiver_occupation

Rules:
- South African paediatric context
- realistic caregiver language
- common paediatric problem
- keep case_summary hidden and concise but clinically useful
- opening_line must be a brief natural caregiver greeting that introduces the caregiver and child
- VARY caregiver and child names across cases
- Avoid repeatedly using the same names such as Thabo, Sipho, Nomsa, Lindiwe unless genuinely needed
- Use a wide range of realistic South African names from different backgrounds and languages
- caregiver_gender must be exactly "female" or "male"
- caregiver_role must match the caregiver_gender naturally
- If caregiver_gender is female, use a female caregiver name and a matching female role
- If caregiver_gender is male, use a male caregiver name and a matching male role
- Child names must vary naturally
- Do not use the same caregiver name and child name together repeatedly
- Make the presenting complaint and summary fit the age group and system requested
- Populate the social/background fields realistically:
  - siblings should be a short natural sentence, e.g. "He has one older sister, Amahle, who is 6 years old."
  - residence should say where they live in a realistic South African way
  - birth_place should be a realistic place of birth or hospital
  - household_structure should say who lives at home
  - school_or_daycare should say creche/daycare/school status or "not yet in school"
  - caregiver_occupation should be simple and realistic
- The background facts must be internally consistent and easy for a caregiver to know.
"""

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
        "that is complete",
        "that's complete",
        "thats complete",
        "history complete",
        "we are done",
        "i am complete",
        "history is complete",
        "can we move to preceptor",
        "can we switch to preceptor",
        "move to preceptor",
        "switch to preceptor",
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

    for line in reversed(assistant_lines[-10:]):
        if any(hint in line for hint in VOICE_COMPLETION_HINTS):
            return True

    return False


def looks_like_greeting_only(text: str) -> bool:
    t = normalize_text(text)
    greetings = {
        "hello", "hi", "hey", "good morning", "good afternoon", "good evening",
        "hello there", "hi there"
    }
    return t in greetings


def resolve_random_selection(selected_age: str, selected_system: str):
    resolved_age = selected_age
    resolved_system = selected_system

    if selected_age == "Random":
        resolved_age = random.choice(RANDOM_AGE_POOL)

    if selected_system == "Random":
        resolved_system = random.choice(RANDOM_SYSTEM_POOL)

    return resolved_age, resolved_system


def sanitize_case_data(data: dict) -> dict:
    caregiver_gender = str(data.get("caregiver_gender", "female")).strip().lower()
    caregiver_role = str(data.get("caregiver_role", "")).strip().lower()
    caregiver_name = str(data.get("caregiver_name", "")).strip()
    child_name = str(data.get("child_name", "")).strip()
    child_age = str(data.get("child_age", "")).strip()
    child_sex = str(data.get("child_sex", "")).strip().lower()
    presenting_complaint = str(data.get("presenting_complaint", "")).strip()
    case_summary = str(data.get("case_summary", "")).strip()
    opening_line = str(data.get("opening_line", "")).strip()

    siblings = str(data.get("siblings", "")).strip()
    residence = str(data.get("residence", "")).strip()
    birth_place = str(data.get("birth_place", "")).strip()
    household_structure = str(data.get("household_structure", "")).strip()
    school_or_daycare = str(data.get("school_or_daycare", "")).strip()
    caregiver_occupation = str(data.get("caregiver_occupation", "")).strip()

    if caregiver_gender not in {"female", "male"}:
        caregiver_gender = "female"

    if caregiver_gender == "female" and caregiver_role not in FEMALE_ROLES:
        caregiver_role = "mother"
    if caregiver_gender == "male" and caregiver_role not in MALE_ROLES:
        caregiver_role = "father"

    if not caregiver_name:
        caregiver_name = "Zanele" if caregiver_gender == "female" else "Sibusiso"
    if not child_name:
        child_name = "Musa"
    if not child_age:
        child_age = "3 years"
    if child_sex not in {"male", "female"}:
        child_sex = "male"
    if not presenting_complaint:
        presenting_complaint = "fever"
    if not case_summary:
        case_summary = f"{child_name} is a child presenting with {presenting_complaint}."
    if not opening_line:
        opening_line = f"Hello doctor, I'm {caregiver_name}, {child_name}'s {caregiver_role}."

    if not siblings:
        siblings = "He has one older sister, Ayanda, who is 6 years old." if child_sex == "male" else "She has one older brother, Luyanda, who is 6 years old."
    if not residence:
        residence = "We live in Soweto with family."
    if not birth_place:
        birth_place = "He was born at Chris Hani Baragwanath Academic Hospital." if child_sex == "male" else "She was born at Chris Hani Baragwanath Academic Hospital."
    if not household_structure:
        household_structure = "At home it is me, the child, and one sibling."
    if not school_or_daycare:
        school_or_daycare = "He goes to crèche during the week." if child_sex == "male" else "She goes to crèche during the week."
    if not caregiver_occupation:
        caregiver_occupation = "I work as a shop assistant."

    data["caregiver_gender"] = caregiver_gender
    data["caregiver_role"] = caregiver_role
    data["caregiver_name"] = caregiver_name
    data["child_name"] = child_name
    data["child_age"] = child_age
    data["child_sex"] = child_sex
    data["presenting_complaint"] = presenting_complaint
    data["case_summary"] = case_summary
    data["opening_line"] = opening_line
    data["siblings"] = siblings
    data["residence"] = residence
    data["birth_place"] = birth_place
    data["household_structure"] = household_structure
    data["school_or_daycare"] = school_or_daycare
    data["caregiver_occupation"] = caregiver_occupation

    return data


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
        "caregiver_gender",
        "caregiver_role",
        "child_name",
        "child_age",
        "child_sex",
        "presenting_complaint",
        "case_summary",
        "opening_line",
        "siblings",
        "residence",
        "birth_place",
        "household_structure",
        "school_or_daycare",
        "caregiver_occupation",
    ]
    for key in required:
        if key not in data:
            raise ValueError(f"Generated case missing key: {key}")

    data = sanitize_case_data(data)
    return data


def build_caregiver_history_instructions(case_data):
    return f"""
You are simulating a realistic caregiver in a paediatric history-taking station.

Hidden medical case summary:
{case_data["case_summary"]}

Known caregiver/background facts that you should know comfortably and consistently:
- Caregiver name: {case_data["caregiver_name"]}
- Caregiver role: {case_data["caregiver_role"]}
- Caregiver occupation: {case_data["caregiver_occupation"]}
- Child name: {case_data["child_name"]}
- Child age: {case_data["child_age"]}
- Child sex: {case_data["child_sex"]}
- Presenting complaint: {case_data["presenting_complaint"]}
- Siblings: {case_data["siblings"]}
- Residence: {case_data["residence"]}
- Birth place: {case_data["birth_place"]}
- Household structure: {case_data["household_structure"]}
- School/daycare: {case_data["school_or_daycare"]}

Rules:
- Stay fully in caregiver role.
- You are not ChatGPT.
- You are not a general assistant.
- Do not break role.
- Do not thank the learner in a generic assistant style.
- Do not say "let me know if you need anything else."
- Do not offer help outside the caregiver role.
- Use English only.
- Use simple, natural, non-medical language.
- Answer only the question that was asked.
- Do not volunteer extra details unless directly asked.
- Being brief does NOT mean being vague or unsure.
- When the learner asks about ordinary caregiver knowledge, answer directly, confidently, and naturally.
- Do not coach the learner.
- Do not ask doctor-like questions.
- Keep your answers internally consistent with the hidden case summary and background facts.
- You should know normal obvious family and social facts about your child and home life.
- If asked about siblings, parents' names, home circumstances, where the child lives, where the child was born, who stays at home, school/daycare, or your work, answer naturally and confidently using the background facts above.
- Do NOT say "I'm not sure" to obvious non-medical facts that a normal caregiver would know.
- Only show uncertainty where it is realistic, such as:
  - medical interpretation or diagnosis
  - exact medical measurements
  - technical medical terms
  - details you genuinely would not have noticed
  - exact timing if not carefully observed
  - information that was never explained to you clearly
- If something is ordinary caregiver knowledge, answer it directly.
- If the learner greets first, greet back briefly as the caregiver.
- Do not immediately give the whole story on a simple greeting alone.
- Never behave like a doctor, receptionist, or assistant.
- Never say: "How can I help you?", "How can I help you and your child today?", "What can I help you with?", "What seems to be the problem today?", or similar clinician-style phrases.
- Never ask the learner a clinical opening question.
- After a simple greeting, reply briefly and wait.
- Good examples:
  "Good afternoon, doctor."
  "Hello, doctor."
  "Good afternoon."
  "Hello doctor."
- If the learner asks broad opening clinical questions like "What brought you in?", "What seems to be the problem?", "Tell me about your child", or "What is the problem with your child?", answer with the main complaint naturally.
- If the learner asks something unclear, ask briefly for clarification.
- If the learner clearly indicates they are finished, respond only with: "{TEXT_PRECEPTOR_INVITE}"
"""


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

    meaningful_turns = [
        msg for msg in student_messages
        if is_meaningful_student_text(msg)
    ]

    total_student_words = sum(
        len([w for w in re.split(r"\s+", msg.strip()) if w])
        for msg in student_messages
    )

    return len(meaningful_turns) >= 2 or total_student_words >= 12


def insufficient_interaction_feedback(detailed: bool = False) -> str:
    if detailed:
        return (
            "Strengths\n"
            "No assessable strengths could be identified because there was insufficient student interaction.\n\n"
            "Priority areas for improvement\n"
            "Complete the history-taking interaction before requesting assessment.\n\n"
            "Missed opportunities\n"
            "The session did not contain enough student questioning or engagement to assess history-taking performance.\n\n"
            "Domain-based scoring comments\n"
            "Scoring was not possible because there was insufficient interaction.\n\n"
            "Overall comment\n"
            "No assessment possible: there was insufficient student interaction to assess this session.\n\n"
            "Overall performance grade (1-5) with label\n"
            "Not assessable - no grade awarded"
        )

    return (
        "Key strengths\n"
        "No assessable strengths could be identified because there was insufficient student interaction.\n\n"
        "Priority improvement points\n"
        "Complete the history-taking interaction before requesting assessment.\n\n"
        "Overall comment\n"
        "No assessment possible: there was insufficient student interaction to assess this session.\n\n"
        "Overall performance grade (1-5) with label\n"
        "Not assessable - no grade awarded"
    )


def call_assessment(messages, detailed: bool = False):
    if not has_meaningful_interaction(messages):
        return insufficient_interaction_feedback(detailed=detailed)

    transcript = transcript_from_messages(messages)
    rubric_text = DETAILED_RUBRIC_TEXT if detailed else BRIEF_RUBRIC_TEXT

    if detailed:
        prompt = f"""
Transcript:
{transcript}

Use this exact order with clear headings:
1. Strengths
2. Priority areas for improvement
3. Missed opportunities
4. Domain-based scoring comments
5. Overall comment
6. Overall performance grade (1-5) with label

Important:
- Put the grade LAST, not first.
"""
    else:
        prompt = f"""
Transcript:
{transcript}

Use this exact order with clear headings:
1. Key strengths
2. Priority improvement points
3. Overall comment
4. Overall performance grade (1-5) with label

Important:
- Keep it concise, specific, and learner-friendly.
- Put the grade LAST, not first.
"""

    instructions = f"""
You are a strict but constructive paediatric preceptor and examiner giving feedback on a student history-taking station.

Use this rubric summary:
{rubric_text}

Rules:
- Base everything only on transcript evidence.
- Do not assume missing history was asked.
- Be honest but supportive.
- Use the 1 to 5 grading scale exactly.
- Follow the requested heading order exactly.
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
        "session_id": session_id,
        "study_number": st.session_state.study_number,
        "interaction_mode": st.session_state.active_mode,
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


def apply_imported_messages(imported_obj, session_id=None, status_message="Voice transcript imported automatically."):
    imported_messages = imported_obj["messages"]
    st.session_state.messages = imported_messages
    st.session_state.raw_voice_payload = imported_obj.get("raw_payload")
    st.session_state.brief_assessment_generated = None
    st.session_state.detailed_assessment_generated = None

    raw_payload = imported_obj.get("raw_payload") or {}
    st.session_state.case_started_at = raw_payload.get("started_at") or st.session_state.case_started_at
    st.session_state.case_ended_at = raw_payload.get("ended_at") or now_iso()

    if raw_payload.get("age_group"):
        st.session_state.resolved_age = raw_payload.get("age_group")
    if raw_payload.get("system"):
        st.session_state.resolved_system = raw_payload.get("system")
    if raw_payload.get("study_number"):
        st.session_state.study_number = raw_payload.get("study_number")

    if session_id:
        st.session_state.current_session_id = session_id

    st.session_state.presentation_done = looks_like_voice_session_complete(imported_messages)
    st.session_state.mode = "post_presentation" if st.session_state.presentation_done else "caregiver"
    st.session_state.text_phase = "post_presentation" if st.session_state.presentation_done else "caregiver"
    st.session_state.active_mode = "Realtime voice"

    set_status("success", status_message)


def build_transcript_text():
    header = [
        f"Study number: {st.session_state.study_number or 'Not recorded'}",
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
        f"Recorded at: {now_iso()}",
        "",
        "Reflection",
        "----------",
        st.session_state.reflection_text.strip(),
    ]
    return "\n".join(lines)


def run_text_state_machine(user_text: str):
    phase = st.session_state.text_phase
    case_data = st.session_state.case_data

    if phase == "caregiver":
        if looks_like_finished_history(user_text):
            st.session_state.text_phase = "await_preceptor_choice"
            return TEXT_PRECEPTOR_INVITE

        if looks_like_greeting_only(user_text):
            return "Good afternoon, doctor." if "afternoon" in normalize_text(user_text) else "Hello, doctor."

        response = client.responses.create(
            model="gpt-4.1-mini",
            instructions=build_caregiver_history_instructions(case_data),
            input=st.session_state.messages,
        )
        return response.output_text.strip()

    if phase == "await_preceptor_choice":
        if is_yes(user_text):
            st.session_state.text_phase = "await_summary_answer"
            return TEXT_SUMMARY_QUESTION
        if is_no(user_text):
            st.session_state.text_phase = "caregiver"
            return "Okay, we can continue with the history."
        return "Please answer yes or no."

    if phase == "await_summary_answer":
        st.session_state.text_phase = "await_diagnosis_answer"
        return TEXT_DIAGNOSIS_QUESTION

    if phase == "await_diagnosis_answer":
        st.session_state.text_phase = "await_differentials_answer"
        return TEXT_DIFFERENTIALS_QUESTION

    if phase == "await_differentials_answer":
        st.session_state.text_phase = "post_presentation"
        st.session_state.presentation_done = True
        st.session_state.mode = "post_presentation"
        st.session_state.case_ended_at = now_iso()
        return TEXT_FINAL_LINE

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
    "mode": "caregiver",
    "text_phase": "caregiver",
    "selected_mode": "Text only",
    "selected_age": "Random",
    "selected_system": "Random",
    "selected_study_number": STUDY_NUMBER_OPTIONS[0],
    "active_mode": None,
    "study_number": None,
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

        if auto_feedback_flag == "1":
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

    if selected_study_number != "Please select study number":
        st.markdown(f"**Study number selected:** {selected_study_number}")
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

    if st.button("Start new case", use_container_width=True):
        if selected_study_number == "Please select study number":
            st.warning("Please select a study number first.")
        elif not st.session_state.study_number_confirmed:
            st.warning("Please confirm the study number before starting.")
        else:
            try:
                resolved_age, resolved_system = resolve_random_selection(selected_age, selected_system)
                case_data = generate_case(resolved_age, resolved_system)
                session_id = str(uuid.uuid4())

                reset_case_state()
                st.session_state.case_data = case_data
                st.session_state.current_session_id = session_id
                st.session_state.case_started_at = now_iso()
                st.session_state.study_number = selected_study_number
                st.session_state.resolved_age = resolved_age
                st.session_state.resolved_system = resolved_system
                st.session_state.transcript_download_name = f"transcript_{selected_study_number}_{session_id}.txt"
                st.session_state.active_mode = selected_mode

                if selected_mode == "Text only":
                    st.session_state.messages = [
                        {"role": "assistant", "content": case_data["opening_line"]}
                    ]

                st.rerun()
            except Exception as e:
                st.error(f"Could not generate case: {e}")

# =========================
# Mode-based UI
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
# Text chat mode
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

        if normalize_text(assistant_text) == normalize_text(TEXT_FINAL_LINE):
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
# Feedback section
# =========================
if st.session_state.presentation_done:
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
        st.write(st.session_state.brief_assessment_generated)

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
                st.write(st.session_state.detailed_assessment_generated)

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
# Reflection section
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

