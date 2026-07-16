import pandas as pd
from index_tracking.data import cleaning as cl


def _idx():
    return pd.to_datetime(["2015-01-02", "2015-01-09", "2015-01-16"])


def test_membership_matrix_and_coverage():
    membership = pd.DataFrame({"date": pd.to_datetime(["2015-01-01"]), "tickers": [["A", "B"]]})
    mat = cl.custom_membership_matrix(_idx(), membership, ["A", "B", "C"])
    assert mat["A"].all() and mat["B"].all() and not mat["C"].any()
    panel = pd.DataFrame({"A": [1.0, 2.0, 3.0], "B": [1.0, None, 3.0]}, index=_idx())
    cov = cl.custom_coverage_within_membership(panel, mat[["A", "B"]]).set_index("ticker")
    assert cov.loc["A", "coverage"] == 1.0
    assert abs(cov.loc["B", "coverage"] - 2 / 3) < 1e-9


def test_quality_status():
    assert cl.custom_quality_status(0.3) == "drop"
    assert cl.custom_quality_status(0.7) == "flag"
    assert cl.custom_quality_status(0.95) == "ok"
