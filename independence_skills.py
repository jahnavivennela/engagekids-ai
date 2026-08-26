"""
independence_skills.py

Self-help / independence skills builder for EngageKids AI.

Two parts:

1. NEW PLAN — educator enters an age group, a skill (e.g. "putting on a
   t-shirt"), and optionally a free-text description of the situation
   (what's been tried, how long, etc). Generates a 4-part plan:
     - ADAPTED_TASK   : easier version of the real task
     - RELATED_GAME    : a game building the same motion
     - SENSORY_PRESKILL: grip/coordination pre-skill activity
     - TRY_DURATION    : how long to try it and when (e.g. "about a week,
       during the morning dressing routine")

2. FOLLOW UP — educator picks a previously generated plan for this age
   group that hasn't been marked resolved yet, describes how it went
   (no change / some progress / working), and gets a NEW escalation
   step — genuinely different from what was already tried, building on
   the outcome. This is saved linked to the original plan (parent_id),
   so a skill can have a whole progression chain over time, not just
   one suggestion.

Grounded in the same milestones data used elsewhere in the app, and
Groq for text generation (consistent with the rest of EngageKids AI).
Image generation, if enabled, reuses the same OPENAI_API_KEY already in
st.secrets for the worksheet generator — separate function/call from
worksheet_generator.py's image_gen.py, so it won't interfere with that,
but billed to the same OpenAI account.

Self-contained: has its own SQLite table (via the shared get_conn() from
db.py, same as worksheet_db.py) so it doesn't depend on activity_db.py
internals. Drop this file next to engagekids_v1.py and wire it in with
the lines shown at the bottom of this file when ready.
"""

import re
import base64
from datetime import datetime, timedelta

import requests
import streamlit as st

from milestones_data import AGE_BANDS, milestones_summary_text
from db import get_conn  # same shared connection helper worksheet_db.py and db.py use


# ==========================================
# STORAGE
# ==========================================

def init_independence_table():
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS independence_skills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                age_group TEXT NOT NULL,
                skill TEXT NOT NULL,
                situation_description TEXT,
                adapted_task TEXT,
                related_game TEXT,
                sensory_preskill TEXT,
                try_duration TEXT,
                outcome TEXT,
                parent_id INTEGER,
                created_at TEXT DEFAULT (datetime('now'))
            )
            """
        )
        # Columns added after the original release — add them to any
        # pre-existing table without losing saved plans (same pattern
        # worksheet_db.py uses for used_items).
        existing_cols = {row["name"] for row in conn.execute("PRAGMA table_info(independence_skills)").fetchall()}
        for col in ("situation_description", "try_duration", "outcome", "parent_id"):
            if col not in existing_cols:
                conn.execute(f"ALTER TABLE independence_skills ADD COLUMN {col} TEXT")


def save_independence_result(age_group, skill, situation_description, adapted_task,
                              related_game, sensory_preskill, try_duration, parent_id=None):
    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO independence_skills
                (age_group, skill, situation_description, adapted_task, related_game,
                 sensory_preskill, try_duration, parent_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (age_group, skill, situation_description, adapted_task, related_game,
             sensory_preskill, try_duration, parent_id, datetime.now().isoformat()),
        )
        return cur.lastrowid


def save_followup_outcome(plan_id, outcome_text):
    """Marks a plan as followed-up-on, so it stops showing in the
    'still open' list for the follow-up dropdown."""
    with get_conn() as conn:
        conn.execute(
            "UPDATE independence_skills SET outcome = ? WHERE id = ?",
            (outcome_text, plan_id),
        )


def get_recent_independence_ideas(age_group, days=75):
    """Flat list of previously-suggested activity lines for this age group
    in the last `days`, so the AI is told to avoid repeating them."""
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT adapted_task, related_game, sensory_preskill
            FROM independence_skills
            WHERE age_group = ? AND created_at >= ?
            """,
            (age_group, cutoff),
        ).fetchall()

    ideas = []
    for row in rows:
        for val in (row["adapted_task"], row["related_game"], row["sensory_preskill"]):
            if val:
                ideas.append(val.strip())
    return ideas


