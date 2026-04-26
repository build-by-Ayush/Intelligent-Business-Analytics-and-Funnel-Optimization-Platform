from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_folder_csvs(folder_name: str) -> pd.DataFrame:
    folder = PROJECT_ROOT / "Dataset" / "All datasets" / folder_name
    if not folder.exists():
        return pd.DataFrame()

    files = sorted(folder.glob("*.csv"))
    if not files:
        return pd.DataFrame()

    frames = []
    for file in files:
        df = pd.read_csv(file)
        frames.append(df)

    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def try_parse_datetime(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce", dayfirst=True)


def load_data():
    events = load_folder_csvs("events")
    order_items = load_folder_csvs("order_items")
    products = pd.read_csv(PROJECT_ROOT / "Dataset" / "All datasets" / "products.csv")
    returns = load_folder_csvs("returns")
    transactions = load_folder_csvs("transactions")

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