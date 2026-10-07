"""Generate written market commentary with the Groq API from computed stats."""
from datetime import date

import pandas as pd
from groq import Groq

import db
from config import GROQ_API_KEY, GROQ_MODEL, SERIES

SYSTEM_PROMPT = (
    "You are a concise commodity market analyst. Write a short market commentary "
    "(120-170 words, plain prose, no bullet points, no headings) using ONLY the "
    "numbers provided. Cover: the recent trend, volatility, and what the ARIMA "
    "forecast implies. State clearly that the forecast is statistical, not "
    "financial advice. Do not invent news events or causes."
)


def build_stats(key: str):
    prices = db.load_prices(key)
    fc = db.load_latest_forecast(key)
    if prices.empty or fc.empty:
        return None
    p = prices.set_index("date")["price"]
    last = p.iloc[-1]

    def chg(n):
        return (last / p.iloc[-n - 1] - 1) * 100 if len(p) > n else float("nan")

    stats = {
        "commodity": SERIES[key]["label"],
        "unit": SERIES[key]["unit"],
        "last_date": p.index[-1].date().isoformat(),
        "last_price": round(float(last), 2),
        "change_1w_pct": round(float(chg(5)), 2),
        "change_1m_pct": round(float(chg(21)), 2),
        "change_3m_pct": round(float(chg(63)), 2),
        "high_52w": round(float(p.tail(252).max()), 2),
        "low_52w": round(float(p.tail(252).min()), 2),
        "volatility_30d_ann_pct": round(
            float(p.pct_change().tail(30).std() * (252 ** 0.5) * 100), 1
        ),
        "forecast_end_price": round(float(fc["yhat"].iloc[-1]), 2),
        "forecast_end_lower": round(float(fc["lower"].iloc[-1]), 2),
        "forecast_end_upper": round(float(fc["upper"].iloc[-1]), 2),
        "forecast_days": int(len(fc)),
    }
    return stats


def generate_commentary(key: str) -> str:
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY missing. Add it to your .env file.")
    stats = build_stats(key)
    if stats is None:
        raise RuntimeError(f"No prices/forecast for {key}. Run ingest and forecast first.")
    client = Groq(api_key=GROQ_API_KEY)
    resp = client.chat.completions.create(
        model=GROQ_MODEL,
        temperature=0.3,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Market data:\n{stats}"},
        ],
    )
    return resp.choices[0].message.content.strip()


def run_all():
    db.init_db()
    run_date = date.today().isoformat()
    for key in SERIES:
        try:
            text = generate_commentary(key)
            db.save_commentary(key, run_date, text, GROQ_MODEL)
            print(f"[ok] commentary saved for {key}")
        except Exception as e:
            print(f"[warn] {key}: {e}")


if __name__ == "__main__":
    run_all()
