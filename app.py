import re
import urllib.parse
import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="History-taking practice bot", page_icon="🩺")
st.title("🩺 History-taking practice bot")

# =========================================================
# VERSION CONTROL
# =========================================================
APP_VERSION = "v3.1-streamlit-with-voice-handoff"
RUBRIC_VERSION = "Wits Paeds Rubric Version 11 Sept 2024"
SCORING_PROMPT_VERSION = "strict-v2"
CAREGIVER_PROMPT_VERSION = "sa-realism-v2"
MODEL_NAME = "gpt-4.1-mini"

# -----------------------------
# API setup
# -----------------------------
api_key = st.secrets["OPENAI_API_KEY"]
client = OpenAI(api_key=api_key)

# -----------------------------
# Rubric text
# -----------------------------
RUBRIC_TEXT = """
Wits Paeds Rubric Version 11 Sept 2024

Use this rubric strictly.
Do not mark liberally or generously.
Do not award credit for content that does not clearly appear in the transcript.
Do not infer that an area was covered unless there is explicit transcript evidence.

Assessment components and weightings:

1. Main Complaint & Development of Symptoms (25)
Grade 4:
Thoroughly explores the main complaint, including onset, duration, progression, characteristics, triggers, alleviating factors, and impact on daily activities. Should include at least 3 specific relevant follow-up questions.
Grade 3:
Covers most aspects but lacks some details such as triggers or impact on daily activities.
Grade 2:
Covers basic aspects but lacks detailed exploration of symptoms.
Grade 1:
Inadequate exploration of symptoms.
Grade 0:
Not covered.

2. Danger Signs (2)
Grade 4:
Enquires about all relevant danger signs. Must specifically include exploration of at least 3 of the following: convulsions, lethargy, vomiting all feeds, not taking any feeds. Also explores danger signs relevant to the involved system, e.g. difficulty or rapid breathing in a respiratory case.
Grade 3:
Enquires about most danger signs but misses one.
Grade 2:
Enquires about some danger signs but misses multiple.
Grade 1:
Inadequate enquiry about danger signs.
Grade 0:
Not covered.

3. Involved System Focused History (5)
Grade 4:
Comprehensive history of the involved system with detailed questions about symptoms and related factors.
Grade 3:
Covers most aspects but lacks some detail.
Grade 2:
Basic history taken with minimal detail.
Grade 1:
Inadequate history of involved system.
Grade 0:
Not covered.

4. Other Systems Enquiry (3)
Grade 4:
At least three additional systems must be assessed with detailed questions on any of the following: weight loss, sleep, urinary and bowel habits, or screen time.
Grade 3:
At least two additional systems must be assessed with detailed questions on any of the following: weight loss, sleep, urinary and bowel habits, or screen time.
Grade 2:
Asks about at least one of the following: weight loss, sleep, urinary and bowel habits, or screen time.
Grade 1:
Inadequate enquiry into any system.
Grade 0:
Not covered.

5. Birth History (5)
Grade 4:
Thorough exploration of birth history, including prenatal, perinatal, and neonatal periods. Must have follow-up questions to elicit specific details including whether the mother was tested for HIV and syphilis during pregnancy. Should ask for the Road to Health Booklet or antenatal card. If mother is HIV infected, there needs to be a thorough enquiry of vertical transmission prevention intervention. Needs to enquire further about miscarriages and known reasons, maternal health during pregnancy, chronic medication, and when antenatal clinic attendance started.
Grade 3:
Covers most aspects but lacks some detail. Must include asking to see the Road to Health Booklet OR any maternal record of the pregnancy.
Grade 2:
Basic birth history taken with minimal detail.
Grade 1:
Inadequate birth history.
Grade 0:
Not covered.

6. Immunization (3)
Grade 4:
Fully reviews immunization status with specific details by hearing what the caregiver says about when these immunizations were given or alternatively must ask for the Road to Health Booklet or Card to be reviewed.
Grade 3:
Covers immunization status but lacks some detail.
Grade 2:
Basic enquiry about immunizations.
Grade 1:
Inadequate enquiry about immunizations.
Grade 0:
Not covered.

7. Nutrition (3)
Grade 4:
Must enquire about breastfeeding, fluid intake, and missed meals, and ask at least one additional question related to diet or feeding practices. Food allergies or intolerances/avoidances must be included.
Grade 3:
Covers most aspects but lacks some detail.
Grade 2:
Basic enquiry about nutrition.
Grade 1:
Inadequate enquiry about nutrition.
Grade 0:
Not covered.

8. Past Medical, Surgical, Medications & Allergies History (5)
Grade 4:
The student must ask about past medical history, surgical history, current medications, allergies, and use of traditional therapies.
Grade 3:
Covers most aspects but lacks some detail.
Grade 2:
Basic enquiry about past history.
Grade 1:
Inadequate enquiry about past history.
Grade 0:
Not covered.

9. Family Medical History (3)
Grade 4:
Comprehensive family medical history including extended family illnesses. Should include a question of exposure to tuberculosis if relevant.
Grade 3:
Covers most aspects but lacks some detail.
Grade 2:
Basic enquiry about family history.
Grade 1:
Inadequate enquiry about family history.
Grade 0:
Not covered.

10. Developmental Milestones (3)
Grade 4:
Detailed assessment of developmental milestones. Needs to ask about specifics showing exploration of gross motor, fine motor, language and social domains.
Grade 3:
Covers most milestones but lacks some detail.
Grade 2:
Basic enquiry about milestones.
Grade 1:
Inadequate enquiry about milestones.
Grade 0:
Not covered.

11. Social History & Travel (3)
Grade 4:
Comprehensive social and travel history with detailed questions. Must enquire about the dwelling, amenities, siblings, family income status, grants, relevant exposures such as polluted areas or factories, who looks after the child during the day where relevant, and must include a travel question.
Grade 3:
Covers most aspects but lacks some detail.
Grade 2:
Basic enquiry about social and travel history.
Grade 1:
Inadequate enquiry about social and travel history.
Grade 0:
Not covered.

12. Assessment from History (20)
Grade 4:
Provides a thorough and logical summary with a comprehensive differential diagnosis. The assessment considers all relevant history details and integrates them into a cohesive clinical picture. Should provide at least one other differential other than the presumed diagnosis.
Grade 3:
Offers a good summary with a reasonably broad differential diagnosis, but may miss some relevant history details or potential diagnoses. The clinical picture is clear but could be more detailed.
Grade 2:
Provides a basic summary with a limited differential diagnosis. Some key history details are missed or inadequately integrated into the assessment. The clinical picture is somewhat unclear or incomplete.
Grade 1:
The summary is inadequate with a narrow or incorrect differential diagnosis. Key history details are missing, and the clinical picture is unclear or disjointed.
Grade 0:
Not covered.

13. Empathy (5)
Grade 4:
Demonstrates consistent and active listening, regularly reflects the caregiver's emotions, offers reassurance and support when needed, and acknowledges the caregiver's concerns empathetically throughout the session.
Grade 3:
Shows empathy and active listening most of the time, with some reflection of the caregiver's emotions and occasional reassurance, but might miss opportunities to fully acknowledge or address the caregiver's concerns.
Grade 2:
Displays basic empathy, such as polite responses, but lacks depth in listening or addressing the caregiver's emotions. Rarely reflects emotions or provides reassurance, and may seem focused on the clinical rather than the personal.
Grade 1:
Little to no demonstration of empathy or active listening. The student may appear detached, clinical, or dismissive, with minimal acknowledgment of the caregiver's emotions or concerns.
Grade 0:
Not shown.

14. Interview Technique, Communication Skills & Overall Impression (15)
Grade 4:
The interview is well-organized with clear, logical flow. The student uses open-ended questions and effectively summarizes key points.
Grade 3:
The interview is generally well-organized with a good flow, but may have minor lapses in logic or sequencing. Uses mostly open-ended questions but may revert to closed-ended questions at times. Good but not exceptional communication skills.
Grade 2:
The interview has noticeable disorganization or awkward transitions. The student relies more on closed-ended questions, with some open-ended questions used inappropriately. Communication is basic and may lack clarity at times.
Grade 1:
The interview is poorly organized with significant lapses in logic and flow. The student primarily uses closed-ended questions and fails to effectively summarize or clarify key points. Communication is unclear or confusing.
Grade 0:
Not covered.

Weightings total 100.

Scoring method:
- Assign an integer grade of 0, 1, 2, 3, or 4 for each category.
- Convert to marks proportionally: score = (grade / 4) * weighting.
- Round category scores to 2 decimal places.
- Total score out of 100.
"""

