from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from src.data_loader import get_data_version, load_data
from src.navigation import render_header_with_nav
from src.metrics import build_item_financials, net_merchandise_sales


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


def load_all_data():
    # src.data_loader owns the shared cache so the same loaded tables can be reused
    # across dashboard pages rather than cached separately in each page module.
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


@st.cache_data(show_spinner=False)
def build_event_analytics(data_version: tuple, _events: pd.DataFrame):
    """Prepare session positions, segment metadata, friction metrics, and product event counts once.

    data_version is based on source-file paths, modification times, and sizes. The large
    events DataFrame is deliberately excluded from Streamlit's cache-key hashing; changing
    any source CSV changes data_version and invalidates this result.
    """
    required = [
        "session_id",
        "event_timestamp",
        "event_step",
        "event_type",
        "traffic_source",
        "device_type",
        "region",
    ]
    df = _events.loc[:, required].copy()

    if not pd.api.types.is_datetime64_any_dtype(df["event_timestamp"]):
        df["event_timestamp_dt"] = pd.to_datetime(
            df["event_timestamp"], errors="coerce", dayfirst=False
        )
    else:
        df["event_timestamp_dt"] = df["event_timestamp"]

    # Sessions with no session_id were excluded by the original groupby logic.
    df = df.dropna(subset=["session_id"])
    df = df.sort_values(
        ["session_id", "event_timestamp_dt", "event_step"],
        kind="mergesort",
    )

    # Keep the first occurrence of each event type within a session, matching the old
    # list(dict.fromkeys(...)) event-sequence semantics.
    df["_event_position"] = df.groupby("session_id", sort=False).cumcount()
    first_events = df.dropna(subset=["event_type"]).drop_duplicates(
        ["session_id", "event_type"], keep="first"
    )
    first_positions = first_events.pivot(
        index="session_id", columns="event_type", values="_event_position"
    )
    first_positions.columns.name = None

    session_meta = (
        df.groupby("session_id", as_index=False, sort=True)
        .agg(
            traffic_source=("traffic_source", "first"),
            device_type=("device_type", "first"),
            region=("region", "first"),
            start_time=("event_timestamp_dt", "min"),
        )
    )
    # Retain sessions with no non-null event_type, as the original sequence map did.
    first_positions = first_positions.reindex(session_meta["session_id"].tolist())
    first_positions.index.name = "session_id"

    # Vectorised consecutive-event timing replaces the nested Python session/event loops.
    timed = df.dropna(subset=["event_timestamp_dt"]).copy()
    grouped = timed.groupby("session_id", sort=False)
    timed["_previous_time"] = grouped["event_timestamp_dt"].shift(1)
    timed["_previous_type"] = grouped["event_type"].shift(1)
    transitions = timed.loc[timed["_previous_time"].notna()].copy()

    if transitions.empty:
        friction_table = pd.DataFrame(
            columns=["transition", "median_minutes", "p75_minutes", "observations"]
        )
    else:
        transitions["transition"] = (
            transitions["_previous_type"].astype(str)
            + " → "
            + transitions["event_type"].astype(str)
        )
        transitions["minutes"] = (
            transitions["event_timestamp_dt"] - transitions["_previous_time"]
        ).dt.total_seconds().div(60).clip(lower=0)
        friction_table = (
            transitions.groupby("transition", as_index=False)
            .agg(
                median_minutes=("minutes", "median"),
                p75_minutes=("minutes", lambda values: values.quantile(0.75)),
                observations=("minutes", "size"),
            )
            .sort_values("median_minutes", ascending=False)
            .reset_index(drop=True)
        )

    # One grouped aggregation supplies the per-product session counts for view, cart,
    # and purchase, instead of scanning the full events table three separate times.
    product_event_rows = _events.loc[
        _events["event_type"].isin(["view", "add_to_cart", "purchase"]),
        ["product_id", "event_type", "session_id"],
    ]
    product_event_counts = (
        product_event_rows.groupby(["product_id", "event_type"])["session_id"]
        .nunique()
        .unstack(fill_value=0)
    )
    product_event_counts.columns.name = None
    product_event_counts.index.name = "product_id"

    return first_positions, session_meta, friction_table, product_event_counts


def build_session_funnel(first_positions: pd.DataFrame, stages: list[str]) -> pd.DataFrame:
    """Calculate sequential stage counts from each session's first occurrence positions."""
    if first_positions.empty:
        return pd.DataFrame(columns=["step", "sessions", "conversion_rate", "dropoff_rate"])

    rows = []
    eligible = pd.Series(True, index=first_positions.index)
    previous_position = None

    for idx, stage in enumerate(stages):
        if stage in first_positions.columns:
            position = first_positions[stage]
        else:
            position = pd.Series(float("nan"), index=first_positions.index)

        stage_present = position.notna()
        if idx == 0:
            eligible = stage_present
        else:
            eligible = eligible & stage_present & position.gt(previous_position)

        sessions = int(eligible.sum())
        if idx == 0:
            conversion = 1.0
            dropoff = 0.0
        else:
            previous_sessions = rows[-1]["sessions"]
            if previous_sessions > 0:
                conversion = sessions / previous_sessions
                dropoff = 1.0 - conversion
            else:
                conversion = 0.0
                dropoff = 0.0

        rows.append(
            {
                "step": stage,
                "sessions": sessions,
                "conversion_rate": conversion,
                "dropoff_rate": dropoff,
            }
        )
        previous_position = position

    return pd.DataFrame(rows)


