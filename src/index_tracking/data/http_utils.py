"""Shared HTTP helper.

Outbound HTTPS in the hosted environment is re-terminated by an egress proxy whose CA
must be trusted; ``yfinance``/``curl_cffi`` browser-impersonation is reset by that proxy,
so the whole project fetches over plain ``requests`` with the proxy CA bundle. This helper
centralizes that (CA handling, a browser User-Agent, and on-disk caching for reproducible
offline reruns).
"""

from __future__ import annotations

import os

import requests

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0 Safari/537.36"
    )
}


def _ca_bundle() -> str | bool:
    """CA bundle for TLS verification.

    Honors the standard env vars, then falls back to the known agent-proxy bundle if
    present. Off this environment it returns ``True`` (default certifi verification).
    """
    for var in ("REQUESTS_CA_BUNDLE", "SSL_CERT_FILE"):
        path = os.environ.get(var)
        if path and os.path.exists(path):
            return path
    fallback = "/root/.ccr/ca-bundle.crt"
    return fallback if os.path.exists(fallback) else True


def custom_http_get_text(
    url: str, *, cache_path: str | None = None, force: bool = False, timeout: int = 30
) -> str:
    """GET ``url`` as text. If ``cache_path`` is given, read/write it (unless ``force``)."""
    if cache_path and os.path.exists(cache_path) and not force:
        with open(cache_path, encoding="utf-8") as fh:
            return fh.read()
    resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout, verify=_ca_bundle())
    resp.raise_for_status()
    text = resp.text
    if cache_path:
        os.makedirs(os.path.dirname(cache_path) or ".", exist_ok=True)
        with open(cache_path, "w", encoding="utf-8") as fh:
            fh.write(text)
    return text
