"""DiMEx: run with `streamlit run app.py`."""
import streamlit as st

st.set_page_config(page_title="DiMEx", layout="wide")

NAVY, NAVY_HOVER, BODY, BAND = "#0B2E59", "#16407A", "#F3F5F8", "#3A5F8F"

# Layout styling. Streamlit has no settings for these, so this is CSS on Streamlit's own page
# elements (their data-testid attributes) plus the "st-key-card_*" class that core.ui.card() gives
# every card. The nav keeps its full width so its "more" overflow menu still works on narrow screens.
st.markdown(
    f"""
    <style>
    /* Header: navy band with the DiMEx name on the left and the page links centered */
    [data-testid="stHeader"] {{
        background: rgba(11, 46, 89, 0.82); height: 64px;        /* navy, slightly see-through */
        backdrop-filter: blur(12px) saturate(140%); -webkit-backdrop-filter: blur(12px) saturate(140%);
    }}
    [data-testid="stHeader"]::before {{
        content: "DiMEx"; position: absolute; left: 32px; top: 50%; transform: translateY(-50%);
        color: #FFFFFF; font-size: 1.4rem; font-weight: 700; letter-spacing: 0.02em; z-index: 2;
    }}
    [data-testid="stHeader"]::after {{
        content: "Dimensional Medication Experience Viewer"; position: absolute; left: 116px; top: 50%;
        transform: translateY(-50%); padding-left: 14px; border-left: 1px solid rgba(255, 255, 255, 0.35);
        color: rgba(255, 255, 255, 0.78); font-size: 0.9rem; letter-spacing: 0.01em; z-index: 2;
    }}
    [data-testid="stToolbar"] {{ height: 64px; }}
    [data-testid="stTopNav"] {{ flex: 1 1 auto; justify-content: center; }}
    [data-testid="stTopNavLink"] {{ color: rgba(255, 255, 255, 0.85) !important; background: transparent !important; }}
    [data-testid="stTopNavLink"] * {{ color: inherit !important; }}
    [data-testid="stTopNavLink"]:hover {{ color: #FFFFFF !important; background: {NAVY_HOVER} !important; }}
    [data-testid="stTopNavLink"][aria-current="page"] {{ color: #FFFFFF !important; background: rgba(255, 255, 255, 0.16) !important; }}
    [data-testid="stToolbarActions"] *, [data-testid="stAppDeployButton"] *, [data-testid="stMainMenu"] * {{
        color: #FFFFFF !important;
    }}
    @media (max-width: 1180px) {{ [data-testid="stHeader"]::after {{ display: none; }} }}
    @media (max-width: 760px) {{ [data-testid="stHeader"]::before {{ display: none; }} }}

    /* Drug page: a full-width lighter-navy band right under the header holds the pickers */
    .st-key-picker_band {{
        background: {BAND}; width: 100vw !important; max-width: 100vw !important;
        margin: -24px 0 8px calc(50% - 50vw);
        padding: 28px max(32px, calc(50vw - 640px)) 32px;
    }}
    .st-key-picker_band h3, .st-key-picker_band [data-testid="stWidgetLabel"] p {{ color: #FFFFFF !important; }}

    /* Drug page: large, centered drug and condition pickers */
    .st-key-pick_drug [data-testid="stWidgetLabel"] p, .st-key-pick_condition [data-testid="stWidgetLabel"] p {{
        font-size: 1.05rem; font-weight: 600;
    }}
    .st-key-pick_drug [data-testid="stSelectbox"] div:has(> input),
    .st-key-pick_condition [data-testid="stSelectbox"] div:has(> input) {{
        min-height: 56px; border-color: #FFFFFF !important;
    }}
    .st-key-pick_drug [data-testid="stSelectbox"] div:has(> input) *,
    .st-key-pick_condition [data-testid="stSelectbox"] div:has(> input) * {{ font-size: 1.15rem; }}

    /* Body: very light grey, with white cards */
    [data-testid="stMainBlockContainer"] {{ padding-top: 72px; padding-bottom: 0 !important; }}
    [class*="st-key-card_"] {{ background: #FFFFFF; }}
    /* Form fields are white too, so give them an outline to stay visible inside white cards */
    [data-testid="stTextAreaRootElement"], [data-testid="stTextInputRootElement"],
    [data-testid="stNumberInputContainer"], [data-testid="stSelectbox"] div:has(> input) {{
        border-color: #C9D1DC !important;
    }}
    [data-testid="stMain"] {{ overflow-x: hidden; }}

    /* Footer: full-width navy band at the end of every page */
    [data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] .dimex-footer) {{
        min-height: calc(100vh - 96px);      /* short pages: push the footer to the bottom */
    }}
    [data-testid="stElementContainer"]:has(.dimex-footer) {{ margin-top: auto; }}
    .dimex-footer {{
        background: {NAVY}; color: rgba(255, 255, 255, 0.85); font-size: 0.85rem; line-height: 1.6;
        width: 100vw; margin: 56px 0 0 calc(50% - 50vw);
        padding: 28px max(32px, calc(50vw - 640px));
        display: flex; flex-wrap: wrap; gap: 8px 32px; justify-content: space-between;
    }}
    .dimex-footer strong {{ color: #FFFFFF; font-size: 1rem; }}
    </style>
    """,
    unsafe_allow_html=True,
)

st.session_state["_card_n"] = 0        # card keys restart at card_0 on every run (core.ui.card)

pages = st.navigation(
    [
        st.Page("views/drug.py", title="Drugs", icon=":material/medication:", default=True),
        st.Page("views/review.py", title="Review detail", icon=":material/article:"),
        st.Page("views/demo.py", title="Try a review", icon=":material/edit_note:"),
    ],
    position="top",
)
pages.run()

st.markdown(
    """
    <div class="dimex-footer">
      <div><strong>DiMEx</strong> · Dimensional Medication Experience Viewer</div>
      <div>Patient-reported experiences, not medical advice.</div>
      <div>Data: Druglib.com and Drugs.com (UCI ML Repository) · SemEval-2026 Task 3 (DimABSA)</div>
    </div>
    """,
    unsafe_allow_html=True,
)
