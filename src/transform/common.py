from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


def ensure_dir(path: Path | str) -> Path:
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def clean_column_name(name: object) -> str:
    text = str(name).strip().lower()
    text = re.sub(r"[%/]+", "_", text)
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")


def clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    seen: dict[str, int] = {}
    names = []
    for col in out.columns:
        base = clean_column_name(col) or "unnamed"
        n = seen.get(base, 0)
        seen[base] = n + 1
        names.append(base if n == 0 else f"{base}_{n+1}")
    out.columns = names
    return out


def coerce_numeric(series: pd.Series) -> pd.Series:
    if pd.api.types.is_numeric_dtype(series):
        return pd.to_numeric(series, errors="coerce")
    cleaned = (series.astype("string").str.replace(",", "", regex=False)
               .str.replace("%", "", regex=False)
               .str.replace(r"^\s*[-–—]\s*$", pd.NA, regex=True).str.strip())
    return pd.to_numeric(cleaned, errors="coerce")


def safe_rate(numerator: pd.Series, denominator: pd.Series, multiplier: float = 100_000.0) -> pd.Series:
    num = pd.to_numeric(numerator, errors="coerce")
    den = pd.to_numeric(denominator, errors="coerce")
    values = np.where((den > 0) & den.notna(), (num / den) * multiplier, np.nan)
    return pd.Series(values, index=numerator.index, dtype="float64")


def safe_pct(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    return safe_rate(numerator, denominator, 100.0)


def first_existing(columns: Iterable[str], candidates: Iterable[str]) -> str | None:
    available = set(columns)
    return next((c for c in candidates if c in available), None)


def write_table(df: pd.DataFrame, output_path: Path | str, *, metadata: dict | None = None) -> Path:
    output_path = Path(output_path)
    ensure_dir(output_path.parent)
    if output_path.suffix.lower() == ".csv":
        df.to_csv(output_path, index=False)
    elif output_path.suffix.lower() in {".parquet", ".pq"}:
        df.to_parquet(output_path, index=False)
    else:
        raise ValueError(f"Unsupported output format: {output_path.suffix}")
    meta = {"rows": int(len(df)), "columns": list(df.columns), "output_file": output_path.name}
    if metadata: meta.update(metadata)
    output_path.with_suffix(output_path.suffix + ".metadata.json").write_text(json.dumps(meta, indent=2, default=str), encoding="utf-8")
    return output_path
