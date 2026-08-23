from groq import Groq
import streamlit as st
from observation import observation_tab
from learning_story import learning_story_tab
from story_generator import story_generator_tab
from worksheet_generator import worksheet_tab, get_week_key
from ui_theme import apply_theme, section_divider, section_header, section_anchor, render_sidebar_nav
from milestones_data import AGE_BANDS, milestones_summary_text
import re
from activity_db import (
    init_activity_tables, save_quick_activity, get_recent_quick_activity_names,
    save_weekly_experiences, get_recent_experience_names,
    save_home_ideas, get_recent_home_ideas,
    save_magic_trick, get_recent_magic_tricks,
)
from db import init_db, add_child, get_children, get_child, add_observation, get_observations

# Setup
api_key = st.secrets["GROQ_API_KEY"]
client = Groq(api_key=api_key)

# Initialize the database (safe to call every run — CREATE TABLE IF NOT EXISTS)
init_db()
init_activity_tables()

# Page config
st.set_page_config(
    page_title="EngageKids AI",
    page_icon="🌟",
    layout="wide"
)

# Hide default Streamlit branding
hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# Apply the shared color palette, card styling, dividers, and watermark
apply_theme()
render_sidebar_nav()

# Header
st.markdown(
    """
    <div style="text-align: center; padding: 10px 0;">
        <h1 style="color: #FF6B6B; margin-bottom: 0; font-size: 30px; font-weight: 600;">🌟 EngageKids AI</h1>
        <p style="color: #666666; font-size: 16px; margin-top: 5px;">
            Real-time, classroom-tested support for early childhood educators
        </p>
    </div>
    """,
    unsafe_allow_html=True
)
st.markdown("---")

# ==========================================
# CHILD SELECTOR (used by Child History below)
# ==========================================

with st.container(border=True):
    st.markdown(section_header("👤", "Select Child", "select-child", "coral"), unsafe_allow_html=True)

    children = get_children()
    child_names = {c["name"]: c["id"] for c in children}

    col_a, col_b = st.columns([2, 1])
    with col_a:
        selected_name = st.selectbox(
            "Choose a child (or add a new one)",
            options=["— None selected —"] + list(child_names.keys()) + ["+ Add new child"]
        )

    child_id = None
    child_record = None

    if selected_name == "+ Add new child":
        with st.form("add_child_form"):
            new_name = st.text_input("🧒 Child's name")
            new_age = st.selectbox("🎂 Age group", AGE_BANDS)
            new_interests = st.text_input("⭐ Interests (comma separated, e.g. dinosaurs, drawing, running)")
            submitted = st.form_submit_button("Save child")
            if submitted and new_name:
                child_id = add_child(new_name, new_age, new_interests)
                st.success(f"Added {new_name}")
                st.rerun()

    elif selected_name != "— None selected —":
        child_id = child_names[selected_name]
        child_record = get_child(child_id)

    if child_id is None:
        st.info("Select or add a child above to build their saved history below.")
    else:
        st.caption(f"Working with: **{selected_name}** ({child_record['age_group']}) — interests: {child_record['interests'] or 'not set'}")

section_divider("coral")

# ==========================================
# SITUATION-BASED SUPPORT
# ==========================================

st.markdown(section_anchor("situation-support"), unsafe_allow_html=True)
with st.container(border=True):
    observation_tab(client)

section_divider("yellow")

# ==========================================
# LEARNING STORY GENERATOR
# ==========================================

st.markdown(section_anchor("learning-story"), unsafe_allow_html=True)
with st.container(border=True):
    learning_story_tab(client)

section_divider("lavender")

# ==========================================
# CHILD HISTORY
# ==========================================

if child_id is not None:
    with st.container(border=True):
        st.markdown(section_header("📖", f"{selected_name}\'s History", "child-history", "lavender"), unsafe_allow_html=True)

        history = get_observations(child_id)
        if not history:
            st.caption("No saved entries yet for this child.")
        else:
            for obs in history:
                label = obs["activity"][:60] + "..." if obs["activity"] and len(obs["activity"]) > 60 else (obs["activity"] or "Note")
                with st.expander(f"{obs['obs_date']} — {label}"):
                    if obs["observation_text"]:
                        st.write(f"**Context:** {obs['observation_text']}")
                    if obs["activity"]:
                        st.write(f"**Activity:**\n\n{obs['activity']}")
                    if obs["parent_note"]:
                        st.write(f"**Parent note:**\n\n{obs['parent_note']}")
                    if obs["home_suggestion"]:
                        st.caption(f"Home / follow-up suggestions:\n\n{obs['home_suggestion']}")

    section_divider("peach")

