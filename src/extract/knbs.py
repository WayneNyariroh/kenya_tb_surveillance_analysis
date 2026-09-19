from __future__ import annotations

import argparse
import logging
from pathlib import Path

import pandas as pd

from .common import build_session, configure_logging, download_file, ensure_dir

LOGGER = logging.getLogger(__name__)

# Direct XLSX links currently published on the KNBS 2019 Census page.
KNBS_DATASETS = {
    "county_population": (
        "https://www.knbs.or.ke/wp-content/uploads/2023/09/"
        "2019-Kenya-population-and-Housing-Census-Population-households-density-by-county.xlsx"
    ),
    "subcounty_population": (
        "https://www.knbs.or.ke/wp-content/uploads/2023/09/"
        "2019-Kenya-population-and-Housing-Census-Population-households-density-by-sub-county.xlsx"
    ),
    "admin_units_population": (
        "https://www.knbs.or.ke/wp-content/uploads/2023/09/"
        "2019-Kenya-population-and-Housing-Census-Population-households-density-by-administrative-units.xlsx"
    ),
    "urban_population": (
        "https://www.knbs.or.ke/wp-content/uploads/2023/09/"
        "2019-Kenya-population-and-Housing-Census-Urban-population-households-density-by-county.xlsx"
    ),
    "rural_population": (
        "https://www.knbs.or.ke/wp-content/uploads/2023/09/"
        "2019-Kenya-population-and-Housing-Census-Rural-population-households-density-by-county.xlsx"
    ),
}


def _validate_excel(path: Path) -> None:
    """
    Fail early if a URL silently returned an HTML error/challenge page.
    """
    with path.open("rb") as fh:
        signature = fh.read(4)

    # Modern .xlsx files are ZIP containers and normally start with PK.
    if signature[:2] != b"PK":
        raise ValueError(
            f"{path} does not look like a valid XLSX file. "
            "The source may have returned an HTML page instead."
        )


def extract_knbs(
    output_dir: Path | str = "data/raw/knbs",
    *,
    datasets: list[str] | None = None,
    force: bool = False,
    make_csv_preview: bool = True,
) -> dict[str, Path]:
    """
    Download selected official KNBS 2019 Census spreadsheets.

    The original Excel workbooks are preserved. A simple CSV preview of the
    first sheet can optionally be created for quick inspection only. Cleaning
    belongs in the transform layer because KNBS sheets can contain titles,
    footnotes and merged-header layouts.
    """
    output_dir = ensure_dir(Path(output_dir))
    session = build_session()
    wanted = datasets or ["county_population", "subcounty_population"]

    unknown = sorted(set(wanted) - set(KNBS_DATASETS))
    if unknown:
        raise ValueError(
            f"Unknown KNBS datasets: {unknown}. Available: {sorted(KNBS_DATASETS)}"
        )

    outputs: dict[str, Path] = {}

    for name in wanted:
        xlsx_path = output_dir / f"knbs_2019_{name}.xlsx"
        download_file(
            session,
            KNBS_DATASETS[name],
            xlsx_path,
            force=force,
            min_bytes=1_000,
        )
        _validate_excel(xlsx_path)
        outputs[name] = xlsx_path

        if make_csv_preview:
            try:
                frame = pd.read_excel(xlsx_path, sheet_name=0, header=None)
                preview_path = output_dir / f"knbs_2019_{name}_sheet1_raw.csv"
                frame.to_csv(preview_path, index=False, header=False)
                LOGGER.info("Wrote raw first-sheet preview: %s", preview_path)
            except Exception as exc:
                LOGGER.warning("Could not create CSV preview for %s: %s", name, exc)

    return outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract KNBS census tables.")
    parser.add_argument("--output-dir", default="data/raw/knbs")
    parser.add_argument(
        "--dataset",
        action="append",
        choices=sorted(KNBS_DATASETS),
        help="Repeat to select datasets. Defaults to county + subcounty population.",
    )
    parser.add_argument("--no-preview", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    configure_logging(args.verbose)
    extract_knbs(
        args.output_dir,
        datasets=args.dataset,
        force=args.force,
        make_csv_preview=not args.no_preview,
    )


if __name__ == "__main__":
    main()
