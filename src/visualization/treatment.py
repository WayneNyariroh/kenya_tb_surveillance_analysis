from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from .common import clean_indicator_label, ensure_dir, read_required_csv
from .theme import apply_theme, save_figure


def plot_treatment_outcomes(
    analysis_dir: Path | str = "data/analysis/treatment",
    output_dir: Path | str = "outputs/figures/treatment",
) -> dict[str, Path]:
    apply_theme()
    analysis_dir = Path(analysis_dir)
    output_dir = ensure_dir(output_dir)

    path = analysis_dir / "treatment_series.csv"
    if not path.exists():
        return {}

    df = pd.read_csv(path, low_memory=False)
    if "year" not in df.columns:
        return {}

    df["year"] = pd.to_numeric(df["year"], errors="coerce")

    metrics = [
        "treatment_success_rate",
        "death_rate",
        "lost_to_followup_rate",
        "failure_rate",
        "not_evaluated_rate",
    ]
    metrics = [m for m in metrics if m in df.columns]

    group_col = next(
        (c for c in ["cohort", "treatment_group", "category"] if c in df.columns),
        None,
    )

    outputs = {}

    for metric in metrics:
        fig, ax = plt.subplots()
        if group_col:
            for group_name, group in df.groupby(group_col, dropna=False):
                y = pd.to_numeric(group[metric], errors="coerce")
                ax.plot(
                    group["year"],
                    y,
                    marker="o",
                    label=str(group_name),
                )
            ax.legend()
        else:
            y = pd.to_numeric(df[metric], errors="coerce")
            ax.plot(df["year"], y, marker="o")

        ax.set_title(clean_indicator_label(metric))
        ax.set_xlabel("Year")
        ax.set_ylabel("Percent")
        ax.set_ylim(bottom=0)
        fig.tight_layout()

        out = output_dir / f"{metric}.png"
        save_figure(fig, out)
        plt.close(fig)
        outputs[metric] = out

    return outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="Plot treatment outcome trends.")
    parser.add_argument("--analysis-dir", default="data/analysis/treatment")
    parser.add_argument("--output-dir", default="outputs/figures/treatment")
    args = parser.parse_args()
    plot_treatment_outcomes(args.analysis_dir, args.output_dir)


if __name__ == "__main__":
    main()