# ==========================================
# QUICK ACTIVITY SUGGESTER
# A very short filler activity for a few minutes — NOT a full learning
# experience, no EYLF write-up, 1-2 materials max, not tied to a specific
# child, and never feeds into Parent Communication below.
# ==========================================

with st.container(border=True):
    st.markdown(section_header("⚡", "Quick Activity Suggester", "quick-activity", "peach"), unsafe_allow_html=True)
    st.caption("A fast, dead-simple activity to re-engage the group for a few minutes — "
               "not a structured learning experience. Repeats are fine; these aren't tracked or saved per child.")

    col1, col2 = st.columns(2)
    with col1:
        quick_age_group = st.selectbox("🎂 Age group", AGE_BANDS, key="quick_age_group")
    with col2:
        quick_mood = st.selectbox(
            "😊 Mood right now",
            ["Energetic and active", "Calm and focused", "Restless and unsettled", "Tired and low energy"],
            key="quick_mood",
        )

    def _extract_activity_name(result_text):

        if not result_text or not result_text.strip():
            return "Quick Activity"

        lines = result_text.splitlines()

        if not lines:
            return "Quick Activity"

        first_line = lines[0].strip()

        if first_line.upper().startswith("ACTIVITY:"):
            return first_line.split(":", 1)[1].strip()

        return first_line

    def _generate_quick_activity():
        # Avoid anything used for this age group in the last ~90 days, not just the last one.
        avoid_names = get_recent_quick_activity_names(quick_age_group, days=90)

        system_prompt = (
            "You suggest VERY QUICK, dead-simple filler activities to re-engage a group of children "
            "for a few minutes when an educator is busy, tired, or between planned activities. This is "
            "NOT a structured learning experience — no EYLF write-up, no elaborate setup. Use at most "
            "1-2 common materials, or none at all (e.g. a running game, clapping game, simple "
            "call-and-response, throwing/catching). Base it only on what's realistic for this age using "
            "the milestones given — do not invent skills beyond them."
        )
        prompt = f"""Age group: {quick_age_group}
Developmental milestones for this age (base the activity on these):
{milestones_summary_text(quick_age_group)}

Mood right now: {quick_mood}
{"Activities already used recently for this age group — do NOT repeat any of these: " + "; ".join(avoid_names) if avoid_names else ""}

Give ONE very quick activity, genuinely different from the ones listed above. Reply in EXACTLY this format, nothing else:
ACTIVITY: <name>
HOW: <one plain sentence>
MATERIALS: <1-2 items max, or 'None needed'>"""
        resp = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
            max_tokens=400,
            reasoning_effort="low",
        )
        result_text = resp.choices[0].message.content.strip()
        save_quick_activity(quick_age_group, _extract_activity_name(result_text))
        return result_text

    if st.button("⚡ Suggest Quick Activity", type="primary"):
        with st.spinner("Thinking of something quick..."):
            st.session_state["quick_activity_result"] = _generate_quick_activity()

    if "quick_activity_result" in st.session_state:
        st.info(st.session_state["quick_activity_result"])
        st.caption("Not feeling it? This one's now logged as recently used, so trying again will skip it and anything else from the last ~3 months.")
        if st.button("🔄 Try another one"):
            with st.spinner("Trying another..."):
                st.session_state["quick_activity_result"] = _generate_quick_activity()
            st.rerun()

section_divider("lavender")

# ==========================================
# WEEKLY MAGIC TRICK
# A single "wow" science moment for the week, using minimal safe household
# materials — meant to surprise/delight the group, not a full lesson plan.
# ==========================================

