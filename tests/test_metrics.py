import pandas as pd

from index_tracking.metrics.summary import custom_summary_stats
from index_tracking.metrics.tracking import custom_tracking_error
from index_tracking.metrics.turnover import custom_turnover


def test_tracking_error():
    port = pd.Series([0.02, 0.01, 0.03, 0.00])
    idx = pd.Series([0.01, 0.01, 0.02, 0.00])
    active = port - idx
    assert abs(custom_tracking_error(port, idx) - active.std(ddof=1) * (52**0.5)) < 1e-12
    assert abs(custom_tracking_error(port, idx, annualize=None) - active.std(ddof=1)) < 1e-12


def test_turnover():
    before = pd.Series({"A": 0.5, "B": 0.5})
    after = pd.Series({"A": 0.3, "C": 0.7})
    assert abs(custom_turnover(before, after) - 0.7) < 1e-12  # 0.5*(0.2+0.5+0.7)
    assert custom_turnover(before, before) == 0.0


def test_summary_stats():
    r = pd.Series([0.10, -0.05, 0.03])
    s = custom_summary_stats(r)
    assert abs(s["mean"] - r.mean()) < 1e-12
    assert abs(s["median"] - r.median()) < 1e-12
    assert abs(s["max_drawdown"] - (-0.05)) < 1e-9  # peak 1.10 -> 1.045
