from groq import Groq
import streamlit as st
from observation import observation_tab
from learning_story import learning_story_tab
from story_generator import story_generator_tab
from worksheet_generator import worksheet_tab, get_week_key
from ui_theme import apply_theme, section_header, section_anchor
from milestones_data import AGE_BANDS, milestones_summary_text, AGE_BAND_SOURCE
from independence_skills import init_independence_table, independence_skills_tab
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
init_independence_table()

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
from login_gate import show_login_gate

apply_theme()
if not show_login_gate():
    st.stop()          # nothing below this runs until the user signs in
# Note: ui_theme's render_sidebar_nav() is intentionally NOT called here —
# it renders same-page "#anchor" scroll links, which only made sense when
# every section lived on one long scrolling page. Now that each feature is
# its own page (see render_sidebar_menu() near the router below), those
# anchor links would mostly point at content that isn't on-screen. The new
# sidebar menu replaces it with real navigation.

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

STREAMS = [
    "Literacy", "Numeracy", "Fine Motor", "Gross Motor / Physical",
    "Social-Emotional", "Sensory Play", "Creative Art",
    "Science & Discovery", "Dramatic / Imaginative Play", "Music & Movement",
]


def _back_button():
    if st.button("← Back to Dashboard", key="ek_back_btn"):
        st.session_state["ek_page"] = "dashboard"
        st.rerun()
    st.write("")


# ==========================================
# PAGE: SELECT CHILD
# ==========================================

def page_select_child():
    _back_button()
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
            st.info("Select or add a child above to build their saved history.")
            st.session_state["ek_child_id"] = None
            st.session_state["ek_child_name"] = None
        else:
            st.session_state["ek_child_id"] = child_id
            st.session_state["ek_child_name"] = selected_name
            st.caption(f"Working with: **{selected_name}** ({child_record['age_group']}) — interests: {child_record['interests'] or 'not set'}")


# ==========================================
# PAGE: SITUATION-BASED SUPPORT
# ==========================================

def page_situation_support():
    _back_button()
    st.markdown(section_anchor("situation-support"), unsafe_allow_html=True)
    with st.container(border=True):
        observation_tab(client)


# ==========================================
# PAGE: LEARNING STORY GENERATOR
# ==========================================

def page_learning_story():
    _back_button()
    st.markdown(section_anchor("learning-story"), unsafe_allow_html=True)
    with st.container(border=True):
        learning_story_tab(client)


# ==========================================
# PAGE: CHILD HISTORY
# ==========================================

def page_child_history():
    _back_button()
    child_id = st.session_state.get("ek_child_id")
    selected_name = st.session_state.get("ek_child_name")

    if child_id is None:
        st.info("No child selected yet. Open **Select Child** first, then come back here.")
        return

    with st.container(border=True):
        st.markdown(section_header("📖", f"{selected_name}'s History", "child-history", "lavender"), unsafe_allow_html=True)

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


# ==========================================
# PAGE: QUICK ACTIVITY SUGGESTER
# A very short filler activity for a few minutes — NOT a full learning
# experience, no EYLF write-up, 1-2 materials max, not tied to a specific
# child, and never feeds into Parent Communication below.
# ==========================================

