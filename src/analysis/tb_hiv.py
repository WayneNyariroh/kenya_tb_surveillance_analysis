from __future__ import annotations

import argparse
import logging
from pathlib import Path

import pandas as pd

from .common import ensure_dir, pct_change, write_csv

LOGGER = logging.getLogger(__name__)


def analyse_tb_hiv(
    indicators_dir: Path | str = "data/indicators",
    output_dir: Path | str = "data/analysis/tb_hiv",
) -> dict[str, Path]:
    """
    Summarise TB/HIV indicators already standardised by src/indicators/tb_hiv.py.
    """
    indicators_dir = Path(indicators_dir)
    output_dir = ensure_dir(output_dir)
    path = indicators_dir / "tb_hiv_long.csv"

    if not path.exists():
        LOGGER.warning("TB/HIV indicator file not found: %s", path)
        return {}

    df = pd.read_csv(path, low_memory=False)
    required = {"year", "indicator_id", "value"}
    if not required.issubset(df.columns):
        raise ValueError(f"{path.name} must contain {sorted(required)}")

    # Keep downstream report and plotting contracts stable while using the
    # canonical indicator-layer identifier as the grouping field.
    df["indicator"] = df["indicator_id"]
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["year", "indicator"]).copy()
    df["year"] = df["year"].astype(int)

    rows = []
    for indicator, group in df.groupby("indicator"):
        valid = group.dropna(subset=["value"]).sort_values("year")
        if valid.empty:
            continue
        rows.append({
            "indicator": indicator,
            "first_year": int(valid["year"].iloc[0]),
            "first_value": float(valid["value"].iloc[0]),
            "latest_year": int(valid["year"].iloc[-1]),
            "latest_value": float(valid["value"].iloc[-1]),
            "absolute_change": float(valid["value"].iloc[-1] - valid["value"].iloc[0]),
            "percent_change": pct_change(valid["value"]),
            "observations": int(len(valid)),
        })

    series_path = output_dir / "tb_hiv_series.csv"
    write_csv(df.sort_values(["indicator", "year"]), series_path)

    summary_path = output_dir / "tb_hiv_trend_summary.csv"
    write_csv(pd.DataFrame(rows), summary_path)

    return {"series": series_path, "summary": summary_path}


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyse TB/HIV indicators.")
    parser.add_argument("--indicators-dir", default="data/indicators")
    parser.add_argument("--output-dir", default="data/analysis/tb_hiv")
    args = parser.parse_args()
    analyse_tb_hiv(args.indicators_dir, args.output_dir)


if __name__ == "__main__":
    main()
