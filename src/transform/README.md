# Transform layer

`src/transform/` converts immutable source files in `data/raw/` into cleaned tables in `data/processed/`, then builds a small analysis model in `data/model/`.

## Principles

- Raw files are never modified.
- Kenya county names are normalised in one place.
- WHO source indicator names are preserved rather than guessed.
- Rates are calculated only when the denominator is explicit.
- Missing data remain missing.
- Every CSV output gets a `.metadata.json` sidecar.

## Modules

- `county.py`: canonical 47-county names and aliases.
- `who_tb.py`: cleans WHO Kenya estimates, notifications and outcomes.
- `knbs.py`: reads KNBS census workbooks, detects headers and prepares county population data.
- `kmhfr.py`: standardises facility fields, county names and coordinates.
- `hiv.py`: transforms only HIV resources actually downloaded by the extract layer.
- `model.py`: builds `dim_county.csv` and `fact_national_tb_year.csv`.
- `pipeline.py`: runs the full transform/model process.

## Run

```bash
python -m src.transform.pipeline
```

Or individually:

```bash
python -m src.transform.who_tb
python -m src.transform.knbs
python -m src.transform.kmhfr
python -m src.transform.hiv
```

Expected model outputs:

```text
data/model/
├── dim_county.csv
├── fact_national_tb_year.csv
└── transform_run.json
```

The next layer should be `src/indicators/`, where WHO variable codes are mapped to named epidemiological indicators after inspecting the current WHO data dictionary.
