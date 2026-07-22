"""Shared matplotlib theme, so every figure across the notebooks looks consistent."""

from __future__ import annotations

import matplotlib.pyplot as plt

PALETTE = ["#2563eb", "#dc2626", "#059669", "#d97706", "#7c3aed"]


def custom_set_style() -> None:
    """Apply the project's plotting style (call once, e.g. in the setup block)."""
    plt.rcParams.update(
        {
            "figure.figsize": (9, 4.5),
            "figure.dpi": 110,
            "savefig.dpi": 110,
            "savefig.bbox": "tight",
            "axes.grid": True,
            "grid.alpha": 0.25,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.titlesize": 13,
            "axes.titleweight": "bold",
            "axes.labelsize": 11,
            "font.size": 11,
            "legend.frameon": False,
            "axes.prop_cycle": plt.cycler(color=PALETTE),
        }
    )
