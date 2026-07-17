"""Convex tracking: minimize tracking error on a selected subset (long-only, fully invested).

Base version (no turnover penalty). We first select the K names most correlated with the
index over the training window, then solve the convex problem
``min ||R w - r||^2  s.t.  w >= 0, sum(w) = 1`` for the tracking-optimal weights on them.
"""

from __future__ import annotations

import cvxpy as cp
import pandas as pd


def custom_convex_tracking(train_returns, train_index, *, k) -> pd.Series:
    """Select K index-correlated names, then convex min-tracking-error weights on them."""
    y = train_index.reindex(train_returns.index)
    corr = train_returns.corrwith(y).dropna()
    selected = list(corr.nlargest(k).index)
    if not selected:
        return pd.Series(dtype=float)

    R = train_returns[selected].fillna(0.0).to_numpy()
    r = y.fillna(0.0).to_numpy()
    w = cp.Variable(len(selected), nonneg=True)
    problem = cp.Problem(cp.Minimize(cp.sum_squares(R @ w - r)), [cp.sum(w) == 1])
    try:
        problem.solve()
    except cp.error.SolverError:
        return pd.Series(1.0 / len(selected), index=selected)
    if w.value is None:
        return pd.Series(1.0 / len(selected), index=selected)

    weights = pd.Series(w.value, index=selected).clip(lower=0)
    total = float(weights.sum())
    return weights / total if total > 0 else pd.Series(dtype=float)
