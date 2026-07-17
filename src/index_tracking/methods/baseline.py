"""Baseline tracking method: cap-weighted Top-K."""

from __future__ import annotations

import pandas as pd


def custom_cap_weighted_topk(train_returns, train_index, *, k, shares, prices) -> pd.Series:
    """The K largest candidates by market cap, cap-weighted.

    Market cap uses the current-shares proxy from notebook 1: ``cap = shares * price`` at the
    last training week. ``shares`` (Series) and ``prices`` (weekly DataFrame) are bound per
    run via ``functools.partial`` so the method still matches the engine contract
    ``method(train_returns, train_index) -> weights``.
    """
    date = train_returns.index[-1]
    px = prices.loc[date] if date in prices.index else pd.Series(dtype=float)
    caps = {}
    for c in train_returns.columns:
        sh = shares.get(c)
        p = px.get(c)
        if sh is not None and pd.notna(sh) and p is not None and pd.notna(p):
            caps[c] = float(sh) * float(p)
    if not caps:
        return pd.Series(dtype=float)
    top = pd.Series(caps).nlargest(k)
    return top / top.sum()
