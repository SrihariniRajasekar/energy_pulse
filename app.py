"""EnergyPulse Streamlit dashboard."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import db
from config import SERIES

st.set_page_config(page_title="EnergyPulse", page_icon="⚡", layout="wide")
st.title("⚡ EnergyPulse")
st.caption("Crude oil & natural gas analytics: EIA data → SQL → ARIMA → Groq commentary")

db.init_db()

with st.sidebar:
    st.header("Controls")
    key = st.selectbox("Commodity", list(SERIES), format_func=lambda k: SERIES[k]["label"])
    lookback = st.select_slider(
        "History window", options=["3M", "6M", "1Y", "3Y", "5Y", "All"], value="1Y"
    )
    show_ma = st.checkbox("Show 30-day moving average", value=True)
    st.markdown("---")
    st.caption("Refresh data: `python run_pipeline.py`")

prices = db.load_prices(key)
if prices.empty:
    st.warning("No data yet. Run `python run_pipeline.py` first.")
    st.stop()

days = {"3M": 63, "6M": 126, "1Y": 252, "3Y": 756, "5Y": 1260, "All": len(prices)}[lookback]
view = prices.tail(days)
fc = db.load_latest_forecast(key)
unit = SERIES[key]["unit"]

# KPI row
p = prices.set_index("date")["price"]
last = p.iloc[-1]
c1, c2, c3, c4 = st.columns(4)
c1.metric("Latest price", f"{last:,.2f} {unit}", help=str(p.index[-1].date()))
if len(p) > 21:
    c2.metric("1-month change", f"{(last / p.iloc[-22] - 1) * 100:+.1f}%")
c3.metric("52-week high", f"{p.tail(252).max():,.2f}")
c4.metric("52-week low", f"{p.tail(252).min():,.2f}")

# Chart
fig = go.Figure()
fig.add_trace(go.Scatter(x=view["date"], y=view["price"], name="Price", line=dict(width=2)))
if show_ma:
    ma = prices.set_index("date")["price"].rolling(30).mean().loc[view["date"].iloc[0]:]
    fig.add_trace(go.Scatter(x=ma.index, y=ma, name="30d MA", line=dict(dash="dot")))
if not fc.empty:
    fig.add_trace(go.Scatter(
        x=pd.concat([fc["forecast_date"], fc["forecast_date"][::-1]]),
        y=pd.concat([fc["upper"], fc["lower"][::-1]]),
        fill="toself", fillcolor="rgba(255,127,14,0.2)", line=dict(width=0),
        name="80% interval", hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=fc["forecast_date"], y=fc["yhat"], name="ARIMA forecast",
        line=dict(color="#ff7f0e", width=2),
    ))
fig.update_layout(
    height=480, margin=dict(l=10, r=10, t=30, b=10),
    yaxis_title=unit, hovermode="x unified", legend=dict(orientation="h"),
)
st.plotly_chart(fig, use_container_width=True)

# Commentary
st.subheader("AI market commentary")
row = db.load_latest_commentary(key)
if row:
    st.write(row[0])
    st.caption(f"Generated {row[1]} by {row[2]} · Statistical forecast, not financial advice.")
else:
    st.info("No commentary yet. Run `python run_pipeline.py` with a GROQ_API_KEY set.")

# Cross-commodity view
with st.expander("Compare commodities (indexed to 100)"):
    comp = go.Figure()
    for k in SERIES:
        d = db.load_prices(k).tail(days)
        if not d.empty:
            comp.add_trace(go.Scatter(x=d["date"], y=d["price"] / d["price"].iloc[0] * 100, name=k))
    comp.update_layout(height=380, margin=dict(l=10, r=10, t=10, b=10), hovermode="x unified")
    st.plotly_chart(comp, use_container_width=True)

with st.expander("Raw data"):
    st.dataframe(view.sort_values("date", ascending=False), use_container_width=True)
