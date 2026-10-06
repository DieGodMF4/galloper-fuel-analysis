"""Project-wide constants and paths.

Keeping magic numbers and file locations in one place makes the notebooks
thin and keeps every path relative to the repository root.
"""
from pathlib import Path

# --- Paths -----------------------------------------------------------------
# config.py lives in src/galloper/, so the repo root is three levels up.
ROOT = Path(__file__).resolve().parents[2]
DATA_RAW = ROOT / "data" / "raw"
DATA_INTERIM = ROOT / "data" / "interim"
DATA_PROCESSED = ROOT / "data" / "processed"
FIGURES = ROOT / "reports" / "figures"

RAW_CSV = DATA_RAW / "fuel_log_1999_2026.csv"

# --- Domain constants ------------------------------------------------------
# Irrevocable peseta-to-euro conversion rate fixed on 1999-01-01.
PESETAS_PER_EURO = 166.386

# Currency label used in the raw file for pre-2002 rows.
CURRENCY_PESETA = "Pts"
CURRENCY_EURO = "EUR"

# Premium-diesel switches annotated by hand in the logbook. Each tuple is
# (label, approximate_start_date) and is used as an intervention marker in
# the causal-impact / change-point analysis (notebook 06).
PREMIUM_DIESEL_EVENTS = [
    ("Shell V-Power (1st mention)", "2006-10-19"),
    ("Shell V-Power (relabelled)", "2007-07-27"),
    ("BP Ultimate Diesel", "2010-06-11"),
]

# Vehicle metadata (for reports and axis captions).
VEHICLE = {
    "model": "Hyundai Galloper Exceed Long 2.5 TCI diesel",
    "purchase_year": 1999,
    "location": "Gran Canaria, Spain",
}