def page_quick_activity():
    _back_button()
    with st.container(border=True):
        st.markdown(section_header("⚡", "Quick Activity Suggester", "quick-activity", "peach"), unsafe_allow_html=True)
        st.caption("A fast, dead-simple activity to re-engage the group for a few minutes — "
                   "not a structured learning experience. Repeats are fine; these aren't tracked or saved per child.")

        quick_is_mixed = st.checkbox(
            "🔀 Mixed-age combined room (e.g. before 8am / after 5:30pm care, all ages together)",
            key="quick_is_mixed",
        )

        col1, col2 = st.columns(2)
        with col1:
            if quick_is_mixed:
                quick_age_bands_selected = st.multiselect(
                    "🎂 Age groups present in the room right now",
                    AGE_BANDS,
                    key="quick_age_bands_selected",
                )
            else:
                quick_age_group = st.selectbox("🎂 Age group", AGE_BANDS, key="quick_age_group")
        with col2:
            quick_mood = st.selectbox(
                "😊 Mood right now",
                ["Energetic and active", "Calm and focused", "Restless and unsettled", "Tired and low energy"],
                key="quick_mood",
            )

        quick_materials = st.text_input(
            "🧰 Materials you actually have on hand right now (optional — leave blank for no/minimal materials)",
            placeholder="e.g. blocks, sensory bin, books, outdoor space",
            key="quick_materials",
        )

        def _mixed_age_key(age_bands: list[str]) -> str:
            # Sorted so the same set of bands always produces the same lookup
            # key for recency tracking, regardless of multiselect click order.
            return "MIXED:" + "+".join(sorted(age_bands))

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
            materials_line = (
                f"Materials available — use ONLY these (or nothing): {quick_materials.strip()}"
                if quick_materials.strip()
                else "No specific materials on hand — keep it to 0-1 common items, or none at all."
            )

            if quick_is_mixed:
                if not quick_age_bands_selected or len(quick_age_bands_selected) < 2:
                    return "Select at least two age groups present in the room for a mixed-age suggestion."

                age_group_key = _mixed_age_key(quick_age_bands_selected)
                avoid_names = get_recent_quick_activity_names(age_group_key, days=90)

                # Some dropdown bands (e.g. "3-4 years" and "4-5 years") share the
                # same underlying source milestones — group selected bands by
                # source so shared content is only sent to the AI once, labelled
                # with all the dropdown bands it covers.
                bands_by_source: dict[str, list[str]] = {}
                for band in quick_age_bands_selected:
                    source = AGE_BAND_SOURCE.get(band, band)
                    bands_by_source.setdefault(source, []).append(band)

                milestones_block = "\n\n".join(
                    f"{' / '.join(bands)}:\n{milestones_summary_text(bands[0])}"
                    for bands in bands_by_source.values()
                )

                system_prompt = (
                    "You suggest VERY QUICK, dead-simple filler activities for a MIXED-AGE group of "
                    "children (e.g. a before/after-care room combining several age bands) to re-engage them "
                    "for a few minutes when an educator is busy, tired, or between planned activities. This is "
                    "NOT a structured learning experience — no EYLF write-up, no elaborate setup. The SAME core "
                    "activity must work for every age band listed, with only the level of challenge or the way "
                    "each age group takes part changing. Do not invent skills beyond the milestones given. "
                    "Flag a supervision/safety note whenever infants or young toddlers are being combined with "
                    "older, more physically active children."
                )
                prompt = f"""Age groups present: {", ".join(quick_age_bands_selected)}
Developmental milestones for each age group (base the activity on these):
{milestones_block}

Mood right now: {quick_mood}
{materials_line}
{"Activities already used recently for this exact combination of ages — do NOT repeat any of these: " + "; ".join(avoid_names) if avoid_names else ""}

Give ONE very quick activity that the whole mixed-age group can do together at the same time, genuinely different from the ones listed above. Reply in EXACTLY this format, nothing else:
ACTIVITY: <name>
HOW: <one plain sentence describing the shared core activity>
FOR EACH AGE: <one short line per age group, format "AGE_BAND — how they take part/what's adapted">
MATERIALS: <based on what's available, or 'None needed'>
SAFETY: <one line supervision/safety note if mixing very young and older children, otherwise 'None needed'>"""
            else:
                age_group_key = quick_age_group
                avoid_names = get_recent_quick_activity_names(age_group_key, days=90)

                system_prompt = (
                    "You suggest VERY QUICK, dead-simple filler activities to re-engage a group of children "
                    "for a few minutes when an educator is busy, tired, or between planned activities. This is "
                    "NOT a structured learning experience — no EYLF write-up, no elaborate setup. Base it only "
                    "on what's realistic for this age using the milestones given — do not invent skills beyond "
                    "them."
                )
                prompt = f"""Age group: {quick_age_group}
Developmental milestones for this age (base the activity on these):
{milestones_summary_text(quick_age_group)}

Mood right now: {quick_mood}
{materials_line}
{"Activities already used recently for this age group — do NOT repeat any of these: " + "; ".join(avoid_names) if avoid_names else ""}

Give ONE very quick activity, genuinely different from the ones listed above. Reply in EXACTLY this format, nothing else:
ACTIVITY: <name>
HOW: <one plain sentence>
MATERIALS: <based on what's available, or 'None needed'>"""

            resp = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
                max_tokens=400,
                reasoning_effort="low",
            )
            result_text = resp.choices[0].message.content.strip()
            save_quick_activity(age_group_key, _extract_activity_name(result_text))
            return result_text

        if st.button("⚡ Suggest Quick Activity", type="primary"):
            if quick_is_mixed and len(st.session_state.get("quick_age_bands_selected", [])) < 2:
                st.warning("Select at least two age groups present in the room before generating a mixed-age activity.")
            else:
                with st.spinner("Thinking of something quick..."):
                    st.session_state["quick_activity_result"] = _generate_quick_activity()

        if "quick_activity_result" in st.session_state:
            st.info(st.session_state["quick_activity_result"])
            st.caption("Not feeling it? This one's now logged as recently used, so trying again will skip it and anything else from the last ~3 months.")
            if st.button("🔄 Try another one"):
                if quick_is_mixed and len(st.session_state.get("quick_age_bands_selected", [])) < 2:
                    st.warning("Select at least two age groups present in the room before generating a mixed-age activity.")
                else:
                    with st.spinner("Trying another..."):
                        st.session_state["quick_activity_result"] = _generate_quick_activity()
                    st.rerun()


