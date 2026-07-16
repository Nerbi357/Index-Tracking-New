"""Point-in-time S&P 500 constituents.

Primary source: fja05680/sp500 "S&P 500 Historical Components & Changes (Updated).csv"
(GitHub) - for each change date since 1996 it lists the full set of index members,
delisted names included, so we get a survivorship-aware universe.

Cross-check / enrichment: the current constituents table from Wikipedia (sector, CIK).

All project functions are prefixed ``custom_`` (project convention).
"""

from __future__ import annotations

import io

import pandas as pd

from .http_utils import custom_http_get_text

FJA_URL = (
    "https://raw.githubusercontent.com/fja05680/sp500/master/"
    "S%26P%20500%20Historical%20Components%20%26%20Changes%20(Updated).csv"
)
WIKI_URL = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"


def custom_normalize_ticker(ticker: str) -> str:
    """Normalize a raw ticker to Yahoo Finance convention (e.g. ``BRK.B`` -> ``BRK-B``)."""
    return ticker.strip().upper().replace(".", "-")


def custom_parse_membership(csv_text: str) -> pd.DataFrame:
    """Parse the fja05680 CSV text into a tidy membership frame.

    Returns columns ``[date (datetime64), tickers (sorted list[str], normalized)]``,
    ordered by date ascending. Kept separate from I/O so it is testable without network.
    """
    raw = pd.read_csv(io.StringIO(csv_text))
    raw["date"] = pd.to_datetime(raw["date"])

    def _split(cell: str) -> list[str]:
        return sorted({custom_normalize_ticker(t) for t in str(cell).split(",") if t.strip()})

    out = pd.DataFrame({"date": raw["date"], "tickers": raw["tickers"].map(_split)})
    return out.sort_values("date").reset_index(drop=True)


def custom_load_sp500_membership(
    *, cache_dir: str = "data/raw_cache", force: bool = False
) -> pd.DataFrame:
    """Download + parse the point-in-time S&P 500 membership (fja05680)."""
    cache_path = f"{cache_dir}/sp500_membership_fja05680.csv"
    text = custom_http_get_text(FJA_URL, cache_path=cache_path, force=force)
    return custom_parse_membership(text)


def custom_members_on(membership: pd.DataFrame, date) -> set[str]:
    """Set of index members active on ``date`` (latest change row with date <= ``date``)."""
    prior = membership[membership["date"] <= pd.Timestamp(date)]
    if prior.empty:
        return set()
    return set(prior.iloc[-1]["tickers"])


def custom_universe(membership: pd.DataFrame, *, start=None, end=None) -> list[str]:
    """Sorted union of every ticker that was a member at any point in ``[start, end]``.

    With no window, unions the whole history. With a window, includes the members active
    at ``start`` plus everyone appearing through ``end`` - i.e. the survivorship-aware set
    of assets relevant for replication over the horizon.
    """
    df = membership
    if start is not None or end is not None:
        start = pd.Timestamp(start) if start is not None else membership["date"].min()
        end = pd.Timestamp(end) if end is not None else membership["date"].max()
        base = membership[membership["date"] <= start].tail(1)
        window = membership[(membership["date"] > start) & (membership["date"] <= end)]
        df = pd.concat([base, window])
    uni: set[str] = set()
    for tickers in df["tickers"]:
        uni.update(tickers)
    return sorted(uni)


def custom_load_wikipedia_sp500(
    *, cache_dir: str = "data/raw_cache", force: bool = False
) -> pd.DataFrame:
    """Current S&P 500 constituents from Wikipedia: ticker, security, sector, cik, date_added."""
    cache_path = f"{cache_dir}/sp500_wikipedia.html"
    html = custom_http_get_text(WIKI_URL, cache_path=cache_path, force=force)
    tables = pd.read_html(io.StringIO(html))
    tbl = next((t for t in tables if "Symbol" in t.columns), tables[0])
    tbl = tbl.rename(
        columns={
            "Symbol": "ticker",
            "Security": "security",
            "GICS Sector": "sector",
            "GICS Sub-Industry": "sub_industry",
            "CIK": "cik",
            "Date added": "date_added",
        }
    )
    tbl["ticker"] = tbl["ticker"].map(custom_normalize_ticker)
    keep = [
        c
        for c in ["ticker", "security", "sector", "sub_industry", "cik", "date_added"]
        if c in tbl.columns
    ]
    return tbl[keep].reset_index(drop=True)
