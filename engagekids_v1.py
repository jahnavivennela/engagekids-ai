from groq import Groq
import streamlit as st
from observation import observation_tab
from learning_story import learning_story_tab
from story_generator import story_generator_tab
from worksheet_generator import worksheet_tab
from db import init_db, add_child, get_children, get_child, add_observation, get_observations

# Setup
api_key = st.secrets["GROQ_API_KEY"]
client = Groq(api_key=api_key)

# Initialize the database (safe to call every run — CREATE TABLE IF NOT EXISTS)
init_db()

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

# Header
st.markdown(
    """
    <div style="text-align: center; padding: 10px 0;">
        <h1 style="color: #FF6B6B; margin-bottom: 0;">🌟 EngageKids AI</h1>
        <p style="color: #666666; font-size: 16px; margin-top: 5px;">
            Real-time, classroom-tested support for early childhood educators
        </p>
    </div>
    """,
    unsafe_allow_html=True
)
st.markdown("---")

# ==========================================
# CHILD SELECTOR (everything below can now save to a specific child)
# ==========================================

st.subheader("👤 Select Child")

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
        new_name = st.text_input("Child's name")
        new_age = st.selectbox("Age group", ["Babies 0-1 years", "Toddlers 1-3 years", "Preschool 3-5 years"])
        new_interests = st.text_input("Interests (comma separated, e.g. dinosaurs, drawing, running)")
        submitted = st.form_submit_button("Save child")
        if submitted and new_name:
            child_id = add_child(new_name, new_age, new_interests)
            st.success(f"Added {new_name}")
            st.rerun()

elif selected_name != "— None selected —":
    child_id = child_names[selected_name]
    child_record = get_child(child_id)

if child_id is None:
    st.info("Select or add a child above to generate a personalised parent message and build their saved history.")
else:
    st.caption(f"Working with: **{selected_name}** ({child_record['age_group']}) — interests: {child_record['interests'] or 'not set'}")

st.markdown("---")

# ==========================================
# ACTIVITY SUGGESTER
# ==========================================

col1, col2 = st.columns(2)

with col1:
    age_group = st.selectbox(
        "Age group",
        ["Babies 0-1 years", "Toddlers 1-3 years", "Preschool 3-5 years"]
    )
    mood = st.selectbox(
        "Current mood of children",
        ["Energetic and active", "Calm and focused", "Restless and unsettled", "Tired and low energy"]
    )

with col2:
    theme = st.text_input("Current theme (e.g. dental week, nature, transport)")
    time_available = st.selectbox(
        "Time available",
        ["15 minutes", "30 minutes", "45 minutes", "1 hour"]
    )

resources = st.multiselect(
    "Available resources",
    ["Art supplies", "Outdoor space", "Water play", "Books", "Music", "Construction toys", "Sensory materials", "Kitchen items"]
)

if st.button("🌟 Suggest Activity", type="primary"):

    with st.spinner("Generating activity..."):

        system_prompt = """You are an expert early childhood educator with deep knowledge of the Early Years Learning Framework (EYLF) Version 2.0 Australia.
        When suggesting activities:
        - Always specify which EYLF outcomes the activity addresses (Identity, Community, Wellbeing, Learning, Communication)
        - Include 3 open ended questions educators can ask during the activity
        - Keep instructions simple and practical
        - Use low cost materials ECE centres typically have
        - Consider the specific developmental stage of the age group
        - Make the activity adaptable for different ability levels"""

        prompt = f"""Suggest one engaging activity for {age_group} children.
        Current mood: {mood}
        Weekly theme: {theme if theme else 'no specific theme'}
        Time available: {time_available}
        Available resources: {', '.join(resources) if resources else 'standard ECE materials'}

        Format your response as:

        ACTIVITY NAME:

        WHY THIS WORKS RIGHT NOW:

        MATERIALS NEEDED:

        STEP BY STEP:

        EYLF OUTCOMES ADDRESSED:

        OPEN ENDED QUESTIONS TO ASK:

        IF CHILDREN LOSE INTEREST:"""

        message = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        )

        activity_result = message.choices[0].message.content

        st.success("Activity generated!")
        st.markdown(activity_result)

        # Keep this available so the Parent Communication section below can reuse it
        st.session_state["last_activity_text"] = activity_result

        if child_id is not None:
            add_observation(
                child_id=child_id,
                activity=activity_result,
                observation_text=f"Mood: {mood}, Theme: {theme}, Time: {time_available}",
            )
            st.caption(f"✅ Saved to {selected_name}'s record")

# ==========================================
# PARENT COMMUNICATION (now child-aware + gives follow-up + home-chore suggestions)
# ==========================================

st.markdown("<br>", unsafe_allow_html=True)
st.divider()
st.markdown("<br>", unsafe_allow_html=True)
st.subheader("📝 Parent Communication Generator")

if child_id is not None:
    st.caption(f"Generating for: **{selected_name}**")
else:
    st.warning("No child selected — select one above so this message and its suggestions get saved to their record.")

default_activity_text = st.session_state.get("last_activity_text", "")
activity_done = st.text_area(
    "What did the child do today? Describe simply:",
    value=default_activity_text if default_activity_text else "",
    help="You can also just paste in the activity generated above, or describe it in your own words."
)

languages = st.multiselect(
    "Translate to (select one or more)",
    ["Hindi", "Spanish", "Arabic", "Mandarin", "Vietnamese", "French"],
    key="parent_comm_languages"
)


