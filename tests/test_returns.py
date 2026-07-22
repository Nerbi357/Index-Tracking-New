import pandas as pd
from index_tracking.metrics.returns import custom_simple_returns


def test_simple_returns():
    p = pd.Series([100.0, 110.0, 99.0])
    r = custom_simple_returns(p)
    assert pd.isna(r.iloc[0])
    assert abs(r.iloc[1] - 0.10) < 1e-9
    assert abs(r.iloc[2] - (-0.10)) < 1e-9
