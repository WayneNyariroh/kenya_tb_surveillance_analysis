# Visualization layer

`src/visualization/` converts the case-study analysis tables into reusable figures
and maps.

The notebook should call these modules or embed the generated files. It should
not contain dozens of one-off plotting cells.

## Static figures

Matplotlib is used for the static figures.

Generated folders:

```text
outputs/figures/
├── national/
├── detection_gap/
├── treatment/
├── tb_hiv/
├── county/
└── concentration/
```

Each major measure is drawn on its own chart instead of combining unrelated
scales on one axis.

### National trends

`national.py` makes one chart per indicator and displays WHO lower/upper
uncertainty bounds when those fields are available.

### Detection gap

`detection_gap.py` produces:

```text
incidence_vs_notifications.png
notification_incidence_gap.png
notification_to_incidence_ratio.png
```

The figures distinguish modelled incidence from observed programme notifications.

### Treatment outcomes

`treatment.py` plots available treatment outcome rates over time.

### TB/HIV

`tb_hiv.py` produces one chart per standardised TB/HIV measure.

### County context

`county.py` creates county comparison charts for genuine available variables such
as population, population density, facility counts and, later, county TB
indicators.

The charts are descriptive comparisons, not performance rankings.

### Geographic concentration

`concentration.py` plots the share of national totals accounted for by the top
five and top ten counties when valid county-level counts exist.

---

# Interactive maps

`maps.py` uses Folium when installed.

Install:

```bash
pip install folium
```

## Facility map

```bash
python -m src.visualization.maps facilities
```

Output:

```text
outputs/maps/facilities.html
```

Facilities with valid coordinates are clustered for performance.

## County choropleth

A county GeoJSON file must be supplied explicitly:

```bash
python -m src.visualization.maps county \
    --geojson-file data/raw/boundaries/kenya_counties.geojson \
    --indicator facilities_per_100k_2019
```

The boundary file is not hard-coded because Kenya administrative boundary files
can differ by source, property names and publication date.

---

# Run the visualization pipeline

```bash
python -m src.visualization.pipeline
```

The pipeline writes:

```text
outputs/visualization_run.json
```

so missing optional data or skipped visualizations remain visible.

---

# Project flow

The project now follows:

```text
extract
   ↓
transform
   ↓
indicators
   ↓
analysis
   ↓
visualization
```

The next layer should be the case-study notebook/report layer, which consumes
these outputs and tells the analytical story without repeating ETL or indicator
logic.