with st.container(border=True):
    st.markdown(section_header("✨", "Weekly Magic Trick", "magic-trick", "lavender"), unsafe_allow_html=True)
    st.caption("One simple, safe 'wow' science moment for the week — minimal household materials, "
               "always educator-led and supervised. Won't repeat for about 2 months. "
               "Safety rules automatically tighten for younger age groups.")

    magic_age_group = st.selectbox("🎂 Age group", AGE_BANDS, key="magic_age_group")

    def _magic_trick_safety_notes(age_group: str) -> str:
        """Younger children mouth objects and have no impulse control around choking
        or chemical hazards, so the youngest bands get much stricter constraints than
        a 4-5 year old room would need.

        IMPORTANT: any band expressed in MONTHS (e.g. "6-12 months") is always an
        infant under 1 year old, no matter what number it starts with — do NOT
        classify by leading digit for these, or "6-12 months" would misread as "6"
        and fall into an older, less-strict tier. Only YEAR-based bands (1-2 years
        and up) are classified by their leading number."""
        if "month" in age_group.lower():
            lead_age = 0  # any month-based band is an infant, full stop
        else:
            match = re.match(r"(\d+)", age_group)
            lead_age = int(match.group(1)) if match else 5

        if lead_age <= 1:
            return (
                "This is an INFANT/YOUNG TODDLER room (0-6 months, 6-12 months, or 1-2 years). EXTRA "
                "SAFETY — non-negotiable: "
                "absolutely NO small parts or choking hazards (no balloons, no beads, buttons, or anything "
                "smaller than a fist), NO chemicals or substances of any kind (no baking soda/vinegar, no "
                "food colouring in an open container) that a child could reach, touch, or put in their "
                "mouth. Children at this age must ONLY WATCH from a safe distance — never hold, touch, or "
                "help with any material. Prefer a purely visual/sensory effect instead: light and shadow "
                "play, a sealed sensory bottle the educator shakes, water poured (by the educator only) "
                "between two clear sealed containers, simple peekaboo-style surprise using only the "
                "educator's hands or a scarf. If you cannot make it this safe, choose a different idea."
            )
        elif lead_age <= 3:
            return (
                "This is a YOUNG PRESCHOOL room (2-3 or 3-4 years). Extra care needed: no small parts or "
                "choking hazards (no loose balloons, no small beads), no substance a child could taste or "
                "get in their eyes if they got close. Chemical reactions (e.g. baking soda + vinegar) are "
                "OK only in a stable, closed or hard-to-tip container, entirely handled by the educator, "
                "with children watching from a safe distance — never handling the materials themselves."
            )
        else:
            return (
                "This is an older preschool room (4-5+ years). Standard supervision applies: educator "
                "handles any chemicals/hot/sharp items, children may help with clearly safe steps (e.g. "
                "adding a pre-measured ingredient under direct supervision), and normal choking-hazard "
                "common sense still applies (no unsupervised small parts)."
            )

    if st.button("✨ Generate This Week's Magic Trick", type="primary"):
        with st.spinner("Conjuring something magical..."):
            avoid_tricks = get_recent_magic_tricks(magic_age_group, days=60)
            avoid_text = (
                "Already used in the last ~2 months — do NOT repeat any of these: " + "; ".join(avoid_tricks)
            ) if avoid_tricks else ""

            magic_prompt = f"""Suggest ONE simple, completely safe "magic trick" science moment for early
childhood educators to show a group of young children, designed to genuinely surprise and delight them
(e.g. a colour that changes, something that fizzes, a balloon that sticks with static, something that
floats then sinks, a "fountain" effect). Requirements:
- Only common, safe household/kitchen materials (e.g. baking soda, vinegar, dish soap, food colouring,
  water, balloons, tissue paper) — nothing a parent or centre wouldn't already have or easily buy at a
  supermarket, and nothing hazardous.
- Must be run BY THE EDUCATOR, with children watching/reacting — not something children do unsupervised.
- Include a one-line safety note if relevant (e.g. adult handles it, keep out of eyes).

Age group this is for: {magic_age_group}
{_magic_trick_safety_notes(magic_age_group)}

{avoid_text}

Reply in EXACTLY this format, nothing else:
NAME: <short catchy name>
MATERIALS: <short list>
STEPS: <2-4 short numbered steps>
WOW: <one sentence on what the children will see/react to>
SKILL: <one short plain-language phrase on what curiosity/skill this builds>
SAFETY: <one short line, or 'None needed'>"""

            resp = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[
                    {"role": "system", "content": "You suggest safe, simple, delightful science demonstrations for early childhood educators to perform for young children, using only common household materials. You strictly enforce stricter safety rules for younger age groups, especially around choking hazards and anything a child could taste or touch unsupervised."},
                    {"role": "user", "content": magic_prompt},
                ],
                max_tokens=700,
                reasoning_effort="low",
            )
            result_text = resp.choices[0].message.content.strip()
            st.session_state["magic_trick_result"] = result_text

            trick_name = "Magic Trick"
            for line in result_text.splitlines():
                if line.upper().startswith("NAME:"):
                    trick_name = line.split(":", 1)[1].strip()
                    break
            save_magic_trick(trick_name, magic_age_group)

    if "magic_trick_result" in st.session_state:
        st.info(st.session_state["magic_trick_result"])

