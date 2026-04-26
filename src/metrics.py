import pandas as pd


def safe_divide(numerator, denominator):
    if denominator in (0, None) or pd.isna(denominator):
        return 0
    return numerator / denominator


def parse_transaction_dates(transactions: pd.DataFrame) -> pd.DataFrame:
    df = transactions.copy()
    df["order_date"] = pd.to_datetime(df["order_date"], dayfirst=True, errors="coerce")
    return df


def parse_event_dates(events: pd.DataFrame) -> pd.DataFrame:
    df = events.copy()
    df["event_date"] = pd.to_datetime(df["event_date"], dayfirst=True, errors="coerce")
    return df


def total_revenue(transactions: pd.DataFrame) -> float:
    return float(transactions["total_amount"].sum())


def total_profit(transactions: pd.DataFrame) -> float:
    return float(transactions["estimated_profit"].sum())


def total_orders(transactions: pd.DataFrame) -> int:
    return int(transactions["order_id"].nunique())


def total_sessions(events: pd.DataFrame) -> int:
    return int(events["session_id"].nunique())


def total_users(events: pd.DataFrame) -> int:
    return int(events["user_id"].nunique())


def average_order_value(transactions: pd.DataFrame) -> float:
    return safe_divide(total_revenue(transactions), total_orders(transactions))


def average_items_per_order(order_items: pd.DataFrame) -> float:
    return safe_divide(order_items["quantity"].sum(), order_items["order_id"].nunique())


def conversion_rate(events: pd.DataFrame) -> float:
    visits = events.loc[events["event_type"] == "visit", "session_id"].nunique()
    purchases = events.loc[events["event_type"] == "purchase", "session_id"].nunique()
    return safe_divide(purchases, visits)


def item_return_rate(order_items: pd.DataFrame, returns: pd.DataFrame) -> float:
    total_items = order_items["order_item_id"].nunique()
    returned_items = returns["order_item_id"].nunique()
    return safe_divide(returned_items, total_items)


def order_return_rate(transactions: pd.DataFrame, returns: pd.DataFrame) -> float:
    total_orders_count = transactions["order_id"].nunique()
    returned_orders = returns["order_id"].nunique()
    return safe_divide(returned_orders, total_orders_count)


def revenue_trend(transactions: pd.DataFrame) -> pd.DataFrame:
    df = parse_transaction_dates(transactions)
    return (
        df.groupby("order_date", as_index=False)["total_amount"]
        .sum()
        .rename(columns={"total_amount": "revenue"})
        .sort_values("order_date")
    )


def profit_trend(transactions: pd.DataFrame) -> pd.DataFrame:
    df = parse_transaction_dates(transactions)
    return (
        df.groupby("order_date", as_index=False)["estimated_profit"]
        .sum()
        .rename(columns={"estimated_profit": "profit"})
        .sort_values("order_date")
    )


def revenue_change_last_7_days(transactions: pd.DataFrame) -> float:
    trend = revenue_trend(transactions)
    if len(trend) < 14:
        return 0.0

    last_7 = trend["revenue"].tail(7).mean()
    prev_7 = trend["revenue"].tail(14).head(7).mean()
    return safe_divide(last_7 - prev_7, prev_7)


def profit_change_last_7_days(transactions: pd.DataFrame) -> float:
    trend = profit_trend(transactions)
    if len(trend) < 14:
        return 0.0

    last_7 = trend["profit"].tail(7).mean()
    prev_7 = trend["profit"].tail(14).head(7).mean()
    return safe_divide(last_7 - prev_7, prev_7)


def revenue_by_category(order_items: pd.DataFrame) -> pd.DataFrame:
    return (
        order_items.groupby("category", as_index=False)["total_price"]
        .sum()
        .rename(columns={"total_price": "revenue"})
        .sort_values("revenue", ascending=False)
    )


def revenue_by_region(transactions: pd.DataFrame) -> pd.DataFrame:
    return (
        transactions.groupby("region", as_index=False)["total_amount"]
        .sum()
        .rename(columns={"total_amount": "revenue"})
        .sort_values("revenue", ascending=False)
    )


def traffic_source_conversion(events: pd.DataFrame) -> pd.DataFrame:
    visits = (
        events.loc[events["event_type"] == "visit"]
        .groupby("traffic_source")["session_id"]
        .nunique()
        .reset_index(name="visit_sessions")
    )
    purchases = (
        events.loc[events["event_type"] == "purchase"]
        .groupby("traffic_source")["session_id"]
        .nunique()
        .reset_index(name="purchase_sessions")
    )

    df = visits.merge(purchases, on="traffic_source", how="left").fillna(0)
    df["conversion_rate"] = df.apply(
        lambda row: safe_divide(row["purchase_sessions"], row["visit_sessions"]),
        axis=1,
    )
    return df.sort_values("conversion_rate", ascending=False)


def top_category_by_revenue(order_items: pd.DataFrame):
    df = revenue_by_category(order_items)
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
    metrics = {
        "total_revenue": total_revenue(transactions),
        "total_profit": total_profit(transactions),
        "total_orders": total_orders(transactions),
        "total_sessions": total_sessions(events),
        "total_users": total_users(events),
        "conversion_rate": conversion_rate(events),
        "item_return_rate": item_return_rate(order_items, returns),
        "order_return_rate": order_return_rate(transactions, returns),
        "average_order_value": average_order_value(transactions),
        "average_items_per_order": average_items_per_order(order_items),
        "revenue_change_last_7_days": revenue_change_last_7_days(transactions),
        "profit_change_last_7_days": profit_change_last_7_days(transactions),
    }

    top_category, top_category_revenue = top_category_by_revenue(order_items)
    top_region, top_region_revenue = top_region_by_revenue(transactions)
    top_source, top_source_conversion = top_traffic_source_by_conversion(events)

    metrics["top_category_by_revenue"] = top_category
    metrics["top_category_revenue"] = top_category_revenue
    metrics["top_region_by_revenue"] = top_region
    metrics["top_region_revenue"] = top_region_revenue
    metrics["top_traffic_source_by_conversion"] = top_source
    metrics["top_traffic_source_conversion"] = top_source_conversion

    return metrics