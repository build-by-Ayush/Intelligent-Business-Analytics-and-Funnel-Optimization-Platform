import pandas as pd


# -----------------------------------------------------------------------------
# General helpers
# -----------------------------------------------------------------------------
def safe_divide(numerator, denominator):
    """Divide safely; return 0 when the denominator is missing or zero."""
    if denominator in (0, None) or pd.isna(denominator):
        return 0.0
    return numerator / denominator


def _numeric(series: pd.Series, default: float = 0.0) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").fillna(default)


def _parse_dates(series: pd.Series) -> pd.Series:
    """Parse ISO dates/timestamps first, then handle other common date formats."""
    raw = series.astype("string").str.strip()
    parsed = pd.to_datetime(raw, format="ISO8601", errors="coerce")
    unresolved = parsed.isna() & raw.notna() & raw.ne("")
    if unresolved.any():
        parsed.loc[unresolved] = pd.to_datetime(raw.loc[unresolved], dayfirst=True, errors="coerce")
    return parsed


def _transaction_net_merchandise_sales(transactions: pd.DataFrame) -> pd.Series:
    """Return per-order merchandise sales after discounts, excluding tax/shipping."""
    if {"subtotal", "discount_amount"}.issubset(transactions.columns):
        subtotal = _numeric(transactions["subtotal"])
        discount = _numeric(transactions["discount_amount"])
        return subtotal - discount

    # Fallback for older transaction extracts that have only final order value.
    # total_amount already includes discounts, so subtract tax and shipping to
    # derive merchandise value after discounts when those columns are available.
    if "total_amount" in transactions.columns:
        order_value = _numeric(transactions["total_amount"])
        shipping = _numeric(transactions["shipping_cost"]) if "shipping_cost" in transactions.columns else 0.0
        tax = _numeric(transactions["tax_amount"]) if "tax_amount" in transactions.columns else 0.0
        return order_value - shipping - tax

    return pd.Series(0.0, index=transactions.index, dtype="float64")


def parse_transaction_dates(transactions: pd.DataFrame) -> pd.DataFrame:
    df = transactions.copy()
    if "order_date" in df.columns:
        df["order_date"] = _parse_dates(df["order_date"]).dt.normalize()
    elif "order_timestamp" in df.columns:
        df["order_date"] = _parse_dates(df["order_timestamp"]).dt.normalize()
    else:
        df["order_date"] = pd.NaT
    return df


def parse_event_dates(events: pd.DataFrame) -> pd.DataFrame:
    df = events.copy()
    if "event_date" in df.columns:
        df["event_date"] = _parse_dates(df["event_date"]).dt.normalize()
    elif "event_timestamp" in df.columns:
        df["event_date"] = _parse_dates(df["event_timestamp"]).dt.normalize()
    else:
        df["event_date"] = pd.NaT
    return df