section_divider("blue")

# ==========================================
# WEEKLY PROGRAM PLANNER
# 15 experiences: 5 tied to the theme, 10 general covering distinct
# curriculum streams (one stream each), grounded in the milestones for
# the selected age band.
# ==========================================

STREAMS = [
    "Literacy", "Numeracy", "Fine Motor", "Gross Motor / Physical",
    "Social-Emotional", "Sensory Play", "Creative Art",
    "Science & Discovery", "Dramatic / Imaginative Play", "Music & Movement",
]

with st.container(border=True):
    st.markdown(section_header("📅", "Weekly Program Planner", "weekly-planner", "blue"), unsafe_allow_html=True)
    st.caption("Generates 15 experiences: 5 tied to your theme, and 10 general experiences "
               "covering every curriculum stream, so the week has full coverage either way.")

    week_theme = st.text_input("🌈 Theme for this week")
    age_for_plan = st.selectbox("🎂 Age group for weekly plan", AGE_BANDS, key="weekly_age_group")

    def _sensory_stream_guidance(age_group: str) -> str:
        """Babies mouth everything and can't be trusted with loose/open sensory
        materials, so their 'Sensory Play' experience should default to a
        SEALED exploration format (e.g. a taped zip-lock sensory bag) rather
        than open trays of material meant for older, non-mouthing children."""
        if age_group in ("0-6 months", "6-12 months"):
            return (
                "\nSPECIAL RULE for the Sensory Play stream, since this room is 0-1 years (babies mouth "
                "everything and must never access loose material): make it a SEALED sensory bag/pouch — "
                "e.g. water plus a little oil (they don't mix, so it's visually interesting) and a few "
                "drops of food colouring or some glitter/pom-poms, sealed and taped shut inside a sturdy "
                "zip-lock bag (reinforce the seal with tape, and taped to a table or the floor so it can't "
                "be picked up whole). Baby explores entirely through the sealed bag — squishing, pressing, "
                "watching the bubbles/colours move — with zero risk of spilling, choking, or ingestion. "
                "Never suggest loose/open sensory materials (rice, beads, paint, etc.) for this age."
            )
        return ""

    if st.button("Generate Weekly Plan", type="primary"):
        with st.spinner("Generating weekly plan (15 experiences)..."):
            # Avoid anything used for this age group in the last ~90 days (roughly 2-3 months).
            recent_names = get_recent_experience_names(age_for_plan, days=90)
            avoid_text = ("Experiences already used in the last ~3 months for this age group — do NOT "
                          "repeat any of these, use genuinely different ones: " + "; ".join(recent_names)) if recent_names else ""

            plan_prompt = f"""Create exactly 15 short early-childhood learning experiences for {age_for_plan}.
Theme for the week: {week_theme if week_theme else 'no specific theme — keep all 15 general'}

Developmental milestones for this age (base every experience on these, don't invent unrelated skills):
{milestones_summary_text(age_for_plan)}
{_sensory_stream_guidance(age_for_plan)}

{avoid_text}

Requirements:
- Exactly 5 of the 15 experiences must connect directly to the theme.
- The remaining 10 must be general (not theme-specific) and must cover these 10 curriculum streams,
  one experience per stream, in this order: {", ".join(STREAMS)}.
- For each of the 15, give: a short name, which stream or theme-link it covers, materials (keep minimal),
  and 1-2 sentences on how to run it. Keep every entry short — this is a planning list, not a full lesson plan.
- Number 1-5 as "Theme" experiences and 6-15 as the 10 stream experiences, clearly labelled.

FIRST, before anything else, output one line listing just the 15 experience names, separated by " | ",
in this exact format (nothing else on that line):
EXPERIENCE_NAMES: name1 | name2 | name3 | ... | name15

Then on the next line put "---" alone, then the full formatted plan below that."""

            plan_message = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[
                    {"role": "system", "content": "You are an expert early childhood educator specialising in curriculum planning aligned to EYLF Version 2.0 Australia, grounded strictly in the developmental milestones provided."},
                    {"role": "user", "content": plan_prompt},
                ],
                max_tokens=3000,
            )

            full_text = plan_message.choices[0].message.content
            experience_names = []
            display_text = full_text

            if "EXPERIENCE_NAMES:" in full_text:
                header_line = full_text.split("EXPERIENCE_NAMES:", 1)[1].splitlines()[0]
                experience_names = [n.strip() for n in header_line.split("|") if n.strip()]
                if "---" in full_text:
                    display_text = full_text.split("---", 1)[1].strip()

            week_key = get_week_key()
            save_weekly_experiences(age_for_plan, week_key, week_theme, experience_names)

            st.success("Weekly plan generated!")
            st.markdown(display_text)

