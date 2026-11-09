"""Model card: what the app's model is, how it was trained and checked, and where it falls short."""
import streamlit as st

from core.registry import APP_MODEL, MODELS, is_real
from core.ui import card

st.title("Model card")
st.caption("What the DiMEx model is, how it was trained and tested, and what it shouldn't be used for")

if not is_real(APP_MODEL):
    st.info("This copy of the app is running on placeholder scores while the trained checkpoint is connected. "
            "The results below are from the training runs.")

left, right = st.columns(2, gap="large")
with left:
    with card(stretch=True):
        st.subheader("Model")
        st.markdown(f"""
- **Encoder:** {APP_MODEL} (`{MODELS[APP_MODEL]['hf_id']}`), fine-tuned with PyTorch and Hugging Face Transformers
- **Head:** two regression outputs per aspect, **valence** (negative → positive) and **arousal** (calm → intense), each 1–9
- **Input:** the review text paired with an aspect name: effectiveness, side effects or satisfaction
- **Output:** valence and arousal per aspect, mapped to Druglib's rating scales (1–5, or 1–10 for satisfaction) and an intensity band
""")
with right:
    with card(stretch=True):
        st.subheader("Training data")
        st.markdown("""
1. **DimABSA** (SemEval-2026 Task 3): restaurant and laptop reviews labeled with valence and arousal per aspect. Teaches the model what intensity sounds like.
2. **Druglib.com** (UCI ML Repository): about 4,100 patient reviews with effectiveness, side-effect and satisfaction ratings, converted to valence and arousal with a fixed table.

The app then scores **Drugs.com** reviews (215,063, UCI ML Repository), which have star ratings but no per-aspect labels.
""")

with card():
    st.subheader("How well it works")
    st.caption("Drugs.com transfer: 3-class agreement (Cohen's kappa ×100) between predicted satisfaction and "
               "the patient's own star rating, the same measure as Gräßer et al. (2018)")
    a, b, c = st.columns(3)
    a.metric("RoBERTa + DimABSA step", "58.6")
    b.metric("ModernBERT + DimABSA step", "61.7")
    c.metric("Gräßer et al. (2018) baseline", "26.8")
    st.markdown("""
- The DimABSA step **improved Drugs.com transfer by 2–6 points** across encoders.
- General-purpose encoders beat biomedical ones (BioBERT, BioRedditBERT) by **10+ points** on Drugs.com.
- On Druglib itself, the DimABSA step **slightly hurt** effectiveness and side-effect scores, so those two are best read alongside the review text.
- MAE, RMSE and accuracy are reported in the project paper.
""")

left, right = st.columns(2, gap="large")
with left:
    with card(stretch=True):
        st.subheader("Intended use")
        st.markdown("""
- Summarizing what **many** patients say about a drug for a condition
- Showing how *intensely* patients describe benefits and side effects, which star ratings can't capture
- Research and teaching in applied deep learning
""")
with right:
    with card(stretch=True):
        st.subheader("Not for")
        st.markdown("""
- **Medical decisions.** These are patient-reported experiences, not clinical evidence. Talk to a doctor or pharmacist.
- Judging a single review or a single patient
- Comparing drugs on safety or efficacy
""")

with card():
    st.subheader("Limitations")
    st.markdown("""
- **Intensity is experimental.** Arousal was learned from restaurant and laptop reviews and hasn't been checked against patient-rated intensity.
- **Only satisfaction has a check on Drugs.com** (star ratings). Effectiveness and side-effect scores there are unverified; a hand-labeled sample is planned.
- **Individual side effects** are found by keyword and scored per mention; the model was trained on whole-review severity.
- **Who writes reviews:** online reviewers skew toward strong experiences, and Drugs.com condition names were partly damaged in the original dataset (repaired where possible).
- Results come from one random seed.
""")
