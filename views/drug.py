import html

import streamlit as st

from core.auth import greeting, viewer_name

from core.data import summarize
from core.labels import chip
from core.registry import APP_MODEL
from core.data import MIN_REVIEWS
from core.ui import card, highlight, load_pairs, pair_predictions, scroll_to
from core.viz import (EFFECT_GROUPS, MUTED, SIDE_GROUPS, breakdown, group_legend,
                      intensity_gauge, share_bars, split_tag, stacked, star_rating, stars_vs_model, va_map)

TILES = [("effectiveness", "Effectiveness", "How well it worked, from review text"),
         ("side_effect", "Side effects", "How bad, from review text (higher = worse)"),
         ("satisfaction", "Satisfaction", "The model's estimate from review text")]
NAMES = {kind: name for kind, name, _ in TILES}

model = APP_MODEL

# Pickers for thousands of drugs and conditions. Two ways in:
#   by condition (most visitors): pick a condition, then one of the drugs reviewed for it
#   by drug: pick any drug, then one of the conditions it's reviewed for
# Both menus are type-to-search, sorted by review count, and only list pairs with at least
# MIN_REVIEWS reviews (fewer is too thin to summarize).
ss = st.session_state
counts = load_pairs()                                         # drug, condition, n; most reviews first
COND_N = counts.groupby("condition").n.sum().sort_values(ascending=False)
DRUG_N = counts.groupby("drug").n.sum().sort_values(ascending=False)
PAIR_N = counts.set_index(["drug", "condition"]).n
POPULAR = list(COND_N.index[:6])
ss.setdefault("pick_mode", "Condition")
ss.setdefault("pick_condition", None)
ss.setdefault("pick_drug", None)


def _drugs_for(c):
    return list(counts[counts.condition == c].drug)            # most reviewed first


def _conditions_for(d):
    return list(counts[counts.drug == d].condition)


def _condition_changed():
    if ss.pick_condition and ss.pick_drug not in _drugs_for(ss.pick_condition):
        ss.pick_drug = _drugs_for(ss.pick_condition)[0]        # start on its most-reviewed drug


def _drug_changed():
    if ss.pick_drug and ss.pick_condition not in _conditions_for(ss.pick_drug):
        ss.pick_condition = _conditions_for(ss.pick_drug)[0]


def _quick_pick(c):
    ss.pick_mode, ss.pick_condition = "Condition", c
    _condition_changed()


def _reviews(n):
    return f"{n:,} review" + ("" if n == 1 else "s")


# Large, centered pickers on a full-width band under the header (styled by their keys in app.py)
with st.container(key="picker_band"):
    _, mid, _ = st.columns([1, 4, 1])
    with mid:
        name = viewer_name()
        st.markdown(f"<div class='band-greeting'>{html.escape(greeting() + (', ' + name if name else ''))}</div>"
                    "<h3 style='text-align:center;margin:0'>Find patient experiences for a drug</h3>",
                    unsafe_allow_html=True)
        with st.container(horizontal=True, horizontal_alignment="center", key="pick_mode_row"):
            st.segmented_control("Search by", ["Condition", "Drug"], key="pick_mode",
                                 label_visibility="collapsed", required=True)
        c1, c2 = st.columns(2, gap="medium")
        if ss.pick_mode == "Condition":
            c1.selectbox("Condition", list(COND_N.index), key="pick_condition", on_change=_condition_changed,
                         index=None, placeholder="Type a condition, e.g. migraine",
                         format_func=lambda c: f"{c} · {_reviews(COND_N[c])}")
            cond = ss.pick_condition
            c2.selectbox("Drug", _drugs_for(cond) if cond else [], key="pick_drug", on_change=_drug_changed,
                         index=None, disabled=not cond,
                         placeholder=f"{len(_drugs_for(cond))} drugs, most reviewed first" if cond
                         else "Pick a condition first",
                         format_func=lambda d: f"{d} · {_reviews(PAIR_N[d, cond])}")
        else:
            c1.selectbox("Drug", list(DRUG_N.index), key="pick_drug", on_change=_drug_changed,
                         index=None, placeholder="Type a drug name, e.g. sertraline",
                         format_func=lambda d: f"{d} · {_reviews(DRUG_N[d])}")
            drug_ = ss.pick_drug
            c2.selectbox("Condition", _conditions_for(drug_) if drug_ else [], key="pick_condition",
                         on_change=_condition_changed, index=None, disabled=not drug_,
                         placeholder="Pick a drug first" if not drug_ else "Conditions it's reviewed for",
                         format_func=lambda c: f"{c} · {_reviews(PAIR_N[drug_, c])}")
        with st.container(horizontal=True, horizontal_alignment="center", key="quick_row"):
            st.markdown("<span class='picker-note'>Popular:</span>", unsafe_allow_html=True)
            for c in POPULAR:
                st.button(c, key=f"quick_{c}", on_click=_quick_pick, args=(c,), type="tertiary")
        st.markdown(f"<div class='picker-note'>{len(COND_N):,} conditions · {len(DRUG_N):,} drugs · "
                    f"{counts.n.sum():,} reviews. Combinations with fewer than {MIN_REVIEWS} reviews "
                    "aren't listed.</div>", unsafe_allow_html=True)