# -----------------------------------------------------------------------------
# Shared order-item financial calculations
# -----------------------------------------------------------------------------
def build_item_financials(
    order_items: pd.DataFrame,
    products: pd.DataFrame,
    transactions: pd.DataFrame,
) -> pd.DataFrame:
    """Build one financially consistent row per order item.

    Net merchandise sales = line merchandise value less the order discount
    allocated in proportion to each line's merchandise value. Tax and shipping
    are excluded. Cost of goods sold comes from products.cost_price * quantity.
    If a product cost is missing, the order's estimated_cost is allocated to
    that item by merchandise-value share as a fallback.

    Original order-item columns are retained; added columns are intermediate
    fields for dashboard calculations only and do not change any CSV schema.
    """
    oi = order_items.copy()
    tx = transactions.copy()

    if "order_id" not in oi.columns or "order_id" not in tx.columns:
        raise KeyError("order_items and transactions must both contain 'order_id'.")

    oi["quantity"] = _numeric(oi["quantity"]) if "quantity" in oi.columns else 0.0
    if "total_price" in oi.columns:
        oi["line_merchandise_value"] = _numeric(oi["total_price"])
    elif {"unit_price", "quantity"}.issubset(oi.columns):
        oi["line_merchandise_value"] = _numeric(oi["unit_price"]) * oi["quantity"]
    else:
        raise KeyError("order_items must contain 'total_price' or both 'unit_price' and 'quantity'.")

    # Only attach transaction columns needed for calculations/context. Deduplicate
    # the order lookup to prevent accidental row multiplication on joins.
    wanted_tx_cols = [
        col for col in [
            "order_id", "order_date", "order_timestamp", "region", "device_type",
            "traffic_source", "subtotal", "discount_amount", "estimated_cost", "total_amount"
        ] if col in tx.columns
    ]
    tx_lookup = tx[wanted_tx_cols].drop_duplicates(subset=["order_id"])
    oi = oi.merge(tx_lookup, on="order_id", how="left", validate="many_to_one", suffixes=("", "_order"))

    if "order_date" in oi.columns:
        oi["order_date"] = _parse_dates(oi["order_date"]).dt.normalize()
    elif "order_timestamp" in oi.columns:
        oi["order_date"] = _parse_dates(oi["order_timestamp"]).dt.normalize()
    else:
        oi["order_date"] = pd.NaT

    order_item_value = oi.groupby("order_id")["line_merchandise_value"].transform("sum")
    item_share = oi["line_merchandise_value"].div(order_item_value.where(order_item_value.ne(0))).fillna(0.0)
    oi["item_share"] = item_share

    if "discount_amount" in oi.columns:
        order_discount = _numeric(oi["discount_amount"])
    else:
        order_discount = pd.Series(0.0, index=oi.index)
    oi["allocated_discount"] = order_discount * oi["item_share"]
    oi["net_merchandise_sales"] = oi["line_merchandise_value"] - oi["allocated_discount"]

    # Bring product unit cost into the order-item grain.
    if products is not None and {"product_id", "cost_price"}.issubset(products.columns) and "product_id" in oi.columns:
        cost_lookup = products[["product_id", "cost_price"]].drop_duplicates(subset=["product_id"])
        oi = oi.merge(cost_lookup, on="product_id", how="left", validate="many_to_one", suffixes=("", "_catalog"))
        unit_cost = pd.to_numeric(oi["cost_price"], errors="coerce")
    else:
        unit_cost = pd.Series(float("nan"), index=oi.index)

    oi["cost_of_goods_sold"] = unit_cost * oi["quantity"]

    # When the catalogue cost is missing, use the order's stored cost estimate
    # proportionally. This is a fallback only; catalogue cost is preferred.
    if "estimated_cost" in oi.columns:
        fallback_order_cost = _numeric(oi["estimated_cost"])
        fallback_item_cost = fallback_order_cost * oi["item_share"]
        missing_cost = oi["cost_of_goods_sold"].isna()
        oi.loc[missing_cost, "cost_of_goods_sold"] = fallback_item_cost.loc[missing_cost]

    if oi["cost_of_goods_sold"].isna().any():
        missing_count = int(oi["cost_of_goods_sold"].isna().sum())
        raise ValueError(
            f"Cannot calculate gross profit reliably: {missing_count} order-item row(s) "
            "have no product cost and no order-level cost fallback."
        )

    oi["gross_profit"] = oi["net_merchandise_sales"] - oi["cost_of_goods_sold"]
    # Compatibility alias for existing page code; it now means item-level gross profit.
    oi["allocated_profit"] = oi["gross_profit"]
    oi["profit_margin"] = oi["gross_profit"].div(oi["net_merchandise_sales"].where(oi["net_merchandise_sales"].ne(0))).fillna(0.0)
    oi["unit_net_price"] = oi["net_merchandise_sales"].div(oi["quantity"].where(oi["quantity"].ne(0))).fillna(0.0)

    return oi


