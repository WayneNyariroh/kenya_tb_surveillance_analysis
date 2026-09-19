from __future__ import annotations

import hashlib
import json
import logging
import certifi
import time
from pathlib import Path
from typing import Any, Iterable

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

LOGGER = logging.getLogger("extract")


def configure_logging(verbose: bool = False) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def build_session(
    retries: int = 5,
    backoff_factor: float = 0.8,
    user_agent: str = "kenya-tb-portfolio/1.0",
) -> requests.Session:
    retry = Retry(
        total=retries,
        connect=retries,
        read=retries,
        status=retries,
        backoff_factor=backoff_factor,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET", "HEAD"}),
        respect_retry_after_header=True,
    )
    adapter = HTTPAdapter(max_retries=retry)

    session = requests.Session()
    session.headers.update({"User-Agent": user_agent})
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.verify = certifi.where()
    return session


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_metadata(
    output_path: Path,
    *,
    source_url: str,
    status_code: int | None = None,
    content_type: str | None = None,
    extra: dict[str, Any] | None = None,
) -> Path:
    metadata = {
        "source_url": source_url,
        "file": output_path.name,
        "sha256": sha256_file(output_path) if output_path.exists() else None,
        "status_code": status_code,
        "content_type": content_type,
    }
    if extra:
        metadata.update(extra)

    meta_path = output_path.with_suffix(output_path.suffix + ".metadata.json")
    meta_path.write_text(json.dumps(metadata, indent=2, default=str), encoding="utf-8")
    return meta_path


def download_file(
    session: requests.Session,
    url: str,
    output_path: Path,
    *,
    timeout: tuple[int, int] = (10, 120),
    force: bool = False,
    min_bytes: int = 100,
) -> Path:
    ensure_dir(output_path.parent)

    if output_path.exists() and not force and output_path.stat().st_size >= min_bytes:
        LOGGER.info("Using cached file: %s", output_path)
        return output_path

    LOGGER.info("Downloading %s", url)
    with session.get(url, stream=True, timeout=timeout) as response:
        response.raise_for_status()

        tmp = output_path.with_suffix(output_path.suffix + ".part")
        with tmp.open("wb") as fh:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    fh.write(chunk)

        if tmp.stat().st_size < min_bytes:
            tmp.unlink(missing_ok=True)
            raise ValueError(
                f"Downloaded file from {url} is unexpectedly small "
                f"({tmp.stat().st_size if tmp.exists() else 0} bytes)."
            )

        tmp.replace(output_path)
        write_metadata(
            output_path,
            source_url=url,
            status_code=response.status_code,
            content_type=response.headers.get("Content-Type"),
            extra={
                "etag": response.headers.get("ETag"),
                "last_modified": response.headers.get("Last-Modified"),
            },
        )

    return output_path


def require_columns(columns: Iterable[str], required: Iterable[str], label: str) -> None:
    present = {str(c).strip() for c in columns}
    missing = [c for c in required if c not in present]
    if missing:
        raise ValueError(f"{label}: missing expected columns: {missing}")
