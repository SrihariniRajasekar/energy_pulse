"""Central configuration for EnergyPulse."""
import os
from dotenv import load_dotenv

load_dotenv()

EIA_API_KEY = os.getenv("EIA_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///energypulse.db")

# EIA API v2 routes + series IDs
EIA_BASE = "https://api.eia.gov/v2"
SERIES = {
    "WTI": {
        "label": "WTI Crude Oil Spot",
        "route": "petroleum/pri/spt",
        "series_id": "RWTC",
        "unit": "USD/barrel",
    },
    "BRENT": {
        "label": "Brent Crude Oil Spot",
        "route": "petroleum/pri/spt",
        "series_id": "RBRTE",
        "unit": "USD/barrel",
    },
    "HENRY_HUB": {
        "label": "Henry Hub Natural Gas Spot",
        "route": "natural-gas/pri/fut",
        "series_id": "RNGWHHD",
        "unit": "USD/MMBtu",
    },
}

START_DATE = "2015-01-01"
FORECAST_HORIZON = 30  # business days
