"""
worksheet_db.py — SQLite layer for the worksheet generator feature.

Uses the same get_conn() context manager as db.py, so worksheets live in the
same engagekids.db database as your children/observations tables.

Import it like:
    from worksheet_db import init_worksheet_tables, save_worksheet, ...

v2 addition: a worksheet_settings table storing worksheets-per-week per age
group, so the educator's chosen frequency persists across sessions instead
of resetting to a hardcoded default every time the app restarts.
"""

from datetime import datetime
from db import get_conn


def init_worksheet_tables():
    """Creates the worksheets, worksheet_feedback and worksheet_settings
    tables if they don't already exist."""
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS worksheets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                week_key TEXT NOT NULL,       -- e.g. "2026-W34"
                age_group TEXT NOT NULL,
                category TEXT NOT NULL,
                title TEXT,
                html_content TEXT,
                source TEXT,                  -- "auto" or "manual"
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS worksheet_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                age_group TEXT NOT NULL,
                week_key TEXT NOT NULL,
                feedback_text TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS worksheet_settings (
                age_group TEXT PRIMARY KEY,
                worksheets_per_week INTEGER NOT NULL DEFAULT 3
            )
        """)


# ---------- Worksheets ----------

def save_worksheet(week_key: str, age_group: str, category: str, title: str, html_content: str, source: str = "auto") -> int:
    """Saves one generated worksheet. Returns the new row's id."""
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO worksheets (week_key, age_group, category, title, html_content, source, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (week_key, age_group, category, title, html_content, source, datetime.now().isoformat()),
        )
        return cur.lastrowid


def get_worksheets_for_week(week_key: str, age_group: str) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM worksheets WHERE week_key = ? AND age_group = ? ORDER BY created_at",
            (week_key, age_group),
        ).fetchall()
        return [dict(r) for r in rows]


def get_recent_titles(age_group: str, lookback_weeks: int = 8) -> list[str]:
    """Returns recent worksheet titles for this age group, so generation prompts
    can be told what NOT to repeat."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT title FROM worksheets WHERE age_group = ? ORDER BY created_at DESC LIMIT ?",
            (age_group, lookback_weeks * 5),
        ).fetchall()
        return [r["title"] for r in rows if r["title"]]


def delete_worksheet(worksheet_id: int) -> None:
    """Removes a single saved worksheet by id — used to clear out stale
    entries generated under older category/age rules."""
    with get_conn() as conn:
        conn.execute("DELETE FROM worksheets WHERE id = ?", (worksheet_id,))


def get_worksheet_history(age_group: str, limit: int = 50) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT week_key, category, title, source FROM worksheets WHERE age_group = ? ORDER BY created_at DESC LIMIT ?",
            (age_group, limit),
        ).fetchall()
        return [dict(r) for r in rows]


# ---------- Feedback ----------

def save_feedback(age_group: str, week_key: str, feedback_text: str) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO worksheet_feedback (age_group, week_key, feedback_text, created_at) VALUES (?, ?, ?, ?)",
            (age_group, week_key, feedback_text, datetime.now().isoformat()),
        )
        return cur.lastrowid


def get_latest_feedback(age_group: str) -> str:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT feedback_text FROM worksheet_feedback WHERE age_group = ? ORDER BY created_at DESC LIMIT 1",
            (age_group,),
        ).fetchone()
        return row["feedback_text"] if row else ""


# ---------- Settings (worksheets per week) ----------

def get_worksheets_per_week(age_group: str, default: int = 3) -> int:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT worksheets_per_week FROM worksheet_settings WHERE age_group = ?",
            (age_group,),
        ).fetchone()
        return row["worksheets_per_week"] if row else default


def set_worksheets_per_week(age_group: str, count: int) -> None:
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO worksheet_settings (age_group, worksheets_per_week)
               VALUES (?, ?)
               ON CONFLICT(age_group) DO UPDATE SET worksheets_per_week = excluded.worksheets_per_week""",
            (age_group, count),
        )


# ---------- Quick manual test ----------
if __name__ == "__main__":
    from db import init_db
    init_db()
    init_worksheet_tables()
    save_worksheet("2026-W34", "Preschool 3-5 years", "Numeracy (counting)", "Count the Dinosaurs", "<html>test</html>", source="auto")
    set_worksheets_per_week("Preschool 3-5 years", 4)
    print("This week:", get_worksheets_for_week("2026-W34", "Preschool 3-5 years"))
    print("Recent titles:", get_recent_titles("Preschool 3-5 years"))
    print("Worksheets/week:", get_worksheets_per_week("Preschool 3-5 years"))