import json
import sqlite3
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "student_progress.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            study_number TEXT NOT NULL,
            session_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            interaction_mode TEXT,
            age_group TEXT,
            system TEXT,
            grade INTEGER,
            grade_label TEXT,
            diagnosis TEXT,
            strengths_json TEXT,
            missed_opportunities_json TEXT,
            key_missed_history_questions_json TEXT,
            overall_feedback TEXT,
            case_summary TEXT,
            transcript_text TEXT,
            duration_minutes INTEGER,
            UNIQUE(study_number, session_id)
        )
        """
    )

    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_sessions_study_number ON sessions(study_number)"
    )
    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON sessions(created_at)"
    )

    conn.commit()
    conn.close()


def _to_json(value: Any) -> str:
    if value is None:
        return "[]"
    return json.dumps(value, ensure_ascii=False)


def _from_json(value: str | None):
    if not value:
        return []
    try:
        return json.loads(value)
    except Exception:
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
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT OR REPLACE INTO sessions (
            study_number,
            session_id,
            created_at,
            interaction_mode,
            age_group,
            system,
            grade,
            grade_label,
            diagnosis,
            strengths_json,
            missed_opportunities_json,
            key_missed_history_questions_json,
            overall_feedback,
            case_summary,
            transcript_text,
            duration_minutes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            study_number,
            session_id,
            created_at,
            interaction_mode,
            age_group,
            system,
            grade,
            grade_label,
            diagnosis,
            _to_json(strengths),
            _to_json(missed_opportunities),
            _to_json(key_missed_history_questions),
            overall_feedback,
            case_summary,
            transcript_text,
            duration_minutes,
        ),
    )

    conn.commit()
    conn.close()


def get_student_sessions(study_number: str) -> list[dict]:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM sessions
        WHERE study_number = ?
        ORDER BY created_at DESC, id DESC
        """,
        (study_number,),
    )

    rows = cur.fetchall()
    conn.close()

    results = []
    for row in rows:
        results.append(
            {
                "id": row["id"],
                "study_number": row["study_number"],
                "session_id": row["session_id"],
                "created_at": row["created_at"],
                "interaction_mode": row["interaction_mode"],
                "age_group": row["age_group"],
                "system": row["system"],
                "grade": row["grade"],
                "grade_label": row["grade_label"],
                "diagnosis": row["diagnosis"],
                "strengths": _from_json(row["strengths_json"]),
                "missed_opportunities": _from_json(row["missed_opportunities_json"]),
                "key_missed_history_questions": _from_json(
                    row["key_missed_history_questions_json"]
                ),
                "overall_feedback": row["overall_feedback"],
                "case_summary": row["case_summary"],
                "transcript_text": row["transcript_text"],
                "duration_minutes": row["duration_minutes"],
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
