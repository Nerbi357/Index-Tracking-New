"""Summary statistics for a return series."""

from __future__ import annotations

import pandas as pd


def custom_summary_stats(returns: pd.Series, *, periods: int = 52) -> pd.Series:
    """Common stats for a (weekly) return series: level, risk, and drawdown.

    Returns a Series with mean, median, std, annualized return/vol, Sharpe (rf = 0),
    skew, kurtosis, and max drawdown.
    """
    r = returns.dropna()
    n = len(r)
    ann_return = (1 + r).prod() ** (periods / n) - 1 if n else float("nan")
    ann_vol = r.std(ddof=1) * (periods**0.5)
    sharpe = ann_return / ann_vol if ann_vol else float("nan")
    wealth = (1 + r).cumprod()
    max_drawdown = float((wealth / wealth.cummax() - 1).min()) if n else float("nan")
    return pd.Series(
        {
            "mean": r.mean(),
            "median": r.median(),
            "std": r.std(ddof=1),
            "ann_return": ann_return,
            "ann_vol": ann_vol,
            "sharpe": sharpe,
            "skew": r.skew(),
            "kurtosis": r.kurtosis(),
            "max_drawdown": max_drawdown,
        }
    )
