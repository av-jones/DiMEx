"""DiMEx: run with `streamlit run app.py`."""
import streamlit as st

st.set_page_config(page_title="DiMEx", layout="wide")

NAVY, NAVY_HOVER, BODY, BAND = "#0B2E59", "#16407A", "#F3F5F8", "#3A5F8F"

# Wave pattern for the picker band: three faint sine-like curves, tiled horizontally (1200px wide)
def _waves():
    import math
    from urllib.parse import quote
    paths = []
    for k, (y0, amp, op) in enumerate([(70, 22, 0.10), (115, 30, 0.08), (160, 18, 0.06)]):
        pts = " ".join(f"{x},{y0 + amp * math.sin(2 * math.pi * x / 600 + k):.1f}" for x in range(0, 1201, 20))
        paths.append(f'<polyline points="{pts}" fill="none" stroke="white" stroke-opacity="{op}" stroke-width="2"/>')
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="220">{"".join(paths)}</svg>'
    return "data:image/svg+xml," + quote(svg)


WAVES = _waves()

# Layout styling. Streamlit has no settings for these, so this is CSS on Streamlit's own page
# elements (their data-testid attributes) plus the "st-key-card_*" class that core.ui.card() gives
# every card. The nav keeps its full width so its "more" overflow menu still works on narrow screens.
st.markdown(
    f"""
    <style>
    /* Header: navy band with the DiMEx name on the left and the page links centered */
    [data-testid="stHeader"] {{
        background: rgba(8, 38, 96, 0.88); height: 64px;         /* deep blue, slightly see-through */
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
        background-color: {BAND}; width: 100vw !important; max-width: 100vw !important;
        margin: -24px 0 8px calc(50% - 50vw);
        padding: 28px max(32px, calc(50vw - 640px)) 32px;
        position: relative; overflow: hidden;
        /* Faint, slowly drifting waves (a nod to the valence-arousal curves) plus a soft moving glow */
        background-image: url("{WAVES}"),
            radial-gradient(ellipse 45% 70% at 20% 30%, rgba(255, 255, 255, 0.10), transparent 70%),
            radial-gradient(ellipse 40% 60% at 80% 75%, rgba(140, 185, 255, 0.14), transparent 70%);
        background-size: 1200px 220px, 200% 200%, 200% 200%;
        background-repeat: repeat-x, no-repeat, no-repeat;
        animation: dimexDrift 40s linear infinite, dimexGlow 18s ease-in-out infinite alternate;
    }}
    @keyframes dimexDrift {{ from {{ background-position: 0 center, 0% 0%, 100% 100%; }}
                             to   {{ background-position: 1200px center, 0% 0%, 100% 100%; }} }}
    @keyframes dimexGlow  {{ from {{ background-position: 0 center, 0% 0%, 100% 100%; }}
                             to   {{ background-position: 600px center, 100% 60%, 0% 40%; }} }}
    @media (prefers-reduced-motion: reduce) {{ .st-key-picker_band {{ animation: none; }} }}
    .picker-note {{ text-align: center; color: rgba(255, 255, 255, 0.85); font-size: 13px; margin-top: -4px; }}
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
    /* Drug page metric boxes: the whole box is clickable through an invisible button laid over it */
    [class*="st-key-metric_"] {{ background: #FFFFFF; position: relative; transition: box-shadow .15s, border-color .15s; }}
    [class*="st-key-metric_"]:hover {{ border-color: #8FA3C0 !important; box-shadow: 0 4px 14px rgba(11, 46, 89, 0.10); }}
    [class*="st-key-metric_"][class*="_on"] {{ border: 2px solid {NAVY} !important; box-shadow: 0 4px 16px rgba(11, 46, 89, 0.14); }}
    [class*="st-key-select_"] {{
        position: absolute !important; inset: 0; z-index: 3; margin: 0 !important;
        width: 100% !important; height: 100% !important;
    }}
    [class*="st-key-select_"] [data-testid="stButton"], [class*="st-key-select_"] [data-testid="stButton"] > * {{
        width: 100% !important; height: 100% !important;
    }}
    [class*="st-key-select_"] button {{ width: 100% !important; height: 100% !important; opacity: 0; cursor: pointer; }}
    [class*="st-key-metric_"]:has(button:focus-visible) {{ outline: 3px solid #5C8FD6; outline-offset: 2px; }}
    .metric-hint {{ font-size: 12px; font-weight: 600; color: #2F6FD0; text-align: right; }}
    .group-head {{ margin-top: 10px; font-size: 13px; font-weight: 600; color: #5B6472; text-transform: uppercase;
                   letter-spacing: .04em; display: flex; align-items: center; gap: 8px; }}
    .group-head span {{ width: 10px; height: 10px; border-radius: 3px; display: inline-block; }}

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
