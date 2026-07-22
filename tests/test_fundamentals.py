from index_tracking.data.fundamentals import _parse_quote_shares


def test_parse_quote_shares_maps_back():
    payload = {"quoteResponse": {"result": [
        {"symbol": "META", "sharesOutstanding": 2_500_000_000},
        {"symbol": "AAPL", "sharesOutstanding": 14_000_000_000},
        {"symbol": "ZZZZ", "sharesOutstanding": 1},  # not requested -> ignored
    ]}}
    sym_to_orig = {"META": "FB", "AAPL": "AAPL"}
    out = _parse_quote_shares(payload, sym_to_orig)
    assert out == {"FB": 2.5e9, "AAPL": 1.4e10}
