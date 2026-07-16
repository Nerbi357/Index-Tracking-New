"""Unit tests for the Yahoo chart parser (no network)."""

import json

from index_tracking.data import prices as px


def test_parse_chart_prefers_adjclose():
    payload = {
        "chart": {
            "result": [
                {
                    "timestamp": [1420156800, 1420761600],
                    "indicators": {
                        "quote": [{"close": [10.0, 11.0]}],
                        "adjclose": [{"adjclose": [9.5, 10.5]}],
                    },
                }
            ]
        }
    }
    s = px._parse_chart(json.dumps(payload), "X")
    assert s is not None
    assert list(s.values) == [9.5, 10.5]  # adjusted close preferred
    assert s.name == "X"
    assert s.index.is_monotonic_increasing


def test_parse_chart_falls_back_to_close():
    payload = {
        "chart": {
            "result": [
                {"timestamp": [1420156800], "indicators": {"quote": [{"close": [12.0]}]}}
            ]
        }
    }
    s = px._parse_chart(json.dumps(payload), "Y")
    assert list(s.values) == [12.0]


def test_parse_chart_empty_or_bad():
    assert px._parse_chart('{"chart":{"result":[]}}', "X") is None
    assert px._parse_chart("not json", "X") is None
    assert px._parse_chart('{"chart":{"result":[{"timestamp":null}]}}', "X") is None
