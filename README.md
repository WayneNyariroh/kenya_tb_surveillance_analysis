# Kenya TB Surveillance Analysis

## Wayne Willis Omondi

This repository builds a reproducible Kenya tuberculosis surveillance case study from public data. It extracts source files, prepares consistent tables, defines indicators, produces descriptive analyses, and writes figures and run records.

The national analysis uses WHO tuberculosis data. County work is limited to population and health-service context unless a genuine county-level TB programme dataset is added. The project does not allocate national TB estimates to counties.

## Current status

The WHO national pipeline is working and produces national trends, notification-gap outputs, treatment summaries, TB/HIV summaries, and figures.

The county population step can use local KNBS workbook copies when the KNBS website cannot be reached. The live KMHFR facility API is an external dependency. If it is unavailable, the pipeline continues without facility counts, county facility-density analysis, or the facility map when run with `--continue-on-error`.

## Questions covered

- How have estimated TB incidence, mortality, and notifications changed in Kenya?
- How do notified cases compare with estimated incidence?
- What do available treatment-cohort outcomes show over time?
- Which TB/HIV measures are available in the current WHO data?
- How do population and facility availability vary across counties when the required source data are available?

The notification-incidence comparison is descriptive. Estimated incidence is modelled, while notifications come from programme reporting. Their difference can reflect diagnosis, reporting, surveillance completeness, and model uncertainty. It is not automatically a measured case-detection rate.

## Sources

| Source | Used for | Notes |
|---|---|---|
| WHO Global TB Database | National burden estimates, notifications, treatment outcomes | Raw files and Kenya-only extracts are kept under `data/raw/who_tb/`. |
| Kenya National Bureau of Statistics, 2019 Census | County and subcounty population tables | The default pipeline uses county and subcounty workbooks. |
| Kenya Master Health Facility Registry | Facility-level service context | Used for facility counts, ownership, type, operational status, and coordinates when available. |
| UNAIDS AIDS Data Repository | Kenya HIV resource discovery | Public metadata are retained. Files requiring login are not bypassed. |

The KNBS census page is the source for the population workbooks. Boundary files for choropleths must be supplied separately because boundary vintages and county names vary by publisher.

## Project layout

```text
run_pipeline.py              Pipeline runner
requirements.txt             Python dependencies
src/extract/                 Download and source-provenance code
src/transform/               Source-specific cleaning and standardisation
src/indicators/              Indicator definitions and quality checks
src/analysis/                Descriptive tables and summaries
src/visualization/           Static figures and optional maps
data/raw/                    Source snapshots
data/processed/              Cleaned source tables
data/model/                  Shared model tables
data/indicators/             Indicator tables
data/analysis/               Analysis tables
outputs/                     Figures and maps
logs/                        Timestamped pipeline logs
runs/                        Machine-readable run summaries
```
The workflow is:

```text
  Data sources
        ↓
     Extract
        ↓
    Transform
        ↓
    Indicators
        ↓
     Analysis
        ↓
   Visualization
        
```

Extraction, cleaning, indicator calculations, analysis and chart logic all live in separated reusable modules. This makes the pipeline easier to review, reproduce and extend in future. And honestly made, and still makes, debugging easier.

![dq-engine-logic-structure](assets/mermaid-diagram.png)

## Setup

Create and activate a virtual environment.

Windows:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

macOS or Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

## Run the pipeline

From the repository root:

```bash
python run_pipeline.py 
```

By default the run stops at the first failed step. To let later stages use available or cached data after an optional source fails:

```bash
python run_pipeline.py --continue-on-error
```

Each run writes a log in `logs/` and a JSON summary in `runs/`. The summary records the status, duration, outputs, and error details for every attempted step.

## KNBS local cache

The KNBS extractor checks for the following files before it makes a network request:

```text
data/raw/knbs/knbs_2019_county_population.xlsx
data/raw/knbs/knbs_2019_subcounty_population.xlsx
```

If a file exists and is at least 1 KB, the extractor uses it as a cache entry. This allows verified manual downloads to be used when KNBS is unavailable from the current network.

KNBS uses longer filenames for its original downloads. Keep those originals if useful, then copy them to the cache names above. The transform layer reads the cache names, not the original download names.

The default extractor requests only county and subcounty population data. It does not use the administrative-unit, urban, or rural workbooks unless the code is extended or the extractor is called with an explicit dataset selection.

## KMHFR input and fallback

The KMHFR transform layer reads one file:

```text
data/raw/kmhfr/facilities.csv
```

The live extractor normally creates that file from the KMHFR API, together with `facilities.ndjson` and `extraction_summary.json`. A verified local facility export can also be used if it is converted to `facilities.csv`.

