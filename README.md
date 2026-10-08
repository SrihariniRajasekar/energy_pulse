# EnergyPulse – Crude Oil & Commodity Market Analytics Pipeline

End-to-end pipeline that ingests WTI, Brent and Henry Hub natural gas prices from the
**EIA API v2**, stores them in a **SQL** database, forecasts with **ARIMA (statsmodels)**,
generates written market commentary with the **Groq API**, and serves everything on a
**Streamlit** dashboard.

```
EIA API ──> ingest.py ──> SQL (prices)
                              │
                         forecast.py ──> SQL (forecasts)  [ARIMA, AIC grid search, 80% CI, MAPE backtest]
                              │
                        commentary.py ──> SQL (commentary) [Groq LLM]
                              │
                           app.py (Streamlit dashboard)
```

## Setup
```bash
cd "E:\energy pulse"
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env      # then add EIA_API_KEY and GROQ_API_KEY
```
- EIA key (free): https://www.eia.gov/opendata/register.php
- Groq key (free tier): https://console.groq.com/keys

## Run
```bash
python run_pipeline.py       # ingest -> forecast -> commentary
streamlit run app.py         # dashboard
```
Run steps individually with `python ingest.py`, `python forecast.py`, `python commentary.py`.

## Design notes
- **Series:** WTI (RWTC), Brent (RBRTE), Henry Hub (RNGWHHD), daily.
- **Model:** ARIMA fit on log prices; `d` chosen by ADF test, `(p,q)` by AIC over a 4×4 grid;
  30 business-day horizon with 80% interval. A 20-day holdout backtest reports MAPE.
- **Database:** SQLite by default (`DATABASE_URL` in `.env`). Tables: `prices`, `forecasts`, `commentary`.
  Upserts use SQLite's `INSERT OR REPLACE`; adapt to `ON CONFLICT` if moving to Postgres.
- **Commentary:** the LLM receives only computed statistics (returns, volatility, forecast range)
  and is told not to invent news, which keeps it grounded.
- ARIMA on price levels is a baseline; it will mostly project near-random-walk behavior. That is
  expected and worth stating in your write-up/interview.

## Output
<img width="953" height="419" alt="image" src="https://github.com/user-attachments/assets/725df9f1-e24e-4f91-a4cb-88ef6ce3a700" />
<img width="949" height="407" alt="image" src="https://github.com/user-attachments/assets/fc506075-292d-4124-ad43-9ff14aee6486" />
<img width="955" height="332" alt="image" src="https://github.com/user-attachments/assets/1e18a3d8-329b-4bfc-816b-1c5aa81a3d43" />
<img width="941" height="349" alt="image" src="https://github.com/user-attachments/assets/dbe07594-ab56-43e0-8bd5-5bfb219cbf83" />
<img width="956" height="383" alt="image" src="https://github.com/user-attachments/assets/9587c100-935d-48a0-bc6d-fde0f3abff15" />


## Possible extensions
- Add GARCH for volatility, or SARIMAX with storage/inventory exogenous variables from EIA.
- Scheduled daily refresh (Task Scheduler / GitHub Actions).
- Forecast accuracy tracking table comparing past forecasts to realized prices.
