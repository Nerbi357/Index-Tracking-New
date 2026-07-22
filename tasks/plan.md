# Implementation Plan: Sparse Index Tracking of the S&P 500

> Derived from `SPEC.md`. Phase 2 ("Plan") of spec-driven development.
> Status: **DRAFT — awaiting review** before implementation begins.

## Overview

Build a reproducible, well-presented sparse index-tracking study for the S&P 500 on
weekly data (~10y), with a method-agnostic data pipeline and walk-forward backtest, then
plug in tracking methods, evaluate them (tracking error, summary stats, cumulative
returns, turnover, cost sensitivity), and produce a polished ≤5-page PDF report.

We build in **thin vertical slices**: the first end-to-end path (data → baseline method →
backtest → one figure) is delivered early to de-risk the whole pipeline, then methods and
evaluation are layered on.

**Deliverable notebooks & per-block workflow (see `SPEC.md` §13).** The three final
notebooks (`01_data`, `02_modeling`, `03_analysis`) + technical `04_report` are created as
empty skeletons and **filled block-by-block only after the author approves each block**.
The author reviews/corrects at every conceptual block; after each fill we commit and point
to exactly what changed and where to look. Notebook filling happens incrementally across
the phases below (NB1 during Phase 1, NB2 during Phases 2–3, NB3 during Phase 4, NB4 in
Phase 5), not only at the end.

## Architecture decisions (from SPEC)

- **Index:** S&P 500; **benchmark:** total-return `^SP500TR`; **rebalance:** monthly on
  weekly prices.
- **Data:** thin `requests`-based Yahoo client (curl_cffi impersonation is reset by the
  MITM egress proxy) + GitHub PIT constituents; committed parquet snapshot.
- **Structure:** logic in `src/index_tracking/`, narrative in thin notebooks, `pytest`
  throughout; synthetic fixtures let non-data code be tested offline.
- **Methods:** baseline Top-K, sparse regression, convex tracking-error min (core);
  exact-cardinality + ML as stretch. Concrete v1 set chosen at the methods milestone.

## Task list

### Phase 0 — Foundation

- **Task 1 — Project scaffolding.** Package `src/index_tracking/` with subpackages
  (`data`, `methods`, `backtest`, `metrics`, `viz`), `pyproject.toml` (deps + `[dev]`),
  `requirements.txt`, `.gitignore` (ignore `data/raw_cache/`, venv, checkpoints), `ruff`
  + `black` config, `data/{snapshot,raw_cache}/`, `tests/`, README stub.
  - *Acceptance:* `pip install -e ".[dev]"` succeeds; `import index_tracking` works;
    `pytest` runs (0 tests OK); `ruff`/`black` configured.
  - *Verify:* `pip install -e ".[dev]" && python -c "import index_tracking" && pytest -q`.
  - *Deps:* None. *Files:* ~6. *Scope:* M.

- **Task 2 — Metrics module.** Pure functions: simple/log returns, cumulative returns,
  annualized tracking error, active return, summary stats (mean/median/var/std/skew/
  kurtosis/Sharpe), turnover.
  - *Acceptance:* each metric correct on hand-computed synthetic inputs; edge cases
    (NaN, empty, misaligned index) handled.
  - *Verify:* `pytest tests/test_metrics.py -q` (green, known-value assertions).
  - *Deps:* 1. *Files:* 2. *Scope:* S.

#### Checkpoint: Foundation
- [ ] Package installs, imports, `pytest` green, tooling configured.

### Phase 1 — Data pipeline (highest risk first)

- **Task 3 — Yahoo price client.** `requests`-based client for weekly adjusted prices
  (chart JSON API, `period1/period2`, `interval=1wk`, adjusted close) and the `^SP500TR`
  benchmark. Retry with exponential backoff, polite throttling, and an on-disk cache;
  CA-bundle aware (`REQUESTS_CA_BUNDLE`/`SSL_CERT_FILE`).
  - *Acceptance:* fetches one ticker + `^SP500TR` live (weekly, multi-year) into a clean
    `DataFrame`; parsing/backoff/cache covered by fixture-based tests (no network in CI).
  - *Verify:* `pytest tests/test_yahoo_client.py -q`; manual: fetch AAPL 5y weekly, assert
    non-empty and monotonic dates.
  - *Deps:* 1. *Files:* 2–3. *Scope:* M. **Risk: Yahoo 429.**