# ==========================================
# PAGE: WEEKLY MAGIC TRICK
# A single "wow" science moment for the week, using minimal safe household
# materials — meant to surprise/delight the group, not a full lesson plan.
# ==========================================

def page_magic_trick():
    _back_button()
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


# ==========================================
# PAGE: WEEKLY PROGRAM PLANNER
# 15 experiences: 5 tied to the theme, 10 general covering distinct
# curriculum streams (one stream each), grounded in the milestones for
# the selected age band.
# ==========================================

def page_weekly_planner():
    _back_button()
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
  1-2 sentences on how to run it, the TOP 2 EYLF (Version 2.0) learning outcomes linked to that experience
  (short form, e.g. "Outcome 1: Identity", "Outcome 4: Learning"), and a one-line "Use:" statement on the
  purpose/benefit of that activity for the child's development. Keep every entry short — this is a planning
  list, not a full lesson plan.
- Number 1-5 as "Theme" experiences and 6-15 as the 10 stream experiences, clearly labelled.
- Format each entry's extra fields on their own short lines, e.g.:
  EYLF Outcomes: <outcome 1> | <outcome 2>
  Use: <one sentence>

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


# ==========================================
# PAGE: WEEKLY WORKSHEET GENERATOR
# ==========================================

def page_worksheets():
    _back_button()
    st.markdown(section_anchor("worksheets"), unsafe_allow_html=True)
    with st.container(border=True):
        worksheet_tab(client)


# ==========================================
# PAGE: INDEPENDENCE SKILLS BUILDER
# ==========================================

def page_independence():
    _back_button()
    with st.container(border=True):
        independence_skills_tab(client)


# ==========================================
# PAGE: HOME EXTENSION MESSAGE (generic — for the whole group, not personalised)
# Photos/day-to-day updates go out separately via WhatsApp; this is only
# for a short, copy-paste, no-names message with take-home ideas.
# ==========================================

def page_home_message():
    _back_button()
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


# ==========================================
# PAGE: STORY TIME GENERATOR
# ==========================================

def page_story_time():
    _back_button()
    st.markdown(section_anchor("story-time"), unsafe_allow_html=True)
    with st.container(border=True):
        story_generator_tab(client)


# ==========================================
# DASHBOARD (home screen — one tile per feature)
# ==========================================

