import pandas as pd

from index_tracking.methods.baseline import custom_cap_weighted_topk


def test_cap_weighted_topk():
    idx = pd.date_range("2015-01-02", periods=3, freq="W-FRI")
    tr = pd.DataFrame({"A": [0.01] * 3, "B": [0.01] * 3, "C": [0.01] * 3}, index=idx)
    shares = pd.Series({"A": 10.0, "B": 5.0, "C": 1.0})
    prices = pd.DataFrame({"A": [100.0] * 3, "B": [100.0] * 3, "C": [100.0] * 3}, index=idx)
    # caps A=1000, B=500, C=100 -> Top-2 = A,B weighted by cap
    w = custom_cap_weighted_topk(tr, tr.mean(axis=1), k=2, shares=shares, prices=prices)
    assert list(w.index) == ["A", "B"]
    assert abs(w["A"] - 1000 / 1500) < 1e-9
    assert abs(w["B"] - 500 / 1500) < 1e-9
    assert abs(w.sum() - 1.0) < 1e-12
