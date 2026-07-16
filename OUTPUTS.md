# Outputs map — what each notebook produces and where

Source of truth = **your own run** of the notebooks. Each notebook regenerates its
artifacts from live sources (Yahoo Finance, GitHub constituents). After running, export the
files below to these folders. Numbers may differ slightly from any prior run because
Yahoo's free data changes over time (that is expected and documented in the notebooks).

## `notebooks/01_data.ipynb` → data stage
- `data/snapshot/prices_weekly.parquet` — weekly adjusted-close panel (universe)
- `data/snapshot/benchmark.parquet` — `^SP500TR` weekly level
- `data/snapshot/returns_weekly.parquet` — weekly simple returns (tradable universe)
- `data/snapshot/benchmark_returns.parquet` — benchmark weekly returns
- `data/tables/universe.csv` — ever-member universe
- `data/tables/constituents_membership.parquet` — point-in-time membership by date
- `data/tables/wikipedia_current.csv` — current members + sector / CIK
- `data/tables/price_coverage.csv` — per-ticker observation count
- `data/tables/coverage_by_date.csv` — member coverage per rebalance date
- `data/tables/missing_tickers.csv` — names with no price
- `data/tables/data_quality.csv` — per-ticker within-membership coverage + status
- `data/tables/shares_outstanding.csv` — current shares outstanding (cap-weighted baseline)

## `notebooks/02_modeling.ipynb` → results (reads NB1 exports)
_to be filled as we build it_

## `notebooks/03_analysis.ipynb` → figures (reads NB2 results)
_to be filled as we build it_

## `notebooks/04_report.ipynb` → `reports/report.pdf`
_to be filled as we build it_

## Regenerating from scratch
Delete `data/snapshot/` and `data/tables/*.csv`, then run `01 → 02 → 03` in order. Each
notebook rebuilds from live sources; nothing depends on an ad-hoc script.
