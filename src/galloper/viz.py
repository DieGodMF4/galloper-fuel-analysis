"""Small plotting helpers with sensible defaults.

Kept minimal: notebooks import these to avoid repeating matplotlib
boilerplate, but heavy/one-off charts stay inline in the notebooks.
"""
from __future__ import annotations

import matplotlib.pyplot as plt


def set_style() -> None:
    """Apply a clean, presentation-friendly default style."""
    plt.rcParams.update({
        "figure.figsize": (11, 5),
        "axes.grid": True,
        "grid.alpha": 0.3,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "font.size": 11,
    })


def savefig(fig, name: str) -> None:
    """Save a figure to reports/figures as tight PNG at 150 dpi."""
    from . import config
    config.FIGURES.mkdir(parents=True, exist_ok=True)
    fig.savefig(config.FIGURES / f"{name}.png", dpi=150, bbox_inches="tight")
