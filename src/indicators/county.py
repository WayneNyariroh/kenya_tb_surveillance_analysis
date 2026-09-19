from __future__ import annotations

import pandas as pd

from .common import rate_per_100k


def build_county_indicators(dim_county: pd.DataFrame) -> pd.DataFrame:
    required = {"county"}
    missing = required - set(dim_county.columns)
    if missing:
        raise ValueError(f"dim_county missing required columns: {sorted(missing)}")

    out = dim_county.copy()

    if {"facility_count", "population_2019"}.issubset(out.columns):
        out["facilities_per_100k_2019"] = rate_per_100k(
            out["facility_count"], out["population_2019"]
        )

    if {"facilities_with_valid_coordinates", "facility_count"}.issubset(out.columns):
        denom = pd.to_numeric(out["facility_count"], errors="coerce")
        num = pd.to_numeric(out["facilities_with_valid_coordinates"], errors="coerce")
        out["facility_geocode_completeness_pct"] = (num / denom.where(denom > 0)) * 100

    return out
