"""Model card: what the app's model is, how it was trained and checked, and where it falls short."""
import streamlit as st

from core.registry import APP_MODEL, MODELS, is_real
from core.druglib import metrics
from core.ui import card, load_druglib

st.title("Model card")
st.caption("What the DiMEx model is, how it was trained and tested, and what it shouldn't be used for")

with card():
    st.subheader("Authors")
    st.markdown("**Tejaswi Vemuri, Athlene V. Jones, Joseph O'Berry**  \n"
                "University of North Florida, Jacksonville, Florida, USA")

if not is_real(APP_MODEL):
    st.info("This copy of the app is running on placeholder scores while the trained checkpoint is connected. "
            "The Drugs.com results below are from the training runs.")

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
""")

# Druglib test split: computed from the same predictions the Druglib page shows
dl, dl_source = load_druglib()
with card():
    st.subheader("Druglib test set: error on the patient's own scales")
    if dl_source == "trained":
        st.caption(f"{len(dl):,} reviews, each field scored by {APP_MODEL}. MAE and RMSE are in rating points "
                   "(lower is better); 3-class accuracy and kappa use Gräßer et al.'s (2018) classes.")
    else:
        st.caption("Placeholder numbers from the stand-in scorer"
                   + (" on a few example reviews" if dl_source == "examples" else "")
                   + ". They update automatically once the trained model's Druglib predictions are connected.")
    table = metrics(dl)
    st.dataframe(table, hide_index=True, width="stretch",
                 column_config={"MAE": st.column_config.NumberColumn(format="%.2f"),
                                "RMSE": st.column_config.NumberColumn(format="%.2f"),
                                "Within 1 point": st.column_config.NumberColumn(format="percent"),
                                "3-class accuracy": st.column_config.NumberColumn(format="percent"),
                                "Kappa": st.column_config.NumberColumn(format="%.2f")})
    st.page_link("views/druglib.py", label="See every review next to its prediction", icon=":material/arrow_forward:")

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
