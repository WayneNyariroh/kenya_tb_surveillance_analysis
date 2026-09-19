from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from .common import ensure_dir, write_csv

LOGGER = logging.getLogger(__name__)


def build_report_tables(
    analysis_root: Path | str = "data/analysis",
    output_dir: Path | str = "data/analysis/report_tables",
) -> dict[str, Path]:
    """
    Build compact tables intended for notebooks, README summaries and reports.
    """
    analysis_root = Path(analysis_root)
    output_dir = ensure_dir(output_dir)
    outputs = {}

    national = analysis_root / "national" / "national_indicator_trends.csv"
    if national.exists():
        df = pd.read_csv(national)
        cols = [
            c for c in [
                "indicator", "first_year", "first_value",
                "latest_year", "latest_value", "percent_change"
            ] if c in df.columns
        ]
        table = df[cols].copy()
        path = output_dir / "table_national_change.csv"
        write_csv(table, path)
        outputs["national_change"] = path

    gap = analysis_root / "detection_gap" / "detection_gap_latest.csv"
    if gap.exists():
        df = pd.read_csv(gap)
        path = output_dir / "table_detection_gap_latest.csv"
        write_csv(df, path)
        outputs["detection_gap_latest"] = path

    treatment = analysis_root / "treatment" / "treatment_trend_summary.csv"
    if treatment.exists():
        df = pd.read_csv(treatment)
        path = output_dir / "table_treatment_summary.csv"
        write_csv(df, path)
        outputs["treatment_summary"] = path

    tb_hiv = analysis_root / "tb_hiv" / "tb_hiv_trend_summary.csv"
    if tb_hiv.exists():
        df = pd.read_csv(tb_hiv)
        path = output_dir / "table_tb_hiv_summary.csv"
        write_csv(df, path)
        outputs["tb_hiv_summary"] = path

    return outputs
