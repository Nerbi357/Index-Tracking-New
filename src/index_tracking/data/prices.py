"""Weekly price fetching from Yahoo Finance via plain requests.

``curl_cffi``/``yfinance`` browser-impersonation is reset by the egress proxy, so we call
the public chart JSON API directly, with throttling, exponential backoff and a per-ticker
on-disk cache (so reruns need no network and results are reproducible).
"""

from __future__ import annotations

import io
import json
import os
import random
import time

import pandas as pd
import requests

from .http_utils import DEFAULT_HEADERS, _ca_bundle

_CHART = "https://query1.finance.yahoo.com/v8/finance/chart/{t}"

# Historical -> current Yahoo symbol, for genuine rebrands/symbol-changes of the SAME
# entity (Yahoo carries the pre-change history under the new symbol). Acquisitions, where
# the old ticker is a different company, are intentionally excluded.
TICKER_RENAMES: dict[str, str] = {
    "FB": "META",  # Facebook -> Meta
    "ANTM": "ELV",  # Anthem -> Elevance
    "FISV": "FI",  # Fiserv symbol change
    "WLTW": "WTW",  # Willis Towers Watson symbol change
    "FBHS": "FBIN",  # Fortune Brands rebrand
    "CTL": "LUMN",  # CenturyLink -> Lumen
    "KORS": "CPRI",  # Michael Kors -> Capri
    "VIAC": "PARA",  # ViacomCBS -> Paramount
    "COG": "CTRA",  # Cabot Oil -> Coterra
    "HFC": "DINO",  # HollyFrontier -> HF Sinclair
    "DISCA": "WBD",  # Discovery -> Warner Bros. Discovery
    "DISCK": "WBD",
}


def _chart_url(ticker: str) -> str:
    return _CHART.format(t=requests.utils.quote(ticker, safe="^"))


def _parse_chart(text: str, name: str) -> pd.Series | None:
    """Extract a weekly adjusted-close Series from a Yahoo chart JSON payload."""
    try:
        result = json.loads(text)["chart"]["result"]
    except (KeyError, TypeError, json.JSONDecodeError):
        return None
    if not result:
        return None
    r = result[0]
    ts = r.get("timestamp")
    if not ts:
        return None
    ind = r.get("indicators", {})
    adj = ind.get("adjclose")
    if adj and adj[0].get("adjclose"):
        values = adj[0]["adjclose"]
    else:
        quote = ind.get("quote")
        values = quote[0].get("close") if quote else None
    if not values:
        return None
    s = pd.Series(values, index=pd.to_datetime(ts, unit="s"), name=name)
    return s[~s.index.duplicated(keep="last")].sort_index()


def custom_fetch_one(
    ticker: str,
    start,
    end,
    *,
    cache_dir: str = "data/raw_cache/prices",
    retries: int = 5,
    base_sleep: float = 0.6,
    throttle: float = 0.25,
    force: bool = False,
) -> pd.Series | None:
    """Weekly adjusted-close Series for one ticker, or ``None`` if Yahoo has no data."""
    p1 = int(pd.Timestamp(start).timestamp())
    p2 = int(pd.Timestamp(end).timestamp())
    cache_path = os.path.join(cache_dir, f"{ticker}.json")

    if not force and os.path.exists(cache_path):
        with open(cache_path, encoding="utf-8") as fh:
            return _parse_chart(fh.read(), ticker)

    params = {
        "period1": p1,
        "period2": p2,
        "interval": "1wk",
        "events": "div,splits",
        "includeAdjustedClose": "true",
    }
    text = None
    for attempt in range(retries):
        try:
            resp = requests.get(
                _chart_url(ticker), params=params, headers=DEFAULT_HEADERS,
                timeout=30, verify=_ca_bundle(),
            )
        except requests.RequestException:
            time.sleep(base_sleep * (2**attempt))
            continue
        if resp.status_code == 200:
            text = resp.text
            break
        if resp.status_code in (429, 503, 999):
            time.sleep(base_sleep * (2**attempt) + random.random() * 0.4)
            continue
        break  # 404 / 400: ticker not available
    time.sleep(throttle)  # polite pause after a network hit
    if text is None:
        return None
    os.makedirs(cache_dir, exist_ok=True)
    with open(cache_path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return _parse_chart(text, ticker)


def custom_fetch_weekly_prices(tickers, start, end, *, renames: dict | None = TICKER_RENAMES, **kw):
    """Fetch weekly adjusted close for many tickers (Yahoo).

    Known rebrands are mapped **proactively** (e.g. ``FB`` is fetched as ``META``) and kept
    under the original name - this both fills the history and avoids the reused-ticker trap
    where an old symbol now points at a different company.

    Returns ``(panel, failed)``: a wide DataFrame (weekly dates x tickers) and the list of
    tickers Yahoo returned nothing for.
    """
    renames = renames or {}
    series: dict[str, pd.Series] = {}
    failed: list[str] = []
    for ticker in tickers:
        symbol = renames.get(ticker, ticker)
        s = custom_fetch_one(symbol, start, end, **kw)
        if s is None or s.dropna().empty:
            failed.append(ticker)
        else:
            s.name = ticker
            series[ticker] = s
    panel = pd.DataFrame(series).sort_index() if series else pd.DataFrame()
    return panel, failed


_STOOQ = "https://stooq.com/q/d/l/"


def custom_fetch_stooq_one(
    ticker: str, start, end, *, cache_dir: str = "data/raw_cache/stooq",
    throttle: float = 0.2, force: bool = False,
) -> pd.Series | None:
    """Weekly close for one ticker from Stooq (fallback source; note: **unadjusted**)."""
    sym = f"{ticker.lower()}.us"
    cache_path = os.path.join(cache_dir, f"{ticker}.csv")
    if not force and os.path.exists(cache_path):
        with open(cache_path, encoding="utf-8") as fh:
            text = fh.read()
    else:
        params = {
            "s": sym, "i": "w",
            "d1": pd.Timestamp(start).strftime("%Y%m%d"),
            "d2": pd.Timestamp(end).strftime("%Y%m%d"),
        }
        try:
            resp = requests.get(_STOOQ, params=params, headers=DEFAULT_HEADERS,
                                timeout=30, verify=_ca_bundle())
        except requests.RequestException:
            return None
        time.sleep(throttle)
        if resp.status_code != 200 or not resp.text.startswith("Date"):
            return None
        text = resp.text
        os.makedirs(cache_dir, exist_ok=True)
        with open(cache_path, "w", encoding="utf-8") as fh:
            fh.write(text)
    try:
        df = pd.read_csv(io.StringIO(text))
        if df.empty or "Close" not in df.columns:
            return None
        return pd.Series(df["Close"].to_numpy(), index=pd.to_datetime(df["Date"]),
                         name=ticker).sort_index()
    except (ValueError, KeyError):
        return None


def custom_recover_via_stooq(failed, start, end, **kw):
    """Try to recover Yahoo-missing tickers from Stooq. Returns ``(recovered, still_missing)``."""
    recovered: dict[str, pd.Series] = {}
    still: list[str] = []
    for ticker in failed:
        s = custom_fetch_stooq_one(ticker, start, end, **kw)
        if s is not None and not s.dropna().empty:
            recovered[ticker] = s
        else:
            still.append(ticker)
    return recovered, still