# -----------------------------
# Prompt blocks
# -----------------------------
CASE_GENERATOR_INSTRUCTIONS = """
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
- Prefer common South African paediatric presentations and locally relevant psychosocial context.
- Vary socioeconomic setting, caregiver background, and home context where relevant.
- Avoid repetitive case archetypes.
- The case summary should be concise but sufficient for internal consistency.
- The opening line should be natural, brief, and non-medical.
- Do not include anything else outside those two sections.
"""

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
- Use socio-linguistically natural phrasing rather than formal textbook language.
- Give only the information asked for.
- Do not volunteer extra details.
- Do not over-inform.
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
- Do not sound medically sophisticated.
- For birth history, immunisations, nutrition, past history, family history, social history, travel, and development, answer only the exact question asked.
- For immunisation-related questions, align with the EPI 2024 schedule.
- If the learner asks something in a non-English language, politely ask them to repeat it in English.
- If the learner asks a confusing question, say something like: "Can you explain what exactly you want to know?"
- Where realistic, be uncertain about dates, sequences, or details rather than sounding scripted.

Transition rule:
- If the learner clearly indicates they are finished with the history, respond ONLY with:
  "Would you like to move to preceptor mode?"
"""

PRECEPTOR_PROMPT = """Preceptor mode.

1. Based on the history, what is your assessment?
2. What are your differential diagnoses?

