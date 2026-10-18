import pandas as pd
import streamlit as st

from core.data import mentions
from core.labels import chip
from core.registry import MODEL_NAMES
from core.ui import fake_data_banner, highlight, load_predictions

preds = mentions(load_predictions())   # keyword-found aspects; whole-review scores are on other pages
fake_data_banner()

# Default: a high-rated review with a severe side effect, the most interesting case.
if "review_id" not in st.session_state:
    flagged = preds[(preds.label == "Severe") & (preds.rating >= 9)]
    st.session_state.review_id = int((flagged if len(flagged) else preds).review_id.iloc[0])

model = st.session_state.get("model", MODEL_NAMES[0])
rid = st.session_state.review_id
review = preds[(preds.review_id == rid) & (preds.model == model)]
first = review.iloc[0]

st.page_link("views/drug.py", label=f"{first.drug} for {first.condition.lower()}", icon=":material/arrow_back:")

main, side = st.columns([3, 1.3], gap="large")

with main:
    with st.container(border=True):
        st.caption(f"Drugs.com review · {first.condition} · Scored by {model}")
        st.metric("Patient's star rating", f"{first.rating}/10")
        text = first.text
        for span in review.span:
            text = highlight(text, span)
        st.markdown(f"#### {text}")

    with st.container(border=True):
        head, toggle = st.columns([2, 1.4], vertical_alignment="center")
        head.subheader("What the model found")
        show = toggle.toggle("Show valence and arousal scores")
        for r in review.itertuples():
            a, b, c = st.columns([3, 1.4, 1.2], vertical_alignment="center")
            a.markdown(f"**{r.aspect}**  \n_“{r.span}”_")
            if show:
                b.code(f"V {r.valence} · A {r.arousal}", language=None)
            c.markdown(chip(r.label))
        st.caption("Scores run from 1 to 9. Low valence is negative; high arousal is intense.")

with side:
    if (review.label == "Severe").any() and first.rating >= 9:
        st.error("**High rating, severe side effect.** The stars reflect effectiveness more "
                 "than tolerability for this patient.")

    with st.container(border=True):
        st.subheader("Model comparison")
        everyone = preds[preds.review_id == rid]
        table = (everyone.pivot_table(index="model", columns="aspect", values="label", aggfunc="first")
                 .reindex(MODEL_NAMES))
        st.dataframe(table, width="stretch")
        agree = table.apply(lambda col: col.nunique() == 1).all()
        if agree:
            st.success("All models agree on this review.")
        else:
            st.warning("Models disagree on at least one aspect. Treat this review as uncertain.")

    with st.container(border=True):
        st.subheader("Patient's own aspect ratings")
        st.write("Not available. Drugs.com reviews only have a star rating, so every label here "
                 "comes from the model. See Model check for Druglib reviews with patient ratings.")
