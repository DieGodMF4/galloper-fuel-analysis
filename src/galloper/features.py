"""Feature engineering and correct aggregate consumption.

METHODOLOGICAL NOTE
-------------------
Fill-ups were done to a FIXED AMOUNT of money, not to a full tank. Therefore
per-leg fuel economy (litres of one fill-up over the km since the previous
one) is noisy, because the tank level at the start and end of each leg is
unknown. It is kept here for exploration but must never be read in isolation.

The valid way to measure consumption is AGGREGATE: sum litres and divide by
the km actually travelled over a wide window (a full year, or a rolling block
of many fill-ups), where the tank-level boundary effect averages out.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def add_trip_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add per-row derived fields based on the odometer and date deltas.

    Assumes df is already sorted by odometer (see cleaning.clean).
    """
    df = df.copy()

    # Distance and time since the previous fill-up.
    df["km_since_prev"] = df["odometer_km"].diff()
    df["days_since_prev"] = df["date"].diff().dt.days

    # Calendar helpers for grouping / seasonality.
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month

    # Per-leg economy: NOISY (fixed-amount fills). For exploration only.
    df["l_per_100km_leg"] = 100 * df["litres"] / df["km_since_prev"]

    # Flag legs that are unusable for economy (missing km or litres,
    # or a non-positive distance from odometer reading issues).
    df["leg_valid"] = (
        df["km_since_prev"].gt(0)
        & df["litres"].notna()
        & df["km_since_prev"].notna()
    )
    return df


def flag_price_outliers(df: pd.DataFrame, window: int = 15,
                        tol: float = 0.35) -> pd.DataFrame:
    """Flag suspicious price_per_l values against their local median.

    Prices span 1999-2026 across a currency change and heavy inflation, so
    an absolute residual threshold is meaningless (0.40 EUR/L in 2000 vs
    1.50 EUR/L in 2026). Instead we compare each price to its centred
    rolling median as a RELATIVE deviation: a fill-up whose price differs
    from its local median by more than `tol` (e.g. 35%) is flagged as a
    likely transcription error for manual review.
    """
    df = df.copy()
    med = df["price_per_l"].rolling(window, center=True, min_periods=5).median()
    rel_dev = (df["price_per_l"] - med).abs() / med
    df["price_rel_dev"] = rel_dev
    df["price_outlier"] = rel_dev > tol
    return df


def yearly_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate the log by calendar year (the CORRECT consumption view).

    Returns one row per year with litres, spend, km travelled and the
    aggregate fuel economy, which is robust to fixed-amount fills.
    """
    g = df.groupby("year")
    out = g.agg(
        fill_ups=("odometer_km", "size"),
        litres=("litres", "sum"),
        spend_eur=("amount_eur", "sum"),
        km_start=("odometer_km", "min"),
        km_end=("odometer_km", "max"),
        avg_price_per_l=("price_per_l", "mean"),
    )
    out["km_travelled"] = out["km_end"] - out["km_start"]
    # Aggregate economy: total litres over total distance in the year.
    out["l_per_100km"] = 100 * out["litres"] / out["km_travelled"]
    out["eur_per_100km"] = 100 * out["spend_eur"] / out["km_travelled"]
    return out.reset_index()


def rolling_economy(df: pd.DataFrame, window: int = 10) -> pd.DataFrame:
    """Aggregate fuel economy over a rolling block of N valid fill-ups.

    Smoother than per-leg economy and independent of calendar-year edges;
    good for plotting a continuous consumption trend across the vehicle's
    life. Only valid legs contribute.
    """
    valid = df[df["leg_valid"]].copy()
    litres_roll = valid["litres"].rolling(window).sum()
    km_roll = valid["km_since_prev"].rolling(window).sum()
    valid["l_per_100km_roll"] = 100 * litres_roll / km_roll
    return valid[["date", "odometer_km", "l_per_100km_roll"]]


# --- Period aggregations ---------------------------------------------------
# NOTE ON INCOMPLETE YEARS
# ------------------------
# Absolute-sum metrics (km travelled, litres, spend) are only comparable
# across *full* calendar years. 1999 starts in August and 2026 is still
# running, so both are partial. Each period below carries an `is_complete`
# flag; always drop incomplete periods before plotting totals, but keep
# them for RATE metrics (avg price/L, L/100km, EUR/100km), which stay
# comparable regardless of how much of the period was observed.

def _tag_complete_years(df: pd.DataFrame) -> set:
    """Return the set of calendar years fully covered by the log.

    A year is treated as complete when it has at least one fill-up in the
    first quarter (Jan-Mar) and one in the last quarter (Oct-Dec), i.e. the
    log spans the whole year. This tolerates low-usage years that simply
    have no fill-up in a specific edge month.
    """
    years = set(df["year"].dropna().astype(int))
    complete = set()
    for y in years:
        months = set(df.loc[df["year"] == y, "month"].dropna().astype(int))
        if months & {1, 2, 3} and months & {10, 11, 12}:
            complete.add(y)
    return complete


def _aggregate(df: pd.DataFrame, group_cols: list) -> pd.DataFrame:
    """Shared aggregation producing both sum and rate metrics.

    km_travelled is the SUM of per-leg distances (km_since_prev) for legs
    closing in each period, not max-min of the odometer within the period.
    Summing legs keeps the year-boundary leg (Dec->Jan) and makes the
    metric additive and gap-free. Only valid legs contribute distance, so
    litres used for economy are restricted to those same legs to keep
    l_per_100km internally consistent.
    """
    g = df.groupby(group_cols)
    out = g.agg(
        fill_ups=("odometer_km", "size"),
        litres=("litres", "sum"),
        spend_eur=("amount_eur", "sum"),
        km_travelled=("km_since_prev", "sum"),
        avg_price_per_l=("price_per_l", "mean"),
    )
    # Litres on valid legs only, so economy pairs litres with measured km.
    litres_valid = df[df["leg_valid"]].groupby(group_cols)["litres"].sum()
    out["litres_valid_legs"] = litres_valid
    out["l_per_100km"] = 100 * out["litres_valid_legs"] / out["km_travelled"]
    out["eur_per_100km"] = 100 * out["spend_eur"] / out["km_travelled"]
    return out.reset_index()


def yearly_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate by calendar year, flagging incomplete years.

    Rows for incomplete years (1999, 2026) are kept but marked
    `is_complete = False` so the caller can exclude them from totals.
    """
    out = _aggregate(df, ["year"])
    complete = _tag_complete_years(df)
    out["is_complete"] = out["year"].astype(int).isin(complete)
    return out


