from __future__ import annotations

import argparse
import logging
from pathlib import Path

import pandas as pd

from .common import ensure_dir, write_csv

LOGGER = logging.getLogger(__name__)


def analyse_counties(
    indicators_dir: Path | str = "data/indicators",
    model_dir: Path | str = "data/model",
    output_dir: Path | str = "data/analysis/county",
) -> dict[str, Path]:
    """
    Create county context tables for later epidemiological analysis.

    Important limitation:
    WHO national TB datasets do not automatically provide county-level TB
    notifications. This module therefore does not fabricate county TB burden.
    It uses whatever county-level indicators are genuinely available.
    """
    indicators_dir = Path(indicators_dir)
    model_dir = Path(model_dir)
    output_dir = ensure_dir(output_dir)

    candidates = [
        indicators_dir / "county_context_indicators.csv",
        model_dir / "dim_county.csv",
    ]
    path = next((p for p in candidates if p.exists()), None)
    if path is None:
        LOGGER.warning("No county context table found.")
        return {}

    df = pd.read_csv(path, low_memory=False)

    if "county" not in df.columns:
        raise ValueError(f"{path.name} has no county column.")

    numeric_cols = [
        c for c in df.columns
        if c != "county" and pd.api.types.is_numeric_dtype(df[c])
    ]

    profile = df.copy()
    if "population_2019" in profile.columns and "facility_count" in profile.columns:
        if "facilities_per_100k_2019" not in profile.columns:
            profile["facilities_per_100k_2019"] = (
                profile["facility_count"] / profile["population_2019"] * 100_000
            ).where(profile["population_2019"] > 0)

    profile_path = output_dir / "county_context_profile.csv"
    write_csv(
        profile.sort_values("county"),
        profile_path,
        metadata={
            "grain": "county",
            "limitation": (
                "This file contains county context indicators only unless a true "
                "county-level TB programme dataset has been added upstream."
            ),
        },
    )

    summary_rows = []
    for col in numeric_cols:
        s = pd.to_numeric(profile[col], errors="coerce").dropna()
        if s.empty:
            continue
        summary_rows.append({
            "indicator": col,
            "counties_with_data": int(s.count()),
            "minimum": float(s.min()),
            "median": float(s.median()),
            "mean": float(s.mean()),
            "maximum": float(s.max()),
        })

    summary_path = output_dir / "county_context_summary.csv"
    write_csv(pd.DataFrame(summary_rows), summary_path)

    return {"profile": profile_path, "summary": summary_path}


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyse county context indicators.")
    parser.add_argument("--indicators-dir", default="data/indicators")
    parser.add_argument("--model-dir", default="data/model")
    parser.add_argument("--output-dir", default="data/analysis/county")
    args = parser.parse_args()
    analyse_counties(args.indicators_dir, args.model_dir, args.output_dir)


if __name__ == "__main__":
    main()