When you are done, click either 'Give me Feedback' or 'Score my Performance'.
"""

FEEDBACK_INSTRUCTIONS_TEMPLATE = """
You are now an experienced paediatric preceptor evaluating a 5th-year undergraduate medical student at the University of the Witwatersrand.

The learner selected:
- Age group: {age_group}
- System: {system}

Hidden case summary:
{case_summary}

Your task:
- Review the entire transcript.
- Give concise, practical, balanced formative feedback.
- Do not score numerically.
- Use the rubric below to guide your comments, but produce narrative feedback only.
- Be honest and not overly generous.
- If important domains were omitted, say so clearly.

Important interpretive cautions:
- Do not infer that an area was covered unless it clearly appears in the transcript.
- For empathy, rapport, and communication quality, judge only what is supported by the text transcript.
- Do not over-credit politeness as empathy.
- Do not infer non-verbal skill, tone, rapport, warmth, or body language from transcript alone.
- If ambiguity or likely transcription issues affect interpretation, note that cautiously rather than inventing credit.

RUBRIC:
{rubric_text}

Output format:
# Feedback

## What the student did well
- 3 to 6 bullet points

## Missed opportunities
- 4 to 8 bullet points

## Comment on assessment and differentials
A short paragraph.

## Most important next-step improvements
- 3 to 5 bullet points
"""

SCORING_INSTRUCTIONS_TEMPLATE = """
You are now a strict paediatric examiner evaluating a 5th-year undergraduate medical student at the University of the Witwatersrand.

The learner selected:
- Age group: {age_group}
- System: {system}

Hidden case summary:
{case_summary}

You must mark STRICTLY and closely follow the rubric below.
Do not mark liberally or generously.
Do not give benefit of the doubt when evidence is absent.
If the transcript does not clearly show the learner covered an area, mark that area low or zero.
Do not infer that questions were asked unless they clearly appear in the transcript.

Important interpretive cautions:
- Empathy and interview technique are partly subjective and text transcripts cannot capture non-verbal behaviour, tone, or rapport.
- Therefore, score empathy and interview technique conservatively unless strong transcript evidence supports higher marks.
- Do not over-credit basic politeness as empathy.
- If transcript ambiguity or likely transcription issues exist, mention that uncertainty in comments, but do not award unsupported credit.
- If a learner statement is incomplete or garbled, interpret only the clearest plausible meaning and do not expand beyond the transcript.

RUBRIC:
{rubric_text}