def extract_section(text, start_marker, end_markers):
    """Pulls the text between start_marker and whichever end_marker comes first."""
    if start_marker not in text:
        return ""
    chunk = text.split(start_marker, 1)[1]
    end_positions = [chunk.find(m) for m in end_markers if chunk.find(m) != -1]
    if end_positions:
        chunk = chunk[:min(end_positions)]
    return chunk.strip(" \n:-")


if st.button("Generate Parent Message", type="primary"):

    with st.spinner("Generating message..."):

        child_context = ""
        if child_record:
            child_context = f"The child's name is {child_record['name']}, age group {child_record['age_group']}, known interests: {child_record['interests'] or 'not specified'}."

        comm_prompt = f"""{child_context}
        Today's activity/observation: {activity_done}

        Write a response for the educator with these exact sections:

        PARENT MESSAGE:
        A warm, professional message to the parent explaining what the child did and what they're developing developmentally, in plain language suitable for a parent with no ECE background.

        TRY THIS AT HOME:
        One simple activity the parent can do at home that repeats or reinforces the same skill.

        BUILD ON IT NEXT:
        One related follow-up activity (a step up in challenge) that extends the same skill area further.

        INVOLVE THEM IN A HOUSEHOLD TASK:
        One everyday household chore or task the parent can involve the child in that uses the same skill (e.g. if it's hand-eye coordination, something like helping set the table or sorting laundry by color).

        {"Also provide the PARENT MESSAGE section translated into: " + ", ".join(languages) if languages else ""}
        """

        comm_message = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are an expert early childhood educator who writes warm, professional, practical parent communications grounded in child development."},
                {"role": "user", "content": comm_prompt}
            ]
        )

        comm_result = comm_message.choices[0].message.content

        st.success("Message generated!")
        st.markdown(comm_result)

        # Pull out the "try this at home" + "build on it" + "household task" bits separately
        home_bits = []
        for label, markers in [
            ("Try this at home", ["BUILD ON IT NEXT", "INVOLVE THEM"]),
            ("Build on it next", ["INVOLVE THEM", "PARENT MESSAGE"]),
            ("Household task", ["PARENT MESSAGE"]),
        ]:
            pass  # simple extraction below covers the common case

        home_suggestion_text = extract_section(comm_result, "TRY THIS AT HOME:", ["BUILD ON IT NEXT:", "INVOLVE THEM IN A HOUSEHOLD TASK:"])
        build_on_it_text = extract_section(comm_result, "BUILD ON IT NEXT:", ["INVOLVE THEM IN A HOUSEHOLD TASK:"])
        household_task_text = extract_section(comm_result, "INVOLVE THEM IN A HOUSEHOLD TASK:", [])

        combined_home_suggestion = "\n".join(filter(None, [
            f"At home: {home_suggestion_text}" if home_suggestion_text else "",
            f"Next level: {build_on_it_text}" if build_on_it_text else "",
            f"Household task: {household_task_text}" if household_task_text else "",
        ]))

        if child_id is not None:
            add_observation(
                child_id=child_id,
                observation_text=activity_done,
                parent_note=comm_result,
                home_suggestion=combined_home_suggestion,
            )
            st.caption(f"✅ Saved to {selected_name}'s record")

# ==========================================
# WEEKLY PROGRAM PLANNER
# ==========================================

st.markdown("<br>", unsafe_allow_html=True)
st.divider()
st.markdown("<br>", unsafe_allow_html=True)
st.subheader("📅 Weekly Program Planner")

week_theme = st.text_input("Theme for this week")
age_for_plan = st.selectbox(
    "Age group for weekly plan",
    ["Babies 0-1 years", "Toddlers 1-3 years", "Preschool 3-5 years"]
)

if st.button("Generate Weekly Plan", type="primary"):

    with st.spinner("Generating weekly plan..."):

        plan_prompt = f"""Create a 5 day activity program for {age_for_plan} children with the theme: {week_theme}

        For each day provide:
        - Activity name
        - Materials needed
        - Step by step instructions
        - EYLF outcomes addressed
        - One open ended question for educators to ask
        - One simple parent communication tip

        Make it practical, low cost and engaging."""

        plan_message = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are an expert early childhood educator specialising in curriculum planning aligned to EYLF Version 2.0 Australia."},
                {"role": "user", "content": plan_prompt}
            ]
        )

        st.success("Weekly plan generated!")
        st.markdown(plan_message.choices[0].message.content)

# ==========================================
# CHILD HISTORY
# ==========================================

if child_id is not None:
    st.markdown("<br>", unsafe_allow_html=True)
    st.divider()
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader(f"📖 {selected_name}'s History")

    history = get_observations(child_id)
    if not history:
        st.caption("No saved entries yet — generate an activity or parent message above to start building this child's record.")
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
# SITUATION-BASED SUPPORT
# ==========================================

st.markdown("<br>", unsafe_allow_html=True)
st.divider()
st.markdown("<br>", unsafe_allow_html=True)
observation_tab(client)

# ==========================================
# LEARNING STORY GENERATOR
# ==========================================

st.markdown("<br>", unsafe_allow_html=True)
st.divider()
st.markdown("<br>", unsafe_allow_html=True)
learning_story_tab(client)

# ==========================================
# STORY TIME GENERATOR
# ==========================================

st.markdown("<br>", unsafe_allow_html=True)
st.divider()
st.markdown("<br>", unsafe_allow_html=True)
story_generator_tab(client)

# ==========================================
# WEEKLY WORKSHEET GENERATOR
# ==========================================

st.markdown("<br>", unsafe_allow_html=True)
st.divider()
st.markdown("<br>", unsafe_allow_html=True)
worksheet_tab(client)