from __future__ import annotations

import argparse
import logging
from pathlib import Path

import pandas as pd

from .common import ensure_dir, write_csv

LOGGER = logging.getLogger(__name__)


def _pivot_indicator_table(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, low_memory=False)
    if {"year", "indicator", "value"}.issubset(df.columns):
        wide = (
            df.pivot_table(index="year", columns="indicator", values="value", aggfunc="first")
            .reset_index()
        )
        wide.columns.name = None
        return wide
    return df


def analyse_detection_gap(
    indicators_dir: Path | str = "data/indicators",
    output_dir: Path | str = "data/analysis/detection_gap",
) -> dict[str, Path]:
    """
    Analyse the gap between estimated incident TB and notified TB.

    The function looks for already-derived indicator names rather than guessing
    raw WHO variable meanings.

    Preferred names:
      estimated_incident_tb
      notifications
      notification_incidence_gap
      notification_to_incidence_ratio
    """
    indicators_dir = Path(indicators_dir)
    output_dir = ensure_dir(output_dir)

    candidates = [
        indicators_dir / "analysis_tb_year.csv",
        indicators_dir / "fact_tb_indicator_year.csv",
    ]
    path = next((p for p in candidates if p.exists()), None)
    if path is None:
        raise FileNotFoundError("No analysis_tb_year.csv or fact_tb_indicator_year.csv found.")

    wide = _pivot_indicator_table(path)

    aliases = {
        "estimated_incident_tb": [
            "estimated_incident_tb",
            "estimated_incidence_count",
            "incidence_estimate",
            "tb_incident_estimate",
        ],
        "notifications": [
            "notifications",
            "tb_notifications",
            "notified_cases",
            "case_notifications",
        ],
        "gap": [
            "notification_incidence_gap",
            "incidence_notification_gap",
            "estimated_minus_notified",
        ],
        "ratio": [
            "notification_to_incidence_ratio",
            "notifications_to_incidence_pct",
        ],
    }

    def find_col(names):
        for name in names:
            if name in wide.columns:
                return name
        return None

    year_col = "year" if "year" in wide.columns else None
    est_col = find_col(aliases["estimated_incident_tb"])
    notif_col = find_col(aliases["notifications"])
    gap_col = find_col(aliases["gap"])
    ratio_col = find_col(aliases["ratio"])

    if year_col is None:
        raise ValueError("Detection-gap input has no year column.")

    result = pd.DataFrame({"year": wide["year"]})

    if est_col:
        result["estimated_incident_tb"] = pd.to_numeric(wide[est_col], errors="coerce")
    if notif_col:
        result["notifications"] = pd.to_numeric(wide[notif_col], errors="coerce")

    if gap_col:
        result["notification_incidence_gap"] = pd.to_numeric(wide[gap_col], errors="coerce")
    elif {"estimated_incident_tb", "notifications"}.issubset(result.columns):
        result["notification_incidence_gap"] = (
            result["estimated_incident_tb"] - result["notifications"]
        )

    if ratio_col:
        result["notification_to_incidence_ratio"] = pd.to_numeric(
            wide[ratio_col], errors="coerce"
        )
    elif {"estimated_incident_tb", "notifications"}.issubset(result.columns):
        result["notification_to_incidence_ratio"] = (
            result["notifications"] / result["estimated_incident_tb"] * 100
        ).where(result["estimated_incident_tb"] > 0)

    if len(result.columns) == 1:
        raise ValueError(
            "No recognised detection-gap indicators were found. "
            "Run the indicators layer first or extend aliases in detection_gap.py."
        )

    result = result.sort_values("year").reset_index(drop=True)

    latest = result.dropna(how="all", subset=[c for c in result.columns if c != "year"])
    summary_rows = []
    if not latest.empty:
        row = latest.iloc[-1]
        summary_rows.append({
            "latest_year": int(row["year"]),
            "estimated_incident_tb": row.get("estimated_incident_tb"),
            "notifications": row.get("notifications"),
            "notification_incidence_gap": row.get("notification_incidence_gap"),
            "notification_to_incidence_ratio": row.get("notification_to_incidence_ratio"),
        })

    series_path = output_dir / "detection_gap_by_year.csv"
    write_csv(
        result,
        series_path,
        metadata={
            "grain": "year",
            "caution": (
                "The notification-to-incidence ratio compares observed notifications "
                "with a modelled incidence estimate. It is not labelled a measured case-detection rate."
            ),
        },
    )

    summary_path = output_dir / "detection_gap_latest.csv"
    write_csv(pd.DataFrame(summary_rows), summary_path)

    return {"series": series_path, "latest": summary_path}


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyse TB incidence-notification gap.")
    parser.add_argument("--indicators-dir", default="data/indicators")
    parser.add_argument("--output-dir", default="data/analysis/detection_gap")
    args = parser.parse_args()
    analyse_detection_gap(args.indicators_dir, args.output_dir)


if __name__ == "__main__":
    main()
