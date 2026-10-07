"""SQL layer (SQLAlchemy). Schema: prices, forecasts, commentary."""
import pandas as pd
from sqlalchemy import create_engine, text

from config import DATABASE_URL

engine = create_engine(DATABASE_URL, future=True)

SCHEMA = [
    """
    CREATE TABLE IF NOT EXISTS prices (
        commodity TEXT NOT NULL,
        date      TEXT NOT NULL,
        price     REAL NOT NULL,
        unit      TEXT,
        PRIMARY KEY (commodity, date)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS forecasts (
        commodity    TEXT NOT NULL,
        run_date     TEXT NOT NULL,
        forecast_date TEXT NOT NULL,
        yhat         REAL,
        lower        REAL,
        upper        REAL,
        model        TEXT,
        PRIMARY KEY (commodity, run_date, forecast_date)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS commentary (
        commodity TEXT NOT NULL,
        run_date  TEXT NOT NULL,
        text      TEXT NOT NULL,
        model     TEXT,
        PRIMARY KEY (commodity, run_date)
    )
    """,
]


def init_db():
    with engine.begin() as conn:
        for stmt in SCHEMA:
            conn.execute(text(stmt))


def upsert_prices(df: pd.DataFrame):
    """df columns: commodity, date, price, unit."""
    with engine.begin() as conn:
        for r in df.itertuples(index=False):
            conn.execute(
                text(
                    "INSERT OR REPLACE INTO prices (commodity, date, price, unit) "
                    "VALUES (:c, :d, :p, :u)"
                ),
                {"c": r.commodity, "d": str(r.date)[:10], "p": float(r.price), "u": r.unit},
            )


def load_prices(commodity: str) -> pd.DataFrame:
    q = text("SELECT date, price FROM prices WHERE commodity = :c ORDER BY date")
    df = pd.read_sql(q, engine, params={"c": commodity}, parse_dates=["date"])
    return df


def save_forecast(commodity: str, run_date: str, fc: pd.DataFrame, model: str):
    with engine.begin() as conn:
        for r in fc.itertuples():
            conn.execute(
                text(
                    "INSERT OR REPLACE INTO forecasts "
                    "(commodity, run_date, forecast_date, yhat, lower, upper, model) "
                    "VALUES (:c, :r, :f, :y, :l, :u, :m)"
                ),
                {
                    "c": commodity, "r": run_date, "f": str(r.Index)[:10],
                    "y": float(r.yhat), "l": float(r.lower), "u": float(r.upper), "m": model,
                },
            )


def load_latest_forecast(commodity: str) -> pd.DataFrame:
    q = text(
        "SELECT forecast_date, yhat, lower, upper, run_date FROM forecasts "
        "WHERE commodity = :c AND run_date = "
        "(SELECT MAX(run_date) FROM forecasts WHERE commodity = :c) "
        "ORDER BY forecast_date"
    )
    return pd.read_sql(q, engine, params={"c": commodity}, parse_dates=["forecast_date"])


def save_commentary(commodity: str, run_date: str, body: str, model: str):
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT OR REPLACE INTO commentary (commodity, run_date, text, model) "
                "VALUES (:c, :r, :t, :m)"
            ),
            {"c": commodity, "r": run_date, "t": body, "m": model},
        )


def load_latest_commentary(commodity: str):
    q = text(
        "SELECT text, run_date, model FROM commentary WHERE commodity = :c "
        "ORDER BY run_date DESC LIMIT 1"
    )
    with engine.connect() as conn:
        row = conn.execute(q, {"c": commodity}).fetchone()
    return row
