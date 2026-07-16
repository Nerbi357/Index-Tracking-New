# Spec: Sparse Index Tracking of the S&P 500 (from scratch)

> Status: **DRAFT — awaiting review** (Phase 1 "Specify" of spec-driven development).
> This is a living document. Update it when decisions change, before writing code.

## 1. Objective

Build — **from scratch**, cleanly, and **step by step** — a project that constructs a
**sparse index-tracking portfolio** for the **S&P 500**: pick a small basket of stocks
(and their weights) that moves almost in step with the full index, then rigorously
evaluate how well it tracks and what it costs to run.

**Why.** A pet project that is simultaneously (a) a learning vehicle (understand every
step), (b) a small research study (compare methods honestly), and (c) a portfolio piece
(clear, reproducible, well-presented). It reworks an earlier draft
(`ml-in-finance-index-tracking`) completely: new data collection (fixing the gaps),
new structure, more methods, more evaluation, much better visualization.

**Primary users.**
1. The author — wants to follow and correct every decision.
2. A reviewer/grader — reads a short PDF report and judges the method.
3. Anyone who clones the repo — must be able to re-run it end-to-end.

**Definition of success.** All assignment deliverables produced (section 8), the main
method demonstrably tracks the index **out-of-sample**, the pipeline is **reproducible**
from a committed data snapshot, and the narrative is understandable from the outside.

## 2. The assignment (hard requirements)

Collect **weekly** prices for the past **~10 years** of a financial index and of the
assets relevant for replication (**ideally every asset that was in the index at least
once** — point-in-time membership, survivorship-aware). Propose a **sparse index
tracking** method, evaluate it, and report in a **PDF of ≤ 5 pages** containing:

1. A detailed **algorithm**: how the tracking portfolio is built, the hyperparameters,
   how they are chosen, and the **estimation / validation / testing** samples.
2. A **table** of summary statistics (mean, median, variance, …) for index returns and
   tracking-portfolio returns.
3. A **figure** of cumulative returns: index vs tracking portfolio.
4. An illustration of **portfolio turnover** (table and/or figure).
5. Any other relevant figures/tables.

All tables/figures must be explained and interpreted, plus a discussion of **how
transaction costs affect the strategy**.

## 3. Tech stack

- **Python 3.11**.
- **Data:** `yfinance` (weekly adjusted prices); point-in-time constituents from a
  GitHub-hosted historical S&P 500 membership dataset; `pandas`, `pyarrow` (parquet).
- **Modeling:** `numpy`, `scipy`, `cvxpy` (convex tracking), `scikit-learn`
  (LASSO / Elastic-Net). Exact-cardinality solver TBD (Open Question 4), **pure Python
  — no R/rpy2**.
- **Viz:** `matplotlib` (primary), optionally `seaborn`.
- **Report:** notebook → PDF (`nbconvert`) or a dedicated figures notebook + short
  write-up (Open Question 5).
- **Quality:** `pytest`, `ruff` (lint), `black` (format).

## 4. Commands (provisional — will firm up in Plan)

```
# environment
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"          # or: pip install -r requirements.txt

# data (network-dependent; writes a committed snapshot under data/)
python -m index_tracking.data.fetch --index sp500 --freq weekly --years 10

# run backtest / evaluation
python -m index_tracking.backtest --method convex_sparse --k 30

# quality
pytest -q
ruff check . && black --check .

# notebooks / report
jupyter lab
```

## 5. Project structure

```
data/
  snapshot/           # committed reproducible data snapshot (parquet)
  raw_cache/          # gitignored local fetch cache
src/index_tracking/
  data/               # fetch, constituents (PIT), cleaning, caching — SOURCE-AGNOSTIC
  methods/            # tracking methods (baseline, lasso, convex, exact, ...)
  backtest/           # walk-forward engine, rebalancing, turnover, costs
  metrics/            # tracking error, summary stats, returns
  viz/                # plotting helpers
notebooks/
  01_data.ipynb              # collection, cleaning, EDA
  02_methods.ipynb           # each method explained + in-sample checks
  03_backtest_eval.ipynb     # walk-forward OOS, costs, turnover
  04_report_figures.ipynb    # final tables/figures for the PDF
reports/
  report.pdf                 # the <=5-page deliverable (+ source)
tests/                       # pytest: metrics, cleaning, methods on fixtures
pyproject.toml
README.md
.claude/                     # vendored agent-skills — DELETABLE at project end
```

**Rule:** notebooks contain narrative + calls into `src/`; **no core logic lives in
notebooks**. This keeps the code testable and the project readable from outside.

## 6. Code style

- Type hints on public functions; short docstrings; small, pure functions.
- Explicit over clever; document every modeling assumption **where it happens**.
- Missing data is handled explicitly and logged — **never silently forward-filled**.

