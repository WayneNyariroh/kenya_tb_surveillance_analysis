# Indicator layer

This layer turns cleaned source fields into explicitly defined epidemiological
measures for the Kenya TB case study.

It sits between `src/transform/` and notebooks/dashboard code:

```text
raw source files
      ↓
src/extract/
      ↓
data/raw/
      ↓
src/transform/
      ↓
data/processed/ + data/model/
      ↓
src/indicators/
      ↓
data/indicators/
      ↓
analysis notebooks / dashboard / case-study report
```

## Why keep indicators outside notebooks?

A notebook should not quietly define `treatment_success_rate` one way while a
Streamlit app defines it another way. These modules establish one reusable
calculation layer.

## Files

### `registry.py`

Human-readable indicator definitions, units, formulas, source tables and
interpretation cautions.

### `burden.py`

Extracts WHO burden indicators when their documented variables are present,
including:

- estimated TB incidence
- incidence rate per 100,000
- estimated TB mortality excluding HIV-associated TB deaths
- HIV-associated TB incidence
- HIV-associated TB mortality
- population denominator

Uncertainty bounds are retained when WHO supplies lower and upper values.

### `notifications.py`

Builds reported notification measures and conservative derived indicators:

```text
notification_rate = notifications / population × 100,000

incidence_notification_gap =
    estimated_incidence - notifications

notification_to_incidence_ratio =
    notifications / estimated_incidence × 100
```

The last measure is intentionally called a notification-to-incidence ratio. It
is not automatically labelled a measured case-detection rate because its
denominator is a modelled burden estimate.

### `treatment.py`

WHO outcome files can contain multiple cohorts and their field names can differ
across releases. This module discovers every `*_coh` variable and looks for
matching outcome fields such as:

```text
*_succ
*_cur
*_cmplt
*_died
*_fail
*_lost
*_neval
```

If a direct success field is unavailable, success is calculated only when both
cured and treatment-completed counts are available.

The result retains the original source variables so every percentage can be
audited.

### `tb_hiv.py`

Builds WHO HIV-associated TB burden measures and, where matching country-reported
variables exist, derives HIV positivity among tested TB patients and ART coverage
among HIV-positive TB patients.

### `diagnostics.py`

Creates an inventory of diagnostic/laboratory variables available in the current
WHO extract. It does not guess denominators. Once we choose specific diagnostic
indicators from the WHO data dictionary, they can be promoted into defined
metrics.

### `county.py`

Builds county context measures from KNBS and KMHFR, including registered health
facilities per 100,000 population and coordinate completeness.

Facility density is context, not TB-service coverage. A registered facility is
not assumed to provide TB diagnosis or treatment.

### `quality.py`

Checks:

- expected indicator columns
- valid years
- duplicate indicator-year rows
- percentage bounds
- treatment successes exceeding cohort sizes
- suspicious negative values

## Run

After extract and transform have completed:

```bash
python -m src.indicators.pipeline
```

Outputs are written to:

```text
data/indicators/
├── tb_burden_long.csv
├── tb_notifications_long.csv
├── tb_hiv_long.csv
├── treatment_cohorts.csv
├── diagnostic_variable_inventory.csv
├── county_context_indicators.csv
├── fact_tb_indicator_year.csv
├── analysis_tb_year.csv
├── quality_indicators.csv
├── quality_treatment.csv
└── indicator_run.json
```

## Two useful tables

`fact_tb_indicator_year.csv` is the tidy long-form table for reusable analysis,
visualisation and dashboards.

`analysis_tb_year.csv` is the wide analyst-friendly table where each year is one
row and each indicator is one column. It is convenient for notebooks, trend
plots and correlations.

## Interpretation rule

WHO burden estimates are modelled estimates. Notifications and treatment
outcomes are programme/surveillance observations. Derived comparisons retain
that distinction in their names and notes.
