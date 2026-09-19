from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

import pandas as pd

from .burden import build_burden_indicators
from .common import ensure_dir, write_csv
from .county import build_county_indicators
from .diagnostics import build_diagnostic_inventory
from .notifications import build_notification_indicators
from .quality import validate_indicator_table, validate_treatment_table
from .tb_hiv import build_tbhiv_indicators
from .treatment import build_treatment_indicators

LOGGER = logging.getLogger(__name__)


def _read(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        LOGGER.warning("Input not found: %s", path)
        return None
    return pd.read_csv(path, low_memory=False)


def build_indicator_layer(
    processed_root: Path | str = "data/processed",
    model_root: Path | str = "data/model",
    output_dir: Path | str = "data/indicators",
) -> dict:
    processed_root = Path(processed_root)
    model_root = Path(model_root)
    output_dir = ensure_dir(output_dir)

    estimates = _read(processed_root / "who_tb" / "estimates_kenya.csv")
    notifications = _read(processed_root / "who_tb" / "notifications_kenya.csv")
    outcomes = _read(processed_root / "who_tb" / "outcomes_kenya.csv")
    county = _read(model_root / "dim_county.csv")

    outputs: dict[str, str] = {}
    long_parts = []

    if estimates is not None:
        burden = build_burden_indicators(estimates)
        if not burden.empty:
            path = write_csv(
                burden,
                output_dir / "tb_burden_long.csv",
                {"grain": "indicator-year", "country": "Kenya"},
            )
            outputs["tb_burden_long"] = str(path)
            long_parts.append(burden)

    if notifications is not None:
        notif = build_notification_indicators(notifications, estimates)
        if not notif.empty:
            path = write_csv(
                notif,
                output_dir / "tb_notifications_long.csv",
                {"grain": "indicator-year", "country": "Kenya"},
            )
            outputs["tb_notifications_long"] = str(path)
            long_parts.append(notif)

        diagnostic = build_diagnostic_inventory(notifications)
        path = write_csv(
            diagnostic,
            output_dir / "diagnostic_variable_inventory.csv",
            {"grain": "source-variable-year"},
        )
        outputs["diagnostic_variable_inventory"] = str(path)

    if estimates is not None:
        tbhiv = build_tbhiv_indicators(estimates, notifications)
        if not tbhiv.empty:
            path = write_csv(
                tbhiv,
                output_dir / "tb_hiv_long.csv",
                {"grain": "indicator-year", "country": "Kenya"},
            )
            outputs["tb_hiv_long"] = str(path)
            # Avoid duplicate core burden indicators in consolidated table.
            extra = tbhiv[~tbhiv["indicator_id"].isin(
                set(pd.concat(long_parts, ignore_index=True)["indicator_id"])
                if long_parts else set()
            )]
            if not extra.empty:
                long_parts.append(extra)

    if outcomes is not None:
        treatment = build_treatment_indicators(outcomes)
        path = write_csv(
            treatment,
            output_dir / "treatment_cohorts.csv",
            {"grain": "treatment-cohort-year", "country": "Kenya"},
        )
        outputs["treatment_cohorts"] = str(path)
        tq = validate_treatment_table(treatment)
        tq_path = write_csv(tq, output_dir / "quality_treatment.csv")
        outputs["quality_treatment"] = str(tq_path)

    if county is not None:
        county_ind = build_county_indicators(county)
        path = write_csv(
            county_ind,
            output_dir / "county_context_indicators.csv",
            {"grain": "county", "country": "Kenya"},
        )
        outputs["county_context_indicators"] = str(path)

    if long_parts:
        consolidated = pd.concat(long_parts, ignore_index=True)
        consolidated = consolidated.sort_values(["indicator_id", "year"]).reset_index(drop=True)
        path = write_csv(
            consolidated,
            output_dir / "fact_tb_indicator_year.csv",
            {
                "grain": "indicator-year",
                "country": "Kenya",
                "description": "Consolidated national TB indicator table.",
            },
        )
        outputs["fact_tb_indicator_year"] = str(path)

        quality = validate_indicator_table(consolidated)
        qpath = write_csv(quality, output_dir / "quality_indicators.csv")
        outputs["quality_indicators"] = str(qpath)

        # Analyst-friendly wide table for charts and notebooks.
        wide = consolidated.pivot_table(
            index="year", columns="indicator_id", values="value", aggfunc="first"
        ).reset_index()
        wide.columns.name = None
        wpath = write_csv(
            wide,
            output_dir / "analysis_tb_year.csv",
            {"grain": "year", "country": "Kenya"},
        )
        outputs["analysis_tb_year"] = str(wpath)

    manifest = output_dir / "indicator_run.json"
    manifest.write_text(json.dumps(outputs, indent=2), encoding="utf-8")
    outputs["manifest"] = str(manifest)
    return outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Kenya TB epidemiological indicators.")
    parser.add_argument("--processed-root", default="data/processed")
    parser.add_argument("--model-root", default="data/model")
    parser.add_argument("--output-dir", default="data/indicators")
    args = parser.parse_args()
    outputs = build_indicator_layer(args.processed_root, args.model_root, args.output_dir)
    print(json.dumps(outputs, indent=2))


if __name__ == "__main__":
    main()
