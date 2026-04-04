import copy
import json
import random
import re
import urllib.parse
import uuid
from datetime import datetime
from typing import Optional

import requests
import streamlit as st
from openai import OpenAI

from dynamic_rubric import (
    choose_case,
    build_history_taking_system_prompt,
    build_assessor_system_prompt,
    build_assessor_schema,
)
from supabase_db import (
    save_session_result,
    get_student_sessions,
    get_student_summary,
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
# Dynamic variation pools
# =========================
FEMALE_CHILD_NAMES = [
    "Amahle", "Ayanda", "Lerato", "Naledi", "Aisha", "Zanele", "Nosipho",
    "Karabo", "Thandeka", "Mpho", "Keitumetse", "Luyanda", "Asanda",
]

MALE_CHILD_NAMES = [
    "Sipho", "Thabo", "Lethabo", "Themba", "Sibusiso", "Musa", "Ayaan",
    "Kagiso", "Vuyo", "Lindo", "Khaya", "Neo", "Ethan",
]

FEMALE_CAREGIVER_NAMES = [
    "Nomsa", "Ayanda", "Zandile", "Lerato", "Amina", "Nandi", "Busisiwe",
    "Thandi", "Mpho", "Palesa", "Siphokazi", "Nokuthula", "Fatima",
]

MALE_CAREGIVER_NAMES = [
    "Thabo", "Sizwe", "Mandla", "Yusuf", "Imran", "Bongani", "Kagiso",
    "Themba", "Musa", "Sibusiso", "Vusi", "Naeem", "Lungelo",
]

CAREGIVER_OCCUPATIONS = [
    "teacher", "shop assistant", "security guard", "driver", "administrator",
    "nurse", "home-based caregiver", "cashier", "clerk", "general worker",
    "hairdresser", "chef", "self-employed",
]

RESIDENCE_POOL = [
    "Soweto", "Johannesburg South", "Randburg", "Alexandra", "Tembisa",
    "Roodepoort", "Lenasia", "Midrand", "Orange Farm", "Diepsloot",
]

BIRTH_PLACE_POOL = [
    "Chris Hani Baragwanath Hospital",
    "Rahima Moosa Mother and Child Hospital",
    "Charlotte Maxeke Johannesburg Academic Hospital",
    "Helen Joseph Hospital",
    "Tembisa Hospital",
    "South Rand Hospital",
]

HOUSEHOLD_POOL = [
    "lives with both parents and two siblings",
    "lives with mother and grandmother",
    "lives with mother, aunt, and cousins",
    "lives with both parents and one older sibling",
    "lives with father and grandmother",
    "lives with mother and three siblings",
]

SCHOOL_DAYCARE_POOL = {
    "Neonate": "not yet attending school or daycare",
    "Infant": "stays at home with family",
    "1-5 years": "attends crèche",
    "6-10 years": "is in primary school",
    "11-19 years": "is in secondary school",
}

SIBLING_POOL = [
    "no siblings",
    "one older sibling",
    "one younger sibling",
    "two siblings",
    "three siblings",
]

GENERIC_PRESENTING_TEMPLATES = [
    "my child has not been well",
    "my child has been sick for a few days",
    "my child has become unwell",
    "something is not right with my child",
]

# =========================
# Helpers
# =========================
def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", str(text).strip().lower())


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def normalize_email(email: str | None) -> str:
    return str(email or "").strip().lower()


def is_valid_email(email: str | None) -> bool:
    value = normalize_email(email)
    return bool(re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", value))


def get_student_lookup_headers() -> dict:
    supabase_key = st.secrets.get("SUPABASE_ANON_KEY") or st.secrets.get("SUPABASE_KEY")
    return {
        "apikey": supabase_key,
        "Authorization": f"Bearer {supabase_key}",
        "Accept": "application/json",
    }


def map_group_name_to_internal(value: str | None) -> str | None:
    raw = normalize_text(value or "")
    if not raw:
        return None
    collapsed = raw.replace("-", " ").replace("_", " ")
    if "non" in collapsed and "custom" in collapsed:
        return NON_CUSTOMIZED_GROUP
    if "custom" in collapsed:
        return CUSTOMIZED_GROUP
    if collapsed in {"control", "generic", "standard"}:
        return NON_CUSTOMIZED_GROUP
    if collapsed in {"intervention", "customised", "customized bot"}:
        return CUSTOMIZED_GROUP
    return None


def fetch_student_record_by_email(email: str) -> tuple[Optional[dict], Optional[str]]:
    email = normalize_email(email)
    if not is_valid_email(email):
        return None, "Please enter a valid email address."

    supabase_url = st.secrets.get("SUPABASE_URL")
    supabase_key = st.secrets.get("SUPABASE_ANON_KEY") or st.secrets.get("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        return None, "Supabase credentials are missing from Streamlit secrets. Add SUPABASE_URL and SUPABASE_ANON_KEY."

    url = f"{str(supabase_url).rstrip('/')}/rest/v1/students"
    params = {
        "select": "*",
        "email": f"ilike.{email}",
        "limit": "1",
    }

    try:
        response = requests.get(url, headers=get_student_lookup_headers(), params=params, timeout=20)
    except Exception as e:
        return None, f"Could not connect to Supabase: {e}"

    if response.status_code != 200:
        try:
            detail = response.json()
        except Exception:
            detail = response.text
        return None, f"Supabase student lookup failed: {detail}"

    try:
        rows = response.json()
    except Exception as e:
        return None, f"Supabase returned unreadable data: {e}"

    if not rows:
        return None, "That email address was not found in the students table."

    row = rows[0] or {}
    study_number = str(row.get("study_number") or row.get("study-number") or "").strip()
    group_name = (
        row.get("group_name")
        or row.get("group-name")
        or row.get("group")
        or row.get("arm")
        or ""
    )

    derived_group = map_group_name_to_internal(group_name) or get_study_group(study_number)

    return {
        "id": row.get("id"),
        "email": normalize_email(row.get("email") or email),
        "study_number": study_number,
        "group_name": str(group_name or "").strip(),
        "study_group": derived_group,
        "created_at": row.get("created_at") or row.get("created-at"),
        "raw": row,
    }, None


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


def safe_int(value):
    try:
        return int(value)
    except Exception:
        return None


def is_yes(text: str) -> bool:
    t = normalize_text(text)
    yes_values = {
        "yes", "y", "yeah", "yep", "yes please", "ready", "ready for feedback",
        "feedback please", "proceed", "please proceed", "continue to feedback"
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

    if not t:
        return False

    word_count = len(t.split())
    if word_count > 12:
        return False

    non_diagnosis_phrases = [
        "that is a diagnosis",
        "this is a diagnosis",
        "i don't know",
        "dont know",
        "not sure",
        "can i ask",
        "tell me",
        "what do you mean",
        "i need more information",
        "more information",
        "question",
    ]
    if any(p in t for p in non_diagnosis_phrases):
        return False

    diagnosis_markers = [
        "pyelonephritis", "uti", "urinary tract infection", "epilepsy", "meningitis",
        "pneumonia", "bronchiolitis", "asthma", "tuberculosis", "tb", "appendicitis",
        "gastroenteritis", "dehydration", "sepsis", "nephrotic syndrome", "nephritic syndrome",
        "reflux", "cerebral palsy", "migraine", "febrile seizure", "pertussis",
        "croup", "foreign body aspiration", "congenital heart disease", "malnutrition",
        "hepatitis", "dysentery", "constipation", "rickets", "congenital syphilis",
        "tetralogy of fallot", "tof", "transposition of the great arteries", "tga",
        "tricuspid atresia", "pulmonary atresia", "ventricular septal defect", "vsd",
        "atrial septal defect", "asd", "patent ductus arteriosus", "pda",
        "coarctation of the aorta", "pulmonary stenosis", "aortic stenosis",
        "cyanotic congenital heart disease", "acyanotic congenital heart disease",
        "heart failure", "cardiomyopathy", "myocarditis", "endocarditis"
    ]

    if any(marker in t for marker in diagnosis_markers):
        return True

    diagnosis_like_prefixes = [
        "i think it is",
        "most likely",
        "this is",
        "it is",
        "likely",
        "probably",
        "concerned about",
        "community acquired",
        "community-acquired",
    ]
    return any(t.startswith(p) for p in diagnosis_like_prefixes)


def looks_like_differentials_response(text: str) -> bool:
    t = normalize_text(text)
    if looks_like_history_question(text):
        return False
    differential_markers = [
        ",", ";", "or", "and", "also", "another", "differential", "possibility", "could be"
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


def extract_case_diagnosis(case_data: dict | None) -> str:
    if not case_data:
        return ""
    diagnosis = (
        case_data.get("expected_diagnosis")
        or case_data.get("diagnosis")
        or case_data.get("true_case_diagnosis")
        or ""
    )
    return str(diagnosis).strip()


def get_recent_customized_sessions(study_number: str, limit: int = 8) -> list[dict]:
    if not study_number or get_study_group(study_number) != CUSTOMIZED_GROUP:
        return []
    sessions = get_student_sessions(study_number)
    return sessions[:limit]


def choose_novel_random_targets(study_number: str, selected_age: str, selected_system: str):
    sessions = get_recent_customized_sessions(study_number, limit=6)

    recent_ages = [str(s.get("age_group", "")).strip() for s in sessions if s.get("age_group")]
    recent_systems = [str(s.get("system", "")).strip() for s in sessions if s.get("system")]

    resolved_age = selected_age
    resolved_system = selected_system

    if selected_age == "Random":
        age_options = [a for a in RANDOM_AGE_POOL if a not in recent_ages[:3]]
        if not age_options:
            age_options = RANDOM_AGE_POOL[:]
        resolved_age = random.choice(age_options)

    if selected_system == "Random":
        system_options = [s for s in RANDOM_SYSTEM_POOL if s not in recent_systems[:3]]
        if not system_options:
            system_options = RANDOM_SYSTEM_POOL[:]
        resolved_system = random.choice(system_options)

    return resolved_age, resolved_system


def choose_case_with_history(requested_system: str, study_number: str | None = None, avoid_recent_repeat: bool = False) -> dict:
    if not avoid_recent_repeat or not study_number or get_study_group(study_number) != CUSTOMIZED_GROUP:
        return choose_case(requested_system=requested_system)

    sessions = get_recent_customized_sessions(study_number, limit=8)
    recent_diagnoses = {
        str(s.get("diagnosis", "")).strip().lower()
        for s in sessions
        if s.get("diagnosis")
    }

    best_case = None
    for _ in range(24):
        candidate = choose_case(requested_system=requested_system)
        diagnosis = extract_case_diagnosis(candidate).lower()
        if diagnosis and diagnosis not in recent_diagnoses:
            return candidate
        best_case = candidate

    return best_case or choose_case(requested_system=requested_system)


def generate_age_string(age_group: str) -> str:
    if age_group == "Neonate":
        days = random.randint(2, 27)
        return f"{days} days"
    if age_group == "Infant":
        months = random.randint(2, 11)
        return f"{months} months"
    if age_group == "1-5 years":
        years = random.randint(1, 5)
        return f"{years} years"
    if age_group == "6-10 years":
        years = random.randint(6, 10)
        return f"{years} years"
    if age_group == "11-19 years":
        years = random.randint(11, 17)
        return f"{years} years"
    return random.choice(["8 months", "2 years", "7 years", "14 years"])


def build_presenting_complaint_variant(diagnosis: str, age_group: str, original: str) -> str:
    d = normalize_text(diagnosis)
    original = str(original or "").strip()

    variants = {
        "rickets": [
            "my child has started walking strangely and the legs look bent",
            "my child is not standing properly and the legs seem bowed",
            "my child seems weak and is not walking the way I expected",
        ],
        "asthma": [
            "my child has been coughing and breathing with difficulty",
            "my child is wheezing and struggling to breathe",
            "my child gets tight-chested and short of breath",
        ],
        "pneumonia": [
            "my child has fever, cough, and fast breathing",
            "my child is coughing badly and breathing quickly",
            "my child has been unwell with fever and difficulty breathing",
        ],
        "bronchiolitis": [
            "the baby has cough, noisy breathing, and is feeding poorly",
            "the baby has a chesty cough and is breathing fast",
            "the baby seems blocked up, coughs a lot, and is not feeding well",
        ],
        "gastroenteritis": [
            "my child has diarrhoea and vomiting",
            "my child has been vomiting and has loose stools",
            "my child has a runny tummy and keeps vomiting",
        ],
        "dehydration": [
            "my child has been vomiting and now seems very weak",
            "my child is not drinking well and looks dry",
            "my child has become floppy after diarrhoea and vomiting",
        ],
        "uti": [
            "my child has fever and cries when passing urine",
            "my child has had fever and seems uncomfortable when urinating",
            "my child has fever and urine problems",
        ],
        "urinary tract infection": [
            "my child has fever and cries when passing urine",
            "my child has had fever and seems uncomfortable when urinating",
            "my child has fever and urine problems",
        ],
        "pyelonephritis": [
            "my child has fever and looks very unwell with urine problems",
            "my child has high fever and seems uncomfortable when passing urine",
            "my child has fever, vomiting, and I think there is a urine problem",
        ],
        "febrile seizure": [
            "my child had a fit with a fever",
            "my child became stiff and jerky while having fever",
            "my child had a seizure when the temperature was high",
        ],
        "epilepsy": [
            "my child has had repeated fits",
            "my child keeps having seizure-like episodes",
            "my child has been having recurrent convulsions",
        ],
        "meningitis": [
            "my child has fever and is very sleepy and irritable",
            "my child is feverish and not responding normally",
            "my child has fever and is behaving strangely",
        ],
        "appendicitis": [
            "my child has stomach pain and vomiting",
            "my child has bad pain on the right side of the tummy",
            "my child has tummy pain that is getting worse",
        ],
        "constipation": [
            "my child struggles to pass stool and complains of tummy pain",
            "my child has not been opening the bowels properly",
            "my child has hard stools and abdominal pain",
        ],
        "nephrotic": [
            "my child has become swollen around the eyes and body",
            "my child is puffy, especially around the eyes",
            "my child has swelling that worries me",
        ],
        "nephritic": [
            "my child has swelling and the urine looks dark",
            "my child is swollen and passing tea-coloured urine",
            "my child has facial swelling and dark urine",
        ],
        "malnutrition": [
            "my child is losing weight and seems weak",
            "my child is not growing well and looks thin",
            "my child has become wasted and has poor appetite",
        ],
        "croup": [
            "my child has a barking cough and noisy breathing",
            "my child woke up with a harsh cough and noisy breathing",
            "my child has a strange barking cough",
        ],
        "foreign body aspiration": [
            "my child suddenly started coughing and breathing badly",
            "my child choked and since then the breathing has not been normal",
            "my child suddenly became short of breath while eating",
        ],
        "congenital heart disease": [
            "my child gets tired easily and breathes fast",
            "my child is not feeding well and breathes quickly",
            "my child becomes sweaty and breathless easily",
        ],
        "dysentery": [
            "my child has diarrhoea with blood in it",
            "my child has been passing loose stools with blood",
            "there is blood in the diarrhoea",
        ],
    }

    for key, options in variants.items():
        if key in d:
            return random.choice(options)

    if original:
        generic_from_original = [
            original,
            f"my child has been having {original.lower()}",
            f"there has been a problem with {original.lower()}",
        ]
        return random.choice(generic_from_original)

    return random.choice(GENERIC_PRESENTING_TEMPLATES)


def build_opening_line(caregiver_name: str, child_name: str, caregiver_role: str, presenting_complaint: str) -> str:
    return f"Hello doctor, I'm {caregiver_name}, {child_name}'s {caregiver_role}."


def adapt_context_age_text(original_context: str, child_age: str) -> str:
    context = str(original_context or "").strip()
    if not context:
        return context

    patterns = [
        r"^(A|An)\s+[^,.]+?\s+(child\s+)?has\s+",
        r"^(A|An)\s+[^,.]+?\s+(with|who has)\s+",
    ]

    for pattern in patterns:
        match = re.match(pattern, context, flags=re.IGNORECASE)
        if match:
            remainder = context[match.end():].strip()
            return f"A child aged {child_age} has {remainder}"

    return re.sub(r"^(A|An)\s+[^,.]+", f"A child aged {child_age}", context, count=1)


def apply_dynamic_case_variation(case_data: dict, resolved_age: str) -> dict:
    varied = copy.deepcopy(case_data)

    diagnosis = extract_case_diagnosis(varied)
    child_sex = random.choice(["male", "female"])

    caregiver_role = (
        random.choice(["mother", "father", "grandmother"])
        if resolved_age in {"Neonate", "Infant"}
        else random.choice(["mother", "father"])
    )

    if child_sex == "female":
        child_name = random.choice(FEMALE_CHILD_NAMES)
    else:
        child_name = random.choice(MALE_CHILD_NAMES)

    if caregiver_role in {"mother", "grandmother", "aunt"}:
        caregiver_name = random.choice(FEMALE_CAREGIVER_NAMES)
        caregiver_gender = "female"
    else:
        caregiver_name = random.choice(MALE_CAREGIVER_NAMES)
        caregiver_gender = "male"

    varied["child_sex"] = child_sex
    varied["child_name"] = child_name
    varied["child_age"] = generate_age_string(resolved_age)
    varied["age_label"] = varied["child_age"]
    varied["caregiver_role"] = caregiver_role
    varied["caregiver_name"] = caregiver_name
    varied["caregiver_gender"] = caregiver_gender
    varied["caregiver_occupation"] = random.choice(CAREGIVER_OCCUPATIONS)
    varied["siblings"] = random.choice(SIBLING_POOL)
    varied["residence"] = random.choice(RESIDENCE_POOL)
    varied["birth_place"] = random.choice(BIRTH_PLACE_POOL)
    varied["household_structure"] = random.choice(HOUSEHOLD_POOL)
    varied["school_or_daycare"] = SCHOOL_DAYCARE_POOL.get(resolved_age, "stays at home with family")

    varied_presenting = build_presenting_complaint_variant(
        diagnosis=diagnosis,
        age_group=resolved_age,
        original=varied.get("presenting_complaint", ""),
    )
    varied["presenting_complaint"] = varied_presenting
    varied["context"] = adapt_context_age_text(varied.get("context", ""), varied["child_age"])
    varied["case_summary"] = varied["context"]
    varied["opening_line"] = build_opening_line(
        caregiver_name=varied["caregiver_name"],
        child_name=varied["child_name"],
        caregiver_role=varied["caregiver_role"],
        presenting_complaint=varied_presenting,
    )

    return varied


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
- Do not ask the student any questions except when you genuinely need clarification of jargon or an unclear question.
- Do not guide the student.
- Do not provide feedback unless explicitly asked to give feedback at the end.
- Do not mention rubrics, scoring, grades, diagnosis, or differentials unless the student directly asks what you were told.
- Answer naturally, briefly, and realistically.
- Do not volunteer the whole history at once.
- Only reveal information when asked.
- Do not volunteer extra symptoms or extra timelines unless the student asked about them.
- Use simple caregiver language, not textbook language.
- You are a lay caregiver, not medically trained unless explicitly stated.
- Do NOT spontaneously use medical jargon or technical labels.
- Do NOT use terms such as:
  "dysentery", "raised intracranial pressure", "bronchiolitis", "meningitis",
  "pyelonephritis", "urinary tract infection", "nephrotic syndrome",
  "congenital heart disease", "cyanosis", "aspiration", "febrile seizure"
  unless the student first uses that exact term.
- Prefer ordinary language such as:
  "diarrhoea with blood", "a fit", "very sleepy", "breathing fast",
  "pain when passing urine", "swollen eyes", "puffy face".
- Keep answers internally consistent with the hidden case summary.
- If the student uses jargon or a word a normal caregiver may not understand, ask briefly:
  "I'm sorry doctor, what do you mean by that?"
  or
  "Can you explain that more simply?"
- Do not repeatedly ask "what else do you want to know?"
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


def save_session_to_db():
    if st.session_state.db_save_completed:
        return

    study_number = st.session_state.study_number
    session_id = st.session_state.current_session_id

    if not study_number or not session_id:
        return

    start_dt = parse_iso(st.session_state.case_started_at)
    end_dt = parse_iso(st.session_state.case_ended_at)
    duration_minutes = None
    if start_dt and end_dt:
        duration_minutes = max(0, int(round((end_dt - start_dt).total_seconds() / 60)))

    assessment = st.session_state.brief_assessment_generated if isinstance(st.session_state.brief_assessment_generated, dict) else {}
    overall_feedback = None
    grade = None
    grade_label = None
    diagnosis = None
    strengths = []
    missed_opportunities = []
    key_missed_history_questions = []
    case_summary = st.session_state.case_data.get("case_summary") if isinstance(st.session_state.case_data, dict) else None

    if st.session_state.study_group == CUSTOMIZED_GROUP:
        if not assessment:
            return
        overall_feedback = assessment.get("overall_feedback")
        grade = safe_int(assessment.get("grade"))
        grade_label = assessment.get("grade_label")
        diagnosis = assessment.get("diagnosis")
        strengths = assessment.get("strengths", [])
        missed_opportunities = assessment.get("missed_opportunities", [])
        key_missed_history_questions = assessment.get("key_missed_history_questions", [])
        case_summary = assessment.get("case_summary") or case_summary
    else:
        overall_feedback = st.session_state.generic_feedback or "Non-customized session captured. No rubric-based feedback."
        diagnosis = None
        strengths = []
        missed_opportunities = []
        key_missed_history_questions = []

    save_session_result(
        study_number=study_number,
        session_id=session_id,
        created_at=st.session_state.case_ended_at or now_iso(),
        interaction_mode=st.session_state.active_mode,
        age_group=st.session_state.resolved_age,
        system=st.session_state.resolved_system,
        grade=grade,
        grade_label=grade_label,
        diagnosis=diagnosis,
        strengths=strengths,
        missed_opportunities=missed_opportunities,
        key_missed_history_questions=key_missed_history_questions,
        overall_feedback=overall_feedback,
        case_summary=case_summary,
        transcript_text=transcript_from_messages(st.session_state.messages),
        duration_minutes=duration_minutes,
    )

    st.session_state.db_save_completed = True


def render_student_progress():
    if st.session_state.study_group != CUSTOMIZED_GROUP:
        return
    if not st.session_state.study_number:
        return

    sessions = get_student_sessions(st.session_state.study_number)
    summary = get_student_summary(st.session_state.study_number)

    st.markdown("### Your progress so far")

    if not sessions:
        st.info("No previous customized sessions recorded yet.")
        return

    total_cases = summary.get("total_cases", 0)
    average_grade = summary.get("average_grade")

    st.markdown(f"**Total customized cases completed:** {total_cases}")
    st.markdown(f"**Average grade:** {average_grade if average_grade is not None else 'Not available'}")

    recent_strengths = summary.get("recent_strengths", [])
    recent_missed = summary.get("recent_missed_opportunities", [])

    if recent_strengths:
        st.markdown("**Recent strengths noticed**")
        for item in recent_strengths:
            st.write(f"- {item}")

    if recent_missed:
        st.markdown("**Recent recurring improvement areas**")
        for item in recent_missed:
            st.write(f"- {item}")

    with st.expander("Previous sessions", expanded=False):
        for session in sessions[:10]:
            created_at = session.get("created_at", "")
            system = session.get("system", "")
            age_group = session.get("age_group", "")
            grade = session.get("grade", "")
            grade_label = session.get("grade_label", "")
            diagnosis = session.get("diagnosis", "")

            st.markdown(
                f"**{created_at}** — {system} — {age_group} — Grade {grade} {f'({grade_label})' if grade_label else ''}"
            )
            if diagnosis:
                st.write(f"Diagnosis: {diagnosis}")
            if session.get("overall_feedback"):
                st.write(session["overall_feedback"])
            st.markdown("---")


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
        "student_email": st.session_state.student_email,
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
    st.session_state.student_email = ""
    st.session_state.student_record = None
    st.session_state.db_save_completed = False
    st.session_state.prior_sessions_loaded = False


def apply_imported_messages(imported_obj, session_id=None, status_message="Voice transcript imported automatically."):
    imported_messages = imported_obj["messages"]
    st.session_state.messages = imported_messages
    st.session_state.raw_voice_payload = imported_obj.get("raw_payload")
    st.session_state.brief_assessment_generated = None
    st.session_state.detailed_assessment_generated = None
    st.session_state.db_save_completed = False

    raw_payload = imported_obj.get("raw_payload") or {}
    st.session_state.case_started_at = raw_payload.get("started_at") or st.session_state.case_started_at
    st.session_state.case_ended_at = raw_payload.get("ended_at") or now_iso()

    if raw_payload.get("age_group"):
        st.session_state.resolved_age = raw_payload.get("age_group")
    if raw_payload.get("system"):
        st.session_state.resolved_system = raw_payload.get("system")
    if raw_payload.get("study_number"):
        st.session_state.study_number = raw_payload.get("study_number")
    if raw_payload.get("student_email"):
        st.session_state.student_email = normalize_email(raw_payload.get("student_email"))

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
        f"Student email: {st.session_state.student_email or 'Not recorded'}",
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
        f"Student email: {st.session_state.student_email or 'Not recorded'}",
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
                st.session_state.generic_feedback = "No feedback selected for this session."
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
    "student_email": "",
    "student_record": None,
    "entered_email": "",
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
    "db_save_completed": False,
    "prior_sessions_loaded": False,
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
                st.session_state.brief_assessment_generated = call_assessment(
                    imported_obj["messages"],
                    detailed=False,
                )
                save_session_to_db()
                st.session_state.presentation_done = True
                st.session_state.mode = "post_presentation"
                st.session_state.text_phase = "post_presentation"
                st.session_state.active_mode = "Realtime voice"
                if not st.session_state.case_ended_at:
                    st.session_state.case_ended_at = now_iso()
        elif st.session_state.study_group == NON_CUSTOMIZED_GROUP:
            if not st.session_state.case_ended_at:
                st.session_state.case_ended_at = now_iso()
            save_session_to_db()

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

    entered_email = st.text_input(
        "Enter your study email address",
        key="entered_email",
        help="Use the email address that was loaded into the students table.",
    )

    lookup_email = normalize_email(entered_email)
    student_record = None
    lookup_error = None

    if lookup_email:
        student_record, lookup_error = fetch_student_record_by_email(lookup_email)
        if student_record:
            st.session_state.student_record = student_record
            st.session_state.student_email = student_record["email"]
            st.session_state.study_number = student_record["study_number"]
            st.session_state.study_group = student_record["study_group"]
        else:
            st.session_state.student_record = None
            st.session_state.student_email = lookup_email
            st.session_state.study_number = None
            st.session_state.study_group = CUSTOMIZED_GROUP

    if student_record:
        arm_label = "Customized bot" if student_record["study_group"] == CUSTOMIZED_GROUP else "Non-customized bot"
        st.success(f"Email found. Study number: {student_record['study_number']} | Study arm: {arm_label}")
        if student_record.get("group_name"):
            st.caption(f"Group name in table: {student_record['group_name']}")
    elif lookup_email and lookup_error:
        st.warning(lookup_error)

    selected_mode = st.radio(
        "Choose interaction mode",
        VISIBLE_INTERACTION_MODES,
        key="selected_mode",
    )

    active_group = student_record["study_group"] if student_record else CUSTOMIZED_GROUP

    if student_record and active_group == CUSTOMIZED_GROUP:
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
    elif student_record and active_group == NON_CUSTOMIZED_GROUP:
        selected_age = "Random"
        selected_system = "Random"

        st.info("A random case will be generated for this study arm.")

        non_custom_instruction = st.text_input(
            "Optional instruction",
            key="non_custom_instruction",
            help="You can ask the chatbot to switch systems or caregiver, should you wish.",
        )

        st.caption("You can ask the chatbot to switch systems or caregiver, should you wish.")
    else:
        selected_age = "Random"
        selected_system = "Random"
        non_custom_instruction = ""

    if student_record and active_group == CUSTOMIZED_GROUP:
        render_student_progress()

    if st.button("Start new case", use_container_width=True):
        if not lookup_email:
            st.warning("Please enter your study email address first.")
        else:
            fresh_student_record, fresh_lookup_error = fetch_student_record_by_email(lookup_email)
            if fresh_lookup_error or not fresh_student_record:
                st.warning(fresh_lookup_error or "That email address was not found in the students table.")
            else:
                try:
                    study_number = fresh_student_record["study_number"]
                    study_group = fresh_student_record["study_group"]

                    use_history_aware_random = (
                        study_group == CUSTOMIZED_GROUP
                        and (selected_age == "Random" or selected_system == "Random")
                    )

                    if use_history_aware_random:
                        resolved_age, resolved_system = choose_novel_random_targets(
                            study_number,
                            selected_age,
                            selected_system,
                        )
                    else:
                        if study_group == CUSTOMIZED_GROUP:
                            resolved_age, resolved_system = resolve_random_selection(selected_age, selected_system)
                        else:
                            resolved_age, resolved_system = resolve_random_selection("Random", "Random")

                    base_case_data = choose_case_with_history(
                        requested_system=resolved_system,
                        study_number=study_number,
                        avoid_recent_repeat=use_history_aware_random,
                    )
                    case_data = apply_dynamic_case_variation(base_case_data, resolved_age)

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
                    st.session_state.student_email = fresh_student_record["email"]
                    st.session_state.student_record = fresh_student_record
                    st.session_state.study_number = study_number
                    st.session_state.study_group = study_group
                    st.session_state.resolved_age = resolved_age
                    st.session_state.resolved_system = resolved_system
                    st.session_state.transcript_download_name = f"transcript_{study_number}_{session_id}.txt"
                    st.session_state.active_mode = selected_mode

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
    arm_text = 'Customized bot' if st.session_state.study_group == CUSTOMIZED_GROUP else 'Non-customized bot'
    st.caption(
        f"Student email: {st.session_state.student_email or 'Not recorded'} | Study number: {st.session_state.study_number or 'Not recorded'} | Study arm: {arm_text}"
    )

# =========================
# Progress display during active customized sessions
# =========================
if st.session_state.study_group == CUSTOMIZED_GROUP and st.session_state.study_number and st.session_state.case_data:
    render_student_progress()

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
# Non-customized text hint
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
                save_session_to_db()

        if (
            st.session_state.study_group == NON_CUSTOMIZED_GROUP
            and st.session_state.presentation_done
            and not st.session_state.db_save_completed
        ):
            save_session_to_db()

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
                save_session_to_db()
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
    if not st.session_state.db_save_completed:
        save_session_to_db()

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



