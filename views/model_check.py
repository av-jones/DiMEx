import streamlit as st

from core.data import FIELDS, druglib_scores, druglib_test
from core.registry import MODEL_NAMES, MODELS
from core.ui import fake_data_banner, load_evaluation, load_predictor

reviews = druglib_test()
fake_data_banner()

st.caption("Druglib test split · held out during training")
st.title("Model check")
st.write("Open a review the model never saw. Each part gets its own score, next to the rating "
         "the patient gave.")

if "check_idx" not in st.session_state:
    st.session_state.check_idx = 0

c1, c2, c3, c4 = st.columns([2, 2, 1, 1], vertical_alignment="bottom")
labels = [f"{r['drug']} · {r['id']}" for r in reviews]
choice = c1.selectbox("Review", range(len(reviews)), format_func=lambda i: labels[i],
                      index=st.session_state.check_idx)
st.session_state.check_idx = choice
model = c2.selectbox("Model", MODEL_NAMES, key="check_model")
if c3.button("Previous", icon=":material/chevron_left:", width="stretch"):
    st.session_state.check_idx = (choice - 1) % len(reviews)
    st.rerun()
if c4.button("Next", icon=":material/chevron_right:", width="stretch"):
    st.session_state.check_idx = (choice + 1) % len(reviews)
    st.rerun()

review = reviews[st.session_state.check_idx]
scores = druglib_scores(load_predictor(model), review)

with st.container(border=True):
    st.subheader(f"{review['drug']} for {review['condition']}")
    for (key, section, label, kind, scale), pred, patient in zip(FIELDS, scores, review["ratings"]):
        st.divider()
        text_col, score_col = st.columns([3, 2], gap="large")
        text_col.caption(section.upper())
        text_col.markdown(f"##### {review[key]}")
        direction = " (higher is worse)" if kind == "side_effect" else ""
        score_col.markdown(f"**{label}** · 1–{scale}{direction}")
        m1, m2 = score_col.columns(2)
        diff = round(pred - patient, 1)
        m1.metric("Model", f"{pred:.1f}", delta=f"{diff:+.1f} vs patient", delta_color="off")
        m2.metric("Patient", str(patient))

with st.container(border=True):
    st.subheader("Results on the test split")
    st.caption("Lower is better. Satisfaction is on a 1–10 scale, so its errors run larger.")
    results = load_evaluation()
    results.insert(1, "Pretraining", results.Model.map(lambda m: MODELS[m]["domain"]))
    st.dataframe(results.style.highlight_between(subset=["Model"], left=model, right=model,
                                                 color="#DCEDE8"),
                 hide_index=True, width="stretch")
