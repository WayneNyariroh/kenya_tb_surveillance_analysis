# Analysis layer

`src/analysis/` turns the indicator tables into case-study outputs.

The extraction layer answers:

> Where did the data come from?

The transformation layer answers:

> How were the source files cleaned and standardised?

The indicators layer answers:

> How is each epidemiological measure defined?

The analysis layer answers:

> What does the data say?

## Modules

### `national.py`

Creates national indicator trend summaries.

Outputs:

```text
data/analysis/national/
├── national_indicator_series.csv
└── national_indicator_trends.csv
```

For each indicator it reports:

```text
first_year
first_value
latest_year
latest_value
absolute_change
percent_change
annual_linear_slope
observations
```

The slope is descriptive, not a causal or forecasting model.

---

### `detection_gap.py`

Builds the incidence-versus-notification analysis.

Preferred measures:

```text
estimated_incident_tb
notifications
notification_incidence_gap
notification_to_incidence_ratio
```

Output:

```text
data/analysis/detection_gap/
├── detection_gap_by_year.csv
└── detection_gap_latest.csv
```

The notification-to-incidence ratio is deliberately not called a measured
"case detection rate". The numerator is routine notification data while the
incidence denominator is a modelled estimate.

---

### `treatment.py`

Summarises treatment cohort indicators produced upstream.

Potential metrics include:

```text
treatment_success_rate
death_rate
lost_to_followup_rate
failure_rate
not_evaluated_rate
cohort_size
successful_treatment
died
lost_to_followup
failed
not_evaluated
```

Output:

```text
data/analysis/treatment/
├── treatment_series.csv
└── treatment_trend_summary.csv
```

---

### `tb_hiv.py`

Creates trend summaries for standardised TB/HIV measures.

Output:

```text
data/analysis/tb_hiv/
├── tb_hiv_series.csv
└── tb_hiv_trend_summary.csv
```

---

### `county.py`

Produces a county context table.

Current county information may include:

```text
population
population density
health facility count
facilities per 100,000
HIV indicators if a public source was downloaded
```

The module explicitly does not invent county TB burden if true county-level
TB programme data are absent.

Outputs:

```text
data/analysis/county/
├── county_context_profile.csv
└── county_context_summary.csv
```

---

### `concentration.py`

Calculates geographic concentration measures for valid county-level count
variables.

Measures:

```text
top 5 county share
top 10 county share
HHI
```

Once county TB notifications are available, this answers questions such as:

> What share of all notifications comes from the five highest-volume counties?

Until then it can still describe facility or population concentration.

---

### `report_tables.py`

Produces compact, presentation-ready CSV tables for the notebook, README and
final report.

---

## Run all analyses

```bash
python -m src.analysis.pipeline
```

The pipeline writes:

```text
data/analysis/analysis_run.json
```

so skipped or failed sections remain visible and auditable.

## Case-study sequence

The intended analytical narrative is:

```text
National burden
      ↓
Long-run trend
      ↓
Estimated incidence vs notifications
      ↓
Notification-incidence gap
      ↓
Treatment outcomes
      ↓
TB/HIV
      ↓
County context
      ↓
Geographic concentration
```

A later notebook should import these outputs rather than reimplementing the
calculations inside notebook cells.