- **Task 4 — PIT constituents loader.** Load historical S&P 500 membership from the
  GitHub dataset; expose `members_on(date) -> set[ticker]` and the full ever-member
  universe; normalize ticker symbols to Yahoo conventions.
  - *Acceptance:* returns plausible membership (~500/date), universe > 500 unique;
    symbol-normalization unit-tested.
  - *Verify:* `pytest tests/test_constituents.py -q`; manual: `members_on('2018-06-01')`
    size ≈ 500.
  - *Deps:* 1. *Files:* 2. *Scope:* S–M.

- **Task 5 — Snapshot builder + missing-data policy.** Orchestrate 3+4 to build the full
  weekly price panel for the ever-member universe (~10y), apply an explicit, **logged**
  missing-data policy (documented coverage, no silent fills), and write a committed
  parquet snapshot + a coverage report.
  - *Acceptance:* `data/snapshot/prices_weekly.parquet` + `benchmark.parquet` +
    `coverage.md` produced; coverage stats logged; snapshot loads offline.
  - *Verify:* run builder; assert snapshot shape/date range; `pytest` for the
    cleaning/missing-data logic on fixtures.
  - *Deps:* 3, 4. *Files:* 2–3. *Scope:* M. **Risk: delisted-ticker gaps.**

#### Checkpoint: Data
- [ ] Committed snapshot exists, coverage documented, all data tests green.
- [ ] **Review with human** (data quality, universe size, missing-data policy).

### Phase 2 — Backtest engine + first method (vertical slice)

- **Task 6 — Method interface + baseline.** `TrackingMethod` protocol
  (`fit(prices, index) -> weights`), plus **market-cap Top-K** baseline (K largest,
  cap-weighted).
  - *Acceptance:* baseline returns valid weights (≥0, sum 1, exactly K non-zero);
    unit-tested on fixtures.
  - *Verify:* `pytest tests/test_methods_baseline.py -q`.
  - *Deps:* 1, 2. *Files:* 2. *Scope:* S–M.

- **Task 7 — Walk-forward backtest engine.** Monthly rebalance on weekly data; trailing
  training window; in-sample vs out-of-sample split; proportional transaction costs
  (configurable bps); records weights, turnover, and net/gross returns per period; PIT
  universe per rebalance date (no hindsight).
  - *Acceptance:* runs a method over a fixture panel; costs + turnover computed correctly;
    no look-ahead (unit-tested).
  - *Verify:* `pytest tests/test_backtest.py -q` (incl. a no-look-ahead assertion).
  - *Deps:* 2, 6. *Files:* 2–3. *Scope:* M.

- **Task 8 — First end-to-end run.** Baseline Top-K on the real snapshot → tracking error,
  summary stats, and a cumulative-returns figure (portfolio vs `^SP500TR`).
  - *Acceptance:* end-to-end script/notebook produces a saved figure + printed metrics on
    real data.
  - *Verify:* manual: figure renders, portfolio tracks index visibly; metrics finite.
  - *Deps:* 5, 6, 7. *Files:* 1–2. *Scope:* S.

#### Checkpoint: End-to-end baseline
- [ ] Full pipeline works on real data; one figure + metrics produced.
- [ ] **Review with human** before adding methods.

### Phase 3 — Methods (v1 scope decided here)

- **Task 9 — Sparse regression method.** LASSO / Elastic-Net tracking with a cardinality
  search to hit target K.
  - *Acceptance:* selects ≈K names; weights valid; unit-tested on fixtures.
  - *Verify:* `pytest tests/test_methods_lasso.py -q`. *Deps:* 6, (2). *Files:* 2. *Scope:* M.

