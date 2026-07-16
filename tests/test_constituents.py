"""Unit tests for PIT constituents logic (no network — synthetic fixtures)."""

import pandas as pd

from index_tracking.data import constituents as c


def test_normalize_ticker():
    assert c.custom_normalize_ticker("BRK.B") == "BRK-B"
    assert c.custom_normalize_ticker(" aapl ") == "AAPL"
    assert c.custom_normalize_ticker("BF.B") == "BF-B"


def test_parse_membership_splits_and_normalizes():
    csv = 'date,tickers\n2015-01-02,"A,BRK.B"\n2016-01-04,"A,C"\n'
    m = c.custom_parse_membership(csv)
    assert list(m.columns) == ["date", "tickers"]
    assert m.iloc[0]["tickers"] == ["A", "BRK-B"]  # normalized + sorted
    assert m["date"].is_monotonic_increasing


def _fixture() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": pd.to_datetime(["2015-01-02", "2016-01-04", "2017-01-03"]),
            "tickers": [["A", "B"], ["A", "C"], ["C", "D"]],
        }
    )


def test_members_on():
    m = _fixture()
    assert c.custom_members_on(m, "2015-06-01") == {"A", "B"}
    assert c.custom_members_on(m, "2016-02-01") == {"A", "C"}
    assert c.custom_members_on(m, "2017-01-03") == {"C", "D"}  # exact change date
    assert c.custom_members_on(m, "2014-01-01") == set()  # before first record


def test_universe_full_and_window():
    m = _fixture()
    assert c.custom_universe(m) == ["A", "B", "C", "D"]
    # window from 2016-01-04: base row {A,C} + everyone through 2017 -> {A, C, D}
    assert set(c.custom_universe(m, start="2016-01-04", end="2017-12-31")) == {"A", "C", "D"}
    # a mid-window start still picks up the as-of base row
    assert set(c.custom_universe(m, start="2016-06-01", end="2017-12-31")) == {"A", "C", "D"}
