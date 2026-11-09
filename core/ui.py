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


def highlight(text, span):
    """Markdown with the span highlighted. Escapes $ so Streamlit doesn't read it as math."""
    text = text.replace("$", r"\$")
    if span and span in text:
        return text.replace(span, f":blue-background[{span}]", 1)
    return text


def card(parent=None):
    """A bordered container with a white background (styled by its key in app.py).
    Keys are numbered in page order; app.py resets the counter on every run so they stay stable."""
    n = st.session_state.get("_card_n", 0)
    st.session_state["_card_n"] = n + 1
    return (parent or st).container(border=True, key=f"card_{n}")
