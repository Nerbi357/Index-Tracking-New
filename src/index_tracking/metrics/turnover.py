"""Portfolio turnover."""

from __future__ import annotations

import pandas as pd


def custom_turnover(weights_before: pd.Series, weights_after: pd.Series) -> float:
    """One-way turnover at a rebalance: ``0.5 * sum |w_after - w_before|``.

    Aligned over the union of names (a name absent on one side counts as weight 0). A full
    swap of the portfolio is a turnover of 1.0.
    """
    names = weights_before.index.union(weights_after.index)
    before = weights_before.reindex(names, fill_value=0.0)
    after = weights_after.reindex(names, fill_value=0.0)
    return 0.5 * float((after - before).abs().sum())
