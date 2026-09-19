from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from .common import clean_indicator_label, ensure_dir
from .theme import apply_theme, save_figure


def plot_county_context(
    analysis_dir: Path | str = "data/analysis/county",
    output_dir: Path | str = "outputs/figures/county",
    indicators: list[str] | None = None,
    top_n: int = 15,
) -> dict[str, Path]:
    """
    Create horizontal county comparison charts for available context measures.

    These charts do not imply a performance ranking. They simply display
    observed values for the selected measure.
    """
    apply_theme()
    analysis_dir = Path(analysis_dir)
    output_dir = ensure_dir(output_dir)

    path = analysis_dir / "county_context_profile.csv"
    if not path.exists():
        return {}

    df = pd.read_csv(path, low_memory=False)
    if "county" not in df.columns:
        return {}

    preferred = [
        "population_2019",
        "population_density_2019",
        "facility_count",
        "facilities_per_100k_2019",
        "tb_notifications",
        "notification_rate",
    ]
    indicators = indicators or [c for c in preferred if c in df.columns]

    outputs = {}

    for indicator in indicators:
        if indicator not in df.columns:
            continue

        plot_df = df[["county", indicator]].copy()
        plot_df[indicator] = pd.to_numeric(plot_df[indicator], errors="coerce")
        plot_df = plot_df.dropna().sort_values(indicator, ascending=True).tail(top_n)

        if plot_df.empty:
            continue

        height = max(5.0, min(10.0, 0.35 * len(plot_df) + 1.5))
        fig, ax = plt.subplots(figsize=(10, height))
        ax.barh(plot_df["county"], plot_df[indicator])
        ax.set_title(f"{clean_indicator_label(indicator)} by county")
        ax.set_xlabel(clean_indicator_label(indicator))
        ax.set_ylabel("")
        fig.tight_layout()

        out = output_dir / f"{indicator}_by_county.png"
        save_figure(fig, out)
        plt.close(fig)
        outputs[indicator] = out

    return outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="Plot county context indicators.")
    parser.add_argument("--analysis-dir", default="data/analysis/county")
    parser.add_argument("--output-dir", default="outputs/figures/county")
    parser.add_argument("--indicator", action="append", dest="indicators")
    parser.add_argument("--top-n", type=int, default=15)
    args = parser.parse_args()

    plot_county_context(
        args.analysis_dir,
        args.output_dir,
        indicators=args.indicators,
        top_n=args.top_n,
    )


if __name__ == "__main__":
    main()
