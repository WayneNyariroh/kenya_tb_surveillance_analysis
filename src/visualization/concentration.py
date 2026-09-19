from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from .common import clean_indicator_label, ensure_dir
from .theme import apply_theme, save_figure


def plot_concentration(
    analysis_dir: Path | str = "data/analysis/concentration",
    output_dir: Path | str = "outputs/figures/concentration",
) -> dict[str, Path]:
    apply_theme()
    analysis_dir = Path(analysis_dir)
    output_dir = ensure_dir(output_dir)

    path = analysis_dir / "geographic_concentration_summary.csv"
    if not path.exists():
        return {}

    df = pd.read_csv(path)
    if "indicator" not in df.columns:
        return {}

    outputs = {}

    share_cols = [c for c in ["top_5_share_pct", "top_10_share_pct"] if c in df.columns]
    if share_cols:
        plot_df = df[["indicator"] + share_cols].copy()
        plot_df = plot_df.set_index("indicator")
        ax = plot_df.plot(kind="bar", figsize=(10, 6))
        ax.set_title("Geographic concentration of county-level counts")
        ax.set_xlabel("")
        ax.set_ylabel("Share of national total (%)")
        ax.tick_params(axis="x", rotation=30)
        fig = ax.get_figure()
        fig.tight_layout()

        out = output_dir / "top_county_shares.png"
        save_figure(fig, out)
        plt.close(fig)
        outputs["top_county_shares"] = out

    return outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="Plot geographic concentration.")
    parser.add_argument("--analysis-dir", default="data/analysis/concentration")
    parser.add_argument("--output-dir", default="outputs/figures/concentration")
    args = parser.parse_args()
    plot_concentration(args.analysis_dir, args.output_dir)


if __name__ == "__main__":
    main()
