"""
ui_theme.py

Shared visual theme for EngageKids AI — one place to control the color
palette, section "cards", the divider style, and the watermark, so every
tab in the app looks like one consistent product instead of a stack of
separately-styled pieces.

DROP-IN REPLACEMENT: same function names, same PALETTE keys, same
NAV_ITEMS tuple shape as before — every call site in your other files
(engagekids_v1.py, worksheet_generator.py, etc.) keeps working with zero
changes. Only what these functions render has been redesigned.

Usage in engagekids_v1.py:
    from ui_theme import apply_theme, section_divider
    apply_theme()   # once, right after st.set_page_config()
    ...
    section_divider("peach")   # between major sections — pass the color
                                # of the section coming NEXT
"""

import streamlit as st

# Same 6 keys as before (coral, yellow, green, blue, lavender, peach) so any
# section_header(..., "coral") or similar call elsewhere keeps working.
# Values are re-tuned to read as ONE coordinated palette (warm accent +
# two structural colors + two muted supports) instead of six competing
# bright tones — same names, calmer, more considered hexes.
PALETTE = {
    "coral": "#E6A335",     # primary accent — was bright red-coral, now the warm marigold used app-wide
    "peach": "#D98E4A",     # secondary warm, close cousin of coral for "in the moment" tools
    "blue": "#2F5EA8",      # structural accent — "planned ahead" tools
    "lavender": "#6B5B95",  # muted plum, used sparingly for the odd accent
    "green": "#4C8B6B",     # sage — "documented & sent home" tools
    "yellow": "#C4841A",    # deep gold, for small highlight moments only
}


def apply_theme():
    # Loaded as <link> tags (with preconnect) rather than a CSS @import —
    # more reliable than @import inside an injected <style> block.
    st.markdown("""
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&family=Inter:wght@400;500;600;700&family=IBM+Plex+Mono:wght@500&display=swap" rel="stylesheet">
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <style>
    /* Inter for body/inputs/buttons — Fraunces reserved for headers only,
       so the app reads as a considered product, not a kids-app template. */
    html, body, [class*="css"] {{
        font-family: 'Inter', sans-serif;
    }}

    .stApp {{
        background: #FBF6EC;
    }}

    /* Main content: a comfortable reading width + generous outer
       padding, instead of stretching edge-to-edge or sitting flush
       against the top of the viewport. */
    div[data-testid="stAppViewContainer"] > .main .block-container {{
        max-width: 980px;
        padding-top: 2.6rem;
        padding-bottom: 4rem;
        padding-left: 2.5rem;
        padding-right: 2.5rem;
    }}

    /* Headings */
    h1 {{
        color: #20242C;
        font-family: 'Fraunces', serif;
        font-weight: 600;
        margin-bottom: 0.6em;
    }}
    h2, h3 {{
        color: #20242C;
        font-family: 'Fraunces', serif;
        font-weight: 600;
        margin-top: 1.4em;
        margin-bottom: 0.7em;
    }}
    .stApp h3 {{
        border-left: 4px solid {PALETTE['coral']};
        padding-left: 12px;
        border-radius: 2px;
    }}

    /* Give Streamlit's own vertical blocks (columns, widgets stacked
       one after another) a bit more room to breathe than the default
       cramped spacing. */
    div[data-testid="stVerticalBlock"] {{
        gap: 0.9rem;
    }}

    /* Buttons — one confident accent instead of a rainbow gradient */
    .stButton > button {{
        background: {PALETTE['coral']};
        color: white;
        border: none;
        border-radius: 11px;
        padding: 0.5em 1.4em;
        font-weight: 700;
        box-shadow: 0 3px 0 rgba(0,0,0,0.08);
        transition: transform 0.1s ease, background 0.15s ease;
    }}
    .stButton > button:hover {{
        transform: translateY(-2px);
        background: #C4841A;
        color: white;
    }}
    .stDownloadButton > button {{
        background: {PALETTE['green']};
        color: white;
        border: none;
        border-radius: 11px;
        font-weight: 700;
    }}

    /* Bordered containers (st.container(border=True)) get a quiet card
       look, with real internal padding and space below each one so
       stacked sections don't crowd each other. */
    div[data-testid="stVerticalBlockBorderWrapper"] {{
        border-radius: 16px !important;
        border: 1px solid rgba(32,36,44,0.10);
        box-shadow: 0 4px 16px rgba(32,36,44,0.10);
        background: white;
        padding: 22px 24px;
        margin-bottom: 28px;
        transition: box-shadow 0.2s ease, transform 0.2s ease;
    }}
    div[data-testid="stVerticalBlockBorderWrapper"]:hover {{
        box-shadow: 0 10px 26px rgba(32,36,44,0.14);
        transform: translateY(-2px);
    }}

    /* Inputs */
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {{
        border-radius: 10px !important;
        border-color: rgba(32,36,44,0.14) !important;
    }}

    /* Sidebar nav — quiet paper tone instead of a two-tone rainbow gradient */
    section[data-testid="stSidebar"] {{
        background: #FFFDF8;
        border-right: 1px solid rgba(32,36,44,0.08);
    }}
    section[data-testid="stSidebar"] a > div:hover {{
        transform: translateX(3px);
    }}

    /* Watermark, bottom-right, non-interactive */
    .ek-watermark {{
        position: fixed;
        bottom: 10px;
        right: 16px;
        font-size: 12px;
        color: #8A8377;
        opacity: 0.7;
        z-index: 9999;
        pointer-events: none;
        font-weight: 600;
        font-family: 'IBM Plex Mono', monospace;
        letter-spacing: 0.02em;
        user-select: none;
    }}
    </style>

    <div class="ek-watermark">EngageKids AI</div>
    """, unsafe_allow_html=True)


