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
- **Data:** a thin **`requests`-based Yahoo Finance client** (chart JSON API) for weekly
  adjusted prices — confirmed working through the environment's TLS-re-terminating egress
  proxy. Note `yfinance` / `curl_cffi` browser-impersonation is **reset** by that proxy
  and is deliberately **not** used. Point-in-time constituents from a GitHub-hosted
  historical S&P 500 membership dataset. `pandas`, `pyarrow` (parquet).
- **Modeling:** `numpy`, `scipy`, `cvxpy` (convex tracking), `scikit-learn`
  (LASSO / Elastic-Net). Exact-cardinality solver TBD (Open Question 4), **pure Python
  — no R/rpy2**.
- **Viz:** `matplotlib` (primary), optionally `seaborn`.
- **Report:** notebook → PDF via `nbconvert`. Presentation quality is a first-class
  requirement — the ≤5-page PDF must look **polished, clear, and official**.
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
  snapshot/           # committed price/benchmark/constituents snapshot (parquet)
  tables/             # NB1 exported tables (universe, coverage, ...)
  raw_cache/          # gitignored local fetch cache
results/
  tables/             # NB2 exported results (metrics, backtest, turnover, robustness)
src/index_tracking/
  data/               # fetch, constituents (PIT), cleaning, caching — SOURCE-AGNOSTIC
  methods/            # tracking methods (baseline, lasso, convex, exact, ...)
  backtest/           # walk-forward engine, rebalancing, turnover, costs
  metrics/            # tracking error, summary stats, returns
  viz/                # plotting helpers (shared figure theme)
notebooks/            # DELIVERABLE notebooks — see section 13
  01_data.ipynb              # env + data import + exports  -> data/
  02_modeling.ipynb          # methods, metrics, backtests, robustness -> results/
  03_analysis.ipynb          # visualization (data -> results) + conclusions
  04_report.ipynb            # technical: assembles key items -> reports/report.pdf
reports/
  figures/            # saved figures (NB3)
  report.pdf          # the <=5-page deliverable
tests/                # pytest: metrics, cleaning, methods on fixtures
pyproject.toml
README.md
.claude/              # vendored agent-skills — DELETABLE at project end
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

## 12. Decisions (review round 1 — locked)

1. **Index:** **S&P 500.** The universe stays configurable; delisted-ticker gaps are
   handled by an explicit, logged missing-data policy (never silent fills).
2. **Rebalance frequency:** **monthly** (on weekly price data).
3. **Method scope for v1:** **decided at implementation time**, per method. The data
   pipeline and backtest engine are built method-agnostic first; the concrete v1 method
   set is chosen when we reach the methods milestone.
4. **Exact cardinality** (mixed-integer, pure Python): included as a **stretch** method.
5. **Report toolchain:** notebook → PDF via **`nbconvert`**, with **polished, clear,
   official** presentation treated as a first-class requirement.
6. **Benchmark:** S&P 500 **total-return** index (`^SP500TR`), dividends included.

**Data access (confirmed).** Live weekly fetch works via plain `requests` + the proxy CA
bundle (`REQUESTS_CA_BUNDLE` / `SSL_CERT_FILE`). Primary data risk is Yahoo rate-limiting
(429) at scale → mitigate with throttling, retry/backoff, and an on-disk cache; commit the
resulting snapshot for reproducibility.

## 13. Deliverable notebooks & ways of working

### Deliverable notebooks (final artifacts)

Three content notebooks + one technical report notebook. Working/scratch notebooks may be
created as needed and later distilled into these. The final notebooks are created up front
(empty skeletons) and **filled block-by-block after the author approves each block**:

- `notebooks/01_data.ipynb` — environment + data import; exports snapshot & tables to `data/`.
- `notebooks/02_modeling.ipynb` — all methods, metrics, walk-forward backtests, robustness;
  exports results to `results/`.
- `notebooks/03_analysis.ipynb` — visualization of the whole path (data → processing →
  results) + substantive conclusions, risks, limitations, extensions, extra sections.
- `notebooks/04_report.ipynb` — technical: gathers the key tables/figures and renders the
  polished ≤ 5-page `reports/report.pdf`.

Notebooks are **decoupled**: each reads the previous stage's exported artifacts, so they
run independently and stay reproducible.

### Notebook internal convention

Each notebook = **conceptual blocks**. For every block:
1. A short **markdown intro before the block** — what it does and **why** (the decision and
   what it is based on).
2. The **code** cells.
3. After important outputs, a **short markdown note** interpreting the result.

Notebooks must be **self-sufficient** (readable without the report). Narrative prose is in
the **author's voice** — lively, semi-formal (samples provided by the author on request).

### Code placement (hybrid)

Reusable, tested primitives live in `src/index_tracking/` (the engine). Notebooks import
them **and** show the meaningful analysis code inline with rationale, so a reader sees the
narrative + the key code without digging through `src/`.

### Ways of working (per-block, human-in-the-loop)

For every conceptual block:
1. **Discuss** the block idea + decisions with the author; get approval.
2. **Implement** in `src/` and/or a scratch notebook; verify (tests / run).
3. **Fill** the corresponding block in the final notebook (intro + code + interpretation),
   in the author's voice.
4. **Commit + push**, then tell the author exactly **where to look** (notebook, block,
   cells) and what changed.

The author reviews and corrects at **every block**. This finer granularity sits inside the
phase checkpoints in `tasks/plan.md`.