def build_return_financials(
    order_items: pd.DataFrame,
    products: pd.DataFrame,
    transactions: pd.DataFrame,
    returns: pd.DataFrame,
) -> pd.DataFrame:
    """Return return-level rows with refund value recalculated from net unit price.

    All return requests remain visible regardless of status. Only approved
    requests are included in approved_refund_amount. Pending and rejected
    requests therefore remain useful for customer-experience analysis without
    being counted as actual refunds.
    """
    rt = returns.copy()
    if rt.empty:
        for col in ["return_quantity", "refund_amount", "calculated_refund_amount", "approved_refund_amount"]:
            if col not in rt.columns:
                rt[col] = pd.Series(dtype="float64")
        return rt

    item_financials = build_item_financials(order_items, products, transactions)
    item_cols = [col for col in [
        "order_item_id", "quantity", "unit_net_price", "net_merchandise_sales", "line_merchandise_value",
        "allocated_discount", "order_id", "product_id", "product_name", "category", "subcategory", "brand"
    ] if col in item_financials.columns]
    item_lookup = item_financials[item_cols].drop_duplicates(subset=["order_item_id"])
    rt = rt.merge(item_lookup, on="order_item_id", how="left", validate="many_to_one", suffixes=("", "_item"))

    rt["return_quantity"] = _numeric(rt["return_quantity"]) if "return_quantity" in rt.columns else 0.0
    rt["calculated_refund_amount"] = rt["unit_net_price"].fillna(0.0) * rt["return_quantity"]

    status = rt["return_status"].astype(str).str.strip().str.lower() if "return_status" in rt.columns else pd.Series("", index=rt.index)
    rt["approved_refund_amount"] = rt["calculated_refund_amount"].where(status.eq("approved"), 0.0)
    rt["is_return_request"] = True
    rt["is_approved_return"] = status.eq("approved")
    rt["is_pending_return"] = status.eq("pending")
    rt["is_rejected_return"] = status.eq("rejected")
    return rt


# -----------------------------------------------------------------------------
# Core business metrics
# -----------------------------------------------------------------------------
def net_merchandise_sales(transactions: pd.DataFrame) -> float:
    """Merchandise sales after discounts, excluding tax/shipping and refunds."""
    return float(_transaction_net_merchandise_sales(transactions).sum())


def total_revenue(transactions: pd.DataFrame) -> float:
    """Compatibility name for net merchandise sales."""
    return net_merchandise_sales(transactions)


def gross_profit(transactions: pd.DataFrame) -> float:
    """Gross profit from net merchandise sales less product cost of goods sold."""
    net_sales = _transaction_net_merchandise_sales(transactions)
    if "estimated_cost" not in transactions.columns:
        raise KeyError("transactions must contain 'estimated_cost' to calculate gross profit.")
    cogs = _numeric(transactions["estimated_cost"])
    return float((net_sales - cogs).sum())


def total_profit(transactions: pd.DataFrame) -> float:
    """Compatibility name for gross profit under the revised metric definition."""
    return gross_profit(transactions)


def total_orders(transactions: pd.DataFrame) -> int:
    return int(transactions["order_id"].nunique()) if "order_id" in transactions.columns else 0


def total_sessions(events: pd.DataFrame) -> int:
    return int(events["session_id"].nunique()) if "session_id" in events.columns else 0


def total_users(events: pd.DataFrame) -> int:
    return int(events["user_id"].nunique()) if "user_id" in events.columns else 0


def average_order_value(transactions: pd.DataFrame) -> float:
    """Average net merchandise sales per order."""
    return safe_divide(net_merchandise_sales(transactions), total_orders(transactions))


def average_items_per_order(order_items: pd.DataFrame) -> float:
    units = _numeric(order_items["quantity"]).sum() if "quantity" in order_items.columns else 0
    orders = order_items["order_id"].nunique() if "order_id" in order_items.columns else 0
    return safe_divide(units, orders)


def conversion_rate(events: pd.DataFrame) -> float:
    """Overall visit-to-purchase conversion across all sessions, independent of search use."""
    visits = events.loc[events["event_type"].eq("visit"), "session_id"].nunique()
    purchases = events.loc[events["event_type"].eq("purchase"), "session_id"].nunique()
    return safe_divide(purchases, visits)


