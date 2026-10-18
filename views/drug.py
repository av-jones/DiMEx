import streamlit as st

from core.data import summarize
from core.labels import chip
from core.registry import MODEL_NAMES, is_real
from core.ui import fake_data_banner, highlight, load_predictions
from core.viz import MUTED, legend, stacked, va_map

TILES = [("effectiveness", "Effectiveness", "How well it worked, from review text"),
         ("side_effect", "Side effects", "How bad, from review text (higher = worse)"),
         ("satisfaction", "Satisfaction", "The model's estimate from review text")]
MODEL_ORDER = sorted(MODEL_NAMES, key=lambda m: not is_real(m))

preds = load_predictions()
fake_data_banner()

c1, c2, c3 = st.columns(3)
drug = c1.selectbox("Drug", sorted(preds.drug.unique()))
condition = c2.selectbox("Condition", sorted(preds[preds.drug == drug].condition.unique()))
model = c3.selectbox("Model", [m for m in MODEL_ORDER if m in set(preds.model)], key="model")

s = summarize(preds, drug, condition, model)
st.caption("PATIENT-REPORTED EXPERIENCES")
st.title(drug)
st.caption(f"For {condition.lower()} · {s['n']:,} reviews analyzed · Source: Drugs.com")

# ---- three summary tiles
cols = st.columns(3)
for col, (kind, name, sub) in zip(cols, TILES):
    with col.container(border=True):
        t = s["tiles"].get(kind)
        if not t:
            st.markdown(f"**{name}**")
            st.caption("Needs predictions that include whole-review scores.")
            continue
        a, b = st.columns([1, 1.4], vertical_alignment="center")
        a.markdown(f"**{name}**")
        b.markdown(chip(t["label"]))
        st.markdown(f"<span style='font-family:IBM Plex Mono,monospace;font-size:30px'>{t['mean']:.1f}</span> "
                    f"<span style='color:{MUTED}'>/ {t['scale']} avg</span>", unsafe_allow_html=True)
        extra = f" Average stars: {s['avg_stars']:.1f}." if kind == "satisfaction" else ""
        st.caption(sub + "." + extra)

main, side = st.columns([1.7, 1], gap="large")

with main:
    if s["intensity"]:
        with st.container(border=True):
            st.subheader("How intense are the side effects?")
            st.caption("Share of reviews reporting side effects, by how intensely they describe them")
            st.markdown(stacked(s["intensity"], height=18), unsafe_allow_html=True)
            cols = st.columns(3)
            for col, band in zip(cols, ("Mild", "Moderate", "Distressing")):
                col.metric(band, f"{s['intensity'][band]:.0%}")

    with st.container(border=True):
        st.subheader("Side effects patients mention")
        st.markdown(legend(), unsafe_allow_html=True)
        for e in s["effects"]:
            n, share, bar, dist = st.columns([2, 0.8, 3, 1.1], vertical_alignment="center")
            n.markdown(f"**{e['name']}**")
            share.caption(f"{e['share']:.0%}")
            bar.markdown(stacked(e["bands"], height=10), unsafe_allow_html=True)
            d = e["bands"]["Distressing"]
            dist.markdown(f"**{d:.0%} distr.**" if d >= 0.3 else f"{d:.0%} distr.")
        st.caption("Share of reviews mentioning each side effect, and how intensely they describe it. "
                   "Side effects are found by keyword and each mention is scored separately "
                   "(experimental: the model was trained on whole-review side-effect severity).")

    with st.container(border=True):
        st.subheader("Same severity, different experience")
        others = sorted(d for d in preds[preds.condition == condition].drug.unique() if d != drug)
        if not others:
            st.caption(f"No other drug for {condition.lower()} to compare with.")
        else:
            other = st.selectbox("Compare with", others, key="compare")
            o = summarize(preds, other, condition, model)
            for name, summ in [(drug, s), (other, o)]:
                if not summ or not summ["intensity"]:
                    continue
                a, b, c = st.columns([1.2, 3, 1.2], vertical_alignment="center")
                a.markdown(f"**{name}**")
                b.markdown(stacked(summ["intensity"]), unsafe_allow_html=True)
                t = summ["tiles"].get("side_effect")
                c.caption(f"{t['mean']:.1f} / 5 avg" if t else "")
            st.caption("Two drugs can have the same average severity but a different mix: more "
                       "distressing reports for one, more moderate ones for the other. A single score hides this.")

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
    if len(s["dots"]):
        with st.container(border=True):
            st.subheader("Where side-effect reports land")
            st.caption("Each dot is one review's side-effect score")
            st.altair_chart(va_map(dots=s["dots"], height=300), width="stretch")
            st.markdown(legend(), unsafe_allow_html=True)

    if s["mismatch"]:
        with st.container(border=True):
            st.markdown("**Stars don't tell the whole story**")
            st.write(f"{len(s['mismatch'])} reviews give 9–10 stars while describing distressing side effects.")
            if st.button("See an example"):
                st.session_state.review_id = int(s["mismatch"][0])
                st.switch_page("views/review.py")

    with st.container(border=True):
        st.subheader("How to read this page")
        st.markdown("- **Scores** use Druglib's patient rating scales (1–5, 1–10).\n"
                    "- **Intensity** is how strongly the patient expresses it, from calm to intense.\n"
                    "- Personal experiences, not medical advice.")
        st.caption("Intensity is experimental until it's checked against patient-rated intensity.")
