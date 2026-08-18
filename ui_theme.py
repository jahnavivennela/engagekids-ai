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

    /* Sidebar nav */
    section[data-testid="stSidebar"] {{
        background: linear-gradient(180deg, #FFF3E0 0%, #EAF6FF 100%);
    }}
    section[data-testid="stSidebar"] a > div:hover {{
        transform: translateX(3px);
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


# Order matters — used to give each section a distinct, consistent color
# both in the sidebar and in its own colored icon badge.
NAV_ITEMS = [
    ("select-child", "👤", "Select Child", "coral"),
    ("quick-activity", "⚡", "Quick Activity", "peach"),
    ("home-message", "🏠", "Home Message", "green"),
    ("weekly-planner", "📅", "Weekly Planner", "blue"),
    ("child-history", "📖", "Child History", "lavender"),
    ("situation-support", "👀", "Situation Support", "coral"),
    ("learning-story", "📔", "Learning Story", "yellow"),
    ("story-time", "📚", "Story Time", "peach"),
    ("worksheets", "🖍️", "Worksheets", "green"),
]


def section_header(icon: str, title: str, anchor_id: str, color_key: str):
    """Drop-in replacement for a plain st.subheader() call — a colorful
    icon badge + the same title text + an invisible anchor for the sidebar
    to jump to. Same spot in the page, same title, purely visual upgrade.
    Use with st.markdown(..., unsafe_allow_html=True)."""
    color = PALETTE.get(color_key, PALETTE["coral"])
    return f'''
    <div id="{anchor_id}"></div>
    <div style="display:flex;align-items:center;gap:14px;margin:6px 0 14px 0;">
        <div style="background:{color};width:46px;height:46px;min-width:46px;border-radius:50%;
                    display:flex;align-items:center;justify-content:center;font-size:22px;
                    box-shadow:0 3px 8px rgba(0,0,0,0.15);">{icon}</div>
        <div style="font-size:25px;font-weight:700;color:#333;">{title}</div>
    </div>
    '''


def section_anchor(anchor_id: str):
    """Just the invisible anchor, for sections whose title lives inside
    another file (e.g. worksheet_tab's own st.subheader) that isn't being
    touched — still lets the sidebar jump to the right place."""
    return f'<div id="{anchor_id}"></div>'


def render_sidebar_nav():
    """Colorful icon sidebar — same-page anchor links only (pure browser
    scroll, no rerun, no state touched)."""
    with st.sidebar:
        st.markdown(
            '<div style="text-align:center;padding:6px 0 18px 0;">'
            '<span style="font-size:30px;">🌟</span><br>'
            '<b style="font-size:17px;">EngageKids AI</b></div>',
            unsafe_allow_html=True,
        )
        for anchor_id, icon, label, color_key in NAV_ITEMS:
            color = PALETTE.get(color_key, PALETTE["coral"])
            st.markdown(
                f'''<a href="#{anchor_id}" style="text-decoration:none;">
                    <div style="display:flex;align-items:center;gap:10px;padding:10px 14px;
                                margin:5px 0;border-radius:12px;background:{color}22;
                                border-left:5px solid {color};color:#333;font-weight:600;
                                font-size:15px;">
                        <span style="font-size:19px;">{icon}</span><span>{label}</span>
                    </div>
                </a>''',
                unsafe_allow_html=True,
            )