PAGES = [
    {"key": "select_child", "icon": "👤", "title": "Select Child",
     "desc": "Choose or add a child to build saved history for.", "func": page_select_child,
     "bg": "#F7E9E2", "accent": "#C97C55"},
    {"key": "situation_support", "icon": "🧩", "title": "Situation-Based Support",
     "desc": "Get strategies for a specific classroom situation.", "func": page_situation_support,
     "bg": "#E6EEF4", "accent": "#5B84A8"},
    {"key": "learning_story", "icon": "📚", "title": "Learning Story Generator",
     "desc": "Turn an observation into a written learning story.", "func": page_learning_story,
     "bg": "#EAE4F1", "accent": "#7C6C9C"},
    {"key": "child_history", "icon": "📖", "title": "Child History",
     "desc": "View saved entries for the selected child.", "func": page_child_history,
     "bg": "#F5EEDA", "accent": "#B9902E"},
    {"key": "quick_activity", "icon": "⚡", "title": "Quick Activity Suggester",
     "desc": "A fast filler activity for a few spare minutes.", "func": page_quick_activity,
     "bg": "#F3E4EC", "accent": "#B0678A"},
    {"key": "magic_trick", "icon": "✨", "title": "Weekly Magic Trick",
     "desc": "One safe, delightful science 'wow' moment for the week.", "func": page_magic_trick,
     "bg": "#E3EFE9", "accent": "#4F8D74"},
    {"key": "weekly_planner", "icon": "📅", "title": "Weekly Program Planner",
     "desc": "Generate a full 15-experience weekly program.", "func": page_weekly_planner,
     "bg": "#E3EEF2", "accent": "#4A8AA0"},
    {"key": "worksheets", "icon": "📝", "title": "Weekly Worksheet Generator",
     "desc": "Printable worksheets for the group.", "func": page_worksheets,
     "bg": "#F6EBDD", "accent": "#BD7F3F"},
    {"key": "independence", "icon": "🧠", "title": "Independence Skills Builder",
     "desc": "Break a self-help skill into practiceable steps.", "func": page_independence,
     "bg": "#E9E3F0", "accent": "#7263A0"},
    {"key": "home_message", "icon": "🏠", "title": "Home Extension Message",
     "desc": "Copy-paste message with take-home ideas for families.", "func": page_home_message,
     "bg": "#E4EEE1", "accent": "#5E8F5E"},
    {"key": "story_time", "icon": "📕", "title": "Story Time Generator",
     "desc": "Generate a short story for group story time.", "func": page_story_time,
     "bg": "#F4E4E3", "accent": "#B06A63"},
]


PAGE_MAP = {p["key"]: p["func"] for p in PAGES}


def _inject_dashboard_css():
    """Gives each dashboard tile (and its Open button) its own soft pastel
    background + matching solid accent button, plus a subtle hover lift.
    Relies on Streamlit's st.container(key=...) emitting a '.st-key-<key>'
    class on the wrapping div (Streamlit 1.36+). If tiles still look plain
    after this, the installed Streamlit version may be older — `pip install
    -U streamlit` and rerun."""
    rules = []
    for page in PAGES:
        css_key = f"tile_{page['key']}"
        bg = page["bg"]
        accent = page["accent"]
        rules.append(f"""
        .st-key-{css_key} {{
            background: {bg} !important;
            border-radius: 18px !important;
            border: none !important;
            box-shadow: 0 2px 10px rgba(32,36,44,0.07) !important;
            transition: transform 0.15s ease, box-shadow 0.15s ease;
            padding: 4px 4px 10px 4px !important;
        }}
        .st-key-{css_key}:hover {{
            transform: translateY(-4px);
            box-shadow: 0 10px 22px rgba(32,36,44,0.13) !important;
        }}
        .st-key-{css_key} button {{
            background: {accent} !important;
            color: white !important;
            border: none !important;
            border-radius: 10px !important;
            font-weight: 700 !important;
            transition: transform 0.1s ease, filter 0.15s ease;
        }}
        .st-key-{css_key} button:hover {{
            filter: brightness(1.08);
            transform: translateY(-1px);
        }}
        """)
    # Sidebar nav buttons — soft, rounded, left-aligned like a proper app menu
    rules.append("""
        div[class*="st-key-tile_"] h4 {
            font-family: 'Fraunces', serif !important;
            color: #20242C !important;
            margin: 0.15em 0 0.25em 0 !important;
        }
        section[data-testid="stSidebar"] .stButton button {
            width: 100%;
            text-align: left !important;
            justify-content: flex-start !important;
            background: transparent !important;
            border: none !important;
            border-radius: 10px !important;
            font-weight: 600 !important;
            color: #20242C !important;
            padding: 0.5em 0.8em !important;
        }
        section[data-testid="stSidebar"] .stButton button:hover {
            background: #FFF1E0 !important;
        }
        /* Dashboard Previous/Next — neutral charcoal so they read as
           navigation controls, not another colored tool tile. */
        div[class*="st-key-dash_prev_btn"] button,
        div[class*="st-key-dash_next_btn"] button {
            background: #3F4550 !important;
            color: white !important;
            border: none !important;
            font-weight: 700 !important;
        }
        div[class*="st-key-dash_prev_btn"] button:hover,
        div[class*="st-key-dash_next_btn"] button:hover {
            background: #2C313A !important;
        }
    """)
    st.markdown(f"<style>{''.join(rules)}</style>", unsafe_allow_html=True)