def build_segment_dropoff_heatmap(
    first_positions: pd.DataFrame,
    session_meta: pd.DataFrame,
    dimension: str,
    transitions: list[tuple[str, str]],
) -> pd.DataFrame:
    """Vectorised drop-off calculation for selected source-to-target transitions."""
    meta = session_meta[["session_id", dimension]].dropna(subset=[dimension]).copy()
    meta[dimension] = meta[dimension].astype(str)
    segment_order = meta[dimension].drop_duplicates().tolist()
    transition_labels = [f"{source} → {target}" for source, target in transitions]
    matrix = pd.DataFrame(index=transition_labels, columns=segment_order, dtype=float)

    segment_by_session = meta.set_index("session_id")[dimension].reindex(first_positions.index)

    for (source, target), label in zip(transitions, transition_labels):
        if source in first_positions.columns:
            source_position = first_positions[source]
            source_reached = source_position.notna()
        else:
            source_position = pd.Series(float("nan"), index=first_positions.index)
            source_reached = pd.Series(False, index=first_positions.index)

        if target in first_positions.columns:
            target_position = first_positions[target]
            target_after_source = target_position.notna() & target_position.gt(source_position)
        else:
            target_after_source = pd.Series(False, index=first_positions.index)

        for segment in segment_order:
            in_segment = segment_by_session.eq(segment)
            denominator_mask = in_segment & source_reached
            denominator = int(denominator_mask.sum())
            if denominator:
                numerator = int((denominator_mask & target_after_source).sum())
                matrix.loc[label, segment] = (1.0 - numerator / denominator) * 100.0
            else:
                # Keep the existing dashboard convention for a segment with no source events.
                matrix.loc[label, segment] = 0.0

    return matrix.fillna(0.0)


