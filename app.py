"""Drug Review Explorer: run with `streamlit run app.py`."""
import streamlit as st

st.set_page_config(page_title="Drug Review Explorer", layout="wide")

# Center the page links in the top bar. Streamlit has no setting for this, so it's CSS on
# Streamlit's own nav element (data-testid="stTopNav"). The nav keeps its full width so its
# "more" overflow menu still works on narrow screens; only the links inside are centered.
st.markdown(
    """
    <style>
    [data-testid="stTopNav"] { flex: 1 1 auto; justify-content: center; }
    </style>
    """,
    unsafe_allow_html=True,
)

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
