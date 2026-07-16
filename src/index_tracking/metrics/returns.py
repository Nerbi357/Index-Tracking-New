"""Return calculations."""

from __future__ import annotations

import numpy as np
import pandas as pd


def custom_simple_returns(prices: pd.DataFrame | pd.Series):
    """Weekly simple returns ``r_t = P_t / P_{t-1} - 1`` (first row is NaN, no fill)."""
    return prices.pct_change()


def custom_log_returns(prices: pd.DataFrame | pd.Series):
    """Weekly log returns ``ln(P_t / P_{t-1})`` (first row is NaN, no fill)."""
    return np.log(prices / prices.shift(1))
