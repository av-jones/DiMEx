import streamlit as st

from core.labels import chip
from core.registry import MODEL_NAMES, is_real
from core.ui import fake_data_banner, load_predictor

EXAMPLES = {
    "Works, but numb": "Panic attacks finally stopped after a month. "
                       "The downside is I feel nothing at all, completely numb most days.",
    "Mild nausea": "Some mild nausea the first week, then it faded. "
                   "My mood lifted and I can focus again.",
    "Did not help": "No change at all after three months. "
                    "Severe insomnia, I was wide awake every night.",
}

# Trained models first, so the default choice is a real one when available.
MODEL_ORDER = sorted(MODEL_NAMES, key=lambda m: not is_real(m))

st.title("Try a review")
st.write("Paste a real drug review, or try an example. The selected model scores how well the "
         "drug worked, how bad the side effects were, and how satisfied the patient sounds.")

if "demo_text" not in st.session_state:
    st.session_state.demo_text = ""

left, right = st.columns(2, gap="large")

with left:
    with st.container(border=True):
        st.caption("Try an example")
        cols = st.columns(len(EXAMPLES))
        for col, (label, text) in zip(cols, EXAMPLES.items()):
            if col.button(label, width="stretch"):
                st.session_state.demo_text = text
        text = st.text_area("Review text", key="demo_text", height=220,
                            placeholder="Describe how the medication worked and any side effects")
        model = st.selectbox("Model", MODEL_ORDER, key="demo_model",
                             format_func=lambda m: m if is_real(m) else f"{m} (not trained yet)")
        run = st.button("Analyze review", type="primary")

with right:
    with st.container(border=True):
        if run and not text.strip():
            st.error("Enter a review first.")
        elif run:
            fake_data_banner(model)
            with st.spinner(f"Scoring with {model}..."):
                predictor = load_predictor(model)
                overall = predictor.score_review(text)
                mentions = [r for r in predictor.predict(text) if r["kind"] == "side_effect"]

            head, toggle = st.columns([2, 1.5], vertical_alignment="center")
            head.subheader("Results")
            show_va = toggle.toggle("Show valence and arousal")
            for r in overall:
                a, b, c = st.columns([2.2, 1.2, 2], vertical_alignment="center")
                a.markdown(f"**{r['aspect']}**")
                b.markdown(f"{r['rating']:.1f} / {r['scale']}")
                c.markdown(chip(r["label"]))
                if show_va:
                    st.caption(f"Valence {r['valence']} · arousal {r['arousal']} (1–9)")
            st.caption("Scores use Druglib's patient rating scales: effectiveness and side "
                       "effects 1–5 (higher side-effect scores are worse), satisfaction 1–10.")

            if mentions:
                st.divider()
                st.markdown("**Side effects mentioned** · experimental")
                for r in mentions:
                    a, c = st.columns([3.4, 2], vertical_alignment="center")
                    a.markdown(f"{r['aspect']}  \n_“{r['span']}”_")
                    c.markdown(chip(r["label"]))
                st.caption("Side effects are found with a keyword list; the model scores each "
                           "one. The model wasn't trained on individual symptoms, so treat these "
                           "as rough.")
        else:
            st.subheader("Results appear here")
            st.caption("Analyze a review to see its effectiveness, side-effect severity and "
                       "satisfaction scores.")
