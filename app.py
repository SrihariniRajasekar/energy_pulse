"""EnergyPulse dashboard: soft-gradient, minimal monitoring UI."""
import html
import math

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import db
from config import SERIES

st.set_page_config(
    page_title="EnergyPulse", page_icon="⚡", layout="wide", initial_sidebar_state="collapsed"
)

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@200;300;400;500;600&display=swap');
html, body, .stApp, .stMarkdown, p, span, label, div { font-family: 'Manrope', sans-serif; }
.stApp { background: radial-gradient(1200px 700px at 20% -10%, #fafafa 0%, #dcdcde 100%); }
header[data-testid="stHeader"], footer, #MainMenu,
[data-testid="stSidebar"], [data-testid="collapsedControl"], [data-testid="stToolbar"] { display: none; }

/* device-like frame */
.block-container {
  max-width: 1280px; margin: 28px auto; padding: 26px 32px 36px;
  background: #fff; border-radius: 22px;
  box-shadow: 0 0 0 9px #111, 0 40px 90px rgba(0,0,0,.28);
}

/* top bar */
.topbar { display:flex; align-items:center; gap:14px; margin-bottom:6px; }
.brand { font-weight:600; font-size:15px; letter-spacing:.02em; color:#111; }
.brand span { font-weight:300; color:#777; }
.dot { width:9px; height:9px; border-radius:50%; background:#c8dd6a; box-shadow:0 0 0 4px rgba(200,221,106,.3); }

/* pill radios */
div[data-testid="stRadio"] > label { display:none; }
div[data-testid="stRadio"] div[role="radiogroup"] { gap:8px; flex-wrap:wrap; }
div[data-testid="stRadio"] label {
  background:#f1f1f1 !important; border-radius:999px; padding:5px 16px; margin:0; cursor:pointer;
}
div[data-testid="stRadio"] label > div:first-child { display:none !important; }
div[data-testid="stRadio"] label p,
div[data-testid="stRadio"] label span { font-size:13px; font-weight:400; color:#222 !important; }
div[data-testid="stRadio"] label:has(input:checked) { background:#111 !important; }
div[data-testid="stRadio"] label:has(input:checked) p,
div[data-testid="stRadio"] label:has(input:checked) span { color:#fff !important; }

/* make every Streamlit widget text readable on the white frame */
.block-container label p, .block-container label span,
.block-container [data-testid="stCheckbox"] p,
div[data-testid="stExpander"] summary, div[data-testid="stExpander"] summary p,
div[data-testid="stExpander"] summary span { color:#222 !important; }
div[data-testid="stExpander"] svg { fill:#222; }

/* hero */
.hero {
  position:relative; overflow:hidden; border-radius:20px; min-height:452px; padding:26px 26px;
  background: linear-gradient(180deg, #fbfbfb 0%, #ececec 100%);
}
.hero .eyebrow { font-size:12px; letter-spacing:.14em; text-transform:uppercase; color:#8a8a8a; }
.hero h1 { font-weight:300; font-size:40px; line-height:1.08; margin:8px 0 0; color:#111; max-width:230px; }
.orb {
  position:absolute; left:46%; top:52%; width:290px; height:350px; transform:translate(-50%,-50%);
  border-radius:48% 48% 44% 44%; filter:blur(16px); opacity:.95;
  background:
    radial-gradient(closest-side at 50% 28%, rgba(25,25,25,.62), rgba(80,80,80,.28) 60%, transparent 100%),
    radial-gradient(closest-side at 50% 78%, rgba(150,200,120,.45), transparent 85%);
}
.hero .price { position:absolute; left:26px; bottom:24px; color:#111; }
.hero .price .n { font-size:64px; font-weight:200; line-height:1; letter-spacing:-.02em; }
.hero .price .u { font-size:13px; color:#666; margin-left:8px; }
.hero .price .d { font-size:12px; color:#888; margin-top:6px; }
.chips { position:absolute; right:20px; top:96px; display:flex; flex-direction:column; gap:12px; }
.chip { background:rgba(255,255,255,.75); backdrop-filter:blur(8px); border-radius:12px; padding:9px 14px; min-width:104px; }
.chip .l { font-size:11px; color:#888; }
.chip .v { font-size:18px; font-weight:300; color:#111; }

/* gradient cards */
.grid { display:grid; grid-template-columns:1fr 1fr; gap:14px; }
.card { border-radius:18px; padding:18px 20px; min-height:219px; position:relative; color:#161616; overflow:hidden; }
.card .l { font-size:12px; letter-spacing:.06em; color:rgba(0,0,0,.55); }
.card .big { font-size:54px; font-weight:200; letter-spacing:-.02em; line-height:1.05; margin-top:6px; }
.card .big small { font-size:14px; font-weight:400; margin-left:6px; color:rgba(0,0,0,.55); }
.card .s { font-size:12px; color:rgba(0,0,0,.55); margin-top:4px; }
.card .foot { position:absolute; left:20px; bottom:16px; font-size:12px; color:rgba(0,0,0,.6); }
.arc { position:absolute; right:10px; bottom:-6px; width:68%; }
.g1 { background:linear-gradient(160deg,#cfe4c6 0%,#e6efc8 52%,#f6dcab 100%); }
.g2 { background:linear-gradient(160deg,#f7d197 0%,#f1a76c 62%,#ebb9a3 100%); }
.g3 { background:linear-gradient(160deg,#f4e7a6 0%,#dde8b6 55%,#b9dfc3 100%); }
.g4 { background:linear-gradient(160deg,#d9e7d0 0%,#efd8b0 100%); }
.spark { position:absolute; left:14px; right:14px; bottom:14px; height:64px; width:calc(100% - 28px); }
.track { position:absolute; left:20px; right:20px; bottom:52px; height:1px; background:rgba(0,0,0,.3); }
.track i { position:absolute; top:-5px; width:11px; height:11px; border-radius:50%; background:#161616; transform:translateX(-50%); }
.track b { position:absolute; top:10px; font-size:11px; font-weight:400; color:rgba(0,0,0,.6); }

/* sections */
.sec { font-size:12px; letter-spacing:.14em; text-transform:uppercase; color:#8a8a8a; margin:26px 0 10px; }
.note { border-radius:18px; padding:22px 26px; font-weight:300; font-size:16px; line-height:1.65; color:#1a1a1a;
  background:linear-gradient(160deg,#eef3e6 0%,#f7ecd8 100%); }
.note .m { font-size:11px; color:#888; margin-top:12px; letter-spacing:.04em; }
div[data-testid="stExpander"] { border:none; background:#f6f6f6; border-radius:14px; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

db.init_db()


# ---------- helpers ----------
def pct_change(p: pd.Series, n: int) -> float:
    return (p.iloc[-1] / p.iloc[-n - 1] - 1) * 100 if len(p) > n else float("nan")


def fmt_pct(x: float) -> str:
    return "n/a" if math.isnan(x) else f"{x:+.1f}%"


def arc_svg(pct: float) -> str:
    pct = max(0.0, min(1.0, pct))
    cx, cy = 90, 95
    rings = "".join(
        f'<path d="M {cx - r} {cy} A {r} {r} 0 0 1 {cx + r} {cy}" fill="none" '
        f'stroke="rgba(0,0,0,.22)" stroke-width="1"/>'
        for r in (78, 64, 50)
    )
    th = math.pi * pct
    x, y = cx - 64 * math.cos(th), cy - 64 * math.sin(th)
    dot = f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.5" fill="#161616"/>'
    return f'<svg class="arc" viewBox="0 0 180 100">{rings}{dot}</svg>'


def spark_svg(values) -> str:
    v = list(values)
    lo, hi = min(v), max(v)
    span = (hi - lo) or 1.0
    pts = " ".join(
        f"{i / (len(v) - 1) * 200:.1f},{56 - (val - lo) / span * 48:.1f}" for i, val in enumerate(v)
    )
    return (
        f'<svg class="spark" viewBox="0 0 200 60" preserveAspectRatio="none">'
        f'<polyline points="{pts}" fill="none" stroke="rgba(0,0,0,.65)" stroke-width="1.3" '
        f'vector-effect="non-scaling-stroke"/></svg>'
    )


# ---------- controls ----------
st.markdown(
    '<div class="topbar"><div class="dot"></div>'
    '<div class="brand">EnergyPulse <span>· market analytics</span></div></div>',
    unsafe_allow_html=True,
)
c_a, c_b = st.columns([3, 2])
with c_a:
    key = st.radio("Commodity", list(SERIES), format_func=lambda k: SERIES[k]["label"].replace(" Spot", ""), horizontal=True)
with c_b:
    lookback = st.radio("Window", ["3M", "6M", "1Y", "3Y", "5Y", "All"], index=2, horizontal=True)

prices = db.load_prices(key)
if prices.empty:
    st.warning("No data yet. Run `python run_pipeline.py` first.")
    st.stop()

meta = SERIES[key]
unit = meta["unit"]
p = prices.set_index("date")["price"]
fc = db.load_latest_forecast(key)

last = float(p.iloc[-1])
last_date = p.index[-1].date()
hi52, lo52 = float(p.tail(252).max()), float(p.tail(252).min())
vol30 = float(p.pct_change().tail(30).std() * (252 ** 0.5) * 100)
ch1w, ch1m, ch3m = pct_change(p, 5), pct_change(p, 21), pct_change(p, 63)
range_pct = (last - lo52) / ((hi52 - lo52) or 1.0)

# ---------- top row: hero + gradient cards ----------
left, right = st.columns([1, 1.35], gap="medium")

with left:
    st.markdown(
        "".join([
            '<div class="hero"><div class="orb"></div>',
            '<div class="eyebrow">Commodity pulse</div>',
            f'<h1>{html.escape(meta["label"])}</h1>',
            '<div class="chips">',
            f'<div class="chip"><div class="l">1 week</div><div class="v">{fmt_pct(ch1w)}</div></div>',
            f'<div class="chip"><div class="l">1 month</div><div class="v">{fmt_pct(ch1m)}</div></div>',
            f'<div class="chip"><div class="l">3 months</div><div class="v">{fmt_pct(ch3m)}</div></div>',
            '</div>',
            f'<div class="price"><span class="n">{last:,.2f}</span><span class="u">{unit}</span>',
            f'<div class="d">Latest close · {last_date:%d %b %Y}</div></div>',
            '</div>',
        ]),
        unsafe_allow_html=True,
    )

with right:
    cards = []

    # 1) forecast
    if not fc.empty:
        f_end = float(fc["yhat"].iloc[-1])
        f_lo, f_hi = float(fc["lower"].iloc[-1]), float(fc["upper"].iloc[-1])
        f_pct = (f_end - lo52) / ((hi52 - lo52) or 1.0)
        cards.append(
            f'<div class="card g1"><div class="l">{len(fc)}-DAY FORECAST</div>'
            f'<div class="big">{f_end:,.1f}<small>{unit}</small></div>'
            f'<div class="s">{fmt_pct((f_end / last - 1) * 100)} vs latest</div>'
            f'{arc_svg(f_pct)}'
            f'<div class="foot">80% range {f_lo:,.1f} – {f_hi:,.1f}</div></div>'
        )
    else:
        cards.append('<div class="card g1"><div class="l">FORECAST</div><div class="s">Run the pipeline</div></div>')

    # 2) momentum
    cards.append(
        f'<div class="card g2"><div class="l">1-MONTH MOMENTUM</div>'
        f'<div class="big">{fmt_pct(ch1m)}</div>'
        f'<div class="s">last 60 sessions</div>{spark_svg(p.tail(60).values)}</div>'
    )

    # 3) volatility
    cards.append(
        f'<div class="card g3"><div class="l">30D VOLATILITY</div>'
        f'<div class="big">{vol30:,.0f}<small>% ann.</small></div>'
        f'<div class="s">{"Elevated" if vol30 > 45 else "Moderate" if vol30 > 25 else "Calm"}</div>'
        f'{arc_svg(vol30 / 80)}</div>'
    )

    # 4) 52-week range
    cards.append(
        f'<div class="card g4"><div class="l">52-WEEK RANGE</div>'
        f'<div class="big">{range_pct * 100:,.0f}<small>% of range</small></div>'
        f'<div class="s">position of latest price</div>'
        f'<div class="track"><i style="left:{max(0, min(1, range_pct)) * 100:.1f}%"></i>'
        f'<b style="left:0">{lo52:,.1f}</b><b style="right:0">{hi52:,.1f}</b></div></div>'
    )

    st.markdown(f'<div class="grid">{"".join(cards)}</div>', unsafe_allow_html=True)

# ---------- chart ----------
st.markdown('<div class="sec">Price &amp; forecast</div>', unsafe_allow_html=True)
days = {"3M": 63, "6M": 126, "1Y": 252, "3Y": 756, "5Y": 1260, "All": len(prices)}[lookback]
view = prices.tail(days)
show_ma = st.checkbox("30-day average", value=False)

fig = go.Figure()
base = float(view["price"].min()) * 0.97
fig.add_trace(go.Scatter(x=view["date"], y=[base] * len(view), line=dict(width=0), hoverinfo="skip", showlegend=False))
fig.add_trace(go.Scatter(
    x=view["date"], y=view["price"], name="Price", fill="tonexty",
    fillcolor="rgba(160,200,140,.18)", line=dict(color="#161616", width=1.6),
))
if show_ma:
    ma = p.rolling(30).mean().loc[view["date"].iloc[0]:]
    fig.add_trace(go.Scatter(x=ma.index, y=ma, name="30d avg", line=dict(color="#8fb36e", width=1.2, dash="dot")))
if not fc.empty:
    fx = pd.concat([pd.Series([p.index[-1]]), fc["forecast_date"]])
    fig.add_trace(go.Scatter(
        x=pd.concat([fc["forecast_date"], fc["forecast_date"][::-1]]),
        y=pd.concat([fc["upper"], fc["lower"][::-1]]),
        fill="toself", fillcolor="rgba(240,170,100,.28)", line=dict(width=0),
        name="80% interval", hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=fx, y=pd.concat([pd.Series([last]), fc["yhat"]]), name="ARIMA forecast",
        line=dict(color="#e8863f", width=2, dash="dash"),
    ))
fig.update_layout(
    height=430, margin=dict(l=4, r=4, t=10, b=4), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Manrope, sans-serif", color="#666", size=12),
    hovermode="x unified", legend=dict(orientation="h", y=1.08, x=0),
    xaxis=dict(showgrid=False, showline=False), yaxis=dict(gridcolor="rgba(0,0,0,.06)", zeroline=False, title=unit),
)
st.plotly_chart(fig, use_container_width=True)

# ---------- commentary ----------
st.markdown('<div class="sec">Market commentary</div>', unsafe_allow_html=True)
row = db.load_latest_commentary(key)
if row:
    body = html.escape(row[0]).replace("\n", "<br>")
    st.markdown(
        f'<div class="note">{body}<div class="m">Generated {row[1]} · {html.escape(str(row[2]))} · '
        f'Statistical forecast, not financial advice.</div></div>',
        unsafe_allow_html=True,
    )
else:
    st.info("No commentary yet. Run `python commentary.py` with a valid GROQ_API_KEY and model.")

# ---------- extras ----------
st.markdown('<div class="sec">More</div>', unsafe_allow_html=True)
with st.expander("Compare commodities (indexed to 100)"):
    comp = go.Figure()
    for k in SERIES:
        d = db.load_prices(k).tail(days)
        if not d.empty:
            comp.add_trace(go.Scatter(x=d["date"], y=d["price"] / d["price"].iloc[0] * 100, name=k, line=dict(width=1.5)))
    comp.update_layout(
        height=360, margin=dict(l=4, r=4, t=10, b=4), paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)", hovermode="x unified",
        xaxis=dict(showgrid=False), yaxis=dict(gridcolor="rgba(0,0,0,.06)"),
    )
    st.plotly_chart(comp, use_container_width=True)

with st.expander("Raw data"):
    st.dataframe(view.sort_values("date", ascending=False), use_container_width=True)
