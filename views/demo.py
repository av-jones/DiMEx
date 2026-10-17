import streamlit as st

from core.labels import chip
from core.registry import MODEL_NAMES
from core.ui import fake_data_banner, load_predictor

EXAMPLES = {
    "Works, but numb": "Panic attacks finally stopped after a month. "
                       "The downside is I feel nothing at all, completely numb most days.",
    "Mild nausea": "Some mild nausea the first week, then it faded. "
                   "My mood lifted and I can focus again.",
    "Did not help": "No change at all after three months. "
                    "Severe insomnia, I was wide awake every night.",
}

fake_data_banner()
st.title("Try a review")
st.write("Write or paste a drug review. The selected model scores effectiveness and each "
         "side effect it finds, live.")

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
        text = st.text_area("Review text", key="demo_text", height=200,
                            placeholder="Describe how the medication worked and any side effects")
        model = st.selectbox("Model", MODEL_NAMES, key="demo_model")
        run = st.button("Analyze review", type="primary")

with right:
    with st.container(border=True):
        if run and not text.strip():
            st.error("Enter a review first.")
        elif run:
            with st.spinner(f"Scoring with {model}..."):
                results = load_predictor(model).predict(text)
            st.subheader("Results")
            st.caption(f"Scored by {model}")
            for r in results:
                a, b, c = st.columns([3, 1.4, 1.2], vertical_alignment="center")
                a.markdown(f"**{r['aspect']}**  \n_“{r['span']}”_")
                b.code(f"V {r['valence']} · A {r['arousal']}", language=None)
                c.markdown(chip(r["label"]))
            st.caption("This page runs the model live. The drug pages use predictions "
                       "computed ahead of time.")
        else:
            st.subheader("Results appear here")
            st.caption("Analyze a review to see effectiveness and side-effect severity, "
                       "with the sentence behind each label.")

