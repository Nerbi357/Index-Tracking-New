"""Sparse-regression tracking: non-negative LASSO with cardinality control."""

from __future__ import annotations

import pandas as pd
from sklearn.linear_model import Lasso


def custom_lasso_tracking(train_returns, train_index, *, k, alpha=None, max_iter=5000) -> pd.Series:
    """Regress the index on the stocks with a non-negative LASSO; keep the top-K names.

    L1 shrinks most coefficients toward zero; we take the K largest non-negative coefficients
    and normalize them to sum to 1. A light default ``alpha`` keeps the fit stable while still
    ordering the names.
    """
    X = train_returns.fillna(0.0).to_numpy()
    y = train_index.reindex(train_returns.index).fillna(0.0).to_numpy()
    if alpha is None:
        alpha = 1e-4 * (y.std() or 1.0)
    model = Lasso(alpha=alpha, positive=True, fit_intercept=True, max_iter=max_iter)
    model.fit(X, y)
    coef = pd.Series(model.coef_, index=train_returns.columns)
    top = coef[coef > 1e-12].nlargest(k)
    if float(top.sum()) <= 0:
        return pd.Series(dtype=float)
    return top / top.sum()
