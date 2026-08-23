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
        conn.execute("""
            CREATE TABLE IF NOT EXISTS home_ideas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                idea_text TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS magic_tricks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                age_group TEXT,
                name TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        # age_group was added after the original release — add it to any
        # pre-existing database file without losing saved tricks. Existing
        # rows get NULL, which get_recent_magic_tricks treats as "any age"
        # so old history still counts as used rather than silently vanishing.
        existing_cols = {row["name"] for row in conn.execute("PRAGMA table_info(magic_tricks)").fetchall()}
        if "age_group" not in existing_cols:
            conn.execute("ALTER TABLE magic_tricks ADD COLUMN age_group TEXT")


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


# ---------- Home Extension Message (repeat-avoidance for "try at home" ideas) ----------

def save_home_ideas(idea_texts: list[str]):
    """Saves each 'try at home' idea (short line, not the whole message) so
    future messages avoid repeating the same idea for a while."""
    with get_conn() as conn:
        now = datetime.now().isoformat()
        for idea in idea_texts:
            idea = idea.strip()
            if idea:
                conn.execute(
                    "INSERT INTO home_ideas (idea_text, created_at) VALUES (?, ?)",
                    (idea, now),
                )


def get_recent_home_ideas(days: int = 75, limit: int = 60) -> list[str]:
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT idea_text FROM home_ideas WHERE created_at >= ? ORDER BY created_at DESC LIMIT ?",
            (cutoff, limit),
        ).fetchall()
        return [r["idea_text"] for r in rows]


# ---------- Weekly Magic Trick (household-item science wow-moments) ----------

def save_magic_trick(name: str, age_group: str = None):
    if not name:
        return
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO magic_tricks (age_group, name, created_at) VALUES (?, ?, ?)",
            (age_group, name, datetime.now().isoformat()),
        )


def get_recent_magic_tricks(age_group: str = None, days: int = 60, limit: int = 30) -> list[str]:
    """Recent tricks for THIS age group only, so a trick used for the 0-1
    room doesn't block a different, perfectly good trick for the 4-5 room.
    Rows saved before age-group tracking existed (NULL) have no age on
    record, so they're still counted as "used" for every age group rather
    than silently forgotten."""
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT name FROM magic_tricks
               WHERE (age_group = ? OR age_group IS NULL) AND created_at >= ?
               ORDER BY created_at DESC LIMIT ?""",
            (age_group, cutoff, limit),
        ).fetchall()
        return [r["name"] for r in rows]