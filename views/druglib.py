"""Druglib: each review's own patient ratings next to DiMEx's predictions (the original viewer design)."""
import html

import streamlit as st

from core.druglib import ASPECTS, LEVEL_NAMES, gap, metrics
from core.labels import chip
from core.ui import card, load_druglib, scroll_to
from core.viz import COMPARE_KEY, MUTED, compare_bar

PAGE = 8          # reviews shown per "Show more"

df, source = load_druglib()

st.title("Predictions")
st.caption("On Druglib.com, patients rated their own experience: how well the drug worked, how bad the side "
           "effects were and how satisfied they were. Here are their ratings next to DiMEx's, which come only "
           "from what they wrote.")
if source == "placeholder":
    st.info("Placeholder predictions: these are real Druglib reviews and ratings, but the DiMEx numbers come "
            "from the stand-in scorer until the trained model is connected.")
elif source == "examples":
    st.info("Showing a few example reviews: the Druglib test set couldn't be loaded here.")

# ---------------------------------------------------------------- side by side: how close | browse
m = metrics(df).rename(columns={"Within 1 point": "within1"})
df = df.assign(gap=gap(df))
drug_n = df.drug.value_counts()
left, right = st.columns(2, gap="medium")

# Both boxes are navy (styled by their keys in app.py)
with left, st.container(border=True, key="dl_panel_close", height="stretch"):
    st.subheader("How close DiMEx gets")
    st.caption(f"Druglib test set · {len(df):,} reviews. Average gap = mean absolute error (MAE): how many "
               "rating points DiMEx is off from the patient, on average. Lower is better.")
    for r in m.itertuples():                       # one row per aspect: name, gap, detail
        a, b = st.columns([1, 1.25], vertical_alignment="center")
        a.markdown(f"**{r.Aspect}**  \n<span class='dl-muted' style='font-size:13px'>scale {r.Scale}</span>",
                   unsafe_allow_html=True)
        b.markdown(f"<span style='font-family:IBM Plex Mono,monospace;font-size:26px'>{r.MAE:.2f}</span> "
                   f"<span class='dl-muted'>average gap</span><br>"
                   f"<span class='dl-muted' style='font-size:13px'>{r.within1:.0%} within 1 point · "
                   f"kappa {r.Kappa:.2f}</span>", unsafe_allow_html=True)

with right, st.container(border=True, key="dl_panel_browse", height="stretch"):
    st.subheader("Browse reviews")
    f1, f2 = st.columns(2)
    drug = f1.selectbox("Drug", list(drug_n.index), index=None, placeholder=f"All {len(drug_n):,} drugs",
                        format_func=lambda d: f"{d} · {drug_n[d]}", key="dl_drug")
    sub = df if drug is None else df[df.drug == drug]
    cond_n = sub.condition.value_counts()
    condition = f2.selectbox("Condition", list(cond_n.index), index=None,
                             placeholder=f"All {len(cond_n):,} conditions",
                             format_func=lambda c: f"{c} · {cond_n[c]}", key="dl_condition")
    if condition is not None:
        sub = sub[sub.condition == condition]
    order = st.selectbox("Order", ["Biggest disagreement", "Closest match", "Drug name"], key="dl_order")
    sub = (sub.sort_values("gap", ascending=False) if order == "Biggest disagreement"
           else sub.sort_values("gap") if order == "Closest match" else sub.sort_values(["drug", "review_id"]))
    st.markdown(f"<div class='dl-muted' style='font-size:13px'>{len(sub):,} reviews · {COMPARE_KEY}</div>",
                unsafe_allow_html=True)

key = (drug, condition, order)
if st.session_state.get("dl_key") != key:          # new filter: start from the top
    st.session_state.dl_key, st.session_state.dl_shown = key, PAGE
shown = st.session_state.dl_shown

# Once both a drug and a condition are picked, glide down to their reviews (once per new pair)
st.markdown("<div class='dl-results' style='scroll-margin-top:84px'></div>", unsafe_allow_html=True)
if drug and condition and st.session_state.get("dl_scrolled") != (drug, condition):
    st.session_state.dl_scrolled = (drug, condition)
    scroll_to("dl-results")


def gap_label(g):
    return "Close match" if g < 0.15 else "Some disagreement" if g < 0.3 else "Big disagreement"


for r in sub.head(shown).itertuples():
    with card():
        head, tag = st.columns([3, 1.2], vertical_alignment="center")
        head.markdown(f"**{html.escape(r.drug)}** <span style='color:{MUTED}'>· {html.escape(r.condition)} "
                      f"· review #{r.review_id}</span>", unsafe_allow_html=True)
        tag.markdown(f"<div style='text-align:right'>{chip(gap_label(r.gap))}</div>", unsafe_allow_html=True)
        # One full-width section per part of the review: what they wrote, then patient vs. DiMEx
        for i, (k, text_col, name, _, scale) in enumerate(ASPECTS):
            gold, pred, text = getattr(r, f"gold_{k}"), getattr(r, f"pred_{k}"), getattr(r, text_col)
            both = gold == gold and pred == pred                       # both present (not NaN)
            level = LEVEL_NAMES.get(k, {}).get(int(gold)) if gold == gold else None
            scores = (f"<span class='dl-scores'>Patient <b style='color:#1B2430'>{gold:g}</b>"
                      f"{' (' + level + ')' if level else ''} · DiMEx <b style='color:#1B2430'>{pred:.1f}</b>"
                      f" · <span title='Absolute error: how far DiMEx is from the patient, in rating points'>"
                      f"off by <b style='color:#1B2430'>{abs(pred - gold):.1f}</b></span></span>") if both else ""
            quote = (f"<div class='dl-quote'>“{html.escape(text)}”</div>" if text
                     else f"<div class='dl-quote' style='color:{MUTED}'>No text for this part.</div>")
            # Left two thirds: what they wrote. Right third: patient vs. DiMEx on the scale.
            st.markdown(f"<div class='dl-part{' dl-first' if i == 0 else ''}'>"
                        f"<div><div class='dl-name'>{name}</div>{quote}</div>"
                        f"<div class='dl-compare'>{scores}"
                        + (compare_bar(float(gold), float(pred), scale) if both else "")
                        + "</div></div>", unsafe_allow_html=True)

if shown < len(sub):
    if st.button(f"Show more ({len(sub) - shown:,} left)", width="stretch"):
        st.session_state.dl_shown += PAGE
        st.rerun()
elif len(sub) == 0:
    st.caption("No reviews match these filters.")