def return_request_unit_rate(order_items: pd.DataFrame, returns: pd.DataFrame) -> float:
    """Units requested for return divided by units sold; include all request statuses."""
    total_units = _numeric(order_items["quantity"]).sum() if "quantity" in order_items.columns else 0
    requested_units = _numeric(returns["return_quantity"]).sum() if "return_quantity" in returns.columns else returns.get("order_item_id", pd.Series(dtype=object)).nunique()
    return safe_divide(requested_units, total_units)


def return_request_line_rate(order_items: pd.DataFrame, returns: pd.DataFrame) -> float:
    """Sold order-item lines associated with a return request / all sold order-item lines."""
    total_lines = order_items["order_item_id"].nunique() if "order_item_id" in order_items.columns else 0
    requested_lines = returns["order_item_id"].nunique() if "order_item_id" in returns.columns else 0
    return safe_divide(requested_lines, total_lines)


def item_return_rate(order_items: pd.DataFrame, returns: pd.DataFrame) -> float:
    """Compatibility name; now returns the unit-based return-request rate."""
    return return_request_unit_rate(order_items, returns)


def approved_return_unit_rate(order_items: pd.DataFrame, returns: pd.DataFrame) -> float:
    total_units = _numeric(order_items["quantity"]).sum() if "quantity" in order_items.columns else 0
    if "return_quantity" not in returns.columns or "return_status" not in returns.columns:
        return 0.0
    approved = returns["return_status"].astype(str).str.strip().str.lower().eq("approved")
    returned_units = _numeric(returns.loc[approved, "return_quantity"]).sum()
    return safe_divide(returned_units, total_units)


def order_return_rate(transactions: pd.DataFrame, returns: pd.DataFrame) -> float:
    """Orders with at least one return request / all orders; all statuses count."""
    total_order_count = transactions["order_id"].nunique() if "order_id" in transactions.columns else 0
    requested_orders = returns["order_id"].nunique() if "order_id" in returns.columns else 0
    return safe_divide(requested_orders, total_order_count)


def approved_refund_amount(returns: pd.DataFrame) -> float:
    """Sum recorded refund amounts for approved requests only (legacy/raw value)."""
    if returns.empty or "refund_amount" not in returns.columns:
        return 0.0
    if "return_status" in returns.columns:
        approved = returns["return_status"].astype(str).str.strip().str.lower().eq("approved")
        amounts = _numeric(returns.loc[approved, "refund_amount"])
    else:
        amounts = _numeric(returns["refund_amount"])
    return float(amounts.sum())


def adjusted_approved_refund_amount(
    order_items: pd.DataFrame,
    products: pd.DataFrame,
    transactions: pd.DataFrame,
    returns: pd.DataFrame,
) -> float:
    """Approved refund value at discounted net unit price, based on return quantity."""
    return_financials = build_return_financials(order_items, products, transactions, returns)
    if return_financials.empty:
        return 0.0
    return float(_numeric(return_financials["approved_refund_amount"]).sum())


def refund_rate(
    transactions: pd.DataFrame,
    returns: pd.DataFrame,
    order_items: pd.DataFrame | None = None,
    products: pd.DataFrame | None = None,
) -> float:
    """Approved refund value divided by net merchandise sales."""
    sales = net_merchandise_sales(transactions)
    if order_items is not None and products is not None:
        refunds = adjusted_approved_refund_amount(order_items, products, transactions, returns)
    else:
        refunds = approved_refund_amount(returns)
    return safe_divide(refunds, sales)


def net_merchandise_sales_after_refunds(
    transactions: pd.DataFrame,
    returns: pd.DataFrame,
    order_items: pd.DataFrame | None = None,
    products: pd.DataFrame | None = None,
) -> float:
    if order_items is not None and products is not None:
        refunds = adjusted_approved_refund_amount(order_items, products, transactions, returns)
    else:
        refunds = approved_refund_amount(returns)
    return net_merchandise_sales(transactions) - refunds


