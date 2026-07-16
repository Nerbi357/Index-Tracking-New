# TODO — Sparse Index Tracking (S&P 500)

Task detail lives in `tasks/plan.md`. Check off as completed.

## Phase 0 — Foundation
- [x] Task 1 — Project scaffolding (package, pyproject, tooling, dirs)
- [ ] Task 2 — Metrics module (returns, tracking error, summary stats, turnover) + tests
- [x] **Checkpoint:** installs, imports, `pytest` green

## Phase 1 — Data pipeline
- [ ] Task 3 — Yahoo price client (`requests`, backoff, cache) + `^SP500TR`
- [x] Task 4 — PIT constituents loader (GitHub) + `members_on(date)` + Wikipedia cross-check
- [ ] Task 5 — Snapshot builder + missing-data policy → committed parquet + coverage
- [ ] **Checkpoint:** snapshot committed, coverage documented — **review with human**

## Phase 2 — Backtest engine + first method (vertical slice)
- [ ] Task 6 — Method interface + market-cap Top-K baseline + tests
- [ ] Task 7 — Walk-forward backtest engine (monthly, costs, turnover, no look-ahead)
- [ ] Task 8 — First end-to-end run: baseline → tracking error + cumulative-returns figure
- [ ] **Checkpoint:** end-to-end works on real data — **review with human**

## Phase 3 — Methods (v1 scope decided here)
- [ ] Task 9 — Sparse regression (LASSO / Elastic-Net + cardinality search)
- [ ] Task 10 — Convex tracking-error minimization (core; sparsity + turnover penalty)
- [ ] Task 11 — (Stretch) Exact cardinality (mixed-integer)
- [ ] Task 12 — (Stretch) ML method (autoencoder / clustering)
- [ ] **Checkpoint:** chosen methods tested; comparison runs

## Phase 4 — Evaluation & notebooks
- [ ] Task 13 — Evaluation suite (stats table, cumulative, turnover, TE-over-time, heatmap, cost sweep)
- [ ] Task 14 — Notebooks 01–04 (thin, call `src/`), execute cleanly

## Phase 5 — Report
- [ ] Task 15 — Polished ≤5-page PDF via `nbconvert` (all 5 items + cost discussion)
- [ ] **Checkpoint:** success criteria met; reproducible; ready for review