```python
def tracking_error(port_returns: pd.Series, index_returns: pd.Series,
                   *, annualize: int | None = 52) -> float:
    """Annualized stddev of active (portfolio - index) weekly returns.

    Args:
        annualize: periods per year for annualization (52 for weekly), or None.
    """
    active = (port_returns - index_returns).dropna()
    te = active.std(ddof=1)
    return te * (annualize ** 0.5) if annualize else te
```

## 7. Methods — the "wider" set

From simplest to most sophisticated (final v1 scope = Open Question 3):

1. **Market-cap Top-K** — baseline: K largest members, cap-weighted. The bar to beat.
2. **Sparse regression (LASSO / Elastic-Net)** — L1 selects a small basket; a search
   hits the target holdings K.
3. **Convex tracking-error minimization** *(core method)* —
   `min ||R w - r_index||₂` subject to long-only, full-investment, with an ℓ1 /
   reweighted-ℓ1 sparsity term **and a turnover penalty** (transaction-cost aware).
4. **Exact cardinality** *(stretch)* — hard `‖w‖₀ = K` via mixed-integer optimization
   (pure-Python solver), replacing the draft's R-based SLAIT with an equivalent.
5. **ML approach** *(stretch)* — e.g. autoencoder-based replication or
   clustering-based selection, for the "wider / more interesting" goal.

## 8. Backtest & validation design

- **Frequency:** weekly prices; **rebalance monthly** by default (configurable) to keep
  turnover realistic (Open Question 2).
- **Walk-forward:** at each rebalance, fit on a trailing window (e.g. 1 year), hold for
  the next period, roll forward across ~10 years.
- **Sampling:** an **in-sample** span for developing + validating hyperparameters, and a
  held-out **out-of-sample** span touched only for the final test. Hyperparameters (K,
  regularization strength, window length) chosen on validation, never on test.
- **Point-in-time & survivorship:** universe = every ticker that was an S&P 500 member
  at each rebalance date (includes names later removed); no hindsight.
- **Transaction costs:** proportional cost (bps × turnover) applied at each rebalance;
  report results with and without costs, plus a cost-sensitivity sweep.

## 9. Report deliverables (maps to section 2)

| # | Deliverable | Where produced |
|---|---|---|
| 1 | Algorithm + hyperparameters + est/val/test description | `reports/`, `notebooks/02,03` |
| 2 | Summary-stats table (index vs portfolio returns) | `metrics/`, `notebooks/04` |
| 3 | Cumulative-returns figure (index vs portfolio) | `viz/`, `notebooks/04` |
| 4 | Turnover table/figure | `backtest/`, `notebooks/04` |
| 5 | Extras: tracking error over time, weights heatmap, cost sensitivity | `notebooks/04` |
| + | Transaction-cost discussion | report text |

## 10. Boundaries

- **Always:** run `pytest` before commit; keep the data layer source-agnostic; commit a
  data snapshot so results are reproducible; document assumptions openly; keep vendored
  skills confined to `.claude/`.
- **Ask first:** adding heavy dependencies (mixed-integer solver, deep-learning libs);
  changing the index/universe; anything that depends on the network policy; enlarging the
  report beyond 5 pages.
- **Never:** commit secrets; route around the egress policy; hide missing data behind
  silent fills; use point-in-time-invalid (hindsight) information in the backtest.

## 11. Success criteria (specific & testable)

- **Data:** documented coverage of PIT constituents' weekly prices over ~10y, with an
  explicit, logged missing-data policy (target: no silent gaps).
- **Tracking:** out-of-sample annualized tracking error within a stated threshold for the
  core method at the chosen K, and OOS performance ≈ in-sample (evidence of genuine
  tracking, not overfitting).
- **Report:** ≤ 5 pages, contains all five required items + transaction-cost discussion,
  every figure/table interpreted.
- **Reproducibility:** fresh clone + committed snapshot → notebooks run end-to-end
  **offline**; `pytest` green.

## 12. Open questions (please review / correct)

1. **Index universe — S&P 500 vs S&P 100.** You chose S&P 500. Caveat: `yfinance` often
   has no data for **long-delisted** tickers, so a full point-in-time S&P 500 universe
   may still show gaps. **S&P 100** (the assignment's own example) is large-cap, far more
   stable, cleaner coverage, faster iteration — and sparse tracking is just as
   illustrative. Keep S&P 500, or switch to S&P 100? (Pipeline stays index-agnostic either
   way.)
2. **Rebalance frequency** — monthly (default, realistic turnover) vs weekly (more
   reactive, higher costs)?
3. **Method scope for v1** — which of the five methods in section 7 do we implement first?
   (Suggested v1: 1 + 2 + 3; 4 and 5 as stretch.)
4. **Exact-cardinality solver** — include a pure-Python mixed-integer method, or skip the
   exact method for v1? (Avoids R entirely.)
5. **Report toolchain** — notebook → PDF via `nbconvert`, or a LaTeX write-up?
6. **Benchmark** — total-return index (matches the draft) vs price index?
