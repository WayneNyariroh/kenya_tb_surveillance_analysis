from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from .county import analyse_counties
from .detection_gap import analyse_detection_gap
from .national import analyse_national_trends
from .treatment import analyse_treatment
from .tb_hiv import analyse_tb_hiv
from .concentration import analyse_geographic_concentration
from .report_tables import build_report_tables

LOGGER = logging.getLogger(__name__)


def run_analysis_pipeline(
    indicators_dir: Path | str = "data/indicators",
    model_dir: Path | str = "data/model",
    analysis_root: Path | str = "data/analysis",
) -> dict:
    indicators_dir = Path(indicators_dir)
    model_dir = Path(model_dir)
    analysis_root = Path(analysis_root)
    analysis_root.mkdir(parents=True, exist_ok=True)

    results = {}

    steps = [
        (
            "national",
            lambda: analyse_national_trends(
                indicators_dir,
                analysis_root / "national",
            ),
        ),
        (
            "detection_gap",
            lambda: analyse_detection_gap(
                indicators_dir,
                analysis_root / "detection_gap",
            ),
        ),
        (
            "treatment",
            lambda: analyse_treatment(
                indicators_dir,
                analysis_root / "treatment",
            ),
        ),
        (
            "tb_hiv",
            lambda: analyse_tb_hiv(
                indicators_dir,
                analysis_root / "tb_hiv",
            ),
        ),
        (
            "county",
            lambda: analyse_counties(
                indicators_dir,
                model_dir,
                analysis_root / "county",
            ),
        ),
    ]

    for name, fn in steps:
        try:
            outputs = fn()
            results[name] = {
                "status": "ok",
                "outputs": {k: str(v) for k, v in outputs.items()},
            }
        except FileNotFoundError as exc:
            LOGGER.warning("%s analysis skipped: %s", name, exc)
            results[name] = {"status": "skipped", "reason": str(exc)}
        except Exception as exc:
            LOGGER.exception("%s analysis failed", name)
            results[name] = {"status": "failed", "reason": str(exc)}

    try:
        outputs = analyse_geographic_concentration(
            analysis_root / "county" / "county_context_profile.csv",
            analysis_root / "concentration",
        )
        results["concentration"] = {
            "status": "ok",
            "outputs": {k: str(v) for k, v in outputs.items()},
        }
    except Exception as exc:
        LOGGER.exception("concentration analysis failed")
        results["concentration"] = {"status": "failed", "reason": str(exc)}

    try:
        outputs = build_report_tables(
            analysis_root,
            analysis_root / "report_tables",
        )
        results["report_tables"] = {
            "status": "ok",
            "outputs": {k: str(v) for k, v in outputs.items()},
        }
    except Exception as exc:
        LOGGER.exception("report table build failed")
        results["report_tables"] = {"status": "failed", "reason": str(exc)}

    manifest = analysis_root / "analysis_run.json"
    manifest.write_text(json.dumps(results, indent=2), encoding="utf-8")
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Kenya TB case-study analyses.")
    parser.add_argument("--indicators-dir", default="data/indicators")
    parser.add_argument("--model-dir", default="data/model")
    parser.add_argument("--analysis-root", default="data/analysis")
    args = parser.parse_args()

    results = run_analysis_pipeline(
        args.indicators_dir,
        args.model_dir,
        args.analysis_root,
    )
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
