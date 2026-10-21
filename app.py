from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.data_loader import load_data
from src.metrics import (
    _transaction_net_merchandise_sales,
    build_item_financials,
    build_return_financials,
    build_overview_metrics,
    parse_transaction_dates,
    revenue_trend,
    revenue_by_category,
)
from src.navigation import render_header_with_nav


st.set_page_config(
    page_title="Overview",
    layout="wide",
    initial_sidebar_state="expanded",
)

PAGE_BG = "#18181B"      # graphite (no blue)
CARD_BG = "#232326"
CARD_BG_2 = "#1C1C1F"
BORDER = "#2F2F33"

TEXT = "#FAFAFA"
MUTED = "#A1A1AA"

# Core identity: growth green (slightly richer than lime)
ACCENT = "#22C55E"       # primary interaction / highlights

SUCCESS = "#16A34A"      # deeper green for confirmed success
DANGER = "#DC2626"
WARNING = "#F59E0B"

LINE_COL = "#F97316"     # contrast for charts

CATEGORY_COLORS = [
    "#22C55E",  # growth green (primary)
    "#4ADE80",  # lighter green (secondary)
    "#F59E0B",  # amber (warnings / mid-performance)
    "#DC2626",  # red (loss)
    "#A78BFA",  # violet (neutral segmentation)
    "#F97316",  # orange (trend contrast)
    "#EAB308",  # yellow (attention)
    "#F43F5E",  # rose (negative variation)
]

