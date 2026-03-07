import re
import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="History-taking practice bot", page_icon="🩺")
st.title("🩺 History-taking practice bot")

# -----------------------------
# API setup
# -----------------------------
api_key = st.secrets["OPENAI_API_KEY"]
client = OpenAI(api_key=api_key)

MODEL_NAME = "gpt-4.1-mini"

# -----------------------------
# Helper functions
# -----------------------------
def looks_like_finished(text: str) -> bool:
    text = text.lower().strip()
    phrases = [
        "i'm done", "im done", "i am done",
        "i'm finished", "im finished", "finished",
        "that is all", "that's all", "thats all",
        "no further questions", "i have no more questions",
        "can i present", "any feedback", "can you give feedback",
        "mark me", "score me"
    ]
    return any(p in text for p in phrases)

def looks_like_yes(text: str) -> bool:
    text = text.lower().strip()
    yes_phrases = [
        "yes", "yes please", "please", "ok", "okay",
        "sure", "go ahead", "go for it", "continue",
        "proceed", "alright"
    ]
    return any(text == p or p in text for p in yes_phrases)

def looks_like_no(text: str) -> bool:
    text = text.lower().strip()
    no_phrases = [
        "no", "no thanks", "not yet", "let me continue",
        "keep going", "not now"
    ]
    return any(text == p or p in text for p in no_phrases)

def generate_case_bundle(age_group: str, system: str):
    instructions = """
You are creating a hidden paediatric practice case for a medical student history-taking simulation in South Africa.

Return exactly in this format:

CASE_SUMMARY:
<concise hidden case summary for internal use only>

OPENING_LINE:
<one realistic opening line from the caregiver, for example:
"Hello, my name is Nomsa, and this is my son Thabo. He has been coughing and breathing fast. Who am I speaking to?">

Rules:
- The case must fit the selected age group and system.
- Make it realistic for South African paediatrics.
- The case summary should be concise but sufficient for internal consistency.
- The opening line should be natural, brief, and non-medical.
- Do not include anything else outside those two sections.
"""

    prompt = f"Age group: {age_group}\nSystem: {system}"

    response = client.responses.create(
        model=MODEL_NAME,
        instructions=instructions,
        input=prompt,
    )

    text = response.output_text.strip()

    case_summary_match = re.search(
        r"CASE_SUMMARY:\s*(.*?)\s*OPENING_LINE:",
        text,
        re.DOTALL
    )
    opening_line_match = re.search(
        r"OPENING_LINE:\s*(.*)",
        text,
        re.DOTALL
    )

    case_summary = (
        case_summary_match.group(1).strip()
        if case_summary_match else
        f"A realistic {age_group.lower()} {system.lower()} case in a South African paediatric setting."
    )

    opening_line = (
        opening_line_match.group(1).strip()
        if opening_line_match else
        "Hello, this is my child. Who am I speaking to?"
    )

    return case_summary, opening_line

CAREGIVER_INSTRUCTIONS_TEMPLATE = """
You are simulating a realistic caregiver or patient in a paediatric history-taking assessment for a 5th-year undergraduate medical student at the University of the Witwatersrand, Johannesburg, South Africa.

The learner has selected:
- Age group: {age_group}
- System: {system}

Hidden case summary:
{case_summary}

Your role:
- Remain fully in character as the caregiver or patient.
- Use English only.
- Use simple, natural, non-medical language.
- Sound like a real caregiver/patient in a South African paediatric setting.
- Give only the information asked for.
- Do not volunteer extra details.
- Do not teach, guide, coach, hint, or assess during the interview.
- Do not reveal the hidden case summary.
- Do not reveal what the rubric expects.
- If the learner asks a vague or unclear question, ask them to clarify.
- If a question is closed, answer briefly and naturally.
- If you do not know something, say so naturally.
- Keep all answers internally consistent with the hidden case summary.

Important behavioural rules:
- Do not provide long lists of symptoms unless specifically and carefully asked.
- Do not provide medical explanations or interpretations.
- For birth history, immunisations, nutrition, past history, family history, social history, travel, and development, answer only the exact question asked.
- For immunisation-related questions, align with the EPI 2024 schedule.
- If the learner asks something in a non-English language, politely ask them to repeat it in English.

Transition rule:
- If the learner clearly indicates they are finished with the history, respond ONLY with:
  "Would you like to move to preceptor mode? I will first ask you two questions: based on the history, what is your assessment, and what are your differential diagnoses?"
"""

PRECEPTOR_QUESTIONS_INSTRUCTIONS = """
You are now the paediatric preceptor, no longer the caregiver.

Ask exactly these two questions and nothing else:

1. Based on the history, what is your assessment?
2. What are your differential diagnoses?
"""

