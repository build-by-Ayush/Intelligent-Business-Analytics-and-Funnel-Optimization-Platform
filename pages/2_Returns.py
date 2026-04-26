from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.data_loader import load_data
from src.navigation import render_header_with_nav


st.set_page_config(
    page_title="Returns Analysis",
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

DEVICE_PALETTE = ["#22C55E", "#4ADE80", "#A78BFA", "#F97316", "#EAB308"]
SOURCE_PALETTE = ["#F97316", "#F59E0B", "#EAB308", "#F43F5E", "#A78BFA", "#22C55E"]
REGION_PALETTE = ["#DC2626", "#F97316", "#F59E0B", "#22C55E", "#A78BFA", "#4ADE80", "#EAB308", "#F43F5E"]
LAG_PALETTE = ["#F97316", "#22C55E", "#A78BFA"]

st.markdown(
    f"""
    <style>
    .stApp {{
        background: {PAGE_BG};
        color: {TEXT};
        overflow-x: hidden;
    }}

    .block-container {{
        padding-top: 3.2rem;
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
        letter-spacing: 0.2px;
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

    .risk-strip {{
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

    .risk-strip-head {{
        max-width: 1200px;
        margin: 0 auto 10px auto;
    }}

    .risk-strip-title {{
        font-size: 1rem;
        font-weight: 800;
        color: {TEXT};
        line-height: 1.2;
    }}

    .risk-strip-subtitle {{
        font-size: 0.85rem;
        color: {MUTED};
        margin-top: 3px;
    }}

    .risk-strip-grid {{
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 16px;
        max-width: 1200px;
        margin: 0 auto;
    }}

    .risk-item {{
        padding: 12px 14px;
        border-radius: 12px;
        background: #18181B;
        border: 1px solid rgba(63, 63, 70, 0.6);
    }}

    .risk-label {{
        font-size: 0.82rem;
        color: {MUTED};
        margin-bottom: 6px;
    }}

    .risk-value {{
        font-size: 1.18rem;
        font-weight: 800;
        color: {TEXT};
        line-height: 1.15;
    }}

    .risk-note {{
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
def parse_return_dates(returns: pd.DataFrame) -> pd.DataFrame:
    df = returns.copy()
    df["order_timestamp_dt"] = pd.to_datetime(df["order_timestamp"], errors="coerce")
    df["return_request_dt"] = pd.to_datetime(df["return_request_date"], errors="coerce")
    df["return_date_dt"] = pd.to_datetime(df["return_date"], errors="coerce")
    df["order_to_request_days"] = (df["return_request_dt"] - df["order_timestamp_dt"]).dt.total_seconds() / 86400.0
    df["request_to_resolution_days"] = (df["return_date_dt"] - df["return_request_dt"]).dt.total_seconds() / 86400.0
    df["order_to_resolution_days"] = (df["return_date_dt"] - df["order_timestamp_dt"]).dt.total_seconds() / 86400.0
    return df


@st.cache_data
def build_return_trend(transactions: pd.DataFrame, returns: pd.DataFrame) -> pd.DataFrame:
    tx = transactions.copy()
    tx["order_date_dt"] = pd.to_datetime(tx["order_date"], dayfirst=True, errors="coerce")
    rt = parse_return_dates(returns)

    max_date = max(tx["order_date_dt"].max(), rt["return_request_dt"].max())
    if pd.isna(max_date):
        return pd.DataFrame(columns=["date", "orders", "returns", "refund_amount", "return_rate"])

    start_date = (max_date.to_period("M") - 3).to_timestamp()
    tx = tx.loc[tx["order_date_dt"] >= start_date].copy()
    rt = rt.loc[rt["return_request_dt"] >= start_date].copy()

    daily_orders = tx.groupby(tx["order_date_dt"].dt.date)["order_id"].nunique().reset_index(name="orders")
    daily_orders.rename(columns={"order_date_dt": "date"}, inplace=True)
    daily_orders["date"] = pd.to_datetime(daily_orders["date"])

    daily_returns = rt.groupby(rt["return_request_dt"].dt.date)["return_id"].nunique().reset_index(name="returns")
    daily_returns.rename(columns={"return_request_dt": "date"}, inplace=True)
    daily_returns["date"] = pd.to_datetime(daily_returns["date"])

    daily_refunds = rt.groupby(rt["return_request_dt"].dt.date)["refund_amount"].sum().reset_index(name="refund_amount")
    daily_refunds.rename(columns={"return_request_dt": "date"}, inplace=True)
    daily_refunds["date"] = pd.to_datetime(daily_refunds["date"])

    trend = daily_orders.merge(daily_returns, on="date", how="outer").merge(daily_refunds, on="date", how="outer").fillna(0)
    trend["return_rate"] = trend.apply(lambda row: safe_divide(row["returns"], row["orders"]), axis=1)
    trend = trend.sort_values("date")
    return trend


@st.cache_data
def build_return_reason_distribution(returns: pd.DataFrame) -> pd.DataFrame:
    return (
        returns.groupby("return_reason", as_index=False)
        .agg(count=("return_id", "nunique"), refund_amount=("refund_amount", "sum"))
        .sort_values("count", ascending=False)
    )


@st.cache_data
def bundle_reason(reason: str) -> str:
    reason = str(reason).lower().strip()

    fit_size = {"size issue", "wrong size", "fabric not as expected"}
    damage_quality = {
        "product damaged", "damaged item", "damaged in transit", "packaging damaged",
        "defective item", "build quality issue", "assembly issue", "product quality issue"
    }
    expectation_mismatch = {"wrong shade", "color mismatch", "wrong item delivered", "changed mind"}
    compatibility = {"compatibility issue"}
    sensitivity = {"skin irritation"}

    if reason in fit_size:
        return "Fit / Size Issues"
    if reason in damage_quality:
        return "Damage / Quality Issues"
    if reason in expectation_mismatch:
        return "Expectation Mismatch"
    if reason in compatibility:
        return "Compatibility / Utility Mismatch"
    if reason in sensitivity:
        return "Sensitivity / Reaction"
    return "Other"


@st.cache_data
def build_reason_category_heatmap(returns: pd.DataFrame) -> pd.DataFrame:
    df = returns.copy()
    df["reason_group"] = df["return_reason"].map(bundle_reason)
    matrix = pd.crosstab(df["reason_group"], df["category"]).astype(float)
    return matrix


@st.cache_data
def build_segment_return_rates(transactions: pd.DataFrame, returns: pd.DataFrame, dimension: str) -> pd.DataFrame:
    tx = transactions[["order_id", dimension]].drop_duplicates().copy()
    tx[dimension] = tx[dimension].astype(str)

    total_orders = tx.groupby(dimension)["order_id"].nunique().reset_index(name="total_orders")
    returned_orders = (
        returns[["order_id"]]
        .drop_duplicates()
        .merge(tx, on="order_id", how="left")
        .groupby(dimension)["order_id"]
        .nunique()
        .reset_index(name="returned_orders")
    )

    df = total_orders.merge(returned_orders, on=dimension, how="left").fillna(0)
    df["return_rate"] = df.apply(lambda row: safe_divide(row["returned_orders"], row["total_orders"]), axis=1)
    return df.sort_values("return_rate", ascending=False)


@st.cache_data
def build_product_return_table(order_items: pd.DataFrame, returns: pd.DataFrame, transactions: pd.DataFrame) -> pd.DataFrame:
    oi = order_items.copy()
    tx = transactions[["order_id", "estimated_profit", "order_date"]].copy()
    tx["order_date"] = pd.to_datetime(tx["order_date"], dayfirst=True, errors="coerce")

    order_item_value = oi.groupby("order_id")["total_price"].transform("sum")
    oi["item_share"] = oi["total_price"] / order_item_value.replace(0, pd.NA)

    oi = oi.merge(tx, on="order_id", how="left")
    oi["allocated_profit"] = oi["estimated_profit"].fillna(0) * oi["item_share"].fillna(0)

    ret = returns[["order_item_id", "refund_amount", "return_reason", "return_status", "return_request_date", "return_date"]].copy()
    ret["return_request_date"] = pd.to_datetime(ret["return_request_date"], errors="coerce")
    ret["return_date"] = pd.to_datetime(ret["return_date"], errors="coerce")

    item_level = oi.merge(ret, on="order_item_id", how="left")
    item_level["is_returned"] = item_level["return_reason"].notna()
    item_level["return_cycle_days"] = (item_level["return_date"] - item_level["order_date"]).dt.total_seconds() / 86400.0

    grouped = (
        item_level.groupby(["product_id", "product_name", "category", "brand"], as_index=False)
        .agg(
            purchases=("order_item_id", "nunique"),
            returns=("is_returned", "sum"),
            revenue=("total_price", "sum"),
            refund_amount=("refund_amount", "sum"),
            allocated_profit=("allocated_profit", "sum"),
            avg_return_cycle_days=("return_cycle_days", "mean"),
        )
    )

    grouped["return_rate"] = grouped.apply(lambda row: safe_divide(row["returns"], row["purchases"]), axis=1)
    grouped["net_profit_after_returns"] = grouped["allocated_profit"].fillna(0) - grouped["refund_amount"].fillna(0)

    return grouped.sort_values(["return_rate", "refund_amount"], ascending=[False, False])


@st.cache_data
def build_return_lag_table(returns: pd.DataFrame) -> pd.DataFrame:
    rt = parse_return_dates(returns)
    lag = rt[["order_to_request_days", "request_to_resolution_days", "order_to_resolution_days"]].copy()
    lag = lag.melt(var_name="lag_type", value_name="days").dropna()
    lag["lag_type"] = lag["lag_type"].map(
        {
            "order_to_request_days": "Order → Request",
            "request_to_resolution_days": "Request → Resolution",
            "order_to_resolution_days": "Order → Resolution",
        }
    )
    return lag


@st.cache_data
def build_top_risks(return_products: pd.DataFrame, return_reasons: pd.DataFrame, return_segments: pd.DataFrame) -> dict:
    top_product = "N/A"
    top_category = "N/A"
    top_reason = "N/A"
    top_segment = "N/A"

    if not return_products.empty:
        row = return_products.iloc[0]
        top_product = f"{row['product_name']} ({row['return_rate'] * 100:.1f}%)"
        top_category = row["category"]

    if not return_reasons.empty:
        top_reason = return_reasons.iloc[0]["return_reason"]

    if not return_segments.empty:
        seg_row = return_segments.iloc[0]
        top_segment = f"{seg_row.iloc[0]} ({seg_row['return_rate'] * 100:.1f}%)"

    return {
        "top_product": top_product,
        "top_category": top_category,
        "top_reason": top_reason,
        "top_segment": top_segment,
    }


@st.cache_data
def build_order_level_metrics(order_items: pd.DataFrame, returns: pd.DataFrame, transactions: pd.DataFrame) -> dict:
    total_orders = transactions["order_id"].nunique()
    total_revenue = float(transactions["total_amount"].sum())
    total_refund_amount = float(returns["refund_amount"].sum())
    refund_rate = safe_divide(total_refund_amount, total_revenue)
    return_rate = safe_divide(returns["order_item_id"].nunique(), order_items["order_item_id"].nunique())
    net_revenue_after_returns = total_revenue - total_refund_amount
    pending = returns[returns["return_status"].eq("pending")].copy()
    pending_exposure = 0.0
    if not pending.empty:
        pending_join = pending.merge(order_items[["order_item_id", "total_price"]], on="order_item_id", how="left")
        pending_exposure = float(pending_join["total_price"].fillna(0).sum())

    return {
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "total_refund_amount": total_refund_amount,
        "refund_rate": refund_rate,
        "return_rate": return_rate,
        "net_revenue_after_returns": net_revenue_after_returns,
        "pending_exposure": pending_exposure,
    }


def render():
    events, order_items, products, returns, transactions = load_all_data()
    return_trend = build_return_trend(transactions, returns)
    return_reason_dist = build_return_reason_distribution(returns)
    reason_category_matrix = build_reason_category_heatmap(returns)
    product_table = build_product_return_table(order_items, returns, transactions)
    lag_table = build_return_lag_table(returns)
    order_metrics = build_order_level_metrics(order_items, returns, transactions)

    device_return_rates = build_segment_return_rates(transactions, returns, "device_type")
    source_return_rates = build_segment_return_rates(transactions, returns, "traffic_source")
    region_return_rates = build_segment_return_rates(transactions, returns, "region")

    top_risks = build_top_risks(product_table, return_reason_dist, device_return_rates)

    total_returned_items = int(returns["order_item_id"].nunique())
    total_sold_items = int(order_items["order_item_id"].nunique())
    return_rate = safe_divide(total_returned_items, total_sold_items)

    total_revenue = order_metrics["total_revenue"]
    total_refund_amount = order_metrics["total_refund_amount"]
    refund_rate = order_metrics["refund_rate"]
    net_revenue_after_returns = order_metrics["net_revenue_after_returns"]
    pending_exposure = order_metrics["pending_exposure"]

    rt = parse_return_dates(returns)
    median_cycle = float(rt["order_to_resolution_days"].median()) if not rt.empty else 0.0
    p75_cycle = float(rt["order_to_resolution_days"].quantile(0.75)) if not rt.empty else 0.0

    approved = int((returns["return_status"] == "approved").sum())
    pending_count = int((returns["return_status"] == "pending").sum())
    completed_refunds = int((returns["return_status"].eq("approved") & returns["refund_amount"].gt(0)).sum())

    render_header_with_nav(
        "Returns Analysis",
        "Return quality, financial leakage, operational lag, and product risk diagnostics.",
        "Returns",
    )
    st.markdown("<div style='height: 22px;'></div>", unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(stat_card("Return Rate", format_pct(return_rate)), unsafe_allow_html=True)
    with c2:
        st.markdown(stat_card("Refund Rate", format_pct(refund_rate)), unsafe_allow_html=True)
    with c3:
        st.markdown(stat_card("Net Revenue After Returns", compact_currency(net_revenue_after_returns)), unsafe_allow_html=True)
    with c4:
        st.markdown(stat_card("Pending Refund Exposure", compact_currency(pending_exposure)), unsafe_allow_html=True)

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    c5, c6, c7, c8 = st.columns(4)
    with c5:
        st.markdown(stat_card("Median Return Cycle", f"{median_cycle:.1f} days"), unsafe_allow_html=True)
    with c6:
        st.markdown(stat_card("P75 Return Cycle", f"{p75_cycle:.1f} days"), unsafe_allow_html=True)
    with c7:
        st.markdown(stat_card("Approved Returns", compact_number(approved)), unsafe_allow_html=True)
    with c8:
        st.markdown(stat_card("Pending Returns", compact_number(pending_count)), unsafe_allow_html=True)

    st.write("")

    st.markdown('<div class="section-title">Return Activity Trend</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-subtitle">Daily return rate over the latest four months. The trend uses the same dark analytical language as the rest of the dashboard.</div>',
        unsafe_allow_html=True,
    )
    if not return_trend.empty:
        trend_fig = px.line(
            return_trend,
            x="date",
            y="return_rate",
            markers=True,
            template="plotly_dark",
            hover_data={"orders": True, "returns": True, "refund_amount": ":.2f", "return_rate": ":.2%"},
        )
        trend_fig.update_traces(line=dict(width=3, color=LINE_COL), marker=dict(size=7, color=LINE_COL))
        trend_fig.update_layout(
            height=430,
            margin=dict(l=10, r=10, t=20, b=10),
            yaxis_tickformat=".0%",
            paper_bgcolor=PAGE_BG,
            plot_bgcolor=PAGE_BG,
            font=dict(color=TEXT),
        )
        trend_fig.update_xaxes(gridcolor="#3F3F46", zerolinecolor="#3F3F46")
        trend_fig.update_yaxes(gridcolor="#3F3F46", zerolinecolor="#3F3F46")
        st.plotly_chart(trend_fig, use_container_width=True)

    st.write("")

    left2, right2 = st.columns([1.0, 1.15], gap="large")
    with left2:
        st.markdown('<div class="section-title">Top Return Reasons</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-subtitle">Top five individual reasons driving the highest return volume.</div>',
            unsafe_allow_html=True,
        )
        if not return_reason_dist.empty:
            top_reasons = return_reason_dist.head(5).copy()
            reasons_fig = px.bar(
                top_reasons,
                x="count",
                y="return_reason",
                orientation="h",
                template="plotly_dark",
                text="count",
                color="return_reason",
                color_discrete_sequence=CATEGORY_COLORS[: len(top_reasons)],
            )
            reasons_fig.update_traces(
                textposition="outside",
                textfont=dict(color=TEXT),
                marker_line_color=PAGE_BG,
                marker_line_width=1.0,
                cliponaxis=False,
            )
            reasons_fig.update_layout(
                height=390,
                margin=dict(l=10, r=10, t=20, b=10),
                showlegend=False,
                paper_bgcolor=PAGE_BG,
                plot_bgcolor=PAGE_BG,
                font=dict(color=TEXT),
                xaxis_title="Return Count",
                yaxis_title="",
            )
            reasons_fig.update_xaxes(gridcolor="#3F3F46", zerolinecolor="#3F3F46")
            reasons_fig.update_yaxes(gridcolor="#3F3F46", zerolinecolor="#3F3F46")
            st.plotly_chart(reasons_fig, use_container_width=True)

    with right2:
        st.markdown('<div class="section-title">Bundled Reason × Category Heatmap</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-subtitle">Bundled reasons show where the same issue type clusters across categories.</div>',
            unsafe_allow_html=True,
        )
        if not reason_category_matrix.empty:
            heat_fig = px.imshow(
                reason_category_matrix,
                text_auto=True,
                aspect="auto",
                color_continuous_scale="Oranges",
                template="plotly_dark",
                labels=dict(x="Category", y="Reason Group", color="Count"),
            )
            heat_fig.update_layout(
                height=390,
                margin=dict(l=10, r=10, t=20, b=10),
                paper_bgcolor=PAGE_BG,
                plot_bgcolor=PAGE_BG,
                font=dict(color=TEXT),
            )
            st.plotly_chart(heat_fig, use_container_width=True)

    st.write("")

    st.markdown('<div class="section-title">Product Return Diagnostics</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-subtitle">Products ranked by return intensity, refund leakage, and profit erosion.</div>',
        unsafe_allow_html=True,
    )
    if not product_table.empty:
        prod_display = product_table.copy()
        prod_display["purchases"] = prod_display["purchases"].map(compact_number)
        prod_display["returns"] = prod_display["returns"].map(compact_number)
        prod_display["return_rate"] = prod_display["return_rate"].map(format_pct)
        prod_display["avg_return_cycle_days"] = prod_display["avg_return_cycle_days"].map(lambda x: f"{x:.1f}" if pd.notna(x) else "-")
        for col in ["revenue", "refund_amount", "allocated_profit", "net_profit_after_returns"]:
            prod_display[col] = prod_display[col].map(compact_currency)

        prod_display = prod_display[[
            "product_name",
            "category",
            "brand",
            "purchases",
            "returns",
            "return_rate",
            "revenue",
            "refund_amount",
            "allocated_profit",
            "net_profit_after_returns",
            "avg_return_cycle_days",
        ]].head(8)

        st.dataframe(prod_display, use_container_width=True, hide_index=True)

    st.write("")

    st.markdown('<div class="section-title">Segment Risk View</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-subtitle">Return rate by device, traffic source, and region.</div>',
        unsafe_allow_html=True,
    )
    seg_left, seg_mid, seg_right = st.columns(3, gap="large")

    with seg_left:
        if not device_return_rates.empty:
            fig = px.bar(
                device_return_rates,
                x="device_type",
                y="return_rate",
                text=device_return_rates["return_rate"].map(lambda x: f"{x * 100:.1f}%"),
                template="plotly_dark",
                color="device_type",
                color_discrete_sequence=DEVICE_PALETTE,
            )
            fig.update_traces(
                textposition="outside",
                textfont=dict(color=TEXT),
                marker_line_color=PAGE_BG,
                marker_line_width=1.0,
                cliponaxis=False,
            )
            fig.update_layout(
                height=320,
                paper_bgcolor=PAGE_BG,
                plot_bgcolor=PAGE_BG,
                font=dict(color=TEXT),
                margin=dict(l=10, r=10, t=20, b=10),
                showlegend=False,
                yaxis_tickformat=".0%",
                yaxis_title="Return Rate",
            )
            fig.update_xaxes(gridcolor="#3F3F46", zerolinecolor="#3F3F46")
            fig.update_yaxes(gridcolor="#3F3F46", zerolinecolor="#3F3F46")
            st.plotly_chart(fig, use_container_width=True)

    with seg_mid:
        if not source_return_rates.empty:
            fig = px.bar(
                source_return_rates,
                x="traffic_source",
                y="return_rate",
                text=source_return_rates["return_rate"].map(lambda x: f"{x * 100:.1f}%"),
                template="plotly_dark",
                color="traffic_source",
                color_discrete_sequence=SOURCE_PALETTE,
            )
            fig.update_traces(
                textposition="outside",
                textfont=dict(color=TEXT),
                marker_line_color=PAGE_BG,
                marker_line_width=1.0,
                cliponaxis=False,
            )
            fig.update_layout(
                height=320,
                paper_bgcolor=PAGE_BG,
                plot_bgcolor=PAGE_BG,
                font=dict(color=TEXT),
                margin=dict(l=10, r=10, t=20, b=10),
                showlegend=False,
                yaxis_tickformat=".0%",
                yaxis_title="Return Rate",
            )
            fig.update_xaxes(gridcolor="#3F3F46", zerolinecolor="#3F3F46")
            fig.update_yaxes(gridcolor="#3F3F46", zerolinecolor="#3F3F46")
            st.plotly_chart(fig, use_container_width=True)

    with seg_right:
        if not region_return_rates.empty:
            fig = px.bar(
                region_return_rates,
                x="region",
                y="return_rate",
                text=region_return_rates["return_rate"].map(lambda x: f"{x * 100:.1f}%"),
                template="plotly_dark",
                color="region",
                color_discrete_sequence=REGION_PALETTE,
            )
            fig.update_traces(
                textposition="outside",
                textfont=dict(color=TEXT),
                marker_line_color=PAGE_BG,
                marker_line_width=1.0,
                cliponaxis=False,
            )
            fig.update_layout(
                height=320,
                paper_bgcolor=PAGE_BG,
                plot_bgcolor=PAGE_BG,
                font=dict(color=TEXT),
                margin=dict(l=10, r=10, t=20, b=10),
                showlegend=False,
                yaxis_tickformat=".0%",
                yaxis_title="Return Rate",
            )
            fig.update_xaxes(gridcolor="#3F3F46", zerolinecolor="#3F3F46")
            fig.update_yaxes(gridcolor="#3F3F46", zerolinecolor="#3F3F46")
            st.plotly_chart(fig, use_container_width=True)

    st.write("")

    st.markdown('<div class="section-title">Return Lag Distribution</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-subtitle">How long it takes users to request and complete returns. Median values are annotated in the chart.</div>',
        unsafe_allow_html=True,
    )
    if not lag_table.empty:
        summary = (
            lag_table.groupby("lag_type", as_index=False)
            .agg(median_days=("days", "median"), p75_days=("days", lambda s: s.quantile(0.75)), observations=("days", "size"))
            .sort_values("median_days", ascending=True)
        )

        fig = go.Figure()
        for i, lag_name in enumerate(summary["lag_type"].tolist()):
            vals = lag_table.loc[lag_table["lag_type"] == lag_name, "days"].dropna()
            color = LAG_PALETTE[i % len(LAG_PALETTE)]
            fig.add_trace(
                go.Box(
                    x=vals,
                    y=[lag_name] * len(vals),
                    orientation="h",
                    name=lag_name,
                    boxpoints=False,
                    showlegend=False,
                    marker_color=color,
                    line_color=color,
                    fillcolor=color,
                )
            )

        fig.add_trace(
            go.Scatter(
                x=summary["median_days"],
                y=summary["lag_type"],
                mode="markers+text",
                text=summary["median_days"].map(lambda x: f"{x:.1f}"),
                textposition="middle right",
                textfont=dict(size=10, color=TEXT),
                marker=dict(size=4, color="rgba(0,0,0,0)"),
                showlegend=False,
                hoverinfo="skip",
            )
        )

        fig.update_layout(
            height=360,
            template="plotly_dark",
            margin=dict(l=10, r=10, t=20, b=10),
            xaxis_title="Days",
            yaxis_title="",
            paper_bgcolor=PAGE_BG,
            plot_bgcolor=PAGE_BG,
            font=dict(color=TEXT),
        )
        fig.update_xaxes(gridcolor="#3F3F46", zerolinecolor="#3F3F46")
        fig.update_yaxes(gridcolor="#3F3F46", zerolinecolor="#3F3F46")
        st.plotly_chart(fig, use_container_width=True)

    st.write("")

    st.markdown(
        f"""
        <div class="risk-strip">
            <div class="risk-strip-head">
                <div class="risk-strip-title">Top Risks Right Now</div>
                <div class="risk-strip-subtitle">Compact monitoring strip for the highest return-risk signals.</div>
            </div>
            <div class="risk-strip-grid">
                <div class="risk-item">
                    <div class="risk-label">Highest-Risk Product</div>
                    <div class="risk-value">{top_risks["top_product"]}</div>
                    <div class="risk-note">Highest return intensity in the catalog</div>
                </div>
                <div class="risk-item">
                    <div class="risk-label">Worst Category</div>
                    <div class="risk-value">{top_risks["top_category"]}</div>
                    <div class="risk-note">Category with the strongest leakage</div>
                </div>
                <div class="risk-item">
                    <div class="risk-label">Most Common Reason</div>
                    <div class="risk-value">{top_risks["top_reason"]}</div>
                    <div class="risk-note">Most frequent cause behind returns</div>
                </div>
                <div class="risk-item">
                    <div class="risk-label">Highest-Risk Segment</div>
                    <div class="risk-value">{top_risks["top_segment"]}</div>
                    <div class="risk-note">Segment with the worst return rate</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")
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

    rt = parse_return_dates(returns).copy()
    rt = rt.dropna(subset=["return_request_dt"])

    if not rt.empty:
        rt["date"] = rt["return_request_dt"].dt.normalize()

        max_date = rt["date"].max()
        recent_start = max_date - pd.Timedelta(days=6)
        baseline_start = max_date - pd.Timedelta(days=27)

        prod_daily = (
            rt.groupby(["product_name", "date"], as_index=False)
            .agg(
                returns=("return_id", "nunique"),
                refund_amount=("refund_amount", "sum"),
            )
        )

        recent_prod = prod_daily.loc[prod_daily["date"] >= recent_start].copy()
        baseline_prod = prod_daily.loc[
            (prod_daily["date"] >= baseline_start) & (prod_daily["date"] < recent_start)
        ].copy()

        if not recent_prod.empty:
            recent_agg = (
                recent_prod.groupby("product_name", as_index=False)
                .agg(
                    recent_returns=("returns", "sum"),
                    recent_refund=("refund_amount", "sum"),
                )
            )

            baseline_agg = (
                baseline_prod.groupby("product_name", as_index=False)
                .agg(
                    baseline_returns=("returns", "sum"),
                    baseline_refund=("refund_amount", "sum"),
                )
            )

            prod_shift = recent_agg.merge(baseline_agg, on="product_name", how="left").fillna(0)
            prod_shift["recent_daily_avg"] = prod_shift["recent_returns"] / 7.0
            prod_shift["baseline_daily_avg"] = prod_shift["baseline_returns"] / 21.0
            prod_shift["lift"] = prod_shift["recent_daily_avg"] - prod_shift["baseline_daily_avg"]

            candidate = prod_shift.loc[
                (prod_shift["recent_returns"] >= 2) & (prod_shift["lift"] > 0)
            ].sort_values(["lift", "recent_returns"], ascending=False)

            if not candidate.empty:
                top_prod = candidate.iloc[0]["product_name"]

                series = (
                    prod_daily.loc[prod_daily["product_name"] == top_prod, ["date", "returns", "refund_amount"]]
                    .set_index("date")
                    .reindex(pd.date_range(baseline_start, max_date, freq="D"), fill_value=0)
                    .reset_index()
                )
                series.columns = ["date", "returns", "refund_amount"]

                recent_total = int(prod_shift.loc[prod_shift["product_name"] == top_prod, "recent_returns"].iloc[0])
                baseline_total = float(prod_shift.loc[prod_shift["product_name"] == top_prod, "baseline_returns"].iloc[0])

                body = (
                    f"<strong>{top_prod}</strong> is showing a recent rise in return activity. "
                    f"The last 7 days recorded <strong>{recent_total}</strong> returns, compared with a baseline of "
                    f"<strong>{baseline_total:.0f}</strong> over the prior 21 days. "
                    f"This suggests a possible product-quality, expectation, or packaging issue."
                )

                def render_product_chart(series=series):
                    fig = px.line(
                        series,
                        x="date",
                        y="returns",
                        markers=True,
                        template="plotly_dark",
                        hover_data={"refund_amount": ":.2f"},
                    )
                    fig.update_traces(line=dict(width=3, color=LINE_COL), marker=dict(size=6, color=LINE_COL))
                    fig.update_layout(
                        height=290,
                        margin=dict(l=10, r=10, t=20, b=10),
                        xaxis_title="Date",
                        yaxis_title="Return Count",
                        paper_bgcolor=PAGE_BG,
                        plot_bgcolor=PAGE_BG,
                        font=dict(color=TEXT),
                    )
                    fig.update_xaxes(gridcolor="#3F3F46", zerolinecolor="#3F3F46")
                    fig.update_yaxes(gridcolor="#3F3F46", zerolinecolor="#3F3F46")
                    st.plotly_chart(fig, use_container_width=True)

                add_insight(
                    priority=100,
                    title="Product Return Spike",
                    body=body,
                    chart_renderer=render_product_chart,
                )

    segment_sources = [
        ("Device Type", device_return_rates),
        ("Traffic Source", source_return_rates),
        ("Region", region_return_rates),
    ]

    best_label = None
    best_df = None
    best_spread = 0.0

    for label, df in segment_sources:
        if df is None or df.empty:
            continue
        spread = float(df["return_rate"].max() - df["return_rate"].min())
        if spread > best_spread:
            best_spread = spread
            best_label = label
            best_df = df.copy()

    if best_df is not None and best_spread >= 0.08:
        worst_row = best_df.sort_values("return_rate", ascending=False).iloc[0]
        best_row = best_df.sort_values("return_rate", ascending=True).iloc[0]

        body = (
            f"Return performance varies across <strong>{best_label.lower()}</strong>. "
            f"The highest-risk segment is <strong>{worst_row.iloc[0]}</strong> at "
            f"<strong>{worst_row['return_rate'] * 100:.1f}%</strong>, while the lowest-risk segment is "
            f"<strong>{best_row.iloc[0]}</strong> at <strong>{best_row['return_rate'] * 100:.1f}%</strong>. "
            f"This points to acquisition-quality, delivery, or expectation differences between segments."
        )

        def render_segment_chart(best_df=best_df, best_label=best_label):
            palette = DEVICE_PALETTE if best_label == "Device Type" else SOURCE_PALETTE if best_label == "Traffic Source" else REGION_PALETTE
            fig = px.bar(
                best_df.sort_values("return_rate", ascending=True),
                x=best_df.columns[0],
                y="return_rate",
                text=best_df["return_rate"].map(lambda x: f"{x * 100:.1f}%"),
                template="plotly_dark",
                color=best_df.columns[0],
                color_discrete_sequence=palette,
            )
            fig.update_traces(
                textposition="outside",
                textfont=dict(color=TEXT),
                marker_line_color=PAGE_BG,
                marker_line_width=1.0,
                cliponaxis=False,
            )
            fig.update_layout(
                height=290,
                margin=dict(l=10, r=10, t=20, b=10),
                xaxis_title=best_label,
                yaxis_title="Return Rate",
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
            title=f"{best_label} Risk Gap",
            body=body,
            chart_renderer=render_segment_chart,
        )

    if not rt.empty:
        rt["reason_group"] = rt["return_reason"].map(bundle_reason)

        recent_reason = rt.loc[rt["date"] >= recent_start].copy()
        baseline_reason = rt.loc[(rt["date"] >= baseline_start) & (rt["date"] < recent_start)].copy()

        if not recent_reason.empty and not baseline_reason.empty:
            recent_counts = recent_reason["reason_group"].value_counts(normalize=True).reset_index()
            recent_counts.columns = ["reason_group", "recent_share"]

            baseline_counts = baseline_reason["reason_group"].value_counts(normalize=True).reset_index()
            baseline_counts.columns = ["reason_group", "baseline_share"]

            reason_shift = recent_counts.merge(baseline_counts, on="reason_group", how="outer").fillna(0)
            reason_shift["share_change"] = reason_shift["recent_share"] - reason_shift["baseline_share"]

            top_shift = reason_shift.sort_values("share_change", ascending=False).iloc[0]

            if float(top_shift["share_change"]) >= 0.12:
                body = (
                    f"The return mix is shifting toward <strong>{top_shift['reason_group']}</strong>. "
                    f"Its share increased by <strong>{top_shift['share_change'] * 100:.1f} percentage points</strong> "
                    f"versus the prior period. This usually indicates a recurring root cause rather than isolated noise."
                )

                add_insight(
                    priority=80,
                    title="Return Reason Shift",
                    body=body,
                    chart_renderer=None,
                )

    if not lag_table.empty:
        lag_summary = (
            lag_table.groupby("lag_type", as_index=False)
            .agg(
                median_days=("days", "median"),
                p75_days=("days", lambda s: s.quantile(0.75)),
                observations=("days", "size"),
            )
            .sort_values("median_days", ascending=False)
        )

        slowest_lag = lag_summary.iloc[0]
        if float(slowest_lag["median_days"]) >= 3.0:
            body = (
                f"Return processing is slowest at <strong>{slowest_lag['lag_type']}</strong>. "
                f"The median delay is <strong>{slowest_lag['median_days']:.1f} days</strong>, with p75 at "
                f"<strong>{slowest_lag['p75_days']:.1f} days</strong>. "
                f"This suggests operational friction in return handling."
            )

            def render_lag_chart(lag_summary=lag_summary):
                fig = go.Figure()
                for i, row in lag_summary.sort_values("median_days", ascending=True).iterrows():
                    color = LAG_PALETTE[i % len(LAG_PALETTE)]
                    vals = lag_table.loc[lag_table["lag_type"] == row["lag_type"], "days"].dropna()
                    fig.add_trace(
                        go.Box(
                            x=vals,
                            y=[row["lag_type"]] * len(vals),
                            orientation="h",
                            name=row["lag_type"],
                            boxpoints=False,
                            showlegend=False,
                            marker_color=color,
                            line_color=color,
                            fillcolor=color,
                        )
                    )

                fig.add_trace(
                    go.Scatter(
                        x=lag_summary.sort_values("median_days", ascending=True)["median_days"],
                        y=lag_summary.sort_values("median_days", ascending=True)["lag_type"],
                        mode="markers+text",
                        text=lag_summary.sort_values("median_days", ascending=True)["median_days"].map(lambda x: f"{x:.1f}"),
                        textposition="middle right",
                        textfont=dict(size=10, color=TEXT),
                        marker=dict(size=4, color="rgba(0,0,0,0)"),
                        showlegend=False,
                        hoverinfo="skip",
                    )
                )

                fig.update_layout(
                    height=290,
                    template="plotly_dark",
                    margin=dict(l=10, r=10, t=20, b=10),
                    xaxis_title="Median Days",
                    yaxis_title="",
                    paper_bgcolor=PAGE_BG,
                    plot_bgcolor=PAGE_BG,
                    font=dict(color=TEXT),
                )
                fig.update_xaxes(gridcolor="#3F3F46", zerolinecolor="#3F3F46")
                fig.update_yaxes(gridcolor="#3F3F46", zerolinecolor="#3F3F46")
                st.plotly_chart(fig, use_container_width=True)

            add_insight(
                priority=70,
                title="Operational Delay",
                body=body,
                chart_renderer=render_lag_chart,
            )

    insights = sorted(insights, key=lambda x: x["priority"], reverse=True)[:4]

    text_insights = [x for x in insights if x["chart_renderer"] is None]
    chart_insights = [x for x in insights if x["chart_renderer"] is not None]

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

    if not text_insights and not chart_insights:
        st.info("No major return anomalies detected at the moment.")
    
render()