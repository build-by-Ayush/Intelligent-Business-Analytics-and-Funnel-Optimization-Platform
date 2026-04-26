import streamlit as st

st.set_page_config(
    page_title="Intelligent Business Analytics and Funnel Optimization Platform",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Intelligent Business Analytics and Funnel Optimization Platform")
st.caption("Use the pages on the left to move between Overview, Funnel Analysis, Returns Analysis, and Product Analysis.")

st.markdown(
    """
    ### Project structure
    - **Overview**: KPI monitoring and top-level business health
    - **Funnel Analysis**: session funnel and product funnel
    - **Returns Analysis**: return behavior and refund impact
    - **Product Analysis**: product-level performance and concentration

    ### Build order
    1. Overview
    2. Funnel
    3. Returns
    4. Product Analysis
    """
)