# -----------------------------------------------------------------------------
# Daily trends and comparable seven-calendar-day periods
# -----------------------------------------------------------------------------
def _daily_calendar(trend: pd.DataFrame, date_col: str, value_cols: list[str]) -> pd.DataFrame:
    if trend.empty or date_col not in trend.columns:
        return trend
    df = trend.copy()
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce").dt.normalize()
    df = df.dropna(subset=[date_col]).sort_values(date_col)
    if df.empty:
        return df
    calendar = pd.date_range(df[date_col].min(), df[date_col].max(), freq="D")
    df = df.set_index(date_col).reindex(calendar)
    df.index.name = date_col
    for col in value_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    return df.reset_index()


def revenue_trend(transactions: pd.DataFrame) -> pd.DataFrame:
    """Daily net merchandise sales, including calendar dates with zero sales."""
    df = parse_transaction_dates(transactions)
    df["revenue"] = _transaction_net_merchandise_sales(df)
    daily = (
        df.dropna(subset=["order_date"])
        .groupby("order_date", as_index=False)["revenue"]
        .sum()
        .sort_values("order_date")
    )
    return _daily_calendar(daily, "order_date", ["revenue"])


def profit_trend(transactions: pd.DataFrame) -> pd.DataFrame:
    """Daily gross profit: net merchandise sales less estimated COGS."""
    df = parse_transaction_dates(transactions)
    df["profit"] = _transaction_net_merchandise_sales(df) - _numeric(df["estimated_cost"])
    daily = (
        df.dropna(subset=["order_date"])
        .groupby("order_date", as_index=False)["profit"]
        .sum()
        .sort_values("order_date")
    )
    return _daily_calendar(daily, "order_date", ["profit"])


def _change_between_last_two_seven_day_periods(trend: pd.DataFrame, value_col: str) -> float:
    if trend.empty or len(trend) < 14:
        return 0.0
    values = _numeric(trend[value_col])
    current_period = float(values.iloc[-7:].sum())
    previous_period = float(values.iloc[-14:-7].sum())
    return safe_divide(current_period - previous_period, previous_period)


def revenue_change_last_7_days(transactions: pd.DataFrame) -> float:
    """Change in sales across the last 7 calendar days vs the prior 7 calendar days."""
    return _change_between_last_two_seven_day_periods(revenue_trend(transactions), "revenue")


def profit_change_last_7_days(transactions: pd.DataFrame) -> float:
    """Change in gross profit across the last 7 calendar days vs prior 7 calendar days."""
    return _change_between_last_two_seven_day_periods(profit_trend(transactions), "profit")


