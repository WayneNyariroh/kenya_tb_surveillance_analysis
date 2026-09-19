from __future__ import annotations

import argparse
import io
import logging
from pathlib import Path

import pandas as pd

from .common import build_session, configure_logging, download_file, ensure_dir

LOGGER = logging.getLogger(__name__)

# These three download endpoints are linked directly from WHO's current TB data page.
WHO_DATASETS = {
    "estimates": "https://extranet.who.int/tme/generateCSV.asp?ds=estimates",
    "notifications": "https://extranet.who.int/tme/generateCSV.asp?ds=notifications",
    "outcomes": "https://extranet.who.int/tme/generateCSV.asp?ds=outcomes",
}

KENYA_ISO3 = "KEN"


def _find_country_column(df: pd.DataFrame) -> str:
    candidates = ("iso3", "country", "country_name")
    for col in candidates:
        if col in df.columns:
            return col
    raise ValueError(
        "WHO CSV does not contain one of the expected country columns: "
        f"{candidates}. Columns begin: {list(df.columns[:20])}"
    )


def _filter_kenya(df: pd.DataFrame) -> pd.DataFrame:
    col = _find_country_column(df)
    if col == "iso3":
        out = df[df[col].astype(str).str.upper().eq(KENYA_ISO3)].copy()
    else:
        out = df[df[col].astype(str).str.strip().str.casefold().eq("kenya")].copy()

    if out.empty:
        raise ValueError(f"No Kenya records found using WHO column {col!r}.")
    return out


def extract_who_tb(
    output_dir: Path | str = "data/raw/who_tb",
    *,
    datasets: list[str] | None = None,
    kenya_only: bool = True,
    force: bool = False,
) -> dict[str, Path]:
    """
    Download WHO Global TB Database CSV extracts.

    Raw source files are preserved. If kenya_only=True, a second Kenya-only CSV
    is written beside each source file.

    Returns a mapping from dataset name to the primary output path.
    """
    output_dir = ensure_dir(Path(output_dir))
    session = build_session()
    wanted = datasets or list(WHO_DATASETS)

    unknown = sorted(set(wanted) - set(WHO_DATASETS))
    if unknown:
        raise ValueError(
            f"Unknown WHO datasets: {unknown}. Available: {sorted(WHO_DATASETS)}"
        )

    outputs: dict[str, Path] = {}

    for name in wanted:
        raw_path = output_dir / f"who_tb_{name}.csv"
        download_file(session, WHO_DATASETS[name], raw_path, force=force, min_bytes=1_000)
        outputs[name] = raw_path

        if kenya_only:
            df = pd.read_csv(raw_path, low_memory=False)
            kenya = _filter_kenya(df)
            kenya_path = output_dir / f"who_tb_{name}_kenya.csv"
            kenya.to_csv(kenya_path, index=False)
            LOGGER.info("Wrote %s rows to %s", len(kenya), kenya_path)

    return outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract WHO TB data.")
    parser.add_argument("--output-dir", default="data/raw/who_tb")
    parser.add_argument(
        "--dataset",
        action="append",
        choices=sorted(WHO_DATASETS),
        help="Repeat to select datasets. Defaults to all.",
    )
    parser.add_argument("--all-countries", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    configure_logging(args.verbose)
    extract_who_tb(
        args.output_dir,
        datasets=args.dataset,
        kenya_only=not args.all_countries,
        force=args.force,
    )


if __name__ == "__main__":
    main()
