"""Streamlit helpers shared by all pages: caching and small display pieces."""
import streamlit as st

from core import data
from core.registry import Predictor


@st.cache_resource(show_spinner="Loading model...")
def load_predictor(name):
    return Predictor(name)          # loaded once per model, reused on every rerun


@st.cache_data(show_spinner="Loading predictions...")
def load_predictions():
    return data.load_predictions()


@st.cache_data
def load_pairs():
    if data.has_predictions():
        return data.pair_counts(load_predictions())
    return data.load_pairs()


@st.cache_data(show_spinner=False, max_entries=64)
def _placeholder_pair(drug, condition):
    return data.pair_predictions(drug, condition)


def pair_predictions(drug, condition):
    """One drug-condition pair's predictions. Real ones are sliced from the full table (loaded once)."""
    if data.has_predictions():
        df = load_predictions()
        return df[(df.drug == drug) & (df.condition == condition)]
    return _placeholder_pair(drug, condition)


@st.cache_data(show_spinner="Loading Druglib reviews...")
def load_druglib():
    from core import druglib
    return druglib.load()


def highlight(text, span):
    """Markdown with the span highlighted. Escapes $ so Streamlit doesn't read it as math."""
    text = text.replace("$", r"\$")
    if span and span in text:
        return text.replace(span, f":blue-background[{span}]", 1)
    return text


def card(parent=None, stretch=False):
    """A bordered container with a white background (styled by its key in app.py).
    stretch=True fills the height of its column, so boxes side by side in a row line up.
    Keys are numbered in page order; app.py resets the counter on every run so they stay stable."""
    n = st.session_state.get("_card_n", 0)
    st.session_state["_card_n"] = n + 1
    return (parent or st).container(border=True, key=f"card_{n}", height="stretch" if stretch else "content")


def scroll_to(class_name):
    """Smoothly scroll the page to the first element with this class after this run renders. Streamlit has no
    scroll API, so a zero-height component runs a small script against the app page."""
    import time
    html = f"""<script>
      // {time.time()}  (unique text so the script runs on every request)
      const go = (tries) => {{
        const el = window.parent.document.querySelector(".{class_name}");
        if (el) el.scrollIntoView({{behavior: "smooth", block: "start"}});
        else if (tries > 0) setTimeout(() => go(tries - 1), 100);
      }};
      setTimeout(() => go(30), 150);
    </script>"""
    if hasattr(st, "iframe"):                   # newer Streamlit: st.iframe replaces components.html
        st.iframe(html, height=1)
    else:
        import streamlit.components.v1 as components
        components.html(html, height=0)


def serious_flag(text):
    """('⚠ Serious event mentioned' tag HTML, True) if the text mentions a serious event, else ('', False)."""
    import html
    from core.aspects import serious_mentions
    found = sorted(set(serious_mentions(text)))
    if not found:
        return "", False
    return (f"<span class='serious-flag' title='Mentions: {html.escape(', '.join(found))}'>"
            "⚠ Serious event mentioned</span>", True)


def review_box(text, key):
    """A card for one review: red-outlined and tinted when the review mentions a serious event."""
    _, serious = serious_flag(text)
    return st.container(border=True, key=f"serious_{key}") if serious else card()