section_divider("green")

# ==========================================
# WEEKLY WORKSHEET GENERATOR
# ==========================================

st.markdown(section_anchor("worksheets"), unsafe_allow_html=True)
with st.container(border=True):
    worksheet_tab(client)

section_divider("green")

# ==========================================
# HOME EXTENSION MESSAGE (generic — for the whole group, not personalised)
# Photos/day-to-day updates go out separately via WhatsApp; this is only
# for a short, copy-paste, no-names message with take-home ideas.
# ==========================================

with st.container(border=True):
    st.markdown(section_header("🏠", "Home Extension Message", "home-message", "green"), unsafe_allow_html=True)
    st.caption("A short, generic, copy-paste message for all families — no child names, "
                "nothing personalised. Day-to-day photos/updates still go out separately via WhatsApp. "
                "'Try at home' ideas only use things families already have — kitchen, laundry, or general "
                "household items, never something to go and buy — and each idea names the skill it builds. "
                "Ideas won't repeat for about 2-3 months.")

    activity_or_theme = st.text_area(
        "✏️ What did the group do today (activity or theme)?",
        key="home_ext_input",
        placeholder="e.g. Water play and pouring/measuring with cups and jugs",
    )
    home_ext_languages = st.multiselect(
        "🌍 Translate to (optional)",
        ["Hindi", "Spanish", "Arabic", "Mandarin", "Vietnamese", "French"],
        key="home_ext_languages",
    )

    if st.button("Generate Home Message", type="primary"):
        with st.spinner("Generating..."):
            avoid_ideas = get_recent_home_ideas(days=75)
            avoid_text = (
                "Ideas already sent to families in the last ~2-3 months — do NOT repeat any of these, "
                "come up with genuinely different ones: " + "; ".join(avoid_ideas)
            ) if avoid_ideas else ""

            home_prompt = f"""Today's group activity/theme: {activity_or_theme}

Write a SHORT, GENERIC message for early childhood educators to copy-paste and send to ALL families in
the room — do not use any child's name or personalise it to one child. Format:

MESSAGE:
1-2 sentence intro about today's activity/theme, written generically for the whole group.

TRY AT HOME (3 ideas):
Three short, simple ideas any parent could do THAT SAME EVENING using ONLY things already in a typical
home — kitchen items (bowls, spoons, cups, pasta, rice), laundry items (socks, pegs, baskets), bathroom
items, or general household objects (cushions, blankets, boxes already lying around). Do NOT suggest
anything a parent would need to buy or source specially (no craft-store items, no printables). For each
idea, on the line right after it, add "Skill: <one short plain-language phrase>" naming the skill it
builds, so it reads like:
1. <idea>
   Skill: <skill>
2. <idea>
   Skill: <skill>
3. <idea>
   Skill: <skill>

{avoid_text}

{"Also translate the MESSAGE section into: " + ", ".join(home_ext_languages) if home_ext_languages else ""}
"""
            home_message = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[
                    {"role": "system", "content": "You write short, warm, generic educator-to-parent messages for early childhood centres. Never personalise to a specific child. 'Try at home' ideas must use only ordinary things already found around a home — never anything to purchase."},
                    {"role": "user", "content": home_prompt},
                ],
            )
            result_text = home_message.choices[0].message.content
            st.success("Ready to copy and send!")
            st.markdown(result_text)

            # Pull out just the idea lines (not the "Skill:" lines) to save for repeat-avoidance.
            idea_lines = [
                re.sub(r"^\s*\d+[\.\)]\s*", "", line).strip()
                for line in result_text.splitlines()
                if re.match(r"^\s*\d+[\.\)]", line)
            ]
            if idea_lines:
                save_home_ideas(idea_lines)

section_divider("peach")

# ==========================================
# STORY TIME GENERATOR
# ==========================================

st.markdown(section_anchor("story-time"), unsafe_allow_html=True)
with st.container(border=True):
    story_generator_tab(client)