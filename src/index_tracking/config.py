"""Project-wide configuration: data window, benchmark, and default hyperparameters.

Keeping these in one place means the "hyperparameters" the assignment asks about are not
scattered across notebooks.
"""

# Data horizon (weekly). ~11 years, so a training window still leaves ~10y of backtest.
WINDOW_START = "2015-01-01"
WINDOW_END = "2026-06-30"

PRICE_INTERVAL = "1wk"  # weekly bars
BENCHMARK_TICKER = "^SP500TR"  # S&P 500 total-return index

# In-sample / out-of-sample boundary: IS 2015-2020, OOS from here.
SPLIT_DATE = "2021-01-01"

# Defaults consumed by later phases.
REBALANCE = "monthly"
TRANSACTION_COST_BPS = 10.0
TRAIN_WINDOW_WEEKS = 52
K_VALUES = (10, 30, 50)
