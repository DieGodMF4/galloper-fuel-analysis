"""CPI (IPC) loading and price deflation.

The Spanish Statistical Office (INE) publishes the Consumer Price Index.
Download the monthly INDEX level (not the % change) from table 50902 and
save it as ``data/raw/ine_ipc.csv``. This module parses the INE CSV layout
(semicolon-separated, comma decimals, Spanish month names) and exposes a
single monthly index series plus a deflation helper.

Deflating nominal prices to a chosen reference period answers:
"how much would this fill-up cost in <reference year> euros?", which
separates real price changes from general inflation.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import config

# INE writes months in Spanish; map to numbers for date parsing.
_ES_MONTHS = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "octubre": 10,
    "noviembre": 11, "diciembre": 12,
}


def load_ipc(path=None) -> pd.DataFrame:
    """Load the INE monthly CPI index as a tidy (date, ipc) frame.

    Expects the INE table 50902 CSV export ("Índice general", data type
    "Índice", monthly). The INE layout has a "Periodo" column like
    "2026M09" or "2026 septiembre" and a value column with comma decimals.
    This parser tolerates both period styles.
    """
    path = path or (config.DATA_RAW / "ine_ipc.csv")
    raw = pd.read_csv(path, sep=";", dtype=str, encoding="latin-1")

    # Find the period and value columns heuristically.
    period_col = next(c for c in raw.columns if "eriodo" in c.lower())
    value_col = raw.columns[-1]  # INE puts the value in the last column

    def parse_period(s: str) -> pd.Timestamp:
        s = s.strip().lower()
        if "m" in s and s.replace("m", "").isdigit():  # "2026M09"
            y, mth = s.split("m")
            return pd.Timestamp(int(y), int(mth), 1)
        # "2026 septiembre"
        parts = s.split()
        year = int(parts[0])
        month = _ES_MONTHS[parts[1]]
        return pd.Timestamp(year, month, 1)

    out = pd.DataFrame({
        "date": raw[period_col].map(parse_period),
        "ipc": raw[value_col].str.replace(".", "", regex=False)
                             .str.replace(",", ".", regex=False).astype(float),
    })
    return out.sort_values("date").reset_index(drop=True)


def attach_real_prices(df: pd.DataFrame, ipc: pd.DataFrame,
                       ref_period: str = "2026-01") -> pd.DataFrame:
    """Add inflation-adjusted columns to the fuel log.

    Joins each fill-up to its month's CPI and rescales nominal euros to the
    purchasing power of ``ref_period`` (YYYY-MM). Adds:
        - ipc              : CPI index of the fill-up month
        - price_per_l_real : price/L in reference-period euros
        - amount_eur_real  : amount paid in reference-period euros
    """
    df = df.copy()
    df["ym"] = df["date"].dt.to_period("M").dt.to_timestamp()
    ipc_m = ipc.rename(columns={"date": "ym"})
    df = df.merge(ipc_m, on="ym", how="left")

    ref = pd.Timestamp(ref_period + "-01")
    ipc_ref = ipc.loc[ipc["date"] == ref, "ipc"]
    if ipc_ref.empty:
        raise ValueError(f"Reference period {ref_period} not found in CPI series")
    ipc_ref = float(ipc_ref.iloc[0])

    factor = ipc_ref / df["ipc"]
    df["price_per_l_real"] = df["price_per_l"] * factor
    df["amount_eur_real"] = df["amount_eur"] * factor
    return df.drop(columns=["ym"])
