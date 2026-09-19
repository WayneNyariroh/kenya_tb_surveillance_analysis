from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

LOGGER = logging.getLogger("analysis")


def ensure_dir(path: Path | str) -> Path:
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_csv(
    df: pd.DataFrame,
    path: Path | str,
    *,
    metadata: dict | None = None,
) -> Path:
    path = Path(path)
    ensure_dir(path.parent)
    df.to_csv(path, index=False)

    meta = {
        "rows": int(len(df)),
        "columns": list(df.columns),
        "output_file": path.name,
    }
    if metadata:
        meta.update(metadata)

    path.with_suffix(path.suffix + ".metadata.json").write_text(
        json.dumps(meta, indent=2, default=str),
        encoding="utf-8",
    )
    return path


def first_present(columns: Iterable[str], candidates: Iterable[str]) -> str | None:
    available = set(columns)
    for c in candidates:
        if c in available:
            return c
    return None


def pct_change(series: pd.Series) -> float | None:
    values = pd.to_numeric(series, errors="coerce").dropna()
    if len(values) < 2:
        return None
    first, last = values.iloc[0], values.iloc[-1]
    if first == 0:
        return None
    return float((last - first) / first * 100.0)


def slope_per_year(year: pd.Series, value: pd.Series) -> float | None:
    x = pd.to_numeric(year, errors="coerce")
    y = pd.to_numeric(value, errors="coerce")
    mask = x.notna() & y.notna()
    if mask.sum() < 2:
        return None
    slope, _ = np.polyfit(x[mask], y[mask], 1)
    return float(slope)


def latest_non_null(df: pd.DataFrame, value_col: str, year_col: str = "year") -> tuple[int | None, float | None]:
    subset = df[[year_col, value_col]].copy()
    subset[year_col] = pd.to_numeric(subset[year_col], errors="coerce")
    subset[value_col] = pd.to_numeric(subset[value_col], errors="coerce")
    subset = subset.dropna().sort_values(year_col)
    if subset.empty:
        return None, None
    row = subset.iloc[-1]
    return int(row[year_col]), float(row[value_col])


def require_file(path: Path | str) -> Path:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)
    return path
