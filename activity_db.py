"""
activity_db.py

Repeat-avoidance for the Quick Activity Suggester and Weekly Program
Planner — same pattern worksheet_db.py already uses for worksheets, so
neither generator hands back something it already suggested recently.

Uses the same get_conn() from db.py, so this lives in the same
engagekids.db database as everything else.
"""

from datetime import datetime, timedelta
from db import get_conn


def init_activity_tables():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS quick_activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                age_group TEXT NOT NULL,
                name TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS weekly_experiences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                age_group TEXT NOT NULL,
                week_key TEXT NOT NULL,
                theme TEXT,
                experience_name TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)


# ---------- Quick Activity Suggester ----------

def save_quick_activity(age_group: str, name: str):
    if not name:
        return
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO quick_activities (age_group, name, created_at) VALUES (?, ?, ?)",
            (age_group, name, datetime.now().isoformat()),
        )


def get_recent_quick_activity_names(age_group: str, days: int = 90, limit: int = 60) -> list[str]:
    """Names used in the last `days` days for this age group, most recent
    first, capped at `limit` so the prompt doesn't grow unbounded."""
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT DISTINCT name FROM quick_activities
               WHERE age_group = ? AND created_at >= ?
               ORDER BY created_at DESC LIMIT ?""",
            (age_group, cutoff, limit),
        ).fetchall()
        return [r["name"] for r in rows]


# ---------- Weekly Program Planner ----------

def save_weekly_experiences(age_group: str, week_key: str, theme: str, experience_names: list[str]):
    with get_conn() as conn:
        now = datetime.now().isoformat()
        for name in experience_names:
            name = name.strip()
            if name:
                conn.execute(
                    """INSERT INTO weekly_experiences (age_group, week_key, theme, experience_name, created_at)
                       VALUES (?, ?, ?, ?, ?)""",
                    (age_group, week_key, theme, name, now),
                )


def get_recent_experience_names(age_group: str, days: int = 90, limit: int = 150) -> list[str]:
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT DISTINCT experience_name FROM weekly_experiences
               WHERE age_group = ? AND created_at >= ?
               ORDER BY created_at DESC LIMIT ?""",
            (age_group, cutoff, limit),
        ).fetchall()
        return [r["experience_name"] for r in rows]