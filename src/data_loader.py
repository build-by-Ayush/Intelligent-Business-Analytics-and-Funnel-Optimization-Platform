from __future__ import annotations

from pathlib import Path
from typing import TypeAlias

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = PROJECT_ROOT / "Dataset" / "All datasets"

# A stable source signature lets cached data refresh automatically when a CSV is
# added, removed, modified, or replaced. Paths and timestamps are cheap to inspect.
DataSignature: TypeAlias = tuple[tuple[str, str, int, int], ...]


def _source_signature() -> DataSignature:
    entries: list[tuple[str, str, int, int]] = []

    for table_name in ("events", "order_items", "returns", "transactions"):
        folder = DATA_ROOT / table_name
        for file in sorted(folder.glob("*.csv")) if folder.exists() else []:
            try:
                stat = file.stat()
            except OSError:
                continue
            entries.append((table_name, str(file), stat.st_size, stat.st_mtime_ns))

    products_file = DATA_ROOT / "products.csv"
    try:
        stat = products_file.stat()
        entries.append(("products", str(products_file), stat.st_size, stat.st_mtime_ns))
    except OSError:
        # Keep a signature entry so the loader still raises the usual read error.
        entries.append(("products", str(products_file), -1, -1))

    return tuple(entries)


def get_data_version() -> DataSignature:
    """Return the current file signature for cache invalidation in dashboard pages."""
    return _source_signature()


def load_folder_csvs(folder_name: str) -> pd.DataFrame:
    """Load and concatenate all CSV files from one existing dataset folder."""
    folder = DATA_ROOT / folder_name
    if not folder.exists():
        return pd.DataFrame()

    files = sorted(folder.glob("*.csv"))
    if not files:
        return pd.DataFrame()

    frames = [pd.read_csv(file) for file in files]
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def try_parse_datetime(series: pd.Series) -> pd.Series:
    # Avoid reparsing a series that already has a datetime dtype.
    if pd.api.types.is_datetime64_any_dtype(series):
        return series
    return pd.to_datetime(series, errors="coerce", dayfirst=True)


@st.cache_data(show_spinner=False)
def _load_data_cached(signature: DataSignature):
    files_by_table: dict[str, list[Path]] = {}
    for table_name, path, _size, _mtime_ns in signature:
        files_by_table.setdefault(table_name, []).append(Path(path))

    def load_table(folder_name: str) -> pd.DataFrame:
        paths = files_by_table.get(folder_name, [])
        if not paths:
            return pd.DataFrame()
        frames = [pd.read_csv(path) for path in paths]
        return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

    events = load_table("events")
    order_items = load_table("order_items")
    returns = load_table("returns")
    transactions = load_table("transactions")

    product_paths = files_by_table.get("products", [])
    products = pd.read_csv(product_paths[0] if product_paths else DATA_ROOT / "products.csv")

    if "event_timestamp" in events.columns:
        events["event_timestamp"] = try_parse_datetime(events["event_timestamp"])

    if "order_timestamp" in transactions.columns:
        transactions["order_timestamp"] = try_parse_datetime(transactions["order_timestamp"])

    if "order_timestamp" in returns.columns:
        returns["order_timestamp"] = try_parse_datetime(returns["order_timestamp"])

    if "return_request_date" in returns.columns:
        returns["return_request_date"] = try_parse_datetime(returns["return_request_date"])

    if "return_date" in returns.columns:
        returns["return_date"] = try_parse_datetime(returns["return_date"])

    if "created_at" in products.columns:
        products["created_at"] = try_parse_datetime(products["created_at"])

    return events, order_items, products, returns, transactions


def load_data():
    """Load the five dashboard datasets from a cross-page, file-versioned cache."""
    return _load_data_cached(_source_signature())
