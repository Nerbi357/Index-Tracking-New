"""Tracking-error metrics."""

from __future__ import annotations

import pandas as pd


def custom_active_returns(port_returns: pd.Series, index_returns: pd.Series) -> pd.Series:
    """Active (portfolio minus index) returns, aligned and NaN-dropped."""
    return (port_returns - index_returns).dropna()


def custom_tracking_error(
    port_returns: pd.Series, index_returns: pd.Series, *, annualize: int | None = 52
) -> float:
    """Annualized standard deviation of active returns (weekly data -> x sqrt(52))."""
    active = custom_active_returns(port_returns, index_returns)
    te = active.std(ddof=1)
    return te * (annualize**0.5) if annualize else te
