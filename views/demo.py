import pandas as pd
import streamlit as st

from core.explain import intensity_band, key_sentences, summary_sentence, why
from core.labels import chip
from core.registry import MODEL_NAMES, is_real
from core.ui import fake_data_banner, load_predictor
from core.viz import ASPECT_COLORS, MUTED, intensity_meter, score_bar, va_map

EXAMPLES = {
    "Works, but rough start": "Zoloft fixed my anxiety within a month, which honestly felt like a miracle. "
                              "But the nausea was constant for the first six weeks and I could barely eat. "
                              "Glad I stuck with it, but I wish my doctor had warned me.",
    "Mild nausea": "Some mild nausea the first week, then it faded. "
                   "My mood lifted and I can focus again.",
    "Did not help": "No change at all after three months. "
                    "Severe insomnia, I was wide awake every night.",
}
SHORT = {"effectiveness": "Effectiveness", "side_effect": "Side effects", "satisfaction": "Satisfaction"}

# Trained models first, so the default choice is a real one when available.
MODEL_ORDER = sorted(MODEL_NAMES, key=lambda m: not is_real(m))

st.title("Try a review")
st.write("Paste a drug review. DiMEx scores how well the drug worked, how bad the side effects were and "
         "how satisfied the patient sounds, and how *intense* each of those feelings is.")

if "demo_text" not in st.session_state:
    st.session_state.demo_text = ""

left, right = st.columns([1, 1.6], gap="large")

with left:
    with st.container(border=True):
        st.caption("Try an example")
        for label, text in EXAMPLES.items():
            if st.button(label, width="stretch"):
                st.session_state.demo_text = text
        text = st.text_area("Review text", key="demo_text", height=220,
                            placeholder="Describe how the medication worked and any side effects")
        stars = st.number_input("Patient's star rating, if any (1–10)", min_value=1, max_value=10,
                                value=None, step=1, placeholder="Optional")
        model = st.selectbox("Model", MODEL_ORDER, key="demo_model",
                             format_func=lambda m: m if is_real(m) else f"{m} (not trained yet)")
        run = st.button("Analyze review", type="primary", width="stretch")

with right:
    if run and not text.strip():
        st.error("Enter a review first.")
    elif not run:
        with st.container(border=True):
            st.subheader("Results appear here")
            st.caption("You'll get a one-sentence summary, a score and an intensity reading for each "
                       "aspect, and a map of where the review lands on valence and arousal.")
    else:
        fake_data_banner(model)
        with st.spinner(f"Scoring with {model}..."):
            predictor = load_predictor(model)
            results = predictor.score_review(text)
            keys = key_sentences(predictor, text)

        with st.container(border=True):
            st.caption("IN ONE SENTENCE")
            st.markdown(f"#### {summary_sentence(results)}")

        with st.container(border=True):
            head, note = st.columns([1, 2], vertical_alignment="bottom")
            head.subheader("By aspect")
            note.caption("Score = direction (Druglib's scale) · Intensity = how strongly it's felt")
            for r in results:
                kind = r["kind"]
                band = intensity_band(r["arousal"], kind)
                with st.container(border=True):
                    a, b = st.columns([2, 1.2], vertical_alignment="center")
                    a.markdown(f"**{SHORT[kind]}**")
                    b.markdown(chip(r["label"]))
                    s_col, i_col = st.columns(2, gap="medium")
                    with s_col:
                        st.caption("Score")
                        st.markdown(f"<span style='font-family:IBM Plex Mono,monospace;font-size:26px'>"
                                    f"{r['rating']:.1f}</span> <span style='color:{MUTED}'>/ {r['scale']}</span>",
                                    unsafe_allow_html=True)
                        st.markdown(score_bar(r["rating"], r["scale"], ASPECT_COLORS[kind]), unsafe_allow_html=True)
                    with i_col:
                        st.caption("Intensity")
                        st.markdown(f"<span style='font-size:20px;font-weight:600'>{band}</span> "
                                    f"<span style='font-family:IBM Plex Mono,monospace;font-size:13px;color:{MUTED}'>"
                                    f"arousal {r['arousal']:.1f}/9</span>", unsafe_allow_html=True)
                        st.markdown(intensity_meter(r["arousal"]), unsafe_allow_html=True)
                    line = f"**Why:** {why(kind, r['valence'], r['arousal'])}"
                    if r["aspect"] in keys:
                        line += f"  \nMost influential sentence: _“{keys[r['aspect']][0]}”_"
                    st.markdown(line)

        with st.container(border=True):
            chart, explain = st.columns([1.3, 1], gap="large", vertical_alignment="center")
            pts = pd.DataFrame([{"v": r["valence"], "a": r["arousal"], "label": SHORT[r["kind"]],
                                 "color": ASPECT_COLORS[r["kind"]]} for r in results])
            chart.altair_chart(va_map(points=pts), width="stretch")
            with explain:
                st.subheader("How to read this map")
                st.write("**Left to right** is valence: how negative or positive the patient sounds.")
                st.write("**Bottom to top** is arousal: how calm or intense.")
                st.caption("“Mild nausea that faded” sits low on the left; “constant vomiting, I couldn't "
                           "work” sits high on the left. Star ratings can't tell these apart.")

        if stars is not None:
            sat = next(r for r in results if r["kind"] == "satisfaction")
            with st.container(border=True):
                st.subheader("Stars vs. model")
                c1, c2 = st.columns(2)
                c1.metric("Patient's stars", f"{stars} / 10")
                c2.metric("Predicted satisfaction", f"{sat['rating']:.1f} / 10")
                gap = abs(sat["rating"] - stars)
                if gap >= 3:
                    st.warning(f"The model and the stars differ by {gap:.1f} points. Read the review "
                               "closely: the text and the rating tell different stories.")
                else:
                    st.success("The model's estimate is close to the patient's own rating.")

        st.caption("Intensity is experimental: the model learned it from restaurant and laptop reviews "
                   "(SemEval) and it hasn't been checked against patient-rated intensity yet. "
                   "The most influential sentence is the one whose removal changes that score the most; "
                   "it shows what the score is sensitive to, not the model's exact reasoning.")
