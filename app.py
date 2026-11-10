"""DiMEx: run with `streamlit run app.py`."""
import streamlit as st

st.set_page_config(page_title="DiMEx", layout="wide")

NAVY, BODY, BAND = "#0B2E59", "#F3F5F8", "#3A5F8F"

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


def _logo_mark():
    from urllib.parse import quote
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">'
           '<path d="M16 2v28M2 16h28" stroke="#FFFFFF" stroke-opacity=".6" stroke-width="2.2" stroke-linecap="round"/>'
           '<circle cx="24" cy="8" r="6" fill="#8FB4F0"/>'
           '<circle cx="8.5" cy="23.5" r="3.6" fill="#FFFFFF" fill-opacity=".85"/></svg>')
    return "data:image/svg+xml," + quote(svg)


LOGO = _logo_mark()

# Layout styling. Streamlit has no settings for these, so this is CSS on Streamlit's own page
# elements (their data-testid attributes) plus the "st-key-card_*" class that core.ui.card() gives
# every card. The nav keeps its full width so its "more" overflow menu still works on narrow screens.
st.markdown(
    f"""
    <style>
    /* Thin outlined icons for the phone tab bar: a 5 KB cut of Google's Material Symbols Outlined
       (Apache 2.0, static/dimex-icons.LICENSE) with only the four icons used, served from static/ */
    @font-face {{ font-family: "DiMEx Icons"; src: url("app/static/dimex-icons.woff2") format("woff2");
                  font-weight: 100 700; font-display: block; }}
    /* Header: navy band with the DiMEx name on the left and the page links centered */
    [data-testid="stHeader"] {{
        background: rgba(8, 38, 96, 0.88); height: 64px;         /* deep blue, slightly see-through */
        backdrop-filter: blur(12px) saturate(140%); -webkit-backdrop-filter: blur(12px) saturate(140%);
    }}
    /* Logo: a small valence-arousal map mark plus the name in Space Grotesk Bold (OFL, static/dimex-logo.*) */
    @font-face {{ font-family: "DiMEx Logo"; src: url("app/static/dimex-logo.woff2") format("woff2");
                  font-weight: 700; font-display: block; }}
    [data-testid="stHeader"]::before {{
        content: "DiMEx"; position: absolute; left: 28px; top: 50%; transform: translateY(-50%);
        padding-left: 40px; line-height: 30px;
        background: url("{LOGO}") left center / 30px 30px no-repeat;
        color: #FFFFFF; font-family: "DiMEx Logo", sans-serif; font-size: 1.55rem; font-weight: 700;
        letter-spacing: -0.02em; z-index: 2;
    }}
    [data-testid="stHeader"]::after {{
        content: "Dimensional Medication Experience Explorer"; position: absolute; left: 160px; top: 50%;
        transform: translateY(-50%); padding-left: 14px; border-left: 1px solid rgba(255, 255, 255, 0.35);
        color: rgba(255, 255, 255, 0.78); font-size: 0.9rem; letter-spacing: 0.01em; z-index: 2;
    }}
    [data-testid="stToolbar"] {{ height: 64px; }}
    /* Tabs start right after the name and tagline, so they never run into it */
    [data-testid="stTopNav"] {{ flex: 1 1 auto; justify-content: flex-start; padding-left: 484px; }}
    @media (max-width: 1180px) {{ [data-testid="stTopNav"] {{ padding-left: 150px; }} }}
    /* Tabs: full-height blocks; hovering shows a 5px white bar along the bottom of the block */
    [data-testid="stTopNavLink"] {{
        color: rgba(255, 255, 255, 0.85) !important; background: transparent !important;
        position: relative; height: 64px; padding: 0 20px !important; border-radius: 0 !important;
        display: flex; align-items: center;
    }}
    [data-testid="stTopNavLink"] * {{ color: inherit !important; font-size: 17px !important; font-weight: 500; }}
    [data-testid="stTopNavLink"]::after {{
        content: ""; position: absolute; left: 0; right: 0; bottom: 0; height: 5px;
        background: #FFFFFF; transform: scaleX(0); transition: transform .15s ease-out;
    }}
    [data-testid="stTopNavLink"]:hover {{ color: #FFFFFF !important; }}
    [data-testid="stTopNavLink"]:hover::after {{ transform: scaleX(1); }}
    [data-testid="stTopNavLink"][aria-current="page"] {{ color: #FFFFFF !important; background: rgba(255, 255, 255, 0.12) !important; }}
    [data-testid="stTopNavLinkContainer"] {{ height: 64px; }}
    [data-testid="stToolbarActions"] *, [data-testid="stAppDeployButton"] *, [data-testid="stMainMenu"] * {{
        color: #FFFFFF !important;
    }}
    @media (max-width: 1180px) {{ [data-testid="stHeader"]::after {{ display: none; }} }}

    /* Bottom tab bar: hidden on wider screens */
    .st-key-bottom_nav {{ display: none !important; }}
    @media (max-width: 760px) {{
        /* Header keeps the DiMEx name; the menu buttons go (the bottom bar does navigation) */
        [data-testid="stHeader"]::before {{ left: 20px; }}
        [data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"], [data-testid="stExpandSidebarButton"],
        [data-testid="stMainMenu"], [data-testid="stAppDeployButton"], [data-testid="stTopNav"] {{ display: none !important; }}
        .st-key-bottom_nav {{
            display: flex !important; position: fixed; left: 0; right: 0; bottom: 0; z-index: 999990;
            width: 100vw !important; margin: 0 !important; gap: 0 !important;
            padding: 11px 4px calc(6px + env(safe-area-inset-bottom));
            background: rgba(255, 255, 255, 0.94); backdrop-filter: blur(12px) saturate(140%);
            -webkit-backdrop-filter: blur(12px) saturate(140%); border-top: 1px solid #DDE2E9;
            box-shadow: 0 -4px 16px rgba(11, 46, 89, 0.06);
        }}
        .st-key-bottom_nav {{ flex-wrap: nowrap !important; }}
        .st-key-bottom_nav > [data-testid="stLayoutWrapper"] {{ flex: 1 1 0 !important; min-width: 0 !important; }}
        [class*="st-key-bnav_"], [class*="st-key-bnav_"] [data-testid="stElementContainer"],
        [class*="st-key-bnav_"] [data-testid="stPageLink"] {{ width: 100% !important; }}
        [class*="st-key-bnav_"] a {{
            display: flex !important; flex-direction: column; align-items: center; justify-content: center; gap: 2px;
            padding: 6px 2px !important; border-radius: 10px; background: transparent !important;
            color: #5B6472 !important; text-decoration: none;
        }}
        [class*="st-key-bnav_"] a * {{ color: inherit !important; font-size: 12px !important; margin: 0 !important;
                                      white-space: nowrap; }}
        /* Big, thin, outlined icons (Material Symbols: no fill, light stroke weight) */
        [class*="st-key-bnav_"] a [data-testid="stIconMaterial"] {{
            font-family: "DiMEx Icons", "Material Symbols Rounded" !important; font-feature-settings: "liga" 1;
            font-size: 34px !important; line-height: 1 !important;
            font-variation-settings: 'FILL' 0, 'wght' 200, 'GRAD' 0, 'opsz' 40 !important; }}
        [class*="st-key-bnav_"][class*="_on"] a {{ color: {NAVY} !important; background: #EAF0F8 !important; }}
        [class*="st-key-bnav_"][class*="_on"] a p {{ font-weight: 600 !important; }}
        /* Room under the content so the bar never covers the footer */
        .dimex-footer {{ padding-bottom: calc(96px + env(safe-area-inset-bottom)); }}
    }}

    /* Drug page: a full-width lighter-navy band right under the header holds the pickers */
    .st-key-picker_band {{
        background-color: {BAND}; width: 100vw !important; max-width: 100vw !important;
        margin: -24px 0 8px calc(50% - 50vw);
        padding: 28px max(32px, calc(50vw - 640px)) 32px;
        position: relative; overflow: hidden; isolation: isolate;
        /* Solid navy with faint waves drifting over it; a soft band of light sweeps across slowly
           (::before, behind the content) */
        background-image: url("{WAVES}");
        background-size: 1200px 220px;
        background-repeat: repeat-x;
        animation: dimexDrift 40s linear infinite;
    }}
    .st-key-picker_band::before {{
        content: ""; position: absolute; inset: 0; z-index: -1; pointer-events: none;
        /* very soft, wide band whose edges fade out gradually, so it reads as a shift in light, not a stripe */
        background: linear-gradient(100deg, rgba(255, 255, 255, 0) 0%, rgba(255, 255, 255, 0.015) 20%,
                    rgba(255, 255, 255, 0.04) 40%, rgba(255, 255, 255, 0.055) 50%, rgba(255, 255, 255, 0.04) 60%,
                    rgba(255, 255, 255, 0.015) 80%, rgba(255, 255, 255, 0) 100%) no-repeat;
        background-size: 70% 100%; background-position: -150% 0;
        animation: dimexSweep 24s ease-in-out infinite;
    }}
    @keyframes dimexDrift {{ from {{ background-position: 0 center; }} to {{ background-position: 1200px center; }} }}
    @keyframes dimexSweep {{ 0% {{ background-position: -150% 0; }} 75%, 100% {{ background-position: 250% 0; }} }}
    @media (prefers-reduced-motion: reduce) {{ .st-key-picker_band::before {{ animation: none; opacity: 0; }} }}
    @media (prefers-reduced-motion: reduce) {{ .st-key-picker_band {{ animation: none; }} }}
    .band-greeting {{ text-align: center; color: #FFD98A; font-size: 1.05rem; font-weight: 600;
                      letter-spacing: .01em; margin-bottom: 2px; }}
    /* Charts sit on white cards, so draw them on white (Streamlit paints them the page grey) */
    [data-testid="stVegaLiteChart"] svg.marks {{ background-color: #FFFFFF !important; }}
    /* Druglib page: each part of a review is a full-width section */
    /* Druglib page: the two summary boxes are navy, with white text (menus stay white) */
    [class*="st-key-dl_panel_"] {{ background: {NAVY}; border-color: {NAVY} !important; }}
    [class*="st-key-dl_panel_"] h3, [class*="st-key-dl_panel_"] p, [class*="st-key-dl_panel_"] strong,
    [class*="st-key-dl_panel_"] [data-testid="stWidgetLabel"] p, [class*="st-key-dl_panel_"] .dl-muted *:not(svg *) {{
        color: #FFFFFF !important; }}
    [class*="st-key-dl_panel_"] [data-testid="stCaptionContainer"] p,
    [class*="st-key-dl_panel_"] .dl-muted {{ color: rgba(255, 255, 255, 0.75) !important; }}
    [class*="st-key-dl_panel_"] [data-testid="stSelectbox"] div:has(> input) {{ border-color: #FFFFFF !important; }}
    [class*="st-key-dl_panel_"] [data-testid="stCaptionContainer"] p {{ color: rgba(255, 255, 255, 0.8) !important; }}
    /* 'How close DiMEx gets' grid: aspect rows, three metric columns of thin labeled bars */
    .acc-grid {{ display: grid; grid-template-columns: minmax(96px, 1.1fr) repeat(3, minmax(0, 1fr));
                 gap: 16px 18px; align-items: center; margin: 4px 0 14px; }}
    .acc-h {{ font-size: 13px; font-weight: 600;
              color: rgba(255, 255, 255, 0.75); align-self: end; padding-bottom: 2px;
              border-bottom: 1px solid rgba(255, 255, 255, 0.18); }}
    .acc-grid .acc-h:first-child {{ border-bottom-color: rgba(255, 255, 255, 0.18); }}
    .acc-name {{ color: #FFFFFF; font-weight: 600; font-size: 15px; line-height: 1.25; }}
    .acc-name span {{ display: block; font-weight: 400; font-size: 12px; color: rgba(255, 255, 255, 0.65); }}
    .acc-val {{ font-family: "IBM Plex Mono", monospace; font-size: 22px; color: #FFFFFF; cursor: default; }}
    @media (max-width: 760px) {{ .acc-grid {{ grid-template-columns: 1fr; gap: 6px; }} .acc-h {{ display: none; }} }}
    .serious-note {{ background: #FDF1F1; border: 1px solid #E8A9A9; color: #8A1F1F; border-radius: 8px;
                     padding: 10px 14px; margin: 4px 0 10px; font-size: 15px; }}
    [class*="st-key-serious_"] {{ background: #FDF1F1; border: 2px solid #C83E3E !important;
                                         box-shadow: 0 0 0 3px rgba(200, 62, 62, 0.10); }}
    [class*="st-key-serious_"] .dl-part {{ border-top-color: rgba(200, 62, 62, 0.18); }}
    .serious-flag {{ display: inline-block; padding: 2px 10px; border-radius: 999px; font-size: 0.85em; font-weight: 600;
                     color: #8A1F1F; background: #FBE3E3; border: 1px solid #E8A9A9; margin-right: 6px; white-space: nowrap; }}
    .aspect-term {{ padding: 0 3px; border-radius: 4px; cursor: help; }}
    [class*="st-key-dl_panel_"] .dl-muted .aspect-term {{ color: #1B2430 !important; }}
    .dl-part {{ display: grid; grid-template-columns: 2fr 1fr; gap: 8px 40px; align-items: center;
                padding: 14px 0 10px; border-top: 1px solid #E3E8EF; }}
    .dl-compare {{ min-width: 0; }}
    @media (max-width: 760px) {{ .dl-part {{ grid-template-columns: 1fr; }} }}
    .dl-part.dl-first {{ border-top: none; padding-top: 4px; }}
    .dl-name {{ font-size: 13px; font-weight: 600; color: #5B6472; text-transform: uppercase; letter-spacing: .04em; }}
    .dl-scores {{ font-size: 14px; color: #5B6472; }}
    .dl-scores b {{ color: #1B2430; }}
    .dl-quote {{ font-size: 1.05rem; line-height: 1.6; margin: 6px 0 2px; color: #1B2430; }}
    .big-head {{ font-size: 1.85rem !important; margin: 0 0 4px !important; padding: 0 !important; }}
    .big-note, .big-note * {{ font-size: 1.2rem !important; line-height: 1.6 !important; color: #3A4352; }}
    .big-note {{ margin: 0 0 8px !important; }}
    .band-head [data-testid="stHeaderActionElements"] {{ display: none !important; }}   /* keeps it centered */
    .band-head {{ padding-bottom: 0 !important; }}
    @media (max-width: 760px) {{ .band-head {{ font-size: clamp(1.1rem, 6.4vw, 1.45rem) !important; white-space: nowrap; }}
                                  .st-key-picker_band {{ padding-left: 20px !important; padding-right: 20px !important; }} }}
    .band-sub {{ text-align: center; color: rgba(255, 255, 255, 0.88) !important; font-size: 1.05rem;
                 max-width: 720px; margin: 10px auto 14px !important; line-height: 1.5; }}
    .picker-note {{ text-align: center; color: rgba(255, 255, 255, 0.85); font-size: 13px; margin-top: -4px; }}
    .st-key-picker_band h3, .st-key-picker_band [data-testid="stWidgetLabel"] p {{ color: #FFFFFF !important; }}
    /* "Search by drug/condition instead" link under the first box, and the popular shortcuts */
    .st-key-swap_mode {{ margin-top: -10px; }}
    .st-key-swap_mode button {{ padding: 0 !important; min-height: 0 !important; color: rgba(255, 255, 255, 0.9) !important; }}
    .st-key-swap_mode button p {{ font-size: 14px !important; text-decoration: underline;
                                 text-underline-offset: 3px; text-decoration-color: rgba(255, 255, 255, 0.45); }}
    .st-key-swap_mode button:hover p {{ color: #FFFFFF !important; text-decoration-color: #FFFFFF; }}
    .st-key-quick_row {{ gap: 4px 6px !important; align-items: center; flex-wrap: wrap; }}
    .st-key-quick_row .picker-note {{ margin: 0; }}
    [class*="st-key-quick_"] button {{
        color: #FFFFFF !important; background: rgba(255, 255, 255, 0.12) !important; border-radius: 999px !important;
        padding: 2px 12px !important; min-height: 0 !important; font-size: 13px;
    }}
    [class*="st-key-quick_"] button:hover {{ background: rgba(255, 255, 255, 0.24) !important; }}
    [class*="st-key-quick_"] button * {{ color: inherit !important; font-size: 13px !important; }}
    .st-key-picker_band [data-testid="stSelectbox"] div:has(> input) input::placeholder {{ color: #6B7685; }}

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
    .dimex-footer strong {{ color: #FFFFFF; font-size: 1.05rem; font-family: "DiMEx Logo", sans-serif;
                            letter-spacing: -0.02em; }}
    </style>
    """,
    unsafe_allow_html=True,
)

