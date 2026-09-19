from __future__ import annotations

import argparse
import logging
from pathlib import Path
import pandas as pd
from .common import clean_columns, ensure_dir, write_table

LOGGER = logging.getLogger(__name__)
DATASET_FILES = {"estimates":"who_tb_estimates_kenya.csv","notifications":"who_tb_notifications_kenya.csv","outcomes":"who_tb_outcomes_kenya.csv"}

def transform_who_tb(raw_dir: Path | str = "data/raw/who_tb", output_dir: Path | str = "data/processed/who_tb") -> dict[str, Path]:
    raw_dir, output_dir = Path(raw_dir), ensure_dir(output_dir)
    outputs = {}
    for dataset, filename in DATASET_FILES.items():
        path = raw_dir / filename
        if not path.exists():
            LOGGER.warning("WHO %s file not found: %s", dataset, path); continue
        df = clean_columns(pd.read_csv(path, low_memory=False))
        if "yr" in df.columns and "year" not in df.columns: df = df.rename(columns={"yr":"year"})
        if "year" in df.columns: df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
        empty = [c for c in df.columns if df[c].isna().all()]
        df = df.drop(columns=empty).drop_duplicates().reset_index(drop=True)
        if "iso3" in df.columns: df["iso3"] = df["iso3"].astype("string").str.upper().str.strip()
        if "country" in df.columns: df["country"] = df["country"].astype("string").str.strip()
        if "year" in df.columns: df = df.sort_values("year", kind="stable").reset_index(drop=True)
        out = output_dir / f"{dataset}_kenya.csv"
        write_table(df, out, metadata={"source":"WHO Global TB Database","dataset":dataset})
        outputs[dataset] = out
    return outputs

def main():
    p=argparse.ArgumentParser(); p.add_argument("--raw-dir",default="data/raw/who_tb"); p.add_argument("--output-dir",default="data/processed/who_tb"); a=p.parse_args(); transform_who_tb(a.raw_dir,a.output_dir)
if __name__ == "__main__": main()
