"""Streamlit helpers shared by all pages: caching and small display pieces."""
import streamlit as st

from core import data
from core.registry import USE_FAKE, Predictor


@st.cache_resource(show_spinner="Loading model...")
def load_predictor(name):
    return Predictor(name)          # loaded once per model, reused on every rerun


@st.cache_data(show_spinner="Loading predictions...")
def load_predictions():
    return data.load_predictions()


@st.cache_data
def load_evaluation():
    return data.evaluate()


def fake_data_banner():
    if USE_FAKE:
        st.warning("Demo data: these reviews and scores are generated placeholders. "
                   "Add checkpoints in core/registry.py and data/predictions.parquet to use real results.",
                   icon=":material/science:")


def highlight(text, span):
    """Markdown with the span highlighted. Escapes $ so Streamlit doesn't read it as math."""
    text = text.replace("$", r"\$")
    if span and span in text:
        return text.replace(span, f":orange-background[{span}]", 1)
    return text