st.session_state["_card_n"] = 0        # card keys restart at card_0 on every run (core.ui.card)

from core.auth import auth_on, login_page, sign_out, signed_in, viewer_email  # noqa: E402

FOOTER = """
    <div class="dimex-footer">
      <div><strong>DiMEx</strong> · Dimensional Medication Experience Explorer</div>
      <div>Patient-reported experiences, not medical advice.</div>
    </div>
"""

# Sign-in gate, on only when accounts exist in the app's secrets ([users]). If the app is made private on
# Streamlit Cloud instead, leave [users] out and Streamlit's own sign-in does the job.
# Until a visitor signs in, only the sign-in form renders (no pages, no data).
if auth_on() and not signed_in():
    login_page()
    st.markdown(FOOTER, unsafe_allow_html=True)
    st.stop()

DRUGS = st.Page("views/drug.py", title="Drugs", default=True)
DRUGLIB = st.Page("views/druglib.py", title="Predictions", url_path="predictions")
TRY = st.Page("views/demo.py", title="Write a review", url_path="write-a-review")
CARD = st.Page("views/model_card.py", title="Model card", url_path="model-card")
# Reached through "Open review" buttons only, so it has no tab
REVIEW = st.Page("views/review.py", title="Review detail", visibility="hidden")
page = st.navigation([DRUGS, DRUGLIB, TRY, CARD, REVIEW], position="top")

page.run()

# Phones: a bottom tab bar with icons replaces the top links (CSS shows it below 760px only)
with st.container(key="bottom_nav", horizontal=True):
    for target, label, icon in [(DRUGS, "Drugs", ":material/search:"),
                                (DRUGLIB, "Predictions", ":material/compare_arrows:"),
                                (TRY, "Write a review", ":material/edit_square:"),
                                (CARD, "Model card", ":material/description:")]:
        on = page.url_path == target.url_path
        with st.container(key=f"bnav_{target.url_path or 'home'}_{'on' if on else 'off'}"):
            st.page_link(target, label=label, icon=icon)

# Who's signed in: this app's sign-in, or Streamlit Cloud's on a private app (see core.auth.viewer_email)
VIEWER = viewer_email()
if VIEWER:
    with st.container(horizontal=True, horizontal_alignment="right", vertical_alignment="center", key="signout_row"):
        st.caption(":material/account_circle: Signed in as "
                   + VIEWER.replace("@", "@\u200b"))                      # zero-width space: not a link
        if auth_on():                       # Cloud's sign-in is ended from Streamlit, not from inside the app
            st.button("Sign out", key="signout", on_click=sign_out, type="tertiary")

st.markdown(FOOTER, unsafe_allow_html=True)