def get_open_plans(age_group, limit=25):
    """Plans for this age group that haven't had an outcome recorded yet —
    these are the ones that can be followed up on."""
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT * FROM independence_skills
            WHERE age_group = ? AND (outcome IS NULL OR outcome = '')
            ORDER BY created_at DESC LIMIT ?
            """,
            (age_group, limit),
        ).fetchall()
        return [dict(r) for r in rows]


# ==========================================
# PARSING
# ==========================================

def _extract_section(text, tag):
    """Pulls the content after 'TAG:' up to the next known tag or end of text."""
    pattern = rf"{tag}:\s*(.*?)(?=\n[A-Z_]+:|$)"
    match = re.search(pattern, text, re.DOTALL)
    return match.group(1).strip() if match else ""


# ==========================================
# OPTIONAL IMAGE — reuses the same OPENAI_API_KEY already in st.secrets for
# the worksheet generator. Separate function/call from image_gen.py, so it
# won't interfere with that code. If the key is missing or the call fails
# for any reason, this just returns None and the text-only plan still
# works fine — it never blocks the main feature.
# ==========================================

def generate_activity_image(description: str):
    api_key = st.secrets.get("OPENAI_API_KEY")
    if not api_key:
        return None

    prompt = (
        "A simple, warm, colorful flat-cartoon illustration for an early childhood "
        "educator's activity card, showing this game in action: "
        f"{description}. Single clear scene, no text or words anywhere in the image, "
        "friendly and child-safe, plain light background."
    )

    try:
        resp = requests.post(
            "https://api.openai.com/v1/images/generations",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": "gpt-image-1",
                "prompt": prompt,
                "size": "1024x1024",
                "n": 1,
            },
            timeout=60,
        )
        resp.raise_for_status()
        item = resp.json()["data"][0]

        if item.get("b64_json"):
            return base64.b64decode(item["b64_json"])
        if item.get("url"):
            img_resp = requests.get(item["url"], timeout=30)
            img_resp.raise_for_status()
            return img_resp.content
    except Exception as e:
        print(f"[independence_skills] image generation failed: {e}")
    return None


# ==========================================
# GENERATION
# ==========================================

def _build_plan_prompt(age_group, skill, situation_description, avoid_text, is_followup, prior_context=""):
    situation_block = (
        f'\nAdditional context from the educator on what has been tried and how it\'s going:\n"{situation_description}"\n'
        if situation_description and situation_description.strip() else ""
    )

    if is_followup:
        task_line = (
            f"This is a FOLLOW-UP. The child already tried the plan below and here's how it went:\n{prior_context}\n\n"
            "Based on that outcome, give the NEXT step — genuinely different from what was already tried, "
            "either a harder progression (if it worked / showed some progress) or a different approach entirely "
            "(if there was no change at all)."
        )
    else:
        task_line = "Give a first plan to help this child build independence in this skill."

    return f"""A child in the {age_group} age band is struggling with this self-help skill: "{skill}"
{situation_block}
Developmental milestones for this age (ground every suggestion in these, don't invent unrelated skills):
{milestones_summary_text(age_group)}

{avoid_text}

{task_line}

Use PLAIN, warm, practical language an educator or parent can act on immediately — no clinical or
therapy language. Each should be do-able with ordinary household or classroom items only. Keep EACH
section to 2 short sentences maximum — this is a quick activity card, not an essay.

Respond in EXACTLY this format, nothing else:

ADAPTED_TASK: A simplified or easier version of the real task itself, so the child can succeed at an
easier version before the full skill. Max 2 sentences.

RELATED_GAME: A playful game or activity that builds the same underlying motion or muscle group as
the real task, without it feeling like practice. Max 2 sentences.

SENSORY_PRESKILL: A sensory or grip/coordination-building activity for a child not yet ready to
attempt the task at all — the foundational skill underneath it. Max 2 sentences.

TRY_DURATION: How long to try this before checking progress, and roughly when in the day it fits best
(e.g. "About a week, during the morning dressing routine" or "3-4 tries over a few days, whenever it's
calm — avoid rushed moments"). One short sentence.
"""


def _run_generation(client, age_group, skill, situation_description, is_followup=False, prior_context="", parent_id=None):
    avoid_ideas = get_recent_independence_ideas(age_group, days=75)
    avoid_text = (
        "Activities already suggested for this age group in the last ~2-3 months — do NOT repeat any "
        "of these, come up with genuinely different ones: " + "; ".join(avoid_ideas)
    ) if avoid_ideas else ""

    prompt = _build_plan_prompt(age_group, skill, situation_description, avoid_text, is_followup, prior_context)

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert early childhood educator specialising in self-help and "
                    "independence skill development, grounded strictly in the developmental "
                    "milestones provided. You never use clinical, diagnostic, or therapy-style "
                    "language — only practical, warm, classroom/home-ready suggestions. You always "
                    "stay within the requested length."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        max_tokens=1100,
    )

    full_text = response.choices[0].message.content
    adapted_task = _extract_section(full_text, "ADAPTED_TASK")
    related_game = _extract_section(full_text, "RELATED_GAME")
    sensory_preskill = _extract_section(full_text, "SENSORY_PRESKILL")
    try_duration = _extract_section(full_text, "TRY_DURATION")

    if not (adapted_task and related_game and sensory_preskill):
        return None, full_text

    new_id = save_independence_result(
        age_group, skill, situation_description, adapted_task, related_game,
        sensory_preskill, try_duration, parent_id=parent_id,
    )
    return {
        "id": new_id,
        "adapted_task": adapted_task,
        "related_game": related_game,
        "sensory_preskill": sensory_preskill,
        "try_duration": try_duration,
    }, full_text


def _render_plan(plan, want_image):
    st.success("Plan ready!")
    st.markdown(f"**👕 Adapted / Easier Version**\n\n{plan['adapted_task']}")
    st.markdown(f"**🎮 Related Game**\n\n{plan['related_game']}")

    if want_image:
        with st.spinner("Generating illustration..."):
            img_bytes = generate_activity_image(plan["related_game"])
        if img_bytes:
            st.image(img_bytes, caption="Related game — illustration", width=300)
        else:
            st.caption("Couldn't generate an image (check OPENAI_API_KEY in st.secrets) — text above still applies.")

    st.markdown(f"**✋ Sensory / Pre-Skill Activity**\n\n{plan['sensory_preskill']}")
    if plan.get("try_duration"):
        st.info(f"⏱️ **Try this for:** {plan['try_duration']}")


# ==========================================
# STREAMLIT TAB
# ==========================================

def independence_skills_tab(client):
    st.markdown("### 🧦 Independence Skills Builder")
    st.caption(
        "For self-help skills a child is still building — dressing, grip, shoes, feeding, etc. "
        "Gives a graduated plan with how long to try it, and lets you check back later for the next step."
    )

    mode = st.radio(
        "What do you need?",
        ["🆕 New plan", "🔁 Follow up on a previous plan"],
        key="indep_mode",
        horizontal=True,
    )

    want_image = st.checkbox(
        "🖼️ Also generate an illustration of the game",
        key="indep_want_image",
        help="Uses the same OPENAI_API_KEY already in st.secrets. Skipped automatically if not set.",
    )

    # ---------------- NEW PLAN ----------------
    if mode == "🆕 New plan":
        col1, col2 = st.columns(2)
        with col1:
            age_group = st.selectbox("🎂 Age group", AGE_BANDS, key="indep_age_group")
        with col2:
            skill = st.text_input(
                "🎯 Skill the child is struggling with",
                key="indep_skill",
                placeholder="e.g. putting on a t-shirt, gripping a pencil, wearing shoes",
            )

        situation_description = st.text_area(
            "📝 Tell us more (optional) — what's already been tried, how long, anything specific",
            key="indep_situation",
            placeholder="e.g. Tried for 2 weeks with hand-over-hand help, still can't get the arm through the sleeve on his own",
        )

        if st.button("Generate Independence Plan", type="primary"):
            if not skill.strip():
                st.warning("Enter a skill first (e.g. 'putting on a t-shirt').")
                return
            with st.spinner("Generating plan..."):
                plan, raw = _run_generation(client, age_group, skill, situation_description)
            if plan is None:
                st.warning("Output didn't fully match the expected format — showing raw response below.")
                st.markdown(raw)
            else:
                _render_plan(plan, want_image)
                st.caption("Saved — you can check back on this one later from 'Follow up on a previous plan'.")

    # ---------------- FOLLOW UP ----------------
    else:
        age_group = st.selectbox("🎂 Age group", AGE_BANDS, key="indep_followup_age_group")
        open_plans = get_open_plans(age_group)

        if not open_plans:
            st.info("No open plans yet for this age group — generate a new plan first, then come back here to follow up on it.")
            return

        options = {
            f"{p['skill']} — started {p['created_at'][:10]}": p for p in open_plans
        }
        chosen_label = st.selectbox("Which plan are you following up on?", list(options.keys()), key="indep_followup_choice")
        chosen = options[chosen_label]

        with st.expander("What was suggested last time"):
            st.markdown(f"**👕 Adapted task:** {chosen['adapted_task']}")
            st.markdown(f"**🎮 Related game:** {chosen['related_game']}")
            st.markdown(f"**✋ Sensory pre-skill:** {chosen['sensory_preskill']}")
            if chosen.get("try_duration"):
                st.caption(f"⏱️ Was suggested for: {chosen['try_duration']}")

        outcome = st.radio(
            "How did it go?",
            ["No change yet", "Some progress", "Working well — ready for the next step"],
            key="indep_outcome",
        )
        outcome_notes = st.text_area(
            "Any notes? (optional)",
            key="indep_outcome_notes",
            placeholder="e.g. Managed the sleeve but still needs help pulling it over the head",
        )

        if st.button("Get Next Step", type="primary"):
            prior_context = (
                f"Original skill: {chosen['skill']}\n"
                f"What was suggested: adapted task — {chosen['adapted_task']}; "
                f"game — {chosen['related_game']}; sensory pre-skill — {chosen['sensory_preskill']}\n"
                f"Outcome: {outcome}. {outcome_notes or ''}"
            )
            save_followup_outcome(chosen["id"], f"{outcome}. {outcome_notes or ''}".strip())

            with st.spinner("Generating next step..."):
                plan, raw = _run_generation(
                    client, age_group, chosen["skill"], outcome_notes,
                    is_followup=True, prior_context=prior_context, parent_id=chosen["id"],
                )
            if plan is None:
                st.warning("Output didn't fully match the expected format — showing raw response below.")
                st.markdown(raw)
            else:
                st.markdown("#### Next step")
                _render_plan(plan, want_image)


# ==========================================
# TO WIRE THIS INTO engagekids_v1.py:
#
# from independence_skills import init_independence_table, independence_skills_tab
#
# init_independence_table()   # next to init_activity_tables()
#
# with st.container(border=True):
#     independence_skills_tab(client)   # anywhere you want it in the page flow
# ==========================================