Marking rules:
- Assign an integer grade of 0, 1, 2, 3, or 4 for each category.
- Convert that to the weighted score using:
  weighted score = (grade / 4) * weighting
- Round each weighted score to 2 decimal places.
- Then provide a total out of 100.
- Be internally consistent and strict.

Output format:
# Marking Report

Overall Score: <number> / 100

| Category | Weighting | Grade (0-4) | Score | Comments |
|---|---:|---:|---:|---|
| Main Complaint & Development of Symptoms | 25 | <grade> | <score> | <comment> |
| Danger Signs | 2 | <grade> | <score> | <comment> |
| Involved System Focused History | 5 | <grade> | <score> | <comment> |
| Other Systems Enquiry | 3 | <grade> | <score> | <comment> |
| Birth History | 5 | <grade> | <score> | <comment> |
| Immunization | 3 | <grade> | <score> | <comment> |
| Nutrition | 3 | <grade> | <score> | <comment> |
| Past Medical, Surgical, Medications & Allergies History | 5 | <grade> | <score> | <comment> |
| Family Medical History | 3 | <grade> | <score> | <comment> |
| Developmental Milestones | 3 | <grade> | <score> | <comment> |
| Social History & Travel | 3 | <grade> | <score> | <comment> |
| Assessment from History | 20 | <grade> | <score> | <comment> |
| Empathy | 5 | <grade> | <score> | <comment> |
| Interview Technique, Communication Skills & Overall Impression | 15 | <grade> | <score> | <comment> |

## Summary
### Strengths
- 2 to 5 bullet points

