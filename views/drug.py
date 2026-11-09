import streamlit as st

from core.data import summarize
from core.labels import chip
from core.registry import APP_MODEL
from core.ui import card, highlight, load_predictions
from core.viz import (BAND_COLORS, EFFECT_GROUPS, MUTED, SIDE_GROUPS, breakdown, group_legend,
                      intensity_gauge, share_bars, split_tag, stacked, star_rating, stars_vs_model, va_map)

TILES = [("effectiveness", "Effectiveness", "How well it worked, from review text"),
         ("side_effect", "Side effects", "How bad, from review text (higher = worse)"),
         ("satisfaction", "Satisfaction", "The model's estimate from review text")]
NAMES = {kind: name for kind, name, _ in TILES}

preds = load_predictions()
model = APP_MODEL

# Both menus list everything. Picking one that doesn't fit the other switches the other to a match:
# a condition this drug isn't reviewed for switches the drug, and the other way around.
pairs = preds[["drug", "condition"]].drop_duplicates()
ALL_DRUGS, ALL_CONDITIONS = sorted(pairs.drug.unique()), sorted(pairs.condition.unique())
if "pick_drug" not in st.session_state:
    st.session_state.pick_drug = ALL_DRUGS[0]
    st.session_state.pick_condition = sorted(pairs[pairs.drug == ALL_DRUGS[0]].condition)[0]


def _drug_changed():
    ok = pairs[pairs.drug == st.session_state.pick_drug].condition
    if st.session_state.pick_condition not in set(ok):
        st.session_state.pick_condition = sorted(ok)[0]


def _condition_changed():
    ok = pairs[pairs.condition == st.session_state.pick_condition].drug
    if st.session_state.pick_drug not in set(ok):
        st.session_state.pick_drug = sorted(ok)[0]


# Large, centered pickers on a full-width band under the header (styled by their keys in app.py)
with st.container(key="picker_band"):
    _, mid, _ = st.columns([1, 4, 1])
    with mid:
        st.markdown("<h3 style='text-align:center;margin:0'>Find patient experiences for a drug</h3>",
                    unsafe_allow_html=True)
        c1, c2 = st.columns(2, gap="medium")
        drug = c1.selectbox("Drug name", ALL_DRUGS, key="pick_drug", on_change=_drug_changed)
        condition = c2.selectbox("Condition", ALL_CONDITIONS, key="pick_condition", on_change=_condition_changed)
        others = sorted(pairs[pairs.drug == drug].condition)
        if len(others) > 1:
            st.markdown(f"<div class='picker-note'>{drug} is also reviewed for: "
                        + ", ".join(c for c in others if c != condition) + "</div>", unsafe_allow_html=True)

s = summarize(preds, drug, condition, model)
st.title(drug)
st.caption(f"For {condition.lower()} · {s['n']:,} reviews analyzed · Source: Drugs.com · "
           "Click a box to see its details")

# ---- the three metric boxes; clicking one opens its details below (selection kept in session state)
selected = st.session_state.setdefault("metric", "side_effect")
cols = st.columns(3)
for col, (kind, name, sub) in zip(cols, TILES):
    is_on = kind == selected
    with col.container(border=True, key=f"metric_{kind}_{'on' if is_on else 'off'}"):
        # An invisible button covers the whole box (CSS in app.py), so the box itself is clickable
        if st.button(f"Show {name.lower()} details", key=f"select_{kind}"):
            st.session_state.metric = kind
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
        st.markdown(star_rating(t["mean"], t["scale"], kind), unsafe_allow_html=True)
        st.markdown(breakdown(t["breakdown"]), unsafe_allow_html=True)
        extra = f" Average stars: {s['avg_stars']:.1f}." if kind == "satisfaction" else ""
        st.caption(sub + ". Bars: share of reviews at each level." + extra)
        hint = "Showing details below" if is_on else "Click for details"
        st.markdown(f"<div class='metric-hint'>{hint} {'▾' if is_on else '›'}</div>", unsafe_allow_html=True)


