"""ARIMA forecasting with a small AIC grid search (statsmodels)."""
import itertools
import warnings
from datetime import date

import numpy as np
import pandas as pd
from statsmodels.tools.sm_exceptions import ConvergenceWarning
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.stattools import adfuller

import db
from config import FORECAST_HORIZON, SERIES

warnings.filterwarnings("ignore", category=ConvergenceWarning)
warnings.filterwarnings("ignore", category=UserWarning)

TRAIN_WINDOW = 1500  # most recent business-day observations


def prepare_series(df: pd.DataFrame) -> pd.Series:
    s = df.set_index("date")["price"].asfreq("B").ffill()
    return s.tail(TRAIN_WINDOW)


def select_order(y: pd.Series, max_p=3, max_q=3):
    """Pick d via ADF on the log series; (p,q) via AIC grid search."""
    ly = np.log(y.clip(lower=0.01))
    d = 0
    series = ly
    while d < 2 and adfuller(series.dropna())[1] > 0.05:
        series = series.diff()
        d += 1

    best = (None, np.inf)
    for p, q in itertools.product(range(max_p + 1), range(max_q + 1)):
        try:
            res = ARIMA(ly, order=(p, d, q)).fit()
            if res.aic < best[1]:
                best = ((p, d, q), res.aic)
        except Exception:
            continue
    return best[0] or (1, 1, 1)


def forecast_series(y: pd.Series, horizon: int = FORECAST_HORIZON):
    order = select_order(y)
    ly = np.log(y.clip(lower=0.01))
    res = ARIMA(ly, order=order).fit()
    fc = res.get_forecast(horizon)
    ci = fc.conf_int(alpha=0.2)  # 80% interval
    out = pd.DataFrame(
        {
            "yhat": np.exp(fc.predicted_mean),
            "lower": np.exp(ci.iloc[:, 0]),
            "upper": np.exp(ci.iloc[:, 1]),
        }
    )
    return out, order


def backtest_mape(y: pd.Series, order, horizon: int = 20) -> float:
    """Hold out the last `horizon` points; report MAPE (%)."""
    train, test = y.iloc[:-horizon], y.iloc[-horizon:]
    res = ARIMA(np.log(train.clip(lower=0.01)), order=order).fit()
    pred = np.exp(res.get_forecast(horizon).predicted_mean)
    return float(np.mean(np.abs((test.values - pred.values) / test.values)) * 100)


def run_all():
    db.init_db()
    run_date = date.today().isoformat()
    metrics = {}
    for key in SERIES:
        df = db.load_prices(key)
        if len(df) < 200:
            print(f"[skip] {key}: not enough data")
            continue
        y = prepare_series(df)
        fc, order = forecast_series(y)
        mape = backtest_mape(y, order)
        db.save_forecast(key, run_date, fc, f"ARIMA{order}")
        metrics[key] = {"order": order, "mape": mape}
        print(f"[ok] {key}: ARIMA{order}, 20-day backtest MAPE {mape:.2f}%")
    return metrics


if __name__ == "__main__":
    run_all()
