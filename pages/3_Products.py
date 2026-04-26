from __future__ import annotations

import math

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.data_loader import load_data
from src.navigation import render_header_with_nav


st.set_page_config(
    page_title="Product Analysis",
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
LINE_COL_2 = "#16EEE7"

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

PRODUCT_PALETTE = ["#3B82F6", "#22C55E", "#A78BFA", "#F97316", "#F59E0B", "#F43F5E"]

st.markdown(
    f"""
    <style>
    .stApp {{
        background: {PAGE_BG};
        color: {TEXT};
        overflow-x: hidden;
    }}

    .block-container {{
        padding-top: 3.5rem;
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

    .product-strip {{
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

    .product-strip-head {{
        max-width: 1200px;
        margin: 0 auto 10px auto;
    }}

    .product-strip-title {{
        font-size: 1rem;
        font-weight: 800;
        color: {TEXT};
        line-height: 1.2;
    }}

    .product-strip-subtitle {{
        font-size: 0.85rem;
        color: {MUTED};
        margin-top: 3px;
    }}

    .product-strip-grid {{
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 16px;
        max-width: 1200px;
        margin: 0 auto;
    }}

    .product-item {{
        padding: 12px 14px;
        border-radius: 12px;
        background: #18181B;
        border: 1px solid rgba(63, 63, 70, 0.6);
    }}

    .product-label {{
        font-size: 0.82rem;
        color: {MUTED};
        margin-bottom: 6px;
    }}

    .product-value {{
        font-size: 1.18rem;
        font-weight: 800;
        color: {TEXT};
        line-height: 1.15;
    }}

    .product-note {{
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


def pretty_metric_label(metric: str) -> str:
    mapping = {
        "revenue": "Revenue",
        "profit": "Profit",
        "orders": "Orders",
        "units_sold": "Units Sold",
        "return_rate": "Return Rate",
    }
    return mapping.get(metric, metric.replace("_", " ").title())


def stat_card(title: str, value: str, subtitle: str | None = None, subtitle_positive: bool | None = None) -> str:
    color = SUCCESS if subtitle_positive else DANGER
    arrow = "▲" if subtitle_positive else "▼"
    subtitle_html = (
        f'<div style="font-size: 0.80rem; color: {color}; margin-top: 6px;">{arrow} {subtitle}</div>'
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


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return "#{:02X}{:02X}{:02X}".format(*rgb)


def mix_with_white(hex_color: str, amount: float) -> str:
    r, g, b = hex_to_rgb(hex_color)
    r = round(r + (255 - r) * amount)
    g = round(g + (255 - g) * amount)
    b = round(b + (255 - b) * amount)
    return rgb_to_hex((r, g, b))


def prettify_category_name(name: str) -> str:
    return str(name).strip()


@st.cache_data
def build_item_level_table(order_items: pd.DataFrame, returns: pd.DataFrame, transactions: pd.DataFrame) -> pd.DataFrame:
    oi = order_items.copy()
    tx = transactions[["order_id", "estimated_profit", "order_date", "total_amount"]].copy()
    tx["order_date"] = pd.to_datetime(tx["order_date"], dayfirst=True, errors="coerce")

    oi = oi.merge(tx, on="order_id", how="left")

    order_total = oi.groupby("order_id")["total_price"].transform("sum")
    oi["item_share"] = oi["total_price"] / order_total.replace(0, pd.NA)
    oi["allocated_profit"] = oi["estimated_profit"].fillna(0) * oi["item_share"].fillna(0)

    ret = returns[["order_item_id", "return_quantity", "refund_amount", "return_reason", "return_status", "return_request_date", "return_date"]].copy()
    ret["return_quantity"] = ret["return_quantity"].fillna(0)
    ret["refund_amount"] = ret["refund_amount"].fillna(0)
    ret["return_request_date"] = pd.to_datetime(ret["return_request_date"], errors="coerce")
    ret["return_date"] = pd.to_datetime(ret["return_date"], errors="coerce")

    item_level = oi.merge(ret, on="order_item_id", how="left")
    item_level["return_quantity"] = item_level["return_quantity"].fillna(0)
    item_level["refund_amount"] = item_level["refund_amount"].fillna(0)
    item_level["month"] = item_level["order_date"].dt.to_period("M").dt.to_timestamp()
    item_level["is_returned"] = item_level["return_quantity"] > 0

    return item_level


@st.cache_data
def build_product_health(item_level: pd.DataFrame) -> pd.DataFrame:
    df = (
        item_level.groupby(["product_id", "product_name", "category", "subcategory", "brand"], as_index=False)
        .agg(
            orders=("order_id", "nunique"),
            units_sold=("quantity", "sum"),
            revenue=("total_price", "sum"),
            profit=("allocated_profit", "sum"),
            returned_units=("return_quantity", "sum"),
            refund_amount=("refund_amount", "sum"),
            latest_order=("order_date", "max"),
        )
    )

    df["profit_margin"] = df.apply(lambda row: safe_divide(row["profit"], row["revenue"]), axis=1)
    df["return_rate"] = df.apply(lambda row: safe_divide(row["returned_units"], row["units_sold"]), axis=1)
    df["net_profit_after_returns"] = df["profit"] - df["refund_amount"]
    df["net_margin_after_returns"] = df.apply(lambda row: safe_divide(row["net_profit_after_returns"], row["revenue"]), axis=1)

    return df.sort_values(["revenue", "profit"], ascending=[False, False])


@st.cache_data
def build_monthly_metric(item_level: pd.DataFrame, metric: str) -> pd.DataFrame:
    base = item_level.copy()

    if metric == "revenue":
        out = base.groupby("month", as_index=False)["total_price"].sum().rename(columns={"total_price": "value"})
    elif metric == "profit":
        out = base.groupby("month", as_index=False)["allocated_profit"].sum().rename(columns={"allocated_profit": "value"})
    elif metric == "orders":
        out = base.groupby("month", as_index=False)["order_id"].nunique().rename(columns={"order_id": "value"})
    elif metric == "units_sold":
        out = base.groupby("month", as_index=False)["quantity"].sum().rename(columns={"quantity": "value"})
    elif metric == "return_rate":
        grouped = base.groupby("month", as_index=False).agg(units_sold=("quantity", "sum"), returned_units=("return_quantity", "sum"))
        grouped["value"] = grouped.apply(lambda row: safe_divide(row["returned_units"], row["units_sold"]), axis=1)
        out = grouped[["month", "value"]]
    else:
        raise ValueError(f"Unsupported metric: {metric}")

    return out.sort_values("month")


@st.cache_data
def build_category_summary(item_level: pd.DataFrame, metric: str, top_n_categories: int = 4) -> pd.DataFrame:
    metric_map = {
        "revenue": "total_price",
        "profit": "allocated_profit",
        "units_sold": "quantity",
    }
    base_col = metric_map[metric]
    top_categories = (
        item_level.groupby("category")[base_col]
        .sum()
        .sort_values(ascending=False)
        .head(top_n_categories)
        .index.tolist()
    )
    df = item_level[item_level["category"].isin(top_categories)].copy()
    out = df.groupby(["category", "subcategory"], as_index=False)[base_col].sum().rename(columns={base_col: "value"})
    out = out.sort_values("value", ascending=False)
    return out


@st.cache_data
def build_category_month_table(item_level: pd.DataFrame, metric: str, top_n_categories: int = 4) -> pd.DataFrame:
    metric_map = {
        "revenue": "total_price",
        "profit": "allocated_profit",
        "units_sold": "quantity",
    }
    base_col = metric_map[metric]
    top_categories = (
        item_level.groupby("category")[base_col].sum().sort_values(ascending=False).head(top_n_categories).index.tolist()
    )
    df = item_level[item_level["category"].isin(top_categories)].copy()
    return (
        df.groupby(["month", "category"], as_index=False)[base_col]
        .sum()
        .rename(columns={base_col: "value"})
        .sort_values(["month", "category"])
    )


@st.cache_data
def build_target_achievement(item_level: pd.DataFrame, target_metric: str) -> tuple[float, float, float, pd.DataFrame, str]:
    monthly = build_monthly_metric(item_level, target_metric)
    if monthly.empty:
        return 0.0, 0.0, 0.0, monthly, target_metric

    current_value = float(monthly.iloc[-1]["value"])
    benchmark_value = float(monthly.iloc[:-1]["value"].mean()) if len(monthly) > 1 else current_value
    achievement = safe_divide(current_value, benchmark_value) * 100
    return current_value, benchmark_value, achievement, monthly, target_metric


@st.cache_data
def build_top_products_table(product_health: pd.DataFrame, metric: str, top_n: int) -> pd.DataFrame:
    sort_map = {
        "revenue": "revenue",
        "profit": "profit",
        "profit_margin": "profit_margin",
        "return_rate": "return_rate",
        "units_sold": "units_sold",
    }
    return product_health.sort_values(sort_map[metric], ascending=False).head(top_n).copy()


@st.cache_data
def build_scatter_data(product_health: pd.DataFrame) -> pd.DataFrame:
    return product_health.copy()


@st.cache_data
def build_key_signals(product_health: pd.DataFrame) -> dict:
    if product_health.empty:
        return {
            "top_revenue_product": "N/A",
            "top_profit_product": "N/A",
            "top_margin_product": "N/A",
            "top_return_risk_product": "N/A",
        }

    top_revenue = product_health.sort_values("revenue", ascending=False).iloc[0]
    top_profit = product_health.sort_values("profit", ascending=False).iloc[0]
    top_margin = product_health.sort_values("profit_margin", ascending=False).iloc[0]
    top_return_risk = product_health.sort_values("return_rate", ascending=False).iloc[0]

    return {
        "top_revenue_product": f"{top_revenue['product_name']}",
        "top_profit_product": f"{top_profit['product_name']}",
        "top_margin_product": f"{top_margin['product_name']}",
        "top_return_risk_product": f"{top_return_risk['product_name']}",
    }


@st.cache_data
def format_currency(value: float) -> str:
    return f"₹{value:,.2f}"


@st.cache_data
def format_compact_number(value: float) -> str:
    abs_value = abs(value)
    if abs_value >= 1_00_00_000:
        return f"{value/1_00_00_000:.2f}Cr"
    if abs_value >= 1_00_000:
        return f"{value/1_00_000:.2f}L"
    if abs_value >= 1_000:
        return f"{value/1_000:.2f}K"
    return f"{value:,.0f}"


def build_category_topline(item_level: pd.DataFrame, metric: str, top_n_categories: int = 4) -> pd.DataFrame:
    metric_map = {
        "revenue": "total_price",
        "profit": "allocated_profit",
        "units_sold": "quantity",
    }
    base_col = metric_map[metric]
    top_categories = (
        item_level.groupby("category")[base_col].sum().sort_values(ascending=False).head(top_n_categories).index.tolist()
    )
    return (
        item_level[item_level["category"].isin(top_categories)]
        .groupby(["month", "category"], as_index=False)[base_col]
        .sum()
        .rename(columns={base_col: "value"})
        .sort_values(["month", "category"])
    )


def build_category_treemap(category_summary_df: pd.DataFrame) -> go.Figure:
    if category_summary_df.empty:
        return go.Figure()

    base_palette = [
        "#3B82F6",
        "#22C55E",
        "#A78BFA",
        "#F97316",
        "#14B8A6",
        "#EAB308",
        "#F43F5E",
        "#60A5FA",
    ]

    categories = category_summary_df["category"].drop_duplicates().tolist()
    category_color_map = {}
    for idx, cat in enumerate(categories):
        category_color_map[cat] = base_palette[idx % len(base_palette)]

    ids = []
    labels = []
    parents = []
    values = []
    colors = []
    hovertext = []

    grouped = category_summary_df.groupby("category", sort=False)

    for cat, grp in grouped:
        cat_total = float(grp["value"].sum())
        cat_color = category_color_map[cat]

        ids.append(cat)
        labels.append(prettify_category_name(cat))
        parents.append("")
        values.append(cat_total)
        colors.append(cat_color)
        hovertext.append(f"{cat}<br>Total: {cat_total:,.2f}")

        grp = grp.sort_values("value", ascending=False).reset_index(drop=True)
        n = len(grp)

        for i, row in grp.iterrows():
            sub = str(row["subcategory"])
            val = float(row["value"])
            shade = mix_with_white(cat_color, 0.18 + (0.38 * (i / max(n - 1, 1))))
            ids.append(f"{cat}::{sub}")
            labels.append(prettify_category_name(sub))
            parents.append(cat)
            values.append(val)
            colors.append(shade)
            hovertext.append(f"{cat} → {sub}<br>Value: {val:,.2f}")

    fig = go.Figure(
        go.Treemap(
            ids=ids,
            labels=labels,
            parents=parents,
            values=values,
            branchvalues="total",
            marker=dict(
                colors=colors,
                line=dict(color=PAGE_BG, width=1.5),
            ),
            textinfo="label+value",
            hovertemplate="%{customdata}<extra></extra>",
            customdata=hovertext,
        )
    )

    fig.update_traces(
        textfont=dict(color=TEXT, size=13),
    )

    fig.update_layout(
        height=420,
        template="plotly_dark",
        paper_bgcolor=PAGE_BG,
        plot_bgcolor=PAGE_BG,
        font=dict(color=TEXT),
        margin=dict(l=10, r=10, t=20, b=10),
    )
    return fig


def render():
    events, order_items, products, returns, transactions = load_all_data()
    item_level = build_item_level_table(order_items, returns, transactions)
    product_health = build_product_health(item_level)
    key_signals = build_key_signals(product_health)

    st.sidebar.title("Product Controls")
    target_metric = st.sidebar.selectbox(
        "Target metric",
        ["revenue", "profit", "orders"],
        index=0,
        help="Used for the target attainment gauge.",
    )
    ranking_metric = st.sidebar.selectbox(
        "Ranking metric",
        ["revenue", "profit", "profit_margin", "return_rate", "units_sold"],
        index=0,
        help="Controls the product health table sorting.",
    )
    trend_metric = st.sidebar.selectbox(
        "Trend metric",
        ["revenue", "profit", "orders", "units_sold", "return_rate"],
        index=0,
        help="Controls the monthly performance trend.",
    )
    category_metric = st.sidebar.selectbox(
        "Category metric",
        ["revenue", "profit", "units_sold"],
        index=0,
        help="Controls category contribution visuals.",
    )
    top_n = st.sidebar.slider("Top products shown", 5, 15, 10)

    current_value, benchmark_value, target_achievement, target_monthly, target_label = build_target_achievement(item_level, target_metric)
    trend_df = build_monthly_metric(item_level, trend_metric)
    category_summary_df = build_category_summary(item_level, category_metric)
    category_month_df = build_category_topline(item_level, category_metric)
    rank_df = build_top_products_table(product_health, ranking_metric, top_n)
    scatter_df = build_scatter_data(product_health)

    total_revenue = float(product_health["revenue"].sum())
    total_profit = float(product_health["profit"].sum())
    profit_margin = safe_divide(total_profit, total_revenue)
    return_rate = safe_divide(float(product_health["returned_units"].sum()), float(product_health["units_sold"].sum()))

    metric_title = pretty_metric_label(trend_metric)
    category_title = pretty_metric_label(category_metric)
    target_title = pretty_metric_label(target_metric)

    render_header_with_nav(
        "Product Analysis",
        "Product performance, profitability, return risk, and category contribution.",
        "Products",
    )
    st.markdown("<div style='height: 22px;'></div>", unsafe_allow_html=True)

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown(stat_card("Total Revenue", compact_currency(total_revenue)), unsafe_allow_html=True)
    with c2:
        st.markdown(stat_card("Total Profit", compact_currency(total_profit)), unsafe_allow_html=True)
    with c3:
        st.markdown(stat_card("Profit Margin %", f"{profit_margin * 100:.2f}%"), unsafe_allow_html=True)
    with c4:
        st.markdown(stat_card("Return Rate %", f"{return_rate * 100:.2f}%"), unsafe_allow_html=True)
    with c5:
        st.markdown(
            stat_card(
                "Target Achievement %",
                f"{target_achievement:.1f}%",
                f"Current {target_title} vs monthly benchmark",
                subtitle_positive=target_achievement >= 100,
            ),
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    left, right = st.columns([0.9, 1.6], gap="large")
    with left:
        st.markdown('<div class="section-title">Target Attainment</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="section-subtitle">{target_title} performance in the latest month vs the historical monthly benchmark.</div>',
            unsafe_allow_html=True,
        )
        max_axis = max(150.0, math.ceil(max(target_achievement, 100.0) * 1.2 / 10.0) * 10.0)
        gauge = go.Figure(
            go.Indicator(
                mode="gauge+number+delta",
                value=target_achievement,
                number={"suffix": "%"},
                delta={"reference": 100, "relative": True, "valueformat": ".1f"},
                title={"text": ""},
                gauge={
                    "axis": {"range": [0, max_axis]},
                    "bar": {"color": ACCENT},
                    "steps": [
                        {"range": [0, 80], "color": "#2A2A2D"},
                        {"range": [80, 100], "color": "#323236"},
                        {"range": [100, max_axis], "color": "#14361F"},
                    ],
                    "threshold": {"line": {"color": DANGER, "width": 4}, "thickness": 0.75, "value": 100},
                },
            )
        )
        gauge.update_layout(
            height=300,
            template="plotly_dark",
            paper_bgcolor=PAGE_BG,
            plot_bgcolor=PAGE_BG,
            font=dict(color=TEXT),
            margin=dict(l=10, r=10, t=0, b=10),
        )
        st.plotly_chart(gauge, use_container_width=True)

    with right:
        st.markdown(f'<div class="section-title">Monthly {metric_title} Trend</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="section-subtitle">Switch between revenue, profit, order count, units sold, and return rate.</div>',
            unsafe_allow_html=True,
        )
        if not trend_df.empty:
            trend_plot = trend_df.copy()
            if trend_metric == "return_rate":
                trend_plot["value_label"] = trend_plot["value"].map(lambda x: f"{x * 100:.1f}%")
                fig = px.line(
                    trend_plot,
                    x="month",
                    y="value",
                    markers=True,
                    template="plotly_dark",
                    hover_data={"value_label": True},
                )
                fig.update_yaxes(tickformat=".0%")
            else:
                fig = px.line(trend_plot, x="month", y="value", markers=True, template="plotly_dark")
                fig.update_yaxes(title=metric_title)

            fig.update_traces(line=dict(width=3, color=LINE_COL_2), marker=dict(size=7, color=LINE_COL_2))
            fig.update_layout(
                height=360,
                margin=dict(l=10, r=10, t=30, b=10),
                showlegend=False,
                paper_bgcolor=PAGE_BG,
                plot_bgcolor=PAGE_BG,
                font=dict(color=TEXT),
                xaxis_title="Month",
            )
            fig.update_xaxes(gridcolor="#3F3F46", zerolinecolor="#3F3F46")
            fig.update_yaxes(gridcolor="#3F3F46", zerolinecolor="#3F3F46")
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    left2, right2 = st.columns([1.0, 1.05], gap="large")
    with left2:
        st.markdown('<div class="section-title">Category / Subcategory Contribution</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="section-subtitle">Contribution structure for the top categories, measured by {category_title.lower()}.</div>',
            unsafe_allow_html=True,
        )
        if not category_summary_df.empty:
            fig = build_category_treemap(category_summary_df)
            st.plotly_chart(fig, use_container_width=True)

    with right2:
        st.markdown('<div class="section-title">Revenue vs Profit</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-subtitle">Bubble size = units sold, color = return rate. This identifies stars, risks, and weak products.</div>',
            unsafe_allow_html=True,
        )
        if not scatter_df.empty:
            fig = px.scatter(
                scatter_df,
                x="revenue",
                y="profit",
                size="units_sold",
                color="return_rate",
                hover_name="product_name",
                hover_data={
                    "category": True,
                    "subcategory": True,
                    "brand": True,
                    "profit_margin": ":.2%",
                    "return_rate": ":.2%",
                    "net_profit_after_returns": ":.2f",
                    "revenue": ":.2f",
                    "profit": ":.2f",
                },
                template="plotly_dark",
                color_continuous_scale="Oranges",
            )
            fig.update_traces(marker=dict(line=dict(color=PAGE_BG, width=1.0), opacity=0.92))
            fig.update_layout(
                height=420,
                margin=dict(l=10, r=10, t=20, b=10),
                paper_bgcolor=PAGE_BG,
                plot_bgcolor=PAGE_BG,
                font=dict(color=TEXT),
                xaxis_title="Revenue",
                yaxis_title="Profit",
            )
            fig.update_xaxes(gridcolor="#3F3F46", zerolinecolor="#3F3F46")
            fig.update_yaxes(gridcolor="#3F3F46", zerolinecolor="#3F3F46")
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    st.markdown(f'<div class="section-title">Monthly {category_title} Contribution Over Time</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Monthly contribution of the top categories for the selected metric.</div>', unsafe_allow_html=True)
    if not category_month_df.empty:
        fig = px.area(
            category_month_df,
            x="month",
            y="value",
            color="category",
            template="plotly_dark",
            color_discrete_sequence=PRODUCT_PALETTE[: len(category_month_df["category"].drop_duplicates())],
        )
        fig.update_traces(line=dict(width=2))
        fig.update_layout(
            height=380,
            margin=dict(l=10, r=10, t=20, b=10),
            paper_bgcolor=PAGE_BG,
            plot_bgcolor=PAGE_BG,
            font=dict(color=TEXT),
            yaxis_title=category_title,
            xaxis_title="Month",
        )
        fig.update_xaxes(gridcolor="#3F3F46", zerolinecolor="#3F3F46")
        fig.update_yaxes(gridcolor="#3F3F46", zerolinecolor="#3F3F46")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    st.markdown('<div class="section-title">Product Health Table</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Compact view of the products driving value and risk.</div>', unsafe_allow_html=True)
    if not product_health.empty:
        table = build_top_products_table(product_health, ranking_metric, top_n).copy()
        display = table[[
            "product_name",
            "category",
            "subcategory",
            "brand",
            "orders",
            "units_sold",
            "revenue",
            "profit",
            "profit_margin",
            "return_rate",
            "refund_amount",
            "net_profit_after_returns",
        ]].copy()

        display["orders"] = display["orders"].map(compact_number)
        display["units_sold"] = display["units_sold"].map(compact_number)
        display["revenue"] = display["revenue"].map(compact_currency)
        display["profit"] = display["profit"].map(compact_currency)
        display["profit_margin"] = display["profit_margin"].map(lambda x: f"{x:.2%}")
        display["return_rate"] = display["return_rate"].map(lambda x: f"{x:.2%}")
        display["refund_amount"] = display["refund_amount"].map(compact_currency)
        display["net_profit_after_returns"] = display["net_profit_after_returns"].map(compact_currency)

        st.dataframe(display, use_container_width=True, hide_index=True)

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    st.markdown(
        f"""
        <div class="product-strip">
            <div class="product-strip-head">
                <div class="product-strip-title">Key Product Segments</div>
                <div class="product-strip-subtitle">Compact product signal strip for the strongest value and risk markers.</div>
            </div>
            <div class="product-strip-grid">
                <div class="product-item">
                    <div class="product-label">Top Revenue Product</div>
                    <div class="product-value">{key_signals["top_revenue_product"]}</div>
                    <div class="product-note">Highest contribution by revenue</div>
                </div>
                <div class="product-item">
                    <div class="product-label">Top Profit Product</div>
                    <div class="product-value">{key_signals["top_profit_product"]}</div>
                    <div class="product-note">Highest contribution by profit</div>
                </div>
                <div class="product-item">
                    <div class="product-label">Highest Margin Product</div>
                    <div class="product-value">{key_signals["top_margin_product"]}</div>
                    <div class="product-note">Strongest efficiency signal</div>
                </div>
                <div class="product-item">
                    <div class="product-label">Highest Return Risk Product</div>
                    <div class="product-value">{key_signals["top_return_risk_product"]}</div>
                    <div class="product-note">Most exposed to post-sale leakage</div>
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

    monthly_product = (
        item_level.groupby(["month", "product_id", "product_name", "category", "subcategory", "brand"], as_index=False)
        .agg(
            revenue=("total_price", "sum"),
            profit=("allocated_profit", "sum"),
            units_sold=("quantity", "sum"),
            returned_units=("return_quantity", "sum"),
        )
        .sort_values("month")
    )

    monthly_category = (
        item_level.groupby(["month", "category"], as_index=False)
        .agg(
            revenue=("total_price", "sum"),
            profit=("allocated_profit", "sum"),
            units_sold=("quantity", "sum"),
        )
        .sort_values("month")
    )

    months = sorted([m for m in monthly_product["month"].dropna().unique()])
    if len(months) >= 2:
        latest_month = months[-1]
        baseline_months = months[-4:-1] if len(months) >= 4 else months[:-1]

        recent_prod = monthly_product.loc[monthly_product["month"] == latest_month].copy()
        baseline_prod = monthly_product.loc[monthly_product["month"].isin(baseline_months)].copy()

        if not recent_prod.empty and not baseline_prod.empty:
            recent_agg = (
                recent_prod.groupby(["product_name", "category", "subcategory", "brand"], as_index=False)
                .agg(recent_revenue=("revenue", "sum"))
            )

            baseline_agg = (
                baseline_prod.groupby(["product_name", "category", "subcategory", "brand"], as_index=False)
                .agg(
                    baseline_revenue=("revenue", "mean"),
                    baseline_std=("revenue", "std"),
                )
            )

            prod_shift = recent_agg.merge(
                baseline_agg,
                on=["product_name", "category", "subcategory", "brand"],
                how="left",
            ).fillna(0)

            prod_shift["drop_pct"] = prod_shift.apply(
                lambda row: safe_divide(row["baseline_revenue"] - row["recent_revenue"], row["baseline_revenue"]),
                axis=1,
            )

            prod_shift["stability"] = prod_shift.apply(
                lambda row: safe_divide(row["baseline_std"], row["baseline_revenue"]),
                axis=1,
            )

            prod_candidates = prod_shift.loc[
                (prod_shift["baseline_revenue"] > 0) &
                (prod_shift["drop_pct"] >= 0.30)
            ].sort_values(["drop_pct", "baseline_revenue"], ascending=[False, False])

            if not prod_candidates.empty:
                top_prod = prod_candidates.iloc[0]
                series = (
                    monthly_product.loc[
                        monthly_product["product_name"] == top_prod["product_name"],
                        ["month", "revenue"]
                    ]
                    .groupby("month", as_index=False)["revenue"]
                    .sum()
                    .set_index("month")
                    .reindex(pd.date_range(min(months), max(months), freq="MS"), fill_value=0)
                    .reset_index()
                )
                series.columns = ["month", "revenue"]

                body = (
                    f"<strong>{top_prod['product_name']}</strong> has shown a sharp drop in sales in the latest month. "
                    f"Revenue fell from about <strong>₹{top_prod['baseline_revenue']:,.2f}</strong> on average in the previous months "
                    f"to <strong>₹{top_prod['recent_revenue']:,.2f}</strong> in the current month. "
                    f"This suggests a sudden sales erosion rather than a normal fluctuation."
                )

                def render_product_drop_chart(series=series):
                    fig = px.line(
                        series,
                        x="month",
                        y="revenue",
                        markers=True,
                        template="plotly_dark",
                    )
                    fig.update_traces(line=dict(width=3, color=LINE_COL), marker=dict(size=7, color=LINE_COL))
                    fig.update_layout(
                        height=290,
                        margin=dict(l=10, r=10, t=20, b=10),
                        xaxis_title="Month",
                        yaxis_title="Revenue",
                        paper_bgcolor=PAGE_BG,
                        plot_bgcolor=PAGE_BG,
                        font=dict(color=TEXT),
                    )
                    fig.update_xaxes(gridcolor="#3F3F46", zerolinecolor="#3F3F46")
                    fig.update_yaxes(gridcolor="#3F3F46", zerolinecolor="#3F3F46")
                    st.plotly_chart(fig, use_container_width=True)

                add_insight(
                    priority=120,
                    title="Product Sales Drop",
                    body=body,
                    chart_renderer=render_product_drop_chart,
                )

        recent_cat = monthly_category.loc[monthly_category["month"] == latest_month].copy()
        baseline_cat = monthly_category.loc[monthly_category["month"].isin(baseline_months)].copy()

        if not recent_cat.empty and not baseline_cat.empty:
            recent_cat_agg = recent_cat.groupby("category", as_index=False).agg(recent_revenue=("revenue", "sum"))
            baseline_cat_agg = baseline_cat.groupby("category", as_index=False).agg(
                baseline_revenue=("revenue", "mean"),
                baseline_std=("revenue", "std"),
            )

            cat_shift = recent_cat_agg.merge(baseline_cat_agg, on="category", how="left").fillna(0)
            cat_shift["drop_pct"] = cat_shift.apply(
                lambda row: safe_divide(row["baseline_revenue"] - row["recent_revenue"], row["baseline_revenue"]),
                axis=1,
            )

            cat_candidates = cat_shift.loc[
                (cat_shift["baseline_revenue"] > 0) &
                (cat_shift["drop_pct"] >= 0.20)
            ].sort_values(["drop_pct", "baseline_revenue"], ascending=[False, False])

            if not cat_candidates.empty:
                top_cat = cat_candidates.iloc[0]
                cat_series = (
                    monthly_category.loc[
                        monthly_category["category"] == top_cat["category"],
                        ["month", "revenue"]
                    ]
                    .groupby("month", as_index=False)["revenue"]
                    .sum()
                    .set_index("month")
                    .reindex(pd.date_range(min(months), max(months), freq="MS"), fill_value=0)
                    .reset_index()
                )
                cat_series.columns = ["month", "revenue"]

                body = (
                    f"<strong>{top_cat['category']}</strong> is showing a noticeable sales decline in the latest month. "
                    f"Revenue dropped from about <strong>₹{top_cat['baseline_revenue']:,.2f}</strong> on average to "
                    f"<strong>₹{top_cat['recent_revenue']:,.2f}</strong>. "
                    f"This points to a category-level slowdown that may need attention."
                )

                def render_category_drop_chart(cat_series=cat_series):
                    fig = px.line(
                        cat_series,
                        x="month",
                        y="revenue",
                        markers=True,
                        template="plotly_dark",
                    )
                    fig.update_traces(line=dict(width=3, color=ACCENT), marker=dict(size=7, color=ACCENT))
                    fig.update_layout(
                        height=290,
                        margin=dict(l=10, r=10, t=20, b=10),
                        xaxis_title="Month",
                        yaxis_title="Revenue",
                        paper_bgcolor=PAGE_BG,
                        plot_bgcolor=PAGE_BG,
                        font=dict(color=TEXT),
                    )
                    fig.update_xaxes(gridcolor="#3F3F46", zerolinecolor="#3F3F46")
                    fig.update_yaxes(gridcolor="#3F3F46", zerolinecolor="#3F3F46")
                    st.plotly_chart(fig, use_container_width=True)

                add_insight(
                    priority=110,
                    title="Category Sales Drop",
                    body=body,
                    chart_renderer=render_category_drop_chart,
                )

    if not product_health.empty:
        risky_candidates = product_health.loc[
            product_health["revenue"] >= product_health["revenue"].median()
        ].sort_values(["return_rate", "revenue"], ascending=[False, False])

        if not risky_candidates.empty:
            risky = risky_candidates.iloc[0]
            if float(risky["return_rate"]) >= 0.10:
                add_insight(
                    priority=90,
                    title="High Return Risk Product",
                    body=(
                        f"<strong>{risky['product_name']}</strong> is generating strong sales but also shows a high return rate of "
                        f"<strong>{risky['return_rate'] * 100:.1f}%</strong>. "
                        f"This suggests the product may be facing quality, expectation, or description mismatch issues."
                    ),
                    chart_renderer=None,
                )

    if not product_health.empty:
        margin_threshold = product_health["profit_margin"].quantile(0.75)
        unit_threshold = product_health["units_sold"].median()

        opportunity_candidates = product_health.loc[
            (product_health["profit_margin"] >= margin_threshold) &
            (product_health["units_sold"] <= unit_threshold)
        ].sort_values(["profit_margin", "units_sold"], ascending=[False, True])

        if not opportunity_candidates.empty:
            opp = opportunity_candidates.iloc[0]
            add_insight(
                priority=80,
                title="Hidden Margin Opportunity",
                body=(
                    f"<strong>{opp['product_name']}</strong> has a strong profit margin of <strong>{opp['profit_margin'] * 100:.1f}%</strong>, "
                    f"but sales volume is still relatively low. "
                    f"This looks like a product that could scale better with more visibility or promotion."
                ),
                chart_renderer=None,
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

    st.write("")

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

    elif not text_insights:
        st.info("No major product anomalies detected at the moment.")

render()