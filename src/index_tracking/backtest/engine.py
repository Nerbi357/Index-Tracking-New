"""Walk-forward backtest engine.

Contract: a tracking *method* is any callable ``method(train_returns, train_index) ->
weights`` that returns a weights ``Series`` on a subset of names (non-negative, summing to
1). The engine owns the walk-forward loop, weight drift, turnover and costs, so every method
plugs into the same harness.

No look-ahead: at each month-end ``t`` the method sees only returns up to ``t`` and the
point-in-time index members on ``t``; those weights then earn returns from the *following*
week and drift until the next rebalance. One-way turnover ``0.5*sum|dw|`` is charged
``cost_bps`` per unit at each rebalance.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from ..data.constituents import custom_members_on
from ..metrics.turnover import custom_turnover


@dataclass
class CustomBacktestResult:
    gross: pd.Series  # weekly portfolio returns, before costs
    net: pd.Series  # weekly portfolio returns, after transaction costs
    turnover: pd.Series  # one-way turnover per rebalance date
    weights: dict  # rebalance date -> weights Series
    rebalance_dates: list


def _rebalance_dates(weekly_index, start, end):
    """Month-end weeks (last available week of each month) within ``[start, end]``."""
    idx = weekly_index[(weekly_index >= start) & (weekly_index <= end)]
    if len(idx) == 0:
        return []
    ser = pd.Series(list(idx), index=idx)
    return [pd.Timestamp(x) for x in ser.groupby([idx.year, idx.month]).last()]


def custom_run_backtest(
    method, returns, index_returns, membership, *,
    train_weeks: int = 52, cost_bps: float = 10.0, start=None, end=None,
) -> CustomBacktestResult:
    """Run ``method`` through a monthly walk-forward backtest (see module docstring)."""
    weekly = returns.index
    start = pd.Timestamp(start) if start is not None else weekly[min(train_weeks, len(weekly) - 1)]
    end = pd.Timestamp(end) if end is not None else weekly[-1]
    rebal = _rebalance_dates(weekly, start, end)
    if not rebal:
        raise ValueError("no rebalance dates in the requested window")
    rebal_set = set(rebal)

    port: dict = {}
    cost: dict = {}
    turnovers: dict = {}
    weights_hist: dict = {}
    w: pd.Series | None = None

    for t in weekly[(weekly >= rebal[0]) & (weekly <= end)]:
        # 1) earn this week's return with the weights set at the previous rebalance
        if w is not None and len(w):
            r_t = returns.loc[t, list(w.index)].fillna(0.0)
            port[t] = float((w * r_t).sum())
            grown = w * (1.0 + r_t)
            total = float(grown.sum())
            if total > 0:
                w = grown / total
        # 2) at a month-end, fit new weights (data up to t only) for the following weeks
        if t in rebal_set:
            train = returns.loc[returns.index <= t].tail(train_weeks)
            train_index = index_returns.reindex(train.index)
            members = custom_members_on(membership, t)
            candidates = [c for c in train.columns if c in members and bool(train[c].notna().all())]
            new_w = method(train[candidates], train_index)
            new_w = new_w[new_w.abs() > 1e-8]
            if float(new_w.sum()) > 0:
                new_w = new_w / new_w.sum()
            prev = w if w is not None else pd.Series(dtype=float)
            turnovers[t] = custom_turnover(prev, new_w)
            cost[t] = (cost_bps / 1e4) * turnovers[t]
            w = new_w
            weights_hist[t] = w.copy()

    gross = pd.Series(port).sort_index()
    costs = pd.Series(cost).reindex(gross.index).fillna(0.0)
    return CustomBacktestResult(
        gross=gross,
        net=gross - costs,
        turnover=pd.Series(turnovers).sort_index(),
        weights=weights_hist,
        rebalance_dates=rebal,
    )