FEEDBACK_INSTRUCTIONS_TEMPLATE = """
You are now an experienced paediatric preceptor evaluating a 5th-year undergraduate medical student at the University of the Witwatersrand.

The learner selected:
- Age group: {age_group}
- System: {system}

Hidden case summary:
{case_summary}

Your job:
- Review the whole transcript.
- Give balanced, practical feedback.
- Base your comments on the Wits paediatric history-taking rubric principles supplied in the app instructions.
- Focus especially on:
  1. Main complaint and development of symptoms
  2. Danger signs
  3. Involved system history
  4. Other systems enquiry
  5. Birth history
  6. Immunisation
  7. Nutrition
  8. Past medical, surgical, medications, allergies, and traditional therapies
  9. Family history

Important:
- Do not invent questions the learner did not ask.
- Do not claim the learner covered an area if they did not.
- If an area was insufficiently explored, say so plainly.
- Comment when the learner used mostly closed questions or did not follow up specifically enough.
- Be supportive but honest.
- Keep the feedback clear and concise.

Output format:
Use this structure only:

# Feedback Report

## What you did well
- 2 to 5 concise bullet points

## Missed opportunities / areas to explore better
- 3 to 8 concise bullet points

## Brief rubric-aligned review
Create a markdown table with these columns:
Area | Brief judgment | Comment

Include these rows:
- Main complaint and symptom development
- Danger signs
- Involved system history
- Other systems enquiry
- Birth history
- Immunisation
- Nutrition
- Past history / medications / allergies
- Family history
- Communication approach

Use brief judgments such as:
- Strong
- Adequate
- Limited
- Not assessed

## Assessment and differentials
Briefly comment on the learner's assessment and differential diagnoses.

## Overall guidance
A short paragraph on what would most improve the learner's next case.

Do not produce a score out of 100 unless explicitly asked.
Do not reproduce the entire transcript.
"""

def initialize_case(age_group: str, system: str):
    case_summary, opening_line = generate_case_bundle(age_group, system)

    st.session_state.case_summary = case_summary
    st.session_state.opening_line = opening_line
    st.session_state.messages = [
        {"role": "assistant", "content": opening_line}
    ]
    st.session_state.mode = "simulation"

# -----------------------------
# Session state
# -----------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "mode" not in st.session_state:
    st.session_state.mode = "simulation"

if "locked_age" not in st.session_state:
    st.session_state.locked_age = None

if "locked_system" not in st.session_state:
    st.session_state.locked_system = None

if "case_summary" not in st.session_state:
    st.session_state.case_summary = None

if "opening_line" not in st.session_state:
    st.session_state.opening_line = None

# -----------------------------
# UI selections
# -----------------------------
selected_age = st.selectbox(
    "Choose age group",
    ["Neonate", "Infant", "1-5 years", "6-10 years", "11-19 years"]
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
    ]
)

if st.session_state.locked_age is None:
    st.session_state.locked_age = selected_age

if st.session_state.locked_system is None:
    st.session_state.locked_system = selected_system

age_for_case = st.session_state.locked_age
system_for_case = st.session_state.locked_system

if st.session_state.case_summary is None or not st.session_state.messages:
    initialize_case(age_for_case, system_for_case)

st.caption(f"Case context: {age_for_case} | {system_for_case} | Mode: {st.session_state.mode}")

# -----------------------------
# Display chat
# -----------------------------
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.write(m["content"])

# -----------------------------
# Chat input
# -----------------------------
if prompt := st.chat_input("Type your response…"):
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.write(prompt)

    assistant_text = ""

    if st.session_state.mode == "simulation":
        if looks_like_finished(prompt):
            st.session_state.mode = "offer_preceptor"
            assistant_text = (
                "Would you like to move to preceptor mode? "
                "I will first ask you two questions: based on the history, what is your assessment, "
                "and what are your differential diagnoses?"
            )
        else:
            instructions = CAREGIVER_INSTRUCTIONS_TEMPLATE.format(
                age_group=age_for_case,
                system=system_for_case,
                case_summary=st.session_state.case_summary
            )

            response = client.responses.create(
                model=MODEL_NAME,
                instructions=instructions,
                input=st.session_state.messages,
            )
            assistant_text = response.output_text

            if "Would you like to move to preceptor mode?" in assistant_text:
                st.session_state.mode = "offer_preceptor"

    elif st.session_state.mode == "offer_preceptor":
        if looks_like_yes(prompt):
            st.session_state.mode = "wait_for_presentation"
            assistant_text = (
                "Preceptor mode.\n\n"
                "1. Based on the history, what is your assessment?\n"
                "2. What are your differential diagnoses?"
            )
        elif looks_like_no(prompt):
            st.session_state.mode = "simulation"
            assistant_text = "Alright. I will stay in character as the caregiver/patient. Please continue your history."
        else:
            assistant_text = "Please say yes if you want to move to preceptor mode, or no if you want to continue the history."

    elif st.session_state.mode == "wait_for_presentation":
        st.session_state.mode = "feedback"

        instructions = FEEDBACK_INSTRUCTIONS_TEMPLATE.format(
            age_group=age_for_case,
            system=system_for_case,
            case_summary=st.session_state.case_summary
        )

        response = client.responses.create(
            model=MODEL_NAME,
            instructions=instructions,
            input=st.session_state.messages,
        )
        assistant_text = response.output_text

    else:
        instructions = FEEDBACK_INSTRUCTIONS_TEMPLATE.format(
            age_group=age_for_case,
            system=system_for_case,
            case_summary=st.session_state.case_summary
        )

        response = client.responses.create(
            model=MODEL_NAME,
            instructions=instructions,
            input=st.session_state.messages,
        )
        assistant_text = response.output_text

    st.session_state.messages.append({"role": "assistant", "content": assistant_text})

    with st.chat_message("assistant"):
        st.write(assistant_text)

# -----------------------------
# Reset
# -----------------------------
if st.button("Reset conversation"):
    st.session_state.locked_age = selected_age
    st.session_state.locked_system = selected_system
    st.session_state.case_summary = None
    st.session_state.opening_line = None
    st.session_state.messages = []
    st.session_state.mode = "simulation"
    st.rerun()
