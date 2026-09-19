from __future__ import annotations

import argparse
import logging
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from .common import clean_indicator_label, ensure_dir, read_required_csv
from .theme import apply_theme, save_figure

LOGGER = logging.getLogger(__name__)


def plot_national_trends(
    analysis_dir: Path | str = "data/analysis/national",
    output_dir: Path | str = "outputs/figures/national",
    indicators: list[str] | None = None,
) -> dict[str, Path]:
    """
    Create one line chart per national indicator.

    One chart per indicator is deliberate. Different epidemiological measures
    can have incompatible units and scales, so they are not forced onto a
    single axis.
    """
    apply_theme()
    analysis_dir = Path(analysis_dir)
    output_dir = ensure_dir(output_dir)

    path = analysis_dir / "national_indicator_series.csv"
    df = read_required_csv(path, {"year", "indicator", "value"})

    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")

    wanted = indicators or sorted(df["indicator"].dropna().unique())
    outputs: dict[str, Path] = {}

    for indicator in wanted:
        subset = (
            df[df["indicator"] == indicator]
            .dropna(subset=["year", "value"])
            .sort_values("year")
        )
        if subset.empty:
            continue

        fig, ax = plt.subplots()
        ax.plot(subset["year"], subset["value"], marker="o", linewidth=1.8)
        ax.set_title(clean_indicator_label(indicator))
        ax.set_xlabel("Year")

        unit = None
        if "unit" in subset.columns:
            units = subset["unit"].dropna().astype(str).unique()
            if len(units) == 1:
                unit = units[0]
        ax.set_ylabel(unit or "Value")

        if {"lower", "upper"}.issubset(subset.columns):
            lower = pd.to_numeric(subset["lower"], errors="coerce")
            upper = pd.to_numeric(subset["upper"], errors="coerce")
            mask = lower.notna() & upper.notna()
            if mask.any():
                ax.fill_between(
                    subset.loc[mask, "year"],
                    lower[mask],
                    upper[mask],
                    alpha=0.15,
                )

        fig.tight_layout()

        safe = "".join(c if c.isalnum() or c in "_-" else "_" for c in str(indicator))
        out = output_dir / f"{safe}.png"
        save_figure(fig, out)
        plt.close(fig)
        outputs[str(indicator)] = out

    return outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="Plot national TB trends.")
    parser.add_argument("--analysis-dir", default="data/analysis/national")
    parser.add_argument("--output-dir", default="outputs/figures/national")
    parser.add_argument("--indicator", action="append", dest="indicators")
    args = parser.parse_args()

    plot_national_trends(
        args.analysis_dir,
        args.output_dir,
        indicators=args.indicators,
    )


if __name__ == "__main__":
    main()
