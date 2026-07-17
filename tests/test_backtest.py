import numpy as np
import pandas as pd

from index_tracking.backtest.engine import _rebalance_dates, custom_run_backtest
from index_tracking.methods.simple import custom_equal_weight


def _fixture(n=90, seed=0):
    idx = pd.date_range("2015-01-02", periods=n, freq="W-FRI")
    rng = np.random.default_rng(seed)
    returns = pd.DataFrame(rng.normal(0.001, 0.02, (n, 4)), index=idx, columns=list("ABCD"))
    index_returns = returns.mean(axis=1)
    membership = pd.DataFrame({"date": [idx[0]], "tickers": [list(returns.columns)]})
    return returns, index_returns, membership


def test_rebalance_dates_monthly():
    idx = pd.date_range("2015-01-02", periods=60, freq="W-FRI")
    reb = _rebalance_dates(idx, idx[10], idx[-1])
    assert all(reb[i] < reb[i + 1] for i in range(len(reb) - 1))
    assert 8 <= len(reb) <= 14  # ~one per month


def test_backtest_runs_and_costs_never_help():
    returns, index_returns, membership = _fixture()
    res = custom_run_backtest(custom_equal_weight, returns, index_returns, membership,
                              train_weeks=20, cost_bps=10)
    assert len(res.gross) > 0
    assert (res.net <= res.gross + 1e-12).all()
    assert (res.turnover >= 0).all()


def test_no_look_ahead():
    returns, index_returns, membership = _fixture(n=90)
    base = custom_run_backtest(custom_equal_weight, returns, index_returns, membership, train_weeks=20)
    cut = returns.index[70]
    mod = returns.copy()
    mod.loc[mod.index > cut] = 3.0  # absurd future values
    res = custom_run_backtest(custom_equal_weight, mod, mod.mean(axis=1), membership, train_weeks=20)
    early = base.gross.index[base.gross.index <= cut]
    pd.testing.assert_series_equal(base.gross.loc[early], res.gross.loc[early])
