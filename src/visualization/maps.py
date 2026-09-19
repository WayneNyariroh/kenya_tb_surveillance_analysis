from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

import pandas as pd

from .common import ensure_dir

LOGGER = logging.getLogger(__name__)


def build_facility_map(
    facility_file: Path | str = "data/processed/kmhfr/dim_facility.csv",
    output_file: Path | str = "outputs/maps/facilities.html",
    *,
    max_points: int | None = 5000,
) -> Path | None:
    """
    Build an interactive Folium map from facilities with valid coordinates.

    Folium is optional. If it is not installed, a clear ImportError is raised.
    """
    try:
        import folium
        from folium.plugins import MarkerCluster
    except ImportError as exc:
        raise ImportError(
            "Facility maps require folium. Install with: pip install folium"
        ) from exc

    facility_file = Path(facility_file)
    if not facility_file.exists():
        LOGGER.warning("Facility file not found: %s", facility_file)
        return None

    df = pd.read_csv(facility_file, low_memory=False)

    required = {"latitude", "longitude"}
    if not required.issubset(df.columns):
        LOGGER.warning("Facility file has no latitude/longitude columns.")
        return None

    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    df = df.dropna(subset=["latitude", "longitude"]).copy()

    if df.empty:
        return None

    if max_points is not None and len(df) > max_points:
        df = df.sample(max_points, random_state=42)

    centre = [float(df["latitude"].median()), float(df["longitude"].median())]
    m = folium.Map(location=centre, zoom_start=6, tiles="CartoDB positron")
    cluster = MarkerCluster().add_to(m)

    for _, row in df.iterrows():
        name = row.get("facility_name", "Health facility")
        county = row.get("county", "")
        ftype = row.get("facility_type", "")
        popup = "<br>".join(
            str(x) for x in [name, county, ftype]
            if pd.notna(x) and str(x).strip()
        )
        folium.Marker(
            location=[row["latitude"], row["longitude"]],
            popup=popup,
            tooltip=str(name),
        ).add_to(cluster)

    output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    m.save(output_file)
    return output_file


def build_county_choropleth(
    geojson_file: Path | str,
    county_data_file: Path | str = "data/analysis/county/county_context_profile.csv",
    output_file: Path | str = "outputs/maps/county_choropleth.html",
    *,
    indicator: str = "facilities_per_100k_2019",
    geojson_name_property: str = "COUNTY",
) -> Path | None:
    """
    Build an interactive county choropleth with Folium.

    A GeoJSON boundary file must be supplied explicitly because administrative
    boundary sources can differ in names and vintage.
    """
    try:
        import folium
    except ImportError as exc:
        raise ImportError(
            "County choropleths require folium. Install with: pip install folium"
        ) from exc

    geojson_file = Path(geojson_file)
    county_data_file = Path(county_data_file)

    if not geojson_file.exists():
        raise FileNotFoundError(geojson_file)
    if not county_data_file.exists():
        raise FileNotFoundError(county_data_file)

    df = pd.read_csv(county_data_file, low_memory=False)
    if not {"county", indicator}.issubset(df.columns):
        raise ValueError(
            f"{county_data_file.name} must contain county and {indicator!r}."
        )

    df[indicator] = pd.to_numeric(df[indicator], errors="coerce")

    geo = json.loads(geojson_file.read_text(encoding="utf-8"))

    m = folium.Map(location=[0.2, 37.8], zoom_start=6, tiles="CartoDB positron")

    folium.Choropleth(
        geo_data=geo,
        data=df,
        columns=["county", indicator],
        key_on=f"feature.properties.{geojson_name_property}",
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name=indicator.replace("_", " ").title(),
        nan_fill_opacity=0.15,
    ).add_to(m)

    output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    m.save(output_file)
    return output_file


def main() -> None:
    parser = argparse.ArgumentParser(description="Build interactive Kenya TB maps.")
    sub = parser.add_subparsers(dest="command", required=True)

    f = sub.add_parser("facilities")
    f.add_argument("--facility-file", default="data/processed/kmhfr/dim_facility.csv")
    f.add_argument("--output-file", default="outputs/maps/facilities.html")
    f.add_argument("--max-points", type=int, default=5000)

    c = sub.add_parser("county")
    c.add_argument("--geojson-file", required=True)
    c.add_argument("--county-data-file", default="data/analysis/county/county_context_profile.csv")
    c.add_argument("--output-file", default="outputs/maps/county_choropleth.html")
    c.add_argument("--indicator", default="facilities_per_100k_2019")
    c.add_argument("--geojson-name-property", default="COUNTY")

    args = parser.parse_args()

    if args.command == "facilities":
        build_facility_map(
            args.facility_file,
            args.output_file,
            max_points=args.max_points,
        )
    else:
        build_county_choropleth(
            args.geojson_file,
            args.county_data_file,
            args.output_file,
            indicator=args.indicator,
            geojson_name_property=args.geojson_name_property,
        )


if __name__ == "__main__":
    main()
