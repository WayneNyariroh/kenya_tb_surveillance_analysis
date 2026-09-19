from __future__ import annotations

import argparse
import json
import logging
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Any

from src.extract.who_tb import extract_who_tb
from src.extract.knbs import extract_knbs
from src.extract.kmhfr import extract_kmhfr_facilities
from src.extract.hiv import extract_hiv_resources

from src.transform.pipeline import run_transform_pipeline
from src.indicators.pipeline import build_indicator_layer
from src.analysis.pipeline import run_analysis_pipeline
from src.visualization.pipeline import run_visualization_pipeline


PROJECT_ROOT = Path(__file__).resolve().parent
LOG_DIR = PROJECT_ROOT / "logs"
RUN_DIR = PROJECT_ROOT / "runs"


def setup_logging(verbose: bool = False) -> tuple[logging.Logger, Path]:
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOG_DIR / f"pipeline_{timestamp}.log"

    logger = logging.getLogger("kenya_tb_pipeline")
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    logger.handlers.clear()

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if verbose else logging.INFO)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # Capture logs emitted by project modules as well.
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    root_logger.handlers.clear()
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    return logger, log_file


def serialise_outputs(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(k): serialise_outputs(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [serialise_outputs(v) for v in value]
    return value


def run_step(name: str, func: Callable[[], Any], logger: logging.Logger,) -> dict:
    logger.info("=" * 72)
    logger.info("STARTING: %s", name)

    started = time.perf_counter()
    started_at = datetime.now(timezone.utc).isoformat()

    try:
        output = func()
        elapsed = time.perf_counter() - started

        logger.info(
            "COMPLETED: %s in %.2f seconds",
            name,
            elapsed,
        )

        return {
            "step": name,
            "status": "success",
            "started_at": started_at,
            "duration_seconds": round(elapsed, 3),
            "outputs": serialise_outputs(output),
            "error": None,
        }

    except Exception as exc:
        elapsed = time.perf_counter() - started

        logger.error(
            "FAILED: %s after %.2f seconds",
            name,
            elapsed,
        )
        logger.error("%s: %s", type(exc).__name__, exc)
        logger.debug(traceback.format_exc())

        return {
            "step": name,
            "status": "failed",
            "started_at": started_at,
            "duration_seconds": round(elapsed, 3),
            "outputs": None,
            "error": {
                "type": type(exc).__name__,
                "message": str(exc),
                "traceback": traceback.format_exc(),
            },
        }


def build_steps( *, skip_hiv: bool = False, skip_maps: bool = False,) -> list[tuple[str, Callable[[], Any]]]:
    data_raw = PROJECT_ROOT / "data" / "raw"
    data_processed = PROJECT_ROOT / "data" / "processed"
    data_model = PROJECT_ROOT / "data" / "model"
    data_indicators = PROJECT_ROOT / "data" / "indicators"
    data_analysis = PROJECT_ROOT / "data" / "analysis"
    outputs = PROJECT_ROOT / "outputs"

    steps: list[tuple[str, Callable[[], Any]]] = [
        (
            "Extract WHO TB data",
            lambda: extract_who_tb(
                data_raw / "who_tb",
            ),
        ),
        (
            "Extract KNBS population data",
            lambda: extract_knbs(
                data_raw / "knbs",
            ),
        ),
        (
            "Extract KMHFR facilities",
            lambda: extract_kmhfr_facilities(
                data_raw / "kmhfr",
            ),
        ),
    ]

    if not skip_hiv:
        steps.append(
            (
                "Discover public HIV resources",
                lambda: extract_hiv_resources(
                    data_raw / "hiv",
                    download=True,
                ),
            )
        )

    steps.extend(
        [
            (
                "Transform raw data",
                lambda: run_transform_pipeline(
                    raw_root=data_raw,
                    processed_root=data_processed,
                    model_root=data_model,
                ),
            ),
            (
                "Build epidemiological indicators",
                lambda: build_indicator_layer(
                    processed_root=data_processed,
                    model_root=data_model,
                    output_dir=data_indicators,
                ),
            ),
            (
                "Run analytical case study",
                lambda: run_analysis_pipeline(
                    indicators_dir=data_indicators,
                    model_dir=data_model,
                    analysis_root=data_analysis,
                ),
            ),
            (
                "Generate visualizations",
                lambda: run_visualization_pipeline(
                    analysis_root=data_analysis,
                    processed_root=data_processed,
                    output_root=outputs,
                ),
            ),
        ]
    )

    return steps


def write_run_summary(
    results: list[dict],
    log_file: Path,
    started_at: str,
    elapsed_seconds: float,
) -> Path:
    RUN_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    summary_file = RUN_DIR / f"pipeline_run_{timestamp}.json"

    success_count = sum(r["status"] == "success" for r in results)
    failed_count = sum(r["status"] == "failed" for r in results)

    summary = {
        "project": "Kenya TB Case Study",
        "started_at": started_at,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "duration_seconds": round(elapsed_seconds, 3),
        "log_file": str(log_file),
        "steps_total": len(results),
        "steps_successful": success_count,
        "steps_failed": failed_count,
        "status": "success" if failed_count == 0 else "completed_with_errors",
        "steps": results,
    }

    summary_file.write_text(
        json.dumps(summary, indent=2, default=str),
        encoding="utf-8",
    )

    return summary_file


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run the complete Kenya TB data pipeline from extraction through "
            "visualization."
        )
    )
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Continue to later layers after a failed step.",
    )
    parser.add_argument(
        "--skip-hiv",
        action="store_true",
        help="Skip UNAIDS HIV resource discovery/download attempts.",
    )
    parser.add_argument(
        "--skip-maps",
        action="store_true",
        help=(
            "Reserved for future map-specific pipeline control. "
            "Static visualizations still run."
        ),
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show DEBUG-level logging in the terminal.",
    )
    args = parser.parse_args()

    logger, log_file = setup_logging(args.verbose)

    pipeline_started = time.perf_counter()
    pipeline_started_at = datetime.now(timezone.utc).isoformat()

    logger.info("Kenya TB Case Study pipeline")
    logger.info("Project root: %s", PROJECT_ROOT)
    logger.info("Log file: %s", log_file)

    steps = build_steps(
        skip_hiv=args.skip_hiv,
        skip_maps=args.skip_maps,
    )

    results: list[dict] = []

    for name, func in steps:
        result = run_step(name, func, logger)
        results.append(result)

        if result["status"] == "failed" and not args.continue_on_error:
            logger.error(
                "Pipeline stopped because '%s' failed.",
                name,
            )
            logger.error(
                "Use --continue-on-error if you want later steps attempted."
            )
            break

    elapsed = time.perf_counter() - pipeline_started

    summary_file = write_run_summary(
        results,
        log_file,
        pipeline_started_at,
        elapsed,
    )

    failures = [r for r in results if r["status"] == "failed"]

    logger.info("=" * 72)
    logger.info("PIPELINE FINISHED")
    logger.info("Duration: %.2f seconds", elapsed)
    logger.info(
        "Successful steps: %s | Failed steps: %s",
        len(results) - len(failures),
        len(failures),
    )
    logger.info("Run summary: %s", summary_file)
    logger.info("Detailed log: %s", log_file)

    if failures:
        logger.error("Pipeline completed with errors.")
        return 1

    logger.info("Pipeline completed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
