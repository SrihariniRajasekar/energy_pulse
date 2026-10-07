"""Pull crude oil and natural gas prices from the EIA API v2 into SQL."""
import pandas as pd
import requests

import db
from config import EIA_API_KEY, EIA_BASE, SERIES, START_DATE

PAGE = 5000


def fetch_series(route: str, series_id: str, start: str = START_DATE) -> pd.DataFrame:
    if not EIA_API_KEY:
        raise RuntimeError("EIA_API_KEY missing. Add it to your .env file.")

    url = f"{EIA_BASE}/{route}/data/"
    rows, offset = [], 0
    while True:
        params = {
            "api_key": EIA_API_KEY,
            "frequency": "daily",
            "data[0]": "value",
            "facets[series][]": series_id,
            "start": start,
            "sort[0][column]": "period",
            "sort[0][direction]": "asc",
            "offset": offset,
            "length": PAGE,
        }
        resp = requests.get(url, params=params, timeout=60)
        resp.raise_for_status()
        data = resp.json()["response"]["data"]
        if not data:
            break
        rows.extend(data)
        if len(data) < PAGE:
            break
        offset += PAGE

    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df["date"] = pd.to_datetime(df["period"])
    df["price"] = pd.to_numeric(df["value"], errors="coerce")
    return df.dropna(subset=["price"])[["date", "price"]]


def ingest_all() -> None:
    db.init_db()
    for key, meta in SERIES.items():
        df = fetch_series(meta["route"], meta["series_id"])
        if df.empty:
            print(f"[warn] no data returned for {key}")
            continue
        df["commodity"] = key
        df["unit"] = meta["unit"]
        db.upsert_prices(df[["commodity", "date", "price", "unit"]])
        print(f"[ok] {key}: {len(df)} rows ({df['date'].min().date()} → {df['date'].max().date()})")


if __name__ == "__main__":
    ingest_all()
