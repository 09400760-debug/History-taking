import json
from typing import Any

import streamlit as st
from supabase import create_client, Client

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def _to_json(value: Any) -> str:
    if value is None:
        return "[]"
    return json.dumps(value, ensure_ascii=False)


def _from_json(value: Any):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        if not value.strip():
            return []
        try:
            return json.loads(value)
        except Exception:
            return []
    return []


def save_session_result(
    study_number: str,
    session_id: str,
    created_at: str,
    interaction_mode: str,
    age_group: str,
    system: str,
    grade: int | None,
    grade_label: str | None,
    diagnosis: str | None,
    strengths: list[str] | None,
    missed_opportunities: list[str] | None,
    key_missed_history_questions: list[str] | None,
    overall_feedback: str | None,
    case_summary: str | None,
    transcript_text: str | None,
    duration_minutes: int | None,
):
    payload = {
        "study_number": study_number,
        "session_id": session_id,
        "created_at": created_at,
        "interaction_mode": interaction_mode,
        "age_group": age_group,
        "system": system,
        "grade": grade,
        "grade_label": grade_label,
        "diagnosis": diagnosis,
        "strengths_json": _to_json(strengths),
        "missed_opportunities_json": _to_json(missed_opportunities),
        "key_missed_history_questions_json": _to_json(key_missed_history_questions),
        "overall_feedback": overall_feedback,
        "case_summary": case_summary,
        "transcript_text": transcript_text,
        "duration_minutes": duration_minutes,
    }

    existing = (
        supabase.table("sessions")
        .select("id")
        .eq("study_number", study_number)
        .eq("session_id", session_id)
        .execute()
    )

    existing_rows = existing.data if hasattr(existing, "data") and existing.data else []

    if existing_rows:
        row_id = existing_rows[0]["id"]
        supabase.table("sessions").update(payload).eq("id", row_id).execute()
    else:
        supabase.table("sessions").insert(payload).execute()


def get_student_sessions(study_number: str) -> list[dict]:
    response = (
        supabase.table("sessions")
        .select("*")
        .eq("study_number", study_number)
        .order("created_at", desc=True)
        .execute()
    )

    rows = response.data if hasattr(response, "data") and response.data else []

    results = []
    for row in rows:
        results.append(
            {
                "id": row.get("id"),
                "study_number": row.get("study_number"),
                "session_id": row.get("session_id"),
                "created_at": row.get("created_at"),
                "interaction_mode": row.get("interaction_mode"),
                "age_group": row.get("age_group"),
                "system": row.get("system"),
                "grade": row.get("grade"),
                "grade_label": row.get("grade_label"),
                "diagnosis": row.get("diagnosis"),
                "strengths": _from_json(row.get("strengths_json")),
                "missed_opportunities": _from_json(row.get("missed_opportunities_json")),
                "key_missed_history_questions": _from_json(
                    row.get("key_missed_history_questions_json")
                ),
                "overall_feedback": row.get("overall_feedback"),
                "case_summary": row.get("case_summary"),
                "transcript_text": row.get("transcript_text"),
                "duration_minutes": row.get("duration_minutes"),
            }
        )

    return results


def get_recent_sessions(study_number: str, limit: int = 3) -> list[dict]:
    sessions = get_student_sessions(study_number)
    return sessions[:limit]


def get_student_summary(study_number: str) -> dict:
    sessions = get_student_sessions(study_number)

    if not sessions:
        return {
            "total_cases": 0,
            "average_grade": None,
            "recent_strengths": [],
            "recent_missed_opportunities": [],
            "recent_systems": [],
        }

    graded = [s["grade"] for s in sessions if isinstance(s.get("grade"), int)]
    average_grade = round(sum(graded) / len(graded), 2) if graded else None

    recent_strengths = []
    recent_missed = []
    recent_systems = []

    for session in sessions[:3]:
        recent_strengths.extend(session.get("strengths", []))
        recent_missed.extend(session.get("missed_opportunities", []))
        if session.get("system"):
            recent_systems.append(session["system"])

    return {
        "total_cases": len(sessions),
        "average_grade": average_grade,
        "recent_strengths": recent_strengths[:6],
        "recent_missed_opportunities": recent_missed[:6],
        "recent_systems": recent_systems,
    }


def build_prior_performance_context(study_number: str, max_sessions: int = 3) -> str:
    sessions = get_recent_sessions(study_number, limit=max_sessions)

    if not sessions:
        return "No previous recorded sessions for this student."

    lines = [
        f"This student has completed {len(get_student_sessions(study_number))} recorded customized sessions.",
        "Recent prior performance:",
    ]

    for i, session in enumerate(sessions, start=1):
        lines.append(
            f"Session {i}: "
            f"grade={session.get('grade')} "
            f"({session.get('grade_label')}); "
            f"system={session.get('system')}; "
            f"diagnosis={session.get('diagnosis')}"
        )

        strengths = session.get("strengths", [])
        missed = session.get("missed_opportunities", [])

        if strengths:
            lines.append(f"  Strengths: {' | '.join(strengths[:3])}")
        if missed:
            lines.append(f"  Missed opportunities: {' | '.join(missed[:3])}")

    lines.append(
        "When generating feedback, note improvement or recurring weaknesses where appropriate."
    )

    return "\n".join(lines)
