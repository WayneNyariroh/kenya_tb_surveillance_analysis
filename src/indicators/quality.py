from __future__ import annotations

from dataclasses import dataclass, asdict

import pandas as pd


@dataclass
class QualityCheck:
    check: str
    status: str
    details: str


def validate_indicator_table(df: pd.DataFrame) -> pd.DataFrame:
    checks: list[QualityCheck] = []

    checks.append(QualityCheck(
        "required_columns",
        "pass" if {"year", "indicator_id", "value"}.issubset(df.columns) else "fail",
        "Expected year, indicator_id and value columns.",
    ))

    if "year" in df.columns:
        years = pd.to_numeric(df["year"], errors="coerce")
        bad = int(years.isna().sum())
        checks.append(QualityCheck(
            "valid_year",
            "pass" if bad == 0 else "warn",
            f"Rows with missing/non-numeric year: {bad}",
        ))

    if {"year", "indicator_id"}.issubset(df.columns):
        dupes = int(df.duplicated(["year", "indicator_id"]).sum())
        checks.append(QualityCheck(
            "unique_indicator_year",
            "pass" if dupes == 0 else "warn",
            f"Duplicate indicator-year rows: {dupes}",
        ))

    if "unit" in df.columns and "value" in df.columns:
        pct = df["unit"].eq("percent")
        vals = pd.to_numeric(df.loc[pct, "value"], errors="coerce")
        outside = int(((vals < 0) | (vals > 100)).sum())
        checks.append(QualityCheck(
            "percentage_bounds",
            "pass" if outside == 0 else "warn",
            f"Percent values outside 0-100: {outside}",
        ))

    if "value" in df.columns:
        negative = int((pd.to_numeric(df["value"], errors="coerce") < 0).sum())
        checks.append(QualityCheck(
            "negative_values",
            "pass" if negative == 0 else "warn",
            f"Negative metric values: {negative}. Some derived gaps may legitimately be negative.",
        ))

    return pd.DataFrame([asdict(c) for c in checks])


def validate_treatment_table(df: pd.DataFrame) -> pd.DataFrame:
    checks = []
    if df.empty:
        return pd.DataFrame([{
            "check": "treatment_rows",
            "status": "warn",
            "details": "No discoverable treatment cohorts were produced.",
        }])

    if "treatment_success_pct" in df.columns:
        s = pd.to_numeric(df["treatment_success_pct"], errors="coerce")
        outside = int(((s < 0) | (s > 100)).sum())
        checks.append({
            "check": "treatment_success_bounds",
            "status": "pass" if outside == 0 else "warn",
            "details": f"Treatment success percentages outside 0-100: {outside}",
        })

    if {"cohort_size", "treatment_success_num"}.issubset(df.columns):
        c = pd.to_numeric(df["cohort_size"], errors="coerce")
        s = pd.to_numeric(df["treatment_success_num"], errors="coerce")
        exceed = int((s > c).sum())
        checks.append({
            "check": "success_not_above_cohort",
            "status": "pass" if exceed == 0 else "warn",
            "details": f"Rows where successful outcomes exceed cohort size: {exceed}",
        })

    return pd.DataFrame(checks)
