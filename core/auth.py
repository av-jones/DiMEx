"""Email and password sign-in. Nothing else on the app renders until a visitor signs in.

Accounts live in Streamlit secrets (never in the repo), as email = bcrypt hash:

    [users]
    "name@unf.edu" = "$2b$12$..."

Make a line with: python scripts/add_user.py name@unf.edu
Locally, put it in .streamlit/secrets.toml (git-ignored); on Streamlit Cloud, in App settings -> Secrets.
"""
import time

import bcrypt
import streamlit as st

# Checked when an email isn't on the list, so a wrong email takes as long as a wrong password
_DUMMY = bcrypt.hashpw(b"not-a-real-password", bcrypt.gensalt())
MAX_TRIES = 5          # per browser session, then a pause before the next try


def _users():
    try:
        return {k.strip().lower(): v for k, v in st.secrets.get("users", {}).items()}
    except FileNotFoundError:          # no secrets file at all
        return {}


def _check(email, password):
    stored = _users().get(email.strip().lower())
    ok = bcrypt.checkpw(password.encode(), (stored or _DUMMY.decode()).encode())
    return ok and stored is not None


def auth_on():
    """Sign-in is required only when at least one account is set up."""
    return bool(_users())


def viewer_email():
    """Who is viewing, for display only (never for access decisions).
    1. this app's own sign-in, if used
    2. Streamlit Cloud's sign-in on a private app: Cloud passes the viewer in an X-Streamlit-User header.
       That header is undocumented and may change, so if it's missing or unreadable this returns None."""
    if st.session_state.get("user"):
        return st.session_state.user
    try:
        raw = st.context.headers.get("X-Streamlit-User")
    except Exception:
        return None
    if not raw:
        return None
    import base64
    import json
    for decode in (lambda v: v, lambda v: base64.b64decode(v + "=" * (-len(v) % 4)).decode()):
        try:
            info = json.loads(decode(raw))
            email = info.get("email") if isinstance(info, dict) else None
            if email:
                return email
        except Exception:
            continue
    return raw if "@" in raw and " " not in raw else None


def signed_in():
    return bool(st.session_state.get("user"))


def sign_out():
    st.session_state.pop("user", None)


def login_page():
    """The sign-in form. Signing in reruns the app, which then shows the real pages."""
    _, mid, _ = st.columns([1, 1.2, 1])
    with mid:
        st.markdown("<div style='height:48px'></div>", unsafe_allow_html=True)
        with st.container(border=True, key="card_login"):
            st.subheader("Sign in to DiMEx")
            st.caption("DiMEx is a class research project. Access is limited to invited accounts.")
            with st.form("login", border=False):
                email = st.text_input("Email", autocomplete="email")
                password = st.text_input("Password", type="password", autocomplete="current-password")
                go = st.form_submit_button("Sign in", type="primary", width="stretch")
            if go:
                tries = st.session_state.get("login_tries", 0)
                if tries >= MAX_TRIES:
                    time.sleep(min(30, 2 ** (tries - MAX_TRIES)))       # slows down password guessing
                if email and password and _check(email, password):
                    st.session_state.user = email.strip().lower()
                    st.session_state.login_tries = 0
                    st.rerun()
                st.session_state.login_tries = tries + 1
                st.error("That email and password don't match an account.")
            st.caption("Need access? Ask a project team member to add you.")
