from supabase import create_client
import streamlit as st
from datetime import datetime

# Load from Streamlit secrets
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def save_session_result(
    study_number,
    session_id,
    system,
    age_group,
    interaction_mode,
    grade,
    score,
    diagnosis,
    transcript,
    feedback
):
    data = {
        "study_number": study_number,
        "session_id": session_id,
        "created_at": datetime.utcnow().isoformat(),
        "system": system,
        "age_group": age_group,
        "interaction_mode": interaction_mode,
        "grade": grade,
        "score": score,
        "diagnosis": diagnosis,
        "transcript": transcript,
        "feedback": feedback,
    }

    supabase.table("sessions").insert(data).execute()


def get_student_sessions(study_number):
    response = supabase.table("sessions") \
        .select("*") \
        .eq("study_number", study_number) \
        .order("created_at", desc=True) \
        .execute()

    return response.data if response.data else []