# -----------------------------------------------------------------------------
# Breakdowns
# -----------------------------------------------------------------------------
def revenue_by_category(
    order_items: pd.DataFrame,
    transactions: pd.DataFrame | None = None,
    products: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Category sales breakdown.

    Pass transactions (and products, when available) to allocate order discounts
    and return net merchandise sales. Without transactions, the legacy fallback
    is gross item-line value, retained for compatibility with pages not yet updated.
    """
    if transactions is not None:
        item_financials = build_item_financials(order_items, products, transactions)
        return (
            item_financials.groupby("category", as_index=False)["net_merchandise_sales"]
            .sum()
            .rename(columns={"net_merchandise_sales": "revenue"})
            .sort_values("revenue", ascending=False)
        )
    return (
        order_items.groupby("category", as_index=False)["total_price"]
        .sum()
        .rename(columns={"total_price": "revenue"})
        .sort_values("revenue", ascending=False)
    )


def revenue_by_region(transactions: pd.DataFrame) -> pd.DataFrame:
    tx = transactions.copy()
    tx["net_merchandise_sales"] = _transaction_net_merchandise_sales(tx)
    return (
        tx.groupby("region", as_index=False)["net_merchandise_sales"]
        .sum()
        .rename(columns={"net_merchandise_sales": "revenue"})
        .sort_values("revenue", ascending=False)
    )


def traffic_source_conversion(events: pd.DataFrame) -> pd.DataFrame:
    visits = (
        events.loc[events["event_type"].eq("visit")]
        .groupby("traffic_source")["session_id"]
        .nunique()
        .reset_index(name="visit_sessions")
    )
    purchases = (
        events.loc[events["event_type"].eq("purchase")]
        .groupby("traffic_source")["session_id"]
        .nunique()
        .reset_index(name="purchase_sessions")
    )
    df = visits.merge(purchases, on="traffic_source", how="left")
    df["purchase_sessions"] = _numeric(df["purchase_sessions"])
    df["conversion_rate"] = df.apply(
        lambda row: safe_divide(row["purchase_sessions"], row["visit_sessions"]), axis=1
    )
    return df.sort_values("conversion_rate", ascending=False)


def top_category_by_revenue(
    order_items: pd.DataFrame,
    transactions: pd.DataFrame | None = None,
    products: pd.DataFrame | None = None,
):
    df = revenue_by_category(order_items, transactions=transactions, products=products)
    if df.empty:
        return None, 0.0
    row = df.iloc[0]
    return row["category"], float(row["revenue"])


def top_region_by_revenue(transactions: pd.DataFrame):
    df = revenue_by_region(transactions)
    if df.empty:
        return None, 0.0
    row = df.iloc[0]
    return row["region"], float(row["revenue"])


def top_traffic_source_by_conversion(events: pd.DataFrame):
    df = traffic_source_conversion(events)
    if df.empty:
        return None, 0.0
    row = df.iloc[0]
    return row["traffic_source"], float(row["conversion_rate"])


def build_overview_metrics(
    events: pd.DataFrame,
    order_items: pd.DataFrame,
    products: pd.DataFrame,
    returns: pd.DataFrame,
    transactions: pd.DataFrame,
) -> dict:
    """Return shared overview metrics, retaining existing keys for page compatibility."""
    item_financials = build_item_financials(order_items, products, transactions)
    total_sales = float(item_financials["net_merchandise_sales"].sum())
    total_gross_profit = float(item_financials["gross_profit"].sum())
    total_units_sold = float(_numeric(order_items["quantity"]).sum()) if "quantity" in order_items.columns else 0.0
    requested_units = float(_numeric(returns["return_quantity"]).sum()) if "return_quantity" in returns.columns else float(returns.get("order_item_id", pd.Series(dtype=object)).nunique())
    requested_lines_rate = return_request_line_rate(order_items, returns)
    approved_units_rate = approved_return_unit_rate(order_items, returns)
    refund_value = adjusted_approved_refund_amount(order_items, products, transactions, returns)

    metrics = {
        # Existing keys retained so pages can be migrated one at a time.
        "total_revenue": total_sales,
        "total_profit": total_gross_profit,
        "total_orders": total_orders(transactions),
        "total_sessions": total_sessions(events),
        "total_users": total_users(events),
        "conversion_rate": conversion_rate(events),
        "item_return_rate": safe_divide(requested_units, total_units_sold),
        "order_return_rate": order_return_rate(transactions, returns),
        "average_order_value": safe_divide(total_sales, total_orders(transactions)),
        "average_items_per_order": average_items_per_order(order_items),
        "revenue_change_last_7_days": revenue_change_last_7_days(transactions),
        "profit_change_last_7_days": profit_change_last_7_days(transactions),
        # Explicit names for pages as they are corrected.
        "net_merchandise_sales": total_sales,
        "gross_profit": total_gross_profit,
        "return_request_unit_rate": safe_divide(requested_units, total_units_sold),
        "return_request_line_rate": requested_lines_rate,
        "approved_return_unit_rate": approved_units_rate,
        "approved_refund_amount": refund_value,
        "refund_rate": safe_divide(refund_value, total_sales),
        "net_merchandise_sales_after_refunds": total_sales - refund_value,
    }

    top_category, top_category_revenue = top_category_by_revenue(
        order_items, transactions=transactions, products=products
    )
    top_region, top_region_revenue = top_region_by_revenue(transactions)
    top_source, top_source_conversion = top_traffic_source_by_conversion(events)

    metrics["top_category_by_revenue"] = top_category
    metrics["top_category_revenue"] = top_category_revenue
    metrics["top_region_by_revenue"] = top_region
    metrics["top_region_revenue"] = top_region_revenue
    metrics["top_traffic_source_by_conversion"] = top_source
    metrics["top_traffic_source_conversion"] = top_source_conversion

    return metrics
