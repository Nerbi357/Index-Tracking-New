import numpy as np
import pandas as pd

from index_tracking.methods.convex import custom_convex_tracking
from index_tracking.methods.regression import custom_lasso_tracking


def _fixture(n=60, p=8, seed=1):
    idx = pd.date_range("2015-01-02", periods=n, freq="W-FRI")
    rng = np.random.default_rng(seed)
    R = pd.DataFrame(rng.normal(0.001, 0.02, (n, p)), index=idx,
                     columns=[f"S{i}" for i in range(p)])
    index = R.iloc[:, :4].mean(axis=1)  # index driven by first 4 names
    return R, index


def _check_weights(w, k):
    assert len(w) <= k
    assert (w >= -1e-9).all()
    assert abs(w.sum() - 1.0) < 1e-6


def test_lasso_tracking():
    R, index = _fixture()
    _check_weights(custom_lasso_tracking(R, index, k=4), 4)


def test_convex_tracking():
    R, index = _fixture()
    _check_weights(custom_convex_tracking(R, index, k=4), 4)
