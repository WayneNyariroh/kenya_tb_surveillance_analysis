from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .common import build_session, configure_logging, download_file, ensure_dir

LOGGER = logging.getLogger(__name__)

# UNAIDS AIDS Data Repository is a CKAN site. Its catalogue/API is public.
CKAN_BASE = "https://adr.unaids.org"
PACKAGE_SEARCH_URL = f"{CKAN_BASE}/api/3/action/package_search"
PACKAGE_SHOW_URL = f"{CKAN_BASE}/api/3/action/package_show"

KENYA_ORG = "kenya-moh"


class ResourceRequiresLogin(RuntimeError):
    pass


def _ckan_get(session, endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
    response = session.get(endpoint, params=params, timeout=(10, 60))
    response.raise_for_status()
    payload = response.json()
    if not payload.get("success"):
        raise RuntimeError(f"CKAN API returned success=false: {payload}")
    return payload["result"]


def search_kenya_hiv_packages(query: str = "HIV Estimates", rows: int = 50) -> list[dict]:
    """
    Search public CKAN metadata for Kenya MoH datasets.

    This does not authenticate and does not bypass resource access controls.
    """
    session = build_session()
    result = _ckan_get(
        session,
        PACKAGE_SEARCH_URL,
        {
            "q": query,
            "fq": f"organization:{KENYA_ORG}",
            "rows": rows,
        },
    )
    return result.get("results", [])


def get_package(package_id: str) -> dict:
    session = build_session()
    return _ckan_get(session, PACKAGE_SHOW_URL, {"id": package_id})


def _safe_filename(resource: dict) -> str:
    name = (resource.get("name") or resource.get("id") or "resource").strip()
    fmt = (resource.get("format") or "").strip().lower()
    safe = "".join(c if c.isalnum() or c in "._-" else "_" for c in name)
    if fmt and not safe.lower().endswith(f".{fmt}"):
        safe = f"{safe}.{fmt}"
    return safe


def _looks_like_login_page(response) -> bool:
    final_url = str(response.url).lower()
    content_type = response.headers.get("Content-Type", "").lower()
    text = ""
    if "text/html" in content_type:
        text = response.text[:5000].lower()

    return (
        "login" in final_url
        or "log in" in text
        or "register to access resource" in text
        or "sign in" in text
    )


def download_public_resource(
    resource_url: str,
    output_path: Path,
    *,
    force: bool = False,
) -> Path:
    """
    Download a UNAIDS ADR resource only if it is actually public.

    Current Kenya HIV Estimates packages may expose public metadata while
    requiring login for their underlying files. In that case this function
    raises ResourceRequiresLogin rather than trying to circumvent access.
    """
    session = build_session()

    if output_path.exists() and not force and output_path.stat().st_size > 100:
        return output_path

    response = session.get(
        resource_url,
        allow_redirects=True,
        stream=False,
        timeout=(10, 120),
    )

    if response.status_code in (401, 403) or _looks_like_login_page(response):
        raise ResourceRequiresLogin(
            "This UNAIDS ADR resource requires login/registration. "
            "The extractor will not bypass that access control."
        )

    response.raise_for_status()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(response.content)
    return output_path


def extract_hiv_resources(
    output_dir: Path | str = "data/raw/hiv",
    *,
    query: str = "Kenya HIV Estimates",
    package_id: str | None = None,
    formats: tuple[str, ...] = ("CSV", "XLSX", "GEOJSON", "ZIP"),
    download: bool = False,
    force: bool = False,
) -> dict[str, Any]:
    """
    Discover Kenya HIV resources in the UNAIDS AIDS Data Repository.

    By default, writes metadata only. Set download=True to attempt downloads.
    Any resource that requires authentication is skipped and reported.

    This design is deliberate: as of the current portal, the catalogue is
    publicly queryable, while some current Kenya HIV Estimates resource files
    require login.
    """
    output_dir = ensure_dir(Path(output_dir))
    session = build_session()

    if package_id:
        packages = [get_package(package_id)]
    else:
        result = _ckan_get(
            session,
            PACKAGE_SEARCH_URL,
            {
                "q": query,
                "fq": f"organization:{KENYA_ORG}",
                "rows": 50,
            },
        )
        packages = result.get("results", [])

    if not packages:
        raise ValueError("No Kenya HIV packages matched the search.")

    allowed = {f.upper() for f in formats}
    manifest: list[dict[str, Any]] = []

    for package in packages:
        package_name = package.get("name")
        title = package.get("title")

        for resource in package.get("resources", []):
            fmt = str(resource.get("format") or "").upper()
            if allowed and fmt not in allowed:
                continue

            item = {
                "package_id": package.get("id"),
                "package_name": package_name,
                "package_title": title,
                "resource_id": resource.get("id"),
                "resource_name": resource.get("name"),
                "format": fmt,
                "url": resource.get("url"),
                "last_modified": resource.get("last_modified"),
                "downloaded": False,
                "status": "metadata_only",
            }

            if download and resource.get("url"):
                target_dir = ensure_dir(output_dir / str(package_name))
                target = target_dir / _safe_filename(resource)
                try:
                    download_public_resource(
                        resource["url"],
                        target,
                        force=force,
                    )
                    item["downloaded"] = True
                    item["status"] = "downloaded"
                    item["local_path"] = str(target)
                except ResourceRequiresLogin as exc:
                    item["status"] = "requires_login"
                    item["error"] = str(exc)
                except Exception as exc:
                    item["status"] = "download_failed"
                    item["error"] = str(exc)

            manifest.append(item)

    manifest_path = output_dir / "unaids_kenya_hiv_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    LOGGER.info("Wrote %s resource records to %s", len(manifest), manifest_path)

    return {
        "manifest": manifest_path,
        "packages": len(packages),
        "resources": len(manifest),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Discover/download public Kenya HIV resources from UNAIDS ADR."
    )
    parser.add_argument("--output-dir", default="data/raw/hiv")
    parser.add_argument("--query", default="Kenya HIV Estimates")
    parser.add_argument("--package-id")
    parser.add_argument(
        "--format",
        action="append",
        dest="formats",
        help="Repeat to select formats, e.g. --format CSV --format GEOJSON",
    )
    parser.add_argument(
        "--download",
        action="store_true",
        help="Attempt downloads. Login-protected resources are skipped.",
    )
    parser.add_argument("--force", action="store_true")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    configure_logging(args.verbose)
    extract_hiv_resources(
        args.output_dir,
        query=args.query,
        package_id=args.package_id,
        formats=tuple(args.formats or ("CSV", "XLSX", "GEOJSON", "ZIP")),
        download=args.download,
        force=args.force,
    )


if __name__ == "__main__":
    main()
