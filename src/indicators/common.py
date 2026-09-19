from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

LOGGER = logging.getLogger("indicators")


def ensure_dir(path: Path | str) -> Path:
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def safe_divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    num = numeric(numerator)
    den = numeric(denominator)
    result = np.where((den > 0) & den.notna(), num / den, np.nan)
    return pd.Series(result, index=numerator.index, dtype="float64")


def rate_per_100k(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    return safe_divide(numerator, denominator) * 100_000


def percentage(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    return safe_divide(numerator, denominator) * 100


def first_present(columns: Iterable[str], candidates: Iterable[str]) -> str | None:
    cols = set(columns)
    for candidate in candidates:
        if candidate in cols:
            return candidate
    return None


def write_csv(df: pd.DataFrame, path: Path | str, metadata: dict | None = None) -> Path:
    path = Path(path)
    ensure_dir(path.parent)
    df.to_csv(path, index=False)
    meta = {
        "rows": int(len(df)),
        "columns": list(df.columns),
        "file": path.name,
    }
    if metadata:
        meta.update(metadata)
    path.with_suffix(path.suffix + ".metadata.json").write_text(
        json.dumps(meta, indent=2, default=str), encoding="utf-8"
    )
    return path


def tidy_metric(
    df: pd.DataFrame,
    *,
    year_col: str,
    value_col: str,
    indicator_id: str,
    indicator_name: str,
    unit: str,
    source: str,
    lower_col: str | None = None,
    upper_col: str | None = None,
    notes: str | None = None,
) -> pd.DataFrame:
    out = pd.DataFrame({
        "year": pd.to_numeric(df[year_col], errors="coerce").astype("Int64"),
        "indicator_id": indicator_id,
        "indicator_name": indicator_name,
        "value": numeric(df[value_col]),
        "unit": unit,
        "source": source,
        "source_variable": value_col,
    })
    out["lower"] = numeric(df[lower_col]) if lower_col and lower_col in df.columns else np.nan
    out["upper"] = numeric(df[upper_col]) if upper_col and upper_col in df.columns else np.nan
    out["notes"] = notes
    return out