st.markdown(
    f"""
    <style>
    .stApp {{
        background: {PAGE_BG};
        color: {TEXT};
    }}

    .block-container {{
        padding-top: 1.0rem;
        padding-bottom: 1.8rem;
    }}

    .section-title {{
        font-size: 1.25rem;
        font-weight: 800;
        margin-bottom: 0.25rem;
        color: {TEXT};
        letter-spacing: 0.2px;
    }}

    .section-subtitle {{
        font-size: 0.9rem;
        color: {MUTED};
        margin-bottom: 0.85rem;
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

    .insight-box {{
        padding: 16px 18px;
        border-radius: 18px;
        border: 1px solid {BORDER};
        background: linear-gradient(180deg, rgba(17,24,39,0.96) 0%, rgba(15,23,42,0.96) 100%);
        box-shadow: 0 2px 10px rgba(0,0,0,0.18);
    }}

    /* Reduce the default white feel in some Streamlit containers */
    div[data-testid="stMetric"] {{
        background: transparent;
    }}

    div[data-testid="stDataFrame"] {{
        border-radius: 14px;
        overflow: hidden;
    }}

    /* Button polish for map mode controls */
    div.stButton > button {{
        border-radius: 12px;
        border: 1px solid {BORDER};
        background: linear-gradient(180deg, rgba(17,24,39,0.95) 0%, rgba(15,23,42,0.95) 100%);
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

CITY_COORDS = {
    "Mumbai": (19.0760, 72.8777),
    "Delhi": (28.7041, 77.1025),
    "Bengaluru": (12.9716, 77.5946),
    "Hyderabad": (17.3850, 78.4867),
    "Pune": (18.5204, 73.8567),
    "Kolkata": (22.5726, 88.3639),
    "Chennai": (13.0827, 80.2707),
    "Ahmedabad": (23.0225, 72.5714),
}


@st.cache_data
def load_all_data():
    return load_data()


@st.cache_data
def get_overview_data():
    events, order_items, products, returns, transactions = load_all_data()
    metrics = build_overview_metrics(events, order_items, products, returns, transactions)
    rev_trend = revenue_trend(transactions)
    cat_rev = revenue_by_category(order_items, transactions=transactions, products=products)
    return events, order_items, products, returns, transactions, metrics, rev_trend, cat_rev


def format_currency(value: float) -> str:
    return f"₹{value:,.2f}"


def compact_currency(value: float) -> str:
    abs_value = abs(value)
    if abs_value >= 1_00_00_000:
        return f"₹{value/1_00_00_000:.2f}Cr"
    if abs_value >= 1_00_000:
        return f"₹{value/1_00_000:.2f}L"
    if abs_value >= 1_000:
        return f"₹{value/1_000:.2f}K"
    return f"₹{value:,.2f}"


def compact_number(value: float) -> str:
    abs_value = abs(value)
    if abs_value >= 1_00_00_000:
        return f"{value/1_00_00_000:.2f}Cr"
    if abs_value >= 1_00_000:
        return f"{value/1_00_000:.2f}L"
    if abs_value >= 1_000:
        return f"{value/1_000:.2f}K"
    return f"{value:,.0f}"


def format_pct(value: float) -> str:
    return f"{value * 100:.2f}%"


def stat_card(
    title: str,
    value: str,
    subtitle: str | None = None,
    subtitle_positive: bool | None = None,
) -> str:
    color = SUCCESS if subtitle_positive is True else DANGER if subtitle_positive is False else MUTED
    arrow = "▲" if subtitle_positive is True else "▼" if subtitle_positive is False else ""
    subtitle_text = f"{arrow} {subtitle}" if arrow else subtitle
    subtitle_html = (
        f'<div style="font-size: 0.82rem; color: {color}; margin-top: 6px;">{subtitle_text}</div>'
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
def build_monthly_snapshot(transactions: pd.DataFrame, returns: pd.DataFrame) -> dict:
    """Compare the latest month-to-date with the same elapsed dates last month."""
    tx = parse_transaction_dates(transactions)
    tx["net_merchandise_sales"] = _transaction_net_merchandise_sales(tx)

    rt = returns.copy()
    raw_return_dates = rt["return_request_date"].astype("string").str.strip()
    rt["return_request_date"] = pd.to_datetime(
        raw_return_dates, format="ISO8601", errors="coerce"
    )
    unresolved = rt["return_request_date"].isna() & raw_return_dates.notna() & raw_return_dates.ne("")
    if unresolved.any():
        rt.loc[unresolved, "return_request_date"] = pd.to_datetime(
            raw_return_dates.loc[unresolved], dayfirst=True, errors="coerce"
        )
    rt["return_request_date"] = rt["return_request_date"].dt.normalize()

    def matched_month_values(
        frame: pd.DataFrame,
        date_column: str,
        value_column: str | None,
        count_column: str | None,
    ) -> dict:
        valid_dates = frame[date_column].dropna()
        if valid_dates.empty:
            return {
                "current": 0.0, "previous": 0.0,
                "current_label": "N/A", "previous_label": "N/A", "change": 0.0,
            }

        latest_date = valid_dates.max().normalize()
        current_start = latest_date.replace(day=1)
        previous_month_end = current_start - pd.Timedelta(days=1)
        previous_start = previous_month_end.replace(day=1)
        previous_end = previous_start + pd.Timedelta(days=min(latest_date.day, previous_month_end.day) - 1)

        def metric_value(start_date: pd.Timestamp, end_date: pd.Timestamp) -> float:
            mask = frame[date_column].between(start_date, end_date, inclusive="both")
            period = frame.loc[mask]
            if value_column is not None:
                return float(pd.to_numeric(period[value_column], errors="coerce").fillna(0).sum())
            if count_column is not None:
                return float(period[count_column].nunique())
            return float(len(period))

        current_value = metric_value(current_start, latest_date)
        previous_value = metric_value(previous_start, previous_end)
        change = None if previous_value == 0 else (current_value - previous_value) / previous_value

        def period_label(start_date: pd.Timestamp, end_date: pd.Timestamp) -> str:
            if start_date.day == 1 and end_date.day == end_date.days_in_month:
                return start_date.strftime("%b %Y")
            return f"{start_date.strftime('%b')} 1–{end_date.day}, {start_date.year}"

        return {
            "current": current_value,
            "previous": previous_value,
            "current_label": period_label(current_start, latest_date),
            "previous_label": period_label(previous_start, previous_end),
            "change": change,
        }

    revenue = matched_month_values(tx, "order_date", "net_merchandise_sales", None)
    orders = matched_month_values(tx, "order_date", None, "order_id")
    returns_monthly = matched_month_values(rt, "return_request_date", None, "return_id")

    return {"revenue": revenue, "orders": orders, "returns": returns_monthly}


@st.cache_data
def build_top_products_table(
    order_items: pd.DataFrame,
    products: pd.DataFrame,
    transactions: pd.DataFrame,
    returns: pd.DataFrame,
) -> pd.DataFrame:
    item_financials = build_item_financials(order_items, products, transactions)
    sold = (
        item_financials.groupby(["product_id", "product_name", "category"], as_index=False)
        .agg(
            orders=("order_id", "nunique"),
            units_sold=("quantity", "sum"),
            net_merchandise_sales=("net_merchandise_sales", "sum"),
        )
    )

    rt = returns.copy()
    if "return_quantity" in rt.columns:
        rt["return_quantity"] = pd.to_numeric(rt["return_quantity"], errors="coerce").fillna(0)
    else:
        rt["return_quantity"] = 1
    returned = (
        rt.groupby("product_id", as_index=False)
        .agg(return_requested_units=("return_quantity", "sum"))
    )

    df = sold.merge(returned, on="product_id", how="left")
    df[["return_requested_units"]] = df[["return_requested_units"]].fillna(0)
    df["return_rate"] = df["return_requested_units"].div(
        df["units_sold"].where(df["units_sold"].ne(0))
    ).fillna(0.0)
    df = df.sort_values(["orders", "net_merchandise_sales"], ascending=[False, False]).head(5).copy()
    df["net_merchandise_sales"] = df["net_merchandise_sales"].map(compact_currency)
    df["return_rate"] = df["return_rate"].map(lambda x: f"{x * 100:.2f}%")
    return df[["product_name", "category", "orders", "net_merchandise_sales", "return_rate"]].rename(
        columns={
            "net_merchandise_sales": "Net Merc Sales",
            "return_rate": "Return Request Rate",
        }
    )


@st.cache_data
def build_profit_scenario(transactions: pd.DataFrame, margin_shift_pp: float) -> pd.DataFrame:
    tx = parse_transaction_dates(transactions)
    tx["net_merchandise_sales"] = _transaction_net_merchandise_sales(tx)
    tx["estimated_cost"] = pd.to_numeric(tx["estimated_cost"], errors="coerce").fillna(0)
    tx["gross_profit"] = tx["net_merchandise_sales"] - tx["estimated_cost"]
    tx["month"] = tx["order_date"].dt.to_period("M").dt.to_timestamp()

    monthly = (
        tx.dropna(subset=["month"])
        .groupby("month", as_index=False)
        .agg(
            revenue=("net_merchandise_sales", "sum"),
            actual_profit=("gross_profit", "sum"),
        )
        .sort_values("month")
    )

    monthly["base_margin"] = monthly.apply(
        lambda row: 0 if row["revenue"] == 0 else row["actual_profit"] / row["revenue"], axis=1
    )
    monthly["adjusted_margin"] = (monthly["base_margin"] + (margin_shift_pp / 100.0)).clip(
        lower=-0.5, upper=0.95
    )
    monthly["adjusted_profit"] = monthly["revenue"] * monthly["adjusted_margin"]

    return monthly


@st.cache_data
def build_region_summary(
    events: pd.DataFrame,
    order_items: pd.DataFrame,
    products: pd.DataFrame,
    transactions: pd.DataFrame,
    returns: pd.DataFrame,
) -> pd.DataFrame:
    evt = events.copy()
    tx = parse_transaction_dates(transactions)
    rt = returns.copy()

    tx["net_merchandise_sales"] = _transaction_net_merchandise_sales(tx)
    tx["estimated_cost"] = pd.to_numeric(tx["estimated_cost"], errors="coerce").fillna(0)
    tx["gross_profit"] = tx["net_merchandise_sales"] - tx["estimated_cost"]

    item_financials = build_item_financials(order_items, products, transactions)

    orders = tx.groupby("region", as_index=False).agg(
        orders=("order_id", "nunique"),
        revenue=("net_merchandise_sales", "sum"),
        profit=("gross_profit", "sum"),
        avg_order_value=("net_merchandise_sales", "mean"),
    )

    sessions = evt.groupby("region", as_index=False).agg(sessions=("session_id", "nunique"))
    visit_sessions = evt.loc[evt["event_type"].eq("visit")].groupby("region", as_index=False).agg(
        visit_sessions=("session_id", "nunique")
    )
    purchase_sessions = evt.loc[evt["event_type"].eq("purchase")].groupby("region", as_index=False).agg(
        purchase_sessions=("session_id", "nunique")
    )
    checkout_start_sessions = evt.loc[evt["event_type"].eq("checkout_start")].groupby("region", as_index=False).agg(
        checkout_start_sessions=("session_id", "nunique")
    )
    checkout_abandon_sessions = evt.loc[evt["event_type"].eq("checkout_abandon")].groupby("region", as_index=False).agg(
        checkout_abandon_sessions=("session_id", "nunique")
    )

    return_financials = build_return_financials(order_items, products, transactions, returns)
    if "return_quantity" in return_financials.columns:
        return_financials["return_quantity"] = pd.to_numeric(
            return_financials["return_quantity"], errors="coerce"
        ).fillna(0)
    else:
        return_financials["return_quantity"] = 1
    returned_items = return_financials.groupby("region", as_index=False).agg(
        returned_units=("return_quantity", "sum"),
        refund_amount=("approved_refund_amount", "sum"),
    )
    if "return_quantity" in rt.columns:
        rt["return_quantity"] = pd.to_numeric(rt["return_quantity"], errors="coerce").fillna(0)
    else:
        rt["return_quantity"] = 1
    pending_refunds = (
        rt.loc[rt["return_status"].astype("string").str.lower().eq("pending")]
        .groupby("region", as_index=False)
        .agg(pending_refunds=("refund_amount", "sum"))
    )

    sold_items = item_financials.groupby("region", as_index=False).agg(
        total_items=("quantity", "sum"),
        product_diversity=("product_id", "nunique"),
    )

    top_category = (
        item_financials.groupby(["region", "category"], as_index=False)["net_merchandise_sales"].sum()
        .sort_values(["region", "net_merchandise_sales"], ascending=[True, False])
        .drop_duplicates("region")
        .rename(columns={"category": "top_category", "net_merchandise_sales": "top_category_revenue"})
    )
    top_product = (
        item_financials.groupby(["region", "product_name"], as_index=False)["net_merchandise_sales"].sum()
        .sort_values(["region", "net_merchandise_sales"], ascending=[True, False])
        .drop_duplicates("region")
        .rename(columns={"product_name": "top_product", "net_merchandise_sales": "top_product_revenue"})
    )
    top_device = (
        evt.groupby(["region", "device_type"], as_index=False)["session_id"].nunique()
        .sort_values(["region", "session_id"], ascending=[True, False])
        .drop_duplicates("region")
        .rename(columns={"device_type": "top_device_type", "session_id": "top_device_sessions"})
    )
    top_source = (
        evt.groupby(["region", "traffic_source"], as_index=False)["session_id"].nunique()
        .sort_values(["region", "session_id"], ascending=[True, False])
        .drop_duplicates("region")
        .rename(columns={"traffic_source": "top_traffic_source", "session_id": "top_traffic_sessions"})
    )

    summary = sessions.merge(orders, on="region", how="outer")
    for frame in [
        visit_sessions, purchase_sessions, checkout_start_sessions, checkout_abandon_sessions,
        returned_items, pending_refunds, sold_items, top_category, top_product, top_device, top_source,
    ]:
        summary = summary.merge(frame, on="region", how="left")

    numeric_fill_cols = [
        "sessions", "orders", "revenue", "profit", "avg_order_value", "visit_sessions",
        "purchase_sessions", "checkout_start_sessions", "checkout_abandon_sessions", "returned_units",
        "refund_amount", "pending_refunds", "total_items", "product_diversity", "top_category_revenue",
        "top_product_revenue", "top_device_sessions", "top_traffic_sessions",
    ]
    for col in numeric_fill_cols:
        if col in summary.columns:
            summary[col] = pd.to_numeric(summary[col], errors="coerce").fillna(0)

    summary["profit_margin"] = summary["profit"].div(summary["revenue"].where(summary["revenue"].ne(0))).fillna(0)
    summary["conversion_rate"] = summary["purchase_sessions"].div(
        summary["visit_sessions"].where(summary["visit_sessions"].ne(0))
    ).fillna(0)
    summary["checkout_abandonment_rate"] = summary["checkout_abandon_sessions"].div(
        summary["checkout_start_sessions"].where(summary["checkout_start_sessions"].ne(0))
    ).fillna(0)
    summary["return_rate"] = summary["returned_units"].div(
        summary["total_items"].where(summary["total_items"].ne(0))
    ).fillna(0)
    summary["top_category_share"] = summary["top_category_revenue"].div(
        summary["revenue"].where(summary["revenue"].ne(0))
    ).fillna(0)

    coords = pd.DataFrame(
        [{"region": city, "lat": lat, "lon": lon} for city, (lat, lon) in CITY_COORDS.items()]
    )
    summary = summary.merge(coords, on="region", how="inner")
    summary["refund_amount"] = summary["refund_amount"].fillna(0)
    summary["pending_refunds"] = summary["pending_refunds"].fillna(0)

    return summary.sort_values("revenue", ascending=False)


@st.cache_data
def build_map_figure(map_df: pd.DataFrame, mode: str) -> go.Figure:
    mode_configs = {
        "Volume": {
            "size": "orders",
            "color": "sessions",
            "color_title": "Sessions",
            "scale": "Tealgrn",
            "subtitle": "Demand intensity",
        },
        "Revenue": {
            "size": "revenue",
            "color": "profit",
            "color_title": "Gross Profit",
            "scale": "Viridis",
            "subtitle": "Commercial quality",
        },
        "Efficiency": {
            "size": "revenue",
            "color": "profit_margin_pct",
            "color_title": "Gross Profit Margin (%)",
            "scale": "Blues",
            "subtitle": "Efficiency",
        },
        "Risk": {
            "size": "orders",
            "color": "return_rate_pct",
            "color_title": "Return Request Unit Rate (%)",
            "scale": "Reds",
            "subtitle": "Risk",
        },
        "Friction": {
            "size": "sessions",
            "color": "checkout_abandonment_rate_pct",
            "color_title": "Checkout Abandonment (%)",
            "scale": "Oranges",
            "subtitle": "Friction",
        },
    }

    cfg = mode_configs[mode]
    plot_df = map_df.copy()

    numeric_cols = [
        "lat",
        "lon",
        "sessions",
        "orders",
        "revenue",
        "profit",
        "profit_margin",
        "return_rate",
        "conversion_rate",
        "checkout_abandonment_rate",
        "refund_amount",
        "pending_refunds",
    ]
    for col in numeric_cols:
        if col in plot_df.columns:
            plot_df[col] = pd.to_numeric(plot_df[col], errors="coerce").fillna(0.0)

    plot_df = plot_df.dropna(subset=["lat", "lon"]).copy()
    # Plot percentage-based color scales as 0–100 values; hover details below
    # continue to use the original fractional rates and render them as percentages.
    plot_df["profit_margin_pct"] = plot_df["profit_margin"] * 100
    plot_df["return_rate_pct"] = plot_df["return_rate"] * 100
    plot_df["checkout_abandonment_rate_pct"] = plot_df["checkout_abandonment_rate"] * 100

    size_col = cfg["size"]
    if plot_df[size_col].fillna(0).sum() == 0:
        plot_df[size_col] = 1

    fig = px.scatter_geo(
        plot_df,
        lat="lat",
        lon="lon",
        size=size_col,
        color=cfg["color"],
        hover_name="region",
        color_continuous_scale=cfg["scale"],
        size_max=42,
        projection="natural earth",
        custom_data=[
            "sessions",
            "orders",
            "revenue",
            "profit",
            "profit_margin",
            "return_rate",
            "conversion_rate",
            "checkout_abandonment_rate",
            "refund_amount",
            "pending_refunds",
            "top_category",
            "top_device_type",
            "top_traffic_source",
            "top_product",
        ],
    )

    fig.update_traces(
        marker=dict(
            line=dict(width=1.2, color="#E2E8F0"),
            opacity=0.92,
        ),
        hovertemplate=(
            "<b>%{hovertext}</b><br>"
            "Sessions: %{customdata[0]:,.0f}<br>"
            "Orders: %{customdata[1]:,.0f}<br>"
            "Net Merchandise Sales: ₹%{customdata[2]:,.2f}<br>"
            "Gross Profit: ₹%{customdata[3]:,.2f}<br>"
            "Gross Profit Margin: %{customdata[4]:.2%}<br>"
            "Return Request Unit Rate: %{customdata[5]:.2%}<br>"
            "Conversion: %{customdata[6]:.2%}<br>"
            "Checkout Abandonment: %{customdata[7]:.2%}<br>"
            "Approved Refund Amount: ₹%{customdata[8]:,.2f}<br>"
            "Pending Refunds: ₹%{customdata[9]:,.2f}<br>"
            "Top Category: %{customdata[10]}<br>"
            "Top Device: %{customdata[11]}<br>"
            "Top Traffic Source: %{customdata[12]}<br>"
            "Top Product: %{customdata[13]}<extra></extra>"
        ),
    )

    fig.update_layout(
        template="plotly_dark",
        height=560,
        margin=dict(l=10, r=10, t=20, b=10),
        coloraxis_colorbar=dict(
            title=cfg["color_title"],
            thickness=14,
            len=0.75,
        ),
        paper_bgcolor=PAGE_BG,
        plot_bgcolor=PAGE_BG,
        font=dict(color=TEXT),
    )

    fig.update_geos(
        showcountries=True,
        countrycolor="#475569",
        showcoastlines=True,
        coastlinecolor="#64748B",
        showland=True,
        landcolor="#111827",
        showocean=True,
        oceancolor="#0B1220",
        showlakes=True,
        lakecolor="#0B1220",
        showframe=False,
        bgcolor=PAGE_BG,
        fitbounds="locations",
        lataxis_range=[6, 30],
        lonaxis_range=[68, 92],
    )

    return fig


def build_region_mode_table(map_df: pd.DataFrame, mode: str) -> pd.DataFrame:
    mode_col = {
        "Volume": "orders",
        "Revenue": "revenue",
        "Efficiency": "profit_margin",
        "Risk": "return_rate",
        "Friction": "checkout_abandonment_rate",
    }[mode]

    cols = [
        "region",
        mode_col,
        "sessions",
        "orders",
        "revenue",
        "profit",
        "profit_margin",
        "return_rate",
        "conversion_rate",
        "checkout_abandonment_rate",
        "top_category",
        "top_device_type",
        "top_traffic_source",
        "top_product",
    ]
    display = map_df.reindex(columns=cols).copy()
    display = display.loc[:, ~display.columns.duplicated()]

    return display.sort_values(mode_col, ascending=False).head(5)


def build_profit_adjustment_chart(monthly_profit: pd.DataFrame, adjustment_pp: float) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=monthly_profit["month"],
            y=monthly_profit["actual_profit"],
            mode="lines+markers",
            name="Actual Gross Profit",
            line=dict(width=3, color=ACCENT),
            marker=dict(size=7, color=ACCENT),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=monthly_profit["month"],
            y=monthly_profit["adjusted_profit"],
            mode="lines+markers",
            name=f"Adjusted Gross Profit ({adjustment_pp:+.1f} pp margin shift)",
            line=dict(width=3, dash="dash", color=WARNING),
            marker=dict(size=7, color=WARNING),
        )
    )
    fig.update_layout(
        template="plotly_dark",
        height=420,
        margin=dict(l=10, r=10, t=30, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        yaxis_title="Gross Profit",
        xaxis_title="Month",
        paper_bgcolor=PAGE_BG,
        plot_bgcolor=PAGE_BG,
        font=dict(color=TEXT),
    )
    fig.update_xaxes(gridcolor="#334155", zerolinecolor="#334155")
    fig.update_yaxes(gridcolor="#334155", zerolinecolor="#334155")
    return fig


def render():
    events, order_items, products, returns, transactions, metrics, rev_trend, cat_rev = get_overview_data()
    monthly_stats = build_monthly_snapshot(transactions, returns)
    top_products = build_top_products_table(order_items, products, transactions, returns)
    region_summary = build_region_summary(events, order_items, products, transactions, returns)

    if "overview_map_mode" not in st.session_state:
        st.session_state.overview_map_mode = "Revenue"

    valid_modes = {"Volume", "Revenue", "Efficiency", "Risk", "Friction"}
    if st.session_state.overview_map_mode not in valid_modes:
        st.session_state.overview_map_mode = "Revenue"

    st.markdown("""
    <style>
    .block-container {
        padding-top: 2.5rem;
        padding-left: 90px;  /* space for nav strip */
    }
    </style>
    """, unsafe_allow_html=True)

    # ----------------------------------------------------------------
    # Project title + page intro
    # ----------------------------------------------------------------
    render_header_with_nav(
        "Intelligent Business Analytics and Funnel Optimization Platform",
        "Overview view: business health, movement, concentration, and regional performance.",
        "Overview",
    )

    st.markdown("<div style='height: 22px;'></div>", unsafe_allow_html=True)
    st.markdown('<div class="section-title">Overview</div>', unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(stat_card("Net Merchandise Sales", compact_currency(metrics["total_revenue"])), unsafe_allow_html=True)
    with c2:
        st.markdown(stat_card("Gross Profit", compact_currency(metrics["total_profit"])), unsafe_allow_html=True)
    with c3:
        st.markdown(stat_card("Total Orders", compact_number(metrics["total_orders"])), unsafe_allow_html=True)
    with c4:
        st.markdown(stat_card("Return Request Rate (Units)", format_pct(metrics["item_return_rate"])), unsafe_allow_html=True)

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    left, right = st.columns([1.55, 1.0], gap="large")
    with left:
        st.markdown('<div class="section-title">Revenue Trend</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-subtitle">Daily merchandise sales after discounts, excluding tax and shipping.</div>',
            unsafe_allow_html=True,
        )
        fig = px.line(rev_trend, x="order_date", y="revenue", markers=True, template="plotly_dark")
        fig.update_traces(line=dict(width=3, color=LINE_COL), marker=dict(size=7, color=LINE_COL))
        fig.update_layout(
            height=410,
            margin=dict(l=10, r=10, t=20, b=10),
            showlegend=False,
            paper_bgcolor=PAGE_BG,
            plot_bgcolor=PAGE_BG,
            font=dict(color=TEXT),
            yaxis_title="Revenue (₹)",
            xaxis_title="Date",
        )
        fig.update_xaxes(gridcolor="#334155", zerolinecolor="#334155")
        fig.update_yaxes(gridcolor="#334155", zerolinecolor="#334155")
        st.plotly_chart(fig, width="stretch")

        st.markdown("<div style='height: 42px;'></div>", unsafe_allow_html=True)
        r1, r2, r3 = st.columns(3)
        revenue = monthly_stats["revenue"]
        orders = monthly_stats["orders"]
        returns_m = monthly_stats["returns"]
        revenue_change_label = (
            "N/A (no prior baseline)"
            if revenue["change"] is None
            else f"{revenue['change'] * 100:.2f}%"
        )
        orders_change_label = (
            "N/A (no prior baseline)"
            if orders["change"] is None
            else f"{orders['change'] * 100:.2f}%"
        )
        returns_change_label = (
            "N/A (no prior baseline)"
            if returns_m["change"] is None
            else f"{returns_m['change'] * 100:.2f}%"
        )

        with r1:
            st.markdown(
                stat_card(
                    f"Monthly Net Sales ({revenue['current_label']})",
                    compact_currency(revenue["current"]),
                    subtitle=(
                        f"Prev ({revenue['previous_label']}): {compact_currency(revenue['previous'])}  |  "
                        f"{revenue_change_label}"
                    ),
                    subtitle_positive=None if revenue["change"] is None else revenue["change"] >= 0,
                ),
                unsafe_allow_html=True,
            )
        with r2:
            st.markdown(
                stat_card(
                    f"Monthly Orders ({orders['current_label']})",
                    compact_number(orders["current"]),
                    subtitle=(
                        f"Prev ({orders['previous_label']}): {compact_number(orders['previous'])}  |  "
                        f"{orders_change_label}"
                    ),
                    subtitle_positive=None if orders["change"] is None else orders["change"] >= 0,
                ),
                unsafe_allow_html=True,
            )
        with r3:
            st.markdown(
                stat_card(
                    f"Return Requests ({returns_m['current_label']})",
                    compact_number(returns_m["current"]),
                    subtitle=(
                        f"Prev ({returns_m['previous_label']}): {compact_number(returns_m['previous'])}  |  "
                        f"{returns_change_label}"
                    ),
                    subtitle_positive=None if returns_m["change"] is None else returns_m["change"] <= 0,
                ),
                unsafe_allow_html=True,
            )

    with right:
        st.markdown('<div class="section-title">Revenue by Category</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-subtitle">Category share of merchandise sales after allocated order discounts.</div>', unsafe_allow_html=True)
        cat_fig = px.pie(
            cat_rev,
            names="category",
            values="revenue",
            hole=0.58,
            template="plotly_dark",
            color_discrete_sequence=CATEGORY_COLORS,
        )
        cat_fig.update_traces(textinfo="percent+label", textfont=dict(color="white"), marker=dict(line=dict(color=PAGE_BG, width=2)))
        cat_fig.update_layout(
            height=360,
            margin=dict(l=10, r=10, t=20, b=10),
            showlegend=True,
            paper_bgcolor=PAGE_BG,
            plot_bgcolor=PAGE_BG,
            font=dict(color=TEXT),
            legend=dict(
                orientation="v",
                yanchor="middle",
                y=0.5,
                xanchor="left",
                x=1.02,
                font=dict(color=TEXT),
            ),
        )
        st.plotly_chart(cat_fig, width="stretch")

        st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
        st.markdown('<div class="section-title">Top 5 Products</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-subtitle">Product-level order counts, net merchandise sales, and requested return units as a share of units sold.</div>', unsafe_allow_html=True)
        st.dataframe(top_products, width="stretch", hide_index=True)

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    st.markdown('<div class="section-title">Profit Scenario Analysis</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-subtitle">Adjust gross profit margin by percentage points; the latest month may be month-to-date.</div>',
        unsafe_allow_html=True,
    )
    margin_shift_pp = st.slider(
        "Profit margin adjustment (percentage points)",
        min_value=-10.0,
        max_value=10.0,
        value=2.0,
        step=0.5,
        help="Positive values simulate a margin improvement; negative values simulate margin compression.",
    )
    profit_scenario = build_profit_adjustment_chart(build_profit_scenario(transactions, margin_shift_pp), margin_shift_pp)
    st.plotly_chart(profit_scenario, width="stretch")

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    st.markdown('<div class="section-title">Regional Geo Performance Map</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-subtitle">A single geo map whose size, color, and meaning change with the selected mode.</div>',
        unsafe_allow_html=True,
    )

    map_left, map_right = st.columns([1.55, 0.65], gap="large")
    with map_right:
        st.markdown("**Map Mode**")
        st.caption("Click a button to change the narrative of the same map.")
        for mode in ["Volume", "Revenue", "Efficiency", "Risk", "Friction"]:
            if st.button(mode, width="stretch", key=f"map_mode_{mode}"):
                st.session_state.overview_map_mode = mode

        current_mode = st.session_state.overview_map_mode
        mode_config = {
            "Volume": "Shows where demand is concentrated.",
            "Revenue": "Shows where commercial value is concentrated.",
            "Efficiency": "Shows where demand turns into profit efficiently.",
            "Risk": "Shows where requested return units are highest relative to units sold.",
            "Friction": "Shows where checkout friction is highest.",
        }
        st.info(f"**Current Mode:** {current_mode}\n\n{mode_config[current_mode]}")

        current_metric_col = {
            "Volume": "orders",
            "Revenue": "revenue",
            "Efficiency": "profit_margin",
            "Risk": "return_rate",
            "Friction": "checkout_abandonment_rate",
        }[current_mode]

        top_region_row = region_summary.sort_values(current_metric_col, ascending=False).iloc[0]
        current_metric_label = {
            "orders": "Orders",
            "revenue": "Net Merchandise Sales",
            "profit_margin": "Gross Profit Margin",
            "return_rate": "Return Request Unit Rate",
            "checkout_abandonment_rate": "Checkout Abandonment Rate",
        }[current_metric_col]
        st.metric(f"Top Region by {current_metric_label}", top_region_row["region"])

    with map_left:
        current_mode = st.session_state.overview_map_mode
        fig = build_map_figure(region_summary, current_mode)
        st.plotly_chart(fig, width="stretch")

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    st.markdown('<div class="section-title">Regional Signals</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-subtitle">Mode-specific regional drill-down. The table changes with the map mode and spans the full width.</div>',
        unsafe_allow_html=True,
    )

    preview = build_region_mode_table(region_summary, st.session_state.overview_map_mode)
    if not preview.empty:
        preview_display = preview.copy()

        if "revenue" in preview_display.columns:
            preview_display["revenue"] = pd.to_numeric(preview_display["revenue"], errors="coerce").fillna(0).map(format_currency)
        if "profit" in preview_display.columns:
            preview_display["profit"] = pd.to_numeric(preview_display["profit"], errors="coerce").fillna(0).map(format_currency)
        if "profit_margin" in preview_display.columns:
            preview_display["profit_margin"] = pd.to_numeric(preview_display["profit_margin"], errors="coerce").fillna(0).map(format_pct)
        if "return_rate" in preview_display.columns:
            preview_display["return_rate"] = pd.to_numeric(preview_display["return_rate"], errors="coerce").fillna(0).map(format_pct)
            preview_display = preview_display.rename(columns={"return_rate": "return_request_unit_rate"})
        if "conversion_rate" in preview_display.columns:
            preview_display["conversion_rate"] = pd.to_numeric(preview_display["conversion_rate"], errors="coerce").fillna(0).map(format_pct)
        if "checkout_abandonment_rate" in preview_display.columns:
            preview_display["checkout_abandonment_rate"] = pd.to_numeric(preview_display["checkout_abandonment_rate"], errors="coerce").fillna(0).map(format_pct)

        st.dataframe(preview_display, width="stretch", hide_index=True)

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    st.markdown('<div class="section-title">Key Summary</div>', unsafe_allow_html=True)

    s1, s2 = st.columns(2)
    with s1:
        st.markdown(
            stat_card(
                "Top Category by Net Merchandise Sales",
                metrics["top_category_by_revenue"],
                subtitle=format_currency(metrics["top_category_revenue"]),
                subtitle_positive=True,
            ),
            unsafe_allow_html=True,
        )
        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
        st.markdown(
            stat_card(
                "Average Order Value",
                compact_currency(metrics["average_order_value"]),
                subtitle=f"{metrics['average_items_per_order']:.2f} items / order",
                subtitle_positive=True,
            ),
            unsafe_allow_html=True,
        )
    with s2:
        revenue_change = metrics["revenue_change_last_7_days"]
        profit_change = metrics["profit_change_last_7_days"]
        st.markdown(
            stat_card(
                "Net Merchandise Sales Change vs Previous 7 Days",
                f"{revenue_change * 100:.2f}%",
                subtitle="Compared with the previous 7-day period",
                subtitle_positive=revenue_change >= 0,
            ),
            unsafe_allow_html=True,
        )
        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
        st.markdown(
            stat_card(
                "Gross Profit Change vs Previous 7 Days",
                f"{profit_change * 100:.2f}%",
                subtitle="Compared with the previous 7-day period",
                subtitle_positive=profit_change >= 0,
            ),
            unsafe_allow_html=True,
        )
        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

render()