def section_divider(color_key: str = "coral"):
    """A single-tone divider matching the color of the section it leads
    into. Pass the NEXT section's color_key — same API as before."""
    color = PALETTE.get(color_key, PALETTE["coral"])
    st.markdown(
        f'<hr style="height:2px;border:none;border-radius:2px;margin:46px 0;'
        f'background:{color};opacity:0.4;">',
        unsafe_allow_html=True,
    )


# Order and shape unchanged — (anchor_id, icon, label, color_key) — so any
# code iterating NAV_ITEMS elsewhere keeps working without edits.
NAV_ITEMS = [
    ("select-child", "👤", "Select Child", "coral"),
    ("situation-support", "👀", "Situation Support", "coral"),
    ("learning-story", "📔", "Learning Story", "green"),
    ("child-history", "📖", "Child History", "green"),
    ("quick-activity", "⚡", "Quick Activity", "coral"),
    ("magic-trick", "✨", "Magic Trick", "coral"),
    ("weekly-planner", "📅", "Weekly Planner", "blue"),
    ("worksheets", "🖍️", "Worksheets", "blue"),
    ("home-message", "🏠", "Home Message", "green"),
    ("story-time", "📚", "Story Time", "coral"),
]


def section_header(icon: str, title: str, anchor_id: str, color_key: str):
    """Drop-in replacement for a plain st.subheader() call — same
    signature as before. A quiet icon badge + title + invisible anchor
    for the sidebar to jump to."""
    color = PALETTE.get(color_key, PALETTE["coral"])
    return f'''
    <div id="{anchor_id}"></div>
    <div style="display:flex;align-items:center;gap:16px;margin:12px 0 22px 0;">
        <div style="background:{color}18;border:1.5px solid {color}55;width:46px;height:46px;min-width:46px;border-radius:13px;
                    display:flex;align-items:center;justify-content:center;font-size:20px;">{icon}</div>
        <div style="font-size:23px;font-weight:600;color:#20242C;font-family:'Fraunces',serif;">{title}</div>
    </div>
    '''


def section_anchor(anchor_id: str):
    """Just the invisible anchor — unchanged API."""
    return f'<div id="{anchor_id}"></div>'


def render_sidebar_nav():
    """Quiet, coordinated sidebar nav — same-page anchor links only
    (pure browser scroll, no rerun, no state touched). Same behavior
    as before, restyled."""
    with st.sidebar:
        st.markdown(
            '<div style="text-align:center;padding:10px 0 20px 0;">'
            '<b style="font-size:16px;font-family:\'Fraunces\',serif;color:#20242C;">EngageKids AI</b></div>',
            unsafe_allow_html=True,
        )
        for anchor_id, icon, label, color_key in NAV_ITEMS:
            color = PALETTE.get(color_key, PALETTE["coral"])
            st.markdown(
                f'''<a href="#{anchor_id}" style="text-decoration:none;">
                    <div style="display:flex;align-items:center;gap:11px;padding:11px 14px;
                                margin:6px 0;border-radius:10px;background:{color}14;
                                border-left:3px solid {color};color:#20242C;font-weight:500;
                                font-size:14px;">
                        <span style="font-size:16px;">{icon}</span><span>{label}</span>
                    </div>
                </a>''',
                unsafe_allow_html=True,
            )