At minimum, the CSV needs a facility name, using one of `name`, `facility_name`, or `official_name`. The following fields make the county and map outputs useful:

```text
id or facility code
county
subcounty
ward
ownership
facility type
KEPH level
operational status
latitude
longitude
```

The transformer accepts several common source names for these fields. It writes `data/processed/kmhfr/dim_facility.csv` and, when county is present, `county_facility_summary.csv`.

If the live API cannot be reached, do not turn off certificate verification. Use a verified local snapshot or run with `--continue-on-error` while investigating network access.

## What each layer does

### Extract

The extract layer saves source files without changing their meaning. It uses retries, timeouts, local caching, metadata files, and hashes where applicable.

WHO outputs include the original data and Kenya-only extracts:

```text
data/raw/who_tb/who_tb_estimates.csv
data/raw/who_tb/who_tb_notifications.csv
data/raw/who_tb/who_tb_outcomes.csv
```

### Transform

The transform layer cleans column names, parses years, removes empty columns, and standardises county names. It does not define epidemiological measures.

Important outputs include:

```text
data/processed/who_tb/estimates_kenya.csv
data/processed/who_tb/notifications_kenya.csv
data/processed/who_tb/outcomes_kenya.csv
data/processed/knbs/county_population_2019.csv
data/processed/kmhfr/dim_facility.csv
```

### Indicators

Indicator definitions are held in one layer so that analysis and charts use the same formulas. Examples include:

```text
notification-incidence gap = estimated incident TB - notified TB cases
notification-to-incidence ratio = notified TB cases / estimated incident TB × 100
facility density = facilities / population × 100,000
```

The pipeline also checks duplicate indicator-year records, invalid years, implausible percentages, negative values, missing denominators, and treatment outcomes larger than their cohort.

National indicator data use `indicator_id` as the stable identifier and `indicator_name` as the display name.

### Analysis and figures

The analysis layer creates descriptive national trend tables, notification-gap tables, treatment summaries, TB/HIV summaries, county-context tables, and report-ready extracts when their upstream data exist.

The visualization layer creates one national chart per indicator rather than combining unrelated units on one axis. It can also create detection-gap, treatment, TB/HIV, county, and concentration figures where data exist.

Interactive maps require `folium` and valid facility coordinates. A county choropleth also requires an externally supplied county-boundary GeoJSON file.

## Run individual layers

Use individual modules when developing or diagnosing a particular stage:

```bash
python -m src.extract.who_tb
python -m src.extract.knbs
python -m src.extract.kmhfr
python -m src.extract.hiv

python -m src.transform.pipeline
python -m src.indicators.pipeline
python -m src.analysis.pipeline
python -m src.visualization.pipeline
```

## Outputs

On a run with the required source inputs, expect outputs such as:

```text
data/indicators/fact_tb_indicator_year.csv
data/indicators/treatment_cohorts.csv
data/indicators/tb_hiv_long.csv
data/analysis/national/national_indicator_series.csv
data/analysis/detection_gap/detection_gap_by_year.csv
data/analysis/treatment/treatment_trend_summary.csv
data/analysis/tb_hiv/tb_hiv_trend_summary.csv
outputs/figures/national/
outputs/figures/detection_gap/
outputs/figures/treatment/
outputs/figures/tb_hiv/
```

County outputs require the KNBS county population file. Facility-density outputs also require KMHFR facility data. No county TB burden or county notification rate is calculated unless a real county-level TB programme dataset is added.

## Interpretation limits

- Counts and population-adjusted rates answer different questions.
- WHO burden estimates and routine notifications are different measurements.
- Missing programme data remain missing.
- County-level associations do not establish individual-level causes.
- Routine surveillance can include reporting delays, changing definitions, incomplete records, and changes in diagnostic practice.

## Next additions

Useful extensions include verified county TB notifications and outcomes, annual county population projections, facility-level TB service availability, county HIV prevalence, scheduled data refresh and a narrative report or dashboard built from the existing output tables.

### Example of a possible future analytical model

With county TB data are available, the county table could support more fields such as:

```text
county
year
population
notifications
notification_rate
estimated_incidence
treatment_started
treatment_success
treatment_success_rate
deaths
death_rate
lost_to_followup
lost_to_followup_rate
hiv_positive_tb
tb_hiv_pct
child_tb
child_tb_pct
bacteriologically_confirmed
confirmation_rate
rr_mdr_tb
hiv_prevalence
population_density
facility_count
facilities_per_100k
```

This would support a much deeper TB programme-performance analysis.

# Author

**Wayne Willis Omondi**

