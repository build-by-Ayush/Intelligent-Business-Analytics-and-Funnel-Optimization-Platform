import streamlit as st

def render_header_with_nav(title: str, subtitle: str, active_page: str) -> None:
    st.markdown(
        """
        <style>
        .page-title {
            font-size: 2rem;
            font-weight: 900;
            color: #FAFAFA;
            line-height: 1.05;
            margin-bottom: 0.08rem;
        }

        .page-subtitle {
            font-size: 0.95rem;
            color: #A1A1AA;
            margin-bottom: 0;
        }

        div[data-testid="stButton"] > button {
            min-width: 40px;
            height: 38px;
            padding: 0;
            border-radius: 11px;
            border: 1px solid #2F2F33;
            background: #232326;
            color: #FAFAFA;
            font-weight: 600;
        }

        div[data-testid="stButton"] > button:hover {
            border-color: #22C55E;
        }

        div[data-testid="stButton"] > button:disabled {
            border-color: #22C55E;
            color: #22C55E;
            opacity: 1;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    left, right = st.columns([0.76, 0.24], vertical_alignment="top", gap="small")

    with left:
        st.markdown(
            f"""
            <div style="margin-bottom: 0;">
                <div class="page-title">{title}</div>
                <div class="page-subtitle">{subtitle}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right:
        spacer, b1, b2, b3, b4 = st.columns([2.8, 1, 1, 1, 1], gap="small")

        with b1:
            if st.button("", icon=":material/home:", key="nav_overview", use_container_width=True, disabled=active_page == "Overview", help="Overview"):
                st.switch_page("app.py")

        with b2:
            if st.button("", icon=":material/tune:", key="nav_funnel", use_container_width=True, disabled=active_page == "Funnel", help="Funnel"):
                st.switch_page("pages/1_Funnel.py")

        with b3:
            if st.button("", icon=":material/keyboard_return:", key="nav_returns", use_container_width=True, disabled=active_page == "Returns", help="Returns"):
                st.switch_page("pages/2_Returns.py")

        with b4:
            if st.button("", icon=":material/apps:", key="nav_products", use_container_width=True, disabled=active_page == "Products", help="Products"):
                st.switch_page("pages/3_Products.py")