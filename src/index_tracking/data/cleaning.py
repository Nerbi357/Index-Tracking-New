"""Data-quality checks: point-in-time membership matrix and price coverage within membership.

The idea: a ticker is only interesting while it is actually an index member. If we hold a
lot of its member-weeks with no price (a reused ticker, or just sparse Yahoo history), that
name is unreliable and should be flagged or dropped rather than silently trusted.
"""

from __future__ import annotations

import pandas as pd

from .constituents import custom_members_on


def custom_membership_matrix(weekly_index, membership: pd.DataFrame, tickers) -> pd.DataFrame:
    """Boolean frame (weeks x tickers): was each ticker an index member that week?"""
    tickers = list(tickers)
    mat = pd.DataFrame(False, index=weekly_index, columns=tickers)
    col = {t: i for i, t in enumerate(tickers)}
    for wk in weekly_index:
        present = [t for t in custom_members_on(membership, wk) if t in col]
        if present:
            mat.loc[wk, present] = True
    return mat


def custom_coverage_within_membership(panel: pd.DataFrame, memb_matrix: pd.DataFrame) -> pd.DataFrame:
    """Per-ticker price coverage over the weeks the ticker was a member.

    Columns: ``ticker, member_weeks, covered_weeks, coverage`` (coverage in [0, 1]).
    """
    rows = []
    for t in memb_matrix.columns:
        is_mem = memb_matrix[t]
        member_weeks = int(is_mem.sum())
        if t in panel.columns:
            have = panel[t].reindex(memb_matrix.index).notna()
            covered = int((is_mem & have).sum())
        else:
            covered = 0
        coverage = covered / member_weeks if member_weeks else 0.0
        rows.append((t, member_weeks, covered, coverage))
    return pd.DataFrame(rows, columns=["ticker", "member_weeks", "covered_weeks", "coverage"])


def custom_quality_status(coverage: float, *, drop_below: float = 0.5, flag_below: float = 0.9) -> str:
    """Classify a ticker by its within-membership coverage: ``drop`` / ``flag`` / ``ok``."""
    if coverage < drop_below:
        return "drop"
    if coverage < flag_below:
        return "flag"
    return "ok"
