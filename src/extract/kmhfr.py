from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any

import pandas as pd

from .common import build_session, configure_logging, ensure_dir, write_metadata

LOGGER = logging.getLogger(__name__)

KMHFR_FACILITIES_URL = "https://api.kmhfr.health.go.ke/api/public/facilities/"


def _records_from_payload(payload: Any) -> tuple[list[dict[str, Any]], str | None]:
    """
    Support the common Django REST Framework response shape:
      {"count": ..., "next": "...", "previous": ..., "results": [...]}

    Also tolerate a bare list.
    """
    if isinstance(payload, list):
        return payload, None

    if not isinstance(payload, dict):
        raise ValueError(f"Unexpected KMHFR response type: {type(payload).__name__}")

    for key in ("results", "data", "facilities"):
        if isinstance(payload.get(key), list):
            return payload[key], payload.get("next")

    raise ValueError(
        "KMHFR payload did not contain a recognised records list. "
        f"Top-level keys: {list(payload)[:30]}"
    )


def extract_kmhfr_facilities(
    output_dir: Path | str = "data/raw/kmhfr",
    *,
    page_size: int = 100,
    force: bool = False,
    max_pages: int | None = None,
) -> dict[str, Path]:
    """
    Extract all facilities from the public KMHFR endpoint.

    Outputs:
      - facilities.ndjson: faithful raw-ish record stream
      - facilities.csv: flattened tabular copy for inspection
      - extraction_summary.json
    """
    output_dir = ensure_dir(Path(output_dir))
    ndjson_path = output_dir / "facilities.ndjson"
    csv_path = output_dir / "facilities.csv"
    summary_path = output_dir / "extraction_summary.json"

    if (
        not force
        and ndjson_path.exists()
        and csv_path.exists()
        and ndjson_path.stat().st_size > 1_000
    ):
        LOGGER.info("Using cached KMHFR extraction in %s", output_dir)
        return {"ndjson": ndjson_path, "csv": csv_path, "summary": summary_path}

    session = build_session()
    url: str | None = KMHFR_FACILITIES_URL
    params: dict[str, Any] | None = {"page": 1, "page_size": page_size}

    all_records: list[dict[str, Any]] = []
    page = 0
    seen_urls: set[str] = set()

    while url:
        page += 1
        if max_pages is not None and page > max_pages:
            break

        LOGGER.info("KMHFR page %s", page)
        response = session.get(url, params=params, timeout=(10, 90))
        response.raise_for_status()

        content_type = response.headers.get("Content-Type", "")
        if "json" not in content_type.lower():
            preview = response.text[:250].replace("\n", " ")
            raise ValueError(
                "KMHFR did not return JSON. "
                f"Content-Type={content_type!r}; body starts {preview!r}"
            )

        payload = response.json()
        records, next_url = _records_from_payload(payload)
        all_records.extend(records)

        if not records:
            break

        # If the API supplies a next link, use it. Otherwise increment page.
        if next_url:
            if next_url in seen_urls:
                raise RuntimeError(f"KMHFR pagination loop detected at {next_url}")
            seen_urls.add(next_url)
            url = next_url
            params = None
        else:
            # Bare-list / non-next response fallback.
            if len(records) < page_size:
                break
            url = KMHFR_FACILITIES_URL
            params = {"page": page + 1, "page_size": page_size}

    if not all_records:
        raise ValueError("KMHFR extraction returned zero facilities.")

    with ndjson_path.open("w", encoding="utf-8") as fh:
        for record in all_records:
            fh.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")

    flat = pd.json_normalize(all_records, sep=".")
    flat.to_csv(csv_path, index=False)

    summary = {
        "source_url": KMHFR_FACILITIES_URL,
        "records": len(all_records),
        "pages_requested": page,
        "columns": list(flat.columns),
    }
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    write_metadata(
        ndjson_path,
        source_url=KMHFR_FACILITIES_URL,
        extra={"records": len(all_records), "pages_requested": page},
    )
    write_metadata(
        csv_path,
        source_url=KMHFR_FACILITIES_URL,
        extra={"records": len(all_records), "columns": len(flat.columns)},
    )

    LOGGER.info("Extracted %s KMHFR facilities", len(all_records))
    return {"ndjson": ndjson_path, "csv": csv_path, "summary": summary_path}


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract Kenya KMHFR facilities.")
    parser.add_argument("--output-dir", default="data/raw/kmhfr")
    parser.add_argument("--page-size", type=int, default=100)
    parser.add_argument("--max-pages", type=int)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    configure_logging(args.verbose)
    extract_kmhfr_facilities(
        args.output_dir,
        page_size=args.page_size,
        max_pages=args.max_pages,
        force=args.force,
    )


if __name__ == "__main__":
    main()
