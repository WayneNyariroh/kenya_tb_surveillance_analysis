from __future__ import annotations

import argparse
import logging
from pathlib import Path

import pandas as pd

from .common import ensure_dir, latest_non_null, pct_change, slope_per_year, write_csv

LOGGER = logging.getLogger(__name__)


def analyse_national_trends(
    indicators_dir: Path | str = "data/indicators",
    output_dir: Path | str = "data/analysis/national",
) -> dict[str, Path]:
    """
    Summarise long-run national TB indicators.

    Expected input:
      data/indicators/fact_tb_indicator_year.csv

    Expected columns:
      year, indicator, value
    Optional:
      lower, upper, unit, source, notes
    """
    indicators_dir = Path(indicators_dir)
    output_dir = ensure_dir(output_dir)
    path = indicators_dir / "fact_tb_indicator_year.csv"

    if not path.exists():
        raise FileNotFoundError(path)

    df = pd.read_csv(path, low_memory=False)
    required = {"year", "indicator", "value"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in {path.name}: {sorted(missing)}")

    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["year", "indicator"]).copy()
    df["year"] = df["year"].astype(int)

    summaries = []
    for indicator, group in df.groupby("indicator", dropna=False):
        group = group.sort_values("year")
        valid = group.dropna(subset=["value"])
        if valid.empty:
            continue

        first = valid.iloc[0]
        last = valid.iloc[-1]

        summaries.append({
            "indicator": indicator,
            "first_year": int(first["year"]),
            "first_value": float(first["value"]),
            "latest_year": int(last["year"]),
            "latest_value": float(last["value"]),
            "absolute_change": float(last["value"] - first["value"]),
            "percent_change": pct_change(valid["value"]),
            "annual_linear_slope": slope_per_year(valid["year"], valid["value"]),
            "observations": int(len(valid)),
        })

    summary = pd.DataFrame(summaries).sort_values("indicator").reset_index(drop=True)

    summary_path = output_dir / "national_indicator_trends.csv"
    write_csv(
        summary,
        summary_path,
        metadata={
            "grain": "indicator",
            "description": "First/latest values and long-run directional summaries for Kenya TB indicators.",
        },
    )

    tidy_path = output_dir / "national_indicator_series.csv"
    write_csv(
        df.sort_values(["indicator", "year"]),
        tidy_path,
        metadata={
            "grain": "indicator-year",
            "description": "Chart-ready national TB indicator series.",
        },
    )

    return {"summary": summary_path, "series": tidy_path}


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyse national TB indicator trends.")
    parser.add_argument("--indicators-dir", default="data/indicators")
    parser.add_argument("--output-dir", default="data/analysis/national")
    args = parser.parse_args()
    analyse_national_trends(args.indicators_dir, args.output_dir)


if __name__ == "__main__":
    main()
