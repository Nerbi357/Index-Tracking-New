"""Simple reference methods (used to exercise the backtest engine)."""

from __future__ import annotations

import pandas as pd


def custom_equal_weight(train_returns: pd.DataFrame, train_index: pd.Series) -> pd.Series:
    """Equal weights on all candidate names - a naive full-replication reference."""
    cols = list(train_returns.columns)
    if not cols:
        return pd.Series(dtype=float)
    return pd.Series(1.0 / len(cols), index=cols)
