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
    section_divider("peach")   # between major sections — pass the color
                                # of the section coming NEXT
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
    # Loaded as <link> tags (with preconnect) rather than a CSS @import —
    # @import inside a <style> block injected via st.markdown can silently
    # fail or load late on some setups; <link> tags are more reliable and
    # show up as a normal failed network request in devtools if blocked.
    st.markdown("""
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Baloo+2:wght@600;700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <style>
    /* Inter for body/inputs/buttons — Baloo 2 reserved for big headers only,
       so the app reads as clean/professional while keeping brand personality
       in the headline moments. */
    html, body, [class*="css"] {{
        font-family: 'Inter', 'Trebuchet MS', sans-serif;
    }}

    .stApp {{
        background: linear-gradient(160deg, #FFFBF5 0%, #FFF6EA 100%);
    }}

    /* Headings */
    h1 {{
        color: {PALETTE['coral']};
        font-family: 'Baloo 2', sans-serif;
    }}
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

    /* Bordered containers (st.container(border=True)) get a soft card look,
       now with a subtle lift on hover so it feels like a built product. */
    div[data-testid="stVerticalBlockBorderWrapper"] {{
        border-radius: 16px !important;
        border: 1px solid rgba(0,0,0,0.08);
        box-shadow: 0 4px 16px rgba(0,0,0,0.12);
        background: white;
        padding: 4px;
        transition: box-shadow 0.2s ease, transform 0.2s ease;
    }}
    div[data-testid="stVerticalBlockBorderWrapper"]:hover {{
        box-shadow: 0 8px 26px rgba(0,0,0,0.16);
        transform: translateY(-2px);
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


def section_divider(color_key: str = "coral"):
    """A single-tone divider matching the color of the section it leads
    into — replaces the old all-colors-at-once rainbow bar, which read as
    busy rather than structured. Pass the NEXT section's color_key."""
    color = PALETTE.get(color_key, PALETTE["coral"])
    st.markdown(
        f'<hr style="height:3px;border:none;border-radius:3px;margin:28px 0;'
        f'background:{color};opacity:0.55;">',
        unsafe_allow_html=True,
    )


# Order matters — used to give each section a distinct, consistent color
# both in the sidebar and in its own colored icon badge.
NAV_ITEMS = [
    ("select-child", "👤", "Select Child", "coral"),
    ("situation-support", "👀", "Situation Support", "coral"),
    ("learning-story", "📔", "Learning Story", "yellow"),
    ("child-history", "📖", "Child History", "lavender"),
    ("quick-activity", "⚡", "Quick Activity", "peach"),
    ("magic-trick", "✨", "Magic Trick", "lavender"),
    ("weekly-planner", "📅", "Weekly Planner", "blue"),
    ("worksheets", "🖍️", "Worksheets", "green"),
    ("home-message", "🏠", "Home Message", "green"),
    ("story-time", "📚", "Story Time", "peach"),
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
        <div style="font-size:25px;font-weight:700;color:#333;font-family:'Baloo 2',sans-serif;">{title}</div>
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
            '<b style="font-size:17px;font-family:\'Baloo 2\',sans-serif;">EngageKids AI</b></div>',
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