DASHBOARD_PAGE_SIZE = 6  # 2 rows of 3 tiles per dashboard page


def render_dashboard():
    st.markdown("## 🎨 Choose a tool")

    total_pages = (len(PAGES) + DASHBOARD_PAGE_SIZE - 1) // DASHBOARD_PAGE_SIZE
    st.session_state.setdefault("ek_dashboard_page_num", 0)
    # Clamp in case PAGES ever shrinks below the saved page number.
    page_num = max(0, min(st.session_state["ek_dashboard_page_num"], total_pages - 1))
    st.session_state["ek_dashboard_page_num"] = page_num

    start = page_num * DASHBOARD_PAGE_SIZE
    visible_pages = PAGES[start:start + DASHBOARD_PAGE_SIZE]

    cols_per_row = 3
    for i in range(0, len(visible_pages), cols_per_row):
        row = visible_pages[i:i + cols_per_row]
        cols = st.columns(cols_per_row)
        for col, page in zip(cols, row):
            with col:
                with st.container(border=True, key=f"tile_{page['key']}"):
                    st.markdown(
                        f"<div style='font-size:2.3em; line-height:1.1; margin-bottom:0.1em;'>{page['icon']}</div>",
                        unsafe_allow_html=True,
                    )
                    st.markdown(f"#### {page['title']}")
                    st.caption(page["desc"])
                    if st.button("Open →", key=f"open_{page['key']}", use_container_width=True):
                        st.session_state["ek_page"] = page["key"]
                        st.rerun()

    # Prev / page indicator / Next
    st.write("")
    nav_prev, nav_mid, nav_next = st.columns([1, 2, 1])
    with nav_prev:
        if page_num > 0:
            if st.button("← Previous", key="dash_prev_btn", use_container_width=True):
                st.session_state["ek_dashboard_page_num"] = page_num - 1
                st.rerun()
    with nav_mid:
        st.markdown(
            f"<div style='text-align:center;color:#8A8377;padding-top:0.6em;font-weight:600;'>"
            f"Page {page_num + 1} of {total_pages}</div>",
            unsafe_allow_html=True,
        )
    with nav_next:
        if page_num < total_pages - 1:
            if st.button("Next →", key="dash_next_btn", use_container_width=True):
                st.session_state["ek_dashboard_page_num"] = page_num + 1
                st.rerun()


def render_sidebar_menu():
    """A persistent left-hand menu (separate from ui_theme's render_sidebar_nav)
    so every feature — and the dashboard itself — is one click away, no
    scrolling needed."""
    with st.sidebar:
        st.markdown("### 🌟 EngageKids AI")
        st.caption("Jump to any tool")
        if st.button("🏠 Dashboard", key="nav_dashboard", use_container_width=True):
            st.session_state["ek_page"] = "dashboard"
            st.rerun()
        st.markdown("---")
        for page in PAGES:
            if st.button(f"{page['icon']} {page['title']}", key=f"nav_{page['key']}", use_container_width=True):
                st.session_state["ek_page"] = page["key"]
                st.rerun()


# ==========================================
# ROUTER
# ==========================================

_inject_dashboard_css()
render_sidebar_menu()

st.session_state.setdefault("ek_page", "dashboard")
current_page = st.session_state["ek_page"]

if current_page == "dashboard":
    render_dashboard()
else:
    PAGE_MAP.get(current_page, render_dashboard)()