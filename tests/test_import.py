"""Smoke tests for the package skeleton."""

import importlib


def test_package_imports():
    import index_tracking

    assert index_tracking.__version__


def test_subpackages_import():
    for sub in ("data", "methods", "backtest", "metrics", "viz"):
        importlib.import_module(f"index_tracking.{sub}")