@st.cache_data(show_spinner=False)
def build_product_funnel(
    order_items: pd.DataFrame,
    products: pd.DataFrame,
    transactions: pd.DataFrame,
    returns: pd.DataFrame,
    product_event_counts: pd.DataFrame,
    top_n: int = 5,
) -> pd.DataFrame:
    # Item-level sales use the shared net-merchandise-sales definition.
    item_financials = build_item_financials(order_items, products, transactions)
    item_sales = (
        item_financials.groupby(["product_id", "product_name", "category"], as_index=False)
        .agg(
            order_item_count=("order_item_id", "nunique"),
            units_sold=("quantity", "sum"),
            revenue=("net_merchandise_sales", "sum"),
        )
    )

    event_counts = product_event_counts.reset_index()
    event_counts = event_counts.rename(
        columns={"view": "views", "add_to_cart": "carts", "purchase": "purchases"}
    )
    for column in ["views", "carts", "purchases"]:
        if column not in event_counts.columns:
            event_counts[column] = 0

    if returns.empty:
        returned = pd.DataFrame(columns=["product_id", "returned_units"])
    elif "return_quantity" in returns.columns:
        return_units = returns.copy()
        return_units["return_quantity"] = pd.to_numeric(
            return_units["return_quantity"], errors="coerce"
        ).fillna(0)
        # Every row is a request; pending/rejected requests remain included.
        returned = return_units.groupby("product_id", as_index=False).agg(
            returned_units=("return_quantity", "sum")
        )
    else:
        raise KeyError(
            "returns must contain 'return_quantity' to calculate a unit-based return-request rate."
        )

    df = (
        item_sales.merge(
            event_counts[["product_id", "views", "carts", "purchases"]],
            on="product_id",
            how="left",
        )
        .merge(returned, on="product_id", how="left")
    )

    for column in ["purchases", "views", "carts", "returned_units", "units_sold", "order_item_count"]:
        df[column] = pd.to_numeric(df[column], errors="coerce").fillna(0).astype(int)

    df["view_to_cart"] = df["carts"].div(df["views"].where(df["views"].ne(0))).fillna(0.0)
    df["cart_to_purchase"] = df["purchases"].div(df["carts"].where(df["carts"].ne(0))).fillna(0.0)
    df["view_to_purchase"] = df["purchases"].div(df["views"].where(df["views"].ne(0))).fillna(0.0)
    df["return_rate"] = df["returned_units"].div(df["units_sold"].where(df["units_sold"].ne(0))).fillna(0.0)

    # Preserve the existing product ranking and table grain.
    return df.sort_values(["order_item_count", "revenue"], ascending=[False, False]).head(top_n).copy()


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
    # Search remains optional in the core conversion funnel.
    stages = ["visit", "view", "add_to_cart", "checkout_start", "purchase"]

    # One cached pass over events supplies all session, friction, segment, and product-event data.
    first_positions, session_meta, friction_table, product_event_counts = build_event_analytics(
        get_data_version(), events
    )
    session_funnel = build_session_funnel(first_positions, stages)
    heatmap_transitions = [
        ("search", "add_to_cart"),
        ("view", "add_to_cart"),
        ("checkout_start", "purchase"),
    ]
    device_heatmap = build_segment_dropoff_heatmap(
        first_positions, session_meta, "device_type", heatmap_transitions
    )
    traffic_heatmap = build_segment_dropoff_heatmap(
        first_positions, session_meta, "traffic_source", heatmap_transitions
    )
    region_heatmap = build_segment_dropoff_heatmap(
        first_positions, session_meta, "region", heatmap_transitions
    )
    product_funnel = build_product_funnel(
        order_items, products, transactions, returns, product_event_counts, top_n=5
    )
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

    total_revenue = net_merchandise_sales(transactions)
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
        st.markdown(stat_card("Avg Median Delay", f"{avg_friction:.2f} min"), unsafe_allow_html=True)

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
        events.loc[events["event_type"] == "visit"]
        .groupby("device_type")["session_id"]
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
            '<div class="section-subtitle">Ordered session journey with session counts and step conversion.</div>',
            unsafe_allow_html=True,
        )
        st.plotly_chart(funnel_fig, width="stretch")

    with right:
        st.markdown('<div class="section-title">Device Conversion</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-subtitle">Session conversion rate by device (purchase sessions / visit sessions).</div>',
            unsafe_allow_html=True,
        )
        st.plotly_chart(fig_dev, width="stretch")

    st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)

    st.markdown('<div class="section-title">Drop-off Heatmap</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-subtitle">Drop-off across search-to-cart, view-to-cart, and checkout-to-purchase transitions by device, traffic source, and region.</div>',
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
                fig.update_traces(xgap=1, ygap=1)
                fig.update_layout(
                    height=420,
                    margin=dict(l=10, r=10, t=20, b=10),
                    paper_bgcolor=PAGE_BG,
                    plot_bgcolor=PAGE_BG,
                    font=dict(color=TEXT),
                )
                st.plotly_chart(fig, width="stretch")

    st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)

    left, right = st.columns([1.05, 1.0], gap="large")
    with left:
        st.markdown('<div class="section-title">Top Product Funnel Table</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-subtitle">Top 5 products by purchased item volume, with event-based session conversion and unit-based return-request signals.</div>',
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
            ].rename(
                columns={
                    "purchases": "purchase_sessions",
                    "return_rate": "return_request_rate",
                    "revenue": "net_merchandise_sales",
                }
            )
            st.dataframe(display, width="stretch", hide_index=True)

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
                    "Net Sales per Visit",
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
            '<div class="section-subtitle">Median time between actions; long gaps flag transitions to review but do not identify the cause.</div>',
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
            st.plotly_chart(fig, width="stretch")

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
                    <div class="checkout-note">Sessions that initiated checkout</div>
                </div>
                <div class="checkout-item">
                    <div class="checkout-label">Purchase Sessions</div>
                    <div class="checkout-value">{purchase_count:,}</div>
                    <div class="checkout-note">Sessions that completed a purchase</div>
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
                f"<strong>{overall_conversion * 100:.1f}%</strong> of visit sessions reached purchase through the required funnel sequence. "
                f"This shows a large gap between visits and completed purchases. Review the stage counts and segment patterns before assigning a cause."
            ),
            chart_renderer=None,
        )

    if checkout_count > 0 and checkout_abandonment > 0.50:
        add_insight(
            priority=110,
            title="Checkout Abandonment Warning",
            body=(
                f"<strong>{checkout_abandonment * 100:.1f}%</strong> of sessions that reached checkout did not reach purchase in the funnel sequence. "
                f"Payment, trust, delivery costs, or checkout usability are possible areas to investigate; this metric alone does not identify the reason."
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
            st.plotly_chart(fig, width="stretch")

        add_insight(
            priority=100,
            title="Critical Drop-Off Stage",
            body=(
                f"The largest observed stage-to-stage decline occurs at <strong>{max_drop_step}</strong>, where session count falls by <strong>{max_drop_value * 100:.1f}%</strong> versus the previous stage. "
                f"This localizes the largest count loss, but does not establish why it occurred."
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
                st.plotly_chart(fig, width="stretch")

            add_insight(
                priority=90,
                title="Device Conversion Gap",
                body=(
                    f"Observed conversion is lower on <strong>{worst['device_type']}</strong> than on "
                    f"<strong>{best['device_type']}</strong> by about <strong>{spread * 100:.1f} percentage points</strong>. "
                    f"Treat this as a segment difference to investigate; it does not by itself prove a device-specific experience issue."
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
                st.plotly_chart(fig, width="stretch")

            add_insight(
                priority=80,
                title="High User Friction",
                body=(
                    f"The longest observed median gap is between <strong>{slowest['transition']}</strong>. "
                    f"The median delay is <strong>{slowest['median_minutes']:.1f} minutes</strong>. Timing alone cannot distinguish hesitation from normal browsing or other behavior."
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