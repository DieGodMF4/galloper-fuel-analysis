"""Cleaning: turn the raw string table into typed, currency-normalised data.

The raw file is faithful to a 27-year paper logbook, so it contains a few
missing values (litres or odometer never written down) and free-text notes.
This module only does deterministic, reversible transformations; it does NOT
drop rows, so downstream notebooks decide how to handle gaps.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import config


def clean(df_raw: pd.DataFrame) -> pd.DataFrame:
    """Parse types, unify currency to euros and sort by odometer.

    Parameters
    ----------
    df_raw : DataFrame
        Output of io.load_raw() (all columns as strings).

    Returns
    -------
    DataFrame with typed columns plus:
        - amount_eur   : paid amount converted to euros (nominal)
        - price_per_l  : nominal euros per litre
        Rows are ordered by the odometer, which is the reliable
        monotonic anchor of the dataset.
    """
    df = df_raw.copy()

    # Numeric columns: coerce, leaving genuine gaps as NaN.
    for col in ["KM", "Litros", "Importe"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Dates are day-first (DD/MM/YYYY). A few illegible ones become NaT.
    df["date"] = pd.to_datetime(df["Fecha"], format="%d/%m/%Y", errors="coerce")

    # Normalise currency to euros. Pre-2002 rows are in pesetas.
    is_peseta = df["Moneda"].eq(config.CURRENCY_PESETA)
    df["amount_eur"] = np.where(
        is_peseta, df["Importe"] / config.PESETAS_PER_EURO, df["Importe"]
    )

    # Nominal price per litre (only where litres are known and non-zero).
    df["price_per_l"] = df["amount_eur"] / df["Litros"].replace(0, np.nan)

    # Rename to tidy english snake_case.
    df = df.rename(
        columns={
            "KM": "odometer_km",
            "Litros": "litres",
            "Importe": "amount_raw",
            "Moneda": "currency",
            "Marca": "brand",
            "Lugar": "place",
            "Notas": "notes",
        }
    )

    # The odometer is the trustworthy axis: sort by it, keep a clean index.
    df = df.sort_values("odometer_km").reset_index(drop=True)
    return df
