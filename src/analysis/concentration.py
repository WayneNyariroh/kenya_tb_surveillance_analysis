from __future__ import annotations

import argparse
import logging
from pathlib import Path

import numpy as np
import pandas as pd

from .common import ensure_dir, write_csv

LOGGER = logging.getLogger(__name__)


def _hhi(values: pd.Series) -> float | None:
    x = pd.to_numeric(values, errors="coerce").dropna()
    x = x[x >= 0]
    total = x.sum()
    if total <= 0:
        return None
    shares = x / total
    return float((shares ** 2).sum())


def _top_share(df: pd.DataFrame, value_col: str, n: int) -> float | None:
    x = pd.to_numeric(df[value_col], errors="coerce").dropna().sort_values(ascending=False)
    total = x.sum()
    if total <= 0:
        return None
    return float(x.head(n).sum() / total * 100.0)


def analyse_geographic_concentration(
    county_file: Path | str = "data/analysis/county/county_context_profile.csv",
    output_dir: Path | str = "data/analysis/concentration",
    value_columns: list[str] | None = None,
) -> dict[str, Path]:
    """
    Calculate concentration statistics for county-level count variables.

    This becomes most useful once true county TB notifications are added.
    Until then it can still describe concentration in facilities or population.
    """
    county_file = Path(county_file)
    output_dir = ensure_dir(output_dir)

    if not county_file.exists():
        LOGGER.warning("County profile not found: %s", county_file)
        return {}

    df = pd.read_csv(county_file, low_memory=False)

    if value_columns is None:
        preferred = [
            "tb_notifications",
            "notifications",
            "facility_count",
            "population_2019",
        ]
        value_columns = [c for c in preferred if c in df.columns]

    rows = []
    for col in value_columns:
        values = pd.to_numeric(df[col], errors="coerce")
        if values.dropna().empty:
            continue

        total = values.sum(min_count=1)
        rows.append({
            "indicator": col,
            "total": float(total) if pd.notna(total) else None,
            "top_5_share_pct": _top_share(df, col, 5),
            "top_10_share_pct": _top_share(df, col, 10),
            "hhi": _hhi(values),
            "counties_with_data": int(values.notna().sum()),
        })

    out = pd.DataFrame(rows)
    path = output_dir / "geographic_concentration_summary.csv"
    write_csv(
        out,
        path,
        metadata={
            "hhi_note": (
                "HHI is the sum of squared county shares. Higher values indicate "
                "greater geographic concentration. Interpret only for comparable count measures."
            ),
        },
    )

    return {"summary": path}


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyse geographic concentration.")
    parser.add_argument(
        "--county-file",
        default="data/analysis/county/county_context_profile.csv",
    )
    parser.add_argument("--output-dir", default="data/analysis/concentration")
    parser.add_argument("--value-column", action="append", dest="value_columns")
    args = parser.parse_args()
    analyse_geographic_concentration(
        args.county_file,
        args.output_dir,
        value_columns=args.value_columns,
    )


if __name__ == "__main__":
    main()