def half_year_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate by calendar half-year (H1 = Jan-Jun, H2 = Jul-Dec).

    Finer than yearly and useful for partial years: 2026-H1 is a complete
    block even though the full year is not.
    """
    df = df.copy()
    df["half"] = np.where(df["month"] <= 6, "H1", "H2")
    df["period"] = df["year"].astype("Int64").astype(str) + "-" + df["half"]
    out = _aggregate(df, ["year", "half", "period"])

    # A half is complete if it has fill-ups near both its start and end.
    complete = set()
    for (y, h), sub in df.groupby(["year", "half"]):
        months = set(sub["month"].dropna().astype(int))
        edges = ({1} & months and {6} & months) if h == "H1" \
            else ({7} & months and {12} & months)
        if edges:
            complete.add((y, h))
    out["is_complete"] = [
        (r.year, r.half) in complete for r in out.itertuples()
    ]
    return out


def season_summary(df: pd.DataFrame, scheme: str = "summer_winter") -> pd.DataFrame:
    """Aggregate by season.

    scheme = "summer_winter": two touristic halves relevant in Gran Canaria
        - summer  = May-October
        - winter  = November-April (crosses the year end)
    scheme = "four": standard meteorological seasons (DJF/MAM/JJA/SON).

    Winter is assigned to the year in which it STARTS (Nov-Dec of year Y and
    Jan-Apr of Y+1 are grouped under the winter labelled Y), so each season
    is a contiguous block.
    """
    df = df.copy()
    m = df["month"]
    if scheme == "summer_winter":
        df["season"] = np.where(m.between(5, 10), "summer", "winter")
        # Winter months Jan-Apr belong to the winter that started last year.
        season_year = df["year"].astype("Int64")
        season_year = season_year.mask(
            (df["season"] == "winter") & (m <= 4), season_year - 1
        )
        df["season_year"] = season_year
    elif scheme == "four":
        season_map = {12: "winter", 1: "winter", 2: "winter",
                      3: "spring", 4: "spring", 5: "spring",
                      6: "summer", 7: "summer", 8: "summer",
                      9: "autumn", 10: "autumn", 11: "autumn"}
        df["season"] = m.map(season_map)
        season_year = df["year"].astype("Int64")
        season_year = season_year.mask(m == 12, season_year + 1)  # DJF -> next yr
        df["season_year"] = season_year
    else:
        raise ValueError("scheme must be 'summer_winter' or 'four'")

    df["period"] = (df["season_year"].astype(str) + "-" + df["season"])
    return _aggregate(df, ["season_year", "season", "period"])
