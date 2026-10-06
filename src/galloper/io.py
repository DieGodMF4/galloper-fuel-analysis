"""Input / output helpers.

Thin wrappers so notebooks never hard-code paths or parsing options.
"""
from __future__ import annotations

import pandas as pd

from . import config


def load_raw() -> pd.DataFrame:
    """Load the raw hand-digitised fuel log exactly as stored on disk.

    No type coercion is done here on purpose: cleaning belongs to the
    cleaning module so the raw load stays a faithful mirror of the CSV.
    """
    return pd.read_csv(config.RAW_CSV, dtype=str)


def save_processed(df: pd.DataFrame, name: str) -> None:
    """Persist an analysis-ready frame to data/processed as parquet.

    Parquet keeps dtypes (dates, floats, categoricals) so the EDA and
    modelling notebooks can reload without re-parsing.
    """
    config.DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    df.to_parquet(config.DATA_PROCESSED / f"{name}.parquet", index=False)


def load_processed(name: str) -> pd.DataFrame:
    """Reload a parquet frame previously written by save_processed."""
    return pd.read_parquet(config.DATA_PROCESSED / f"{name}.parquet")
