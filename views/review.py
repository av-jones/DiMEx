import streamlit as st

from core.data import mentions
from core.labels import chip
from core.ui import card, highlight, load_predictions

preds = mentions(load_predictions())   # keyword-found aspects; whole-review scores are on other pages

# Default: a high-rated review with a severe side effect, the most interesting case.
if "review_id" not in st.session_state:
    flagged = preds[(preds.label == "Severe") & (preds.rating >= 9)]
    st.session_state.review_id = int((flagged if len(flagged) else preds).review_id.iloc[0])

rid = st.session_state.review_id
review = preds[preds.review_id == rid]
first = review.iloc[0]

st.page_link("views/drug.py", label=f"{first.drug} for {first.condition.lower()}", icon=":material/arrow_back:")

main, side = st.columns([3, 1.3], gap="large")

with main:
    with card():
        st.caption(f"Drugs.com review · {first.condition}")
        st.metric("Patient's star rating", f"{first.rating}/10")
        text = first.text
        for span in review.span:
            text = highlight(text, span)
        st.markdown(f"#### {text}")

    with card():
        head, toggle = st.columns([2, 1.4], vertical_alignment="center")
        head.subheader("What the model found")
        show = toggle.toggle("Show valence and arousal scores")
        for r in review.itertuples():
            a, b, c = st.columns([3, 1.4, 1.2], vertical_alignment="center")
            a.markdown(f"**{r.aspect}**  \n_“{r.span}”_")
            if show:
                b.code(f"V {r.valence} · A {r.arousal}", language=None)
            c.markdown(chip(r.label), unsafe_allow_html=True)
        st.caption("Scores run from 1 to 9. Low valence is negative; high arousal is intense.")

with side:
    if (review.label == "Severe").any() and first.rating >= 9:
        st.info("**High rating, severe side effect.** The stars reflect effectiveness more "
                 "than tolerability for this patient.")

    with card():
        st.subheader("Patient's own aspect ratings")
        st.write("Not available. Drugs.com reviews only have a star rating, so every label here "
                 "comes from the model.")