- **Task 10 — Convex tracking-error minimization (core).** `cvxpy`: minimize tracking
  error s.t. long-only + full-investment, with ℓ1 / reweighted-ℓ1 sparsity **and a
  turnover penalty** (cost-aware).
  - *Acceptance:* solves on fixtures; K controllable; turnover penalty reduces turnover;
    unit-tested. *Verify:* `pytest tests/test_methods_convex.py -q`. *Deps:* 6. *Files:* 2. *Scope:* M.

- **Task 11 — (Stretch) Exact cardinality.** Mixed-integer formulation (hard `‖w‖₀=K`)
  via an available pure-Python MIP solver; heuristic fallback.
  - *Acceptance:* exact K holdings on a small fixture; documented solver. *Deps:* 6, 10.
    *Files:* 1–2. *Scope:* M.

- **Task 12 — (Stretch) ML method.** e.g. autoencoder / clustering-based selection.
  - *Acceptance:* produces a valid sparse portfolio; documented. *Deps:* 6. *Files:* 2. *Scope:* M.

#### Checkpoint: Methods
- [ ] Chosen v1 methods implemented + unit-tested; multi-method comparison runs.

### Phase 4 — Evaluation & notebooks

- **Task 13 — Evaluation suite.** Reusable comparison across methods/K: summary-stats
  table, cumulative-returns figure, turnover table+figure, tracking-error-over-time,
  weights heatmap, transaction-cost sensitivity sweep.
  - *Acceptance:* one call → all tables/figures for a set of methods; figures saved to
    `reports/figures/`. *Verify:* manual review of outputs; `pytest` for table builders.
  - *Deps:* 7, 9–10. *Files:* 3–4. *Scope:* M–L (split if needed).

- **Task 14 — Consolidate content notebooks 01–03.** These are filled incrementally
  block-by-block across earlier phases (SPEC §13); this task is the final consolidation +
  clean top-to-bottom execution, with each block carrying intro + code + interpretation in
  the author's voice.
  - *Acceptance:* `01_data`, `02_modeling`, `03_analysis` execute cleanly via
    `nbconvert --execute`; self-sufficient and in the author's voice. *Verify:*
    `jupyter nbconvert --to notebook --execute notebooks/0{1,2,3}_*.ipynb`.
  - *Deps:* 8, 13. *Files:* 3. *Scope:* M.

### Phase 5 — Report

- **Task 15 — Technical report notebook → polished PDF (≤5 pages).** Fill
  `notebooks/04_report.ipynb`: gather the key tables/figures from `results/` and
  `reports/figures/`, explain the study step by step, render via `nbconvert`; professional/
  official styling; all 5 required items + transaction-cost discussion, every item
  interpreted.
  - *Acceptance:* `reports/report.pdf` ≤5 pages, contains items 1–5 + cost discussion,
    looks polished/official. *Verify:* build PDF; page count ≤5; visual review.
  - *Deps:* 13, 14. *Files:* 2–3. *Scope:* M.

#### Checkpoint: Complete
- [ ] All SPEC success criteria met; report renders; `pytest` green; reproducible from
  snapshot; ready for final review.

## Risks and mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Yahoo rate-limiting (429) at scale | High | Throttle + exponential backoff + on-disk cache; incremental fetch; commit snapshot so re-runs need no network |
| Delisted tickers missing from Yahoo (PIT gaps) | Med | Explicit logged missing-data policy; document coverage; optionally restrict to names with sufficient history |
| `cvxpy` solver availability/convergence | Med | Use bundled solvers (ECOS/OSQP/SCS); fallbacks; scale/condition inputs |
| MIP solver for exact cardinality | Med | Use available MI solver or heuristic; it is a stretch method |
| Report polish via `nbconvert` | Med | Custom CSS/LaTeX template + shared figure theme; treat presentation as first-class |
| Session ephemerality | Low | Commit + push after each task/checkpoint |

## Open questions (non-blocking; defaults chosen)

- **Transaction cost:** default **10 bps** proportional per turnover (configurable); report a sweep.
- **Training window:** default **52 weeks** trailing (tunable on validation).
- **K values to study:** default **{10, 30, 50}**.
- **Universe handling:** full ever-member set vs a min-history-filtered subset (decide at Task 5 from observed coverage).
- **Method v1 scope:** decided at the Phase 3 milestone (per SPEC decision 3).
