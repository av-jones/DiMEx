"""Druglib: each review's own patient ratings next to DiMEx's predictions (the original viewer design)."""
import html

import streamlit as st

from core.druglib import ASPECTS, LEVEL_NAMES, gap, metrics
from core.labels import chip
from core.ui import card, load_druglib
from core.viz import COMPARE_KEY, MUTED, compare_bar

PAGE = 8          # reviews shown per "Show more"

df, source = load_druglib()

st.title("Druglib")
st.caption("On Druglib.com, patients rated their own experience: how well the drug worked, how bad the side "
           "effects were and how satisfied they were. Here are their ratings next to DiMEx's, which come only "
           "from what they wrote.")
if source == "placeholder":
    st.info("Placeholder predictions: these are real Druglib reviews and ratings, but the DiMEx numbers come "
            "from the stand-in scorer until the trained model is connected.")
elif source == "examples":
    st.info("Showing a few example reviews: the Druglib test set couldn't be loaded here.")

# ---------------------------------------------------------------- how close, overall
m = metrics(df).rename(columns={"Within 1 point": "within1"})
with card():
    st.subheader("How close DiMEx gets")
    st.caption(f"Druglib test set · {len(df):,} reviews. Average gap = mean absolute error (MAE) on the "
               "patient's own scale; lower is better.")
    cols = st.columns(len(m))
    for col, r in zip(cols, m.itertuples()):
        with col:
            st.markdown(f"**{r.Aspect}** <span style='color:{MUTED}'>· scale {r.Scale}</span>",
                        unsafe_allow_html=True)
            st.markdown(f"<span style='font-family:IBM Plex Mono,monospace;font-size:30px'>{r.MAE:.2f}</span> "
                        f"<span style='color:{MUTED}'>average gap</span>", unsafe_allow_html=True)
            st.caption(f"{r.within1:.0%} within 1 point · agreement (kappa) {r.Kappa:.2f}")

# ---------------------------------------------------------------- browse
df = df.assign(gap=gap(df))
drug_n = df.drug.value_counts()
with card():
    st.subheader("Browse reviews")
    f1, f2, f3 = st.columns([1.2, 1.2, 1])
    drug = f1.selectbox("Drug", list(drug_n.index), index=None, placeholder=f"All {len(drug_n):,} drugs",
                        format_func=lambda d: f"{d} · {drug_n[d]}", key="dl_drug")
    sub = df if drug is None else df[df.drug == drug]
    cond_n = sub.condition.value_counts()
    condition = f2.selectbox("Condition", list(cond_n.index), index=None,
                             placeholder=f"All {len(cond_n):,} conditions",
                             format_func=lambda c: f"{c} · {cond_n[c]}", key="dl_condition")
    if condition is not None:
        sub = sub[sub.condition == condition]
    order = f3.selectbox("Order", ["Biggest disagreement", "Closest match", "Drug name"], key="dl_order")
    sub = (sub.sort_values("gap", ascending=False) if order == "Biggest disagreement"
           else sub.sort_values("gap") if order == "Closest match" else sub.sort_values(["drug", "review_id"]))
    st.markdown(f"<div style='font-size:13px;color:{MUTED}'>{len(sub):,} reviews · {COMPARE_KEY}</div>",
                unsafe_allow_html=True)

key = (drug, condition, order)
if st.session_state.get("dl_key") != key:          # new filter: start from the top
    st.session_state.dl_key, st.session_state.dl_shown = key, PAGE
shown = st.session_state.dl_shown


def gap_label(g):
    return "Close match" if g < 0.15 else "Some disagreement" if g < 0.3 else "Big disagreement"


for r in sub.head(shown).itertuples():
    with card():
        head, tag = st.columns([3, 1.2], vertical_alignment="center")
        head.markdown(f"**{html.escape(r.drug)}** <span style='color:{MUTED}'>· {html.escape(r.condition)} "
                      f"· review #{r.review_id}</span>", unsafe_allow_html=True)
        tag.markdown(f"<div style='text-align:right'>{chip(gap_label(r.gap))}</div>", unsafe_allow_html=True)
        cols = st.columns(3, gap="large")
        for col, (k, text_col, name, _, scale) in zip(cols, ASPECTS):
            gold, pred, text = getattr(r, f"gold_{k}"), getattr(r, f"pred_{k}"), getattr(r, text_col)
            with col:
                st.markdown(f"<div class='group-head' style='margin-top:0'>{name}</div>", unsafe_allow_html=True)
                if text:
                    short = text if len(text) <= 260 else text[:257].rsplit(" ", 1)[0] + "…"
                    st.markdown(f"<div style='font-size:15px;line-height:1.5;min-height:3em'>“{html.escape(short)}”"
                                "</div>", unsafe_allow_html=True)
                else:
                    st.caption("No text for this part.")
                if gold == gold and pred == pred:            # both present (not NaN)
                    level = LEVEL_NAMES.get(k, {}).get(int(gold))
                    st.markdown(compare_bar(float(gold), float(pred), scale), unsafe_allow_html=True)
                    st.markdown(f"<div style='font-size:13px'>Patient <b>{gold:g}</b>"
                                f"{' (' + level + ')' if level else ''} · DiMEx <b>{pred:.1f}</b></div>",
                                unsafe_allow_html=True)

if shown < len(sub):
    if st.button(f"Show more ({len(sub) - shown:,} left)", width="stretch"):
        st.session_state.dl_shown += PAGE
        st.rerun()
elif len(sub) == 0:
    st.caption("No reviews match these filters.")
