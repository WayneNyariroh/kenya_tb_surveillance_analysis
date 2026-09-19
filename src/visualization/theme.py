from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import matplotlib as mpl


@dataclass(frozen=True)
class ChartTheme:
    figure_width: float = 10.0
    figure_height: float = 6.0
    dpi: int = 160
    title_size: int = 16
    subtitle_size: int = 10
    label_size: int = 10
    tick_size: int = 9
    note_size: int = 8
    font_family: str = "DejaVu Sans"


DEFAULT_THEME = ChartTheme()


def apply_theme(theme: ChartTheme = DEFAULT_THEME) -> None:
    mpl.rcParams.update(
        {
            "figure.figsize": (theme.figure_width, theme.figure_height),
            "figure.dpi": theme.dpi,
            "font.family": theme.font_family,
            "axes.titlesize": theme.title_size,
            "axes.labelsize": theme.label_size,
            "xtick.labelsize": theme.tick_size,
            "ytick.labelsize": theme.tick_size,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": False,
            "legend.frameon": False,
            "savefig.bbox": "tight",
            "savefig.dpi": 220,
        }
    )


def save_figure(fig, path: Path | str) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, bbox_inches="tight")
    return path
