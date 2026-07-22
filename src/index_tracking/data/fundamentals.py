"""Fundamental data from Yahoo: current shares outstanding (for the cap-weighted baseline).

Yahoo's quote endpoint needs a cookie + crumb, so we do the small crumb handshake once per
session, then batch-query. Only currently-listed names return data (delisted members have no
current shares) - the cap-weighted baseline uses current shares as a documented proxy for
market cap, cap_t ~= shares_current * price_t.
"""

from __future__ import annotations

import json
import os
import time

import pandas as pd
import requests

from .http_utils import DEFAULT_HEADERS, _ca_bundle
from .prices import TICKER_RENAMES


def _yahoo_session():
    s = requests.Session()
    s.headers.update(DEFAULT_HEADERS)
    s.verify = _ca_bundle()
    try:
        s.get("https://fc.yahoo.com", timeout=15)
    except requests.RequestException:
        pass
    crumb = s.get("https://query1.finance.yahoo.com/v1/test/getcrumb", timeout=15).text
    return s, crumb


def _parse_quote_shares(payload: dict, sym_to_orig: dict) -> dict:
    """Map Yahoo quote results back to the original tickers, keeping sharesOutstanding."""
    out = {}
    for d in payload.get("quoteResponse", {}).get("result", []):
        sym, sh = d.get("symbol"), d.get("sharesOutstanding")
        if sym in sym_to_orig and sh:
            out[sym_to_orig[sym]] = float(sh)
    return out


def custom_fetch_shares_outstanding(
    tickers, *, cache_dir: str = "data/raw_cache", force: bool = False, batch: int = 100
) -> pd.Series:
    """Current shares outstanding per ticker (Series indexed by the original ticker).

    Renames are applied for the query (e.g. ``FB`` -> ``META``) and mapped back. Cached to
    disk so reruns need no network.
    """
    cache_path = os.path.join(cache_dir, "shares_outstanding.json")
    if not force and os.path.exists(cache_path):
        with open(cache_path, encoding="utf-8") as fh:
            return pd.Series(json.load(fh), dtype="float64")

    sym_to_orig = {TICKER_RENAMES.get(t, t): t for t in tickers}
    syms = list(sym_to_orig)
    session, crumb = _yahoo_session()
    out: dict[str, float] = {}
    for i in range(0, len(syms), batch):
        chunk = syms[i : i + batch]
        try:
            r = session.get(
                "https://query1.finance.yahoo.com/v7/finance/quote",
                params={"symbols": ",".join(chunk), "crumb": crumb}, timeout=30,
            )
        except requests.RequestException:
            continue
        if r.status_code == 200:
            out.update(_parse_quote_shares(r.json(), sym_to_orig))
        time.sleep(0.5)

    os.makedirs(cache_dir, exist_ok=True)
    with open(cache_path, "w", encoding="utf-8") as fh:
        json.dump(out, fh)
    return pd.Series(out, dtype="float64")
