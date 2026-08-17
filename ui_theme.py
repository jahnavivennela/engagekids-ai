"""
ui_theme.py

Shared visual theme for EngageKids AI — one place to control the color
palette, section "cards", the divider style, and the watermark, so every
tab in the app looks like one consistent product instead of a stack of
separately-styled pieces.

Usage in engagekids_v1.py:
    from ui_theme import apply_theme, section_divider
    apply_theme()   # once, right after st.set_page_config()
    ...
    section_divider()   # between major sections, instead of manual <br>/divider
"""

import streamlit as st

# Same palette used in worksheet_generator.py, so worksheets and the rest of
# the app feel like one product rather than two different tools bolted together.
PALETTE = {
    "coral": "#FF6B6B",
    "yellow": "#FFD93D",
    "green": "#6BCB77",
    "blue": "#4D96FF",
    "lavender": "#B983FF",
    "peach": "#FF9F45",
}


def apply_theme():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Baloo+2:wght@500;700&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Baloo 2', 'Trebuchet MS', sans-serif;
    }}

    .stApp {{
        background: linear-gradient(160deg, #FFF9EC 0%, #FFF3E0 40%, #EAF6FF 100%);
    }}

    /* Headings */
    h1 {{ color: {PALETTE['coral']}; }}
    h2, h3 {{ color: #333; }}
    .stApp h3 {{
        border-left: 6px solid {PALETTE['blue']};
        padding-left: 10px;
        border-radius: 3px;
    }}

    /* Buttons */
    .stButton > button {{
        background: linear-gradient(90deg, {PALETTE['coral']}, {PALETTE['peach']});
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.5em 1.4em;
        font-weight: 700;
        box-shadow: 0 3px 0 rgba(0,0,0,0.08);
        transition: transform 0.1s ease;
    }}
    .stButton > button:hover {{
        transform: translateY(-2px);
        color: white;
    }}
    .stDownloadButton > button {{
        background: linear-gradient(90deg, {PALETTE['green']}, {PALETTE['blue']});
        color: white;
        border: none;
        border-radius: 12px;
        font-weight: 700;
    }}

    /* Bordered containers (st.container(border=True)) get a soft card look */
    div[data-testid="stVerticalBlockBorderWrapper"] {{
        border-radius: 16px !important;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        background: white;
        padding: 4px;
    }}

    /* Inputs */
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {{
        border-radius: 10px !important;
    }}

    /* Rainbow divider used by section_divider() */
    .ek-divider {{
        height: 5px;
        border: none;
        border-radius: 5px;
        margin: 28px 0;
        background: linear-gradient(90deg, {PALETTE['coral']}, {PALETTE['yellow']}, {PALETTE['green']}, {PALETTE['blue']}, {PALETTE['lavender']});
        opacity: 0.85;
    }}

    /* Watermark, bottom-right, non-interactive */
    .ek-watermark {{
        position: fixed;
        bottom: 10px;
        right: 16px;
        font-size: 13px;
        color: #bbb;
        opacity: 0.6;
        z-index: 9999;
        pointer-events: none;
        font-weight: 700;
        user-select: none;
    }}
    </style>

    <div class="ek-watermark">🌟 EngageKids AI</div>
    """, unsafe_allow_html=True)


def section_divider():
    """A colorful divider with consistent spacing — replaces the repeated
    st.markdown('<br>') + st.divider() + st.markdown('<br>') pattern."""
    st.markdown('<hr class="ek-divider">', unsafe_allow_html=True)