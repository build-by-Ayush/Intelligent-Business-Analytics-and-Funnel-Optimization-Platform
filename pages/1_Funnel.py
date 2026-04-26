from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from src.data_loader import load_data
from src.navigation import render_header_with_nav


st.set_page_config(
    page_title="Funnel Analysis",
    layout="wide",
    initial_sidebar_state="expanded",
)

PAGE_BG = "#18181B"
CARD_BG = "#232326"
CARD_BG_2 = "#1C1C1F"
BORDER = "#2F2F33"

TEXT = "#FAFAFA"
MUTED = "#A1A1AA"

ACCENT = "#22C55E"
SUCCESS = "#16A34A"
DANGER = "#DC2626"
WARNING = "#F59E0B"

LINE_COL = "#F97316"

CATEGORY_COLORS = [
    "#22C55E",
    "#4ADE80",
    "#F59E0B",
    "#DC2626",
    "#A78BFA",
    "#F97316",
    "#EAB308",
    "#F43F5E",
]

st.markdown(
    f"""
    <style>
    .stApp {{
        background: {PAGE_BG};
        color: {TEXT};
    }}

    .block-container {{
        padding-top: 1.1rem;
        padding-bottom: 1.8rem;
    }}

    .page-title {{
        font-size: 2rem;
        font-weight: 900;
        color: {TEXT};
        line-height: 1.08;
        margin-bottom: 0.35rem;
    }}

    .page-subtitle {{
        font-size: 0.95rem;
        color: {MUTED};
        margin-bottom: 1.15rem;
    }}

    .section-title {{
        font-size: 1.25rem;
        font-weight: 800;
        margin-bottom: 0.25rem;
        color: {TEXT};
    }}

    .section-subtitle {{
        font-size: 0.9rem;
        color: {MUTED};
        margin-bottom: 0.85rem;
    }}

    .insight-box {{
        padding: 16px 18px;
        border-radius: 18px;
        border: 1px solid {BORDER};
        background: linear-gradient(180deg, rgba(35,35,38,0.96) 0%, rgba(28,28,31,0.96) 100%);
        box-shadow: 0 2px 10px rgba(0,0,0,0.18);
    }}

    .insight-title {{
        font-size: 1rem;
        font-weight: 800;
        color: {TEXT};
        margin-bottom: 6px;
    }}

    .insight-body {{
        font-size: 0.92rem;
        color: {TEXT};
        line-height: 1.55;
    }}

    .checkout-strip {{
        position: relative;
        left: 50%;
        right: 50%;
        margin-left: -50vw;
        margin-right: -50vw;

        width: 100vw;
        padding: 18px 32px;

        background: rgba(35, 35, 38, 0.78);
        border-top: 1px solid rgba(255,255,255,0.06);
        border-bottom: 1px solid rgba(255,255,255,0.06);

        border-radius: 0;
        box-shadow: none;
    }}

    .checkout-strip-head {{
        max-width: 1200px;
        margin: 0 auto 10px auto;
    }}

    .checkout-strip-title {{
        font-size: 1rem;
        font-weight: 800;
        color: {TEXT};
        line-height: 1.2;
    }}

    .checkout-strip-subtitle {{
        font-size: 0.85rem;
        color: {MUTED};
        margin-top: 3px;
    }}

    .checkout-strip-grid {{
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 16px;

        max-width: 1200px;
        margin: 0 auto;
    }}

    .checkout-item {{
        padding: 12px 14px;
        border-radius: 12px;
        background: #18181B;
        border: 1px solid rgba(63, 63, 70, 0.6);
    }}

    .checkout-label {{
        font-size: 0.82rem;
        color: {MUTED};
        margin-bottom: 6px;
    }}

    .checkout-value {{
        font-size: 1.18rem;
        font-weight: 800;
        color: {TEXT};
        line-height: 1.15;
    }}

    .checkout-note {{
        font-size: 0.78rem;
        color: {MUTED};
        margin-top: 5px;
    }}

    div.stButton > button {{
        border-radius: 12px;
        border: 1px solid {BORDER};
        background: linear-gradient(180deg, rgba(35,35,38,0.96) 0%, rgba(28,28,31,0.96) 100%);
        color: {TEXT};
        font-weight: 600;
    }}

    div.stButton > button:hover {{
        border-color: {ACCENT};
        color: {TEXT};
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_all_data():
    return load_data()


def safe_divide(numerator, denominator):
    if denominator in (0, None) or pd.isna(denominator):
        return 0
    return numerator / denominator


def stat_card(
    title: str,
    value: str,
    subtitle: str | None = None,
    subtitle_positive: bool | None = None,
) -> str:
    color = SUCCESS if subtitle_positive else DANGER
    arrow = "▲" if subtitle_positive else "▼"
    subtitle_html = (
        f'<div style="font-size: 0.82rem; color: {color}; margin-top: 6px;">{arrow} {subtitle}</div>'
        if subtitle
        else ""
    )
    return f"""
    <div style="
        padding: 18px 16px;
        border-radius: 18px;
        border: 1px solid {BORDER};
        background: linear-gradient(180deg, rgba(17,24,39,0.97) 0%, rgba(15,23,42,0.97) 100%);
        box-shadow: 0 8px 24px rgba(0,0,0,0.22);
        min-height: 118px;
    ">
        <div style="font-size: 0.86rem; color: {MUTED}; margin-bottom: 8px;">{title}</div>
        <div style="font-size: 1.7rem; font-weight: 800; color: {TEXT}; line-height: 1.1;">{value}</div>
        {subtitle_html}
    </div>
    """


@st.cache_data
def build_session_sequences(events: pd.DataFrame):
    df = events.copy()
    df["event_timestamp_dt"] = pd.to_datetime(df["event_timestamp"], dayfirst=True, errors="coerce")
    df = df.sort_values(["session_id", "event_timestamp_dt", "event_step"])

    seq_map = (
        df.groupby("session_id")["event_type"]
        .apply(lambda s: list(dict.fromkeys(s.dropna().tolist())))
        .to_dict()
    )

    meta = (
        df.groupby("session_id", as_index=True)
        .agg(
            traffic_source=("traffic_source", "first"),
            device_type=("device_type", "first"),
            region=("region", "first"),
            start_time=("event_timestamp_dt", "min"),
        )
        .reset_index()
    )

    return seq_map, meta, df


@st.cache_data
def build_session_funnel(events: pd.DataFrame, stages: list[str]) -> pd.DataFrame:
    seq_map, _, _ = build_session_sequences(events)

    remaining_sessions = set(seq_map.keys())
    rows = []
    last_positions = {sid: -1 for sid in remaining_sessions}

    for idx, stage in enumerate(stages):
        matched = set()
        for sid in list(remaining_sessions):
            seq = seq_map.get(sid, [])
            try:
                position = seq.index(stage, last_positions[sid] + 1)
            except ValueError:
                continue
            matched.add(sid)
            last_positions[sid] = position

        sessions = len(matched)
        if idx == 0:
            conversion = 1.0
            dropoff = 0.0
        else:
            prev_sessions = rows[-1]["sessions"]
            conversion = safe_divide(sessions, prev_sessions)
            dropoff = 1 - conversion

        rows.append(
            {
                "step": stage,
                "sessions": sessions,
                "conversion_rate": conversion,
                "dropoff_rate": dropoff,
            }
        )
        remaining_sessions = matched

    return pd.DataFrame(rows)


@st.cache_data
def build_segment_dropoff_heatmap(events: pd.DataFrame, dimension: str, stages: list[str]) -> pd.DataFrame:
    seq_map, meta, _ = build_session_sequences(events)
    meta = meta[["session_id", dimension]].dropna()
    segments = meta[dimension].astype(str).unique().tolist()

    transitions = [f"{stages[i]} → {stages[i+1]}" for i in range(len(stages) - 1)]
    matrix = pd.DataFrame(index=transitions, columns=segments, dtype=float)

    for segment in segments:
        segment_sessions = set(meta.loc[meta[dimension].astype(str) == segment, "session_id"].tolist())
        if not segment_sessions:
            continue

        prev_sessions = segment_sessions
        last_positions = {sid: -1 for sid in prev_sessions if sid in seq_map}

        step_counts = []
        for stage in stages:
            matched = set()
            for sid in list(prev_sessions):
                seq = seq_map.get(sid, [])
                try:
                    position = seq.index(stage, last_positions.get(sid, -1) + 1)
                except ValueError:
                    continue
                matched.add(sid)
                last_positions[sid] = position
            step_counts.append(len(matched))
            prev_sessions = matched

        for i in range(len(step_counts) - 1):
            prev_val = step_counts[i]
            next_val = step_counts[i + 1]
            conversion = safe_divide(next_val, prev_val)
            dropoff = 1 - conversion
            matrix.loc[transitions[i], segment] = dropoff * 100

    return matrix.fillna(0)


@st.cache_data
def build_friction_table(events: pd.DataFrame) -> pd.DataFrame:
    df = events.copy()
    df["event_timestamp_dt"] = pd.to_datetime(df["event_timestamp"], dayfirst=True, errors="coerce")
    df = df.sort_values(["session_id", "event_timestamp_dt", "event_step"])

    rows = []
    for session_id, group in df.groupby("session_id"):
        group = group.dropna(subset=["event_timestamp_dt"])
        if len(group) < 2:
            continue
        times = group["event_timestamp_dt"].tolist()
        types = group["event_type"].tolist()

        for i in range(len(times) - 1):
            transition = f"{types[i]} → {types[i+1]}"
            minutes = (times[i + 1] - times[i]).total_seconds() / 60.0
            rows.append({"session_id": session_id, "transition": transition, "minutes": max(minutes, 0)})

    out = pd.DataFrame(rows)
    if out.empty:
        return out

    summary = (
        out.groupby("transition", as_index=False)
        .agg(
            median_minutes=("minutes", "median"),
            p75_minutes=("minutes", lambda s: s.quantile(0.75)),
            observations=("minutes", "size"),
        )
        .sort_values("median_minutes", ascending=False)
    )
    return summary


@st.cache_data
def build_product_funnel(order_items: pd.DataFrame, returns: pd.DataFrame, events: pd.DataFrame, top_n: int = 5) -> pd.DataFrame:
    views = (
        events.loc[events["event_type"] == "view"]
        .groupby(["product_id", "product_name", "category"], as_index=False)
        .agg(views=("session_id", "nunique"))
    )
    carts = (
        events.loc[events["event_type"] == "add_to_cart"]
        .groupby(["product_id", "product_name", "category"], as_index=False)
        .agg(carts=("session_id", "nunique"))
    )
    purchases = (
        order_items.groupby(["product_id", "product_name", "category"], as_index=False)
        .agg(
            purchases=("order_item_id", "nunique"),
            revenue=("total_price", "sum"),
        )
    )
    returned = (
        returns.groupby("product_id", as_index=False)
        .agg(returned_items=("order_item_id", "nunique"))
    )

    df = (
        purchases.merge(views, on=["product_id", "product_name", "category"], how="left")
        .merge(carts, on=["product_id", "product_name", "category"], how="left")
        .merge(returned, on="product_id", how="left")
        .fillna(0)
    )

    df["view_to_cart"] = df.apply(lambda row: safe_divide(row["carts"], row["views"]), axis=1)
    df["cart_to_purchase"] = df.apply(lambda row: safe_divide(row["purchases"], row["carts"]), axis=1)
    df["view_to_purchase"] = df.apply(lambda row: safe_divide(row["purchases"], row["views"]), axis=1)
    df["return_rate"] = df.apply(lambda row: safe_divide(row["returned_items"], row["purchases"]), axis=1)

    df = df.sort_values(["purchases", "revenue"], ascending=[False, False]).head(top_n).copy()
    return df


@st.cache_data
def build_funnel_insights(session_funnel: pd.DataFrame, product_funnel: pd.DataFrame, friction_table: pd.DataFrame) -> dict:
    top_drop_step = "N/A"
    if len(session_funnel) >= 2:
        drops = session_funnel.iloc[1:]["dropoff_rate"].tolist()
        steps = session_funnel.iloc[1:]["step"].tolist()
        if drops:
            top_drop_step = steps[drops.index(max(drops))]

    highest_return_product = "N/A"
    if not product_funnel.empty:
        highest_return_product = product_funnel.sort_values("return_rate", ascending=False).iloc[0]["product_name"]

    slowest_transition = "N/A"
    if not friction_table.empty:
        slowest_transition = friction_table.sort_values("median_minutes", ascending=False).iloc[0]["transition"]

    return {
        "top_drop_step": top_drop_step,
        "highest_return_product": highest_return_product,
        "slowest_transition": slowest_transition,
    }


def render():
    events, order_items, products, returns, transactions = load_all_data()
    stages = ["visit", "search", "view", "add_to_cart", "checkout_start", "purchase"]

    session_funnel = build_session_funnel(events, stages)
    device_heatmap = build_segment_dropoff_heatmap(events, "device_type", stages)
    traffic_heatmap = build_segment_dropoff_heatmap(events, "traffic_source", stages)
    region_heatmap = build_segment_dropoff_heatmap(events, "region", stages)
    friction_table = build_friction_table(events)
    product_funnel = build_product_funnel(order_items, returns, events, top_n=5)
    funnel_insights = build_funnel_insights(session_funnel, product_funnel, friction_table)

    total_visit = int(session_funnel.iloc[0]["sessions"]) if not session_funnel.empty else 0
    total_purchase = int(session_funnel.iloc[-1]["sessions"]) if not session_funnel.empty else 0
    overall_conversion = safe_divide(total_purchase, total_visit)

    checkout_row = session_funnel.loc[session_funnel["step"] == "checkout_start"]
    purchase_row = session_funnel.loc[session_funnel["step"] == "purchase"]
    checkout_count = int(checkout_row.iloc[0]["sessions"]) if not checkout_row.empty else 0
    purchase_count = int(purchase_row.iloc[0]["sessions"]) if not purchase_row.empty else 0
    checkout_abandonment = 1 - safe_divide(purchase_count, checkout_count)

    cart_row = session_funnel.loc[session_funnel["step"] == "add_to_cart"]
    cart_count = int(cart_row.iloc[0]["sessions"]) if not cart_row.empty else 0
    cart_to_purchase = safe_divide(purchase_count, cart_count)

    max_drop_row = session_funnel.iloc[1:].sort_values("dropoff_rate", ascending=False).iloc[0]
    max_drop_value = max_drop_row["dropoff_rate"]
    max_drop_step = max_drop_row["step"]

    total_revenue = order_items["total_price"].sum()
    revenue_per_visit = safe_divide(total_revenue, total_visit)

    view_row = session_funnel.loc[session_funnel["step"] == "view"]
    view_count = int(view_row.iloc[0]["sessions"]) if not view_row.empty else 0
    view_to_cart_rate = safe_divide(cart_count, view_count)

    avg_friction = 0.0
    if not friction_table.empty:
        avg_friction = float(friction_table["median_minutes"].mean())

    st.markdown("""
    <style>
    .block-container {
        padding-top: 2.5rem;
        padding-left: 90px;  /* space for nav strip */
    }
    </style>
    """, unsafe_allow_html=True)

    render_header_with_nav(
        "Funnel Analysis",
        "Customer journey, drop-off diagnostics, product funnel behavior, and friction signals.",
        "Funnel",
    )
    st.markdown("<div style='height: 22px;'></div>", unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(stat_card("Overall Conversion", f"{overall_conversion * 100:.2f}%"), unsafe_allow_html=True)
    with c2:
        st.markdown(stat_card("Checkout Abandonment", f"{checkout_abandonment * 100:.2f}%"), unsafe_allow_html=True)
    with c3:
        st.markdown(stat_card("Cart → Purchase", f"{cart_to_purchase * 100:.2f}%"), unsafe_allow_html=True)
    with c4:
        st.markdown(stat_card("Avg Step Friction", f"{avg_friction:.2f} min"), unsafe_allow_html=True)

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    left, right = st.columns([1.1, 1.0], gap="large")

    funnel_fig = px.funnel(session_funnel, x="sessions", y="step", template="plotly_dark")
    funnel_fig.update_traces(
        textposition="inside",
        textinfo="value+percent previous",
        textfont=dict(color=TEXT, size=14),
        marker=dict(color=ACCENT, line=dict(color=PAGE_BG, width=1.2)),
    )
    funnel_fig.update_layout(
        height=430,
        margin=dict(l=10, r=10, t=20, b=10),
        showlegend=False,
        paper_bgcolor=PAGE_BG,
        plot_bgcolor=PAGE_BG,
        font=dict(color=TEXT),
    )
    funnel_fig.update_xaxes(gridcolor="#3F3F46", zerolinecolor="#3F3F46")
    funnel_fig.update_yaxes(gridcolor="#3F3F46", zerolinecolor="#3F3F46")

    device_conv = (
        events.groupby("device_type")["session_id"]
        .nunique()
        .reset_index(name="visits")
    )

    purchases = (
        events[events["event_type"] == "purchase"]
        .groupby("device_type")["session_id"]
        .nunique()
        .reset_index(name="purchases")
    )

    device_conv = device_conv.merge(purchases, on="device_type", how="left").fillna(0)
    device_conv["conversion_rate"] = device_conv.apply(
        lambda row: safe_divide(row["purchases"], row["visits"]), axis=1
    )

    DEVICE_PALETTE = ["#F97316", "#A78BFA", "#F59E0B", "#F43F5E", "#EAB308"]

    fig_dev = px.bar(
        device_conv,
        x="device_type",
        y="conversion_rate",
        text=device_conv["conversion_rate"].map(lambda x: f"{x*100:.1f}%"),
        template="plotly_dark",
        color="device_type",
        color_discrete_sequence=DEVICE_PALETTE[: len(device_conv)],
    )
    fig_dev.update_traces(
        textposition="outside",
        textfont=dict(color=TEXT),
        marker_line_color=PAGE_BG,
        marker_line_width=1.0,
        opacity=0.95,
        hovertemplate="<b>%{x}</b><br>Conversion Rate: %{y:.1%}<extra></extra>",
    )
    fig_dev.update_layout(
        height=430,
        yaxis_title="Conversion Rate",
        paper_bgcolor=PAGE_BG,
        plot_bgcolor=PAGE_BG,
        font=dict(color=TEXT),
        margin=dict(l=10, r=10, t=20, b=10),
        showlegend=False,
        bargap=0.3,        # increase gap between bars (default ~0.2)
        bargroupgap=0.2,   # gap between grouped bars (if any)
    )
    fig_dev.update_xaxes(gridcolor="#3F3F46", zerolinecolor="#3F3F46")
    fig_dev.update_yaxes(gridcolor="#3F3F46", zerolinecolor="#3F3F46", tickformat=".0%")

    with left:
        st.markdown('<div class="section-title">Core Conversion Funnel</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-subtitle">Ordered customer journey with absolute users and step conversion.</div>',
            unsafe_allow_html=True,
        )
        st.plotly_chart(funnel_fig, use_container_width=True)

    with right:
        st.markdown('<div class="section-title">Device Conversion</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-subtitle">Conversion rate by device type (purchase / visit).</div>',
            unsafe_allow_html=True,
        )
        st.plotly_chart(fig_dev, use_container_width=True)

    st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)

    st.markdown('<div class="section-title">Drop-off Heatmap</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-subtitle">Where the funnel weakens across device, traffic source, and region.</div>',
        unsafe_allow_html=True,
    )
    heat_tabs = st.tabs(["Device Type", "Traffic Source", "Region"])

    heatmap_specs = [
        (heat_tabs[0], device_heatmap),
        (heat_tabs[1], traffic_heatmap),
        (heat_tabs[2], region_heatmap),
    ]

    for tab, matrix in heatmap_specs:
        with tab:
            if matrix.empty:
                st.info("No heatmap data available.")
            else:
                fig = px.imshow(
                    matrix,
                    text_auto=".1f",
                    aspect="auto",
                    color_continuous_scale="Reds",
                    labels=dict(x="Segment", y="Step Transition", color="Drop-off %"),
                    template="plotly_dark",
                )
                fig.update_layout(
                    height=420,
                    margin=dict(l=10, r=10, t=20, b=10),
                    paper_bgcolor=PAGE_BG,
                    plot_bgcolor=PAGE_BG,
                    font=dict(color=TEXT),
                )
                st.plotly_chart(fig, use_container_width=True)

    st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)

    left, right = st.columns([1.05, 1.0], gap="large")
    with left:
        st.markdown('<div class="section-title">Top Product Funnel Table</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-subtitle">Top 5 products by purchase volume, with view/cart/purchase and return signals.</div>',
            unsafe_allow_html=True,
        )
        if product_funnel.empty:
            st.info("No product funnel data available.")
        else:
            display = product_funnel.copy()
            display["view_to_cart"] = display["view_to_cart"].map(lambda x: f"{x * 100:.2f}%")
            display["cart_to_purchase"] = display["cart_to_purchase"].map(lambda x: f"{x * 100:.2f}%")
            display["view_to_purchase"] = display["view_to_purchase"].map(lambda x: f"{x * 100:.2f}%")
            display["return_rate"] = display["return_rate"].map(lambda x: f"{x * 100:.2f}%")
            display["revenue"] = display["revenue"].map(lambda x: f"₹{x:,.2f}")
            display = display[
                [
                    "product_name",
                    "category",
                    "views",
                    "carts",
                    "purchases",
                    "view_to_cart",
                    "cart_to_purchase",
                    "view_to_purchase",
                    "return_rate",
                    "revenue",
                ]
            ]
            st.dataframe(display, use_container_width=True, hide_index=True)

        st.markdown('<div class="section-title">Key Funnel Signals</div>', unsafe_allow_html=True)
        k1, k2, k3 = st.columns(3)

        with k1:
            st.markdown(
                stat_card(
                    "Max Drop-Off",
                    f"{max_drop_value * 100:.1f}%",
                    subtitle=f"at {max_drop_step}",
                    subtitle_positive=False,
                ),
                unsafe_allow_html=True,
            )

        with k2:
            st.markdown(
                stat_card(
                    "Revenue per Visit",
                    f"₹{revenue_per_visit:,.2f}",
                    subtitle="Business value per session",
                    subtitle_positive=True,
                ),
                unsafe_allow_html=True,
            )

        with k3:
            st.markdown(
                stat_card(
                    "View → Cart Rate",
                    f"{view_to_cart_rate * 100:.2f}%",
                    subtitle="Product interest conversion",
                    subtitle_positive=view_to_cart_rate >= 0.10,
                ),
                unsafe_allow_html=True,
            )

    with right:
        st.markdown('<div class="section-title">Behavioral Friction</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-subtitle">Median time delay between user actions; long delays imply hesitation or friction.</div>',
            unsafe_allow_html=True,
        )
        if friction_table.empty:
            st.info("No friction data available.")
        else:
            top_friction = friction_table.sort_values("median_minutes", ascending=True).copy()
            fig = px.box(
                top_friction,
                x="median_minutes",
                y="transition",
                orientation="h",
                template="plotly_dark",
                points=False,
            )
            fig.update_traces(
                fillcolor="rgba(34,197,94,0.18)",
                line_color=ACCENT,
                marker_color=LINE_COL,
            )
            fig.update_layout(
                height=460,
                margin=dict(l=10, r=10, t=20, b=10),
                xaxis_title="Median Minutes",
                yaxis_title="Transition",
                paper_bgcolor=PAGE_BG,
                plot_bgcolor=PAGE_BG,
                font=dict(color=TEXT),
            )
            fig.update_xaxes(gridcolor="#3F3F46", zerolinecolor="#3F3F46")
            fig.update_yaxes(gridcolor="#3F3F46", zerolinecolor="#3F3F46")
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    st.markdown(
        f"""
        <div class="checkout-strip">
            <div class="checkout-strip-head">
                <div class="checkout-strip-title">Checkout Focus</div>
                <div class="checkout-strip-subtitle">A compact post-funnel strip for final-step monitoring.</div>
            </div>
            <div class="checkout-strip-grid">
                <div class="checkout-item">
                    <div class="checkout-label">Checkout Start Sessions</div>
                    <div class="checkout-value">{checkout_count:,}</div>
                    <div class="checkout-note">Users who reached the final purchase stage</div>
                </div>
                <div class="checkout-item">
                    <div class="checkout-label">Purchase Sessions</div>
                    <div class="checkout-value">{purchase_count:,}</div>
                    <div class="checkout-note">Users who completed the transaction</div>
                </div>
                <div class="checkout-item">
                    <div class="checkout-label">Highest Friction Transition</div>
                    <div class="checkout-value">{funnel_insights["slowest_transition"]}</div>
                    <div class="checkout-note">Longest delay between actions</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
    st.markdown('<div class="section-title">Key Insights</div>', unsafe_allow_html=True)

    insights = []

    def add_insight(priority: int, title: str, body: str, chart_renderer=None):
        insights.append(
            {
                "priority": priority,
                "title": title,
                "body": body,
                "chart_renderer": chart_renderer,
            }
        )

    if overall_conversion < 0.15 and not session_funnel.empty:
        add_insight(
            priority=120,
            title="Low Overall Conversion",
            body=(
                f"Only <strong>{overall_conversion * 100:.1f}%</strong> of visits are turning into purchases. "
                f"This means most users are leaving before the funnel reaches the final stage. "
                f"The issue is likely broader than one isolated step and should be treated as a full funnel conversion problem."
            ),
            chart_renderer=None,
        )

    if checkout_count > 0 and checkout_abandonment > 0.50:
        add_insight(
            priority=110,
            title="Checkout Abandonment Warning",
            body=(
                f"About <strong>{checkout_abandonment * 100:.1f}%</strong> of users leave after checkout begins. "
                f"This suggests friction in the final purchase step, such as payment hesitation, trust issues, or a confusing checkout flow."
            ),
            chart_renderer=None,
        )

    if not session_funnel.empty and len(session_funnel) > 1 and max_drop_value > 0.40:
        def render_dropoff_chart():
            df = session_funnel.iloc[1:].copy()
            fig = px.bar(
                df,
                x="step",
                y="dropoff_rate",
                text=df["dropoff_rate"].map(lambda x: f"{x * 100:.1f}%"),
                template="plotly_dark",
                color="step",
                color_discrete_sequence=CATEGORY_COLORS[: len(df)],
            )
            fig.update_traces(
                textposition="outside",
                textfont=dict(color=TEXT),
                marker_line_color=PAGE_BG,
                marker_line_width=1.0,
            )
            fig.update_layout(
                height=300,
                margin=dict(l=10, r=10, t=20, b=10),
                xaxis_title="Funnel Step",
                yaxis_title="Drop-off Rate",
                yaxis_tickformat=".0%",
                paper_bgcolor=PAGE_BG,
                plot_bgcolor=PAGE_BG,
                font=dict(color=TEXT),
                showlegend=False,
            )
            fig.update_xaxes(gridcolor="#3F3F46", zerolinecolor="#3F3F46")
            fig.update_yaxes(gridcolor="#3F3F46", zerolinecolor="#3F3F46")
            st.plotly_chart(fig, use_container_width=True)

        add_insight(
            priority=100,
            title="Critical Drop-Off Stage",
            body=(
                f"The largest drop happens at <strong>{max_drop_step}</strong>, where the funnel loses a major share of users. "
                f"This indicates a strong point of friction in the journey and should be reviewed first."
            ),
            chart_renderer=render_dropoff_chart,
        )

    device_conv_sorted = device_conv.sort_values("conversion_rate") if not device_conv.empty else pd.DataFrame()

    if len(device_conv_sorted) > 1:
        worst = device_conv_sorted.iloc[0]
        best = device_conv_sorted.iloc[-1]
        spread = float(best["conversion_rate"] - worst["conversion_rate"])

        if spread > 0.10:
            def render_device_chart():
                fig = px.bar(
                    device_conv.sort_values("conversion_rate", ascending=True),
                    x="device_type",
                    y="conversion_rate",
                    text=device_conv["conversion_rate"].map(lambda x: f"{x * 100:.1f}%"),
                    template="plotly_dark",
                    color="device_type",
                    color_discrete_sequence=CATEGORY_COLORS[: len(device_conv)],
                )
                fig.update_traces(
                    textposition="outside",
                    textfont=dict(color=TEXT),
                    marker_line_color=PAGE_BG,
                    marker_line_width=1.0,
                )
                fig.update_layout(
                    height=300,
                    margin=dict(l=10, r=10, t=20, b=10),
                    xaxis_title="Device Type",
                    yaxis_title="Conversion Rate",
                    yaxis_tickformat=".0%",
                    paper_bgcolor=PAGE_BG,
                    plot_bgcolor=PAGE_BG,
                    font=dict(color=TEXT),
                    showlegend=False,
                )
                fig.update_xaxes(gridcolor="#3F3F46", zerolinecolor="#3F3F46")
                fig.update_yaxes(gridcolor="#3F3F46", zerolinecolor="#3F3F46")
                st.plotly_chart(fig, use_container_width=True)

            add_insight(
                priority=90,
                title="Device Conversion Gap",
                body=(
                    f"Conversion is noticeably weaker on <strong>{worst['device_type']}</strong> compared with "
                    f"<strong>{best['device_type']}</strong>. The gap is about <strong>{spread * 100:.1f} percentage points</strong>, "
                    f"which suggests a device-specific experience issue."
                ),
                chart_renderer=render_device_chart,
            )

    if not friction_table.empty:
        slowest = friction_table.sort_values("median_minutes", ascending=False).iloc[0]

        if float(slowest["median_minutes"]) > 2:
            def render_friction_chart():
                top_friction = friction_table.sort_values("median_minutes", ascending=False).head(5).copy()
                fig = px.bar(
                    top_friction,
                    x="median_minutes",
                    y="transition",
                    orientation="h",
                    text=top_friction["median_minutes"].map(lambda x: f"{x:.1f}"),
                    template="plotly_dark",
                    color="transition",
                    color_discrete_sequence=CATEGORY_COLORS[: len(top_friction)],
                )
                fig.update_traces(
                    textposition="outside",
                    textfont=dict(color=TEXT),
                    marker_line_color=PAGE_BG,
                    marker_line_width=1.0,
                )
                fig.update_layout(
                    height=300,
                    margin=dict(l=10, r=10, t=20, b=10),
                    xaxis_title="Median Minutes",
                    yaxis_title="Transition",
                    paper_bgcolor=PAGE_BG,
                    plot_bgcolor=PAGE_BG,
                    font=dict(color=TEXT),
                    showlegend=False,
                )
                fig.update_xaxes(gridcolor="#3F3F46", zerolinecolor="#3F3F46")
                fig.update_yaxes(gridcolor="#3F3F46", zerolinecolor="#3F3F46")
                st.plotly_chart(fig, use_container_width=True)

            add_insight(
                priority=80,
                title="High User Friction",
                body=(
                    f"Users take the longest time between <strong>{slowest['transition']}</strong>. "
                    f"The median delay is <strong>{slowest['median_minutes']:.1f} minutes</strong>, which suggests hesitation "
                    f"or confusion at this stage."
                ),
                chart_renderer=render_friction_chart,
            )

    insights = sorted(insights, key=lambda x: x["priority"], reverse=True)[:4]

    text_insights = [x for x in insights if x["chart_renderer"] is None]
    chart_insights = [x for x in insights if x["chart_renderer"] is not None]

    def render_chart_panel(item: dict):
        st.markdown(
            f"""
            <div class="insight-box" style="margin-bottom: 12px;">
                <div class="insight-title">{item["title"]}</div>
                <div class="insight-body" style="margin-bottom: 10px;">{item["body"]}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        item["chart_renderer"]()

    if text_insights:
        st.markdown('<div class="section-subtitle">Textual insights</div>', unsafe_allow_html=True)
        for item in text_insights:
            st.markdown(
                f"""
                <div class="insight-box" style="margin-bottom: 12px;">
                    <div class="insight-title">{item["title"]}</div>
                    <div class="insight-body">{item["body"]}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)

    if chart_insights:
        st.markdown('<div class="section-subtitle">Chart insights</div>', unsafe_allow_html=True)

        n = len(chart_insights)

        if n == 1:
            render_chart_panel(chart_insights[0])

        elif n % 2 == 0:
            for i in range(0, n, 2):
                c1, c2 = st.columns(2, gap="large")
                with c1:
                    render_chart_panel(chart_insights[i])
                with c2:
                    render_chart_panel(chart_insights[i + 1])

        else:
            for i in range(0, n - 1, 2):
                c1, c2 = st.columns(2, gap="large")
                with c1:
                    render_chart_panel(chart_insights[i])
                with c2:
                    render_chart_panel(chart_insights[i + 1])

            render_chart_panel(chart_insights[-1])

    elif not text_insights:
        st.info("No major issues detected in the funnel. Performance is stable.")

render()