import streamlit as st

from core.data import summarize
from core.labels import chip
from core.registry import MODEL_NAMES
from core.ui import fake_data_banner, highlight, load_predictions

preds = load_predictions()
fake_data_banner()

c1, c2, c3 = st.columns([2, 2, 2])
drug = c1.selectbox("Drug", sorted(preds.drug.unique()))
condition = c2.selectbox("Condition", sorted(preds[preds.drug == drug].condition.unique()))
model = c3.selectbox("Model", MODEL_NAMES, key="model")

s = summarize(preds, drug, condition, model)
st.title(drug)
st.caption(f"For {condition.lower()} · {s['n']:,} reviews analyzed · Source: Drugs.com")

main, side = st.columns([3, 1.3], gap="large")

with main:
    with st.container(border=True):
        st.subheader("Does it work?")
        a, b, c = st.columns(3)
        a.metric("Worked well", f"{s['worked']:.0%}")
        b.metric("Some benefit", f"{s['some']:.0%}")
        c.metric("Didn't help", f"{s['none']:.0%}")

    with st.container(border=True):
        st.subheader("Side effects patients mention")
        st.caption("Share of reviews · typical severity")
        for e in s["effects"]:
            n, bar, sev = st.columns([2, 3, 1.4], vertical_alignment="center")
            n.write(f"**{e['name']}**")
            bar.progress(e["share"], text=f"{e['share']:.0%} of reviews")
            sev.markdown(chip(e["severity"]))

    with st.container(border=True):
        st.subheader("What patients say")
        for q in s["quotes"]:
            with st.container(border=True):
                st.markdown(highlight(q.text, q.span))
                left, right = st.columns([3, 1], vertical_alignment="center")
                left.markdown(f"{chip(q.label)} {q.aspect} · Rated {q.rating}/10")
                if right.button("Open review", key=f"open-{q.review_id}-{q.aspect}"):
                    st.session_state.review_id = int(q.review_id)
                    st.switch_page("views/review.py")

with side:
    with st.container(border=True):
        st.subheader("At a glance")
        top = s["effects"][0]["name"] if s["effects"] else "None reported"
        st.write(f"**Most mentioned side effect:** {top}")
        st.write(f"**Reviews analyzed:** {s['n']:,}")
    if s["mismatch"]:
        st.info(f"**Stars don't tell the whole story.** {s['mismatch']} reviews give 9–10 stars "
                "while describing a severe side effect.")
    with st.container(border=True):
        st.subheader("How to read this")
        st.write("A language model reads each review and scores how positive and how intense the "
                 "patient sounds about effectiveness and each side effect. Those scores become the "
                 "labels shown here.")
        st.caption("Personal experiences, not medical advice.")
