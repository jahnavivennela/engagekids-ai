from groq import Groq
import streamlit as st
from observation import observation_tab
from learning_story import learning_story_tab
from story_generator import story_generator_tab

# Setup
api_key = st.secrets["GROQ_API_KEY"]
client = Groq(api_key=api_key)

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

        st.success("Activity generated!")
        st.markdown(message.choices[0].message.content)

# ==========================================
# PARENT COMMUNICATION
# ==========================================

st.markdown("<br>", unsafe_allow_html=True)
st.divider()
st.markdown("<br>", unsafe_allow_html=True)
st.subheader("📝 Parent Communication Generator")

activity_done = st.text_area("What did children do today? Describe simply:")

languages = st.multiselect(
    "Translate to (select one or more)",
    ["Hindi", "Spanish", "Arabic", "Mandarin", "Vietnamese", "French"],
    key="parent_comm_languages"
)

if st.button("Generate Parent Message", type="primary"):

    with st.spinner("Generating message..."):

        comm_prompt = f"""Write a warm professional parent communication message about this activity: {activity_done}

        The message should:
        - Be warm and engaging
        - Explain what children learned developmentally
        - Suggest one simple thing parents can do at home
        - Be suitable for families with no ECE background
        {"- Also provide the message translated into: " + ", ".join(languages) if languages else "- Keep in English only"}"""

        comm_message = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are an expert early childhood educator who writes warm professional parent communications."},
                {"role": "user", "content": comm_prompt}
            ]
        )

        st.success("Message generated!")
        st.markdown(comm_message.choices[0].message.content)

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