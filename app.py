"""Drug Review Explorer: run with `streamlit run app.py`."""
import streamlit as st

st.set_page_config(page_title="Drug Review Explorer", layout="wide")

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
