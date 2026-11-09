"""DiMEx: run with `streamlit run app.py`."""
import streamlit as st

st.set_page_config(page_title="DiMEx", layout="wide")

NAVY, NAVY_HOVER, BODY = "#0B2E59", "#16407A", "#F3F5F8"

# Layout styling. Streamlit has no settings for these, so this is CSS on Streamlit's own page
# elements (their data-testid attributes) plus the "st-key-card_*" class that core.ui.card() gives
# every card. The nav keeps its full width so its "more" overflow menu still works on narrow screens.
st.markdown(
    f"""
    <style>
    /* Header: navy band with the DiMEx name on the left and the page links centered */
    [data-testid="stHeader"] {{ background: {NAVY}; height: 64px; }}
    [data-testid="stHeader"]::before {{
        content: "DiMEx"; position: absolute; left: 32px; top: 50%; transform: translateY(-50%);
        color: #FFFFFF; font-size: 1.4rem; font-weight: 700; letter-spacing: 0.02em; z-index: 2;
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
    @media (max-width: 760px) {{ [data-testid="stHeader"]::before {{ display: none; }} }}

    /* Body: very light grey, with white cards */
    [data-testid="stMainBlockContainer"] {{ padding-top: 96px; padding-bottom: 0 !important; }}
    [class*="st-key-card_"] {{ background: #FFFFFF; }}
    /* Form fields are white too, so give them an outline to stay visible inside white cards */
    [data-testid="stTextAreaRootElement"], [data-testid="stTextInputRootElement"],
    [data-testid="stNumberInputContainer"], [data-testid="stSelectbox"] div:has(> input) {{
        border-color: #C9D1DC !important;
    }}
    [data-testid="stMain"] {{ overflow-x: hidden; }}

    /* Footer: full-width navy band at the end of every page */
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
        st.Page("views/model_check.py", title="Model check", icon=":material/fact_check:"),
    ],
    position="top",
)
pages.run()

st.markdown(
    """
    <div class="dimex-footer">
      <div><strong>DiMEx</strong> · Medication-Experience Viewer</div>
      <div>Patient-reported experiences, not medical advice.</div>
      <div>Data: Druglib.com and Drugs.com (UCI ML Repository) · SemEval-2026 Task 3 (DimABSA)</div>
    </div>
    """,
    unsafe_allow_html=True,
)
