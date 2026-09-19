from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from .common import clean_indicator_label, ensure_dir, read_required_csv
from .theme import apply_theme, save_figure


def plot_tb_hiv(
    analysis_dir: Path | str = "data/analysis/tb_hiv",
    output_dir: Path | str = "outputs/figures/tb_hiv",
) -> dict[str, Path]:
    apply_theme()
    analysis_dir = Path(analysis_dir)
    output_dir = ensure_dir(output_dir)

    path = analysis_dir / "tb_hiv_series.csv"
    if not path.exists():
        return {}

    df = read_required_csv(path, {"year", "indicator", "value"})
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")

    outputs = {}
    for indicator, group in df.groupby("indicator"):
        group = group.dropna(subset=["year", "value"]).sort_values("year")
        if group.empty:
            continue

        fig, ax = plt.subplots()
        ax.plot(group["year"], group["value"], marker="o")
        ax.set_title(clean_indicator_label(indicator))
        ax.set_xlabel("Year")

        unit = None
        if "unit" in group.columns:
            units = group["unit"].dropna().astype(str).unique()
            if len(units) == 1:
                unit = units[0]
        ax.set_ylabel(unit or "Value")

        fig.tight_layout()
        safe = "".join(c if c.isalnum() or c in "_-" else "_" for c in str(indicator))
        out = output_dir / f"{safe}.png"
        save_figure(fig, out)
        plt.close(fig)
        outputs[str(indicator)] = out

    return outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="Plot TB/HIV trends.")
    parser.add_argument("--analysis-dir", default="data/analysis/tb_hiv")
    parser.add_argument("--output-dir", default="outputs/figures/tb_hiv")
    args = parser.parse_args()
    plot_tb_hiv(args.analysis_dir, args.output_dir)


if __name__ == "__main__":
    main()