def show(drug, condition):
    """The drug page for one drug-condition pair."""
    with st.spinner("Loading reviews..."):
        preds = pair_predictions(drug, condition)
    st.session_state.review_pair = (drug, condition)       # the review page opens reviews from this pair
    s = summarize(preds, drug, condition, model)
    st.title(drug)
    st.caption(f"For {condition.lower()} · {PAIR_N[drug, condition]:,} reviews · Source: Drugs.com · "
               "Click a box to see its details")

    # ---- the three metric boxes; clicking one opens its details below (selection kept in session state)
    selected = st.session_state.setdefault("metric", "side_effect")
    cols = st.columns(3)
    for col, (kind, name, sub) in zip(cols, TILES):
        is_on = kind == selected
        with col.container(border=True, key=f"metric_{kind}_{'on' if is_on else 'off'}", height="stretch"):
            # An invisible button covers the whole box (CSS in app.py), so the box itself is clickable
            if st.button(f"Show {name.lower()} details", key=f"select_{kind}"):
                st.session_state.metric = kind
                st.session_state.scroll_to_details = True
                st.rerun()
            t = s["tiles"].get(kind)
            if not t:
                st.markdown(f"**{name}**")
                st.caption("Needs predictions that include whole-review scores.")
                continue
            a, b = st.columns([1, 1.4], vertical_alignment="center")
            a.markdown(f"**{name}**")
            b.markdown(chip(t["label"]), unsafe_allow_html=True)
            st.markdown(f"<span style='font-family:IBM Plex Mono,monospace;font-size:30px'>{t['mean']:.1f}</span> "
                        f"<span style='color:{MUTED}'>/ {t['scale']} avg</span>"
                        + (split_tag(kind) if t["split"] else ""), unsafe_allow_html=True)
            if kind != "side_effect":       # stars read as "good"; side effects have no stars
                st.markdown(star_rating(t["mean"], t["scale"], kind), unsafe_allow_html=True)
            st.markdown(breakdown(t["breakdown"]), unsafe_allow_html=True)
            extra = f" Average stars: {s['avg_stars']:.1f}." if kind == "satisfaction" else ""
            st.caption(sub + ". Bars: share of reviews at each level." + extra)
            hint = "Showing details below" if is_on else "Click for details"
            st.markdown(f"<div class='metric-hint'>{hint} {'▾' if is_on else '›'}</div>", unsafe_allow_html=True)


    def quote_card(text, span, chip_label, meta, review_id, key):
        with card():
            st.markdown(highlight(text, span) if span else text.replace("$", r"\$"))
            left, right = st.columns([4, 1], vertical_alignment="center")
            left.markdown(f"{chip(chip_label) if chip_label else ''} {meta}", unsafe_allow_html=True)
            if right.button("Open review", key=key):
                st.session_state.review_id = int(review_id)
                st.switch_page("views/review.py")


    st.markdown(f"<h2 class='metric-details' style='margin:12px 0 0;scroll-margin-top:84px'>{NAMES[selected]}: details</h2>",
                unsafe_allow_html=True)
    if st.session_state.pop("scroll_to_details", False):
        scroll_to("metric-details")

    # ---------------------------------------------------------------- side effects
    if selected == "side_effect":
        main, side = st.columns([1.7, 1], gap="large")
        with main:
            if s["intensity"]:
                with card():
                    st.subheader("How intense are the side effects?")
                    gauge_col, split_col = st.columns([1, 1.7], gap="large", vertical_alignment="center")
                    gauge_col.markdown(intensity_gauge(s["dots"].a.mean(), "side_effect", size=210,
                                                       caption="Average intensity, calm to intense"),
                                       unsafe_allow_html=True)
                    with split_col:
                        st.caption("Share of reviews reporting side effects, by how intensely they describe them")
                        st.markdown(stacked(s["intensity"], height=18), unsafe_allow_html=True)
                        mcols = st.columns(3)
                        for mcol, band in zip(mcols, ("Mild", "Moderate", "Distressing")):
                            mcol.metric(band, f"{s['intensity'][band]:.0%}")

            with card():
                st.subheader("Side effects patients mention")
                st.markdown(group_legend(SIDE_GROUPS), unsafe_allow_html=True)
                for e in s["effects"]:          # already ordered: mostly mild first, then moderate, then distressing
                    n, share, bar, dist = st.columns([2, 0.8, 3, 1.1], vertical_alignment="center")
                    n.markdown(f"**{e['name']}**")
                    share.caption(f"{e['share']:.0%}")
                    bar.markdown(stacked(e["bands"], height=10), unsafe_allow_html=True)
                    d = e["bands"]["Distressing"]
                    dist.markdown(f"**{d:.0%} distr.**" if d >= 0.3 else f"{d:.0%} distr.")
                st.caption("Share of reviews mentioning each side effect, and how intensely they describe it. "
                           "Side effects are found by keyword and each mention is scored separately "
                           "(experimental: the model was trained on whole-review side-effect severity).")
        with side:
            if len(s["dots"]):
                with card(stretch=True):
                    st.subheader("Where side-effect reports land")
                    st.caption("Each dot is one review's side-effect score")
                    st.altair_chart(va_map(dots=s["dots"], height=300), width="stretch")
                    st.markdown(group_legend(SIDE_GROUPS), unsafe_allow_html=True)

        with card():
            st.subheader("What patients say about side effects")
            st.caption("Most severe first")
            for q in s["quotes"]:
                quote_card(q.text, q.span, q.label, f"{q.aspect} · Rated {q.rating}/10", q.review_id,
                           f"open-side-{q.review_id}-{q.aspect}")

    # ---------------------------------------------------------------- effectiveness
    elif selected == "effectiveness" and "eff_dots" in s:
        with card():
            st.markdown("<h2 class='big-head'>Where effectiveness reports land</h2>", unsafe_allow_html=True)
            st.markdown("<p class='big-note'>Each dot is one review. <b>Left to right</b>: how well the patient says "
                        "it worked. <b>Bottom to top</b>: how strongly they say it, from calm (“it helps a bit”) "
                        "to intense (“it changed my life”).</p>", unsafe_allow_html=True)
            st.altair_chart(va_map(dots=s["eff_dots"], height=440, groups=EFFECT_GROUPS, big=True), width="stretch")
            st.markdown(group_legend(EFFECT_GROUPS, size=16), unsafe_allow_html=True)

        with card():
            st.subheader("What patients say about how well it worked")
            for title, rows in [("Worked best", s["eff_best"]), ("Worked least", s["eff_worst"])]:
                st.markdown(f"<div class='group-head'>{title}</div>", unsafe_allow_html=True)
                for r in rows.itertuples():
                    quote_card(r.text, r.span, r.label, f"Rated {r.stars}/10", r.review_id,
                               f"open-eff-{title}-{r.review_id}")

    # ---------------------------------------------------------------- satisfaction
    elif selected == "satisfaction" and "sat_points" in s:
        left, right = st.columns([1.2, 1], gap="large")
        with left:
            with card(stretch=True):
                st.subheader("Stars vs. what they wrote")
                st.caption("Each dot is one review: the patient's star rating against the model's estimate "
                           "from the text. Dots on the dashed line agree.")
                st.altair_chart(stars_vs_model(s["sat_points"]), width="stretch")
                st.markdown(f"**{s['sat_agree']:.0%}** of reviews agree within 2 points.")
                if s["mismatch"]:
                    st.markdown(f"**{len(s['mismatch'])}** reviews give 9–10 stars while describing distressing "
                                "side effects: the stars reflect the benefit more than the experience.")
                    if st.button("See an example", key="mismatch_example"):
                        st.session_state.review_id = int(s["mismatch"][0])
                        st.switch_page("views/review.py")
        with right:
            with card(stretch=True):
                st.subheader("What drives satisfaction")
                st.caption("Share of patients who are satisfied (7–10), by their other experiences")
                st.markdown("**By side effects**")
                st.markdown(share_bars(s["sat_by_side"]), unsafe_allow_html=True)
                st.markdown("**By how well it worked**")
                st.markdown(share_bars(s["sat_by_effect"]), unsafe_allow_html=True)
                st.caption("Compare the gaps: a bigger gap means that experience matters more to "
                           "how satisfied patients are with this drug.")

        with card():
            st.subheader("What patients say overall")
            for title, rows in [("Most satisfied", s["sat_best"]), ("Least satisfied", s["sat_worst"])]:
                st.markdown(f"<div class='group-head'>{title}</div>", unsafe_allow_html=True)
                for r in rows.itertuples():
                    quote_card(r.text, None, r.label, f"Rated {r.stars}/10", r.review_id,
                               f"open-sat-{title}-{r.review_id}")
    else:
        st.caption("Details need predictions that include whole-review scores.")


drug, condition = ss.pick_drug, ss.pick_condition
if not (drug and condition):
    with card():
        st.subheader("Pick a condition to begin")
        st.write("Choose what the medication is for, then a drug reviewed for it. Or switch to "
                 "**Drug** to start from a drug you already know. You'll see how well it worked, how "
                 "bad the side effects were and how satisfied patients sound, from their own words.")
else:
    show(drug, condition)