### Areas for improvement
- 4 to 8 bullet points
"""

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
        "can i present", "ready to present"
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
    prompt = f"Age group: {age_group}\nSystem: {system}"
    response = client.responses.create(
        model=MODEL_NAME,
        instructions=CASE_GENERATOR_INSTRUCTIONS,
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

def initialize_case(age_group: str, system: str):
    case_summary, opening_line = generate_case_bundle(age_group, system)
    st.session_state.case_summary = case_summary
    st.session_state.opening_line = opening_line
    st.session_state.messages = [
        {"role": "assistant", "content": opening_line}
    ]
    st.session_state.mode = "simulation"
    st.session_state.case_started = True
    st.session_state.presentation_done = False
    st.session_state.feedback_generated = None
    st.session_state.score_generated = None

def clear_case():
    st.session_state.locked_age = None
    st.session_state.locked_system = None
    st.session_state.case_summary = None
    st.session_state.opening_line = None
    st.session_state.messages = []
    st.session_state.mode = "simulation"
    st.session_state.case_started = False
    st.session_state.presentation_done = False
    st.session_state.feedback_generated = None
    st.session_state.score_generated = None

def selection_changed():
    if st.session_state.case_started:
        clear_case()

def call_feedback(age_for_case, system_for_case):
    instructions = FEEDBACK_INSTRUCTIONS_TEMPLATE.format(
        age_group=age_for_case,
        system=system_for_case,
        case_summary=st.session_state.case_summary,
        rubric_text=RUBRIC_TEXT
    )
    response = client.responses.create(
        model=MODEL_NAME,
        instructions=instructions,
        input=st.session_state.messages,
    )
    return response.output_text

def call_scoring(age_for_case, system_for_case):
    instructions = SCORING_INSTRUCTIONS_TEMPLATE.format(
        age_group=age_for_case,
        system=system_for_case,
        case_summary=st.session_state.case_summary,
        rubric_text=RUBRIC_TEXT
    )
    response = client.responses.create(
        model=MODEL_NAME,
        instructions=instructions,
        input=st.session_state.messages,
    )
    return response.output_text

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
if "case_started" not in st.session_state:
    st.session_state.case_started = False
if "presentation_done" not in st.session_state:
    st.session_state.presentation_done = False
if "feedback_generated" not in st.session_state:
    st.session_state.feedback_generated = None
if "score_generated" not in st.session_state:
    st.session_state.score_generated = None
if "selected_age" not in st.session_state:
    st.session_state.selected_age = "Select age group"
if "selected_system" not in st.session_state:
    st.session_state.selected_system = "Select system"

# -----------------------------
# UI selections
# -----------------------------
st.selectbox(
    "Choose age group",
    ["Select age group", "Neonate", "Infant", "1-5 years", "6-10 years", "11-19 years"],
    key="selected_age",
    on_change=selection_changed
)

st.selectbox(
    "Choose system",
    [
        "Select system",
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
    key="selected_system",
    on_change=selection_changed
)

# -----------------------------
# Top buttons
# -----------------------------
col1, col2 = st.columns(2)

with col1:
    if st.button("Start case"):
        if (
            st.session_state.selected_age != "Select age group"
            and st.session_state.selected_system != "Select system"
        ):
            st.session_state.locked_age = st.session_state.selected_age
            st.session_state.locked_system = st.session_state.selected_system
            initialize_case(
                st.session_state.locked_age,
                st.session_state.locked_system
            )
            st.rerun()
        else:
            st.warning("Please choose both an age group and a system before starting the case.")

with col2:
    if st.button("Reset conversation"):
        clear_case()
        st.session_state.selected_age = "Select age group"
        st.session_state.selected_system = "Select system"
        st.rerun()

age_for_case = st.session_state.locked_age
system_for_case = st.session_state.locked_system

# -----------------------------
# Status
# -----------------------------
st.caption(
    f"App {APP_VERSION} | Model {MODEL_NAME} | Rubric {RUBRIC_VERSION} | "
    f"Scoring prompt {SCORING_PROMPT_VERSION} | Caregiver prompt {CAREGIVER_PROMPT_VERSION}"
)

if not st.session_state.case_started:
    st.info("Choose an age group and a system, then click Start case.")
else:
    st.caption(
        f"Case context: {age_for_case} | {system_for_case} | Mode: {st.session_state.mode}"
    )

    voice_url = (
        "http://localhost:8000/?"
        + urllib.parse.urlencode({
            "age_group": st.session_state.locked_age,
            "system": st.session_state.locked_system,
            "case_summary": st.session_state.case_summary,
            "opening_line": st.session_state.opening_line,
        })
    )

    st.markdown("### Live voice mode")
    st.link_button("Open realtime voice case", voice_url)

# -----------------------------
# Display chat
# -----------------------------
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.write(m["content"])

# -----------------------------
# Chat input
# -----------------------------
if st.session_state.case_started and not st.session_state.presentation_done:
    if prompt := st.chat_input("Type your response…"):
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.write(prompt)

        assistant_text = ""

        if st.session_state.mode == "simulation":
            if looks_like_finished(prompt):
                st.session_state.mode = "offer_preceptor"
                assistant_text = "Would you like to move to preceptor mode?"
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
                assistant_text = PRECEPTOR_PROMPT
            elif looks_like_no(prompt):
                st.session_state.mode = "simulation"
                assistant_text = "Alright. I will stay in character as the caregiver/patient. Please continue your history."
            else:
                assistant_text = "Please say yes if you want to move to preceptor mode, or no if you want to continue the history."

        elif st.session_state.mode == "wait_for_presentation":
            st.session_state.mode = "post_presentation"
            st.session_state.presentation_done = True
            assistant_text = (
                "Thank you. You can now choose one of the options below:\n\n"
                "- Give me Feedback\n"
                "- Score my Performance"
            )

        st.session_state.messages.append({"role": "assistant", "content": assistant_text})

        with st.chat_message("assistant"):
            st.write(assistant_text)

# -----------------------------
# End-of-case buttons
# -----------------------------
if st.session_state.case_started and st.session_state.presentation_done:
    st.markdown("---")
    st.subheader("Post-case review")

    col3, col4 = st.columns(2)

    with col3:
        if st.button("Give me Feedback"):
            feedback_text = call_feedback(age_for_case, system_for_case)
            st.session_state.feedback_generated = feedback_text

    with col4:
        if st.button("Score my Performance"):
            score_text = call_scoring(age_for_case, system_for_case)
            st.session_state.score_generated = score_text

    if st.session_state.feedback_generated:
        st.markdown("## Feedback")
        st.markdown(st.session_state.feedback_generated)

    if st.session_state.score_generated:
        st.markdown("## Marking Report")
        st.markdown(st.session_state.score_generated)
