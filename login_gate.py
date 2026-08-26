"""
login_gate.py

A cosmetic login screen — any email + any password (as long as both
fields have something in them) signs you in. No database, no account
list, no restrictions.

On successful sign-in, this shows a brief full-screen "loading" state
and then reruns, so it feels like navigating INTO the app rather than
content just appearing below the form.

USAGE — add to the very top of your main app file:

    from ui_theme import apply_theme, render_sidebar_nav
    from login_gate import show_login_gate

    apply_theme()
    if not show_login_gate():
        st.stop()          # <-- nothing below this runs until signed in
    render_sidebar_nav()
    # ... rest of your app goes here

IMPORTANT for the "feels like a real app" effect to work:
    Make sure NOTHING else (sidebar, headers, tabs, etc.) is rendered
    BEFORE show_login_gate() is called and its result checked. If any
    other UI renders first, it will show up above/around the login
    card and break the illusion of a separate screen. show_login_gate()
    should be the very first UI call in your script, right after
    apply_theme().
"""

import time
import streamlit as st

from ui_theme import PALETTE

_FONT_LINKS = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
"""

_STYLE = f"""
<style>
html, body, [class*="css"] {{
    font-family: 'Inter', sans-serif;
}}
div[data-testid="stAppViewContainer"] > .main {{
    background: radial-gradient(circle at 12% 18%, {PALETTE['coral']}22 0%, transparent 40%),
                radial-gradient(circle at 88% 15%, {PALETTE['blue']}1f 0%, transparent 42%),
                radial-gradient(circle at 20% 88%, {PALETTE['green']}22 0%, transparent 42%),
                radial-gradient(circle at 90% 85%, {PALETTE['lavender']}1f 0%, transparent 42%),
                #FBF6EC;
    background-attachment: fixed;
}}
div[data-testid="stAppViewContainer"] > .main .block-container{{
    max-width: 460px;
    padding-top: 9vh;
}}
.ek-login-card{{
    background:#FFFFFF;
    border:1px solid rgba(32,36,44,0.10);
    border-radius:18px;
    padding:38px 32px 30px;
    text-align:center;
    box-shadow:0 8px 28px rgba(32,36,44,0.14);
    position:relative;
    overflow:hidden;
    margin-bottom: 24px;
}}
.ek-login-card::before{{
    content:"";
    position:absolute; top:0; left:0; right:0; height:6px;
    background:linear-gradient(90deg, {PALETTE['coral']} 0%, {PALETTE['peach']} 25%, {PALETTE['green']} 50%, {PALETTE['blue']} 75%, {PALETTE['lavender']} 100%);
}}
.ek-login-badge{{
    width:54px; height:54px; margin:4px auto 20px;
    border-radius:14px;
    background:linear-gradient(135deg, {PALETTE['coral']} 0%, {PALETTE['peach']} 100%);
    display:flex; align-items:center; justify-content:center;
    font-size:25px;
    box-shadow:0 8px 18px -6px {PALETTE['coral']}88;
}}
.ek-login-card h1{{
    font-family:'Fraunces', serif; font-size:24px; font-weight:600;
    color:#20242C; margin-bottom:8px;
}}
.ek-login-sub{{
    font-size:13.5px; color:#8A8377; margin-bottom:10px;
}}
.stFormSubmitButton > button{{
    background: linear-gradient(90deg, {PALETTE['coral']} 0%, {PALETTE['peach']} 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 11px !important;
    font-weight: 700 !important;
    padding: 0.6em 0 !important;
    box-shadow: 0 3px 0 rgba(0,0,0,0.08) !important;
    transition: transform 0.1s ease, background 0.15s ease !important;
}}
.stFormSubmitButton > button:hover{{
    transform: translateY(-2px);
}}
.stTextInput input{{
    border-radius: 10px !important;
    border-color: rgba(32,36,44,0.14) !important;
}}
.ek-loading-wrap{{
    text-align:center;
    padding: 22vh 0 0;
}}
.ek-loading-wrap h2{{
    font-family:'Fraunces', serif; font-size:22px; color:#20242C;
}}
</style>
"""

_CARD_HEADER = """
<div class="ek-login-card">
    <div class="ek-login-badge">✨</div>
    <h1>Welcome back</h1>
    <div class="ek-login-sub">Sign in to EngageKids AI</div>
</div>
"""


def show_login_gate() -> bool:
    """
    Renders the login screen if the user isn't signed in yet.
    Returns True if the user IS signed in (safe to render the rest of
    the app), False if the login screen was shown instead (caller
    should st.stop() right after).
    """
    if st.session_state.get("ek_logged_in"):
        return True

    placeholder = st.empty()

    with placeholder.container():
        st.markdown(_FONT_LINKS, unsafe_allow_html=True)
        st.markdown(_STYLE, unsafe_allow_html=True)
        st.markdown(_CARD_HEADER, unsafe_allow_html=True)

        with st.form("ek_login_form", clear_on_submit=False):
            email = st.text_input("Email", value="", placeholder="you@example.com")
            password = st.text_input("Password", value="", type="password",
                                      placeholder="Enter your password")
            submitted = st.form_submit_button("Sign in", use_container_width=True)

        if submitted:
            if not email.strip() or not password.strip():
                st.error("Please enter both email and password.")
            else:
                st.session_state["ek_logged_in"] = True
                st.session_state["ek_user"] = {"email": email.strip()}

                # replace the entire login card with a full-screen
                # transition so it feels like navigating into the
                # app, not content appending below the form
                placeholder.empty()
                with placeholder.container():
                    st.markdown(_FONT_LINKS, unsafe_allow_html=True)
                    st.markdown(_STYLE, unsafe_allow_html=True)
                    st.markdown("""
                    <div class="ek-loading-wrap">
                        <h2>Taking you in...</h2>
                    </div>
                    """, unsafe_allow_html=True)
                time.sleep(0.6)
                placeholder.empty()
                st.rerun()

    return False