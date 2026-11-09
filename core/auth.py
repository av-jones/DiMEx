"""Email and password sign-in. Nothing else on the app renders until a visitor signs in.

Accounts live in Streamlit secrets (never in the repo), as email = bcrypt hash:

    [users]
    "name@unf.edu" = "$2b$12$..."

Make a line with: python scripts/add_user.py name@unf.edu
Locally, put it in .streamlit/secrets.toml (git-ignored); on Streamlit Cloud, in App settings -> Secrets.
"""
import time

import streamlit as st

# bcrypt is imported only when someone signs in with this app's own form, so the app still runs
# (e.g. as a private Streamlit Cloud app) even where bcrypt isn't installed.
MAX_TRIES = 5          # per browser session, then a pause before the next try


def _users():
    try:
        return {k.strip().lower(): v for k, v in st.secrets.get("users", {}).items()}
    except FileNotFoundError:          # no secrets file at all
        return {}


def _check(email, password):
    import bcrypt
    stored = _users().get(email.strip().lower())
    # An unknown email is checked against a throwaway hash, so it takes as long as a wrong password
    dummy = bcrypt.hashpw(b"not-a-real-password", bcrypt.gensalt()).decode()
    ok = bcrypt.checkpw(password.encode(), (stored or dummy).encode())
    return ok and stored is not None


def auth_on():
    """Sign-in is required only when at least one account is set up."""
    return bool(_users())


def _cloud_viewer():
    """Streamlit Cloud's sign-in on a private app passes the viewer in an X-Streamlit-User header.
    That header is undocumented and may change, so anything missing or unreadable gives {}."""
    try:
        raw = st.context.headers.get("X-Streamlit-User")
    except Exception:
        return {}
    if not raw:
        return {}
    import base64
    import json
    for decode in (lambda v: v, lambda v: base64.b64decode(v + "=" * (-len(v) % 4)).decode()):
        try:
            info = json.loads(decode(raw))
            if isinstance(info, dict) and info.get("email"):
                return info
        except Exception:
            continue
    return {"email": raw} if "@" in raw and " " not in raw else {}


def viewer_email():
    """Who is viewing, for display only (never for access decisions): this app's own sign-in if used,
    else Streamlit Cloud's sign-in on a private app. None if unknown."""
    return st.session_state.get("user") or _cloud_viewer().get("email")


def viewer_name():
    """A first name to greet the viewer with, or None.
    Order: a name set in secrets ([names] "email" = "AV"), a name Cloud provides, then a guess from
    an email like first.last@... (only when the address has a separator, so 'jdoe42@' isn't guessed)."""
    import re
    email = viewer_email()
    if not email:
        return None
    try:
        names = {k.strip().lower(): v for k, v in st.secrets.get("names", {}).items()}
    except Exception:
        names = {}
    if email.lower() in names:
        return names[email.lower()]
    cloud = _cloud_viewer()
    for key in ("given_name", "first_name", "name"):
        if cloud.get(key):
            return str(cloud[key]).split()[0]
    local = email.split("@")[0]
    parts = [p for p in re.split(r"[._-]", local) if p.isalpha()]
    return parts[0].capitalize() if len(re.split(r"[._-]", local)) > 1 and parts else None


def greeting():
    """'Good morning/afternoon/evening' in the viewer's own time zone (from the browser)."""
    from datetime import datetime
    from zoneinfo import ZoneInfo
    try:
        now = datetime.now(ZoneInfo(st.context.timezone or "America/New_York"))
    except Exception:
        now = datetime.now(ZoneInfo("America/New_York"))
    part = "morning" if 5 <= now.hour < 12 else "afternoon" if now.hour < 17 else "evening"
    return f"Good {part}"


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
