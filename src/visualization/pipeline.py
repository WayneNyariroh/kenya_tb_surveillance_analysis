from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from .county import plot_county_context
from .detection_gap import plot_detection_gap
from .national import plot_national_trends
from .tb_hiv import plot_tb_hiv
from .treatment import plot_treatment_outcomes
from .concentration import plot_concentration
from .maps import build_facility_map

LOGGER = logging.getLogger(__name__)


def run_visualization_pipeline(
    analysis_root: Path | str = "data/analysis",
    processed_root: Path | str = "data/processed",
    output_root: Path | str = "outputs",
) -> dict:
    analysis_root = Path(analysis_root)
    processed_root = Path(processed_root)
    output_root = Path(output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    results = {}

    steps = [
        (
            "national",
            lambda: plot_national_trends(
                analysis_root / "national",
                output_root / "figures" / "national",
            ),
        ),
        (
            "detection_gap",
            lambda: plot_detection_gap(
                analysis_root / "detection_gap",
                output_root / "figures" / "detection_gap",
            ),
        ),
        (
            "treatment",
            lambda: plot_treatment_outcomes(
                analysis_root / "treatment",
                output_root / "figures" / "treatment",
            ),
        ),
        (
            "tb_hiv",
            lambda: plot_tb_hiv(
                analysis_root / "tb_hiv",
                output_root / "figures" / "tb_hiv",
            ),
        ),
        (
            "county",
            lambda: plot_county_context(
                analysis_root / "county",
                output_root / "figures" / "county",
            ),
        ),
        (
            "concentration",
            lambda: plot_concentration(
                analysis_root / "concentration",
                output_root / "figures" / "concentration",
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
            LOGGER.warning("%s visualization skipped: %s", name, exc)
            results[name] = {"status": "skipped", "reason": str(exc)}
        except Exception as exc:
            LOGGER.exception("%s visualization failed", name)
            results[name] = {"status": "failed", "reason": str(exc)}

    try:
        facility_map = build_facility_map(
            processed_root / "kmhfr" / "dim_facility.csv",
            output_root / "maps" / "facilities.html",
        )
        results["facility_map"] = {
            "status": "ok" if facility_map else "skipped",
            "output": str(facility_map) if facility_map else None,
        }
    except ImportError as exc:
        results["facility_map"] = {
            "status": "skipped",
            "reason": str(exc),
        }
    except Exception as exc:
        LOGGER.exception("facility map failed")
        results["facility_map"] = {
            "status": "failed",
            "reason": str(exc),
        }

    manifest = output_root / "visualization_run.json"
    manifest.write_text(json.dumps(results, indent=2), encoding="utf-8")
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Kenya TB visualizations.")
    parser.add_argument("--analysis-root", default="data/analysis")
    parser.add_argument("--processed-root", default="data/processed")
    parser.add_argument("--output-root", default="outputs")
    args = parser.parse_args()

    results = run_visualization_pipeline(
        args.analysis_root,
        args.processed_root,
        args.output_root,
    )
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