def quote_card(text, span, chip_label, meta, review_id, key):
    with card():
        st.markdown(highlight(text, span) if span else text.replace("$", r"\$"))
        st.markdown(f"{chip(chip_label) if chip_label else ''} {meta}", unsafe_allow_html=True)
        if st.button("Open review", key=key):
            st.session_state.review_id = int(review_id)
            st.switch_page("views/review.py")


st.markdown(f"<h2 style='margin:12px 0 0'>{NAMES[selected]}: details</h2>", unsafe_allow_html=True)

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
            headings = {"Mild": "Mostly mild", "Moderate": "Mostly moderate", "Distressing": "Mostly distressing"}
            group = None
            for e in s["effects"]:
                if e["group"] != group:
                    group = e["group"]
                    st.markdown(f"<div class='group-head'><span style='background:{BAND_COLORS[group]}'></span>"
                                f"{headings[group]}</div>", unsafe_allow_html=True)
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
            with card():
                st.subheader("Where side-effect reports land")
                st.caption("Each dot is one review's side-effect score")
                st.altair_chart(va_map(dots=s["dots"], height=300), width="stretch")
                st.markdown(group_legend(SIDE_GROUPS), unsafe_allow_html=True)

    with card():
        st.subheader("What patients say about side effects")
        st.caption("Most severe first")
        qcols = st.columns(len(s["quotes"]) or 1)
        for qcol, q in zip(qcols, s["quotes"]):
            with qcol:
                quote_card(q.text, q.span, q.label, f"{q.aspect} · Rated {q.rating}/10", q.review_id,
                           f"open-side-{q.review_id}-{q.aspect}")

# ---------------------------------------------------------------- effectiveness
elif selected == "effectiveness" and "eff_dots" in s:
    left, right = st.columns([1, 1.25], gap="large")
    with left:
        with card():
            st.subheader("How strongly patients describe the benefit")
            st.markdown(intensity_gauge(s["eff_intensity"], "effectiveness", size=230,
                                        caption="Average intensity, from calm (“it helps a bit”) "
                                                "to strong (“it changed my life”)"),
                        unsafe_allow_html=True)
            st.caption("Intensity is how strongly a review expresses the effect, not whether the drug "
                       "worked; the score and bars above show that.")
    with right:
        with card():
            st.subheader("Where effectiveness reports land")
            st.caption("Each dot is one review's effectiveness score")
            st.altair_chart(va_map(dots=s["eff_dots"], height=300, groups=EFFECT_GROUPS), width="stretch")
            st.markdown(group_legend(EFFECT_GROUPS), unsafe_allow_html=True)

    with card():
        st.subheader("What patients say about how well it worked")
        best_col, worst_col = st.columns(2, gap="large")
        for col_, title, rows in [(best_col, "Worked best", s["eff_best"]), (worst_col, "Worked least", s["eff_worst"])]:
            with col_:
                st.markdown(f"<div class='group-head'>{title}</div>", unsafe_allow_html=True)
                for r in rows.itertuples():
                    quote_card(r.text, r.span, r.label, f"Rated {r.stars}/10", r.review_id,
                               f"open-eff-{title}-{r.review_id}")

# ---------------------------------------------------------------- satisfaction
elif selected == "satisfaction" and "sat_points" in s:
    left, right = st.columns([1.2, 1], gap="large")
    with left:
        with card():
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
        with card():
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
        best_col, worst_col = st.columns(2, gap="large")
        for col_, title, rows in [(best_col, "Most satisfied", s["sat_best"]),
                                  (worst_col, "Least satisfied", s["sat_worst"])]:
            with col_:
                st.markdown(f"<div class='group-head'>{title}</div>", unsafe_allow_html=True)
                for r in rows.itertuples():
                    quote_card(r.text, None, r.label, f"Rated {r.stars}/10", r.review_id,
                               f"open-sat-{title}-{r.review_id}")
else:
    st.caption("Details need predictions that include whole-review scores.")
