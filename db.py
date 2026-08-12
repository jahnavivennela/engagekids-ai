"""
db.py — SQLite layer for EngageKids AI

Drop this file into your Streamlit project folder (same folder as your main app.py).
Import it like:
    from db import init_db, add_child, get_children, add_observation, get_observations

Call init_db() once when your app starts (Streamlit re-runs the script on every
interaction, but CREATE TABLE IF NOT EXISTS makes this safe to call every time).
"""

import sqlite3
from contextlib import contextmanager
from datetime import date

DB_PATH = "engagekids.db"


@contextmanager
def get_conn():
    """Yields a connection with foreign keys enabled, commits on success, closes always."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row  # lets us access columns by name, e.g. row["name"]
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    """Creates the children and observations tables if they don't already exist."""
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS children (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                age_group TEXT,           -- e.g. "3-4 years"
                interests TEXT,           -- free text, e.g. "dinosaurs, drawing, running"
                created_at TEXT DEFAULT (date('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS observations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                child_id INTEGER NOT NULL,
                obs_date TEXT DEFAULT (date('now')),
                observation_text TEXT,    -- what you (the educator) saw/typed in
                activity TEXT,            -- the activity that was done
                skill_note TEXT,          -- plain-language skill being developed (AI-generated)
                parent_note TEXT,         -- the parent-facing note (AI-generated)
                home_suggestion TEXT,     -- suggested home-repeat activity (AI-generated)
                FOREIGN KEY (child_id) REFERENCES children(id) ON DELETE CASCADE
            )
        """)


# ---------- Children ----------

def add_child(name: str, age_group: str = "", interests: str = "") -> int:
    """Adds a child, returns the new child's id."""
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO children (name, age_group, interests) VALUES (?, ?, ?)",
            (name, age_group, interests),
        )
        return cur.lastrowid


def get_children() -> list[dict]:
    """Returns all children as a list of dicts, e.g. for populating a dropdown."""
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM children ORDER BY name").fetchall()
        return [dict(r) for r in rows]


def get_child(child_id: int) -> dict | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM children WHERE id = ?", (child_id,)).fetchone()
        return dict(row) if row else None


def update_child_interests(child_id: int, interests: str):
    with get_conn() as conn:
        conn.execute("UPDATE children SET interests = ? WHERE id = ?", (interests, child_id))


def delete_child(child_id: int):
    """Deletes a child and all their observations (CASCADE)."""
    with get_conn() as conn:
        conn.execute("DELETE FROM children WHERE id = ?", (child_id,))


# ---------- Observations ----------

def add_observation(
    child_id: int,
    observation_text: str = "",
    activity: str = "",
    skill_note: str = "",
    parent_note: str = "",
    home_suggestion: str = "",
    obs_date: str = None,
) -> int:
    """Saves one observation/note entry for a child. Returns the new row's id."""
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO observations
               (child_id, obs_date, observation_text, activity, skill_note, parent_note, home_suggestion)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                child_id,
                obs_date or date.today().isoformat(),
                observation_text,
                activity,
                skill_note,
                parent_note,
                home_suggestion,
            ),
        )
        return cur.lastrowid


def get_observations(child_id: int, limit: int = None) -> list[dict]:
    """Returns a child's observations, most recent first. Use this to build their history."""
    with get_conn() as conn:
        query = "SELECT * FROM observations WHERE child_id = ? ORDER BY obs_date DESC, id DESC"
        if limit:
            query += f" LIMIT {int(limit)}"
        rows = conn.execute(query, (child_id,)).fetchall()
        return [dict(r) for r in rows]


def get_latest_observation(child_id: int) -> dict | None:
    obs = get_observations(child_id, limit=1)
    return obs[0] if obs else None


# ---------- Quick manual test ----------
if __name__ == "__main__":
    init_db()
    cid = add_child("Raden", "3-5 years", "dinosaurs, building blocks")
    add_observation(
        child_id=cid,
        observation_text="Built a tall tower and named each block a dinosaur",
        activity="Block building with dinosaur figures",
        skill_note="Fine motor skills and early counting/sorting",
        parent_note="Today Raden built a tall tower, carefully balancing each block and naming them after dinosaurs — great focus and hand control!",
        home_suggestion="Try stacking cups or blocks at home and counting them together as he builds.",
    )
    print("Children:", get_children())
    print("Observations for Raden:", get_observations(cid))